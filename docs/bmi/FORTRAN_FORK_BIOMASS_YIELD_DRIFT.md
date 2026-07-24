# Fork defect (uninvestigated): slow Biomass/Yield/CC precision drift

**Status: discovered, not yet root-caused. This document is an
observation record only — do not treat "rounding/precision drift" below
as a confirmed mechanism, it is a working hypothesis.**

## How this was found

Discovered while investigating the `StExp` divergence
(`docs/bmi/FORTRAN_FORK_StExp_DIVERGENCE.md`). That investigation's
corrected, properly-column-aligned re-analysis of the fork (post-
`2591601`, the `CropZx_eff` fix) against the vendored, uncompromised
`OUTP_REF` (Ottawa/alfalfa 3-run/892-day fixture, official v7.3 via a
fresh `KUL-RSDA/AquaCrop` clone at tag `v7.3`, commit
`4c2af029644a04708b64481215aa3ba73cb78ba8`) found this divergence to be
real, but starting far earlier in the season than `StExp`'s first
mismatch (DAP 137) — ruling out `StExp` as its cause. It has not
previously been documented as its own item.

## Symptom

`Biomass`, `Y(fresh)`/`Y(dry)` (yield), and `CC`/`CCw` (canopy cover)
all diverge from official by a small amount that starts near-zero early
in the season and grows (compounds) as the multi-year, multi-run
simulation progresses.

Measured (correct, dynamically-aligned column comparison, verified via
`NF` field-count checks and direct header-row confirmation on both
files):

| Variable | Mismatched in-season rows | First mismatch | Example (fork vs. official) |
|---|---|---|---|
| Biomass | 467 | **DAP 18** | `0.689` vs `0.688` t/ha |
| `Y(fresh)` | 480 | ~DAP 20 | `3.494` vs `3.493` t/ha |
| CC/CCw | 113 | ~DAP 118 | `49.7` vs `49.8` pt |

By deep into the multi-year run (row ~472-473 of 892, several hundred
days in), the same variables show:

- Biomass: `10.642` vs `10.793` t/ha (diff `0.151`, ~1.4% relative)
- `Y(fresh)`: `53.211` vs `53.967` t/ha (diff `0.756`, ~1.4% relative)
- CC: `53.5` vs `52.2` pt (diff `1.3`, ~2.5% relative)

The divergence is monotonically small-to-moderate throughout — no
sudden jumps, no NaN/undefined values, no sign flips. Relative magnitude
stays in the roughly 1-2.5% range even at its largest observed point.

## What has been ruled out

- **Not caused by the `CropZx_eff` fix.** Present at the same magnitude
  before and after `2591601`.
- **Not caused by `StExp`/`StressLeaf`.** Confirmed by timing: this
  drift starts at DAP 18; `StExp`'s first mismatch is DAP 137. The
  causal direction, if anything, plausibly runs the other way (see
  `docs/bmi/FORTRAN_FORK_StExp_DIVERGENCE.md`'s root-cause section: the
  `StExp` sentinel flip appears to be a downstream trip of an internal
  canopy-plateau threshold caused by *this* drift, not the reverse).
- **Not an off-season/gap-row artifact.** Confirmed present on real
  in-season rows (`DAP != -9`).

## Working hypothesis (NOT confirmed)

"Slow rounding/precision drift" — i.e., some tiny, systematic
per-day computational difference (order 0.001 t/ha or less at first)
that compounds because Biomass and CC are both cumulative/recursive
quantities (each day's value depends on the previous day's), rather
than a single discrete formula error, NaN, or uninitialized read of the
kind found in every other fork defect so far in this project. This is a
different *class* of problem than the six previously-fixed/documented
defects (biomass NaN, day-3 canopy, `calculate_transpiration`/
SinkMajor-SinkMinor, ET accumulator, finalize abort, Rosetta, and
`CropZx_eff`) — those were discrete, identifiable code defects; this one
has not yet been shown to be anything more specific than "the numbers
drift apart gradually."

This hypothesis is *not* backed by a source diff or instrumentation yet
— it is offered only as the most likely-sounding explanation for the
observed shape (small, monotonic, compounding, no discrete jumps), and
should not be relied upon until confirmed or refuted by actual
investigation.

## Severity

**TBD / needs investigation.** Deliberately not rated HIGH or LOW.
A genuine ~1-2% cumulative drift over a multi-year run is a real,
measurable divergence from official — larger in ultimate reach (starts
earliest, DAP 18, and keeps growing across all 892 days) than the
`StExp` finding, but categorically different from the discrete,
bounded-impact defects fixed so far. Whether this is a benign,
acceptable floating-point artifact or a genuine formula/precision
defect worth fixing cannot be determined without root-causing it.

## What has NOT been done (explicitly out of scope for this document)

- No root-cause investigation. No Fortran routine has been identified
  as responsible.
- No source diff against pristine official v7.3 has been performed for
  whatever routine(s) compute daily Biomass/CC accumulation.
- No instrumentation has been added.
- No fix, speculative or otherwise, has been applied or proposed.
- BMI-path-specificity has not been checked.

## Next step

Dedicated, separate root-cause investigation — same discipline as prior
fixes: identify the exact routine(s) responsible for daily Biomass and
CC accumulation, diff against pristine official v7.3 source (a fresh
`KUL-RSDA/AquaCrop` clone at the tag above — not `port45`, confirmed not
genuine official source), and instrument day-by-day from the earliest
divergence point (DAP 18) to find the first point at which fork and
official inputs to the relevant calculation differ. Given the drift
starts so early and grows steadily, tracing from DAP 1-20 is likely more
tractable than starting from a point deep in the compounding drift.
