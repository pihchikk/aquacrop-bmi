"""Regression test for the HarvestNow uninitialized-variable bug.

AdvanceOneTimeStep (aquacrop_fortran/run.f90) used to read its local
HarvestNow variable (via InitializeTransferAssimilates, step 8) before
ever writing it (step 13, the Cuttings section, later in the same
call). That's an uninitialized read whose value depends on stack
contents left by the caller. It happened to come up false through the
console entry point (StartTheProgram -> RunSimulation -> FileManagement)
but effectively true through the BMI entry point
(bmi_aquacrop%initialize/%update -> BMI_SimulateOneDay ->
AdvanceOneTimeStep), because the two call chains leave different stack
layouts before AdvanceOneTimeStep runs.

The effect: perennial assimilate storage (Bout) silently went to zero
for the rest of the season on the Ottawa/AlfOttawaGDD BMI fixture,
starving the dynamic soil-fertility-stress relaxation, freezing the
canopy-cover ceiling, and stalling canopy cover at ~55.8% by day 163
instead of climbing to ~57.6% (matching both the console entry point
and official AquaCrop ground truth).

This test drives the Ottawa fixture through the BMI entry point
specifically (not the console path) and asserts canopy cover reaches
the correct ~57.6% by day 163, so a reintroduced uninitialized-read bug
in this call chain shows up here even if console-mode testing stays
green.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

FIXTURE_PRM = Path(__file__).parent / "fixtures" / "ottawa_bmi" / "LIST" / "Ottawa.PRM"


@pytest.fixture(scope="module")
def ottawa_bmi_model():
    if not FIXTURE_PRM.exists():
        pytest.skip(f"Ottawa BMI fixture not found at {FIXTURE_PRM}")

    try:
        from aquacrop_bmi_babel import AquaCrop
    except ImportError as e:
        pytest.skip(f"aquacrop_bmi_babel compiled extension not available: {e}")

    m = AquaCrop()
    m.initialize(str(FIXTURE_PRM))
    yield m
    m.finalize()


def test_bmi_path_canopy_cover_does_not_stall(ottawa_bmi_model):
    """Canopy cover must reach ~57.6% by day 163, not stall at ~55.8%."""
    m = ottawa_bmi_model
    cc = np.empty(1, dtype=np.float64)
    biomass = np.empty(1, dtype=np.float64)

    for _ in range(163):
        m.update()

    m.get_value("crop__canopy_cover", cc)
    m.get_value("crop__biomass", biomass)

    # The pre-fix (buggy HarvestNow) trajectory plateaus at ~55.8%.
    # The fixed trajectory (matching console mode and OUTP_REF ~57.9%) reaches ~57.6%.
    assert cc[0] > 57.0, (
        f"canopy cover stalled at {cc[0]:.2f}% by day 163 (expected ~57.6%) - "
        f"this is the HarvestNow uninitialized-read regression"
    )
    assert cc[0] < 59.0, f"canopy cover implausibly high: {cc[0]:.2f}%"
    assert np.isfinite(biomass[0]) and biomass[0] > 0


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
