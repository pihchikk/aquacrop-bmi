# Fork defect: `StExp` divergence (originally reported as the "7th fork defect")

**⚠️ CORRECTION (see below): the original finding in this document was
substantially wrong, caused by a bug in the diagnostic script used to
produce it, not a fork physics defect of the claimed scope. The original
text is retained below, struck through, for history — do not act on it.
Corrected findings follow in the "CORRECTION" section.**

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

## ~~Symptom (ORIGINAL — SUPERSEDED, see correction below)~~

~~`StExp` (the "% water stress reduction of canopy expansion" column in
the daily output, `OttawaPRMday.OUT`) mismatches between this fork and
official output on **520 of 524** real in-season rows (`DAP != -9`) of
the Ottawa/alfalfa 3-run/892-day fixture — i.e. essentially the entire
season.~~

~~Concrete examples (fork vs. official):~~

| DAP | ~~Fork `StExp`~~ | ~~Official `StExp`~~ |
|---|---|---|
| ~~1~~ | ~~`-9` (undefined)~~ | ~~`29.0`~~ |
| ~~2~~ | ~~`-9` (undefined)~~ | ~~`29.0`~~ |
| ~~3~~ | ~~`-9` (undefined)~~ | ~~`29.0`~~ |
| ~~4~~ | ~~`0`~~ | ~~`29.0`~~ |
| ~~5~~ | ~~`0`~~ | ~~`29.0`~~ |
| ~~6~~ | ~~`0`~~ | ~~`29.0`~~ |
| ~~7~~ | ~~`0`~~ | ~~`29.0`~~ |
| ~~8~~ | ~~`0`~~ | ~~`29.0`~~ |

~~Excluding the `DAP=-9` off-season/gap rows entirely (376 of 892 total
rows; ruled out separately as a formatting artifact, not part of this
finding), the max `StExp` divergence observed was 9 percentage points
(at DAP 137, fork value not yet cross-checked further).~~

## ~~Apparently-downstream divergences (ORIGINAL — SUPERSEDED)~~

~~The following columns also diverge from official at magnitudes far
larger than rounding noise, at fixed magnitude before and after the
`CropZx_eff` fix, and **appear** (not yet confirmed as causally linked —
no mechanism investigation performed) to co-occur with the `StExp`
pattern:~~

| ~~Variable~~ | ~~Max abs diff vs official~~ | ~~Example location~~ |
|---|---|---|
| ~~Canopy cover `CC`/`CCw`~~ | ~~1.3 pt~~ | ~~DAP 151~~ |
| ~~`Brelative` (relative biomass)~~ | ~~2 %~~ | ~~DAP 100~~ |
| ~~Biomass~~ | ~~0.151 t/ha~~ | ~~DAP 124~~ |
| ~~`Y(fresh)` (fresh yield)~~ | ~~0.756 t/ha~~ | ~~DAP 123~~ |
| ~~`ET/ETx` ratio~~ | ~~1 %~~ | ~~DAP 160~~ |
| ~~`E/Ex` ratio~~ | ~~2 %~~ | ~~DAP 154~~ |

~~These are plausible downstream effects of a water-stress-index defect
(canopy expansion, biomass accumulation, and yield are all normally
sensitive to stress-reduction factors) but this is an inference, not a
confirmed causal chain. No code path has been inspected for this defect
yet.~~

## ~~Severity (ORIGINAL — SUPERSEDED)~~

~~**Potentially HIGH.** Reach (520/524 in-season days on the tested
fixture) is larger than any of the six previously-fixed fork defects.~~

---

## CORRECTION

**What went wrong:** the "520 of 524 rows" / "official = 29.0" finding
above was produced by a one-off diagnostic script (a follow-up query run
after the main column-sweep, checking specifically for `StExp`
mismatches) that used a **hardcoded field offset** (`$74`) left over
from an earlier, differently-shaped calculation, instead of the correct
dynamically-computed offset for this comparison.

`StExp` is column 26 in the daily output. With both files having 98
fields per row, after pasting them side by side the official file's
column 26 value lands at field `26 + 98 = 124`, not field `74`. Field 74
is actually part of the `WC 4` header (a soil-compartment water-content
value, unrelated to `StExp`) — and its values happen to sit in a similar
numeric neighborhood (roughly 20-29) to what a real stress percentage
would look like, which is why the spurious comparison produced a
plausible-looking but entirely fictitious "official reports 29.0"
result.

**How this was caught:** while instrumenting `DetermineCCiGDD` (the
routine that computes `StExp`'s underlying variable, `StressLeaf`) for
root-cause work, a freshly-built, from-source pristine v7.3 console's
*own* output was checked directly against `OUTP_REF` for the `StExp`
column and found to read `-9, -9, -9, 0, 0, 0, 0, 0` for DAP 1-8 —
identical to what had been recorded for the fork, not `29.0`. That
contradiction triggered re-deriving the original comparison with
verified-correct column alignment (confirmed via `NF` field-count checks
on both files, and by reading the header row directly to confirm column
identity) from scratch, on the currently-committed `HEAD`.

**The real `StExp` divergence, correctly measured:**

- **27 in-season rows** mismatch (not 520/524).
- Every mismatch is a **`-9` (undefined) vs `0`** boundary flip — never
  a real percentage-value difference, and `29.0` does not appear
  anywhere in official's `StExp` output on this fixture. The "9.0
  percentage points" reported as a max diff in the original finding was
  simply `|(-9) - 0| = 9` — the numeric distance between the sentinel
  and zero, not a genuine 9-point stress swing.
- Concentrated in a late-season DAP range (observed instances at DAP
  137, 139, 143, 145, 146, 149, 150, 154, 155, 156, 160, 161, 162, 163)
  recurring across the fixture's 3 linked runs — i.e. this looks like a
  boundary condition near senescence or a cutting event, not a
  season-wide computation failure.

**The "downstream" columns (CC, Biomass, Yield, Brelative, ET/E ratios)
are real, but are NOT downstream of `StExp`.** Re-checked with the same
corrected methodology:

| Variable | Real mismatch count (in-season rows) | Character |
|---|---|---|
| Biomass | 467 | starts at **DAP 18** (0.689 vs 0.688), grows to ~0.15-0.75 t/ha by deep into the multi-year run |
| `Y(fresh)` | 480 | same pattern, starts small, compounds |
| CC/CCw | 113 | starts ~DAP 118 (49.7 vs 49.8), compounds to ~1.3 pt |

These begin at **DAP 18** — well before the first `StExp` mismatch at
DAP 137. Timing alone rules out the causal chain speculated in the
original (struck-through) text above. This is a **separate, distinct,
unrelated finding** — see
`docs/bmi/FORTRAN_FORK_BIOMASS_YIELD_DRIFT.md`.

**Corrected severity:** downgraded from "potentially HIGH" to **LOW/
narrow**, pending root cause. 27 rows, all a discrete sentinel-vs-zero
boundary flip late in the season, is a materially smaller and different
class of finding than a season-wide, large-magnitude stress-index
failure.

---

## What has been ruled out (still valid after correction)

- **Not the `CropZx_eff` fix.** Every affected column's max divergence
  is byte-identical in magnitude between the pre-`CropZx_eff`-fix and
  post-fix runs. This defect exists independent of, and is unaffected
  by, `2591601`.
- **Not an off-season/gap-row artifact.** Initially, an apparent 29.2 m
  "rooting depth" divergence was flagged and then ruled out as a
  formatting quirk confined to `DAP=-9` gap rows. The (corrected, 27-row)
  `StExp` divergence was re-checked with all `DAP=-9` rows excluded and
  remains — this is a genuine in-season divergence, not a gap-row
  formatting artifact.

## Root cause (found)

**Mechanism: the 27-row flip is a downstream symptom of a separate,
already-documented small canopy-cover (`CC`) precision drift — not an
independent defect in `StExp`/`StressLeaf` computation or in
`DetermineCCiGDD` itself.**

`StrExp`'s underlying variable, `StressLeaf`, is set to the sentinel
`-33._dp` ("maximum canopy is reached") at several points inside
`DetermineCCiGDD` (`aquacrop_fortran/simul.f90:3517`, `:3521`, `:3529`)
whenever `CCiActual` (current canopy cover that day) reaches or exceeds
`CCxSFCD` (the fertility/salinity-stress-adjusted maximum achievable
canopy). In the daily-output write logic
(`aquacrop_fortran/run.f90:7560-7563`), **any negative `StressLeaf`
value displays as `-9` (undefined)**:

```fortran
if (GetStressLeaf() < 0._dp) then
    StrExp = undef_int   ! -9
else
    StrExp = roundc(GetStressLeaf(), mold=1)
```

So the observed `-9`-vs-`0` output flip is really a `-33`
("max canopy reached") vs. a normal computed value (which happens to be
`0` in this late-season, plateaued regime) — both of which round to `-9`
or `0` respectively at the output layer.

**Why it flips between fork and official:** `DetermineCCiGDD` is
confirmed structurally identical to pristine official v7.3 (see below),
and its traced entry values (`SumGDDadjCC`, the germination flag,
`StressLeaf` on entry) match exactly on the days checked. But `CC`
itself already differs between fork and official by a small amount
(0.1-1.1 pt) at every one of the 27 mismatched rows — this is the same
compounding drift documented separately in
`docs/bmi/FORTRAN_FORK_BIOMASS_YIELD_DRIFT.md`. Late in the season, `CC`
plateaus near its ceiling (`CCxSFCD`); when it is this close to the
ceiling, a tiny cross-tree difference is enough to land `CCiActual` on
opposite sides of the `> CCxSFCD` comparison on a given day, toggling
`StressLeaf` between `-33` and a normal value in one tree but not the
other. Confirmed directly: at all 27 mismatch rows, `CC` sits in the
low-to-mid 50s % (late-season plateau) with the fork-vs-official
difference at the same small magnitude as the general drift (0.1-1.1
pt) — not a sudden large jump.

**Structural check (`DetermineCCiGDD`, fork
`aquacrop_fortran/simul.f90:3286-4009` vs. pristine
`src/simul.f90:3286-4008` at v7.3):** confirmed byte-identical (CRLF-
normalized) except three purely cosmetic differences — official uses a
named constant `ac_zero_threshold` where the fork inlines the equivalent
literal (`0.00000001_dp`/`0.000001_dp`), and one comment-line offset.
Same pattern as the earlier, unrelated `CropZx_eff` finding was
*structural*; this one is *not* — `StExp` is the "HarvestNow pattern"
(identical routine, values it operates on differ), not the
"`CropZx_eff` pattern" (deleted code).

**Confirmed via direct instrumentation** (scratch-only debug prints
added to both a fork build and a freshly-built pristine v7.3 console at
the `DetermineCCiGDD` germination-check entry point; git diff confirmed
clean afterward — no instrumentation left in the tracked repo):
`SumGDDadjCC` and the germination-passed flag matched exactly between
trees at every traced day; `StressLeaf`-on-entry matched at rows
137/145 and only began differing once the internal `-33` sentinel had
already been set differently between the two trees on an intervening
day — consistent with the `CC`-vs-`CCxSFCD` boundary mechanism above,
not with any divergence in `DetermineCCiGDD`'s own logic.

## Severity (revised after root cause)

**LOW / cosmetic.** This is a discrete sentinel-display flip (`-9` vs
`0` for an already-near-zero stress reading) on 27 of 892 rows, itself
caused by a separate, tiny, already-documented `CC` drift crossing an
internal plateau threshold differently between trees. It has no
independent physics impact beyond what the underlying `CC` drift already
carries. No fix is proposed for `StExp`/`StressLeaf` specifically — the
actionable item is the separate `CC`/Biomass/Yield drift investigation
(`docs/bmi/FORTRAN_FORK_BIOMASS_YIELD_DRIFT.md`), not this display-layer
symptom.

## What has NOT been done

- The upstream cause of the small `CC` drift itself has *not* been
  investigated here — that is explicitly the separate, dedicated task
  scoped in `docs/bmi/FORTRAN_FORK_BIOMASS_YIELD_DRIFT.md`.
- No fix has been applied or proposed for `StExp`/`StressLeaf` — none is
  warranted independent of the `CC` drift fix.
- BMI-path-specificity has not been separately checked (low priority
  given the finding is cosmetic and traced to shared `global.f90`/
  `simul.f90` physics reached identically from both entry points, same
  as every other fork defect found in this project).

## Next step

None for `StExp` itself. Root-causing the underlying `CC` precision
drift (`docs/bmi/FORTRAN_FORK_BIOMASS_YIELD_DRIFT.md`) will, if fixed,
very likely also close this flip as a side effect — worth re-checking
once that investigation concludes, but not worth independent effort
before then.
