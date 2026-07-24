# Fork defect: missing `CropZx_eff` epsilon padding in `AdjustSizeCompartments`

## Symptom

Total profile soil water and compartment sizing diverged from official
AquaCrop v7.3 on the Ottawa/AlfOttawaGDD 3-run/892-day fixture: the last
(12th) soil compartment sized to **0.40 m** instead of official's
**0.45 m**, and total profile water was off by up to **14.6 mm**.

## Root cause

- **Official** (`src/global.f90:6689-6769` at
  [KUL-RSDA/AquaCrop tag `v7.3`, commit `4c2af029644a04708b64481215aa3ba73cb78ba8`](https://github.com/KUL-RSDA/AquaCrop),
  independently re-cloned and confirmed to reproduce the vendored
  `testcase/OUTP_REF/OttawaPRMday.OUT` byte-for-byte): computes
  `CropZx_eff = CropZx + 0.000001_dp` once at the top of
  `AdjustSizeCompartments`, then uses the padded `CropZx_eff` in every
  growth/shrink comparison inside the routine.
- **This fork** (`aquacrop_fortran/global.f90:6591-6668`, before the fix
  in commit `2591601`): had no `CropZx_eff` at all — every comparison
  used the raw, unpadded `CropZx`.

This is a direct deletion of the epsilon padding in the fork's own copy
of the routine, not an input divergence (contrast with the `HarvestNow`
pattern, where the routine was identical and only its input differed).

Without the padding, floating-point comparisons that should land exactly
on a threshold (e.g. `TotDepthC + 0.00001 >= CropZx`) can fall a hair
short, changing how the compartment-building loop sizes the last
compartment relative to official.

## BMI-path-specificity check

**Not BMI-path-specific.** `AdjustSizeCompartments` lives in shared
`global.f90` physics, called from the same `run.f90` sites regardless of
entry point — the console executable (`aquacrop.F90`) and the BMI
wrapper both route through it identically.

## Downstream impact (measured against the vendored, uncompromised
`OUTP_REF`, Ottawa/alfalfa 3-run/892-day fixture)

| Metric | Before fix | After fix | Official (`OUTP_REF`) |
|---|---|---|---|
| DAP 1 profile water `WC(3.05)` | 866.5 mm | **881.0 mm** | 881.0 mm |
| `WC(3.05)` / `Wr(3.00)` / `Wr` max abs diff vs official | 14.6 mm / 3.3 mm | **~0.1 mm** (rounding-level residual) | — |
| Compartment-12 depth marker (header) | 2.80 | **2.83** (matches official) | 2.83 |
| `Drain`, `WC02`, `WC11`/`ECe` max diff vs official | ~0.1 mm / 0.1 mm / 0.03 | **~0 / ~0 / ~0** | — |
| Columns regressed by the fix | — | **zero** | — |

Every column this fix targets moved from mm-scale divergence down to
residual floating-point rounding noise, and nothing regressed.

## What this fix does **not** resolve

The Ottawa/alfalfa 3-run/892-day fixture is **not** byte-identical to
`OUTP_REF` after this fix. 486 of 524 real in-season rows (496 of 892
total rows, including off-season gap rows) still diverge from official.
Every one of these residual divergences is **identical in magnitude
before and after this fix**, proving they are pre-existing and entirely
unrelated to `CropZx_eff`/`AdjustSizeCompartments`. The dominant symptom
is `StExp` (canopy-expansion water-stress %) mismatching on 520 of 524
in-season days. This is a separate, previously-undocumented fork defect
— see `docs/bmi/FORTRAN_FORK_StExp_DIVERGENCE.md`.

## The fix

In `aquacrop_fortran/global.f90`, inside `AdjustSizeCompartments`:

1. Added `CropZx_eff = CropZx + 0.000001_dp`, computed once, matching
   official's placement and comment (copied verbatim, including
   official's own "esnures" typo, for an exact line-for-line port).
2. Replaced every use of raw `CropZx` in growth/shrink comparisons
   within the routine with `CropZx_eff`, matching official's usage
   pattern line-for-line.

The routine is now byte-identical to official's structure (CRLF-
normalized; the fork's pre-existing CRLF line endings in this file were
left untouched — this predates the fix and is unrelated to it).

Committed as `2591601`.

## Correction to previously-circulated "before" impact numbers

The task that specified this fix (a document supplied outside this repo,
not committed here) stated a pre-fix impact table with these ranges:
Transpiration 0-0.1 mm, ET 0, Rooting depth 0, Canopy cover 0-0.1 pt,
Biomass/Yield 0-0.001 t/ha.

**Do not cite these numbers.** A direct fork-vs-pristine-official diff on
this exact fixture, performed as part of verifying this fix, measured
substantially larger pre-fix divergences in the same variables — e.g.
canopy cover off by up to 1.3 pt (13x), biomass off by up to 0.151 t/ha
(151x), fresh yield off by up to 0.756 t/ha (756x). Only the profile-water
figure (14.5-14.6 mm) matched what was independently measured here. The
source and method behind the original table is unclear — it does not
appear to have been a direct Fortran-fork-vs-pristine-official diff on
this exact 3-run/892-day scenario. Those larger divergences are, in any
case, not attributable to this fix (see "What this fix does not resolve"
above) — they are the same pre-existing, unrelated defect documented in
`docs/bmi/FORTRAN_FORK_StExp_DIVERGENCE.md`.

Going forward, use the pristine-verified numbers in this document (from a
fresh `KUL-RSDA/AquaCrop` clone at tag `v7.3`, cross-checked against the
vendored `OUTP_REF`) as ground truth, not any number traceable to the
original task document's impact table.

## Reference-material provenance note

Earlier fixes in this investigation (`4848518` — `calculate_transpiration`
port; `9fcedad` — BMI cumulative-ET getter) were verified in part by
diffing this fork's source against a scratch directory referred to as
`port45`, believed at the time to be official v7.3 source.

**`port45` is not genuine official source.** It carries
`max_SoilLayers = 10` (matching this fork) rather than official's `5`,
and — as this investigation discovered — it lacks `CropZx_eff` entirely,
identical to this fork's pre-fix defect. It was built from this fork's
own base with specific known fixes manually layered on top, not from a
pristine official checkout.

This does **not** invalidate the numerical conclusions of `4848518` or
`9fcedad`: both were verified numerically against the vendored
`OUTP_REF` output files (never compromised), not against `port45` as a
source-code reference. But any characterization of those fixes as
"byte-identical to v7.3" that rested on a `port45` source diff should be
treated as unverified going forward. Use a freshly-cloned pristine tree
(see the Root cause section above for the exact tag/commit used here)
for any future source-level diff against official AquaCrop.
