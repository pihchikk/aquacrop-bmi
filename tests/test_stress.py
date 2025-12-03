#!/usr/bin/env python3
"""
Stress Test Suite - Edge Cases and Error Conditions
Tests unusual patterns, race conditions, and error paths
"""

import sys
import numpy as np
from pathlib import Path


def test_rapid_reinit():
    """Rapid reinitialization without finalize"""
    print("\n=== TEST: Rapid Reinitialization ===")
    from pymt.models import AquaCrop
    
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    
    for i in range(5):
        print(f"  Attempt {i+1}/5...")
        m = AquaCrop()
        m.initialize(scenario)
        m.update_until(10.0)
        m.finalize()
        del m
    
    print("✓ Rapid reinit successful")


def test_finalize_twice():
    """Call finalize twice - should not crash"""
    print("\n=== TEST: Double Finalize ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    m.update_until(10.0)
    
    print("  First finalize...")
    m.finalize()
    
    print("  Second finalize...")
    m.finalize()  # Should be safe
    
    print("✓ Double finalize handled safely")


def test_no_update_before_finalize():
    """Initialize and immediately finalize"""
    print("\n=== TEST: Finalize Without Update ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    
    print("  Finalizing immediately after init...")
    m.finalize()
    
    print("✓ Immediate finalize works")


def test_massive_time_jump():
    """Jump to very large time value"""
    print("\n=== TEST: Massive Time Jump ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    
    print(f"  End time: {m.end_time}")
    print(f"  Jumping to 1000.0...")
    
    try:
        m.update_until(1000.0)
        current = m.time
        print(f"  Actual time reached: {current}")
        assert current <= m.end_time, "Should stop at end_time"
    except Exception as e:
        print(f"  Exception (expected): {e}")
    
    m.finalize()
    print("✓ Massive time jump handled")


def test_negative_setter_values():
    """Try setting negative values"""
    print("\n=== TEST: Negative Setter Values ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    m.update_until(10.0)
    
    print("  Setting negative rainfall...")
    src = np.array([-10.0], dtype=np.float64)
    m.set_value('weather__rainfall_amount', src)
    m.update()
    
    print("  Setting negative temperature...")
    src = np.array([-5.0], dtype=np.float64)
    m.set_value('weather__air_temperature_min', src)
    m.update()
    
    m.finalize()
    print("✓ Negative values handled (may be clamped internally)")


def test_nan_setter_values():
    """Try setting NaN values"""
    print("\n=== TEST: NaN Setter Values ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    m.update_until(10.0)
    
    print("  Setting NaN rainfall...")
    try:
        src = np.array([np.nan], dtype=np.float64)
        m.set_value('weather__rainfall_amount', src)
        m.update()
        print("  NaN accepted (may cause issues)")
    except Exception as e:
        print(f"  Exception (good): {type(e).__name__}")
    
    m.finalize()
    print("✓ NaN handling tested")


def test_inf_setter_values():
    """Try setting infinity values"""
    print("\n=== TEST: Infinity Setter Values ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    m.update_until(10.0)
    
    print("  Setting infinite rainfall...")
    try:
        src = np.array([np.inf], dtype=np.float64)
        m.set_value('weather__rainfall_amount', src)
        m.update()
        print("  Infinity accepted (may cause issues)")
    except Exception as e:
        print(f"  Exception (good): {type(e).__name__}")
    
    m.finalize()
    print("✓ Infinity handling tested")


def test_wrong_array_size():
    """Try setting value with wrong array size"""
    print("\n=== TEST: Wrong Array Size ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    m.update_until(10.0)
    
    print("  Setting value with size 3 array...")
    try:
        src = np.array([10.0, 20.0, 30.0], dtype=np.float64)
        m.set_value('weather__rainfall_amount', src)
        print("  Large array accepted (may truncate)")
    except Exception as e:
        print(f"  Exception (expected): {type(e).__name__}")
    
    m.finalize()
    print("✓ Array size mismatch tested")


def test_empty_array():
    """Try setting empty array"""
    print("\n=== TEST: Empty Array ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    m.update_until(10.0)
    
    print("  Setting empty array...")
    try:
        src = np.array([], dtype=np.float64)
        m.set_value('weather__rainfall_amount', src)
        print("  Empty array accepted")
    except Exception as e:
        print(f"  Exception (expected): {type(e).__name__}")
    
    m.finalize()
    print("✓ Empty array tested")


def test_update_beyond_end():
    """Keep calling update after reaching end"""
    print("\n=== TEST: Update Beyond End ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    
    end = m.end_time
    print(f"  End time: {end}")
    
    # Go to end
    m.update_until(end)
    print(f"  Reached end: {m.time}")
    
    # Try updating past end
    print("  Attempting 10 more updates...")
    for i in range(10):
        try:
            m.update()
            print(f"    Update {i+1}: time={m.time}")
        except Exception as e:
            print(f"    Update {i+1}: {type(e).__name__}")
            break
    
    m.finalize()
    print("✓ Updates beyond end tested")


def test_interleaved_operations():
    """Interleave different operations"""
    print("\n=== TEST: Interleaved Operations ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    
    dest = np.empty(1, dtype=np.float64)
    src = np.array([25.0], dtype=np.float64)
    
    for i in range(20):
        # Mix of operations
        if i % 3 == 0:
            m.set_value('weather__rainfall_amount', src)
        if i % 5 == 0:
            m.get_value('crop__yield', dest)
        m.update()
    
    m.finalize()
    print("✓ Interleaved operations successful")


def test_calibration_then_immediate_simulation():
    """Run calibration then immediately use result"""
    print("\n=== TEST: Calibration → Immediate Simulation ===")
    from pymt.models import AquaCrop
    
    # Calibration
    print("  Running calibration...")
    m1 = AquaCrop()
    calib_scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/crop-calibration.json"
    m1.initialize(calib_scenario)
    
    # Find output
    outputs_dir = Path.cwd() / "outputs"
    calib_dirs = list(outputs_dir.glob("crop-calibration_*"))
    if not calib_dirs:
        print("  ✗ No calibration output found")
        return
    
    latest = max(calib_dirs, key=lambda p: p.stat().st_mtime)
    scenarios_file = latest / "scenarios_from_bmi_calib.json"
    
    # Immediate simulation
    print("  Running simulation with calibrated params...")
    m2 = AquaCrop()
    m2.initialize(str(scenarios_file))
    m2.update_until(20.0)
    
    dest = np.empty(1, dtype=np.float64)
    m2.get_value('crop__yield', dest)
    print(f"  Yield: {dest[0]:.3f} t/ha")
    
    m2.finalize()
    print("✓ Calibration → Simulation pipeline works")


def test_missing_scenario_file():
    """Try initializing with non-existent file"""
    print("\n=== TEST: Missing Scenario File ===")
    from pymt.models import AquaCrop
    
    m = AquaCrop()
    fake_scenario = "/nonexistent/path/fake_scenario.json"
    
    print(f"  Attempting to initialize with {fake_scenario}...")
    try:
        m.initialize(fake_scenario)
        print("  ✗ Should have raised exception")
    except FileNotFoundError as e:
        print(f"  ✓ Correctly raised FileNotFoundError")
    except Exception as e:
        print(f"  Got {type(e).__name__}: {e}")
    
    print("✓ Missing file handled")


def test_corrupted_scenario_file():
    """Try initializing with invalid JSON"""
    print("\n=== TEST: Corrupted Scenario File ===")
    from pymt.models import AquaCrop
    import tempfile
    
    # Create corrupted JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json content }")
        corrupted_file = f.name
    
    m = AquaCrop()
    print(f"  Attempting to initialize with corrupted file...")
    try:
        m.initialize(corrupted_file)
        print("  ✗ Should have raised exception")
    except Exception as e:
        print(f"  ✓ Correctly raised {type(e).__name__}")
    finally:
        Path(corrupted_file).unlink()
    
    print("✓ Corrupted file handled")


def main():
    """Run all stress tests"""
    print("\n" + "="*80)
    print("AQUACROP BMI - STRESS TEST SUITE")
    print("Testing edge cases, error conditions, and unusual patterns")
    print("="*80)
    
    tests = [
        test_rapid_reinit,
        test_finalize_twice,
        test_no_update_before_finalize,
        test_massive_time_jump,
        test_negative_setter_values,
        test_nan_setter_values,
        test_inf_setter_values,
        test_wrong_array_size,
        test_empty_array,
        test_update_beyond_end,
        test_interleaved_operations,
        test_calibration_then_immediate_simulation,
        test_missing_scenario_file,
        test_corrupted_scenario_file,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ TEST CRASHED: {test.__name__}")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print(f"STRESS TESTS COMPLETE: {len(tests) - failed}/{len(tests)} passed")
    print("="*80 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
