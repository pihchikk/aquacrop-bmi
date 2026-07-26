"""Regression tests for BMI_CorrectGDDayiForTemperatureOverride
(aquacrop_fortran/bmi_aquacrop.f90).

Background: every weather ``set_value`` on this fork writes immediately to
the day about to be simulated *and* sets a persistent flag that
``ReadClimateNextDay`` re-applies to every subsequent day -- but
``SetGDDVariablesNextDay`` (which accumulates ``SumGDD``/``SumGDDfromDay1``)
used to run once per day from the *pre-override* temperature, so an
injected temperature's contribution to growing-degree-days was
permanently one day stale (see docs/bmi/FORK_INJECTION_DOUBLE_APPLICATION.md
in the aquacrop-rs repo for the full root-cause). The fix
(``BMI_CorrectGDDayiForTemperatureOverride``) recomputes ``GDDayi`` from
the just-written Tmin/Tmax at ``set_value`` time and applies the resulting
delta to ``SumGDD``/``SumGDDfromDay1`` immediately, replicating the same
day-0-vs-later-day accumulation guards the model already uses internally
(``InitializeSimulationRunPart2`` for day 0, ``SetGDDVariablesNextDay`` for
every day after).

These tests exercise that fix through the real BMI ``set_value``/
``get_value`` contract -- no internal state is poked directly. Two new
read-only outputs support this: ``crop__gdd_cumulative`` (SumGDD) and
``crop__gdd_cumulative_from_planting`` (SumGDDfromDay1).

Every model instance here runs in its own subprocess (via
``_gdd_runner.py``) against its own fresh copy of the Ottawa fixture --
both are standing requirements in this project: the fork's model
instances are not isolated from each other when more than one is alive
in the same process (docs/bmi/COUPLING_READINESS.md, blocker 4), and the
model mutates its own project directory in place during a run
(docs/bmi/FORK_INJECTION_DOUBLE_APPLICATION.md).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ottawa_bmi"
RUNNER = Path(__file__).parent / "_gdd_runner.py"


def _fresh_fixture(tmp_path: Path, name: str) -> Path:
    """Copy the Ottawa BMI fixture into a fresh directory and return the
    path to its LIST/Ottawa.PRM. The model rewrites files inside its own
    project directory during a run, so every test gets its own copy."""
    if not FIXTURE_DIR.exists():
        pytest.skip(f"Ottawa BMI fixture not found at {FIXTURE_DIR}")
    dest = tmp_path / name
    shutil.copytree(FIXTURE_DIR, dest)
    return dest / "LIST" / "Ottawa.PRM"


def _make_linked_run_fixture(tmp_path: Path, name: str) -> Path:
    """A copy of the Ottawa fixture whose simulation start (PRM line 4) is
    4 days after the crop's own cropping-period start (PRM line 6, left
    at 21-May-2014 / day 41414). This is the one state where
    InitializeSimulationRunPart2's day-0 guard is asymmetric between
    SumGDD (only on DayNri == Crop_Day1) and SumGDDfromDay1 (on
    DayNri >= Crop_Day1) -- a "linked run" starting after the crop's
    calendar Day1. Ottawa's own unmodified fixture has
    Crop_Day1 == FromDayNr, which can't exercise this branch."""
    prm = _fresh_fixture(tmp_path, name)
    original = prm.read_text()
    patched = original.replace(
        "  41414         : First day of simulation period - 21 May 2014",
        "  41418         : First day of simulation period - 25 May 2014",
        1,
    )
    assert patched != original, "PRM line to patch was not found -- fixture format changed?"
    prm.write_text(patched)
    return prm


def _run_program(program: dict) -> dict:
    """Run one AquaCrop instance in a fresh subprocess against the given
    program (see _gdd_runner.py for the step language). Returns the
    parsed JSON result."""
    proc = subprocess.run(
        [sys.executable, str(RUNNER)],
        input=json.dumps(program),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"runner subprocess failed (exit {proc.returncode}):\n"
        f"stdout={proc.stdout!r}\nstderr={proc.stderr[-4000:]!r}"
    )
    # The Fortran runtime's own stdout buffer can flush after our JSON
    # line is printed (a pre-existing quirk of suppress_fortran_output's
    # fd-dup2 timing, unrelated to this fix), so scan for the line that
    # actually parses as JSON rather than assuming the whole stream is one.
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    raise AssertionError(f"no JSON line found in runner stdout:\n{proc.stdout!r}")


def test_day0_asymmetric_guard_not_uniform(tmp_path):
    """The divergent case: DayNri (day 0) > Crop_Day1. A naive correction
    that applies a uniform ">=" guard to both sums would add the
    perturbation's delta to SumGDD too. The real guard must leave SumGDD
    untouched (it was never seeded with day 0's GDD in the first place --
    see InitializeSimulationRunPart2's asymmetric guard) while
    SumGDDfromDay1 does pick up the delta.
    """
    prm = _make_linked_run_fixture(tmp_path, "linked_run")

    result = _run_program({
        "fixture_prm": str(prm),
        "steps": [
            {"record": ["crop__gdd_cumulative", "crop__gdd_cumulative_from_planting"]},
            {"set": {"air_temperature_minimum~day": 13.8}},
            {"set": {"air_temperature_maximal~day": 25.7}},
            {"record": ["crop__gdd_cumulative", "crop__gdd_cumulative_from_planting"]},
        ],
    })

    before, after = result["records"]
    delta_sumgdd = after["crop__gdd_cumulative"] - before["crop__gdd_cumulative"]
    delta_sumgddfromday1 = (
        after["crop__gdd_cumulative_from_planting"] - before["crop__gdd_cumulative_from_planting"]
    )

    assert abs(delta_sumgdd) < 1e-9, (
        f"SumGDD changed by {delta_sumgdd} on a day where DayNri != Crop_Day1 -- "
        f"the day-0 asymmetric guard was not replicated (a naive uniform '>=' "
        f"correction would fail exactly this way)"
    )
    assert delta_sumgddfromday1 > 1e-6, (
        f"SumGDDfromDay1 did not pick up the temperature perturbation "
        f"({delta_sumgddfromday1})"
    )


def test_day0_guard_matches_uniform_when_start_equals_crop_day1(tmp_path):
    """Control case: on the unmodified Ottawa fixture (simulation start ==
    crop start), both guards agree and SumGDD *should* move together with
    SumGDDfromDay1. This is what rules out "SumGDD is just never touched"
    as a trivial way to pass the divergent-case test above."""
    prm = _fresh_fixture(tmp_path, "matched_run")

    result = _run_program({
        "fixture_prm": str(prm),
        "steps": [
            {"record": ["crop__gdd_cumulative", "crop__gdd_cumulative_from_planting"]},
            {"set": {"air_temperature_minimum~day": 13.8}},
            {"set": {"air_temperature_maximal~day": 25.7}},
            {"record": ["crop__gdd_cumulative", "crop__gdd_cumulative_from_planting"]},
        ],
    })

    before, after = result["records"]
    delta_sumgdd = after["crop__gdd_cumulative"] - before["crop__gdd_cumulative"]
    delta_sumgddfromday1 = (
        after["crop__gdd_cumulative_from_planting"] - before["crop__gdd_cumulative_from_planting"]
    )
    assert delta_sumgdd > 1e-6, "SumGDD should move when DayNri == Crop_Day1"
    assert abs(delta_sumgdd - delta_sumgddfromday1) < 1e-9, (
        "SumGDD and SumGDDfromDay1 should move by the same delta when "
        "simulation start == crop start"
    )


def test_idempotent_reordered_temperature_calls(tmp_path):
    """SetTmin then SetTmax (order A) must net out identically to SetTmax
    then SetTmin (order B), and a repeated call with an unchanged value
    must be a no-op (order C). All three are compared against the same
    starting fixture, each in its own subprocess/instance."""
    order_a_prm = _fresh_fixture(tmp_path, "order_a")
    order_b_prm = _fresh_fixture(tmp_path, "order_b")
    repeat_prm = _fresh_fixture(tmp_path, "repeat")

    new_tmin, new_tmax = 13.8, 25.7
    record = ["crop__gdd_cumulative", "crop__gdd_cumulative_from_planting"]

    order_a = _run_program({
        "fixture_prm": str(order_a_prm),
        "steps": [
            {"set": {"air_temperature_minimum~day": new_tmin}},
            {"set": {"air_temperature_maximal~day": new_tmax}},
            {"record": record},
        ],
    })
    order_b = _run_program({
        "fixture_prm": str(order_b_prm),
        "steps": [
            {"set": {"air_temperature_maximal~day": new_tmax}},
            {"set": {"air_temperature_minimum~day": new_tmin}},
            {"record": record},
        ],
    })
    assert order_a["records"][0] == order_b["records"][0], (
        f"SetTmin-then-SetTmax vs SetTmax-then-SetTmin diverged: "
        f"{order_a['records'][0]} != {order_b['records'][0]}"
    )

    repeat = _run_program({
        "fixture_prm": str(repeat_prm),
        "steps": [
            {"record": record},
            {"set": {"air_temperature_minimum~day": new_tmin}},
            {"record": record},
            {"set": {"air_temperature_minimum~day": new_tmin}},
            {"record": record},
        ],
    })
    _, after_first, after_second = repeat["records"]
    assert after_first == after_second, (
        f"a repeated set_value with an unchanged value was not a no-op: "
        f"{after_first} != {after_second}"
    )


def test_persistence_after_single_set_value(tmp_path):
    """The maintainers' documented persistence contract: a single
    set_value on day K must keep applying on every subsequent day until
    bmi__clear_weather_overrides is called (BMI_has_Tmin_override /
    ReadClimateNextDay). Set once, then step several days without setting
    again, and confirm the overridden temperature -- and its GDD
    contribution -- keeps taking effect rather than reverting to the
    file's day-by-day value.
    """
    prm = _fresh_fixture(tmp_path, "persistence")
    # Both overridden once and fixed, so the daily GDD increment under the
    # persisted override is deterministic and constant -- letting only
    # Tmax vary with the file's real daily values would make the expected
    # increment vary day to day too, which is a separate effect this test
    # isn't about.
    override_tmin, override_tmax = 13.8, 25.7

    result = _run_program({
        "fixture_prm": str(prm),
        "steps": [
            {"set": {"air_temperature_minimum~day": override_tmin}},
            {"set": {"air_temperature_maximal~day": override_tmax}},
            {"update": True},
            {"record": [
                "air_temperature_minimum~day", "air_temperature_maximal~day",
                "crop__gdd_cumulative_from_planting",
            ]},
            {"update": True},
            {"record": [
                "air_temperature_minimum~day", "air_temperature_maximal~day",
                "crop__gdd_cumulative_from_planting",
            ]},
            {"update": True},
            {"record": [
                "air_temperature_minimum~day", "air_temperature_maximal~day",
                "crop__gdd_cumulative_from_planting",
            ]},
        ],
    })

    for i, snapshot in enumerate(result["records"]):
        assert snapshot["air_temperature_minimum~day"] == pytest.approx(override_tmin), (
            f"day {i}: Tmin reverted to the file value instead of persisting "
            f"the single set_value ({snapshot['air_temperature_minimum~day']} != {override_tmin})"
        )
        assert snapshot["air_temperature_maximal~day"] == pytest.approx(override_tmax), (
            f"day {i}: Tmax reverted to the file value instead of persisting "
            f"the single set_value ({snapshot['air_temperature_maximal~day']} != {override_tmax})"
        )

    gdd = [s["crop__gdd_cumulative_from_planting"] for s in result["records"]]
    increments = [b - a for a, b in zip(gdd, gdd[1:])]
    assert all(inc > 0 for inc in increments), (
        f"SumGDDfromDay1 should keep increasing under a persisted override, got {gdd}"
    )
    assert max(increments) - min(increments) < 1e-6, (
        f"SumGDDfromDay1's daily increment should be constant while the same "
        f"persisted Tmin/Tmax override is in effect on every day: {increments}"
    )


def test_injection_equivalence_run_d(tmp_path):
    """Run-D-style sanity check: injecting each day's own true weather
    value back through set_value must not perturb the season's GDD
    trajectory at all, relative to a plain (never-overridden) run.
    Compares two full fresh instances, each in its own subprocess/fixture
    copy.

    Both trajectories are sampled at the same point in each day's cycle:
    right before that day's update() (for the injected run, right after
    that day's set_value, i.e. after that day's correction has run). This
    matters for day N >= 1: the persisted-override flag means
    ReadClimateNextDay/SetGDDVariablesNextDay compute a *stale* seed for
    day N at the tail end of day N-1's update() (using day N-1's
    persisted value, not day N's true one yet) -- Design 2's fix is that
    the *next* set_value call (day N's own) retroactively corrects it
    before day N is actually simulated. Sampling right after update()
    instead (before that correction has run) would catch this
    intentional, self-repairing one-step staleness and misreport it as a
    regression -- see docs/bmi/FORK_INJECTION_DOUBLE_APPLICATION.md's
    "self-repairing" analysis in the aquacrop-rs repo.

    Note this also deliberately captures each day's *true* weather from
    the plain run rather than echoing get_value on the injected instance
    turn by turn: once any override is active, ReadClimateNextDay
    persists it forward, so "whatever get_value currently returns" on the
    injected instance would already be contaminated by the previous
    day's override by day 1 -- that would test something else, not the
    Run-D invariant.
    """
    plain_prm = _fresh_fixture(tmp_path, "run_d_plain")
    injected_prm = _fresh_fixture(tmp_path, "run_d_injected")

    n_days = 30
    weather_vars = [
        "air_temperature_minimum~day",
        "air_temperature_maximal~day",
        "air_precipitation",
        "air_evapotranspiration~reference",
    ]
    output_vars = ["crop__gdd_cumulative", "crop__gdd_cumulative_from_planting", "crop__biomass"]

    plain_steps = []
    for _ in range(n_days):
        plain_steps.append({"record": weather_vars + output_vars})
        plain_steps.append({"update": True})

    plain = _run_program({"fixture_prm": str(plain_prm), "steps": plain_steps})
    weather_by_day = [
        {name: snapshot[name] for name in weather_vars} for snapshot in plain["records"]
    ]
    plain_outputs_by_day = [
        {name: snapshot[name] for name in output_vars} for snapshot in plain["records"]
    ]

    injected_steps = []
    for day_weather in weather_by_day:
        injected_steps.append({"set": day_weather})
        injected_steps.append({"record": output_vars})
        injected_steps.append({"update": True})

    injected = _run_program({"fixture_prm": str(injected_prm), "steps": injected_steps})
    injected_outputs_by_day = injected["records"]

    for day, (p, inj) in enumerate(zip(plain_outputs_by_day, injected_outputs_by_day)):
        for name in output_vars:
            assert inj[name] == pytest.approx(p[name], abs=1e-9), (
                f"day {day}: {name} diverged under same-value daily injection: "
                f"{inj[name]} != {p[name]}"
            )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
