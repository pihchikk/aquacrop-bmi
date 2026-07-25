# Fork defect: Biomass/Yield/CC drift — root-caused (7th confirmed fork defect)

**Status: ROOT-CAUSED. Not yet fixed — this is a substantial, multi-file
missing feature, not a small patch, and porting it changes the physical
interpretation of a core calculation input. Per this investigation's
explicit stop-criteria, implementation was deliberately not attempted
without review. See "Root cause" and "Why this is not fixed here" below.**

## How this was found

Discovered while investigating the `StExp` divergence
(`docs/bmi/FORTRAN_FORK_StExp_DIVERGENCE.md`). That investigation's
corrected, properly-column-aligned re-analysis of the fork (post-
`2591601`, the `CropZx_eff` fix) against the vendored, uncompromised
`OUTP_REF` (Ottawa/alfalfa 3-run/892-day fixture, official v7.3 via a
fresh `KUL-RSDA/AquaCrop` clone at tag `v7.3`, commit
`4c2af029644a04708b64481215aa3ba73cb78ba8`) found this divergence to be
real, but starting far earlier in the season than `StExp`'s first
mismatch (DAP 137) — ruling out `StExp` as its cause.

## Symptom

`Biomass`, `Y(fresh)`/`Y(dry)` (yield), and `CC`/`CCw` (canopy cover)
all diverge from official by a small amount that starts near-zero early
in the season and grows (compounds) as the multi-year, multi-run
simulation progresses.

| Variable | Mismatched in-season rows | First mismatch | Example (fork vs. official) |
|---|---|---|---|
| Biomass | 467 | **DAP 18** | `0.689` vs `0.688` t/ha |
| `Y(fresh)` | 480 | ~DAP 20 | `3.494` vs `3.493` t/ha |
| CC/CCw | 113 | ~DAP 118 | `49.7` vs `49.8` pt |

By deep into the multi-year run (row ~472-473 of 892):

- Biomass: `10.642` vs `10.793` t/ha (diff `0.151`, ~1.4% relative)
- `Y(fresh)`: `53.211` vs `53.967` t/ha (diff `0.756`, ~1.4% relative)
- CC: `53.5` vs `52.2` pt (diff `1.3`, ~2.5% relative)

## Priority 1: compiler-flags hypothesis — RULED OUT

Tested directly, both directions, per the standard build vs. this
fork's actual meson-python-resolved release flags:

| | Official (`make bin`) | Fork (meson-python `release`, empirically captured via `ninja -v`) |
|---|---|---|
| Optimization | `-O2` | `-O3` |
| `-march=native` | present | absent |
| `-funroll-loops` | present | absent |
| `-fall-intrinsics` | present | absent |

- Fork source built with **official's exact flags** (`-fPIC
  -fall-intrinsics -O2 -march=native -funroll-loops`): drift unchanged
  (496 row-level diffs, DAP 18 Biomass still `0.689` vs `0.688`).
- Pristine source built with **the fork's exact flags** (`-Wall -O3
  -fPIC -g`, reverse test): **0 diff vs `OUTP_REF`** — byte-for-byte
  identical.

Conclusive: the drift is a genuine source-level difference, not a build
configuration artifact. gfortran 13.3.0 in both cases.

## Root cause (found via direct instrumentation, not speculation)

**`SeasonalSumOfKcPot`** (`aquacrop_fortran/global.f90:5339-5556` in this
fork vs. `src/global.f90:5408-5647` in pristine v7.3) computes a
once-per-crop-cycle "potential" seasonal Kc-sum baseline
(`SetSumKcTop(SeasonalSumOfKcPot(...))`, called once per `Run` from
`RelationshipsForFertilityAndSaltStress` in `run.f90`), which feeds
`SumKcTopStress` (`= SumKcTop * FracBiomassPotSF`) and, through it, the
WPi-normalized daily Biomass/Yield calculation every single day of that
crop cycle.

**The fork's version of this function is structurally behind official
v7.3** — a full diff shows:

1. **Missing parameters**: official's signature adds `Lend` (an
   integer day-count) and `ReferenceClimate` (logical) that the fork's
   signature does not have at all.
2. **Missing `'(External)'` temperature-file branch entirely.**
3. **Missing the `ReferenceClimate`-gated file selection**: official
   opens `TCropReference.SIM` when `ReferenceClimate .eqv. .true.`, or
   the regular `TCrop.SIM` otherwise, with an EOF-wraparound fallback
   when reading the reference file. The fork always opens `TCrop.SIM`
   unconditionally — it has no concept of a separate reference climate
   at all.

At the actual call site (`run.f90`), official passes `GetCrop_
DaysToHarvest()` **twice** (once for `L1234`, once for the new `Lend`
— same value in this scenario, so the loop-bound itself is not the
active difference) and a trailing **`.true.`** for `ReferenceClimate`.

**What `TCropReference.SIM` actually is**: a 365-day, smoothed/mean
daily-temperature series, dynamically generated at runtime (comment in
official source, `preparefertilitysalinity.f90:817/956`: *"Create
TCropReference.SIM (i.e. daily mean Tnx for 365 days from Onset
onwards)"*). **This entire module — `preparefertilitysalinity.f90` —
does not exist in this fork.** Its other responsibilities were folded
into this fork's `RelationshipsForFertilityAndSaltStress` (`run.f90`),
confirmed earlier in this project's history, but the `TCropReference.SIM`
generation piece was never ported. Confirmed empirically: a completed
pristine run leaves both `TCrop.SIM` (175 lines, one specific year) and
`TCropReference.SIM` (365 lines, full smoothed year) in its `SIMUL/`
directory; the fork's run directory only ever produces `TCrop.SIM`.

**Confirmed via direct instrumentation** (scratch-only debug prints
inside `SeasonalSumOfKcPot` at its return point, both trees; `git
status` confirmed clean afterward):

```
fork:      TempFile=[Ottawa.Tnx] L1234=164 SumKcPot=142.958... SumGDD=1802.6...
pristine:  TempFile=[Ottawa.Tnx] L1234=164 SumKcPot=135.099... SumGDD=1880.64...
```

(repeated for all 3 linked runs — L1234=177/175 in both trees, SumGDD
differing by 78-112, roughly 4-5% relative, in every run)

**`TempFile` name and `L1234` (loop bound) are identical in both
trees** — ruling out filename selection and iteration count as the
difference — **yet `SumGDD` differs substantially from the first call**
(one-time, per-crop-cycle value, not a daily accumulator; this is why
the symptom is small-but-nonzero from the very start of Biomass
computation and compounds thereafter, rather than appearing as a
discrete jump). This is the expected signature of summing the same
number of days from two genuinely different temperature series — the
fork's actual-year `TCrop.SIM` vs. official's smoothed 365-day
`TCropReference.SIM` — exactly matching the missing-feature diagnosis
above.

An earlier attempt to confirm this by manually swapping file content
(replacing the fork's `TCrop.SIM` with pristine's generated
`TCropReference.SIM` before running) showed **no effect** and briefly
looked like disconfirming evidence — but this test was invalid: the
program regenerates `TCrop.SIM` from the actual weather data during its
own initialization, unconditionally overwriting the manual swap before
`SeasonalSumOfKcPot` ever reads it. The direct instrumentation above
supersedes that test and is conclusive.

## ~~Working hypothesis (NOT confirmed) — SUPERSEDED~~

~~"Slow rounding/precision drift" — i.e., some tiny, systematic per-day
computational difference... This hypothesis is not backed by a source
diff or instrumentation yet.~~

**Superseded.** The mechanism is not rounding/precision at all — it is
a missing v7.3 feature (reference-climate generation) causing a
materially different, one-time seasonal baseline input. Struck through
rather than deleted, per this project's documentation-correction
convention.

## Why this is not fixed here

Porting this requires:
- Recreating `preparefertilitysalinity.f90`'s `TCropReference.SIM`
  generation logic (or folding the equivalent into `run.f90`, matching
  this fork's existing structural choice) — a mean-daily-temperature
  computation across an onset-relative 365-day window, with its own
  file lifecycle (create/delete/regenerate).
- Adding the `Lend`/`ReferenceClimate` parameters to `SeasonalSumOfKcPot`
  and updating every call site.
- Adding the missing `'(External)'` branch and the `ReferenceClimate`-
  gated file selection with EOF-wraparound fallback.
- Checking whether the same `ReferenceClimate` pattern is needed at the
  *other* `TCropReference.SIM` read site found in official
  (`global.f90:5538`, inside the CC-with-weed/fertility-stress function
  near `tempprocessing.f90:2841`) — not yet investigated for this fork.

This is a genuinely new feature addition to the fork, not a bounded
bug fix — it changes what physical data feeds a core calculation. Per
this investigation's explicit stop-criteria ("a decision that changes
physical interpretation"), implementation was deliberately not
attempted without review, rather than porting it autonomously.

## Severity

**MEDIUM, now that mechanism is known** (revised from "TBD" — enough is
now understood to assess this, unlike the earlier undiagnosed state).
Bounded, monotonic, ~1-2.5% relative effect on Biomass/Yield/CC over a
multi-year run in the one fixture tested; not a crash, NaN, or sign
error. But it is systematic (affects every GDD-mode crop cycle that
reaches this code path, not an edge case) and affects exactly the kind
of season-long potential-biomass baseline that calibration and
yield-prediction use cases would care about most.

## What remains undone

- No fix implemented (see above).
- Not checked whether `'(External)'` temperature-file mode is used by
  any bundled scenario (if not, that specific gap is lower priority).
- Not checked whether the second `TCropReference.SIM` read site
  (`global.f90:5538`) has the same or a related gap.
- Not checked whether calendar-days-mode crops (not just this GDD-mode
  fixture) reach the same code path with the same effect.
- BMI-path-specificity not checked (low priority — shared `global.f90`/
  `run.f90` physics, same pattern as every other fork defect in this
  project; console and BMI wrapper reach it identically).
