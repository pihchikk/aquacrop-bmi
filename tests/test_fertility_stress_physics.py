#!/usr/bin/env python3
"""
Regression tests for two confirmed physics bugs in the Fortran core:

1. Canopy cover under calibrated soil-fertility stress must never exceed
   the unstressed canopy cover for the same crop/weather. The pre-fix
   DetermineCCiGDD/DetermineCCi code re-derived CCiActual from the
   canopy-cover-vs-time curve by dividing CCxAdjusted back up by
   (1 - RedCCx/100) once canopy had plateaued near CCx, which could
   produce a stressed CC higher than the unstressed reference.

2. crop__biomass must stay finite for the whole season when calibrated
   soil-fertility stress is active. The pre-fix CalculateETpot ageing
   correction was an unbounded linear decline in Kc (no ceiling on
   elapsed days past L12+5), which could drive Kc, and thus SumKcTop /
   WPi, negative for long-cycle crops, producing NaN via log() of a
   negative ratio.

Both bugs are gated on calibrated fertility stress being active
(management_fertility_stress > 0 and Crop.StressResponse.Calibrated).
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest

BASE_SCENARIO = Path(__file__).parent.parent / "scenarios" / "AquacropSimulationData.json"
SKIP_REASON = f"Base scenario not found at {BASE_SCENARIO}"


def _make_scenario(fertility_stress: int, tmp_dir: Path) -> Path:
    """Load the bundled Wheat scenario, override fertility_stress, keep
    only the first season, and write it to a fresh temp file."""
    config = json.loads(BASE_SCENARIO.read_text())
    config["fertility_stress"] = fertility_stress
    config["seasons"] = config["seasons"][:1]

    out_path = tmp_dir / f"scenario_fs{fertility_stress}.json"
    out_path.write_text(json.dumps(config))
    return out_path


def _run_season(scenario_path: Path, n_days: int):
    """Run n_days of simulation, return (biomass[], canopy_cover[])."""
    from aquacrop_bmi_babel import AquaCrop

    m = AquaCrop()
    m.initialize(str(scenario_path))

    biomass = np.empty(n_days)
    canopy = np.empty(n_days)
    dest = np.empty(1, dtype=np.float64)

    for day in range(n_days):
        m.update()
        m.get_value("crop__biomass", dest)
        biomass[day] = dest[0]
        m.get_value("crop__canopy_cover", dest)
        canopy[day] = dest[0]

    m.finalize()
    return biomass, canopy


@pytest.fixture(scope="module")
def tmp_scenario_dir():
    if not BASE_SCENARIO.exists():
        pytest.skip(SKIP_REASON)
    d = Path(tempfile.mkdtemp(prefix="aquacrop_fertility_stress_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


N_DAYS = 130  # covers most of the ~137-day Wheat cycle embedded in the scenario


def test_biomass_finite_under_calibrated_fertility_stress(tmp_scenario_dir):
    """Bug 2 regression: biomass must never go NaN under fertility stress."""
    scenario = _make_scenario(fertility_stress=50, tmp_dir=tmp_scenario_dir)
    biomass, _ = _run_season(scenario, N_DAYS)

    assert np.all(np.isfinite(biomass)), (
        f"biomass went non-finite under fertility stress: "
        f"first bad day={np.argmax(~np.isfinite(biomass))}, values={biomass}"
    )
    assert biomass[-1] >= 0.0


def test_canopy_cover_stress_never_exceeds_unstressed(tmp_scenario_dir):
    """Bug 1 regression: stressed canopy cover must never exceed the
    unstressed reference for the same crop/weather/day."""
    unstressed_scenario = _make_scenario(fertility_stress=0, tmp_dir=tmp_scenario_dir)
    stressed_scenario = _make_scenario(fertility_stress=50, tmp_dir=tmp_scenario_dir)

    _, canopy_unstressed = _run_season(unstressed_scenario, N_DAYS)
    _, canopy_stressed = _run_season(stressed_scenario, N_DAYS)

    assert np.all(np.isfinite(canopy_unstressed))
    assert np.all(np.isfinite(canopy_stressed))

    tolerance = 1e-6
    violations = np.where(canopy_stressed > canopy_unstressed + tolerance)[0]
    assert len(violations) == 0, (
        f"stressed CC exceeded unstressed CC on days {violations.tolist()}: "
        f"stressed={canopy_stressed[violations]}, "
        f"unstressed={canopy_unstressed[violations]}"
    )


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
