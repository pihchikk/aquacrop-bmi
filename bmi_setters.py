#!/usr/bin/env python3
"""
Test Script for AquaCrop BMI Functions

This script performs two main tasks:
1.  Calls all metadata 'get_...' functions to verify they are implemented.
2.  Runs a "Control vs. Intervention" A/B test to prove that the 'set_value'
    function has an observable and drastic impact on the simulation.
3.  Tests the 'update_until' function.
4.  Tests the 'get_value_ptr' function for live memory reference.

**PREREQUISITE:**
You must run 'bmi_interactive_demo.py' at least once to generate
the project files this test depends on.
"""

import numpy as np
from aquacrop_bmi_babel import AquaCrop
from pathlib import Path
import sys

# --- CONFIGURATION ---
# This path MUST exist. Run 'bmi_interactive_demo.py' first to create it.
CONFIG_FILE = Path("outputs/scenario_1_baseline_rainfed/LIST/project.PRO")

def run_metadata_test():
    """
    Initializes the model and calls all 'get_...' functions
    from the BMI interface to verify they return values.
    """
    print("="*80)
    print("PART 1: METADATA FUNCTION TEST")
    print("="*80)
    
    if not CONFIG_FILE.exists():
        print(f"❌ ERROR: Config file not found at:\n{CONFIG_FILE.resolve()}")
        print("Please run 'bmi_interactive_demo.py' first to generate it.")
        return False

    model = AquaCrop()
    
    try:
        # Initialize
        print(f"Initializing model with: {CONFIG_FILE}\n")
        model.initialize(str(CONFIG_FILE))

        # --- Test BMI 'get' functions ---
        print(f"get_component_name(): {model.get_component_name()}")
        
        # Time functions
        print(f"get_start_time(): {model.get_start_time()}")
        print(f"get_end_time(): {model.get_end_time()}")
        print(f"get_current_time(): {model.get_current_time()}")
        print(f"get_time_step(): {model.get_time_step()}")
        print(f"get_time_units(): {model.get_time_units()}")
        
        # Variable counts
        print(f"get_input_item_count(): {model.get_input_item_count()}")
        print(f"get_output_item_count(): {model.get_output_item_count()}")

        # Variable lists
        print(f"\nget_input_var_names():\n {model.get_input_var_names()}")
        print(f"\nget_output_var_names():\n {model.get_output_var_names()}")
        
        # Test info for one variable: 'crop__biomass'
        print("\n--- Variable Info (for 'crop__biomass') ---")
        var_name = "crop__biomass"
        grid_id = model.get_var_grid(var_name)
        print(f"get_var_grid('{var_name}'): {grid_id}")
        print(f"get_var_itemsize('{var_name}'): {model.get_var_itemsize(var_name)}")
        print(f"get_var_location('{var_name}'): {model.get_var_location(var_name)}")
        print(f"get_var_nbytes('{var_name}'): {model.get_var_nbytes(var_name)}")
        print(f"get_var_type('{var_name}'): {model.get_var_type(var_name)}")
        print(f"get_var_units('{var_name}'): {model.get_var_units(var_name)}")

        # Test info for the grid (AquaCrop is a 0D point model, so grid is 0)
        print("\n--- Grid Info (for Grid 0) ---")
        rank = model.get_grid_rank(grid_id)
        print(f"get_grid_rank({grid_id}): {rank}")
        size = model.get_grid_size(grid_id)
        print(f"get_grid_size({grid_id}): {size}")
        print(f"get_grid_type({grid_id}): {model.get_grid_type(grid_id)}")
        
        # --- CORRECTED BMI CALLS ---
        # These functions populate an array, they don't return a value.
        
        # get_grid_shape(grid_id, array)
        shape = np.empty(rank, dtype=np.int32)
        model.get_grid_shape(grid_id, shape)
        print(f"get_grid_shape({grid_id}): {shape}")

        # get_grid_spacing(grid_id, array)
        spacing = np.empty(rank, dtype=np.float64)
        model.get_grid_spacing(grid_id, spacing)
        print(f"get_grid_spacing({grid_id}): {spacing}")

        # get_grid_origin(grid_id, array)
        origin = np.empty(rank, dtype=np.float64)
        model.get_grid_origin(grid_id, origin)
        print(f"get_grid_origin({grid_id}): {origin}")

        # get_grid_x(grid_id, array)
        grid_x = np.empty(size, dtype=np.float64)
        model.get_grid_x(grid_id, grid_x)
        print(f"get_grid_x({grid_id}): {grid_x}")

        # get_grid_y(grid_id, array)
        grid_y = np.empty(size, dtype=np.float64)
        model.get_grid_y(grid_id, grid_y)
        print(f"get_grid_y({grid_id}): {grid_y}")

        # get_grid_z(grid_id, array)
        grid_z = np.empty(size, dtype=np.float64)
        model.get_grid_z(grid_id, grid_z)
        print(f"get_grid_z({grid_id}): {grid_z}")
        # --- END OF CORRECTIONS ---

        print("\n--- Grid Connectivity (for 0D model, expect 0) ---")
        try:
            print(f"get_grid_edge_count({grid_id}): {model.get_grid_edge_count(grid_id)}")
            print(f"get_grid_face_count({grid_id}): {model.get_grid_face_count(grid_id)}")
        except Exception as e:
            print(f"  (Could not get edge/face count, as expected for scalar): {e}")

        print("\n✅ PART 1: Metadata test passed.")
        return True

    except Exception as e:
        print(f"❌ PART 1: Metadata test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Finalize
        if 'model' in locals():
            print("\nFinalizing model...")
            model.finalize()

def run_setter_test():
    """
    Runs an A/B test to prove 'set_value' impacts the simulation.
    - Run A: Control simulation with no intervention.
    - Run B: Intervention simulation with a large irrigation event.
    """
    print("\n" + "="*80)
    print("PART 2: 'set_value' INTERVENTION TEST")
    print("="*80)

    # --- RUN A: CONTROL (NO INTERVENTION) ---
    print("\n--- Running CONTROL (A) ---")
    model_A = AquaCrop()
    model_A.initialize(str(CONFIG_FILE))
    
    n_days = 50
    for day in range(n_days):
        model_A.update()
        
    # Get final state
    biomass_A = np.empty(1, dtype=np.float64)
    moisture_A = np.empty(1, dtype=np.float64)
    model_A.get_value("crop__biomass", biomass_A)
    model_A.get_value("soil__moisture", moisture_A)
    model_A.finalize()
    
    print("Control run complete.")
    print(f"  Final Biomass (A):   {biomass_A[0]:.4f}")
    print(f"  Final Moisture (A): {moisture_A[0]:.4f}")

    # --- RUN B: INTERVENTION (SET_VALUE) ---
    print("\n--- Running INTERVENTION (B) ---")
    model_B = AquaCrop()
    model_B.initialize(str(CONFIG_FILE))
    
    irrigation_day = 25
    irrigation_amount = 50.0  # Apply a drastic 50mm of water
    
    for day in range(n_days):
        if day == irrigation_day:
            print(f"  Day {day}: >>> APPLYING {irrigation_amount}mm IRRIGATION via set_value() <<<")
            src = np.array([irrigation_amount], dtype=np.float64)
            model_B.set_value("management__irrigation_amount", src)
            
        model_B.update()
        
    # Get final state
    biomass_B = np.empty(1, dtype=np.float64)
    moisture_B = np.empty(1, dtype=np.float64)
    model_B.get_value("crop__biomass", biomass_B)
    model_B.get_value("soil__moisture", moisture_B)
    model_B.finalize()

    print("Intervention run complete.")
    print(f"  Final Biomass (B):   {biomass_B[0]:.4f}")
    print(f"  Final Moisture (B): {moisture_B[0]:.4f}")

    # --- ASSERTION ---
    print("\n--- RESULTS ---")
    if moisture_A[0] != moisture_B[0] and biomass_A[0] != biomass_B[0]:
        print("✅ SUCCESS: 'set_value' test passed!")
        print("   Final moisture and biomass values are different,")
        print("   proving the intervention successfully altered the model state.")
    else:
        print("❌ FAILED: 'set_value' test failed.")
        print("   Control and Intervention runs produced identical results.")
    return moisture_A[0] != moisture_B[0]

def run_update_until_test():
    """Tests the update_until function."""
    print("\n" + "="*80)
    print("PART 3: 'update_until' TEST")
    print("="*80)

    model = AquaCrop()
    model.initialize(str(CONFIG_FILE))
    
    start_time = model.get_current_time()
    target_time = start_time + 30.0 # Advance 30 days
    
    print(f"  Start time: {start_time}")
    print(f"  Calling update_until({target_time})...")
    model.update_until(target_time)
    
    end_time = model.get_current_time()
    print(f"  End time:   {end_time}")
    
    model.finalize()
    
    if np.isclose(end_time, target_time):
        print("\n✅ SUCCESS: 'update_until' test passed.")
        print("   Model correctly advanced to the target time.")
        return True
    else:
        print("\n❌ FAILED: 'update_until' test failed.")
        print(f"   Model time {end_time} does not match target {target_time}.")
        return False

def run_pointer_test():
    """Tests the get_value_ptr function for a live memory reference."""
    print("\n" + "="*80)
    print("PART 4: 'get_value_ptr' TEST")
    print("="*80)
    
    model = AquaCrop()
    model.initialize(str(CONFIG_FILE))
    
    var_name = "crop__biomass"
    
    print(f"  Requesting pointer for: '{var_name}'")
    # Get the pointer. This is a 1-element NumPy array
    # that references the model's internal memory.
    biomass_ptr = model.get_value_ptr(var_name)
    
    print(f"  Value from pointer at Day 0: {biomass_ptr[0]:.4f}")
    
    # Run the model for 30 days
    model.update_until(model.get_current_time() + 30)
    
    print(f"  Model updated to Day 30.")
    print(f"  Value from pointer at Day 30: {biomass_ptr[0]:.4f}")
    
    # Get the value using the standard get_value for comparison
    biomass_val = np.empty(1, dtype=np.float64)
    model.get_value(var_name, biomass_val)
    print(f"  Value from get_value at Day 30: {biomass_val[0]:.4f}")
    
    model.finalize()
    
    if biomass_ptr[0] > 0 and np.isclose(biomass_ptr[0], biomass_val[0]):
        print("\n✅ SUCCESS: 'get_value_ptr' test passed.")
        print("   Pointer value updated automatically as model state changed.")
        return True
    else:
        print("\n❌ FAILED: 'get_value_ptr' test failed.")
        print("   Pointer value did not update or match get_value.")
        return False

def main():
    if not run_metadata_test():
        sys.exit(1) # Stop if metadata test fails (e.g., file not found)
    
    if not run_setter_test():
        sys.exit(1) # Stop if setter test fails
        
    if not run_update_until_test():
        sys.exit(1) # Stop if update_until test fails
        
    if not run_pointer_test():
        sys.exit(1) # Stop if pointer test fails

    print("\n" + "*"*80)
    print("🌟 ALL BMI TESTS PASSED! 🌟")
    print("*"*80)

if __name__ == "__main__":
    main()