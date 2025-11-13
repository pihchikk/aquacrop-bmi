#!/usr/bin/env python3
"""
Unified AquaCrop Runner
Handles all 4 scenario types:
1. Scenarios Simulation (regular forward runs)
2. Crop Calibration (optimize crop parameters)
3. Fertility Stress Calibration (optimize fertility level)  
4. AquaCrop Simulation Data (regular runs with texture-based soil)
"""

import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

# BMI wrapper
from aquacrop_bmi_babel import AquaCrop

# Data generation and processing
from aquacrop_bmi.models import (
    ScenariosSimulationInput,
    CropCalibrationInput,
    FertilityStressCalibrationInput,
)
from aquacrop_bmi.project import AquacropProject
from aquacrop_bmi.util import loads_crop_file, get_weather_data, get_elevation
from aquacrop_bmi.soil_texture import get_soil_params
from aquacrop_bmi.data import get_crop_params
from aquacrop_bmi import sync


class UnifiedAquaCropRunner:
    """Handles all AquaCrop scenario types"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path.cwd()
        self.outputs_dir = self.base_dir / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
    
    
    def detect_scenario_type(self, config: dict) -> str:
        """Detect which type of scenario this is"""
        
        # Check for calibration scenarios (have observed yields)
        if 'seasons' in config and len(config['seasons']) > 0:
            if 'yield' in config['seasons'][0]:
                # Has observed yields - it's a calibration scenario
                if 'crop_ref' in config and 'crop_params' in config:
                    return 'crop-calibration'
                elif 'fertility_stress_range' in config:
                    return 'fertility-stress-calibration'
        
        # Regular simulation scenario
        if 'soils' in config:  # Note: plural
            return 'scenarios-simulation'
        
        # Could be simulation data with single soil
        if 'soil' in config:
            # Could be calibration or old-style simulation
            # If no yield data, treat as simulation
            return 'simulation-data'
        
        raise ValueError("Unknown scenario type - could not detect structure")
    
    
    def run_scenarios_simulation(self, config: dict, output_name: str = None):
        """Handle ScenariosSimulationInput - regular forward simulation"""
        
        print(f"\n{'='*70}")
        print("SCENARIO TYPE: REGULAR SIMULATION")
        print(f"{'='*70}")
        
        input_data = ScenariosSimulationInput(**config)
        
        # Get first season for single-season BMI run
        season = input_data.seasons[0]
        soil = input_data.soils[0]
        
        print(f"\n📍 Location: {input_data.point.latitude}°N, {input_data.point.longitude}°E")
        print(f"📅 Period: {season.simulation_start} to {season.simulation_end}")
        print(f"🌱 Crop: {input_data.crop_file[:50]}...")
        
        # Parse crop
        _, crop_index, crop_params = loads_crop_file(input_data.crop_file)
        
        # Fetch weather
        print(f"\n🌦️  Fetching weather...")
        point = input_data.point
        if not hasattr(point, 'altitude'):
            altitude = get_elevation(point.latitude, point.longitude)
        else:
            altitude = point.altitude
            
        weather_data = get_weather_data(
            point.latitude, point.longitude, altitude,
            season.simulation_start, season.simulation_end
        )
        print(f"   ✓ Got {len(weather_data)} days")
        
        # Get soil params
        soil_params = get_soil_params(soil)
        
        # Generate data
        print(f"\n📁 Creating project files...")
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"sim_{timestamp}"
        
        output_path = self.outputs_dir / output_name
        
        project_ctx = AquacropProject(with_default=True)
        project = project_ctx.__enter__()
        
        try:
            project.write_climate_files(season.simulation_start, weather_data)
            project.write_crop_file(crop_index, crop_params)
            project.write_fertility_management_file(input_data.fertility_stress)
            project.write_gwt_file(depth=input_data.gwt_depth, ec=input_data.gwt_ec)
            project.write_soil_file(soil_params)
            project.write_sw0_file(soil_params)
            project.write_calendar_file(season)
            project.write_project_file(season)
            project.write_daily_out_config()
            
            if output_path.exists():
                shutil.rmtree(output_path)
            shutil.copytree(project.root, output_path)
            
            print(f"   ✓ Data saved to: {output_path.relative_to(self.base_dir)}")
            
        finally:
            project_ctx.__exit__(None, None, None)
        
        # Run BMI simulation
        return self.run_bmi(output_path)
    
    
    def run_crop_calibration(self, config: dict, output_name: str = None):
        """Handle CropCalibrationInput - optimize crop parameters"""
        
        print(f"\n{'='*70}")
        print("SCENARIO TYPE: CROP PARAMETER CALIBRATION")
        print(f"{'='*70}")
        
        input_data = CropCalibrationInput(**config)
        
        print(f"\n📍 Location: {input_data.point.latitude}°N, {input_data.point.longitude}°E")
        print(f"📊 Seasons: {len(input_data.seasons)}")
        print(f"🔬 Crop: {input_data.crop_ref}")
        print(f"🎯 Optimizing {len(input_data.crop_params.model_dump(exclude_none=True))} parameters")
        print(f"📈 Sample size: {input_data.sample_size}")
        print(f"📐 Sampling range: ±{input_data.sampling_range}%")
        
        # Run calibration using the sync module
        print(f"\n⏳ Running calibration (this may take a while)...")
        result = sync.run_crop_calibration(input_data)
        
        print(f"\n✅ CALIBRATION COMPLETE!")
        print(f"\n📊 Optimization Results:")
        print(f"   RMSE: {result.error:.3f} t/ha")
        
        print(f"\n🌱 Optimized Crop Parameters:")
        for key, value in result.crop_params.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.4f}")
            else:
                print(f"   {key}: {value}")
        
        # Save results
        output_file = self.outputs_dir / "crop_calibration_result.json"
        with open(output_file, 'w') as f:
            json.dump({
                'error': result.error,
                'crop_params': result.crop_params,
                'crop_file': result.crop_file,
            }, f, indent=2)
        
        print(f"\n💾 Results saved: {output_file.relative_to(self.base_dir)}")
        
        return result
    
    
    def run_fertility_calibration(self, config: dict, output_name: str = None):
        """Handle FertilityStressCalibrationInput - optimize fertility stress"""
        
        print(f"\n{'='*70}")
        print("SCENARIO TYPE: FERTILITY STRESS CALIBRATION")
        print(f"{'='*70}")
        
        input_data = FertilityStressCalibrationInput(**config)
        
        print(f"\n📍 Location: {input_data.point.latitude}°N, {input_data.point.longitude}°E")
        print(f"📊 Seasons: {len(input_data.seasons)}")
        print(f"🌱 Testing fertility stress range: {input_data.fertility_stress_range}")
        print(f"📈 Sample size: {input_data.sample_size}")
        
        # Run calibration
        print(f"\n⏳ Running calibration (this may take a while)...")
        result = sync.run_fertility_stress_calibration(input_data)
        
        print(f"\n✅ CALIBRATION COMPLETE!")
        print(f"\n📊 Optimization Results:")
        print(f"   Optimal fertility stress: {result.fertility_stress}%")
        print(f"   RMSE: {result.error:.3f} t/ha")
        
        # Save results
        output_file = self.outputs_dir / "fertility_calibration_result.json"
        with open(output_file, 'w') as f:
            json.dump({
                'fertility_stress': result.fertility_stress,
                'error': result.error,
                'crop_file': result.crop_file,
            }, f, indent=2)
        
        print(f"\n💾 Results saved: {output_file.relative_to(self.base_dir)}")
        
        return result
    
    
    def run_simulation_data(self, config: dict, output_name: str = None):
        """Handle old-style simulation data format - convert and run"""
        
        print(f"\n{'='*70}")
        print("SCENARIO TYPE: SIMULATION DATA (converting...)")
        print(f"{'='*70}")
        
        # Convert to ScenariosSimulationInput format
        converted = {
            'gwt_depth': config['gwt_depth'],
            'gwt_ec': config['gwt_ec'],
            'point': config['point'],
            'seasons': config['seasons'],
            'crop_file': config['crop_file'],
            'soils': [config['soils']],  # Wrap in list
            'fertility_stress': config.get('fertility_stress', 10),
        }
        
        print("✓ Converted to standard simulation format")
        
        return self.run_scenarios_simulation(converted, output_name)
    
    
    def run_bmi(self, data_path: Path):
        """Run BMI simulation and return results"""
        
        print(f"\n{'='*70}")
        print("RUNNING BMI SIMULATION")
        print(f"{'='*70}")
        
        model = AquaCrop()
        config_file = str(data_path / "LIST" / "project.PRO")
        
        print(f"\n🚀 Initializing...")
        model.initialize(config_file)
        
        start_time = model.get_start_time()
        end_time = model.get_end_time()
        n_steps = int(end_time - start_time)
        
        print(f"   Duration: {n_steps} days")
        
        # Storage
        results = {
            'time': [],
            'canopy_cover': [],
            'biomass': [],
            'yield': [],
            'soil_moisture': []
        }
        
        print(f"\n⏳ Running simulation...")
        dest = np.empty(1, dtype=np.float64)
        
        for step in range(n_steps + 1):
            current_time = model.get_current_time()
            
            model.get_value("crop__canopy_cover", dest)
            results['canopy_cover'].append(dest[0])
            
            model.get_value("crop__biomass", dest)
            results['biomass'].append(dest[0])
            
            model.get_value("crop__yield", dest)
            results['yield'].append(dest[0])
            
            model.get_value("soil__moisture", dest)
            results['soil_moisture'].append(dest[0])
            
            results['time'].append(current_time)
            
            if step % 30 == 0:
                cc = results['canopy_cover'][-1]
                bio = results['biomass'][-1]
                yld = results['yield'][-1]
                print(f"   Day {current_time:.0f}/{end_time:.0f} - "
                      f"CC: {cc:.1f}%, Bio: {bio:.1f} t/ha, Yield: {yld:.1f} t/ha")
            
            if current_time < end_time:
                model.update()
        
        model.finalize()
        print("   ✓ Complete")
        
        # Convert to arrays
        for key in results:
            results[key] = np.array(results[key])
        
        # Print stats
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Max canopy cover:  {np.max(results['canopy_cover']):.2f}%")
        print(f"   Final biomass:     {results['biomass'][-1]:.2f} ton/ha")
        print(f"   Final yield:       {results['yield'][-1]:.2f} ton/ha")
        print(f"   Avg soil moisture: {np.mean(results['soil_moisture']):.2f} mm")
        
        # Save CSV
        output_file = self.outputs_dir / f"results_{data_path.name}.csv"
        with open(output_file, 'w') as f:
            f.write("day,canopy_cover,biomass,yield,soil_moisture\n")
            for i in range(len(results['time'])):
                f.write(f"{results['time'][i]:.0f},{results['canopy_cover'][i]:.2f},"
                       f"{results['biomass'][i]:.2f},{results['yield'][i]:.2f},"
                       f"{results['soil_moisture'][i]:.2f}\n")
        
        print(f"\n💾 Results saved: {output_file.relative_to(self.base_dir)}")
        
        return results
    
    
    def run(self, scenario_file: Path, output_name: str = None):
        """Auto-detect scenario type and run appropriate handler"""
        
        print(f"\n{'#'*70}")
        print(f"# AQUACROP UNIFIED RUNNER")
        print(f"# File: {scenario_file.name}")
        print(f"{'#'*70}")
        
        # Load config
        with open(scenario_file) as f:
            config = json.load(f)
        
        # Detect type
        scenario_type = self.detect_scenario_type(config)
        print(f"\n🔍 Detected type: {scenario_type}")
        
        # Route to appropriate handler
        if scenario_type == 'scenarios-simulation':
            return self.run_scenarios_simulation(config, output_name)
        elif scenario_type == 'crop-calibration':
            return self.run_crop_calibration(config, output_name)
        elif scenario_type == 'fertility-stress-calibration':
            return self.run_fertility_calibration(config, output_name)
        elif scenario_type == 'simulation-data':
            return self.run_simulation_data(config, output_name)
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")


def main():
    parser = argparse.ArgumentParser(
        description='Unified AquaCrop runner - handles all scenario types automatically'
    )
    parser.add_argument(
        'scenario',
        type=Path,
        help='Path to scenario JSON file'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output directory name'
    )
    
    args = parser.parse_args()
    
    runner = UnifiedAquaCropRunner()
    
    if not args.scenario.exists():
        print(f"❌ Error: File not found: {args.scenario}")
        return 1
    
    try:
        runner.run(args.scenario, args.output)
        
        print(f"\n{'='*70}")
        print("✅ COMPLETE!")
        print(f"{'='*70}\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())