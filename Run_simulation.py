#!/usr/bin/env python3
"""
AquaCrop BMI Simulation Runner
Centralized script for running simulations with dynamic data generation
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

# Data generation utilities
from aquacrop_bmi.models import ScenariosSimulationInput
from aquacrop_bmi.project import AquacropProject
from aquacrop_bmi.util import loads_crop_file, get_weather_data
from aquacrop_bmi.soil_texture import get_soil_params


class AquaCropSimulator:
    """Centralized AquaCrop BMI simulator with data generation"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path.cwd()
        self.data_dir = self.base_dir / "data"
        self.scenarios_dir = self.base_dir / "scenarios"
        self.outputs_dir = self.base_dir / "outputs"
        
        # Create directories if needed
        self.outputs_dir.mkdir(exist_ok=True)
        self.scenarios_dir.mkdir(exist_ok=True)
    
    
    def generate_data(self, scenario_file: Path, output_name: str = None):
        """Generate AquaCrop input files from scenario JSON"""
        
        print(f"\n{'='*70}")
        print(f"GENERATING DATA FROM SCENARIO: {scenario_file.name}")
        print(f"{'='*70}")
        
        # Load scenario
        with open(scenario_file) as f:
            config = json.load(f)
        
        input_data = ScenariosSimulationInput(**config)
        
        # Get first season (can extend to multiple later)
        season = input_data.seasons[0]
        soil = input_data.soils[0]
        
        print(f"\n📍 Location: {input_data.point.latitude}°N, {input_data.point.longitude}°E")
        print(f"📅 Period: {season.simulation_start} to {season.simulation_end}")
        print(f"🌱 Crop: {input_data.crop_file[:50]}...")
        
        # Parse crop
        _, crop_index, crop_params = loads_crop_file(input_data.crop_file)
        
        # Fetch weather
        print(f"\n🌦️  Fetching weather from NASA POWER...")
        point = input_data.point
        altitude = getattr(point, 'altitude', 0)
        weather_data = get_weather_data(
            point.latitude,
            point.longitude,
            altitude,
            season.simulation_start,
            season.simulation_end,
        )
        print(f"   ✓ Got {len(weather_data)} days of weather data")
        
        # Get soil params
        soil_params = get_soil_params(soil)
        print(f"   ✓ Soil parameters calculated")
        
        # Create project
        print(f"\n📁 Creating AquaCrop project files...")
        project_ctx = AquacropProject(with_default=True)
        project = project_ctx.__enter__()
        
        try:
            # Write all files
            project.write_climate_files(season.simulation_start, weather_data)
            project.write_crop_file(crop_index, crop_params)
            project.write_fertility_management_file(input_data.fertility_stress)
            project.write_gwt_file(depth=input_data.gwt_depth, ec=input_data.gwt_ec)
            project.write_soil_file(soil_params)
            project.write_sw0_file(soil_params)
            project.write_calendar_file(season)
            project.write_project_file(season)
            project.write_daily_out_config()
            
            # Copy to output
            if output_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"sim_{timestamp}"
            
            output_path = self.outputs_dir / output_name
            if output_path.exists():
                shutil.rmtree(output_path)
            
            shutil.copytree(project.root, output_path)
            
            print(f"   ✓ Data saved to: {output_path.relative_to(self.base_dir)}")
            
            return output_path
            
        finally:
            project_ctx.__exit__(None, None, None)
    
    
    def run_bmi_simulation(self, data_path: Path, visualize: bool = True):
        """Run BMI simulation with generated data"""
        
        print(f"\n{'='*70}")
        print(f"RUNNING BMI SIMULATION")
        print(f"{'='*70}")
        
        model = AquaCrop()
        config_file = str(data_path / "LIST" / "project.PRO")
        
        print(f"\n🚀 Initializing model: {config_file}")
        model.initialize(config_file)
        
        # Get simulation info
        start_time = model.get_start_time()
        end_time = model.get_end_time()
        time_step = model.get_time_step()
        n_steps = int((end_time - start_time) / time_step)
        
        print(f"   Duration: {n_steps} days")
        print(f"   Time: {start_time} to {end_time}")
        
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
            
            # Get values
            model.get_value("crop__canopy_cover", dest)
            results['canopy_cover'].append(dest[0])
            
            model.get_value("crop__biomass", dest)
            results['biomass'].append(dest[0])
            
            model.get_value("crop__yield", dest)
            results['yield'].append(dest[0])
            
            model.get_value("soil__moisture", dest)
            results['soil_moisture'].append(dest[0])
            
            results['time'].append(current_time)
            
            # Progress
            if step % 30 == 0:
                cc = results['canopy_cover'][-1]
                bio = results['biomass'][-1]
                yld = results['yield'][-1]
                print(f"   Day {current_time:.0f}/{end_time:.0f} - "
                      f"CC: {cc:.1f}%, Bio: {bio:.1f} t/ha, Yield: {yld:.1f} t/ha")
            
            # Update
            if current_time < end_time:
                model.update()
        
        model.finalize()
        print("   ✓ Simulation complete")
        
        # Convert to arrays
        for key in results:
            results[key] = np.array(results[key])
        
        # Print stats
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Max canopy cover:  {np.max(results['canopy_cover']):.2f}%")
        print(f"   Final biomass:     {results['biomass'][-1]:.2f} ton/ha")
        print(f"   Final yield:       {results['yield'][-1]:.2f} ton/ha")
        print(f"   Avg soil moisture: {np.mean(results['soil_moisture']):.2f} mm")
        
        # Visualize
        if visualize:
            self.visualize_results(results, data_path.name)
        
        return results
    
    
    def visualize_results(self, results, title_suffix=""):
        """Create visualization of simulation results"""
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'AquaCrop BMI Simulation - {title_suffix}', 
                     fontsize=16, fontweight='bold')
        
        time = results['time']
        
        # Canopy Cover
        ax = axes[0, 0]
        ax.plot(time, results['canopy_cover'], 'g-', linewidth=2)
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Canopy Cover (%)')
        ax.set_title('Crop Canopy Development', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Biomass
        ax = axes[0, 1]
        ax.plot(time, results['biomass'], 'b-', linewidth=2)
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Biomass (ton/ha)')
        ax.set_title('Biomass Accumulation', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Yield
        ax = axes[1, 0]
        ax.plot(time, results['yield'], 'orange', linewidth=2)
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Yield (ton/ha)')
        ax.set_title('Crop Yield Development', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Soil Moisture
        ax = axes[1, 1]
        ax.plot(time, results['soil_moisture'], 'brown', linewidth=2)
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Soil Moisture (mm)')
        ax.set_title('Root Zone Soil Moisture', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        plt.tight_layout()
        
        # Save
        output_file = self.outputs_dir / f"plot_{title_suffix}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n💾 Plot saved: {output_file.relative_to(self.base_dir)}")
        
        plt.show()
    
    
    def run_full_pipeline(self, scenario_file: Path, output_name: str = None):
        """Complete pipeline: generate data → run BMI → visualize"""
        
        # Step 1: Generate data
        data_path = self.generate_data(scenario_file, output_name)
        
        # Step 2: Run simulation
        results = self.run_bmi_simulation(data_path)
        
        print(f"\n{'='*70}")
        print("✅ PIPELINE COMPLETE!")
        print(f"{'='*70}")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Run AquaCrop BMI simulations with dynamic data generation'
    )
    parser.add_argument(
        'scenario',
        type=Path,
        help='Path to scenario JSON file (relative to scenarios/ or absolute)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output directory name (default: auto-generated timestamp)'
    )
    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Skip visualization'
    )
    
    args = parser.parse_args()
    
    # Setup
    simulator = AquaCropSimulator()
    
    # Resolve scenario path
    if not args.scenario.is_absolute():
        scenario_file = simulator.scenarios_dir / args.scenario
    else:
        scenario_file = args.scenario
    
    if not scenario_file.exists():
        print(f"❌ Error: Scenario file not found: {scenario_file}")
        return 1
    
    # Run pipeline
    try:
        simulator.run_full_pipeline(scenario_file, args.output)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())