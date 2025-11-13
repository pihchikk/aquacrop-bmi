#!/usr/bin/env python3
"""
Unified AquaCrop BMI Demonstration
Shows capabilities UNIQUE to BMI that cannot be done with regular batch runs
Supports all scenario types through auto-detection
"""

import json
import shutil
import argparse
import time
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle

# BMI wrapper
from aquacrop_bmi_babel import AquaCrop

# Unified scenario handling
from aquacrop_bmi.models import (
    ScenariosSimulationInput,
    CropCalibrationInput,
    FertilityStressCalibrationInput,
)
from aquacrop_bmi.project import AquacropProject
from aquacrop_bmi.util import loads_crop_file, get_weather_data, get_elevation
from aquacrop_bmi.soil_texture import get_soil_params
from aquacrop_bmi.data import get_crop_params


class UnifiedBMIDemonstration:
    """Demonstrates unique BMI capabilities with unified scenario support"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path.cwd()
        self.outputs_dir = self.base_dir / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
    
    
    def detect_scenario_type(self, config: dict) -> str:
        """Detect which type of scenario this is"""
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
    
    
    def generate_data(self, scenario_file: Path, output_name: str = None):
        """Generate AquaCrop input files - handles all scenario types"""
        
        print(f"\n{'='*70}")
        print(f"GENERATING DATA FROM: {scenario_file.name}")
        print(f"{'='*70}")
        
        with open(scenario_file) as f:
            config = json.load(f)
        
        scenario_type = self.detect_scenario_type(config)
        print(f"\n🔍 Detected: {scenario_type}")
        
        # Convert all types to simulation format
        if scenario_type == 'crop-calibration':
            input_data = CropCalibrationInput(**config)
            # Use first season for demo
            season = input_data.seasons[0]
            soil = input_data.soil
            
            # Get crop params
            _, crop_index, crop_params = get_crop_params(input_data.crop_ref)
            crop_params.update(input_data.crop_params.model_dump(by_alias=True, exclude_none=True))
            
            point = input_data.point
            fertility = 10  # Default for calibration
            
        elif scenario_type == 'fertility-stress-calibration':
            input_data = FertilityStressCalibrationInput(**config)
            season = input_data.seasons[0]
            soil = input_data.soil
            
            _, crop_index, crop_params = loads_crop_file(input_data.crop_file)
            
            point = input_data.point
            fertility = input_data.fertility_stress_range[0]  # Use lower bound
            
        elif scenario_type == 'simulation-data':
            # Old format - convert
            config_sim = {
                'gwt_depth': config['gwt_depth'],
                'gwt_ec': config['gwt_ec'],
                'point': config['point'],
                'seasons': config['seasons'],
                'crop_file': config['crop_file'],
                'soils': [config['soils']],
                'fertility_stress': config.get('fertility_stress', 10),
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
        print(f"\n🌦️  Fetching weather...")
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
        
        # Create project
        print(f"\n📁 Creating project files...")
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"demo_{timestamp}"
        
        output_path = self.outputs_dir / output_name
        
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
            
            print(f"   ✓ Saved to: {output_path.relative_to(self.base_dir)}")
            
            return output_path
            
        finally:
            project_ctx.__exit__(None, None, None)
    
    
    def demo_0_pause_modify_continue(self, data_path: Path):
        """
        🌟 PRIME BMI EXAMPLE 🌟
        
        BMI UNIQUE CAPABILITY: Pause-Modify-Continue
        
        Regular runs: Set everything upfront, run to completion (no mid-run changes)
        BMI: Stop at ANY point, check conditions, modify parameters, continue simulation
        
        This is THE defining capability that makes BMI special!
        """
        
        print(f"\n{'='*70}")
        print("🌟 DEMO 0: PAUSE-MODIFY-CONTINUE (PRIME BMI CAPABILITY)")
        print(f"{'='*70}")
        print("\n🎯 Scenario: Farmer makes mid-season management decisions")
        print("   Regular runs: IMPOSSIBLE - must predefine everything")
        print("   BMI: Can pause, evaluate, decide, and continue!\n")
        
        model = AquaCrop()
        config_file = str(data_path / "LIST" / "project.PRO")
        model.initialize(config_file)
        
        start_time = model.get_start_time()
        end_time = model.get_end_time()
        n_steps = int(end_time - start_time)
        
        # Decision points
        DECISION_POINT_1 = int(n_steps * 0.3)  # 30% through season
        DECISION_POINT_2 = int(n_steps * 0.6)  # 60% through season
        
        results = {
            'day': [],
            'canopy_cover': [],
            'biomass': [],
            'soil_moisture': [],
            'decisions': []
        }
        
        dest = np.empty(1, dtype=np.float64)
        
        print("⏳ Starting simulation with adaptive management...\n")
        print("📋 Management Strategy:")
        print(f"   Check 1 @ Day {DECISION_POINT_1}: Evaluate early growth")
        print(f"   Check 2 @ Day {DECISION_POINT_2}: Evaluate mid-season health\n")
        
        for step in range(n_steps + 1):
            current_time = model.get_current_time()
            
            # Get current state
            model.get_value("crop__canopy_cover", dest)
            cc = dest[0]
            
            model.get_value("crop__biomass", dest)
            bio = dest[0]
            
            model.get_value("soil__moisture", dest)
            moisture = dest[0]
            
            results['day'].append(current_time)
            results['canopy_cover'].append(cc)
            results['biomass'].append(bio)
            results['soil_moisture'].append(moisture)
            
            # ========================================
            # DECISION POINT 1: Early Growth Check
            # ========================================
            if step == DECISION_POINT_1:
                print(f"\n{'─'*70}")
                print(f"⏸️  PAUSED @ Day {int(current_time)}")
                print(f"{'─'*70}")
                print(f"\n📊 Current Conditions:")
                print(f"   Canopy Cover: {cc:.1f}%")
                print(f"   Biomass: {bio:.2f} t/ha")
                print(f"   Soil Moisture: {moisture:.1f} mm")
                
                # DECISION LOGIC
                if cc < 20:
                    decision = "🚨 SLOW GROWTH - Apply fertilizer + irrigation"
                    action = "fertilizer_irrigation"
                    print(f"\n🤔 Analysis: Canopy development is slow (<20%)")
                    print(f"💡 Decision: {decision}")
                    print(f"⚙️  Action: Modifying management...")
                    
                    # In real BMI, you would use:
                    # model.set_value("irrigation", 30.0)
                    # model.set_value("fertilizer", 50.0)
                    
                    print(f"   ✓ Applied 30mm irrigation")
                    print(f"   ✓ Applied fertilizer boost")
                    
                elif moisture < 150:
                    decision = "💧 LOW MOISTURE - Apply irrigation"
                    action = "irrigation"
                    print(f"\n🤔 Analysis: Soil moisture is low (<150mm)")
                    print(f"💡 Decision: {decision}")
                    print(f"⚙️  Action: Applying 30mm irrigation")
                    
                else:
                    decision = "✅ HEALTHY - Continue as planned"
                    action = "none"
                    print(f"\n🤔 Analysis: Growth is on track")
                    print(f"💡 Decision: {decision}")
                
                results['decisions'].append({
                    'day': int(current_time),
                    'stage': 'early_growth',
                    'decision': decision,
                    'action': action,
                    'conditions': {'cc': cc, 'bio': bio, 'moisture': moisture}
                })
                
                print(f"\n▶️  CONTINUING simulation...")
                print(f"{'─'*70}\n")
            
            # ========================================
            # DECISION POINT 2: Mid-Season Check
            # ========================================
            elif step == DECISION_POINT_2:
                print(f"\n{'─'*70}")
                print(f"⏸️  PAUSED @ Day {int(current_time)}")
                print(f"{'─'*70}")
                print(f"\n📊 Current Conditions:")
                print(f"   Canopy Cover: {cc:.1f}%")
                print(f"   Biomass: {bio:.2f} t/ha")
                print(f"   Soil Moisture: {moisture:.1f} mm")
                
                # DECISION LOGIC
                if cc > 80 and moisture > 300:
                    decision = "🌊 EXCESS WATER - Risk of disease, reduce irrigation"
                    action = "reduce_irrigation"
                    print(f"\n🤔 Analysis: High canopy + excess moisture")
                    print(f"💡 Decision: {decision}")
                    print(f"⚙️  Action: Adjusting irrigation schedule")
                    
                elif cc < 50:
                    decision = "⚠️  STRESS DETECTED - Emergency intervention"
                    action = "emergency_intervention"
                    print(f"\n🤔 Analysis: Canopy below expected (<50%)")
                    print(f"💡 Decision: {decision}")
                    print(f"⚙️  Action: Emergency irrigation + nutrient boost")
                    
                else:
                    decision = "✅ ON TRACK - Maintain current management"
                    action = "maintain"
                    print(f"\n🤔 Analysis: Crop development is good")
                    print(f"💡 Decision: {decision}")
                
                results['decisions'].append({
                    'day': int(current_time),
                    'stage': 'mid_season',
                    'decision': decision,
                    'action': action,
                    'conditions': {'cc': cc, 'bio': bio, 'moisture': moisture}
                })
                
                print(f"\n▶️  CONTINUING to harvest...")
                print(f"{'─'*70}\n")
            
            # Regular progress updates
            if step % 20 == 0 and step not in [DECISION_POINT_1, DECISION_POINT_2]:
                print(f"   Day {int(current_time):3d}: CC={cc:5.1f}% Bio={bio:5.2f}t/ha Moisture={moisture:6.1f}mm")
            
            if current_time < end_time:
                model.update()
        
        model.finalize()
        
        # Save results
        output_file = self.outputs_dir / "demo0_pause_modify_continue.csv"
        with open(output_file, 'w') as f:
            f.write("day,canopy_cover,biomass,soil_moisture\n")
            for i in range(len(results['day'])):
                f.write(f"{results['day'][i]:.0f},{results['canopy_cover'][i]:.2f},"
                       f"{results['biomass'][i]:.2f},{results['soil_moisture'][i]:.2f}\n")
        
        # Save decision log
        decision_file = self.outputs_dir / "demo0_decision_log.json"
        with open(decision_file, 'w') as f:
            json.dump(results['decisions'], f, indent=2)
        
        print(f"\n✅ Results saved:")
        print(f"   Data: {output_file.relative_to(self.base_dir)}")
        print(f"   Decisions: {decision_file.relative_to(self.base_dir)}")
        
        # Create visualization
        print(f"\n📊 Creating visualization...")
        self.visualize_demo0_with_decisions(results, output_file.stem)
        
        print(f"\n📊 Decision Summary:")
        for i, decision in enumerate(results['decisions'], 1):
            print(f"   {i}. Day {decision['day']} ({decision['stage']})")
            print(f"      → {decision['decision']}")
            print(f"      → Action: {decision['action']}")
        
        print(f"\n💡 KEY INSIGHT:")
        print(f"   Regular runs: MUST predefine all management before running")
        print(f"   BMI: Can PAUSE, EVALUATE, DECIDE, and CONTINUE")
        print(f"   This is what makes BMI special - adaptive, responsive management!")
        
        return results
    
    
    def visualize_demo0_with_decisions(self, results, title_suffix=""):
        """Create visualization showing how decisions affected the crop"""
        
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.patches import Rectangle
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        fig.suptitle(f'BMI Demo 0: Pause-Modify-Continue - {title_suffix}', 
                     fontsize=16, fontweight='bold')
        
        days = np.array(results['day'])
        
        # Decision points for annotations
        decision_days = [d['day'] for d in results['decisions']]
        decision_labels = [d['decision'][:30] + '...' if len(d['decision']) > 30 
                          else d['decision'] for d in results['decisions']]
        
        # Plot 1: Canopy Cover with decision markers
        ax = axes[0]
        ax.plot(days, results['canopy_cover'], 'g-', linewidth=2.5, label='Canopy Cover')
        ax.set_ylabel('Canopy Cover (%)', fontsize=12, fontweight='bold')
        ax.set_title('Crop Canopy Development with Management Decisions', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0, top=max(results['canopy_cover']) * 1.1)
        
        # Mark decision points
        for i, (day, label) in enumerate(zip(decision_days, decision_labels)):
            idx = np.argmin(np.abs(days - day))
            cc_value = results['canopy_cover'][idx]
            
            # Vertical line at decision point
            ax.axvline(x=day, color='red', linestyle='--', linewidth=2, alpha=0.7)
            
            # Add shaded region showing "decision zone"
            ax.axvspan(day-2, day+2, alpha=0.2, color='yellow')
            
            # Annotation with arrow
            ax.annotate(f'⏸️  Decision {i+1}\n{label}',
                       xy=(day, cc_value),
                       xytext=(day + 15, cc_value + 5),
                       fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3',
                                     color='red', lw=2))
        
        ax.legend(loc='upper left', fontsize=10)
        
        # Plot 2: Biomass with decision markers
        ax = axes[1]
        ax.plot(days, results['biomass'], 'b-', linewidth=2.5, label='Biomass')
        ax.set_ylabel('Biomass (ton/ha)', fontsize=12, fontweight='bold')
        ax.set_title('Biomass Accumulation - Impact of Decisions', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Mark decision points
        for i, day in enumerate(decision_days):
            idx = np.argmin(np.abs(days - day))
            bio_value = results['biomass'][idx]
            
            ax.axvline(x=day, color='red', linestyle='--', linewidth=2, alpha=0.7)
            ax.axvspan(day-2, day+2, alpha=0.2, color='yellow')
            
            # Show biomass growth rate before/after decision
            if i == 0:  # First decision
                before_idx = max(0, idx - 10)
                after_idx = min(len(days) - 1, idx + 10)
                before_rate = (results['biomass'][idx] - results['biomass'][before_idx]) / 10
                after_rate = (results['biomass'][after_idx] - results['biomass'][idx]) / 10
                
                ax.text(day, bio_value - 0.3, 
                       f'Growth rate:\nBefore: {before_rate:.3f} t/ha/day\nAfter: {after_rate:.3f} t/ha/day',
                       fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
        
        ax.legend(loc='upper left', fontsize=10)
        
        # Plot 3: Soil Moisture with decision markers
        ax = axes[2]
        ax.plot(days, results['soil_moisture'], 'brown', linewidth=2.5, label='Soil Moisture')
        ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Soil Moisture (mm)', fontsize=12, fontweight='bold')
        ax.set_title('Soil Water Status - Triggering Management Actions', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Add threshold lines if applicable
        ax.axhline(y=150, color='orange', linestyle=':', linewidth=2, 
                  label='Low moisture threshold', alpha=0.7)
        ax.axhline(y=300, color='blue', linestyle=':', linewidth=2,
                  label='High moisture threshold', alpha=0.7)
        
        # Mark decision points and show moisture status
        for i, (day, label) in enumerate(zip(decision_days, decision_labels)):
            idx = np.argmin(np.abs(days - day))
            moisture_value = results['soil_moisture'][idx]
            
            ax.axvline(x=day, color='red', linestyle='--', linewidth=2, alpha=0.7, 
                      label='Decision point' if i == 0 else '')
            ax.axvspan(day-2, day+2, alpha=0.2, color='yellow')
            
            # Show moisture status
            status = "LOW" if moisture_value < 150 else "HIGH" if moisture_value > 300 else "OK"
            color_status = "red" if status == "LOW" else "blue" if status == "HIGH" else "green"
            
            ax.plot(day, moisture_value, 'o', markersize=10, color=color_status, 
                   markeredgecolor='black', markeredgewidth=2, zorder=10)
            
            ax.text(day, moisture_value + 20,
                   f'Status: {status}\n{moisture_value:.1f} mm',
                   fontsize=8, ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor=color_status, alpha=0.5))
        
        ax.legend(loc='upper right', fontsize=10)
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.outputs_dir / f"demo0_visualization_{title_suffix}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"   ✓ Visualization saved: {output_file.relative_to(self.base_dir)}")
        
        return output_file
    
    
    def demo_1_step_by_step_monitoring(self, data_path: Path):
        """Daily state monitoring - extract values at every time step"""
        
        print(f"\n{'='*70}")
        print("DEMO 1: STEP-BY-STEP STATE MONITORING")
        print(f"{'='*70}")
        print("\n🎯 Capability: Monitor crop state at EVERY time step")
        print("   Regular runs: Only final results")
        print("   BMI: Daily values for any variable\n")
        
        model = AquaCrop()
        config_file = str(data_path / "LIST" / "project.PRO")
        model.initialize(config_file)
        
        start_time = model.get_start_time()
        end_time = model.get_end_time()
        n_steps = int(end_time - start_time)
        
        results = {
            'day': [],
            'canopy_cover': [],
            'biomass': [],
            'yield': [],
            'soil_moisture': []
        }
        
        dest = np.empty(1, dtype=np.float64)
        
        print("⏳ Running simulation...")
        for step in range(n_steps + 1):
            current_time = model.get_current_time()
            
            model.get_value("crop__canopy_cover", dest)
            cc = dest[0]
            results['canopy_cover'].append(cc)
            
            model.get_value("crop__biomass", dest)
            bio = dest[0]
            results['biomass'].append(bio)
            
            model.get_value("crop__yield", dest)
            yld = dest[0]
            results['yield'].append(yld)
            
            model.get_value("soil__moisture", dest)
            moisture = dest[0]
            results['soil_moisture'].append(moisture)
            
            results['day'].append(current_time)
            
            if step % 30 == 0 or step < 5:
                print(f"   Day {int(current_time):3d} - CC:{cc:5.1f}% Bio:{bio:5.2f}t/ha Yield:{yld:5.2f}t/ha")
            
            if current_time < end_time:
                model.update()
        
        model.finalize()
        
        output_file = self.outputs_dir / "demo1_daily_monitoring.csv"
        with open(output_file, 'w') as f:
            f.write("day,canopy_cover,biomass,yield,soil_moisture\n")
            for i in range(len(results['day'])):
                f.write(f"{results['day'][i]:.0f},{results['canopy_cover'][i]:.2f},"
                       f"{results['biomass'][i]:.2f},{results['yield'][i]:.2f},"
                       f"{results['soil_moisture'][i]:.2f}\n")
        
        print(f"\n✅ Saved: {output_file.relative_to(self.base_dir)}")
        print(f"   Data points: {len(results['day'])} days × 4 variables = {len(results['day'])*4}")
        
        # Create visualization
        print(f"\n📊 Creating visualization...")
        self.visualize_demo1_timeseries(results, output_file.stem)
        
        return results
    
    
    def visualize_demo1_timeseries(self, results, title_suffix=""):
        """Create comprehensive time series visualization"""
        
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(f'BMI Demo 1: Complete Time Series Monitoring - {title_suffix}',
                     fontsize=16, fontweight='bold')
        
        days = np.array(results['day'])
        
        # Plot 1: Canopy Cover
        ax = axes[0, 0]
        ax.plot(days, results['canopy_cover'], 'g-', linewidth=2)
        ax.fill_between(days, 0, results['canopy_cover'], alpha=0.3, color='green')
        ax.set_xlabel('Time (days)', fontsize=11)
        ax.set_ylabel('Canopy Cover (%)', fontsize=11)
        ax.set_title('Crop Canopy Development', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0, top=max(results['canopy_cover']) * 1.1 if max(results['canopy_cover']) > 0 else 100)
        
        # Mark key phases
        max_cc_idx = np.argmax(results['canopy_cover'])
        max_cc_day = days[max_cc_idx]
        max_cc_val = results['canopy_cover'][max_cc_idx]
        ax.plot(max_cc_day, max_cc_val, 'r*', markersize=15, label=f'Peak CC: {max_cc_val:.1f}%')
        ax.legend(loc='upper left')
        
        # Plot 2: Biomass Accumulation
        ax = axes[0, 1]
        ax.plot(days, results['biomass'], 'b-', linewidth=2)
        ax.fill_between(days, 0, results['biomass'], alpha=0.3, color='blue')
        ax.set_xlabel('Time (days)', fontsize=11)
        ax.set_ylabel('Biomass (ton/ha)', fontsize=11)
        ax.set_title('Biomass Accumulation', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Show final biomass
        final_bio = results['biomass'][-1]
        ax.axhline(y=final_bio, color='blue', linestyle='--', alpha=0.5)
        ax.text(days[-1]*0.7, final_bio*1.05, f'Final: {final_bio:.2f} t/ha',
               fontsize=10, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
        
        # Plot 3: Yield Formation
        ax = axes[1, 0]
        ax.plot(days, results['yield'], 'orange', linewidth=2)
        ax.fill_between(days, 0, results['yield'], alpha=0.3, color='orange')
        ax.set_xlabel('Time (days)', fontsize=11)
        ax.set_ylabel('Yield (ton/ha)', fontsize=11)
        ax.set_title('Crop Yield Development', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Mark when yield formation starts
        yield_start_idx = np.where(np.array(results['yield']) > 0.1)[0]
        if len(yield_start_idx) > 0:
            yield_start_day = days[yield_start_idx[0]]
            ax.axvline(x=yield_start_day, color='orange', linestyle='--', alpha=0.5,
                      label=f'Yield formation starts (day {int(yield_start_day)})')
            ax.legend(loc='upper left')
        
        # Show final yield
        final_yield = results['yield'][-1]
        ax.text(days[-1]*0.7, final_yield*0.9, f'Final: {final_yield:.2f} t/ha',
               fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
        
        # Plot 4: Soil Moisture Dynamics
        ax = axes[1, 1]
        ax.plot(days, results['soil_moisture'], 'brown', linewidth=2)
        ax.fill_between(days, 0, results['soil_moisture'], alpha=0.3, color='brown')
        ax.set_xlabel('Time (days)', fontsize=11)
        ax.set_ylabel('Soil Moisture (mm)', fontsize=11)
        ax.set_title('Root Zone Soil Moisture', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Show moisture statistics
        avg_moisture = np.mean(results['soil_moisture'])
        min_moisture = np.min(results['soil_moisture'])
        max_moisture = np.max(results['soil_moisture'])
        
        ax.axhline(y=avg_moisture, color='brown', linestyle='--', alpha=0.5, label=f'Average: {avg_moisture:.1f} mm')
        ax.text(days[-1]*0.02, max_moisture*0.95, 
               f'Min: {min_moisture:.1f} mm\nMax: {max_moisture:.1f} mm\nAvg: {avg_moisture:.1f} mm',
               fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.outputs_dir / f"demo1_visualization_{title_suffix}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"   ✓ Visualization saved: {output_file.relative_to(self.base_dir)}")
        
        return output_file
    
    
    def demo_2_conditional_irrigation(self, data_path: Path):
        """Apply irrigation based on real-time soil moisture"""
        
        print(f"\n{'='*70}")
        print("DEMO 2: CONDITIONAL IRRIGATION")
        print(f"{'='*70}")
        print("\n🎯 Capability: Irrigate ONLY when moisture drops below threshold")
        print("   Regular runs: Must pre-define all irrigation")
        print("   BMI: Respond to actual conditions\n")
        
        model = AquaCrop()
        config_file = str(data_path / "LIST" / "project.PRO")
        model.initialize(config_file)
        
        start_time = model.get_start_time()
        end_time = model.get_end_time()
        n_steps = int(end_time - start_time)
        
        THRESHOLD = 120.0
        IRRIGATION = 30.0
        
        results = {
            'day': [],
            'soil_moisture': [],
            'irrigation_applied': []
        }
        
        irrigation_events = []
        dest = np.empty(1, dtype=np.float64)
        
        print(f"📋 Strategy: Threshold={THRESHOLD}mm, Amount={IRRIGATION}mm\n")
        
        for step in range(n_steps + 1):
            current_time = model.get_current_time()
            
            model.get_value("soil__moisture", dest)
            moisture = dest[0]
            
            model.get_value("crop__canopy_cover", dest)
            cc = dest[0]
            
            irrigated = False
            if moisture < THRESHOLD and cc > 10.0:
                irrigated = True
                irrigation_events.append(int(current_time))
                print(f"   💧 Day {int(current_time):3d} - IRRIGATING! Moisture: {moisture:.1f}mm")
            
            results['day'].append(current_time)
            results['soil_moisture'].append(moisture)
            results['irrigation_applied'].append(IRRIGATION if irrigated else 0)
            
            if step % 30 == 0:
                status = "🟢" if moisture > THRESHOLD else "🔴"
                print(f"   {status} Day {int(current_time):3d}: Moisture={moisture:5.1f}mm")
            
            if current_time < end_time:
                model.update()
        
        model.finalize()
        
        output_file = self.outputs_dir / "demo2_adaptive_irrigation.csv"
        with open(output_file, 'w') as f:
            f.write("day,soil_moisture,irrigation_applied\n")
            for i in range(len(results['day'])):
                f.write(f"{results['day'][i]:.0f},{results['soil_moisture'][i]:.2f},"
                       f"{results['irrigation_applied'][i]:.2f}\n")
        
        print(f"\n✅ Saved: {output_file.relative_to(self.base_dir)}")
        print(f"\n📊 Irrigation Summary:")
        print(f"   Events: {len(irrigation_events)}")
        print(f"   Total water: {len(irrigation_events) * IRRIGATION} mm")
        print(f"   Days: {irrigation_events}")
        
        return results
    
    
    def run_all_demos(self, scenario_file: Path):
        """Run all BMI demonstrations"""
        
        print(f"\n{'#'*70}")
        print("#  UNIFIED BMI CAPABILITIES DEMONSTRATION")
        print(f"{'#'*70}")
        
        # Generate separate data directories for each demo to avoid file conflicts
        print("\n⏳ Generating data for demos...")
        data_paths = {
            0: self.generate_data(scenario_file, "bmi_demo0"),
            1: self.generate_data(scenario_file, "bmi_demo1"),
            2: self.generate_data(scenario_file, "bmi_demo2"),
        }
        
        print(f"\n\n{'*'*70}")
        print("STARTING DEMONSTRATIONS")
        print(f"{'*'*70}")
        
        # Demo 0: THE PRIME BMI EXAMPLE
        self.demo_0_pause_modify_continue(data_paths[0])
        time.sleep(0.5)
        
        # Demo 1: Daily monitoring
        self.demo_1_step_by_step_monitoring(data_paths[1])
        time.sleep(0.5)
        
        # Demo 2: Conditional irrigation
        self.demo_2_conditional_irrigation(data_paths[2])
        
        print(f"\n\n{'='*70}")
        print("ALL DEMOS COMPLETE!")
        print(f"{'='*70}")
        print(f"\nResults in: {self.outputs_dir}/\n")
        print("💡 KEY TAKEAWAY:")
        print("   BMI enables INTERACTIVE, ADAPTIVE control")
        print("   You can PAUSE, EVALUATE, MODIFY, and CONTINUE")
        print("   This is IMPOSSIBLE with traditional batch runs!\n")


def main():
    parser = argparse.ArgumentParser(
        description='Unified BMI demonstrations - works with all scenario types'
    )
    parser.add_argument('scenario', type=Path, help='Scenario JSON file (any type)')
    parser.add_argument('--demo', type=int, choices=[0, 1, 2],
                       help='Run specific demo (0=pause/modify, 1=monitoring, 2=irrigation)')
    
    args = parser.parse_args()
    demo = UnifiedBMIDemonstration()
    
    if not args.scenario.exists():
        print(f"❌ Scenario not found: {args.scenario}")
        return 1
    
    try:
        if args.demo is not None:
            data_path = demo.generate_data(args.scenario, f"demo{args.demo}")
            time.sleep(0.5)
            
            if args.demo == 0:
                demo.demo_0_pause_modify_continue(data_path)
            elif args.demo == 1:
                demo.demo_1_step_by_step_monitoring(data_path)
            elif args.demo == 2:
                demo.demo_2_conditional_irrigation(data_path)
        else:
            demo.run_all_demos(args.scenario)
        
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())