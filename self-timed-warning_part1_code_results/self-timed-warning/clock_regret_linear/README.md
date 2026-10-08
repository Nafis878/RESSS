# Exact relative-regret replacement: completed computational contribution

This directory contains the new exact integer solver, continuous extension,
constructive proofs, computational study and research draft. The final scientific
status is **B: a precise, potentially novel contribution supported by proofs and
tests; historical originality and public priority remain unestablished**.

Start with `REPORT.md`, `THEORY.md`, `MANUSCRIPT.md` and `LITERATURE.md`.
The PDF and all new evidence are in `out/clock_regret_linear/`.
`PRIORITY.md` states the disclosure claim and the outstanding author/account
metadata. No DOI, accepted publication, author identity or public disclosure was
invented. The review archive is local and unpublished.

## Reproduce in the preserved workspace

Run from the project root, using its existing Python environment. Dependencies:
Python 3.12, NumPy, pandas, SciPy, matplotlib, reportlab, pypdf and PyMuPDF.
The observed versions are recorded in `research_record.json`.

```powershell
$env:PYTHONUTF8 = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
.venv/Scripts/python.exe -m unittest clock_regret_linear.test_core -v
.venv/Scripts/python.exe -m clock_regret_linear.run
.venv/Scripts/python.exe -m clock_regret_linear.resolution_run
.venv/Scripts/python.exe -m clock_regret_linear.report
.venv/Scripts/python.exe -m clock_regret_linear.verify
```

`run` replays the frozen public inputs and recomputes timings. The timing seed,
repetitions and amended independent sample count are fixed in the retained plan;
elapsed values depend on the computer. `resolution_run` recomputes the continuous
oracle and refinement studies. `report` rebuilds the manuscript and renders every
page; any rebuilt PDF must be visually inspected before delivery. `verify`
recomputes unit tests and stored evidence checks, checks the earlier 858 protected
artifacts, records provenance, builds a review archive and hashes all new files.
It does not rerun the timing experiment or change the frozen earlier results.
After editing, regenerate the report and repeat visual QA before `verify`.

Do not run earlier modules' writeful experiment/report commands: all earlier
artifacts are protected, including the predecessor `clock_regret` implementation.
The new modules import its pure validation and independent state-oracle helpers.

## Using the method

```python
from clock_regret_linear.core import select
from clock_regret_linear.continuous import select as continuous_select

answer = select([1, 1, 5], [False, False, True], [2, 4, 20], rho=20)
# chosen is an index in the supplied candidate list; scores are exact Fractions.
continuous_answer = continuous_select([1, 1, 5], [False, False, True], [2, 4, 20], 20)
# A continuous pair may supply a limiting world, rather than an attained optimum.
world = continuous_answer['pairs'][0][1].completion()
```

Inputs are public recording horizons and observed-failure flags. The APIs accept
no sealed lifetimes. Use `include_witness=False` with the integer API to avoid
retaining all witness vectors. Horizons and ages are positive integers, the
implementation accepts an integer common cost ratio greater than one, and
overflow-prone array totals are rejected. The continuous model varies latent
lifetimes while retaining exact recorded horizons and ages.

## Review archive and integrity

`review_bundle.zip` contains the new source, manuscript, derived evidence,
provenance and the two frozen helper modules needed for mathematical unit tests.
It includes frozen public replay inputs and the predecessor comparison tables.
It excludes raw original datasets, local environments, bytecode, QA page images
and the archive itself. It is an internal review bundle, with no invented license
or authorization for public dataset redistribution. Public release requires a
rights check and actual authorship metadata.

After extraction, unit tests and theorem implementations work with the included
helpers. Full `run`, `resolution_run` and `verify` protect all 858 original files
and therefore require the preserved full workspace; a partial archive cannot
substitute for that integrity audit. `payload_hashes.json` inside the ZIP checks
every included payload. `completion_manifest.json` outside it checks the ZIP
and every new artifact; the manifest deliberately excludes its own hash.

The 84 independently generated timing inputs are the statistical units, rather
than the 252 repeated measurements. Holm correction covers seven size contrasts.
These tests establish computational acceleration against the specified frozen
implementation. They do not prove originality or improved maintenance outcomes.
