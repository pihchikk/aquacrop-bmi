#!/usr/bin/env python3
"""
Simple BMI AquaCrop Interactive Demo
Real-time terminal visualization with decision points
"""

import numpy as np
from aquacrop_bmi_babel import AquaCrop
import time
import sys

def print_header():
    """Print demo header"""
    print("\n" + "="*80)
    print(" " * 25 + "🌱 BMI AQUACROP LIVE DEMO 🌱")
    print("="*80)
    print()
    print("This demo shows how BMI enables INTERACTIVE crop simulation where")
    print("farmers can make management decisions and see immediate model response.")
    print()
    print("="*80)
    print()

def print_day_header():
    """Print table header for daily output"""
    print()
    print("-" * 95)
    print(f"{'Day':>4} | {'Action':^20} | {'CC%':>6} | {'Biomass':>8} | {'Moisture':>8} | {'Stress':>6} | {'Status':^15}")
    print("-" * 95)

def print_day_status(day, action, state):
    """Print one day's status"""
    cc = state['canopy_cover']
    biomass = state['biomass']
    moisture = state['soil_moisture']
    stress = state['water_stress']
    
    # Determine status
    if moisture < 150:
        status = "🔴 DROUGHT"
    elif moisture < 200:
        status = "🟡 DRY"
    else:
        status = "🟢 GOOD"
    
    print(f"{day:>4} | {action:^20} | {cc:>6.1f} | {biomass:>8.2f} | {moisture:>8.1f} | {stress:>6.0f} | {status:^15}")

def run_interactive_demo():
    """Run the interactive demonstration"""
    
    print_header()
    
    # Initialize model
    config_file = "/mnt/d/KNP/aquacrop-bmi/aquacrop/bmi_test_data/LIST/project.PRO"
    
    print("Initializing AquaCrop via BMI...")
    model = AquaCrop()
    model.initialize(config_file)
    
    print(f"✓ Initialized")
    print(f"  Duration: {int(model.get_end_time())} days")
    print()
    
    # Helper function to get state
    def get_state():
        state = {}
        for var, key in [
            ("crop__canopy_cover", "canopy_cover"),
            ("crop__biomass", "biomass"),
            ("crop__yield", "yield"),
            ("soil__moisture", "soil_moisture"),
            ("crop__water_stress", "water_stress"),
        ]:
            val = np.empty(1, dtype=np.float64)
            model.get_value(var, val)
            state[key] = val[0]
        return state
    
    # Helper function to apply inputs
    def set_inputs(rainfall=0.0, irrigation=0.0, co2=None, mulch=None):
        src = np.array([rainfall], dtype=np.float64)
        model.set_value("weather__rainfall_amount", src)
        
        src = np.array([irrigation], dtype=np.float64)
        model.set_value("management__irrigation_amount", src)
        
        if co2 is not None:
            src = np.array([co2], dtype=np.float64)
            model.set_value("atmosphere__co2_concentration", src)
        
        if mulch is not None:
            src = np.array([mulch], dtype=np.float64)
            model.set_value("management__mulch_cover", src)
    
    # ==================================================================
    # PHASE 1: ESTABLISHMENT (Days 1-20) - No intervention
    # ==================================================================
    print("┌" + "─" * 78 + "┐")
    print("│" + " PHASE 1: CROP ESTABLISHMENT (Days 1-20)".center(78) + "│")
    print("│" + " Strategy: Minimal intervention, let crop establish".center(78) + "│")
    print("└" + "─" * 78 + "┘")
    
    print_day_header()
    
    for day in range(1, 21):
        # Occasional rain
        rainfall = 5.0 if day % 7 == 0 else 0.0
        set_inputs(rainfall=rainfall, irrigation=0.0)
        
        model.update()
        state = get_state()
        
        action = f"Rain {rainfall:.0f}mm" if rainfall > 0 else "Wait"
        print_day_status(day, action, state)
        time.sleep(0.05)  # Small delay for visualization
    
    print()
    print(f"📊 Phase 1 Summary:")
    print(f"   Canopy cover: {state['canopy_cover']:.1f}%")
    print(f"   Biomass: {state['biomass']:.2f} t/ha")
    print(f"   Soil moisture: {state['soil_moisture']:.1f} mm")
    input("\n   Press Enter to continue to Phase 2...")
    
    # ==================================================================
    # PHASE 2: CRITICAL PERIOD (Days 21-50) - Smart irrigation
    # ==================================================================
    print("\n┌" + "─" * 78 + "┐")
    print("│" + " PHASE 2: VEGETATIVE GROWTH (Days 21-50)".center(78) + "│")
    print("│" + " Strategy: Smart irrigation when moisture < 200mm".center(78) + "│")
    print("└" + "─" * 78 + "┘")
    
    print_day_header()
    
    irrigation_events = []
    
    for day in range(21, 51):
        # Check moisture and decide irrigation
        state = get_state()
        
        rainfall = 3.0 if day % 10 == 0 else 0.0
        irrigation = 15.0 if state['soil_moisture'] < 200.0 else 0.0
        
        if irrigation > 0:
            irrigation_events.append(day)
        
        set_inputs(rainfall=rainfall, irrigation=irrigation)
        model.update()
        state = get_state()
        
        action = ""
        if irrigation > 0:
            action = f"💧 Irrigate {irrigation:.0f}mm"
        elif rainfall > 0:
            action = f"🌧 Rain {rainfall:.0f}mm"
        else:
            action = "Monitor"
        
        print_day_status(day, action, state)
        time.sleep(0.05)
    
    print()
    print(f"📊 Phase 2 Summary:")
    print(f"   Canopy cover: {state['canopy_cover']:.1f}%")
    print(f"   Biomass: {state['biomass']:.2f} t/ha")
    print(f"   Soil moisture: {state['soil_moisture']:.1f} mm")
    print(f"   Irrigation events: {len(irrigation_events)} ({sum([15]*len(irrigation_events)):.0f} mm total)")
    input("\n   Press Enter to continue to Phase 3...")
    
    # ==================================================================
    # PHASE 3: MATURATION (Days 51-80) - Conservation measures
    # ==================================================================
    print("\n┌" + "─" * 78 + "┐")
    print("│" + " PHASE 3: FLOWERING & MATURATION (Days 51-80)".center(78) + "│")
    print("│" + " Strategy: Add mulch cover + smart irrigation".center(78) + "│")
    print("└" + "─" * 78 + "┘")
    
    print_day_header()
    
    # Apply mulch
    set_inputs(mulch=50.0)
    print("\n   🌾 Applied 50% mulch cover (reduces evaporation)")
    print()
    
    phase3_irrigation = []
    
    for day in range(51, 81):
        state = get_state()
        
        # More conservative irrigation with mulch
        rainfall = 2.0 if day % 12 == 0 else 0.0
        irrigation = 12.0 if state['soil_moisture'] < 180.0 else 0.0
        
        if irrigation > 0:
            phase3_irrigation.append(day)
        
        set_inputs(rainfall=rainfall, irrigation=irrigation, mulch=50.0)
        model.update()
        state = get_state()
        
        action = ""
        if irrigation > 0:
            action = f"💧 Irrigate {irrigation:.0f}mm"
        elif rainfall > 0:
            action = f"🌧 Rain {rainfall:.0f}mm"
        else:
            action = "Monitor + Mulch"
        
        print_day_status(day, action, state)
        time.sleep(0.05)
    
    print()
    print(f"📊 Phase 3 Summary:")
    print(f"   Canopy cover: {state['canopy_cover']:.1f}%")
    print(f"   Biomass: {state['biomass']:.2f} t/ha")
    print(f"   Soil moisture: {state['soil_moisture']:.1f} mm")
    print(f"   Irrigation events: {len(phase3_irrigation)} ({sum([12]*len(phase3_irrigation)):.0f} mm total)")
    print(f"   Water saved vs. Phase 2: ~{(15-12)*len(phase3_irrigation):.0f} mm")
    input("\n   Press Enter for final results...")
    
    # ==================================================================
    # FINAL HARVEST
    # ==================================================================
    print("\n" + "="*80)
    print(" " * 30 + "🌾 FINAL RESULTS 🌾")
    print("="*80)
    
    final_state = get_state()
    
    print()
    print(f"  Crop Performance:")
    print(f"    Final Canopy Cover:    {final_state['canopy_cover']:>8.1f} %")
    print(f"    Total Biomass:         {final_state['biomass']:>8.2f} t/ha")
    print(f"    Final Yield:           {final_state['yield']:>8.2f} t/ha")
    print()
    print(f"  Water Management:")
    print(f"    Total irrigation:      {sum([15]*len(irrigation_events) + [12]*len(phase3_irrigation)):>8.0f} mm")
    print(f"    Irrigation events:     {len(irrigation_events) + len(phase3_irrigation):>8d}")
    print(f"    Final soil moisture:   {final_state['soil_moisture']:>8.1f} mm")
    print()
    print(f"  Stress Impact:")
    print(f"    Water stress days:     {final_state['water_stress']:>8.0f} days")
    print()
    
    # ==================================================================
    # KEY INSIGHTS
    # ==================================================================
    print("="*80)
    print(" " * 30 + "💡 KEY INSIGHTS 💡")
    print("="*80)
    print()
    print("  ✓ BMI enables REAL-TIME decision making")
    print("    → Model responds immediately to irrigation decisions")
    print()
    print("  ✓ ADAPTIVE management based on current state")
    print("    → Irrigation triggered when moisture drops below threshold")
    print()
    print("  ✓ CONSERVATION practices (mulch) reduce water needs")
    print("    → Less frequent irrigation needed with mulch cover")
    print()
    print("  ✓ Model can be COUPLED with other systems")
    print("    → Weather forecasts, optimization algorithms, IoT sensors")
    print()
    print("="*80)
    print()
    
    # Finalize
    model.finalize()
    print("✓ Simulation complete and finalized")
    print()
    print("This demo shows how BMI transforms AquaCrop from a batch tool")
    print("into an interactive decision support system!")
    print()


if __name__ == "__main__":
    try:
        run_interactive_demo()
    except KeyboardInterrupt:
        print("\n\n⚠ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()