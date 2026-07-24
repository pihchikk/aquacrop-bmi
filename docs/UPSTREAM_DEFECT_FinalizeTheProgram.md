# Upstream defect: `FinalizeTheProgram` aborts under library/BMI embedding

## Summary

`FinalizeTheProgram()` in AquaCrop's `startunit.F90` writes its end-of-run
marker `AllDone.OUT` through a **relative-path `open()` with no `iostat=`**.
When the program is embedded as a library (BMI / coupled / multi-instance)
and `finalize()` is invoked from a process working directory other than the
project directory, that `open()` fails, gfortran raises an unhandled runtime
error, and the process `abort()`s (exit code 2). The abort is uncatchable
from the embedding (Python/Cython) layer and takes down the whole caller.

This is a **latent upstream defect**, not a fork regression: the offending
line is byte-identical to KUL-RSDA AquaCrop v7.3.

## Provenance

- Fork: `aquacrop_fortran/startunit.F90:1851`, in `FinalizeTheProgram()`.
- Upstream: `src/startunit.F90:930` (KUL-RSDA AquaCrop v7.3) — **byte-identical**.

```fortran
open(newunit=fend, file=(GetPathNameOutp() // 'AllDone.OUT'), &
     status='replace', action='write')
```

`GetPathNameOutp()` returns a **relative** path (`'OUTP/'`). There is no
`iostat=` on the `open()`, so a failure is fatal rather than recoverable.

## Why console mode never hits it

The AquaCrop console executable always runs from the project directory, so
`'OUTP/'` always resolves and the `open()` always succeeds. The defect is
therefore invisible in normal command-line use and only manifests through
library/BMI embedding where the caller's cwd is arbitrary.

## Why it matters

`finalize()` is routinely called from a cwd ≠ project dir in exactly the
scenarios the BMI exists for:

- multi-instance spatial runs (N models driven from an orchestrator's cwd),
- any coupled / framework-driven setup (e.g. driven from a coupler's cwd).

The genuine finalization work (`FinalizeRun1/2`, `FinalizeSimulation`)
completes **before** this line, so no simulation data is lost or corrupted —
but the spurious abort still kills the calling process.

## Minimal reproduction

1. Build the BMI library.
2. From Python, `initialize()` a model with an absolute config path.
3. `chdir` the process to any directory other than the project dir
   (e.g. `/tmp`).
4. Call `finalize()`.

Result (unpatched): process exits 2 (abort) instead of returning cleanly;
`AllDone.OUT` is not written.

## Sibling instances of the same pattern (latent)

The same "relative path, no `iostat=`" `open()` pattern exists at:

- `aquacrop_fortran/global.f90:5384` — `TCrop.SIM` (upstream).
- `aquacrop_fortran/tempprocessing.f90:2677` — `TestBio.SIM` (fork-added,
  debug-gated behind `if (TestRecord .eqv. .true.)`).

Neither executes after the working directory has been reverted, so neither
manifests today, but both are the same latent fragility and should be
hardened if upstream addresses the pattern generally.

## Fork mitigation (does not touch upstream code)

The fix is confined to the BMI wrapper; `FinalizeTheProgram` itself is left
byte-identical to upstream:

- `BMI_InitializeAquaCrop` captures the absolute project directory into a
  module-level save variable (`bmi_project_dir`) right after its `chdir`.
- `aquacrop_finalize` (BMI wrapper) `chdir`s back to `bmi_project_dir`
  before calling into `FinalizeTheProgram`, then restores the caller's
  original cwd afterward.

Known limitation (by design, not fixed): with two simultaneously-live
instances in one process, the older instance's `AllDone` marker lands in the
most-recently-initialized project's `OUTP/`, because `bmi_project_dir` is
process-global. This mirrors AquaCrop's existing process-global BMI state
(two live instances already share the entire simulation state), it is
cosmetic (`AllDone` is only an end-marker), and papering over it per-instance
would mask the cosmetic symptom while the deeper shared-state limitation
remains.

## Suggested upstream fixes (for reporting to KUL-RSDA)

1. Add `iostat=` to the `AllDone.OUT` `open()` (and the sibling `.SIM`
   opens) and handle failure gracefully instead of aborting; **and/or**
2. Resolve output paths against a stored absolute output directory rather
   than a relative one, so finalization is independent of the process cwd.
