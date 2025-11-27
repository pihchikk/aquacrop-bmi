#!/usr/bin/env python3
"""
A simple scenario runner for Aquacrop-BMI
Runs simulation scenarios only (not calibration)
"""
import os
import sys
import json
from pathlib import Path
import numpy as np

from .bmi_aquacrop import BmiAquaCrop


def detect_scenario_type(config: dict) -> str:
    """Detect scenario type from JSON structure"""
    if 'crop_ref' in config and 'crop_params' in config:
        return 'crop-calibration'
    elif 'crop_file' in config and 'fertility_stress_range' in config:
        return 'fertility-stress-calibration'
    elif 'crop_file' in config and 'scenarios' not in config:
        return 'simulation-data'
    else:
        return 'scenarios-simulation'


def run_scenario(scenario_file: Path):
    scenario_file = Path(scenario_file).resolve()
    original_cwd = os.getcwd()
    
    with open(scenario_file) as f:
        scenario_data = json.load(f)
    
    # Check scenario type
    scenario_type = detect_scenario_type(scenario_data)
    
    if scenario_type in ['crop-calibration', 'fertility-stress-calibration']:
        print(f"ERROR: This is a {scenario_type} scenario")
        print(f"  For calibration, use: python -m aquacrop_bmi_babel.calibrate_bmi {scenario_file}")
        print(f"  This runner only supports simulation scenarios:")
        print(f"    - simulation-data (AquaCropSimulationData.json)")
        print(f"    - scenarios-simulation (scenarios-simulation.json)")
        return None
    
    num_seasons = len(scenario_data.get('seasons', [1]))
    num_soils = len(scenario_data.get('soils', [1]))
    total_runs = num_seasons * num_soils
    
    print(f"Scenario type: {scenario_type}")
    print(f"Seasons: {num_seasons}, Soils: {num_soils}, Total runs: {total_runs}\n")
    
    all_results = []
    model = None
    run_count = 0
    
    try:
        model = BmiAquaCrop()
        model.initialize(str(scenario_file))
        
        while True:
            run_count += 1
            season_idx = model._current_season_idx
            soil_idx = model._current_soil_idx
            
            print(f"\n{'='*60}")
            print(f"RUN {run_count}/{total_runs}")
            print(f"SEASON {season_idx + 1}/{num_seasons}, SOIL {soil_idx + 1}/{num_soils}")
            print(f"{'='*60}")
            
            start_time = model.get_start_time()
            end_time = model.get_end_time()
            n_steps = int(end_time - start_time)
            
            print(f"Days to simulate: {n_steps}\nRunning...")
            
            season_results = []
            dest = np.empty(1, dtype=np.float64)
            
            for step in range(n_steps + 1):
                current_time = model.get_current_time()
                
                model.get_value("crop__yield", dest)
                yield_val = float(dest[0])
                
                model.get_value("crop__biomass", dest)
                biomass = float(dest[0])
                
                season_results.append({
                    "day": int(current_time),
                    "yield": yield_val,
                    "biomass": biomass
                })
                
                if step % 30 == 0 or step == n_steps:
                    print(f"  Day {int(current_time):3d}: Yield={yield_val:.2f} t/ha")
                
                if current_time < end_time:
                    model.update()
            
            print(f"Final: {season_results[-1]['yield']:.2f} t/ha")
            all_results.append({
                'season': season_idx + 1,
                'soil': soil_idx + 1,
                'results': season_results
            })
            
            has_next = model.reinitialize_next_season()
            if not has_next:
                break
    
    finally:
        if model:
            try:
                model.finalize()
            except:
                pass
        os.chdir(original_cwd)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"{'Run':<6} {'Season':<10} {'Soil':<10} {'Simulated':<15}")
    
    for idx, result in enumerate(all_results, 1):
        season = result['season']
        soil = result['soil']
        sim_yield = result['results'][-1]['yield']
        print(f"{idx:<6} {season:<10} {soil:<10} {sim_yield:<15.2f}")
    
    return all_results


def main():
    if len(sys.argv) < 2:
        print("Usage: python aquacrop_runner.py <scenario.json>")
        print("\nExamples:")
        print("  python aquacrop_runner.py scenarios/scenarios-simulation.json")
        print("  python aquacrop_runner.py scenarios/AquaCropSimulationData.json")
        print("\nNote: For calibration scenarios, use calibrate_bmi.py instead")
        return 1
    
    scenario_file = Path(sys.argv[1]).resolve()
    
    if not scenario_file.exists():
        print(f"ERROR: File not found: {scenario_file}")
        return 1
    
    try:
        results = run_scenario(scenario_file)
        if results is None:
            return 1
        return 0
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())