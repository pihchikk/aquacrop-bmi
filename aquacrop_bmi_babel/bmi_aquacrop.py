"""
BMI wrapper for calibration
- crop-calibration: Calibrates crop parameters to match observed yields
- fertility-stress-calibration: Finds optimal fertility stress values per season  
- scenarios-simulation: Direct simulation with provided parameters
- Multiple seasons/soils: Step-by-step via reinitialize_next_season()
"""

from __future__ import annotations

import json
import httpx
import shutil
import os
import uuid
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
from .validation import validate_all, AquaCropValidationError
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
from pydantic import ValidationError



if TYPE_CHECKING:
    from aquacrop_bmi.models import Season


def safe_getcwd():
    """Пробует несколько вариантов по порядку"""
    
    # 1. Попробуй текущую директорию
    try:
        cwd = Path(os.getcwd())
        # Проверь что можем писать
        test_file = cwd / ".write_test"
        test_file.touch()
        test_file.unlink()
        return cwd  # ✓ Работает - используем!
    except:
        pass
    
    # 2. Попробуй home директорию пользователя
    try:
        home = Path.home()
        if home.exists():
            return home  # ✓ ~/outputs будет создан
    except:
        pass
    
    # 3. Fallback - /tmp (только если всё остальное не работает)
    return Path("/tmp")


def suppress_fortran_output():
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
        'soil__water_content_in_layers',
    )
    _output_var_names = (
        'crop__yield',
        'crop__biomass',
        'crop__canopy_cover',
        'soil__moisture',
        'crop__water_stress',
        'crop__evapotranspiration',
        'soil__moisture_layer_1',
        'soil__moisture_layer_2',
        'soil__moisture_layer_3',
        'soil__moisture_layer_4',
        'soil__moisture_layer_5',
        'soil__moisture_layer_6',
        'soil__moisture_layer_7',
        'soil__moisture_layer_8',
        'soil__moisture_layer_9',
        'soil__moisture_layer_10',
        'soil__water_content_in_compartments',
        'soil__compartment_thickness',
        'soil_water__deep_percolation_flux',
        'land_surface_water__runoff_flux',
        'soil_water__infiltration_flux',
        'soil__evaporation_flux',
        'crop__transpiration_flux_actual',
        'soil_water__capillary_rise_flux',
    )
    
    def __init__(self, original_cwd: Path | None = None, init_fortran: bool = True) -> None:
        self._init_fortran = init_fortran
        if init_fortran:
            self._fortran_bmi = FortranBMI()
        else:
            self._fortran_bmi = None
        self._config_file: Path | None = None
        self._scenario_data: ScenariosSimulationInput | None = None
        self._current_season_idx = 0
        self._current_soil_idx = 0
        self._data_root: Path | None = None
        self._scenario_type = None
        self._calibration_results = {}
        self._calibration_only = False

        try:
            self._original_cwd = original_cwd or safe_getcwd()
        except FileNotFoundError:
            self._original_cwd = Path("/tmp")
    def initialize(self, config_file: str) -> None:
        
        try:
            config_path = Path(config_file).resolve()
            
            if not config_path.exists():
                print(self._format_file_not_found_error(str(config_path)))
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            try:
                with open(config_path) as f:
                    config = json.load(f)
            except json.JSONDecodeError as e:
                print(self._format_json_error(str(config_path), e))
                raise
            
            self._config_file = config_path
            self._scenario_type = self._detect_scenario_type(config)
            
            print(f"Detected scenario type: {self._scenario_type}")
            
            if self._scenario_type == 'crop-calibration':
                print("Performing crop parameter calibration...")
                try:
                    self._calibration_results = self._run_crop_calibration(config)
                except ValidationError as e:
                    print(self._format_validation_error(e, str(config_path)))
                    raise
                
                output_dir = self._save_calibration_results()
                self._data_root = output_dir
                self._calibration_only = True
                print(f"\n✓ Calibration complete. Results saved.")
                print(f"  To run simulation, use the generated scenarios file in outputs/")
                return
            
            elif self._scenario_type == 'fertility-stress-calibration':
                print("Performing fertility stress calibration...")
                try:
                    self._calibration_results = self._run_fertility_stress_calibration(config)
                except ValidationError as e:
                    print(self._format_validation_error(e, str(config_path)))
                    raise
                
                output_dir = self._save_calibration_results()
                self._data_root = output_dir
                self._calibration_only = True
                print(f"\n✓ Calibration complete. Results saved.")
                print(f"  To run simulation, use the generated scenarios file in outputs/")
                return
            
            try:
                if self._scenario_type == 'simulation-data':
                    self._scenario_data = ScenariosSimulationInput(**config)
                else:  
                    self._scenario_data = self._load_scenario_simulation(config)
            except ValidationError as e:
                print(self._format_validation_error(e, str(config_path)))
                raise
            
            self._initialize_season()
            
        except httpx.ReadTimeout:
            print(self._format_network_error())
            raise
        except AquaCropValidationError:
            raise
        except Exception as e:
            print(f"\nInitialization error: {type(e).__name__}")
            print(str(e))
            raise


    def _format_file_not_found_error(self, config_file: str) -> str:
        return f"""
    Configuration file not found

    File: {config_file}

    The specified file does not exist.

    Troubleshooting:
    1. Check that the path is correct.
    2. Ensure the file has a .json extension.
    3. Verify the current working directory.

    Example scenario files:
    - scenarios/AquacropSimulationData.json
    - scenarios/crop-calibration.json
    - scenarios/fertility-stress-calibration.json

    """
    
    def _format_json_error(self, config_file: str, error: json.JSONDecodeError) -> str:
        return f"""
    Invalid JSON syntax

    File: {config_file}
    Line: {error.lineno}, Column: {error.colno}
    Message: {error.msg}

    Common causes:
    1. Missing or extra commas.
    2. Single quotes instead of double quotes.
    3. Unmatched brackets {{ }} or [ ].
    4. Trailing comma after the last item.

    Suggestion:
    Validate your file using an online JSON validator (e.g., jsonlint.com).

    """



    def _format_validation_error(self, error: ValidationError, config_file: str) -> str:
        errors = error.errors()

        missing = ['.'.join(str(x) for x in e['loc']) for e in errors if e['type'] == 'missing']
        type_errs = [('.'.join(str(x) for x in e['loc']), e['msg'])
                    for e in errors if 'type' in e['type']]

        lines = [
            "Invalid scenario structure",
            f"\nFile: {config_file}\n"
        ]

        if missing:
            lines.append("Missing required fields:")
            for field in missing:
                lines.append(f"  - {field}")
                if 'simulation_start' in field or 'simulation_end' in field:
                    lines.append("    Expected format: YYYY-MM-DD")
                elif 'const.wc' in field:
                    lines.append("    Expected water content value (0–1)")
                elif 'const.ec' in field:
                    lines.append("    Expected electrical conductivity (dS/m)")
                elif 'const.ksat' in field:
                    lines.append("    Expected hydraulic conductivity (mm/day)")

        if type_errs:
            lines.append("\nType errors:")
            for loc, msg in type_errs:
                lines.append(f"  - {loc}: {msg}")

        if any('season' in f for f in missing):
            lines.extend([
                "\nExpected season structure:",
                "\"seasons\": [{",
                "  \"planting_date\": \"2020-05-01\",",
                "  \"simulation_start\": \"2020-04-15\",",
                "  \"simulation_end\": \"2020-09-20\",",
                "  \"growing_season_start\": \"2020-05-01\",",
                "  \"growing_season_end\": \"2020-09-15\",",
                "  \"harvest_date\": \"2020-09-15\",",
                "  \"yield_\": 8.5",
                "}]"
            ])

        if any('soil' in f for f in missing):
            lines.extend([
                "\nExpected soil structure:",
                "\"soils\": [[{",
                "  \"thickness\": 200.0,",
                "  \"sat\": 0.50,",
                "  \"fc\": 0.31,",
                "  \"wp\": 0.15,",
                "  \"Ksat\": 1200.0,",
                "  \"const\": {",
                "    \"wc\": 0.31,",
                "    \"ec\": 0.5,",
                "    \"ksat\": 1200.0",
                "  }",
                "}]]"
            ])

        lines.extend([
            "\nReference:",
            "  See example files in the scenarios/ directory.",
        ])

        return '\n'.join(lines)


    def _format_network_error(self) -> str:
        return f"""
    Network timeout while requesting elevation data

    The elevation API did not respond.

    Workaround:
    Add an altitude value directly in your scenario file, for example:

    {
    "point": {
        "latitude": 35.0,
        "longitude": -120.0,
        "altitude": 100.0
    }
    }

    """
    
    def _initialize_season(self) -> None:
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

        if self._init_fortran and self._fortran_bmi is not None:
            project_file = str(data_dir / "LIST" / "project.PRO")
            with suppress_fortran_output():
                self._fortran_bmi.initialize(project_file)
            print(f"Season initialized")

    def update(self) -> None:
        self._fortran_bmi.update()
    
    def update_until(self, then: float) -> None:
        self._fortran_bmi.update_until(then)
    
    def finalize(self) -> None:
        if self._fortran_bmi is not None:
            self._fortran_bmi.finalize()
        if self._data_root and self._data_root.exists():
            shutil.rmtree(self._data_root)
            self._data_root = None
    
    def reinitialize_next_season(self) -> bool:
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
        return ScenariosSimulationInput(**config)
    
    def _save_calibration_results(self) -> Path:
        from datetime import datetime
        from pathlib import Path
        import json
        
        if not self._calibration_results:
            print("Warning: No calibration results to save")
            return Path("/tmp/outputs")
        
        if hasattr(self, '_original_cwd') and self._original_cwd:
            base_output = self._original_cwd / "outputs"
        elif hasattr(self, '_output_base'):
            base_output = self._output_base
        else:
            try:
                base_output = Path.cwd() / "outputs"
            except:
                base_output = Path("/tmp/outputs")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = base_output / f"{self._scenario_type}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        crop_file_path = output_dir / "crop_calibrated_bmi.txt"
        with open(crop_file_path, 'w') as f:
            f.write(self._calibration_results['crop_file'])
        print(f"  Saved: {crop_file_path}")
        
        scenarios_file_path = output_dir / "scenarios_from_bmi_calib.json"
        
        scenario_data = {
            'gwt_depth': self._calibration_results.get('gwt_depth', 3.0),
            'gwt_ec': self._calibration_results.get('gwt_ec', 0.0),
            'point': self._calibration_results.get('point', {}),
            'seasons': self._calibration_results.get('seasons', []),
            'crop_file': self._calibration_results['crop_file'],
            'soils': self._calibration_results.get('soils', []),
            'fertility_stress': self._calibration_results.get('fertility_stress_per_season', [10])[0],
        }
        
        with open(scenarios_file_path, 'w') as f:
            json.dump(scenario_data, f, indent=2, default=str)
        print(f"  Saved: {scenarios_file_path}")
        
        metadata_path = output_dir / "calibration_metadata.json"
        metadata = {
            'scenario_type': self._scenario_type,
            'error': float(self._calibration_results.get('error', 0.0)),
            'best_sample_index': int(self._calibration_results.get('best_num', 0)),
            'timestamp': datetime.now().isoformat(),
        }
        
        if 'fertility_stress_per_season' in self._calibration_results:
            metadata['fertility_stress'] = [int(x) for x in self._calibration_results['fertility_stress_per_season']]
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"  Saved: {metadata_path}")
        
        return output_dir
        
    def _run_crop_calibration(self, config: dict) -> dict:
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
            'best_num': best_num,
            'crop_file': crop_file,
            'fertility_stress_per_season': [10] * len(input_data.seasons),
            'gwt_depth': input_data.gwt_depth,
            'gwt_ec': input_data.gwt_ec,
            'point': input_data.point.model_dump() if hasattr(input_data.point, 'model_dump') else input_data.point,
            'seasons': [s.model_dump() if hasattr(s, 'model_dump') else s for s in input_data.seasons],
            'soils': [[layer.model_dump() if hasattr(layer, 'model_dump') else layer for layer in input_data.soil]],
        }
    
    def _sample_crop_params(
        self, crop_params: dict, data: CropCalibrationInput
    ) -> NDArray:
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
        crop_file_text = self._resolve_crop_file(input_data.crop_file)
        crop_name, crop_index, crop_params = loads_crop_file(crop_file_text)
        
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
            'best_num': best_num,
            'crop_file': crop_file,
            'fertility_stress_per_season': stress_values,
            'gwt_depth': input_data.gwt_depth,
            'gwt_ec': input_data.gwt_ec,
            'point': input_data.point.model_dump() if hasattr(input_data.point, 'model_dump') else input_data.point,
            'seasons': [s.model_dump() if hasattr(s, 'model_dump') else s for s in input_data.seasons],
            'soils': [[layer.model_dump() if hasattr(layer, 'model_dump') else layer for layer in input_data.soil]],
        }
    
    def _sample_crop_params_with_stress(
        self, crop_params: dict, data: FertilityStressCalibrationInput
    ) -> tuple[NDArray, NDArray]:
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
        
        self._crop_name = crop_name
        self._current_gwt_depth = data.gwt_depth
        self._current_gwt_ec = data.gwt_ec
        self._current_point = data.point.model_dump() if hasattr(data.point, 'model_dump') else data.point
        self._current_soil = data.soil
        
        sample_count = len(samples)
        season_count = len(data.seasons)
        
        print(f"Running {season_count * sample_count} simulations...")
        
        errors = np.zeros((season_count, sample_count))
        
        sim_count = 0
        total = season_count * sample_count
        CLEANUP_BATCH = 10  # Force cleanup every N simulations
        
        for season_idx, season in enumerate(data.seasons):
            print(f"Season {season_idx + 1}/{season_count}")
            
            for sample_idx, (sample, stress) in enumerate(zip(samples, stress_samples)):
                sim_count += 1
                
                error = self._calibration_worker(
                    None,  
                    calibrated_params,
                    crop_index,
                    (crop_params.copy(), season, sample, stress)
                )
                
                errors[season_idx, sample_idx] = error
                
                if sim_count % CLEANUP_BATCH == 0:
                    import gc
                    gc.collect()
                
                if sim_count % 50 == 0 or sim_count == total:
                    print(f"  Progress: {sim_count}/{total} simulations")
        
        errors_mean = errors.mean(axis=0)
        best_num = errors_mean.argmin()
        best_error = errors_mean[best_num]
        
        crop_params.update(zip(calibrated_params, samples[best_num], strict=True))
        
        with StringIO() as buffer:
            dump_crop_file(buffer, crop_index, crop_params, crop_name)
            crop_file = buffer.getvalue()
        
        return best_num, best_error, crop_file

    def _calibration_worker(
        self, parent: Path, calibrated_params: tuple, crop_index: tuple,
        args: tuple
    ) -> float:
        import tempfile
        import json
        import os
        from io import StringIO
        from contextlib import redirect_stdout, redirect_stderr
        import numpy as np
        
        crop_params, season, sample, stress = args
        
        try:
            for key, val in zip(calibrated_params, sample, strict=True):
                crop_params[key] = val
            
            with StringIO() as buffer:
                dump_crop_file(buffer, crop_index, crop_params, self._crop_name)
                test_crop_file = buffer.getvalue()
            
            temp_dict = {
                'gwt_depth': self._current_gwt_depth,
                'gwt_ec': self._current_gwt_ec,
                'point': self._current_point,
                'seasons': [season.model_dump() if hasattr(season, 'model_dump') else season],
                'crop_file': test_crop_file,
                'soils': [[layer.model_dump() if hasattr(layer, 'model_dump') else layer 
                        for layer in self._current_soil]],  
                'fertility_stress': int(stress),
            }
                
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(temp_dict, f, default=str)
                temp_file = f.name
            
            try:
                from aquacrop_bmi_babel.bmi_aquacrop import BmiAquaCrop
                model = BmiAquaCrop()
                
                try:
                    with open(os.devnull, 'w') as devnull:
                        with redirect_stdout(devnull), redirect_stderr(devnull):
                            model.initialize(temp_file)
                    
                    start_time = model.get_start_time()
                    end_time = model.get_end_time()
                    n_steps = int(end_time - start_time)
                    
                    dest = np.empty(1, dtype=np.float64)
                    
                    for step in range(n_steps + 1):
                        current_time = model.get_current_time()
                        
                        if current_time < end_time:
                            model.update()
                    
                    model.get_value("crop__yield", dest)
                    yield_simulated = float(dest[0])
                    
                    yield_observed = season.yield_
                    error = abs(yield_observed - yield_simulated)
                    return error
                
                finally:
                    try:
                        model.finalize()
                    except Exception as e:
                        pass  
                    finally:
                        del model  # Explicit cleanup
            
            finally:
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        except Exception as e:
            print(f"Calibration worker error: {e}")
            import traceback
            traceback.print_exc()
            return 1e6
        
    def _resolve_crop_file(self, crop_file: str) -> str:
        """Resolve crop_file to full CRO text.

        Accepts either:
        - Full CRO text (multi-line with ':' delimiters)
        - Built-in crop name like "Maize", "MaizeGDD", "Wheat"
        """
        # If it looks like full CRO text, return as-is
        if ':' in crop_file and '\n' in crop_file:
            return crop_file

        # Try to resolve as a built-in crop name
        from .data_modules import CropRef

        name = crop_file.strip()
        # Strip common suffixes to find the base crop name
        for suffix in ('GDD', 'Cal', 'Calendar'):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        # Try exact match, then case-insensitive
        for ref in CropRef:
            if ref.value == name or ref.value.lower() == name.lower():
                crop_path = Path(__file__).parent / 'data_modules' / 'crops' / f'{ref.value}.CRO'
                if crop_path.exists():
                    return crop_path.read_text()

        raise ValueError(
            f"Unknown crop_file: '{crop_file}'. "
            f"Pass full CRO text or a built-in name: {[r.value for r in CropRef]}"
        )

    def _generate_aquacrop_data(
        self, data: ScenariosSimulationInput, season, soil, fertility_stress
    ) -> Path:
        crop_file_text = self._resolve_crop_file(data.crop_file)
        _, crop_index, crop_params = loads_crop_file(crop_file_text)

        # Apply user-provided crop parameter overrides
        if data.crop_params is not None:
            overrides = data.crop_params.to_cro_overrides()
            if overrides:
                crop_params.update(overrides)
                print(f"Applied {len(overrides)} crop parameter override(s)")

        season = self._fix_season_dates(season, crop_params)
        point = self._normalize_point(data.point)
        
        weather_data = get_weather_data(
            point.latitude, point.longitude, point.altitude,
            season.simulation_start, season.simulation_end
        )
        
        soil_params = get_soil_params(soil)

        # Validate all inputs BEFORE writing files for Fortran.
        # Catches int8 overflows, impossible soil combos, division-by-zero
        # triggers, etc. that would otherwise cause cryptic Fortran crashes.
        validate_all(
            soil_layers=soil_params,
            fertility_stress=fertility_stress,
            seasons=[season],
        )

        if hasattr(self, '_original_cwd') and self._original_cwd:
            original_cwd = self._original_cwd
        else:
            try:
                original_cwd = Path.cwd()
            except FileNotFoundError:
                original_cwd = Path.home()

        output_dir = (original_cwd / "outputs").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        unique_id = uuid.uuid4().hex[:8]

        scenario_name = getattr(self, '_scenario_type', 'simulation')
        data_path = output_dir / f"{scenario_name}_{unique_id}"
        
        with AquacropProject(with_default=True) as project:
            project.write_climate_files(season.simulation_start, weather_data)
            project.write_crop_file(crop_index, crop_params)
            project.write_fertility_management_file(fertility_stress)
            if isinstance(data.gwt_depth, list):
                project.write_gwt_file(gwt_series=[
                    {"day": e.day, "depth": e.depth, "ec": e.ec} for e in data.gwt_depth
                ])
            else:
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
        if isinstance(point, Point3D):
            return point
        
        latitude = point.latitude
        longitude = point.longitude
        altitude = get_elevation(latitude, longitude)
        
        return Point3D(latitude=latitude, longitude=longitude, altitude=altitude)

    def _fix_season_dates(self, season, crop_params):
        """Auto-correct season dates to prevent Fortran EOF crashes.

        1. growing_season_start must be >= simulation_start
        2. growing_season_end must be > growing_season_start
        3. simulation_end must be >= growing_season_end
        4. GDD crops: add 30-day safety buffer (actual cycle length is
           computed dynamically from temperatures at runtime)
        """
        from copy import deepcopy
        from datetime import timedelta

        s = deepcopy(season)

        if s.growing_season_start < s.simulation_start:
            print(f"Warning: growing_season_start adjusted to {s.simulation_start}")
            s.growing_season_start = s.simulation_start

        if s.growing_season_end <= s.growing_season_start:
            print(f"Warning: growing_season_end adjusted to {s.simulation_end}")
            s.growing_season_end = s.simulation_end

        if s.simulation_end < s.growing_season_end:
            print(f"Warning: simulation_end extended to {s.growing_season_end}")
            s.simulation_end = s.growing_season_end

        # GDD crop: value 0 means modeCycle_GDDays
        is_gdd_crop = crop_params.get(
            'Determination of crop cycle : by calendar days', 1
        ) == 0

        if is_gdd_crop:
            min_end = s.growing_season_end + timedelta(days=30)
            if s.simulation_end < min_end:
                s.simulation_end = min_end
                print(f"Warning: simulation_end extended to {min_end} (GDD crop buffer)")

        return s

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
