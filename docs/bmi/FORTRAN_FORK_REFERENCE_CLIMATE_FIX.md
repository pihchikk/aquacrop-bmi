# Fork defect fix: reference-climate feature ported (root cause of the Biomass/Yield/CC drift)

**Status: PORTED AND WIRED IN. Numerically proven correct at every point
this feature itself controls. A separate, previously-masked defect was
uncovered during verification and is flagged below, not fixed here.**

## Background

`docs/bmi/FORTRAN_FORK_BIOMASS_YIELD_DRIFT.md` root-caused a Biomass/
Yield/CC drift (the fork's 7th confirmed defect) to a missing v7.3
feature: official AquaCrop calibrates the fertility/salinity
stress-response curves (and the "potential" seasonal Kc-sum baseline
that feeds daily WPi-normalized biomass) against a synthetic, smoothed
**reference climate** (`TCropReference.SIM`) rather than the actual
simulated year's weather. This fork had no concept of a reference
climate at all — the entire `preparefertilitysalinity.f90` module and
its supporting `tempprocessing.f90`/`global.f90` machinery were never
ported. This document covers porting that feature.

## What "reference climate" is

A 365-day, onset-independent, smoothed daily Tmin/Tmax series, built in
two stages:

1. **`CreateTnxReferenceFile`**: reads the full multi-year daily
   temperature record and computes 12 mean-monthly Tmin/Tmax values,
   writing them to `<name>Reference.Tnx`.
2. **`CreateTnxReference365Days`**: fits each 3-consecutive-month window
   of those 12 means to a quadratic (`GetMonthlyTemperatureDataSetFromTnx
   ReferenceFile`, reusing the same parabolic-interpolation math this
   fork's `GetMonthlyTemperatureDataSet` already had, verified identical
   before porting), and evaluates it as a per-day average across all 365
   days, writing `TnxReference365Days.SIM`.
3. **`DailyTnxReferenceFileCoveringCropPeriod`**: re-rotates that 365-day
   series to start on the *crop's* onset day (not Jan 1) and writes
   `TCropReference.SIM` — this is what the calibration functions
   actually read.

Both stages run once per project run, right after the temperature file
is loaded (`LoadSimulationRunProject`). The per-crop rotation runs once
per crop cycle, inside the two calibration entry points below.

## Scope: daily temperature records only

`CreateTnxReferenceFile`'s 10-day and monthly record-type branches are
**not implemented**. Every scenario in this project's test matrix
(confirmed by reading each bundled `.Tnx` file's own declared record
type) uses daily records exclusively. Porting the 10-day/monthly
branches without any way to exercise or verify them would be exactly
the kind of unverifiable shortcut this project's standing rules forbid.
If a 10-day or monthly record ever reaches this function, it fails
loudly:

```fortran
if (GetTemperatureRecord_DataType() /= datatype_daily) then
    error stop 'CreateTnxReferenceFile: 10-day/monthly reference-' // &
        'climate generation not yet ported -- daily records only ' // &
        '(see docs/bmi/FORTRAN_FORK_REFERENCE_CLIMATE_FIX.md)'
end if
```

This is a known, deliberate limitation, not a silently-wrong result.

## The port (commit sequence)

Seven commits on `feat/coupling-balance-vars`, each independently
buildable and verified before the next:

1. `f931a2b` — new global state: 12-month and 365-day reference arrays
   plus their Get/Set accessors (`aquacrop_fortran/global.f90`).
2. `6e5da6a` — `GetMonthlyTemperatureDataSetFromTnxReferenceFile`
   (`tempprocessing.f90`), reusing the fork's existing, verified-correct
   parabolic interpolation.
3. `42cd895` + `29ab06a` — `LoadClim` bug fix (see below) and
   `CreateTnxReferenceFile` (daily-only, as scoped above).
4. `bc36f33` — `CreateTnxReference365Days`.
5. `846879b` — `SeasonalSumOfKcPot`/`Bnormalized` signature updates
   (`Lend`, `ReferenceClimate` params, `(External)` branch,
   EOF-wraparound-to-reference-file fallback) plus `GDDCDCToCDC`'s
   missing `Reference` parameter — all discovered as prerequisites for
   the new module to compile, done ahead of the module itself. All
   existing call sites updated to preserve current behavior exactly
   (`ReferenceClimate=.false.`), verified as a pure no-op.
6. `2bb307a` — new module `aquacrop_fortran/preparefertilitysalinity.f90`
   (all 7 functions), wired into the Makefile and `meson.build`. Still
   dead code at this point (verified via full-console regression,
   unchanged).
7. `13193de` — wiring: `LoadSimulationRunProject` now creates the
   reference-climate files; `RelationshipsForFertilityAndSaltStress`
   calls the `Reference*` calibration functions instead of the bare
   (actual-year) ones; the missing gate around `SeasonalSumOfKcPot`
   (`GetCrop_StressResponse_Calibrated() .and. FertilityStress > 0`) is
   restored, now passing `ReferenceClimate=.true.`.

## A deliberate, documented type adaptation (not a pristine mismatch)

`StressBiomassRelationshipForTnxReference`'s `SiPr` is declared `int8`
where pristine has `int32`. This fork already represents stress-level
values as `int8` everywhere they matter
(`CropStressParametersSoilFertility`'s `StressLevel`,
`TimeToMaxCanopySF`'s `ClassSF`, and the sibling function
`StressBiomassRelationship`'s own `SiPr`) — widening `TimeToMaxCanopySF`
to match pristine's `int32` instead was considered and rejected: it
would cascade into `StressSFadjNEW`/`PreviousStressLevel`/`FertStress`
across `run.f90` and `simul.f90` (all `int8` by the same fork
convention, with explicit `int8↔int32` adapters already sitting at the
`Get/SetStressSFadjNEW` API boundary) — a much larger, unrelated
refactor of already-working code, for no behavioral benefit (values are
always in `[0, 100]`, losing nothing in the narrower width).
`CCxSaltStressRelationshipForTnxReference` keeps `Si`/`SiPr` as
pristine's `int32`, since its one `int8`-typed call
(`CropStressParametersSoilSalinity`) already takes an explicit inline
cast in pristine's own source — no fork-specific adaptation needed
there.

## `LoadClim` bug found and fixed along the way

While building `CreateTnxReferenceFile`'s verification driver, its
`FromY`/`ToY` output didn't match pristine on real `Ottawa.Tnx` data.
Root cause: `LoadClim` (`global.f90`) was missing one
`read(fhandle, *, iostat=rc)` skip-line pristine has as a loop-priming
read before the `NrObs`-counting `do while` loop. The fork's version
effectively counted the file's `===` header-separator line as a phantom
observation, making `ClimateRecord%NrObs` systematically one too high,
cascading into wrong `ToY`/`ToM`/`ToDayNr`.

**Time-boxed impact check on pre-port behavior** (requested explicitly,
mid-session): dormant for `Ottawa.Tnx`'s real ~1096-row daily file —
`GetSetofThreeMonths`'s `NrObs<=2`/`NrObs<=3` special-case branches
never trigger at that size. A plausible-but-unconfirmed effect remains
on the "last observation" branch near a multi-year record's true end;
not confirmed to affect any currently-tested scenario. Verified
empirically: the Ottawa/AlfOttawaGDD @ fertility=50 3-run console
regression produced the identical 496-line `OttawaPRMday.OUT` diff
before and after this fix — no behavior change to anything
already-passing. Fixed in `42cd895`, now byte-for-byte identical to
pristine's `LoadClim`.

## Verification

### Numeric, in isolation (before wiring)

Standalone test drivers linked against both trees' object files, run
against real `Ottawa.Tnx`:

| Check | Result |
|---|---|
| `CreateTnxReferenceFile`: `FromY`/`ToY`/`FromM`/`ToM`/`TnxReferenceYear`, all 12 monthly Tmin/Tmax | byte-for-byte identical |
| `CreateTnxReference365Days`: all 12 monthly means + all 365 daily Tmin/Tmax | byte-for-byte identical |

### Full-console regression, Ottawa/AlfOttawaGDD @ fertility=50 (3-run/892-day)

| Stage | `OttawaPRMday.OUT` diff lines (vs. official `OUTP_REF`) | First mismatch |
|---|---|---|
| Before this port (baseline, per drift doc) | 496 | DAP 18 |
| After steps 1–6 (port complete, not yet wired) | 496 (unchanged — confirmed dead code) | DAP 18 |
| After step 7 (wired in) | **403** | **DAP 104** |

`OttawaPRM1evaluation.OUT` (run 1's harvest-evaluation summary) is now
**0 diff**.

### Calibration values proven exact (debug-instrumented, both trees, same real scenario)

```
DEBUG_COEFF b0/1/2=  8.493491201490E+01 -5.395815954288E-01 -3.041016944000E-03 DayNri=0
DEBUG_COEFF b0/1/2=  8.523992744460E+01 -5.434918208766E-01 -3.031650773305E-03 DayNri=41578
DEBUG_COEFF b0/1/2=  8.538595276658E+01 -5.448811865335E-01 -3.033267831748E-03 DayNri=41936

DEBUG_SUMKC top/stress=<identical to official for all 3 runs>
```

Identical between fork and official for all 3 linked runs, matching
`diff` exit 0. This directly confirms `ReferenceStressBiomassRelationship`
and the `SeasonalSumOfKcPot`/`ReferenceClimate=.true.` gate — the exact
mechanism named in the original root-cause finding — are now producing
official's exact numbers.

### Controls unchanged

Ottawa/Wheat.CRO @ fertility=0: still byte-for-byte identical to a
pristine-built console on the same scenario (0 diff), confirming the
restored gate correctly leaves fertility=0 scenarios untouched.

### Build

Full source tree compiles clean via the actual `Makefile` with
production flags (`-fPIC -fall-intrinsics -O2 -march=native
-funroll-loops`), producing a working `aquacrop` console executable.
`meson.build` updated to include the new module in `fortran_sources`.

### Not done here

- **Full pytest suite**: infeasible in this container — the `bmif`
  pkg-config dependency the BMI wrapper needs to build isn't installed
  here (`pip install -e .` fails at the meson dependency-resolution
  step, unrelated to this change). Not attempted.
- **Exhaustive regression across every calendar-days crop at
  fertility=50, and the other 6 confirmed fork defects' specific
  scenarios**: not re-run individually this session, given the finding
  below changes what "full verification" should even be checking
  against. Worth doing once the newly-found defect (below) is
  understood, so a single regression pass covers both.
- **StExp**: not re-checked as a side effect of this fix.

## New finding: a separate, previously-masked defect remains

The residual 403-line diff is **not** a gap in this feature. Direct
proof: both quantities this port controls — the calibration
coefficients (`Coeffb0`/`Coeffb1`/`Coeffb2`) and `SumKcTop`/
`SumKcTopStress` (the exact variable named in the original drift doc's
root-cause finding) — are byte-for-byte identical to official for all 3
linked runs (debug-instrumented, both trees, verified via `diff` exit
0). The day-by-day divergence starts at DAP 104 (well into the season,
mid-cycle, `Stage` unchanged), not at day 1 — inconsistent with a
seasonal-baseline input being wrong, and consistent with something in
the *daily* budget loop diverging independently.

The first diverging columns at DAP 104 are `Bin`/`Bout` (the
"Transfer of Assimilates" mobilization/storage mechanism — `Bin_temp`/
`Bout_temp` via `InitializeTransferAssimilates`, `run.f90`), with small
knock-on differences in `Biomass`/`Y(dry)`/`Y(fresh)`/`WPet`
(`Biomass` off by 0.019 t/ha out of 7.9, ~0.24% relative, at first
mismatch — much smaller than this defect's original 0.15 t/ha/~1.4%
magnitude). This is consistent with a threshold/day-count effect
(a `roundc()`-derived trigger day shifting by one) somewhere in that
mechanism, not a missing calculation of the scale this session's
feature was.

**Not investigated further here**, per this session's explicit
stop-criterion: continuing into a new, structurally distinct bug mid-way
through wrapping up an already-large, already-verified port would
repeat the exact pattern this session was told to avoid ("discovering
more hidden scope mid-implementation that changes the picture
materially"). This is flagged as a new, 8th-ish fork defect candidate
for separate investigation, with the exact reproduction already in
hand: Ottawa/AlfOttawaGDD.CRO @ fertility=50, 3-run console, first
mismatch at DAP 104 (absolute day 41577+104), `Bin`/`Bout` columns.

## Severity (of the fix landed here)

The originally-documented drift (496 diff lines, first mismatch DAP 18,
~1.4-2.5% relative on Biomass/Yield/CC by late-season) is now almost
entirely closed — divergence no longer starts until DAP 104, and the
mechanism this session set out to fix is proven exact. What remains is
materially smaller and a different defect.
