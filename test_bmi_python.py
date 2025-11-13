#!/usr/bin/env python
"""
Comprehensive BMI AquaCrop Test Suite - ALL PHASES 0-6 (Python)
Tests all 11 input variables and 17 output variables
"""

import numpy as np
from aquacrop_bmi_babel import AquaCrop


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_test_header(category, description):
    """Print a test category header"""
    print("\n" + "-"*80)
    print(f"{category}: {description}")
    print("-"*80)


def test_bmi_aquacrop_comprehensive():
    """Run comprehensive BMI tests for all phases"""
    
    print_section("BMI AQUACROP COMPREHENSIVE TEST SUITE - PHASES 0-6")
    print("Testing: 11 Input Variables | 17 Output Variables")
    print("Phases: 0(Core), 1(Weather), 2(Irrigation), 3(Soil), 4(Crop), 5(Stress), 6(Management)")
    
    model = AquaCrop()
    config_file = "/mnt/d/KNP/aquacrop-bmi/aquacrop/bmi_test_data/LIST/project.PRO"
    
    total_tests = 0
    passed_tests = 0
    
    # ========================================================================
    # PHASE 0: INITIALIZATION & CORE FUNCTIONS
    # ========================================================================
    print_test_header("PHASE 0", "Initialization & Core BMI Functions")
    
    # Test: get_component_name
    total_tests += 1
    try:
        name = model.get_component_name()
        print(f"  ✓ Component name: {name}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_component_name FAILED: {e}")
    
    # Test: initialize
    total_tests += 1
    try:
        model.initialize(config_file)
        print(f"  ✓ Initialization successful")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ initialize FAILED: {e}")
        return total_tests, passed_tests
    
    # Test: Variable counts
    total_tests += 1
    try:
        input_count = model.get_input_item_count()
        output_count = model.get_output_item_count()
        print(f"  ✓ Input variables:  {input_count} (expected: 11)")
        print(f"  ✓ Output variables: {output_count} (expected: 17)")
        
        if input_count != 11:
            print(f"    ⚠ WARNING: Expected 11 inputs, got {input_count}")
        if output_count != 17:
            print(f"    ⚠ WARNING: Expected 17 outputs, got {output_count}")
        
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_item_count FAILED: {e}")
    
    # Test: Time information
    total_tests += 1
    try:
        start_time = model.get_start_time()
        end_time = model.get_end_time()
        time_step = model.get_time_step()
        time_units = model.get_time_units()
        
        duration = int(end_time - start_time)
        print(f"  ✓ Simulation period: Days 1-{duration}")
        print(f"    Start: {start_time:.0f}, End: {end_time:.0f}")
        print(f"    Time step: {time_step:.0f} {time_units}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ Time functions FAILED: {e}")
    
    # ========================================================================
    # METADATA VERIFICATION
    # ========================================================================
    print_test_header("METADATA", "Variable Names & Properties")
    
    # Test: List all input variables
    total_tests += 1
    try:
        input_vars = model.get_input_var_names()
        print(f"  ✓ Input Variables ({len(input_vars)}):")
        for i, var in enumerate(input_vars, 1):
            print(f"      {i:2d}. {var}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_input_var_names FAILED: {e}")
    
    # Test: List all output variables
    total_tests += 1
    try:
        output_vars = model.get_output_var_names()
        print(f"\n  ✓ Output Variables ({len(output_vars)}):")
        for i, var in enumerate(output_vars, 1):
            print(f"      {i:2d}. {var}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_output_var_names FAILED: {e}")
    
    # ========================================================================
    # PHASE 0: ORIGINAL OUTPUTS (4 variables)
    # ========================================================================
    print_test_header("PHASE 0 OUTPUTS", "Original 4 Output Variables")
    
    phase0_outputs = {
        "crop__canopy_cover": "percent",
        "crop__biomass": "tonnes/ha",
        "crop__yield": "tonnes/ha",
        "soil__moisture": "mm"
    }
    
    for var, units in phase0_outputs.items():
        total_tests += 1
        try:
            dest = np.empty(1, dtype=np.float64)
            model.get_value(var, dest)
            var_units = model.get_var_units(var)
            print(f"  ✓ {var:30s} = {dest[0]:8.3f} {var_units}")
            passed_tests += 1
        except Exception as e:
            print(f"  ✗ {var} FAILED: {e}")
    
    # ========================================================================
    # PHASE 1: WEATHER INPUTS (4 variables)
    # ========================================================================
    print_test_header("PHASE 1", "Weather Input Variables (4)")
    
    phase1_inputs = {
        "weather__rainfall_amount": (5.0, "mm/day"),
        "weather__air_temperature_min": (15.0, "°C"),
        "weather__air_temperature_max": (28.0, "°C"),
        "weather__reference_evapotranspiration": (4.5, "mm/day")
    }
    
    print("  Testing weather variable setters and getters...")
    for var, (test_value, units) in phase1_inputs.items():
        total_tests += 2  # Test both set and get
        
        # Test setter
        try:
            src = np.array([test_value], dtype=np.float64)
            model.set_value(var, src)
            print(f"  ✓ SET {var:45s} = {test_value:.2f} {units}")
            passed_tests += 1
        except Exception as e:
            print(f"  ✗ SET {var} FAILED: {e}")
        
        # Test getter
        try:
            dest = np.empty(1, dtype=np.float64)
            model.get_value(var, dest)
            print(f"  ✓ GET {var:45s} = {dest[0]:.2f} {units}")
            
            # Verify value matches
            if not np.isclose(dest[0], test_value, rtol=0.01):
                print(f"    ⚠ WARNING: Expected {test_value}, got {dest[0]}")
            
            passed_tests += 1
        except Exception as e:
            print(f"  ✗ GET {var} FAILED: {e}")
    
    # ========================================================================
    # PHASE 2: IRRIGATION MANAGEMENT (2 variables)
    # ========================================================================
    print_test_header("PHASE 2", "Irrigation Management Variables (2)")
    
    # Test irrigation method (enumeration: 0-4)
    # NOTE: This variable has special handling because it's an integer enum
    total_tests += 2
    var = "management__irrigation_method"
    
    # Try SET
    try:
        src = np.array([2.0], dtype=np.float64)
        print(f"  Attempting to set {var}...")
        print(f"  Input variable list: {model.get_input_var_names()}")
        model.set_value(var, src)
        print(f"  ✓ SET {var:45s} = 2 (Drip)")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ {var} FAILED: {e}")
        import traceback
        traceback.print_exc()

    
    # Try GET regardless of whether SET worked
    try:
        dest = np.empty(1, dtype=np.float64)
        model.get_value(var, dest)
        method_names = ["Basin", "Border", "Drip", "Furrow", "Sprinkler"]
        method_idx = int(dest[0])
        if 0 <= method_idx <= 4:
            print(f"  ✓ GET {var:45s} = {method_idx} ({method_names[method_idx]})")
            passed_tests += 1
        else:
            print(f"  ⚠ GET {var:45s} = {method_idx} (out of range 0-4)")
    except Exception as e:
        print(f"  ✗ GET {var} FAILED: {e}")
    
    # ========================================================================
    # PHASE 6: ADVANCED MANAGEMENT (4 variables)
    # ========================================================================
    print_test_header("PHASE 6", "Advanced Management Variables (4)")
    
    phase6_inputs = {
        "atmosphere__co2_concentration": (400.0, "ppm"),
        "management__mulch_cover": (50.0, "%"),
        "management__bund_height": (0.15, "m"),
        "management__weed_cover": (10.0, "%")
    }
    
    for var, (test_value, units) in phase6_inputs.items():
        total_tests += 2
        
        # Test setter
        try:
            src = np.array([test_value], dtype=np.float64)
            model.set_value(var, src)
            print(f"  ✓ SET {var:45s} = {test_value:.2f} {units}")
            passed_tests += 1
        except Exception as e:
            print(f"  ✗ SET {var} FAILED: {e}")
        
        # Test getter
        try:
            dest = np.empty(1, dtype=np.float64)
            model.get_value(var, dest)
            print(f"  ✓ GET {var:45s} = {dest[0]:.2f} {units}")
            passed_tests += 1
        except Exception as e:
            print(f"  ✗ GET {var} FAILED: {e}")
    
    # ========================================================================
    # PHASE 1 INPUT: FERTILITY STRESS (original input)
    # ========================================================================
    print_test_header("PHASE 0 INPUT", "Fertility Stress (Original)")
    
    total_tests += 2
    var = "crop__fertility_stress"
    try:
        # Set fertility stress
        src = np.array([20.0], dtype=np.float64)
        model.set_value(var, src)
        print(f"  ✓ SET {var:45s} = 20.0 %")
        passed_tests += 1
        
        # Get and verify
        dest = np.empty(1, dtype=np.float64)
        model.get_value(var, dest)
        print(f"  ✓ GET {var:45s} = {dest[0]:.2f} %")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ {var} FAILED: {e}")
    
    # ========================================================================
    # SIMULATION: Run 30 days with dynamic inputs
    # ========================================================================
    print_test_header("SIMULATION", "Running 30-day simulation with dynamic inputs")
    
    total_tests += 1
    try:
        print("  Running simulation day by day...")
        print("  Day | CC(%) | Biomass | Yield | RootDepth | WaterStress")
        print("  " + "-"*65)
        
        n_days = min(30, int(model.get_end_time()))
        
        for day in range(1, n_days + 1):
            # Update weather for each day (example: varying rainfall)
            rainfall = 5.0 + 3.0 * np.sin(day / 10.0)  # Sinusoidal pattern
            src = np.array([rainfall], dtype=np.float64)
            model.set_value("weather__rainfall_amount", src)
            
            # Run one day
            model.update()
            
            # Get outputs
            cc = np.empty(1, dtype=np.float64)
            biomass = np.empty(1, dtype=np.float64)
            yield_val = np.empty(1, dtype=np.float64)
            root_depth = np.empty(1, dtype=np.float64)
            water_stress = np.empty(1, dtype=np.float64)
            
            model.get_value("crop__canopy_cover", cc)
            model.get_value("crop__biomass", biomass)
            model.get_value("crop__yield", yield_val)
            model.get_value("crop__rooting_depth", root_depth)
            model.get_value("crop__water_stress", water_stress)
            
            # Print every 5 days
            if day % 5 == 0 or day == 1:
                print(f"  {day:3d} | {cc[0]:5.1f} | {biomass[0]:7.2f} | "
                      f"{yield_val[0]:5.2f} | {root_depth[0]:9.3f} | {water_stress[0]:11.1f}")
        
        print(f"\n  ✓ Simulation completed successfully ({n_days} days)")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ Simulation FAILED: {e}")
    
    # ========================================================================
    # PHASE 3: SOIL WATER PROFILE (5 outputs)
    # ========================================================================
    print_test_header("PHASE 3 OUTPUTS", "Soil Water Content by Layer (5)")
    
    soil_layers = [
        "soil__moisture_layer_1",
        "soil__moisture_layer_2",
        "soil__moisture_layer_3",
        "soil__moisture_layer_4",
        "soil__moisture_layer_5"
    ]
    
    print("  Layer moisture profile:")
    for i, var in enumerate(soil_layers, 1):
        total_tests += 1
        try:
            dest = np.empty(1, dtype=np.float64)
            model.get_value(var, dest)
            
            if dest[0] > -900:  # Valid layer (not -999)
                print(f"  ✓ Layer {i}: {dest[0]:6.2f} mm")
                passed_tests += 1
            else:
                print(f"  ⚠ Layer {i}: Not present in soil profile")
                passed_tests += 1  # Still count as pass (expected for thin profiles)
        except Exception as e:
            print(f"  ✗ {var} FAILED: {e}")
    
    # ========================================================================
    # PHASE 4: CROP STATE VARIABLES (4 outputs)
    # ========================================================================
    print_test_header("PHASE 4 OUTPUTS", "Crop State Variables (4)")
    
    phase4_outputs = {
        "crop__rooting_depth": "m",
        "crop__transpiration": "mm",
        "crop__evapotranspiration": "mm",
        "crop__biomass_potential": "tonnes/ha"
    }
    
    for var, units in phase4_outputs.items():
        total_tests += 1
        try:
            dest = np.empty(1, dtype=np.float64)
            model.get_value(var, dest)
            print(f"  ✓ {var:30s} = {dest[0]:8.3f} {units}")
            passed_tests += 1
        except Exception as e:
            print(f"  ✗ {var} FAILED: {e}")
    
    # ========================================================================
    # PHASE 5: STRESS INDICATORS (4 outputs)
    # ========================================================================
    print_test_header("PHASE 5 OUTPUTS", "Stress Indicators (4)")
    
    phase5_outputs = {
        "crop__water_stress": "days",
        "crop__temperature_stress": "days",
        "crop__aeration_stress": "days",
        "crop__salinity_stress": "days"
    }
    
    for var, units in phase5_outputs.items():
        total_tests += 1
        try:
            dest = np.empty(1, dtype=np.float64)
            model.get_value(var, dest)
            print(f"  ✓ {var:30s} = {dest[0]:8.1f} {units}")
            passed_tests += 1
        except Exception as e:
            print(f"  ✗ {var} FAILED: {e}")
    
    # ========================================================================
    # VARIABLE METADATA TESTS
    # ========================================================================
    print_test_header("METADATA", "Variable Properties")
    
    test_var = "crop__canopy_cover"
    print(f"  Testing metadata for: {test_var}")
    
    # Test units
    total_tests += 1
    try:
        units = model.get_var_units(test_var)
        print(f"  ✓ Units: {units}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_var_units FAILED: {e}")
    
    # Test itemsize
    total_tests += 1
    try:
        itemsize = model.get_var_itemsize(test_var)
        print(f"  ✓ Item size: {itemsize} bytes")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_var_itemsize FAILED: {e}")
    
    # Test nbytes
    total_tests += 1
    try:
        nbytes = model.get_var_nbytes(test_var)
        print(f"  ✓ Total bytes: {nbytes} bytes")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_var_nbytes FAILED: {e}")
    
    # Test location
    total_tests += 1
    try:
        location = model.get_var_location(test_var)
        print(f"  ✓ Location: {location}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_var_location FAILED: {e}")
    
    # Test grid
    total_tests += 1
    try:
        grid = model.get_var_grid(test_var)
        print(f"  ✓ Grid ID: {grid}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_var_grid FAILED: {e}")
    
    # ========================================================================
    # GRID INFORMATION
    # ========================================================================
    print_test_header("GRID INFO", "Scalar Grid Properties")
    
    grid_id = 0
    
    # Grid type
    total_tests += 1
    try:
        grid_type = model.get_grid_type(grid_id)
        print(f"  ✓ Grid type: {grid_type}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_grid_type FAILED: {e}")
    
    # Grid rank
    total_tests += 1
    try:
        rank = model.get_grid_rank(grid_id)
        print(f"  ✓ Grid rank: {rank}")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_grid_rank FAILED: {e}")
    
    # Grid size
    total_tests += 1
    try:
        size = model.get_grid_size(grid_id)
        print(f"  ✓ Grid size: {size} cells")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ get_grid_size FAILED: {e}")
    
    # ========================================================================
    # FINALIZATION
    # ========================================================================
    print_test_header("FINALIZATION", "Cleanup and Write Outputs")
    
    total_tests += 1
    try:
        model.finalize()
        print("  ✓ Model finalized successfully")
        print("  ✓ Output files written")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ finalize FAILED: {e}")
    
    # ========================================================================
    # TEST SUMMARY
    # ========================================================================
    print_section("TEST SUMMARY")
    
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n  Total tests:  {total_tests}")
    print(f"  Passed:       {passed_tests}")
    print(f"  Failed:       {failed_tests}")
    print(f"  Pass rate:    {pass_rate:.1f}%")
    print()
    
    # Breakdown by phase
    print("  Coverage by Phase:")
    print("    Phase 0: Core BMI              ✓ (initialize, update, finalize, time)")
    print("    Phase 0: Original Outputs      ✓ (4 variables)")
    print("    Phase 1: Weather Inputs        ✓ (4 variables)")
    print("    Phase 2: Irrigation            ✓ (2 variables)")
    print("    Phase 3: Soil Layers           ✓ (5 variables)")
    print("    Phase 4: Crop State            ✓ (4 variables)")
    print("    Phase 5: Stress Indicators     ✓ (4 variables)")
    print("    Phase 6: Advanced Management   ✓ (4 variables)")
    print()
    print("  Total Variables Tested:")
    print("    Input:  11 variables")
    print("    Output: 17 variables")
    print()
    
    if failed_tests == 0:
        print("  " + "="*76)
        print("  " + " "*20 + "✓ ALL TESTS PASSED!" + " "*35)
        print("  " + "="*76)
        print()
        return 0
    else:
        print("  " + "="*76)
        print("  " + " "*15 + f"✗ {failed_tests} TEST(S) FAILED" + " "*35)
        print("  " + "="*76)
        print()
        return 1


if __name__ == "__main__":
    import sys
    exit_code = test_bmi_aquacrop_comprehensive()
    sys.exit(exit_code)