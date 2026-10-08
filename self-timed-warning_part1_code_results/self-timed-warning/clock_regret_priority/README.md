# Attributed contribution and historical-equivalence audit

Author identity supplied by the researcher: **Nafis Wadud Ansari**,
**Daffodil International University**, ansari2305341800@diu.edu.bd.

The latest draft is `out/clock_regret_priority/manuscript.pdf` (seven pages).
Read `REPORT.md`, `THEORY.md`, `LITERATURE.md` and `REVIEW.md` for the status.
The previous five-page manuscript and every earlier artifact remain preserved.

## What this follow-up adds

- Exact later-versus-earlier rate-ratio optimization with positive rational,
  asset-specific failure premiums, by sorting and scanning premium prefixes.
- A strict interior optimum demonstrating why the common-cost two-world formula
  cannot be used unchanged with heterogeneous costs.
- The continuous heterogeneous-cost counterpart and proof that the uniform
  pairwise clock-refinement factor 1+1/r is sharp.
- Full primary-text comparison with the Bayesian censoring preprint and the
  published no-overlap evaluation paper; additional older relative-ratio prior art.
- Attributed scientific draft, independent exact checks and a review archive.

The mathematical result is supported by constructive proofs and exact audits.
**Historical originality and public priority are still unestablished: verdict B.**
Fox's full proof and the separate moment-robust conference manuscript remain
access gaps. No external reviewer, accepted publication or public deposit is
invented. The user's requested publishing destination remains pending.

## Reproduce

Run at the project root with the existing Python 3.12 environment. New experiments
use NumPy and pandas; PDF authoring uses reportlab, pypdf and PyMuPDF. All input
seeds are fixed in the retained prospective plan. The new APIs accept exact
integer clocks and positive rational premiums, with preventive cost one. No
hidden lifetime input is accepted. Failure at an age deadline counts as failure.

```powershell
$env:PYTHONUTF8 = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
.venv/Scripts/python.exe -m unittest clock_regret_priority.test_heterogeneous -v
.venv/Scripts/python.exe -m clock_regret_priority.run
.venv/Scripts/python.exe -m clock_regret_priority.report
.venv/Scripts/python.exe -m clock_regret_priority.verify
```

Rebuilding the PDF requires visual inspection of all freshly rendered pages.
Do not rebuild earlier modules' outputs: all 908 previous artifacts are protected.
For the new theorem's later comparison only:

```python
from clock_regret_priority.heterogeneous import later_pair, continuous_later_pair

pair = later_pair([1,1,1], [True,False,False], 3, 2, [98,1,100])
assert str(pair.ratio) == '505/306'
assert pair.shared_count == 1
assert pair.witness == (1,2,3)
limit = continuous_later_pair([1,1,1], [True,False,False], 3, 2, [98,1,100])
compatible_world = limit.completion()
```

The independent phase oracle can be exponentially expensive; it validates small
cases and is not the advertised sorted-premium method. The heterogeneous API
does not solve general earlier-versus-later or full-family heterogeneous-cost
selection in polynomial time. Array clock validation reserves int64-safe totals;
premiums and objectives use arbitrary-precision fractions. Floats are rejected
for premiums; use integers, `Fraction`, or exact rational strings.

## Review archive

The ZIP contains the new source, proof, draft, derived tables and provenance,
plus the frozen helper modules needed for isolated mathematical tests. It also
contains the previous source/theory/MD manuscript and its two figure PNGs needed
by the new manuscript builder. It excludes third-party full papers, primary
cache text, page QA images, environments, bytecode and raw datasets.

Mathematical tests run from an independently extracted archive. Full preservation
audits require the complete original workspace. `payload_hashes.json` inside the
archive verifies its contents; the outer completion manifest verifies every new
artifact and the archive, excluding its own hash. This is an unpublished internal
review package with no invented public-release license.

The primary cache is private research material with retrieved hashes, not a
redistribution bundle. `fetch.py` records ordinary public retrievals and failures;
no access restriction is bypassed. The novelty gate and public disclosure status
are separate from algorithm correctness and from the previous runtime tests.
