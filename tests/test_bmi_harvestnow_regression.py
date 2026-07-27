"""Regression test for HarvestNow's cross-day persistence (transfer-of-assimilates
timing on Ottawa/AlfOttawaGDD's scheduled cuttings).

History, in three stages:

1. **Originally**: `AdvanceOneTimeStep` (`aquacrop_fortran/run.f90`) declared
   `HarvestNow` as a local variable and read it (via
   `InitializeTransferAssimilates`, step 8) before ever writing it (step 13,
   the Cuttings section, later in the same call) -- an uninitialized read
   whose value depended on stack contents left by the caller, differing
   between the console entry point (effectively `.false.`) and the BMI entry
   point (effectively `.true.`, by stack-layout coincidence).

2. **First fix (superseded)**: pinned `HarvestNow = .false.` at the top of
   every call, eliminating the undefined-behavior crash risk. This is
   *safe* but *semantically wrong*: official declares `HarvestNow` once in
   its own daily-loop caller (`FileManagement`) and threads it as an
   `intent(inout)` parameter across every call to `AdvanceOneTimeStep` --
   step 8 of day N+1 is meant to see day N's step-13 cutting result, a
   deliberate one-day lag. A local variable reset every call can never
   carry that lag, on either entry point -- so the pinned-`.false.` fix
   made the "zero out storage fraction on harvest day" branch in
   `InitializeTransferAssimilates` permanently dead code, on the console
   path too, not just BMI. This test's original version only asserted a
   loose bound (`crop__canopy_cover > 57.0` by day 163) that happened to
   still pass under this wrong-but-safe behavior, so it protected against
   a return to undefined behavior while quietly legitimizing incorrect
   behavior.

3. **Real fix**: `HarvestNow` hoisted to module-level persistent state
   (`GetHarvestNowPersisted`/`SetHarvestNowPersisted`, `global.f90`), reset
   once per run (`FileManagement` for console, the BMI per-run setup in
   `startunit.F90`) rather than once per day -- matching official's
   parameter-threading semantics exactly. See
   `docs/bmi/PHASE2_REBASELINE.md` (aquacrop-rs) for the full root-cause
   trail and the version-matrix verification (`ottawa-baseline` and
   `shallow-groundwater` move from FAIL to byte-exact PASS against
   OFFICIAL v7.3 with this fix).

Verified against both buggy predecessors (not just stage 2). Stage 1
(commit `788e147`, the parent of the pinning fix `fef8c8e`) predates the
`tests/fixtures/ottawa_bmi` fixture itself, so it was exercised by
copying the fixture's data files (inert w.r.t. the bug -- `Ottawa.PRM`,
`.CRO`, `.SOL`, `.MAN`) into a worktree at that commit. As expected of
genuine uninitialized-stack-read undefined behavior, its manifestation is
unstable across calling context: under pytest's deeper call stack it
crashes outright (segfault, pytest exit code 2, no assertions reached);
invoked directly with a shallower call stack it instead runs to
completion but on a completely different trajectory with no cutting
event at all (canopy cover climbs monotonically to a ~52% plateau
instead of crashing to ~28.8% near day 104; day 163 biomass 11.53 vs the
correct 9.17). Both manifestations fail this test, just via different
mechanisms -- which is the expected signature of true UB, not a property
to force into one deterministic shape.

What this test checks, and why (correcting an earlier draft of it)
--------------------------------------------------------------------
The scheduled cutting on day 104 of this fixture's 163-day season is
**not** itself timing-sensitive to this bug: `Ottawa.MAN`'s cutting
schedule is evaluated as a pure day-count against an explicit day list
(`InitializeTransferAssimilates`'s "Start of storage period?" check, step
13), independent of `HarvestNow`'s stale-vs-fresh value at step 8 -- a
direct day-by-day comparison of the stage-2 and stage-3 trajectories
(captured while writing this test) confirms canopy cover crashes on
*exactly* day 104 under both. An earlier draft of this test asserted
"day 104, not day 105" as the discriminator; that claim was wrong (traced
to a separate exploration against a different, 3-run Ottawa fixture) and
has been corrected here rather than left in.

What *does* differ is **biomass**, from day 104 onward: `InitializeTransferAssimilates`
computes `FracAssim` (and, downstream, `Bin`/`Bout`) using `HarvestNow`,
and under stage 2 that value is permanently stale/wrong, producing a
small (~0.02 t/ha), persistent biomass offset starting the day of the
cut and carried forward unchanged for the rest of the season. This test
checks biomass at day 104 itself (catching the bug at its point of
origin) and at day 163 (the season-end value the original test checked,
now to a precise tolerance instead of a loose bound).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

FIXTURE_PRM = Path(__file__).parent / "fixtures" / "ottawa_bmi" / "LIST" / "Ottawa.PRM"

# Ground truth for this fixture, captured from the fixed BMI path itself and
# cross-checked for mechanism correctness against the console binary's
# byte-exact match to OFFICIAL v7.3 on the equivalent 3-run Ottawa project
# (same AlfOttawaGDD.CRO, same Ottawa.MAN cutting schedule, same underlying
# Fortran code path -- console and BMI now share it identically, which is
# the whole point of the persisted-HarvestNow fix). No independent OFFICIAL
# run exists for this exact single-season 163-day fixture, so mechanism
# correctness (not an independent absolute cross-check) is what's being
# leaned on here; noted explicitly rather than overclaiming.
CUT_DAY = 104
EXPECTED_CUT_DAY_CC = 28.797939
EXPECTED_CUT_DAY_BIOMASS = 7.901802
FINAL_DAY = 163
EXPECTED_FINAL_CC = 57.859360
EXPECTED_FINAL_BIOMASS = 9.170674
TOLERANCE = 0.01


@pytest.fixture(scope="module")
def ottawa_bmi_trajectory():
    if not FIXTURE_PRM.exists():
        pytest.skip(f"Ottawa BMI fixture not found at {FIXTURE_PRM}")

    try:
        from aquacrop_bmi_babel import AquaCrop
    except ImportError as e:
        pytest.skip(f"aquacrop_bmi_babel compiled extension not available: {e}")

    m = AquaCrop()
    m.initialize(str(FIXTURE_PRM))

    cc_dest = np.empty(1, dtype=np.float64)
    biomass_dest = np.empty(1, dtype=np.float64)
    cc_by_day = []
    biomass_by_day = []
    for _ in range(FINAL_DAY):
        m.update()
        m.get_value("crop__canopy_cover", cc_dest)
        m.get_value("crop__biomass", biomass_dest)
        cc_by_day.append(float(cc_dest[0]))
        biomass_by_day.append(float(biomass_dest[0]))
    m.finalize()

    return cc_by_day, biomass_by_day


def test_cutting_day_is_unaffected_by_this_bug(ottawa_bmi_trajectory):
    """Sanity check, not the regression itself: the schedule-driven cutting
    day (and the canopy-cover value it produces) is independent of
    HarvestNow's persistence and must land on day 104 either way. Confirms
    the fixture/harness are wired correctly before the biomass checks
    below attribute a divergence to the right mechanism."""
    cc_by_day, _ = ottawa_bmi_trajectory
    assert cc_by_day[CUT_DAY - 1] == pytest.approx(EXPECTED_CUT_DAY_CC, abs=TOLERANCE), (
        f"day {CUT_DAY} canopy cover {cc_by_day[CUT_DAY - 1]:.6f}% != expected "
        f"{EXPECTED_CUT_DAY_CC:.6f}% -- the cutting schedule itself has moved, which "
        f"is a different, unrelated regression from the one this file guards"
    )


def test_biomass_diverges_from_cut_day_under_stale_harvestnow(ottawa_bmi_trajectory):
    """The actual regression: biomass at the cut day itself must match ground
    truth precisely. Confirmed (while writing this test) to fail by ~0.02
    t/ha against the pinned-HarvestNow-always-false build -- InitializeTransferAssimilates
    computing FracAssim/Bin/Bout from a stale HarvestNow produces a small,
    persistent biomass offset starting exactly here."""
    _, biomass_by_day = ottawa_bmi_trajectory
    cut_day_biomass = biomass_by_day[CUT_DAY - 1]
    assert cut_day_biomass == pytest.approx(EXPECTED_CUT_DAY_BIOMASS, abs=TOLERANCE), (
        f"day {CUT_DAY} biomass {cut_day_biomass:.6f} != expected "
        f"{EXPECTED_CUT_DAY_BIOMASS:.6f} -- this is exactly the stale-HarvestNow "
        f"regression this test exists to catch"
    )


def test_bmi_path_matches_ground_truth_at_season_end(ottawa_bmi_trajectory):
    """Canopy cover and biomass at day 163 must match the fixed trajectory's
    ground truth precisely, not just clear a loose bound (the original
    version of this test asserted only `> 57.0`, which the pinned-
    HarvestNow-always-false build also happened to clear)."""
    cc_by_day, biomass_by_day = ottawa_bmi_trajectory
    final_cc = cc_by_day[-1]
    final_biomass = biomass_by_day[-1]

    assert final_cc == pytest.approx(EXPECTED_FINAL_CC, abs=TOLERANCE), (
        f"day 163 canopy cover {final_cc:.6f}% != expected {EXPECTED_FINAL_CC:.6f}% -- "
        f"either a HarvestNow regression or a genuine, unrelated behavior change "
        f"that needs its own investigation"
    )
    assert final_biomass == pytest.approx(EXPECTED_FINAL_BIOMASS, abs=TOLERANCE), (
        f"day 163 biomass {final_biomass:.6f} != expected {EXPECTED_FINAL_BIOMASS:.6f}"
    )
    assert np.isfinite(final_biomass) and final_biomass > 0


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
