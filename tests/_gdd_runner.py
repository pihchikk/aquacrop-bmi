"""Subprocess driver for GDD-correction tests.

Runs one AquaCrop BMI instance per process invocation, per this project's
standing isolation requirement: the fork's model instances are not
isolated from each other within a single process when more than one is
alive at a time (see docs/bmi/OVERRIDE_PHYSICS_VERIFICATION.md, blocker 4
in docs/bmi/COUPLING_READINESS.md). Tests that need to compare two
trajectories (e.g. a baseline vs. an injected run) invoke this script
twice, as two separate ``python -m`` subprocesses, and diff the JSON each
one writes -- never by holding two model objects live in the same
process.

A "program" is a small JSON-described sequence of steps, read from stdin:

    {
      "fixture_prm": "/path/to/LIST/Ottawa.PRM",
      "steps": [
        {"update": true},
        {"set": {"air_temperature_minimum~day": 13.8}},
        {"echo_get_as_set": ["air_temperature_maximal~day"]},
        {"record": ["crop__gdd_cumulative", "crop__biomass"]}
      ]
    }

Step kinds:
  - {"update": true}          -- call m.update()
  - {"set": {name: value}}    -- call m.set_value(name, [value])
  - {"echo_get_as_set": [names]} -- read each name's current value and
                                     set_value it right back (a true
                                     no-op injection, for Run-D-style
                                     equivalence checks)
  - {"record": [names]}       -- snapshot get_value(name) for each name,
                                     appended to the output "records" list

Output (written to stdout as one JSON document):

    {
      "start_time": 0.0,
      "end_time": 163.0,
      "records": [ {name: value, ...}, ... ]   # one dict per "record" step
    }
"""
from __future__ import annotations

import json
import sys

import numpy as np


def run_program(program: dict) -> dict:
    from aquacrop_bmi_babel import AquaCrop

    m = AquaCrop(verbose=False)
    m.initialize(program["fixture_prm"])

    result = {
        "start_time": m.get_start_time(),
        "end_time": m.get_end_time(),
        "records": [],
    }

    dest = np.empty(1, dtype=np.float64)
    try:
        for step in program["steps"]:
            if "update" in step:
                m.update()
            elif "set" in step:
                for name, value in step["set"].items():
                    m.set_value(name, np.array([float(value)]))
            elif "echo_get_as_set" in step:
                for name in step["echo_get_as_set"]:
                    m.get_value(name, dest)
                    m.set_value(name, np.array([dest[0]]))
            elif "record" in step:
                snapshot = {}
                for name in step["record"]:
                    m.get_value(name, dest)
                    snapshot[name] = float(dest[0])
                result["records"].append(snapshot)
            else:
                raise ValueError(f"unknown step: {step!r}")
    finally:
        m.finalize()

    return result


if __name__ == "__main__":
    program = json.loads(sys.stdin.read())
    output = run_program(program)
    print(json.dumps(output))
