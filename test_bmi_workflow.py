# ./test_bmi_workflow.py

import json
from pathlib import Path

# *** NEW: Import numpy for array allocation ***
import numpy as np

from aquacrop_bmi.bmi_aquacrop import BmiAquaCrop
# from aquacrop_bmi.models import ScenariosSimulationInput 

def get_config_path(file_name: str) -> Path:
    """Constructs the path to the example JSON file."""
    package_dir = Path('./src/aquacrop_bmi')
    examples_dir = package_dir / 'examples'
    return examples_dir / file_name

def run_full_workflow():
    # --- Configuration ---
    config_path = get_config_path('scenarios-simulation.json') 
    DAYS_TO_SIMULATE = 10
    
    print(f"Loading simulation configuration from: {config_path.name}")
    
    # --- 1. Instantiate BMI ---
    bmi = BmiAquaCrop()
    
    # --- 2. Initialize ---
    print("Calling BMI.initialize...")
    try:
        bmi.initialize(str(config_path))
        print(f"✅ Initialization successful! Component: {bmi.get_component_name()}")
        print("-" * 30)

    except Exception as e:
        print(f"❌ Initialization FAILED. Error: {e}")
        return

    # --- 3. Run Simulation (Update loop) ---
    print(f"Starting simulation. Model time step: {bmi.get_time_step()} days")
    start_time = bmi.get_current_time()
    
    print(f"Advancing model by {DAYS_TO_SIMULATE} steps...")
    
    for i in range(DAYS_TO_SIMULATE):
        bmi.update() 
        # Optional: Print progress
        # print(f" Day {i+1}: Current time = {bmi.get_current_time():.1f} days", end='\r')

    # --- 4. Get Current Time and Status ---
    final_time = bmi.get_current_time()
    print(f"\n✅ Simulation advanced successfully!")
    print(f"Start Time: {start_time:.1f} days")
    print(f"Final Time: {final_time:.1f} days (Advanced by {final_time - start_time:.1f} days)")
    print("-" * 30)

    # --- 5. Get Output Values ---
    print("Retrieving simulation outputs:")
    
    # Get necessary metadata for allocation
    var_biomass = "crop__biomass"
    biomass_dtype = bmi.get_var_type(var_biomass)
    
    # *** CORRECTED: Allocate array and pass it to get_value ***
    # Since it's a scalar value, the array size is 1.
    biomass_buffer = np.empty(1, dtype=biomass_dtype) 
    biomass_value = bmi.get_value(var_biomass, biomass_buffer).item()
    
    biomass_units = bmi.get_var_units(var_biomass)
    print(f" - {var_biomass}: {biomass_value:.2f} {biomass_units}")

    var_yield = "crop__yield"
    yield_dtype = bmi.get_var_type(var_yield)
    
    # *** CORRECTED: Allocate array and pass it to get_value ***
    yield_buffer = np.empty(1, dtype=yield_dtype)
    yield_value = bmi.get_value(var_yield, yield_buffer).item()
    
    yield_units = bmi.get_var_units(var_yield)
    print(f" - {var_yield}: {yield_value:.2f} {yield_units}")

    # --- 6. Finalize ---
    print("\nCalling BMI.finalize...")
    bmi.finalize()
    print("✅ Model finalized.")

if __name__ == '__main__':
    run_full_workflow()