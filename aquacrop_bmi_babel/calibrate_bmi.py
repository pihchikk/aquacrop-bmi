"""
Calibrate AquaCrop through BMI, tracking is done step-by-step
"""

import json
import sys
import os
import tempfile
from pathlib import Path
from io import StringIO
from datetime import datetime
from itertools import product
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from contextlib import redirect_stdout, redirect_stderr

import numpy as np
from SALib.sample import sobol

from .models import (
    CropCalibrationInput,
    FertilityStressCalibrationInput,
    ScenariosSimulationInput,
)
from .util import loads_crop_file, get_weather_data, get_elevation, dump_crop_file
from .soil_texture import get_soil_params
from .data_modules import get_crop_params
from .settings import settings
from .bmi_aquacrop import BmiAquaCrop


def safe_getcwd():
    """Get current working directory with fallback"""
    try:
        return Path(os.getcwd())
    except FileNotFoundError:
        return Path("/mnt/d")

# Calibration parameters
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


def run_bmi_simulation_for_calibration(
    scenario_data: ScenariosSimulationInput,
    season,
    show_progress: bool = False
) -> float:
    """
    Run one BMI simulation and return final yield
    
    Args:
        scenario_data: ScenariosSimulationInput object
        season: Season object
        show_progress: Print daily yield updates
    
    Returns:
        Final yield value
    """
    temp_dict = {
        'gwt_depth': scenario_data.gwt_depth,
        'gwt_ec': scenario_data.gwt_ec,
        'point': scenario_data.point.model_dump() if hasattr(scenario_data.point, 'model_dump') else scenario_data.point,
        'seasons': [season.model_dump() if hasattr(season, 'model_dump') else season],
        'crop_file': scenario_data.crop_file,
        'soils': [[s.model_dump() if hasattr(s, 'model_dump') else s for s in scenario_data.soils[0]]],
        'fertility_stress': scenario_data.fertility_stress,
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(temp_dict, f, default=str)
        temp_file = f.name
    
    try:
        model = BmiAquaCrop()
        
        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                model.initialize(temp_file)
        
        start_time = model.get_start_time()
        end_time = model.get_end_time()
        n_steps = int(end_time - start_time)
        
        dest = np.empty(1, dtype=np.float64)
        final_yield = 0.0
        
        for step in range(n_steps + 1):
            current_time = model.get_current_time()
            model.get_value("crop__yield", dest)
            final_yield = float(dest[0])
            
            if show_progress and step % 30 == 0:
                print(f"    Day {int(current_time):3d}: Yield={final_yield:.2f} t/ha")
            
            if current_time < end_time:
                model.update()
        
        if show_progress:
            print(f"    Final: {final_yield:.2f} t/ha")
        
        model.finalize()
        return final_yield
    
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass


def calibrate_through_bmi(scenario_file: Path, output_dir: str = None):
    scenario_file = Path(scenario_file).resolve()
    
    if not scenario_file.exists():
        print(f"ERROR: File not found: {scenario_file}")
        return 1
    
    with open(scenario_file) as f:
        config = json.load(f)
    
    # Detect scenario type
    if 'crop_ref' in config and 'crop_params' in config:
        scenario_type = 'crop-calibration'
    elif 'crop_file' in config and 'fertility_stress_range' in config:
        scenario_type = 'fertility-stress-calibration'
    else:
        print(f"ERROR: Unsupported scenario type")
        print(f"  This script requires calibration scenarios:")
        print(f"    - crop-calibration.json (has 'crop_ref' and 'crop_params')")
        print(f"    - fertility-stress-calibration.json (has 'crop_file' and 'fertility_stress_range')")
        print(f"  For simulation scenarios, use: python -m pymt.models AquaCrop")
        return 1
    
    print(f"\n{'='*60}")
    print(f"{scenario_type.upper()}")
    print(f"{'='*60}\n")
    
    # Load and prepare data
    if scenario_type == 'crop-calibration':
        input_data = CropCalibrationInput(**config)
        
        crop_name, crop_index, crop_params = get_crop_params(input_data.crop_ref)
        crop_params.update(input_data.crop_params.model_dump(by_alias=True, exclude_none=True))
        
        bounds = [
            (crop_params[name] * (1 - input_data.sampling_range/100),
             crop_params[name] * (1 + input_data.sampling_range/100))
            for name in CALIBRATED_PARAMETERS
        ]
        
        samples = sobol.sample(
            {
                'num_vars': len(CALIBRATED_PARAMETERS),
                'names': CALIBRATED_PARAMETERS,
                'bounds': bounds,
            },
            input_data.sample_size,
        )
        
        stress_samples = np.zeros(len(samples))
        calibrated_params = CALIBRATED_PARAMETERS
        
    else:  # fertility-stress-calibration
        input_data = FertilityStressCalibrationInput(**config)
        crop_name, crop_index, crop_params = loads_crop_file(input_data.crop_file)
        
        bounds = [
            (crop_params[name] * (1 - input_data.sampling_range/100),
             crop_params[name] * (1 + input_data.sampling_range/100))
            for name in CALIBRATED_PARAMETERS_WITH_STRESS
        ]
        bounds.append(tuple(input_data.fertility_stress_range))
        
        names = [*CALIBRATED_PARAMETERS_WITH_STRESS, 'fertility_stress']
        all_samples = sobol.sample(
            {
                'num_vars': len(names),
                'names': names,
                'bounds': bounds,
            },
            input_data.sample_size,
        )
        
        samples = all_samples[:, :-1]
        stress_samples = all_samples[:, -1]
        calibrated_params = CALIBRATED_PARAMETERS_WITH_STRESS
    
    print(f"Seasons: {len(input_data.seasons)}")
    print(f"Samples: {len(samples)}")
    print(f"Total simulations: {len(input_data.seasons) * len(samples)}\n")
    
    # Run calibration
    errors = np.zeros((len(input_data.seasons), len(samples)))
    
    sim_count = 0
    total_sims = len(input_data.seasons) * len(samples)
    
    for season_idx, season in enumerate(input_data.seasons):
        print(f"Season {season_idx + 1}/{len(input_data.seasons)}: Observed yield = {season.yield_:.2f} t/ha")
        
        for sample_idx, (sample, stress) in enumerate(zip(samples, stress_samples)):
            sim_count += 1
            
            # Update params with sample
            test_params = crop_params.copy()
            for param_name, param_value in zip(calibrated_params, sample):
                test_params[param_name] = param_value
            
            # Generate crop file for this sample
            with StringIO() as buffer:
                dump_crop_file(buffer, crop_index, test_params, crop_name)
                test_crop_file = buffer.getvalue()
            
            # Create scenario for this simulation
            scenario_data = ScenariosSimulationInput(
                gwt_depth=input_data.gwt_depth,
                gwt_ec=input_data.gwt_ec,
                point=input_data.point,
                seasons=[season],
                crop_file=test_crop_file,
                soils=[input_data.soil],
                fertility_stress=int(stress),
            )
            
            # Run simulation
            final_yield = run_bmi_simulation_for_calibration(
                scenario_data,
                season,
                show_progress=False
            )
            
            error = abs(season.yield_ - final_yield)
            errors[season_idx, sample_idx] = error
            
            if (sample_idx + 1) % 2 == 0 or sample_idx == len(samples) - 1:
                print(f"  Sample {sample_idx + 1}/{len(samples)}: "
                      f"sim_count={sim_count}/{total_sims}, "
                      f"yield_sim={final_yield:.2f}, error={error:.4f}")
    
    # Find best sample
    mean_errors = errors.mean(axis=0)
    best_idx = mean_errors.argmin()
    best_error = mean_errors[best_idx]
    
    print(f"\n{'='*60}")
    print(f"CALIBRATION RESULTS")
    print(f"{'='*60}")
    print(f"Best sample index: {best_idx}")
    print(f"Mean error: {best_error:.4f}")
    
    # Update crop params with best values
    for param_name, param_value in zip(calibrated_params, samples[best_idx]):
        crop_params[param_name] = param_value
    
    # Generate final crop file
    with StringIO() as buffer:
        dump_crop_file(buffer, crop_index, crop_params, crop_name)
        final_crop_file = buffer.getvalue()
    
    # Save results to timestamped outputs/ folder
    if output_dir is None:
        try:
            base_output = safe_getcwd() / "outputs"
        except:
            base_output = scenario_file.parent.parent / "outputs"
    else:
        base_output = Path(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = base_output / f"calibration_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "crop_calibrated_bmi.txt"
    with open(output_file, 'w') as f:
        f.write(final_crop_file)
    print(f"\n✓ Saved calibrated crop file to: {output_file}")
    
    # Create scenarios file for BMI use
    if scenario_type == 'fertility-stress-calibration':
        fertility_stress = int(stress_samples[best_idx])
        print(f"✓ Best fertility stress: {fertility_stress}%")
    else:
        fertility_stress = 10
    
    scenarios_file = output_dir / "scenarios_from_calibration.json"
    with open(scenarios_file, 'w') as f:
        json.dump({
            'gwt_depth': input_data.gwt_depth,
            'gwt_ec': input_data.gwt_ec,
            'point': input_data.point.model_dump() if hasattr(input_data.point, 'model_dump') else input_data.point,
            'seasons': [s.model_dump() if hasattr(s, 'model_dump') else s for s in input_data.seasons],
            'crop_file': final_crop_file,
            'soils': [s.model_dump() if hasattr(s, 'model_dump') else s for s in input_data.soil] if isinstance(input_data.soil, list) else input_data.soil,
            'fertility_stress': fertility_stress,
        }, f, indent=2, default=str)
    print(f"✓ Saved scenarios file to: {scenarios_file}")
    
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python calibrate_bmi.py <scenario.json>")
        print("\nExamples:")
        print("  python calibrate_bmi.py scenarios/crop-calibration.json")
        print("  python calibrate_bmi.py scenarios/fertility-stress-calibration.json")
        return 1
    
    scenario_file = Path(sys.argv[1])
    return calibrate_through_bmi(scenario_file)


if __name__ == "__main__":
    sys.exit(main())