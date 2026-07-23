#!/usr/bin/env python3
"""
Regression tests for two confirmed physics bugs in the Fortran core:

1. Canopy cover under calibrated soil-fertility stress must never exceed
   the unstressed canopy cover for the same crop/weather. The pre-fix
   DetermineCCiGDD/DetermineCCi code re-derived CCiActual from the
   canopy-cover-vs-time curve by dividing CCxAdjusted back up by
   (1 - RedCCx/100) once canopy had plateaued near CCx, which could
   produce a stressed CC higher than the unstressed reference.

2. crop__biomass must stay finite AND accumulate as a well-formed curve
   for the whole season when calibrated soil-fertility stress is active.
   The pre-fix CalculateETpot ageing correction was an *unbounded* linear
   decline in Kc:

       Kc_local = Kc - (day - DayLastCut - (L12 + 5)) * (KcDecline/100) * CCxWithered

   with no ceiling on elapsed days. Fed a crop-coefficient ageing field
   large enough (e.g. a v7.3 ``KcDeclineCumul`` value of ~11, which the
   pre-fix reader misinterprets as an 11 %/day rate rather than an 11 %
   cumulative-at-maturity figure), this drives Kc — and hence SumKcTop /
   WPi — negative within the first weeks of the season, producing NaN via
   log() of a negative ratio. The v7.3 fix replaces it with a *bounded*
   exponential-shape decline normalised over [L12, LHarvest] plus
   version-gated reading of the ageing field, so Kc stays positive and
   biomass accumulates monotonically to a sane value.

Both bugs are gated on calibrated fertility stress being active
(management_fertility_stress > 0 and Crop.StressResponse.Calibrated).

Coverage note for bug 2
------------------------
Two biomass tests run, deliberately:

* ``test_biomass_finite_under_calibrated_fertility_stress`` uses the
  *shipped* Default Wheat (ageing field 0.09 %/day). That field is far
  too small to ever drive Kc negative, so this test cannot reproduce
  bug 2 and passes even against the buggy core. It is kept as a cheap
  smoke test for the common, in-distribution case.

* ``test_biomass_finite_under_ageing_stress_regime`` *injects* a crop
  file whose ageing field sits in bug 2's actual failing regime (the
  magnitude a v7.3 file carries). This one genuinely reproduces the NaN
  on the pre-fix core and asserts the bounded-decline repair. It is the
  test that would have caught the original bug.

The injection is verified to survive the crop-file (de)serialisation
round-trip by ``test_ageing_injection_survives_crop_file_roundtrip``.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from io import StringIO
from pathlib import Path

import numpy as np
import pytest

BASE_SCENARIO = Path(__file__).parent.parent / "scenarios" / "AquacropSimulationData.json"
SKIP_REASON = f"Base scenario not found at {BASE_SCENARIO}"

# Crop-coefficient ageing field value that puts the season in bug 2's
# failing regime. This is the magnitude a v7.3 crop file stores in the
# ageing field (KcDeclineCumul, a cumulative % at maturity); the pre-fix
# core misreads it as an 11 %/day rate, which drives Kc negative within
# ~2 weeks and NaNs biomass. The fixed core reads it as a bounded
# cumulative decline and stays finite.
AGEING_FIELD_FAILING_REGIME = 11.0
AGEING_FIELD_MARKER = "Decline of crop coefficient"

# Physical envelope for above-ground wheat biomass (t/ha) over a season.
# Comfortably brackets the fixed-core result while still rejecting a
# "finite but exploded" regression.
BIOMASS_SANE_MAX_T_HA = 30.0


def _inject_ageing_stress_crop(config: dict) -> None:
    """Rewrite the scenario's inline crop file so its crop-coefficient
    ageing field sits in bug 2's failing regime. Mutates ``config`` in
    place. Only the numeric value on the ageing line is changed; the line
    key/description and every other crop parameter are left untouched, so
    the Fortran core reads the new value positionally exactly as it would
    from a real crop file."""
    lines = config["crop_file"].splitlines()
    for i, line in enumerate(lines):
        if AGEING_FIELD_MARKER in line and ":" in line:
            _val, key = line.split(":", 1)
            lines[i] = f"{AGEING_FIELD_FAILING_REGIME:<15.3f}:{key}"
            break
    else:  # pragma: no cover - guards against a crop-file format change
        raise AssertionError(
            f"could not find ageing line ({AGEING_FIELD_MARKER!r}) in crop_file"
        )
    config["crop_file"] = "\n".join(lines)


def _make_scenario(
    fertility_stress: int, tmp_dir: Path, *, ageing_stress: bool = False
) -> Path:
    """Load the bundled Wheat scenario, override fertility_stress, keep
    only the first season, optionally inject a failing-regime ageing
    field, and write it to a fresh temp file."""
    config = json.loads(BASE_SCENARIO.read_text())
    config["fertility_stress"] = fertility_stress
    config["seasons"] = config["seasons"][:1]
    if ageing_stress:
        _inject_ageing_stress_crop(config)

    suffix = "_ageing" if ageing_stress else ""
    out_path = tmp_dir / f"scenario_fs{fertility_stress}{suffix}.json"
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


def _assert_bounded_finite_biomass(biomass: np.ndarray) -> None:
    """Assert the biomass trajectory shows the v7.3 bounded-decline
    behaviour, not just "not all NaN".

    Each check independently fails on the pre-fix core (which NaNs the
    whole trajectory from the first weeks onward):

    * finite everywhere          -> NaN trajectory fails outright
    * monotonic non-decreasing   -> biomass is cumulative; a negative-Kc
                                    excursion cannot make it drop
    * strictly positive at end   -> a real season accumulated biomass
    * within a physical envelope -> rejects a "finite but exploded"
                                    regression of the bounded formula
    """
    all_finite = bool(np.all(np.isfinite(biomass)))
    first_bad = int(np.argmax(~np.isfinite(biomass))) if not all_finite else -1
    assert all_finite, (
        f"biomass went non-finite under calibrated fertility stress in the "
        f"ageing regime (bug 2): first bad day={first_bad}, values={biomass}"
    )
    assert biomass[-1] > 0.0, f"season ended with non-positive biomass: {biomass[-1]}"
    drops = np.where(np.diff(biomass) < -1e-6)[0]
    assert drops.size == 0, (
        f"biomass decreased on days {drops.tolist()} — accumulation is not "
        f"monotonic, indicating a corrupted (negative-Kc) ageing correction: "
        f"{biomass[drops]} -> {biomass[drops + 1]}"
    )
    assert biomass[-1] < BIOMASS_SANE_MAX_T_HA, (
        f"biomass {biomass[-1]} t/ha exceeds the sane physical envelope "
        f"({BIOMASS_SANE_MAX_T_HA} t/ha) — bounded ageing decline looks broken"
    )


@pytest.fixture(scope="module")
def tmp_scenario_dir():
    if not BASE_SCENARIO.exists():
        pytest.skip(SKIP_REASON)
    d = Path(tempfile.mkdtemp(prefix="aquacrop_fertility_stress_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


N_DAYS = 130  # covers most of the ~137-day Wheat cycle embedded in the scenario


def test_biomass_finite_under_calibrated_fertility_stress(tmp_scenario_dir):
    """Bug 2 smoke test (common case): with the *shipped* crop and
    calibrated fertility stress active, biomass must stay finite.

    NB: the shipped ageing field (0.09 %/day) never drives Kc negative,
    so this passes on the pre-fix core too — it does not reproduce bug 2.
    See ``test_biomass_finite_under_ageing_stress_regime`` for the test
    that actually exercises the failing regime.
    """
    scenario = _make_scenario(fertility_stress=50, tmp_dir=tmp_scenario_dir)
    biomass, _ = _run_season(scenario, N_DAYS)

    assert np.all(np.isfinite(biomass)), (
        f"biomass went non-finite under fertility stress: "
        f"first bad day={np.argmax(~np.isfinite(biomass))}, values={biomass}"
    )
    assert biomass[-1] >= 0.0


def test_biomass_finite_under_ageing_stress_regime(tmp_scenario_dir):
    """Bug 2 regression (the one that matters): with a crop-coefficient
    ageing field in the failing regime and calibrated fertility stress
    active, biomass must stay finite and accumulate as a well-formed
    bounded-decline curve.

    Against the pre-fix core this NaNs the whole trajectory (unbounded
    Kc decline drives Kc negative within ~2 weeks); the v7.3 bounded
    decline keeps it finite and monotonic.
    """
    scenario = _make_scenario(
        fertility_stress=50, tmp_dir=tmp_scenario_dir, ageing_stress=True
    )
    biomass, _ = _run_season(scenario, N_DAYS)
    _assert_bounded_finite_biomass(biomass)


def test_ageing_injection_survives_crop_file_roundtrip():
    """The failing-regime injection is only meaningful if the modified
    ageing value survives the crop-file (de)serialisation the model does
    internally (loads_crop_file -> dump_crop_file -> Fortran reads it
    positionally). Verify the value is preserved as 11 across a full
    parse/emit/re-parse cycle, independent of the ETo/weather pipeline.
    """
    from aquacrop_bmi_babel.util import dump_crop_file, loads_crop_file

    config = {"crop_file": json.loads(BASE_SCENARIO.read_text())["crop_file"]}
    _inject_ageing_stress_crop(config)

    name, index, params = loads_crop_file(config["crop_file"])
    key = next(k for k in index if AGEING_FIELD_MARKER in k)
    assert params[key] == AGEING_FIELD_FAILING_REGIME, (
        f"loads_crop_file did not preserve the injected ageing value: "
        f"{params[key]} != {AGEING_FIELD_FAILING_REGIME}"
    )

    buf = StringIO()
    dump_crop_file(buf, index, params, name)
    dumped = buf.getvalue()
    dumped_line = next(l for l in dumped.splitlines() if AGEING_FIELD_MARKER in l)
    dumped_val = float(dumped_line.split(":", 1)[0].strip())
    assert dumped_val == AGEING_FIELD_FAILING_REGIME, (
        f"dump_crop_file did not preserve the injected ageing value: "
        f"{dumped_val} != {AGEING_FIELD_FAILING_REGIME}"
    )

    # full round-trip stability: re-parsing the dumped text yields 11 again
    _, _, params2 = loads_crop_file(dumped)
    assert params2[key] == AGEING_FIELD_FAILING_REGIME


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
