"""
BMI wrapper for calibration
- crop-calibration: Calibrates crop parameters to match observed yields
- fertility-stress-calibration: Finds optimal fertility stress values per season  
- scenarios-simulation: Direct simulation with provided parameters
- Multiple seasons/soils: Step-by-step via reinitialize_next_season()
"""

from __future__ import annotations

import json
import shutil
import os
from pathlib import Path
from datetime import datetime
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from itertools import product, repeat
from typing import TYPE_CHECKING

import numpy as np
from bmipy import Bmi
from numpy.typing import NDArray
from SALib.sample import sobol

from .project import AquacropProject
from .util import (
    loads_crop_file, get_weather_data, get_elevation, 
    dump_crop_file
)
from .soil_texture import get_soil_params
from .data_modules import get_crop_params
from .settings import settings
from .models import (
    ScenariosSimulationInput,
    CropCalibrationInput,
    FertilityStressCalibrationInput,
    Point3D,
    Point,
)
from .lib.aquacrop import AquaCrop as FortranBMI

if TYPE_CHECKING:
    from aquacrop_bmi.models import Season


def safe_getcwd():
    """Get current working directory with fallback for broken cwd"""
    try:
        return Path(os.getcwd())
    except FileNotFoundError:
        return Path("/mnt/d")


def suppress_fortran_output():
    """suppress Fortran stdout/stderr"""
    class FortranSuppressor:
        def __enter__(self):
            self.old_stdout = os.dup(1)
            self.old_stderr = os.dup(2)
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)
            os.close(devnull)
            return self
        
        def __exit__(self, *args):
            os.dup2(self.old_stdout, 1)
            os.dup2(self.old_stderr, 2)
            os.close(self.old_stdout)
            os.close(self.old_stderr)
    
    return FortranSuppressor()

CALIBRATED_PARAMETERS = (
    'Soil water depletion factor for canopy expansion (p-exp) - Upper threshold',
    'Soil water depletion factor for canopy expansion (p-exp) - Lower threshold',
    'Shape factor for water stress coefficient for canopy expansion (0.0 = straight line)',
    'Soil water depletion fraction for stomatal control (p - sto) - Upper threshold',
    'Shape factor for water stress coefficient for stomatal control (0.0 = straight line)',
    'Soil water depletion factor for canopy senescence (p - sen) - Upper threshold',
    'Shape factor for water stress coefficient for canopy senescence (0.0 = straight line)',
    'Soil water depletion factor for pollination (p - pol) - Upper threshold',
    'Vol% for Anaerobiotic point (* (SAT - [vol%]) at which deficient aeration occurs *)',
    'Canopy growth coefficient (CGC): Increase in canopy cover (fraction soil cover per day)',
    'Canopy decline coefficient (CDC): Decrease in canopy cover (in fraction per day)',
    'Reference Harvest Index (HIo) (%)',
    'Water Productivity normalized for ETo and CO2 (WP*) (gram/m2)',
)

CALIBRATED_PARAMETERS_WITH_STRESS = (
    'Response of canopy expansion is not considered',
)

POOL = ThreadPoolExecutor(max_workers=int(settings.max_workers or 4))


class BmiAquaCrop(Bmi):
    
    METADATA = "data/AquaCrop"
    """
    Inherited from Bmi CSDMS module
    
    - Calibration happens once during initialize()
    - Results stored for all seasons OR soils
    - reinitialize_next_season() steps through calibrated combinations
    """
    
    _name = "AquaCrop"
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
    _output_var_names = (
        'crop__yield',
        'crop__biomass',
        'crop__canopy_cover',
        'soil__moisture',
        'crop__water_stress',
        'crop__evapotranspiration',
    )
    
    def __init__(self, original_cwd: Path | None = None) -> None:
        self._fortran_bmi = FortranBMI()
        self._config_file: Path | None = None
        self._scenario_data: ScenariosSimulationInput | None = None
        self._current_season_idx = 0
        self._current_soil_idx = 0
        self._data_root: Path | None = None
        self._scenario_type = None
        self._calibration_results = {}
        
        try:
            self._original_cwd = original_cwd or safe_getcwd()
        except FileNotFoundError:
            self._original_cwd = Path("/tmp")
    def initialize(self, config_file: str) -> None:
        """
        Initialize from JSON scenario file
        
        Performs calibration if needed (crop-calibration, fertility-stress-calibration),
        then initializes first season OR soil combination
        """
        config_path = Path(config_file).resolve()
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path) as f:
            config = json.load(f)
        
        self._scenario_type = self._detect_scenario_type(config)
        print(f"Detected scenario type: {self._scenario_type}")
        
        if self._scenario_type == 'crop-calibration':
            print("Performing crop parameter calibration...")
            self._calibration_results = self._run_crop_calibration(config)
            self._scenario_data = self._convert_crop_calibration_to_simulation(
                config, self._calibration_results['crop_file']
            )
        
        elif self._scenario_type == 'fertility-stress-calibration':
            print("Performing fertility stress calibration...")
            self._calibration_results = self._run_fertility_stress_calibration(config)
            self._scenario_data = self._convert_fertility_calibration_to_simulation(
                config, 
                self._calibration_results['crop_file'],
                self._calibration_results['fertility_stress_per_season']
            )
        
        else: 
            self._scenario_data = self._load_scenario_simulation(config)
        
        self._current_season_idx = 0
        self._current_soil_idx = 0
        self._initialize_season()
    
    def _initialize_season(self) -> None:
        """Initialize current season/soil combination"""
        season = self._scenario_data.seasons[self._current_season_idx]
        soil = self._scenario_data.soils[self._current_soil_idx]
        
        if self._scenario_type == 'fertility-stress-calibration':
            fertility_stress = self._calibration_results['fertility_stress_per_season'][
                self._current_season_idx
            ]
        else:
            fertility_stress = self._scenario_data.fertility_stress
        
        print(f"Initializing season {self._current_season_idx + 1}/"
              f"{len(self._scenario_data.seasons)}, "
              f"soil {self._current_soil_idx + 1}/{len(self._scenario_data.soils)}, "
              f"fertility_stress={fertility_stress}")
        
        data_dir = self._generate_aquacrop_data(
            self._scenario_data, season, soil, fertility_stress
        )
        self._data_root = data_dir
        
        project_file = str(data_dir / "LIST" / "project.PRO")
        with suppress_fortran_output():
            self._fortran_bmi.initialize(project_file)
        print(f"Season initialized")
    
    def update(self) -> None:
        """Advance model by one time step"""
        self._fortran_bmi.update()
    
    def update_until(self, then: float) -> None:
        """Advance model until specified time"""
        self._fortran_bmi.update_until(then)
    
    def finalize(self) -> None:
        """Finalize model"""
        self._fortran_bmi.finalize()
        if self._data_root and self._data_root.exists():
            shutil.rmtree(self._data_root)
            self._data_root = None
    
    def reinitialize_next_season(self) -> bool:
        """Move to next season/soil combination"""
        if not self._scenario_data:
            return False
        
        self._current_season_idx += 1
        
        if self._current_season_idx >= len(self._scenario_data.seasons):
            self._current_season_idx = 0
            self._current_soil_idx += 1
            
            if self._current_soil_idx >= len(self._scenario_data.soils):
                return False
        
        self.finalize()
        self._initialize_season()
        return True
    
        
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
    
    def get_var_type(self, var_name: str) -> str:
        return "float64"
    
    def get_var_units(self, var_name: str) -> str:
        units = {
            "crop__yield": "tonnes/ha",
            "crop__biomass": "tonnes/ha",
            "crop__canopy_cover": "fraction",
            "crop__fertility_stress": "percent",
        }
        return units.get(var_name, "")
    
    def get_var_itemsize(self, var_name: str) -> int:
        return 8
    
    def get_var_nbytes(self, var_name: str) -> int:
        return 8
    
    def get_current_time(self) -> float:
        return self._fortran_bmi.get_current_time()
    
    def get_start_time(self) -> float:
        return self._fortran_bmi.get_start_time()
    
    def get_end_time(self) -> float:
        return self._fortran_bmi.get_end_time()
    
    def get_time_units(self) -> str:
        return "days"
    
    def get_time_step(self) -> float:
        return 1.0
    
    def get_value(self, var_name: str, dest: NDArray) -> NDArray:
        return self._fortran_bmi.get_value(var_name, dest)
    
    def set_value(self, var_name: str, src: NDArray) -> None:
        self._fortran_bmi.set_value(var_name, src)
    
    
    def _detect_scenario_type(self, config: dict) -> str:
        """Detect scenario type from JSON structure"""
        if 'crop_ref' in config and 'crop_params' in config:
            return 'crop-calibration'
        elif 'crop_file' in config and 'fertility_stress_range' in config:
            return 'fertility-stress-calibration'
        elif 'crop_file' in config and 'scenarios' not in config:
            return 'simulation-data'
        else:
            return 'scenarios-simulation'
    
    def _convert_crop_calibration_to_simulation(
        self, config: dict, crop_file: str
    ) -> ScenariosSimulationInput:
        """Convert crop-calibration to simulation format"""
        input_data = CropCalibrationInput(**config)
        return ScenariosSimulationInput(
            gwt_depth=input_data.gwt_depth,
            gwt_ec=input_data.gwt_ec,
            point=input_data.point,
            seasons=[s for s in input_data.seasons],
            crop_file=crop_file,
            soils=[input_data.soil],
            fertility_stress=10,
        )
    
    def _convert_fertility_calibration_to_simulation(
        self, config: dict, crop_file: str, stress_per_season: list[int]
    ) -> ScenariosSimulationInput:
        """Convert fertility calibration to simulation format"""
        input_data = FertilityStressCalibrationInput(**config)
        return ScenariosSimulationInput(
            gwt_depth=input_data.gwt_depth,
            gwt_ec=input_data.gwt_ec,
            point=input_data.point,
            seasons=[s for s in input_data.seasons],
            crop_file=crop_file,
            soils=[input_data.soil],
            fertility_stress=stress_per_season[0],  
        )
    
    def _load_scenario_simulation(self, config: dict) -> ScenariosSimulationInput:
        """Load scenarios-simulation directly"""
        return ScenariosSimulationInput(**config)
        
    def _run_crop_calibration(self, config: dict) -> dict:
        """Calibrate crop parameters to match observed yields"""
        input_data = CropCalibrationInput(**config)
        crop_name, crop_index, crop_params = get_crop_params(input_data.crop_ref)
        crop_params.update(input_data.crop_params.model_dump(by_alias=True, exclude_none=True))
        
        samples = self._sample_crop_params(crop_params, input_data)
        
        best_num, best_error, crop_file = self._run_calibration(
            input_data, CALIBRATED_PARAMETERS, crop_name, crop_index, 
            crop_params, samples, None
        )
        
        print(f"Calibration complete: error={best_error:.4f}")
        
        return {
            'crop_params': crop_params,
            'error': best_error,
            'crop_file': crop_file,
        }
    
    def _sample_crop_params(
        self, crop_params: dict, data: CropCalibrationInput
    ) -> NDArray:
        """Generate parameter samples using Sobol sequence"""
        bounds = [
            self._param_bounds(name, crop_params[name], data.sampling_range)
            for name in CALIBRATED_PARAMETERS
        ]
        
        return sobol.sample(
            {
                'num_vars': len(CALIBRATED_PARAMETERS),
                'names': CALIBRATED_PARAMETERS,
                'bounds': bounds,
            },
            data.sample_size,
        )
    
    def _param_bounds(
        self, name: str, value: float | int, sampling_range: float
    ) -> tuple[float, float]:
        sampling_range /= 100.0
        lower = value - (value * sampling_range)
        upper = value + (value * sampling_range)
        return (lower, upper)
    
    
    def _run_fertility_stress_calibration(self, config: dict) -> dict:
        input_data = FertilityStressCalibrationInput(**config)
        crop_name, crop_index, crop_params = loads_crop_file(input_data.crop_file)
        
        samples, stress_samples = self._sample_crop_params_with_stress(crop_params, input_data)
        
        best_num, best_error, crop_file = self._run_calibration(
            input_data, CALIBRATED_PARAMETERS_WITH_STRESS, crop_name, crop_index,
            crop_params, samples, stress_samples
        )
        
        stress_values = [int(stress_samples[best_num])] * len(input_data.seasons)
        
        print(f"Calibration complete: error={best_error:.4f}")
        print(f"Best fertility stress: {stress_samples[best_num]:.0f}%")
        
        return {
            'crop_params': crop_params,
            'error': best_error,
            'crop_file': crop_file,
            'fertility_stress_per_season': stress_values,
        }
    
    def _sample_crop_params_with_stress(
        self, crop_params: dict, data: FertilityStressCalibrationInput
    ) -> tuple[NDArray, NDArray]:
        """Generate samples for crop params and stress"""
        bounds = [
            self._param_bounds(name, crop_params[name], data.sampling_range)
            for name in CALIBRATED_PARAMETERS_WITH_STRESS
        ]
        bounds.append(tuple(data.fertility_stress_range))
        
        names = [*CALIBRATED_PARAMETERS_WITH_STRESS, 'fertility_stress']
        samples = sobol.sample(
            {
                'num_vars': len(names),
                'names': names,
                'bounds': bounds,
            },
            data.sample_size,
        )
        
        return samples[:, :-1], samples[:, -1]
        
    def _run_calibration(
        self, data, calibrated_params, crop_name, crop_index,
        crop_params, samples, stress_samples=None
    ) -> tuple[int, float, str]:
        """
        Run calibration for all season-sample combinations & calculate error
        Returns: (best_sample_index, best_error, best_crop_file)
        """
        if stress_samples is None:
            stress_samples = np.zeros(len(samples))
        
        soil = get_soil_params(data.soil)
        sample_count = len(samples)
        season_count = len(data.seasons)
        
        date_start = min(s.simulation_start for s in data.seasons)
        date_end = max(s.simulation_end for s in data.seasons)
        point = self._normalize_point(data.point)
        
        print(f"Getting weather data for {date_start} to {date_end}...")
        weather_data = get_weather_data(
            point.latitude, point.longitude, point.altitude,
            date_start, date_end
        )
        
        with AquacropProject(with_default=False) as project:
            project.write_climate_files(date_start, weather_data)
            project.write_soil_file(soil)
            project.write_sw0_file(soil)
            project.write_gwt_file(depth=data.gwt_depth, ec=data.gwt_ec)
            
            print(f"Running {season_count * sample_count} simulations...")
            worker = partial(
                self._calibration_worker, project.root, calibrated_params, crop_index
            )
            
            args = (
                (crop_params.copy(), season, sample, stress)
                for season, (sample, stress) in product(
                    data.seasons,
                    zip(samples, stress_samples, strict=False)
                )
            )
            
            error_iter = POOL.map(worker, args)
            errors = np.fromiter(error_iter, np.float64, season_count * sample_count)
            errors = errors.reshape((season_count, sample_count)).mean(axis=0)
        
        best_num = errors.argmin()
        best_error = errors[best_num]
        
        crop_params.update(zip(calibrated_params, samples[best_num], strict=True))
        
        with StringIO() as buffer:
            dump_crop_file(buffer, crop_index, crop_params, crop_name)
            crop_file = buffer.getvalue()
        
        return best_num, best_error, crop_file
    
    def _calibration_worker(
        self, parent: Path, calibrated_params: tuple, crop_index: tuple,
        args: tuple
    ) -> float:
        """Worker: run one simulation and return error"""
        crop_params, season, sample, stress = args
        
        try:
            with AquacropProject(parent) as project:
                project.write_calendar_file(season)
                project.write_project_file(season)
                project.write_fertility_management_file(float(stress))
                
                for key, val in zip(calibrated_params, sample, strict=True):
                    crop_params[key] = val
                
                project.write_crop_file(crop_index, crop_params)
                project.run_aquacrop()
                
                yield_simulated = project.read_final_yield()
                yield_observed = season.yield_
                
                error = abs(yield_observed - yield_simulated)
                return error
        
        except Exception as e:
            print(f"Calibration worker error: {e}")
            return 1e6
        
    def _generate_aquacrop_data(
        self, data: ScenariosSimulationInput, season, soil, fertility_stress
    ) -> Path:
        _, crop_index, crop_params = loads_crop_file(data.crop_file)
        point = self._normalize_point(data.point)
        
        weather_data = get_weather_data(
            point.latitude, point.longitude, point.altitude,
            season.simulation_start, season.simulation_end
        )
        
        soil_params = get_soil_params(soil)
        
        try:
            original_cwd = Path.cwd()
        except FileNotFoundError:
            original_cwd = Path.home()

        output_dir = (original_cwd / "outputs").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_path = output_dir / f"bmi_data_{timestamp}"
        
        with AquacropProject(with_default=True) as project:
            project.write_climate_files(season.simulation_start, weather_data)
            project.write_crop_file(crop_index, crop_params)
            project.write_fertility_management_file(fertility_stress)
            project.write_gwt_file(depth=data.gwt_depth, ec=data.gwt_ec)
            project.write_soil_file(soil_params)
            project.write_sw0_file(soil_params)
            project.write_calendar_file(season)
            project.write_project_file(season)
            project.write_daily_out_config()
            
            if data_path.exists():
                shutil.rmtree(data_path)
            shutil.copytree(project.root, data_path)
        
        print(f"Generated data: {data_path}")
        return data_path
    
    def _normalize_point(self, point: Point | Point3D) -> Point3D:
        """Normalize point to Point3D with altitude"""
        if isinstance(point, Point3D):
            return point
        
        latitude = point.latitude
        longitude = point.longitude
        altitude = get_elevation(latitude, longitude)
        
        return Point3D(latitude=latitude, longitude=longitude, altitude=altitude)
        
    def get_var_grid(self, var_name: str) -> int:
        return 0
    
    def get_grid_rank(self, grid_id: int) -> int:
        return 0
    
    def get_grid_size(self, grid_id: int) -> int:
        return 1
    
    def get_grid_type(self, grid_id: int) -> str:
        return "scalar"
    
    def get_grid_shape(self, grid_id: int, shape: NDArray) -> NDArray:
        shape[:] = [1]
        return shape
    
    def get_grid_spacing(self, grid_id: int, spacing: NDArray) -> NDArray:
        spacing[:] = [1.0]
        return spacing
    
    def get_grid_origin(self, grid_id: int, origin: NDArray) -> NDArray:
        origin[:] = [0.0]
        return origin
    
    def get_grid_x(self, grid_id: int, x: NDArray) -> NDArray:
        x[:] = [0.0]
        return x
    
    def get_grid_y(self, grid_id: int, y: NDArray) -> NDArray:
        y[:] = [0.0]
        return y
    
    def get_grid_z(self, grid_id: int, z: NDArray) -> NDArray:
        z[:] = [0.0]
        return z
    
    def get_grid_node_count(self, grid_id: int) -> int:
        return 1
    
    def get_grid_edge_count(self, grid_id: int) -> int:
        return 0
    
    def get_grid_face_count(self, grid_id: int) -> int:
        return 0
    
    def get_grid_edge_nodes(self, grid_id: int, edge_nodes: NDArray) -> NDArray:
        return edge_nodes
    
    def get_grid_face_edges(self, grid_id: int, face_edges: NDArray) -> NDArray:
        return face_edges
    
    def get_grid_face_nodes(self, grid_id: int, face_nodes: NDArray) -> NDArray:
        return face_nodes
    
    def get_grid_nodes_per_face(self, grid_id: int, nodes_per_face: NDArray) -> NDArray:
        return nodes_per_face
    
    def get_var_location(self, var_name: str) -> str:
        return "node"
    
    def get_value_ptr(self, var_name: str) -> NDArray:
        dest = np.empty(1, dtype=np.float64)
        return self.get_value(var_name, dest)
    
    def get_value_at_indices(self, var_name: str, dest: NDArray, indices: NDArray) -> NDArray:
        return self.get_value(var_name, dest)
    
    def set_value_at_indices(self, var_name: str, inds: NDArray, src: NDArray) -> None:
        self.set_value(var_name, src)