"""
Test AquaCrop BMI from Python
"""
import numpy as np

def test_basic_bmi():
    """Test basic BMI functionality from Python"""
    from aquacrop_bmi import AquaCrop
    
    # Create model
    model = AquaCrop()
    print("✅ Model created")
    
    # Get component name
    name = model.get_component_name()
    print(f"✅ Component name: {name}")
    assert name == "AquaCrop"
    
    # Initialize
    config_file = "aquacrop/bmi_test_data/LIST/project.PRO"
    model.initialize(config_file)
    print(f"✅ Initialized with: {config_file}")
    
    # Get model info
    n_inputs = model.get_input_item_count()
    n_outputs = model.get_output_item_count()
    print(f"✅ Inputs: {n_inputs}, Outputs: {n_outputs}")
    
    # Get variable names
    input_vars = model.get_input_var_names()
    output_vars = model.get_output_var_names()
    print(f"✅ Input variables: {input_vars}")
    print(f"✅ Output variables: {output_vars}")
    
    # Get time info
    start_time = model.get_start_time()
    end_time = model.get_end_time()
    time_step = model.get_time_step()
    time_units = model.get_time_units()
    print(f"✅ Time: {start_time} to {end_time} {time_units}, step={time_step}")
    
    # Run simulation for 30 days
    print("\n📊 Running simulation for 30 days:")
    print("Day |  CC(%)  | Biomass | Yield  | Soil H2O")
    print("----|---------|---------|--------|----------")
    
    for day in range(30):
        model.update()
        current_time = model.get_current_time()
        
        # Get all outputs
        cc = model.get_value("crop__canopy_cover")
        biomass = model.get_value("crop__biomass")
        yield_val = model.get_value("crop__yield")
        soil_water = model.get_value("soil__moisture")
        
        if day % 5 == 0:
            print(f"{day+1:3d} | {cc[0]:7.2f} | {biomass[0]:7.3f} | "
                  f"{yield_val[0]:6.3f} | {soil_water[0]:8.2f}")
    
    # Final values
    print("\n📈 Final values:")
    cc_final = model.get_value("crop__canopy_cover")
    biomass_final = model.get_value("crop__biomass")
    yield_final = model.get_value("crop__yield")
    soil_water_final = model.get_value("soil__moisture")
    
    print(f"  Canopy Cover:  {cc_final[0]:.2f} %")
    print(f"  Biomass:       {biomass_final[0]:.3f} tonnes/ha")
    print(f"  Yield:         {yield_final[0]:.3f} tonnes/ha")
    print(f"  Soil Moisture: {soil_water_final[0]:.2f} mm")
    
    # Finalize
    model.finalize()
    print("\n✅ Model finalized")
    print("\n🎉 ALL TESTS PASSED!")

def test_grid_functions():
    """Test BMI grid functions"""
    from aquacrop_bmi import AquaCrop
    
    model = AquaCrop()
    model.initialize("aquacrop/bmi_test_data/LIST/project.PRO")
    
    # Get grid info for first variable
    var_name = "crop__canopy_cover"
    grid_id = model.get_var_grid(var_name)
    print(f"✅ Grid ID for {var_name}: {grid_id}")
    
    # Grid properties
    grid_type = model.get_grid_type(grid_id)
    grid_rank = model.get_grid_rank(grid_id)
    grid_size = model.get_grid_size(grid_id)
    
    print(f"✅ Grid type: {grid_type}")
    print(f"✅ Grid rank: {grid_rank}")
    print(f"✅ Grid size: {grid_size}")
    
    assert grid_type == "scalar"
    assert grid_rank == 0
    assert grid_size == 1
    
    model.finalize()
    print("✅ Grid tests passed")

def test_variable_info():
    """Test BMI variable information functions"""
    from aquacrop_bmi import AquaCrop
    
    model = AquaCrop()
    model.initialize("aquacrop/bmi_test_data/LIST/project.PRO")
    
    var_name = "crop__canopy_cover"
    
    # Variable properties
    var_type = model.get_var_type(var_name)
    var_units = model.get_var_units(var_name)
    var_itemsize = model.get_var_itemsize(var_name)
    var_nbytes = model.get_var_nbytes(var_name)
    var_location = model.get_var_location(var_name)
    
    print(f"✅ {var_name}:")
    print(f"   Type: {var_type}")
    print(f"   Units: {var_units}")
    print(f"   Item size: {var_itemsize} bytes")
    print(f"   Total bytes: {var_nbytes} bytes")
    print(f"   Location: {var_location}")
    
    assert var_type == "double"
    assert var_units == "percent"
    
    model.finalize()
    print("✅ Variable info tests passed")

def test_numpy_integration():
    """Test integration with NumPy arrays"""
    from aquacrop_bmi import AquaCrop
    
    model = AquaCrop()
    model.initialize("aquacrop/bmi_test_data/LIST/project.PRO")
    
    # Run simulation and collect data
    days = 50
    cc_data = np.zeros(days)
    biomass_data = np.zeros(days)
    
    for i in range(days):
        model.update()
        cc_data[i] = model.get_value("crop__canopy_cover")[0]
        biomass_data[i] = model.get_value("crop__biomass")[0]
    
    print(f"✅ Collected {days} days of data")
    print(f"   CC range: {cc_data.min():.2f} - {cc_data.max():.2f} %")
    print(f"   Biomass range: {biomass_data.min():.3f} - {biomass_data.max():.3f} t/ha")
    print(f"   CC mean: {cc_data.mean():.2f} %")
    print(f"   Biomass mean: {biomass_data.mean():.3f} t/ha")
    
    model.finalize()
    print("✅ NumPy integration tests passed")

if __name__ == "__main__":
    print("=" * 70)
    print("          AQUACROP BMI PYTHON TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        print("Test 1: Basic BMI Functions")
        print("-" * 70)
        test_basic_bmi()
        print()
        
        print("Test 2: Grid Functions")
        print("-" * 70)
        test_grid_functions()
        print()
        
        print("Test 3: Variable Information")
        print("-" * 70)
        test_variable_info()
        print()
        
        print("Test 4: NumPy Integration")
        print("-" * 70)
        test_numpy_integration()
        print()
        
        print("=" * 70)
        print("  ✅ ALL PYTHON TESTS PASSED!")
        print("=" * 70)
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMake sure to:")
        print("  1. Run babelizer: babelize generate ...")
        print("  2. Install package: pip install -e .")
        print("  3. Set library path: export LD_LIBRARY_PATH=$PWD/aquacrop")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
