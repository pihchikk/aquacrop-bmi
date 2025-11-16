"""
Proper BMI wrapper for AquaCrop with correct data loading.

Uses the SAME data generation pipeline as sync.py but for BMI step-by-step execution.
Supports:
- Multiple scenario types (crop-calibration, fertility-stress-calibration, scenarios-simulation)
- Automatic data generation from JSON
- Multiple seasons (via re-initialization)
- Fortran BMI backend (aquacrop_bmi_babel)
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

import numpy as np
from bmipy import Bmi
from numpy.typing import NDArray

# Data generation pipeline (same as sync.py)
import aquacrop_bmi.models
from aquacrop_bmi.project import AquacropProject
from aquacrop_bmi.util import loads_crop_file, get_weather_data, get_elevation
from aquacrop_bmi.soil_texture import get_soil_params
from aquacrop_bmi.data import get_crop_params
from aquacrop_bmi_babel import AquaCrop as FortranBMI  # ← ОСТАВИТЬ КАК ЕСТЬ

if TYPE_CHECKING:
    from models import Season


class BmiAquaCrop(Bmi):
    """
    BMI wrapper that properly loads data from JSON scenarios.
    
    Differences from sync.py:
    - sync.py: Batch processing - runs all (soil × season) combinations in parallel
    - BMI: Interactive - step-by-step execution for ONE (soil, season) at a time
    
    Similarities with sync.py:
    - Same data loading pipeline
    - Same crop/soil/weather processing
    - Same file generation
    """
    
    _name = "AquaCrop"
    
    # Input variables (can be set during simulation)
    _input_var_names = (
        'weather__rainfall_amount',
        'weather__air_temperature_max',
        'weather__air_temperature_min',
        'weather__reference_evapotranspiration',
        'management__irrigation_amount',
        'management__irrigation_method',
        'management__mulch_cover',
        'management__bund_height',
        'management__weed_cover',
        'atmosphere__co2_concentration',
        'crop__fertility_stress',
    )
    
    # Output variables (read during simulation)
    _output_var_names = (
        'crop__yield',
        'crop__biomass',
        'crop__canopy_cover',
        'soil__moisture',
        'crop__water_stress',
        'crop__evapotranspiration',
    )
    
    def __init__(self) -> None:
        """Initialize BMI wrapper."""
        self._fortran_bmi = FortranBMI()
        self._config_file: Path | None = None
        self._scenario_data = None
        self._current_season_idx = 0
        self._current_soil_idx = 0
        self._data_root: Path | None = None
    
    
    def initialize(self, config_file: str) -> None:
        """
        Initialize from JSON scenario file.
        
        Generates AquaCrop input files using the SAME pipeline as sync.py,
        then initializes Fortran BMI.
        
        Args:
            config_file: Path to JSON scenario (any type supported)
        """
        config_path = Path(config_file).resolve()
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # Load JSON
        with open(config_path) as f:
            config = json.load(f)
        
        # Detect scenario type and convert to simulation format
        scenario_type = self._detect_scenario_type(config)
        print(f"[BMI] Detected scenario type: {scenario_type}")
        
        self._scenario_data = self._load_scenario(config, scenario_type)
        
        # Generate data for FIRST season and FIRST soil
        # (Like sync.py's _simulation_scenarios_worker but for BMI)
        season = self._scenario_data.seasons[self._current_season_idx]
        soil = self._scenario_data.soils[self._current_soil_idx]
        
        print(f"[BMI] Generating data for season {self._current_season_idx + 1}/{len(self._scenario_data.seasons)}, "
              f"soil {self._current_soil_idx + 1}/{len(self._scenario_data.soils)}")
        
        data_dir = self._generate_aquacrop_data(self._scenario_data, season, soil)
        self._data_root = data_dir
        
        # Initialize Fortran BMI
        project_file = str(data_dir / "LIST" / "project.PRO")
        self._config_file = Path(project_file)
        
        print(f"[BMI] Initializing Fortran BMI with: {project_file}")
        self._fortran_bmi.initialize(project_file)
        
        print(f"[BMI] ✓ Initialization complete")
    
    
    def update(self) -> None:
        """Advance model by one time step."""
        self._fortran_bmi.update()
    
    
    def update_until(self, then: float) -> None:
        """Advance model until specified time."""
        self._fortran_bmi.update_until(then)
    
    
    def finalize(self) -> None:
        """Finalize model."""
        self._fortran_bmi.finalize()
        
        # Clean up generated data
        if self._data_root and self._data_root.exists():
            shutil.rmtree(self._data_root)
            self._data_root = None
    
    
    def reinitialize_next_season(self) -> bool:
        """
        Re-initialize for the next season.
        
        Returns:
            True if there's a next season, False if all seasons are done.
        """
        if not self._scenario_data:
            return False
        
        # Try next season
        self._current_season_idx += 1
        
        if self._current_season_idx >= len(self._scenario_data.seasons):
            # Try next soil
            self._current_season_idx = 0
            self._current_soil_idx += 1
            
            if self._current_soil_idx >= len(self._scenario_data.soils):
                # All done
                return False
        
        # Finalize current
        self.finalize()
        
        # Re-initialize with next season/soil
        season = self._scenario_data.seasons[self._current_season_idx]
        soil = self._scenario_data.soils[self._current_soil_idx]
        
        print(f"\n[BMI] Re-initializing for season {self._current_season_idx + 1}/{len(self._scenario_data.seasons)}, "
              f"soil {self._current_soil_idx + 1}/{len(self._scenario_data.soils)}")
        
        data_dir = self._generate_aquacrop_data(self._scenario_data, season, soil)
        self._data_root = data_dir
        
        project_file = str(data_dir / "LIST" / "project.PRO")
        self._config_file = Path(project_file)
        
        self._fortran_bmi.initialize(project_file)
        
        return True
    
    
    # ========================================================================
    # BMI: Model Information
    # ========================================================================
    
    def get_component_name(self) -> str:
        return self._name
    
    def get_input_item_count(self) -> int:
        return len(self._input_var_names)
    
    def get_output_item_count(self) -> int:
        return len(self._output_var_names)
    
    def get_input_var_names(self) -> tuple[str, ...]:
        return self._input_var_names
    
    def get_output_var_names(self) -> tuple[str, ...]:
        return self._output_var_names
    
    
    # ========================================================================
    # BMI: Variable Information
    # ========================================================================
    
    def get_var_grid(self, var_name: str) -> int:
        return self._fortran_bmi.get_var_grid(var_name)
    
    def get_var_type(self, var_name: str) -> str:
        return self._fortran_bmi.get_var_type(var_name)
    
    def get_var_units(self, var_name: str) -> str:
        return self._fortran_bmi.get_var_units(var_name)
    
    def get_var_itemsize(self, var_name: str) -> int:
        return self._fortran_bmi.get_var_itemsize(var_name)
    
    def get_var_nbytes(self, var_name: str) -> int:
        return self._fortran_bmi.get_var_nbytes(var_name)
    
    def get_var_location(self, var_name: str) -> str:
        return self._fortran_bmi.get_var_location(var_name)
    
    
    # ========================================================================
    # BMI: Time Information
    # ========================================================================
    
    def get_current_time(self) -> float:
        return self._fortran_bmi.get_current_time()
    
    def get_start_time(self) -> float:
        return self._fortran_bmi.get_start_time()
    
    def get_end_time(self) -> float:
        return self._fortran_bmi.get_end_time()
    
    def get_time_units(self) -> str:
        return self._fortran_bmi.get_time_units()
    
    def get_time_step(self) -> float:
        return self._fortran_bmi.get_time_step()
    
    
    # ========================================================================
    # BMI: Variable Getters/Setters
    # ========================================================================
    
    def get_value(self, var_name: str, dest: NDArray) -> NDArray:
        return self._fortran_bmi.get_value(var_name, dest)
    
    def get_value_ptr(self, var_name: str) -> NDArray:
        return self._fortran_bmi.get_value_ptr(var_name)
    
    def get_value_at_indices(self, var_name: str, dest: NDArray, indices: NDArray) -> NDArray:
        return self._fortran_bmi.get_value_at_indices(var_name, dest, indices)
    
    def set_value(self, var_name: str, src: NDArray) -> None:
        self._fortran_bmi.set_value(var_name, src)
    
    def set_value_at_indices(self, var_name: str, inds: NDArray, src: NDArray) -> None:
        self._fortran_bmi.set_value_at_indices(var_name, inds, src)
    
    
    # ========================================================================
    # BMI: Grid Information
    # ========================================================================
    
    def get_grid_rank(self, grid_id: int) -> int:
        return self._fortran_bmi.get_grid_rank(grid_id)
    
    def get_grid_size(self, grid_id: int) -> int:
        return self._fortran_bmi.get_grid_size(grid_id)
    
    def get_grid_type(self, grid_id: int) -> str:
        return self._fortran_bmi.get_grid_type(grid_id)
    
    def get_grid_shape(self, grid_id: int, shape: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_shape(grid_id, shape)
    
    def get_grid_spacing(self, grid_id: int, spacing: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_spacing(grid_id, spacing)
    
    def get_grid_origin(self, grid_id: int, origin: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_origin(grid_id, origin)
    
    def get_grid_x(self, grid_id: int, x: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_x(grid_id, x)
    
    def get_grid_y(self, grid_id: int, y: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_y(grid_id, y)
    
    def get_grid_z(self, grid_id: int, z: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_z(grid_id, z)
    
    def get_grid_node_count(self, grid_id: int) -> int:
        return self._fortran_bmi.get_grid_node_count(grid_id)
    
    def get_grid_edge_count(self, grid_id: int) -> int:
        return self._fortran_bmi.get_grid_edge_count(grid_id)
    
    def get_grid_face_count(self, grid_id: int) -> int:
        return self._fortran_bmi.get_grid_face_count(grid_id)
    
    def get_grid_edge_nodes(self, grid_id: int, edge_nodes: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_edge_nodes(grid_id, edge_nodes)
    
    def get_grid_face_edges(self, grid_id: int, face_edges: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_face_edges(grid_id, face_edges)
    
    def get_grid_face_nodes(self, grid_id: int, face_nodes: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_face_nodes(grid_id, face_nodes)
    
    def get_grid_nodes_per_face(self, grid_id: int, nodes_per_face: NDArray) -> NDArray:
        return self._fortran_bmi.get_grid_nodes_per_face(grid_id, nodes_per_face)
    
    
    # ========================================================================
    # PRIVATE: Data Generation (same as sync.py)
    # ========================================================================
    
    def _detect_scenario_type(self, config: dict) -> str:
        """Detect scenario type (same logic as simple_baseline_runner.py)"""
        if 'seasons' in config and len(config['seasons']) > 0:
            if 'yield' in config['seasons'][0]:
                if 'crop_ref' in config and 'crop_params' in config:
                    return 'crop-calibration'
                elif 'fertility_stress_range' in config:
                    return 'fertility-stress-calibration'
        
        if 'soils' in config:
            return 'scenarios-simulation'
        
        if 'soil' in config:
            return 'simulation-data'
        
        raise ValueError("Unknown scenario type")
    
    
    def _load_scenario(self, config: dict, scenario_type: str) -> ScenariosSimulationInput:
        """
        Load and convert any scenario type to ScenariosSimulationInput format.
        
        This is like sync.py but converting ALL types to simulation format.
        """
        
        if scenario_type == 'crop-calibration':
            input_data = CropCalibrationInput(**config)
            _, crop_index, crop_params = get_crop_params(input_data.crop_ref)
            crop_params.update(input_data.crop_params.model_dump(by_alias=True, exclude_none=True))
            
            # Convert crop params to crop_file string
            from io import StringIO
            from aquacrop_bmi.util import dump_crop_file
            buffer = StringIO()
            dump_crop_file(buffer, crop_index, crop_params, "Crop")
            crop_file = buffer.getvalue()
            
            # Convert to simulation format
            return ScenariosSimulationInput(
                gwt_depth=input_data.gwt_depth,
                gwt_ec=input_data.gwt_ec,
                point=input_data.point,
                seasons=[s for s in input_data.seasons],  # Remove yield
                crop_file=crop_file,
                soils=[input_data.soil],
                fertility_stress=10,
            )
        
        elif scenario_type == 'fertility-stress-calibration':
            input_data = FertilityStressCalibrationInput(**config)
            return ScenariosSimulationInput(
                gwt_depth=input_data.gwt_depth,
                gwt_ec=input_data.gwt_ec,
                point=input_data.point,
                seasons=[s for s in input_data.seasons],
                crop_file=input_data.crop_file,
                soils=[input_data.soil],
                fertility_stress=input_data.fertility_stress_range[0],
            )
        
        elif scenario_type == 'simulation-data':
            # Convert to scenarios-simulation format
            config_sim = {
                'gwt_depth': config['gwt_depth'],
                'gwt_ec': config['gwt_ec'],
                'point': config['point'],
                'seasons': config['seasons'],
                'crop_file': config['crop_file'],
                'soils': [config['soil']],
                'fertility_stress': config.get('fertility_stress', 10),
            }
            return ScenariosSimulationInput(**config_sim)
        
        else:  # scenarios-simulation
            return ScenariosSimulationInput(**config)
    
    
    def _generate_aquacrop_data(
        self, 
        data: ScenariosSimulationInput,
        season: Season,
        soil: list,
    ) -> Path:
        """
        Generate AquaCrop input files for ONE (season, soil) combination.
        
        This is EXACTLY like sync.py's _simulation_scenarios_worker,
        but saves to permanent location instead of running in-place.
        """
        
        # Get crop params
        _, crop_index, crop_params = loads_crop_file(data.crop_file)
        
        # Get point with altitude
        point = data.point
        if not hasattr(point, 'altitude'):
            altitude = get_elevation(point.latitude, point.longitude)
            from aquacrop_bmi.models import Point3D
            point = Point3D(
                latitude=point.latitude,
                longitude=point.longitude,
                altitude=altitude
            )
        else:
            altitude = point.altitude
        
        # Fetch weather for THIS season
        weather_data = get_weather_data(
            point.latitude, point.longitude, altitude,
            season.simulation_start, season.simulation_end
        )
        
        # Get soil params
        soil_params = get_soil_params(soil)
        
        # Create output directory
        output_dir = Path("outputs").resolve()
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_path = output_dir / f"bmi_data_{timestamp}"
        
        # Generate files (same as sync.py's worker)
        with AquacropProject(with_default=True) as project:
            project.write_climate_files(season.simulation_start, weather_data)
            project.write_crop_file(crop_index, crop_params)
            project.write_fertility_management_file(data.fertility_stress)
            project.write_gwt_file(depth=data.gwt_depth, ec=data.gwt_ec)
            project.write_soil_file(soil_params)
            project.write_sw0_file(soil_params)
            project.write_calendar_file(season)
            project.write_project_file(season)
            project.write_daily_out_config()
            
            # Copy to permanent location
            if data_path.exists():
                shutil.rmtree(data_path)
            shutil.copytree(project.root, data_path)
        
        print(f"[BMI] ✓ Generated data: {data_path}")
        
        return data_path
