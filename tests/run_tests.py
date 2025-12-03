#!/usr/bin/env python3
"""
Quick Test Runner - Run specific test suites
"""

import sys
from pathlib import Path


def print_menu():
    """Display test menu"""
    print("\n" + "="*60)
    print("AQUACROP BMI TEST RUNNER")
    print("="*60)
    print("\n1. Complete Integration Tests (15 tests, ~30 min)")
    print("   - All workflows, calibration, multi-season")
    print("\n2. Stress Tests (14 tests, ~10 min)")
    print("   - Edge cases, error handling, unusual patterns")
    print("\n3. Quick Smoke Test (3 tests, ~2 min)")
    print("   - Basic functionality only")
    print("\n4. Exit")
    print()


def run_integration_tests():
    """Run comprehensive integration tests"""
    print("\nRunning comprehensive integration tests...")
    import test_comprehensive_integration
    return test_comprehensive_integration.main()


def run_stress_tests():
    """Run stress tests"""
    print("\nRunning stress tests...")
    import test_stress
    return test_stress.main()


def run_smoke_tests():
    """Run quick smoke tests"""
    print("\nRunning quick smoke tests...")
    from pymt.models import AquaCrop
    import numpy as np
    
    print("\n=== SMOKE TEST 1: Basic Initialize/Update/Finalize ===")
    m = AquaCrop()
    scenario = "/mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel/scenarios/AquacropSimulationData.json"
    m.initialize(scenario)
    m.update_until(10.0)
    dest = np.empty(1, dtype=np.float64)
    m.get_value('crop__yield', dest)
    print(f"Yield at day 10: {dest[0]:.3f} t/ha")
    m.finalize()
    print("✓ Test 1 passed")
    
    print("\n=== SMOKE TEST 2: Getters/Setters ===")
    m = AquaCrop()
    m.initialize(scenario)
    m.update_until(20.0)
    src = np.array([25.0], dtype=np.float64)
    m.set_value('weather__rainfall_amount', src)
    m.update()
    m.get_value('crop__biomass', dest)
    print(f"Biomass after irrigation: {dest[0]:.3f} t/ha")
    m.finalize()
    print("✓ Test 2 passed")
    
    print("\n=== SMOKE TEST 3: Error After Finalize ===")
    m = AquaCrop()
    m.initialize(scenario)
    m.update_until(10.0)
    m.finalize()
    try:
        m.update()
        print("✗ Test 3 failed - should have raised error")
        return 1
    except RuntimeError:
        print("✓ Test 3 passed - correctly raised RuntimeError")
    
    print("\n✓ All smoke tests passed!")
    return 0


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        while True:
            print_menu()
            try:
                choice = input("Select test suite (1-4): ").strip()
                if choice in ['1', '2', '3', '4']:
                    break
                print("Invalid choice. Please enter 1-4.")
            except (KeyboardInterrupt, EOFError):
                print("\n\nExiting...")
                return 0
    
    if choice == '1':
        return run_integration_tests()
    elif choice == '2':
        return run_stress_tests()
    elif choice == '3':
        return run_smoke_tests()
    elif choice == '4':
        print("Exiting...")
        return 0
    else:
        print(f"Unknown choice: {choice}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
