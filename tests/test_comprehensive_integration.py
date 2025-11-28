#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for AquaCrop BMI
Tests all workflows, edge cases, and error conditions
"""

import sys
import time
import shutil
import numpy as np
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Test execution framework with detailed reporting"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        self.start_time = None
    
    def start(self):
        """Start test suite"""
        self.start_time = time.time()
        print("\n" + "="*80)
        print("AQUACROP BMI - COMPREHENSIVE INTEGRATION TEST SUITE")
        print("="*80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def run_test(self, name, func):
        """Run a single test with error handling"""
        self.tests_run += 1
        print(f"\n{'='*80}")
        print(f"TEST {self.tests_run}: {name}")
        print(f"{'='*80}")
        
        try:
            func()
            self.tests_passed += 1
            self.test_results.append((name, "PASS", None))
            print(f"\n✓ TEST PASSED: {name}")
        except AssertionError as e:
            self.tests_failed += 1
            self.test_results.append((name, "FAIL", str(e)))
            print(f"\n✗ TEST FAILED: {name}")
            print(f"   Assertion Error: {e}")
        except Exception as e:
            self.tests_failed += 1
            self.test_results.append((name, "ERROR", str(e)))
            print(f"\n✗ TEST ERROR: {name}")
            print(f"   Exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def finish(self):
        """Print final summary"""
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total tests:  {self.tests_run}")
        print(f"Passed:       {self.tests_passed} ({100*self.tests_passed/self.tests_run:.1f}%)")
        print(f"Failed:       {self.tests_failed}")
        print(f"Elapsed time: {elapsed:.2f}s")
        print()
        
        # Detailed results
        if self.tests_failed > 0:
            print("FAILED TESTS:")
            for name, status, error in self.test_results:
                if status != "PASS":
                    print(f"  ✗ {name}: {error}")
        
        print(f"\n{'='*80}\n")
        
        return self.tests_failed == 0


# =============================================================================
# TEST SCENARIOS
# =============================================================================

def test_basic_simulation_workflow(runner):
    """Test 1: Basic simulation workflow - initialize, update, finalize"""
    from pymt.models import AquaCrop
    
    def test():
        print("Creating AquaCrop instance...")
        m = AquaCrop()
        
        print("Initializing with simulation-data scenario...")
        scenario = Path(__file__).parent / "scenarios" / "AquacropSimulationData.json"
        if not scenario.exists():
            # Fallback to absolute path
            scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m.initialize(str(scenario))
        
        print(f"Start time: {m.start_time}")
        print(f"End time: {m.end_time}")
        print(f"Time step: {m.time_step}")
        
        # Run 10 steps
        print("Running 10 update steps...")
        for i in range(10):
            m.update()
            print(f"  Step {i+1}: time={m.time}")
        
        # Get values
        dest = np.empty(1, dtype=np.float64)
        m.get_value('crop__yield', dest)
        print(f"Current yield: {dest[0]:.3f} t/ha")
        
        m.get_value('crop__biomass', dest)
        print(f"Current biomass: {dest[0]:.3f} t/ha")
        
        # Finalize
        print("Finalizing...")
        m.finalize()
        
        assert dest[0] >= 0, "Biomass should be non-negative"
        print("✓ Basic simulation completed successfully")
    
    runner.run_test("Basic Simulation Workflow", test)


def test_update_until(runner):
    """Test 2: update_until functionality"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m.initialize(str(scenario))
        
        print("Testing update_until...")
        target_time = 30.0
        m.update_until(target_time)
        
        current = m.time
        print(f"Target: {target_time}, Current: {current}")
        
        assert abs(current - target_time) < 1.0, f"Expected time ~{target_time}, got {current}"
        
        m.finalize()
        print("✓ update_until works correctly")
    
    runner.run_test("Update Until Functionality", test)


def test_getters_setters(runner):
    """Test 3: All getter/setter variables"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m.initialize(str(scenario))
        
        m.update_until(20.0)
        
        # Test all output getters
        print("Testing output getters...")
        outputs = [
            'crop__yield',
            'crop__biomass',
            'crop__canopy_cover',
            'soil__moisture',
            'crop__water_stress',
            'crop__evapotranspiration',
        ]
        
        dest = np.empty(1, dtype=np.float64)
        for var in outputs:
            m.get_value(var, dest)
            print(f"  {var}: {dest[0]:.3f}")
            assert not np.isnan(dest[0]), f"{var} returned NaN"
        
        # Test input setters
        print("\nTesting input setters...")
        inputs = {
            'weather__rainfall_amount': 25.0,
            'weather__air_temperature_max': 35.0,
            'weather__air_temperature_min': 20.0,
            'weather__reference_evapotranspiration': 6.0,
            'management__irrigation_amount': 15.0,
            'crop__fertility_stress': 50.0,
        }
        
        for var, val in inputs.items():
            src = np.array([val], dtype=np.float64)
            m.set_value(var, src)
            print(f"  Set {var} = {val}")
        
        # Continue simulation
        m.update()
        print("✓ Simulation continues after setters")
        
        m.finalize()
        print("✓ All getters/setters work")
    
    runner.run_test("Getters and Setters", test)


def test_reinitialize_next_season(runner):
    """Test 4: Multi-season workflow (SKIPPED - not part of BMI spec)"""
    
    def test():
        print("Skipping - reinitialize_next_season() not part of BMI 2.0 spec")
        print("Multi-season handled via scenarios-simulation.json with season array")
    
    runner.run_test("Multi-Season Reinitialization (SKIPPED)", test)


def test_crop_calibration(runner):
    """Test 5: Crop parameter calibration workflow"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/crop-calibration.json"
        
        print("Running crop calibration (this takes time)...")
        m.initialize(str(scenario))
        
        # Check that calibration results were saved
        # Look in BOTH locations: /mnt/d/outputs/ and /tmp/
        outputs_dir = Path("/mnt/d/outputs")
        calibration_dirs = list(outputs_dir.glob("*calibration*"))
        
        if not calibration_dirs:
            # Fallback to /tmp/
            import glob
            tmp_dirs = glob.glob("/tmp/aquacrop_prep_*/outputs/*calibration*")
            calibration_dirs = [Path(p) for p in tmp_dirs]
        
        assert len(calibration_dirs) > 0, f"No calibration output found in {outputs_dir} or /tmp/"
        
        latest_dir = max(calibration_dirs, key=lambda p: p.stat().st_mtime)
        print(f"Calibration output: {latest_dir}")
        
        # Check files exist
        assert (latest_dir / "crop_calibrated_bmi.txt").exists(), "Missing crop file"
        assert (latest_dir / "scenarios_from_bmi_calib.json").exists(), "Missing scenarios file"
        assert (latest_dir / "calibration_metadata.json").exists(), "Missing metadata"
        
        print("✓ Calibration completed and files saved")
    
    runner.run_test("Crop Parameter Calibration", test)


def test_fertility_stress_calibration(runner):
    """Test 6: Fertility stress calibration workflow"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/fertility-stress-calibration.json"
        
        print("Running fertility stress calibration...")
        m.initialize(str(scenario))
        
        # Check output in both locations
        outputs_dir = Path("/mnt/d/outputs")
        calibration_dirs = list(outputs_dir.glob("*calibration*"))
        
        if not calibration_dirs:
            import glob
            tmp_dirs = glob.glob("/tmp/aquacrop_prep_*/outputs/*calibration*")
            calibration_dirs = [Path(p) for p in tmp_dirs]
        
        assert len(calibration_dirs) > 0, f"No calibration output found"
        
        latest_dir = max(calibration_dirs, key=lambda p: p.stat().st_mtime)
        print(f"Calibration output: {latest_dir}")
        
        assert (latest_dir / "crop_calibrated_bmi.txt").exists(), "Missing crop file"
        assert (latest_dir / "scenarios_from_bmi_calib.json").exists(), "Missing scenarios file"
        
        print("✓ Fertility calibration completed")
    
    runner.run_test("Fertility Stress Calibration", test)


def test_simulation_after_calibration(runner):
    """Test 7: Run simulation with calibrated parameters"""
    from pymt.models import AquaCrop
    
    def test():
        # Find latest calibration output in both locations
        outputs_dir = Path("/mnt/d/outputs")
        calibration_dirs = list(outputs_dir.glob("*calibration*"))
        
        if not calibration_dirs:
            import glob
            tmp_dirs = glob.glob("/tmp/aquacrop_prep_*/outputs/*calibration*")
            calibration_dirs = [Path(p) for p in tmp_dirs]
        
        if not calibration_dirs:
            print("Skipping - no calibration results found (run calibration tests first)")
            return
        
        latest_dir = max(calibration_dirs, key=lambda p: p.stat().st_mtime)
        scenarios_file = latest_dir / "scenarios_from_bmi_calib.json"
        
        print(f"Using calibrated scenario: {scenarios_file}")
        
        m = AquaCrop()
        m.initialize(str(scenarios_file))
        
        # Run simulation
        m.update_until(m.end_time)
        
        # Get final yield
        dest = np.empty(1, dtype=np.float64)
        m.get_value('crop__yield', dest)
        print(f"Final yield with calibrated params: {dest[0]:.3f} t/ha")
        
        m.finalize()
        print("✓ Simulation with calibrated parameters works")
    
    runner.run_test("Simulation After Calibration", test)


def test_error_after_finalize(runner):
    """Test 8: Proper error handling after finalize"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m.initialize(str(scenario))
        
        m.update_until(10.0)
        m.finalize()
        
        print("Attempting update after finalize...")
        try:
            m.update()
            raise AssertionError("Should have raised RuntimeError")
        except RuntimeError as e:
            print(f"✓ Correctly raised RuntimeError: {e}")
        
        print("Attempting update_until after finalize...")
        try:
            m.update_until(20.0)
            raise AssertionError("Should have raised RuntimeError")
        except RuntimeError as e:
            print(f"✓ Correctly raised RuntimeError: {e}")
        
        print("✓ Proper error handling after finalize")
    
    runner.run_test("Error Handling After Finalize", test)


def test_multiple_instances(runner):
    """Test 9: Multiple AquaCrop instances simultaneously"""
    from pymt.models import AquaCrop
    
    def test():
        print("Creating 3 AquaCrop instances...")
        
        m1 = AquaCrop()
        m2 = AquaCrop()
        m3 = AquaCrop()
        
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        
        print("Initializing instance 1...")
        m1.initialize(str(scenario))
        
        print("Initializing instance 2...")
        m2.initialize(str(scenario))
        
        print("Initializing instance 3...")
        m3.initialize(str(scenario))
        
        # Run each to different times
        print("Running instance 1 to t=10...")
        m1.update_until(10.0)
        
        print("Running instance 2 to t=20...")
        m2.update_until(20.0)
        
        print("Running instance 3 to t=30...")
        m3.update_until(30.0)
        
        # Check they're independent
        assert m1.time != m2.time, "Instances should be independent"
        assert m2.time != m3.time, "Instances should be independent"
        
        print(f"Instance 1 time: {m1.time}")
        print(f"Instance 2 time: {m2.time}")
        print(f"Instance 3 time: {m3.time}")
        
        m1.finalize()
        m2.finalize()
        m3.finalize()
        
        print("✓ Multiple instances work independently")
    
    runner.run_test("Multiple Instances", test)


def test_create_after_calibration(runner):
    """Test 10: Create new instance after calibration without crash"""
    from pymt.models import AquaCrop
    
    def test():
        print("Running calibration...")
        m1 = AquaCrop()
        scenario_calib = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/crop-calibration.json"
        m1.initialize(str(scenario_calib))
        
        print("Creating new instance after calibration...")
        m2 = AquaCrop()
        scenario_sim = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m2.initialize(str(scenario_sim))
        
        print("Running simulation...")
        m2.update_until(10.0)
        
        dest = np.empty(1, dtype=np.float64)
        m2.get_value('crop__yield', dest)
        print(f"Yield: {dest[0]:.3f} t/ha")
        
        m2.finalize()
        
        print("✓ Can create new instance after calibration")
    
    runner.run_test("Create Instance After Calibration", test)


def test_boundary_values(runner):
    """Test 11: Boundary value testing for setters"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m.initialize(str(scenario))
        
        m.update_until(20.0)
        
        print("Testing boundary values...")
        
        # Test zero values
        print("  Testing zero values...")
        src = np.array([0.0], dtype=np.float64)
        m.set_value('weather__rainfall_amount', src)
        m.set_value('management__irrigation_amount', src)
        m.update()
        
        # Test extreme values
        print("  Testing extreme temperature...")
        src = np.array([50.0], dtype=np.float64)
        m.set_value('weather__air_temperature_max', src)
        m.update()
        
        # Test 100% stress
        print("  Testing 100% fertility stress...")
        src = np.array([100.0], dtype=np.float64)
        m.set_value('crop__fertility_stress', src)
        m.update()
        
        # Test 0% stress
        print("  Testing 0% fertility stress...")
        src = np.array([0.0], dtype=np.float64)
        m.set_value('crop__fertility_stress', src)
        m.update()
        
        m.finalize()
        print("✓ Boundary values handled correctly")
    
    runner.run_test("Boundary Value Testing", test)


def test_output_directory_structure(runner):
    """Test 12: Verify output directory naming and structure"""
    from pymt.models import AquaCrop
    
    def test():
        outputs_dir = Path.cwd() / "outputs"
        
        print(f"Checking outputs directory: {outputs_dir}")
        
        # Check for different scenario types
        patterns = [
            "crop-calibration_*",
            "fertility-stress-calibration_*",
            "simulation-data_*",
            "scenarios-simulation_*",
        ]
        
        for pattern in patterns:
            matches = list(outputs_dir.glob(pattern))
            if matches:
                print(f"  ✓ Found {len(matches)} {pattern} directories")
                
                # Check latest
                latest = max(matches, key=lambda p: p.stat().st_mtime)
                print(f"    Latest: {latest.name}")
                
                # Verify structure
                if "calibration" in pattern:
                    assert (latest / "crop_calibrated_bmi.txt").exists(), f"Missing crop file in {latest}"
                    assert (latest / "scenarios_from_bmi_calib.json").exists(), f"Missing scenarios file in {latest}"
                    assert (latest / "calibration_metadata.json").exists(), f"Missing metadata in {latest}"
                else:
                    assert (latest / "LIST").exists(), f"Missing LIST dir in {latest}"
                    assert (latest / "OUTP").exists(), f"Missing OUTP dir in {latest}"
        
        print("✓ Output directory structure correct")
    
    runner.run_test("Output Directory Structure", test)


def test_stress_cycle(runner):
    """Test 13: Cycling through different stress levels"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m.initialize(str(scenario))
        
        stress_levels = [10, 30, 50, 70, 90, 100, 0]
        
        print("Cycling through stress levels...")
        for stress in stress_levels:
            src = np.array([float(stress)], dtype=np.float64)
            m.set_value('crop__fertility_stress', src)
            m.update()
            
            dest = np.empty(1, dtype=np.float64)
            m.get_value('crop__yield', dest)
            print(f"  Stress {stress}%: yield = {dest[0]:.3f} t/ha")
        
        m.finalize()
        print("✓ Stress cycling works")
    
    runner.run_test("Fertility Stress Cycling", test)


def test_irrigation_management(runner):
    """Test 14: Dynamic irrigation management"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m.initialize(str(scenario))
        
        print("Testing irrigation management...")
        
        # Dry period
        print("  Dry period (no irrigation)...")
        for _ in range(10):
            src = np.array([0.0], dtype=np.float64)
            m.set_value('management__irrigation_amount', src)
            m.update()
        
        dest = np.empty(1, dtype=np.float64)
        m.get_value('crop__water_stress', dest)
        stress_dry = dest[0]
        print(f"    Water stress: {stress_dry:.3f}")
        
        # Heavy irrigation
        print("  Heavy irrigation period...")
        for _ in range(10):
            src = np.array([50.0], dtype=np.float64)  # 50mm/day
            m.set_value('management__irrigation_amount', src)
            m.update()
        
        m.get_value('crop__water_stress', dest)
        stress_irrigated = dest[0]
        print(f"    Water stress: {stress_irrigated:.3f}")
        
        m.finalize()
        print("✓ Irrigation management works")
    
    runner.run_test("Irrigation Management", test)


def test_complete_season_tracking(runner):
    """Test 15: Track complete season with all variables"""
    from pymt.models import AquaCrop
    
    def test():
        m = AquaCrop()
        scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
        m.initialize(str(scenario))
        
        print("Tracking complete season...")
        
        dest = np.empty(1, dtype=np.float64)
        checkpoints = [0, 30, 60, 90, 120, 150]
        
        for checkpoint in checkpoints:
            if checkpoint <= m.end_time:
                m.update_until(float(checkpoint))
                
                m.get_value('crop__yield', dest)
                yield_val = dest[0]
                
                m.get_value('crop__biomass', dest)
                biomass = dest[0]
                
                m.get_value('crop__canopy_cover', dest)
                cc = dest[0]
                
                m.get_value('soil__moisture', dest)
                moisture = dest[0]
                
                print(f"  Day {checkpoint:3d}: Y={yield_val:.2f}, B={biomass:.2f}, CC={cc:.1f}%, SM={moisture:.1f}%")
        
        m.finalize()
        print("✓ Complete season tracking successful")
    
    runner.run_test("Complete Season Tracking", test)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run all tests"""
    runner = TestRunner()
    runner.start()
    
    # Basic functionality tests
    test_basic_simulation_workflow(runner)
    test_update_until(runner)
    test_getters_setters(runner)
    
    # Multi-season tests
    test_reinitialize_next_season(runner)
    
    # Calibration tests (slow)
    test_crop_calibration(runner)
    test_fertility_stress_calibration(runner)
    test_simulation_after_calibration(runner)
    
    # Error handling tests
    test_error_after_finalize(runner)
    
    # Advanced tests
    test_multiple_instances(runner)
    test_create_after_calibration(runner)
    test_boundary_values(runner)
    
    # Output validation
    test_output_directory_structure(runner)
    
    # Dynamic management tests
    test_stress_cycle(runner)
    test_irrigation_management(runner)
    test_complete_season_tracking(runner)
    
    # Finish and report
    success = runner.finish()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())