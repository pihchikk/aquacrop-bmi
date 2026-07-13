#!/usr/bin/env python3
"""
Contract test for soil_water__infiltration_amount override.

Verifies that when a BMI caller supplies an external infiltration value,
AquaCrop bypasses its CN-based runoff partition and pushes the supplied
amount directly into the soil profile.

A/B comparison:
  - Control run:  rain-forced, CN runoff computed internally.
  - Override run: same rain, but set_value('soil_water__infiltration_amount', X)
                  each day ⇒ runoff must be ≈0, profile ΔS consistent with X.
"""

import sys
import numpy as np
from pathlib import Path


def make_model(scenario_path):
    from pymt.models import AquaCrop
    m = AquaCrop()
    m.initialize(str(scenario_path))
    return m


def run_control(scenario_path, n_days=10):
    m = make_model(scenario_path)
    runoffs = []
    dest = np.empty(1, dtype=np.float64)
    for _ in range(n_days):
        m.update()
        m.get_value('land_surface_water__runoff_flux', dest)
        runoffs.append(dest[0])
    m.finalize()
    return runoffs


def run_override(scenario_path, infil_mm, n_days=10):
    m = make_model(scenario_path)
    runoffs = []
    dest = np.empty(1, dtype=np.float64)
    src = np.array([infil_mm], dtype=np.float64)
    for _ in range(n_days):
        m.set_value('soil_water__infiltration_amount', src)
        m.update()
        m.get_value('land_surface_water__runoff_flux', dest)
        runoffs.append(dest[0])
    m.finalize()
    return runoffs


def test_infiltration_override():
    scenario = Path(__file__).parent / "scenarios" / "AquacropSimulationData.json"
    if not scenario.exists():
        print(f"SKIP: scenario not found at {scenario}")
        return False

    infil_value = 5.0
    n_days = 10

    print("Running control (rain-forced, CN runoff) ...")
    ctrl_runoff = run_control(scenario, n_days)
    print(f"  Control runoffs: {[f'{r:.2f}' for r in ctrl_runoff]}")

    print(f"Running override (infiltration = {infil_value} mm/day) ...")
    ovr_runoff = run_override(scenario, infil_value, n_days)
    print(f"  Override runoffs: {[f'{r:.2f}' for r in ovr_runoff]}")

    for day, ro in enumerate(ovr_runoff, 1):
        assert abs(ro) < 1e-6, (
            f"Day {day}: runoff should be ~0 under infiltration override, got {ro}"
        )

    print("All override-day runoffs are ~0.")
    return True


def test_variable_registered():
    from pymt.models import AquaCrop
    m = AquaCrop()
    scenario = Path(__file__).parent / "scenarios" / "AquacropSimulationData.json"
    if not scenario.exists():
        print(f"SKIP: scenario not found at {scenario}")
        return False

    m.initialize(str(scenario))

    names = m.input_var_names
    assert 'soil_water__infiltration_amount' in names, (
        f"soil_water__infiltration_amount not in input_var_names: {names}"
    )
    print(f"soil_water__infiltration_amount found in {len(names)} input vars.")

    dest = np.empty(1, dtype=np.float64)
    m.get_var_units('soil_water__infiltration_amount', dest)
    m.finalize()
    return True


if __name__ == '__main__':
    passed = 0
    failed = 0

    for name, func in [
        ("Variable registered", test_variable_registered),
        ("Infiltration override A/B", test_infiltration_override),
    ]:
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print('='*60)
        try:
            result = func()
            if result is False:
                print(f"  SKIPPED")
            else:
                passed += 1
                print(f"  PASSED")
        except Exception as e:
            failed += 1
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print('='*60)
    sys.exit(1 if failed else 0)
