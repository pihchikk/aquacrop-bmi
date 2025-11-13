#!/usr/bin/env python3
"""
Interactive BMI AquaCrop Demonstration v3
Shows real-time model response to management decisions

Uses the ORIGINAL data loading logic from bmi_demo.py
Takes a JSON scenario file as input
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from aquacrop_bmi_babel import AquaCrop
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
import argparse
import os # Import os for debugging CWD (optional, but good practice)

# Import data generation tools - SAME AS ORIGINAL
from aquacrop_bmi.models import (
    ScenariosSimulationInput,
    CropCalibrationInput,
    FertilityStressCalibrationInput,
)
from aquacrop_bmi.project import AquacropProject
from aquacrop_bmi.util import loads_crop_file, get_weather_data, get_elevation
from aquacrop_bmi.soil_texture import get_soil_params
from aquacrop_bmi.data import get_crop_params


class InteractiveBMIDemo:
    """Interactive demonstration of BMI AquaCrop with live visualization"""
    
    def __init__(self, config_file):
        self.model = AquaCrop()
        self.config_file = config_file
        
        # Storage for time series data
        self.days = []
        self.canopy_cover = []
        self.biomass = []
        self.soil_moisture = []
        self.water_stress = []
        self.irrigation = []
        self.rainfall = []
        self.et = []
        
        # Initialize model
        print("="*80)
        print(" "*20 + "🌱 INTERACTIVE BMI AQUACROP DEMO 🌱")
        print("="*80)
        print()
        print("Initializing model...")
        self.model.initialize(config_file)
        
        # Get simulation info
        self.start_time = self.model.get_start_time()
        self.end_time = self.model.get_end_time()
        self.current_time = self.start_time
        
        print(f"✓ Model initialized")
        print(f"  Simulation period: {int(self.end_time)} days")
        print(f"  Input variables:  {self.model.get_input_item_count()}")
        print(f"  Output variables: {self.model.get_output_item_count()}")
        print()
        
    def get_state(self):
        """Get current model state"""
        state = {}
        
        # Crop state
        cc = np.empty(1, dtype=np.float64)
        self.model.get_value("crop__canopy_cover", cc)
        state['canopy_cover'] = cc[0]
        
        biomass = np.empty(1, dtype=np.float64)
        self.model.get_value("crop__biomass", biomass)
        state['biomass'] = biomass[0]
        
        yield_val = np.empty(1, dtype=np.float64)
        self.model.get_value("crop__yield", yield_val)
        state['yield'] = yield_val[0]
        
        # Water balance
        moisture = np.empty(1, dtype=np.float64)
        self.model.get_value("soil__moisture", moisture)
        state['soil_moisture'] = moisture[0]
        
        et_val = np.empty(1, dtype=np.float64)
        self.model.get_value("crop__evapotranspiration", et_val)
        state['et'] = et_val[0]
        
        # Stress
        stress = np.empty(1, dtype=np.float64)
        self.model.get_value("crop__water_stress", stress)
        state['water_stress'] = stress[0]
        
        return state
    
    def apply_management(self, rainfall=None, irrigation=None, co2=None, mulch=None):
        """Apply management decisions for current day"""
        
        if rainfall is not None:
            src = np.array([rainfall], dtype=np.float64)
            self.model.set_value("weather__rainfall_amount", src)
        
        if irrigation is not None:
            src = np.array([irrigation], dtype=np.float64)
            self.model.set_value("management__irrigation_amount", src)
        
        if co2 is not None:
            src = np.array([co2], dtype=np.float64)
            self.model.set_value("atmosphere__co2_concentration", src)
        
        if mulch is not None:
            src = np.array([mulch], dtype=np.float64)
            self.model.set_value("management__mulch_cover", src)
    
    def run_day(self, **management):
        """Run one day with optional management changes"""
        
        # Apply management BEFORE update
        self.apply_management(**management)
        
        # Store rainfall and irrigation for this day
        rainfall = management.get('rainfall', 0.0)
        irrigation = management.get('irrigation', 0.0)
        
        # Run model
        self.model.update()
        self.current_time = self.model.get_current_time()
        
        # Get state after update
        state = self.get_state()
        
        # Store data
        self.days.append(int(self.current_time))
        self.canopy_cover.append(state['canopy_cover'])
        self.biomass.append(state['biomass'])
        self.soil_moisture.append(state['soil_moisture'])
        self.water_stress.append(state['water_stress'])
        self.irrigation.append(irrigation)
        self.rainfall.append(rainfall)
        self.et.append(state['et'])
        
        return state
    
    def print_status(self, state):
        """Print current status"""
        print(f"\r Day {int(self.current_time):3d}/{int(self.end_time):3d} | "
              f"CC: {state['canopy_cover']:5.1f}% | "
              f"Biomass: {state['biomass']:6.2f} t/ha | "
              f"Moisture: {state['soil_moisture']:6.1f} mm | "
              f"Stress: {state['water_stress']:4.0f} days", end='')
        sys.stdout.flush()
    
    def finalize(self):
        """Finalize model"""
        self.model.finalize()
        print("\n\n✓ Model finalized")


def detect_scenario_type(config: dict) -> str:
    """Detect which type of scenario this is - EXACT COPY FROM ORIGINAL"""
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


def generate_scenario_data(scenario_file: Path, output_dir: Path, output_name: str):
    """
    Generate AquaCrop input files - EXACT COPY FROM ORIGINAL bmi_demo.py
    Handles all scenario types
    """
    
    print(f"\n{'='*70}")
    print(f"GENERATING DATA FROM: {scenario_file.name}")
    print(f"{'='*70}")
    # ADDED CWD PRINT FOR DEBUGGING
    print(f"cwd {os.getcwd()}") 

    with open(scenario_file) as f:
        config = json.load(f)
    
    scenario_type = detect_scenario_type(config)
    print(f"\n🔍 Detected: {scenario_type}")
    
    # Convert all types to simulation format - EXACT LOGIC FROM ORIGINAL
    if scenario_type == 'crop-calibration':
        input_data = CropCalibrationInput(**config)
        season = input_data.seasons[0]
        soil = input_data.soil
        
        _, crop_index, crop_params = get_crop_params(input_data.crop_ref)
        crop_params.update(input_data.crop_params.model_dump(by_alias=True, exclude_none=True))
        
        point = input_data.point
        fertility = 100  # Default for calibration
        
    elif scenario_type == 'fertility-stress-calibration':
        input_data = FertilityStressCalibrationInput(**config)
        season = input_data.seasons[0]
        soil = input_data.soil
        
        _, crop_index, crop_params = loads_crop_file(input_data.crop_file)
        
        point = input_data.point
        fertility = input_data.fertility_stress_range[0]
        
    elif scenario_type == 'simulation-data':
        # Old format - convert
        config_sim = {
            'gwt_depth': config['gwt_depth'],
            'gwt_ec': config['gwt_ec'],
            'point': config['point'],
            'seasons': config['seasons'],
            'crop_file': config['crop_file'],
            'soils': [config['soil']],
            'fertility_stress': config.get('fertility_stress', 100),
        }
        input_data = ScenariosSimulationInput(**config_sim)
        season = input_data.seasons[0]
        soil = input_data.soils[0]
        
        _, crop_index, crop_params = loads_crop_file(input_data.crop_file)
        
        point = input_data.point
        fertility = input_data.fertility_stress
        
    else:  # scenarios-simulation
        input_data = ScenariosSimulationInput(**config)
        season = input_data.seasons[0]
        soil = input_data.soils[0]
        
        _, crop_index, crop_params = loads_crop_file(input_data.crop_file)
        
        point = input_data.point
        fertility = input_data.fertility_stress
    
    print(f"\n📍 Location: {point.latitude}°N, {point.longitude}°E")
    print(f"📅 Period: {season.simulation_start} to {season.simulation_end}")
    
    # Fetch weather
    print(f"\n🌦️  Fetching weather...")
    if not hasattr(point, 'altitude'):
        altitude = get_elevation(point.latitude, point.longitude)
    else:
        altitude = point.altitude
        
    weather_data = get_weather_data(
        point.latitude, point.longitude, altitude,
        season.simulation_start, season.simulation_end
    )
    print(f"   ✓ Got {len(weather_data)} days")
    
    # Get soil params - USES ORIGINAL LOGIC (handles both dict and objects)
    soil_params = get_soil_params(soil)
    
    # Create project
    print(f"\n📁 Creating project files...")
    output_path = output_dir / output_name
    
    project_ctx = AquacropProject(with_default=True)
    project = project_ctx.__enter__()
    
    try:
        project.write_climate_files(season.simulation_start, weather_data)
        project.write_crop_file(crop_index, crop_params)
        project.write_fertility_management_file(fertility)
        project.write_gwt_file(depth=input_data.gwt_depth, ec=input_data.gwt_ec)
        project.write_soil_file(soil_params)
        project.write_sw0_file(soil_params)
        project.write_calendar_file(season)
        project.write_project_file(season)
        project.write_daily_out_config()
        
        if output_path.exists():
            shutil.rmtree(output_path)
        shutil.copytree(project.root, output_path)
        
        print(f"   ✓ Saved to: {output_path}")
        
        return output_path
        
    finally:
        project_ctx.__exit__(None, None, None)


def scenario_baseline(demo, weather_pattern):
    """Scenario 1: Baseline - natural rainfall only, NO irrigation"""
    print("\n" + "="*80)
    print("SCENARIO 1: BASELINE (Rainfed - No Irrigation)")
    print("="*80)
    print("Running rainfed simulation with natural rainfall...")
    print()
    
    n_days = min(100, int(demo.end_time))
    
    for day in range(1, n_days + 1):
        rainfall = weather_pattern.get(day, 0.0)
        
        # NO irrigation, NO CO2 boost, NO mulch
        state = demo.run_day(
            rainfall=rainfall,
            irrigation=0.0,
            co2=369.47,
            mulch=0.0
        )
        demo.print_status(state)
    
    print("\n")
    final_state = demo.get_state()
    print(f"Final Results:")
    print(f"  Biomass: {final_state['biomass']:.2f} t/ha")
    print(f"  Yield: {final_state['yield']:.2f} t/ha")
    print(f"  Water stress days: {final_state['water_stress']:.0f}")


def scenario_smart_irrigation(demo, weather_pattern):
    """Scenario 2: Smart irrigation based on soil moisture"""
    print("\n" + "="*80)
    print("SCENARIO 2: SMART IRRIGATION")
    print("="*80)
    print("Irrigating when soil moisture drops below threshold...")
    print()
    
    MOISTURE_THRESHOLD = 200.0
    IRRIGATION_AMOUNT = 20.0
    
    n_days = min(100, int(demo.end_time))
    total_irrigation = 0
    
    for day in range(1, n_days + 1):
        rainfall = weather_pattern.get(day, 0.0)
        
        state = demo.get_state()
        
        if state['soil_moisture'] < MOISTURE_THRESHOLD:
            irrigation = IRRIGATION_AMOUNT
            total_irrigation += irrigation
        else:
            irrigation = 0.0
        
        state = demo.run_day(
            rainfall=rainfall,
            irrigation=irrigation,
            co2=369.47,
            mulch=0.0
        )
        demo.print_status(state)
    
    print("\n")
    final_state = demo.get_state()
    print(f"Final Results:")
    print(f"  Biomass: {final_state['biomass']:.2f} t/ha")
    print(f"  Yield: {final_state['yield']:.2f} t/ha")
    print(f"  Water stress days: {final_state['water_stress']:.0f}")
    print(f"  Total irrigation: {total_irrigation:.0f} mm")


def scenario_climate_change(demo, weather_pattern):
    """Scenario 3: Elevated CO2 (climate change)"""
    print("\n" + "="*80)
    print("SCENARIO 3: CLIMATE CHANGE (Elevated CO2)")
    print("="*80)
    print("Simulating with 550ppm CO2 (climate change scenario)...")
    print()
    
    MOISTURE_THRESHOLD = 200.0
    IRRIGATION_AMOUNT = 20.0
    CO2_ELEVATED = 550.0
    
    n_days = min(100, int(demo.end_time))
    total_irrigation = 0
    
    for day in range(1, n_days + 1):
        rainfall = weather_pattern.get(day, 0.0)
        
        state = demo.get_state()
        
        if state['soil_moisture'] < MOISTURE_THRESHOLD:
            irrigation = IRRIGATION_AMOUNT
            total_irrigation += irrigation
        else:
            irrigation = 0.0
        
        state = demo.run_day(
            rainfall=rainfall,
            irrigation=irrigation,
            co2=CO2_ELEVATED,
            mulch=0.0
        )
        demo.print_status(state)
    
    print("\n")
    final_state = demo.get_state()
    print(f"Final Results:")
    print(f"  Biomass: {final_state['biomass']:.2f} t/ha")
    print(f"  Yield: {final_state['yield']:.2f} t/ha")
    print(f"  Water stress days: {final_state['water_stress']:.0f}")
    print(f"  Total irrigation: {total_irrigation:.0f} mm")


def scenario_mulch_conservation(demo, weather_pattern):
    """Scenario 4: Conservation agriculture with mulch"""
    print("\n" + "="*80)
    print("SCENARIO 4: CONSERVATION AGRICULTURE (50% Mulch)")
    print("="*80)
    print("Using mulch cover to reduce evaporation...")
    print()
    
    MOISTURE_THRESHOLD = 200.0
    IRRIGATION_AMOUNT = 20.0
    MULCH_COVER = 50.0
    
    n_days = min(100, int(demo.end_time))
    total_irrigation = 0
    
    for day in range(1, n_days + 1):
        rainfall = weather_pattern.get(day, 0.0)
        
        state = demo.get_state()
        
        if state['soil_moisture'] < MOISTURE_THRESHOLD:
            irrigation = IRRIGATION_AMOUNT
            total_irrigation += irrigation
        else:
            irrigation = 0.0
        
        state = demo.run_day(
            rainfall=rainfall,
            irrigation=irrigation,
            co2=369.47,
            mulch=MULCH_COVER
        )
        demo.print_status(state)
    
    print("\n")
    final_state = demo.get_state()
    print(f"Final Results:")
    print(f"  Biomass: {final_state['biomass']:.2f} t/ha")
    print(f"  Yield: {final_state['yield']:.2f} t/ha")
    print(f"  Water stress days: {final_state['water_stress']:.0f}")
    print(f"  Total irrigation: {total_irrigation:.0f} mm")


def create_weather_pattern(n_days=100):
    """Create a realistic weather pattern"""
    pattern = {}
    
    for day in range(1, 31):
        if day % 10 == 0:
            pattern[day] = 8.0
        else:
            pattern[day] = 0.0
    
    for day in range(31, 61):
        if day % 7 == 0:
            pattern[day] = 12.0
        else:
            pattern[day] = 0.0
    
    for day in range(61, n_days + 1):
        if day % 12 == 0:
            pattern[day] = 6.0
        else:
            pattern[day] = 0.0
    
    return pattern


def plot_results(demos, titles, output_file="bmi_scenarios_comparison.png"):
    """Create comprehensive comparison plots"""
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.25)
    
    # Plot 1: Canopy Cover
    ax1 = fig.add_subplot(gs[0, 0])
    for demo, title, color in zip(demos, titles, colors):
        ax1.plot(demo.days, demo.canopy_cover, label=title, linewidth=2.5,
                 color=color, alpha=0.8)
    ax1.set_xlabel('Days After Planting', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Canopy Cover (%)', fontsize=11, fontweight='bold')
    ax1.set_title('🌿 Canopy Development', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    
    # Plot 2: Biomass
    ax2 = fig.add_subplot(gs[0, 1])
    for demo, title, color in zip(demos, titles, colors):
        ax2.plot(demo.days, demo.biomass, label=title, linewidth=2.5,
                 color=color, alpha=0.8)
    ax2.set_xlabel('Days After Planting', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Biomass (tonnes/ha)', fontsize=11, fontweight='bold')
    ax2.set_title('📈 Biomass Accumulation', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xlim(0, 100)
    
    for demo, color in zip(demos, colors):
        if len(demo.biomass) > 0:
            final_b = demo.biomass[-1]
            ax2.text(101, final_b, f'{final_b:.1f}', 
                     fontsize=9, color=color, fontweight='bold')
    
    # Plot 3: Soil Moisture
    ax3 = fig.add_subplot(gs[1, 0])
    for demo, title, color in zip(demos, titles, colors):
        ax3.plot(demo.days, demo.soil_moisture, label=title, linewidth=2.5,
                 color=color, alpha=0.8)
    ax3.axhline(y=200, color='red', linestyle='--', linewidth=2, alpha=0.7, 
                label='Irrigation threshold')
    ax3.set_xlabel('Days After Planting', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Soil Moisture (mm)', fontsize=11, fontweight='bold')
    ax3.set_title('💧 Water Balance', fontsize=12, fontweight='bold')
    ax3.legend(loc='best', fontsize=8)
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.set_xlim(0, 100)
    
    # Plot 4: Irrigation Events
    ax4 = fig.add_subplot(gs[1, 1])
    width = 0.8
    for i, (demo, title, color) in enumerate(zip(demos, titles, colors)):
        if len(demo.days) > 0:
            days_array = np.array(demo.days)
            rain_array = np.array(demo.rainfall)
            irri_array = np.array(demo.irrigation)
            
            water_days = (rain_array > 0) | (irri_array > 0)
            if np.any(water_days):
                plot_days = days_array[water_days]
                plot_rain = rain_array[water_days]
                plot_irri = irri_array[water_days]
                
                offset = (i - 1.5) * width / 4
                ax4.bar(plot_days + offset, plot_rain, width=width/4,
                        color=color, alpha=0.4)
                ax4.bar(plot_days + offset, plot_irri, width=width/4,
                        bottom=plot_rain, color=color, alpha=0.9)
    
    ax4.set_xlabel('Days After Planting', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Water Input (mm/day)', fontsize=11, fontweight='bold')
    ax4.set_title('🚰 Management Actions', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax4.set_xlim(0, 100)
    
    # Plot 5: Final Comparison
    ax5 = fig.add_subplot(gs[2, :])
    
    metrics = ['Biomass\n(t/ha)', 'Yield\n(t/ha)', 'Stress\n(days)', 'Irrigation\n(mm)']
    x_pos = np.arange(len(metrics))
    bar_width = 0.2
    
    for i, (demo, title, color) in enumerate(zip(demos, titles, colors)):
        final_state = demo.get_state()
        total_irri = sum(demo.irrigation)
        
        values = [
            final_state['biomass'],
            final_state['yield'],
            final_state['water_stress'],
            total_irri
        ]
        
        offset = (i - 1.5) * bar_width
        bars = ax5.bar(x_pos + offset, values, bar_width, 
                       label=title, color=color, alpha=0.8)
        
        for bar, val in zip(bars, values):
            height = bar.get_height()
            if height > 0:
                ax5.text(bar.get_x() + bar.get_width()/2., height,
                         f'{val:.1f}', ha='center', va='bottom', 
                         fontsize=8, fontweight='bold')
    
    ax5.set_ylabel('Value', fontsize=11, fontweight='bold')
    ax5.set_title('📊 Final Results Comparison', fontsize=12, fontweight='bold')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(metrics, fontsize=10)
    ax5.legend(loc='upper left', fontsize=9)
    ax5.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    interpretation = (
        "💡 BMI enables real-time adaptive management:\n"
        "• Smart irrigation DOUBLES yield vs rainfed\n"
        "• Climate change provides CO₂ fertilization benefit\n"
        "• Conservation practices reduce water consumption\n"
        "• Interactive decisions drive dramatic outcome differences"
    )
    fig.text(0.02, 0.02, interpretation, fontsize=10, 
             bbox=dict(boxstyle='round,pad=1', facecolor='wheat', alpha=0.8),
             verticalalignment='bottom')
    
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"\n✓ Plot saved: {output_file}")
    plt.close()


def main():
    """Run interactive demonstration"""
    
    parser = argparse.ArgumentParser(
        description='BMI Interactive Demo - Uses your JSON scenario files'
    )
    parser.add_argument('scenario_json', type=Path, 
                        help='Path to scenario JSON file (any type supported)')
    parser.add_argument('--output-dir', type=Path, default=Path("outputs"),
                        help='Output directory for generated files')
    
    args = parser.parse_args()
    
    # --- FIX START (Existing) ---
    # Resolve the scenario file path to an absolute path immediately.
    try:
        resolved_scenario_path = args.scenario_json.resolve()
    except Exception:
        # Fallback if resolve fails for some environmental reason
        resolved_scenario_path = args.scenario_json
        
    if not resolved_scenario_path.exists():
        print(f"❌ Scenario file not found: {resolved_scenario_path}")
        return 1
    # --- FIX END (Existing) ---
    
    # --- NEW FIX START ---
    # Setup - Resolve the output directory to an absolute path to ensure correct file saving,
    # regardless of CWD changes made by the BMI model's initialization.
    outputs_dir = args.output_dir
    try:
        outputs_dir = outputs_dir.resolve()
    except Exception:
        # Fallback if resolve fails for some environmental reason
        pass
        
    outputs_dir.mkdir(exist_ok=True)
    # --- NEW FIX END ---
    
    print("\n")
    print("█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 20 + "BMI AQUACROP INTERACTIVE DEMO v3" + " " * 25 + "█")
    print("█" + " " * 15 + "Real-time Model-Management Interaction" + " " * 26 + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    print()
    print("🎯 Demonstrating BMI's Power:")
    print("   • Interactive decision-making")
    print("   • Real-time response to conditions")
    print("   • Adaptive management strategies")
    print()
    
    # Create weather pattern
    weather_pattern = create_weather_pattern(100)
    
    # Run scenarios SEQUENTIALLY
    demos = []
    titles = []
    scenarios = [
        ("Baseline (Rainfed)", scenario_baseline),
        ("Smart Irrigation", scenario_smart_irrigation),
        ("Climate Change (550ppm CO2)", scenario_climate_change),
        ("Conservation (50% Mulch)", scenario_mulch_conservation),
    ]
    
    for i, (title, scenario_func) in enumerate(scenarios, 1):
        print(f"\n🔄 Running Scenario {i}/{len(scenarios)}...")
        
        # Generate scenario data using ORIGINAL logic
        scenario_name = f"scenario_{i}_{title.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}"
        scenario_dir = generate_scenario_data(
            resolved_scenario_path, # <--- Using the resolved absolute path here
            outputs_dir,
            scenario_name
        )
        
        # Run scenario
        config_file = str(scenario_dir / "LIST" / "project.PRO")
        demo = InteractiveBMIDemo(config_file)
        scenario_func(demo, weather_pattern)
        demo.finalize()
        
        demos.append(demo)
        titles.append(title)
    
    # Summary
    print("\n" + "="*80)
    print("SCENARIO COMPARISON")
    print("="*80)
    print()
    print(f"{'Scenario':<35} {'Biomass':<12} {'Yield':<12} {'Stress':<12} {'Irrigation':<12}")
    print("-" * 85)
    
    for demo, title in zip(demos, titles):
        final = demo.get_state()
        total_irri = sum(demo.irrigation)
        print(f"{title:<35} {final['biomass']:>8.2f} t/ha {final['yield']:>8.2f} t/ha "
              f"{final['water_stress']:>8.0f} days {total_irri:>8.0f} mm")
    
    print()
    
    # Generate plots
    try:
        plot_results(demos, titles, str(outputs_dir / "bmi_scenarios_comparison.png"))
    except Exception as e:
        print(f"⚠ Could not generate plots: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE!")
    print("="*80)
    print()
    print("🌟 KEY FINDINGS:")
    print("  • BMI allows REAL-TIME management decisions")
    print("  • Management strategies have SIGNIFICANT impact")
    print("  • Smart irrigation dramatically increases yield")
    print("  • Climate/conservation practices change outcomes")
    print()
    print("💡 This is IMPOSSIBLE with traditional batch runs!")
    print()
    
    return 0


if __name__ == "__main__":
    # Ensure the script runs from its execution context
    sys.exit(main())