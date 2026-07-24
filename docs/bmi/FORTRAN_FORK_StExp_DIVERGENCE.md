# Fork defect (7th, uninvestigated): `StExp` divergence, pervasive across the season

**Status: discovered, not yet root-caused. Do not treat any explanation
below as established — this document is an observation record only.**

## How this was found

Discovered as a byproduct of verifying the `CropZx_eff` epsilon-padding
fix (`2591601`, see `docs/bmi/FORTRAN_FORK_COMPARTMENT_PADDING_DIVERGENCE.md`).
After that fix, the Ottawa/alfalfa 3-run/892-day fixture was diffed
column-by-column against the vendored, uncompromised official output
(`OUTP_REF`, from a fresh `KUL-RSDA/AquaCrop` clone at tag `v7.3`, commit
`4c2af029644a04708b64481215aa3ba73cb78ba8` — independently confirmed to
reproduce `OUTP_REF` byte-for-byte). A large, previously-undocumented
divergence remained, identical in magnitude both before and after the
`CropZx_eff` fix — proving it is a separate defect, unrelated to and
unaffected by that fix.

## Symptom

`StExp` (the "% water stress reduction of canopy expansion" column in
the daily output, `OttawaPRMday.OUT`) mismatches between this fork and
official output on **520 of 524** real in-season rows (`DAP != -9`) of
the Ottawa/alfalfa 3-run/892-day fixture — i.e. essentially the entire
season.

Concrete examples (fork vs. official):

| DAP | Fork `StExp` | Official `StExp` |
|---|---|---|
| 1 | `-9` (undefined) | `29.0` |
| 2 | `-9` (undefined) | `29.0` |
| 3 | `-9` (undefined) | `29.0` |
| 4 | `0` | `29.0` |
| 5 | `0` | `29.0` |
| 6 | `0` | `29.0` |
| 7 | `0` | `29.0` |
| 8 | `0` | `29.0` |

Excluding the `DAP=-9` off-season/gap rows entirely (376 of 892 total
rows; ruled out separately as a formatting artifact, not part of this
finding), the max `StExp` divergence observed was 9 percentage points
(at DAP 137, fork value not yet cross-checked further).

## Apparently-downstream divergences

The following columns also diverge from official at magnitudes far
larger than rounding noise, at fixed magnitude before and after the
`CropZx_eff` fix, and **appear** (not yet confirmed as causally linked —
no mechanism investigation performed) to co-occur with the `StExp`
pattern:

| Variable | Max abs diff vs official | Example location |
|---|---|---|
| Canopy cover `CC`/`CCw` | 1.3 pt | DAP 151 |
| `Brelative` (relative biomass) | 2 % | DAP 100 |
| Biomass | 0.151 t/ha | DAP 124 |
| `Y(fresh)` (fresh yield) | 0.756 t/ha | DAP 123 |
| `ET/ETx` ratio | 1 % | DAP 160 |
| `E/Ex` ratio | 2 % | DAP 154 |

These are plausible downstream effects of a water-stress-index defect
(canopy expansion, biomass accumulation, and yield are all normally
sensitive to stress-reduction factors) but this is an inference, not a
confirmed causal chain. No code path has been inspected for this defect
yet.

## What has been ruled out

- **Not the `CropZx_eff` fix.** Every affected column's max divergence
  is byte-identical in magnitude between the pre-`CropZx_eff`-fix and
  post-fix runs. This defect exists independent of, and is unaffected
  by, `2591601`.
- **Not an off-season/gap-row artifact.** Initially, an apparent 29.2 m
  "rooting depth" divergence was flagged and then ruled out as a
  formatting quirk confined to `DAP=-9` gap rows. The `StExp` divergence
  and its apparent downstream effects were re-checked with all
  `DAP=-9` rows excluded and remain — this is a genuine in-season
  divergence, not a gap-row formatting artifact.

## What has NOT been done (explicitly out of scope for this document)

- No root-cause investigation. The Fortran routine(s) responsible for
  computing `StExp` have not been identified or inspected in this pass.
- No comparison against pristine official source for the relevant
  routine(s) (unlike the `CropZx_eff` fix, which was root-caused via a
  direct source diff before any code change).
- No fix, speculative or otherwise, has been applied or proposed.
- BMI-path-specificity has not been checked (unknown whether this
  affects the console entry point, the BMI wrapper entry point, or
  both).

## Severity (preliminary, unconfirmed)

**Potentially HIGH.** Reach (520/524 in-season days on the tested
fixture) is larger than any of the six previously-fixed fork defects.
Severity should be re-assessed once root cause is established — a
single systemic cause affecting one derived index differently, near-
constant magnitude, or highly numerically consequential can look very
different once understood, so this rating should not be treated as
final.

## Next step

Root-cause investigation, same discipline as prior fixes: identify the
exact Fortran routine(s) computing `StExp` in this fork, diff against
pristine official v7.3 source (a fresh `KUL-RSDA/AquaCrop` clone at the
tag above — **not** the `port45` scratch reference, which is confirmed
not to be genuine official source; see the provenance note in
`docs/bmi/FORTRAN_FORK_COMPARTMENT_PADDING_DIVERGENCE.md`), and
instrument/trace before proposing any fix. Scoped as a separate,
subsequent task.
