# Exact shared-lifetime relative regret

Start with [REPORT.md](REPORT.md), then [THEORY.md](THEORY.md), [LITERATURE.md](LITERATURE.md) and [PRIORITY_DOSSIER.md](PRIORITY_DOSSIER.md). Outcome **B: potentially novel but insufficiently established**. The implementation exactly solves its stated finite-cohort model; historical priority and future-population superiority remain unestablished.

Run from the repository root using the existing virtual environment:

```powershell
$env:PYTHONUTF8 = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
.venv/Scripts/python.exe -m unittest clock_regret.test_core -v
.venv/Scripts/python.exe -m clock_regret.run
.venv/Scripts/python.exe -m clock_regret.analyze
.venv/Scripts/python.exe -m clock_regret.report
.venv/Scripts/python.exe -m clock_regret.verify
```

`run` regenerates only the new experiment outputs, checking all 809 frozen prior artifacts before and after. `analyze` reads a pure Holm utility from the previous validation module; it does not run or overwrite that module's experiments. `report` writes the new report, an exact mechanism example and scientific PNG/SVG figures. `verify` runs the new test suite and independently checks stored witnesses, statistics, public/hidden separation, exact recommendations, provenance and protected hashes, then hashes all new deliverables. Runtime fields and gzip headers can change on rerun; repeat verification to create the corresponding manifest.

The main APIs in `core.py` are `worst_pair(horizon, logger_failed, age_a, age_b, rho)` and `select(horizon, logger_failed, ages, rho)`. Inputs are positive integer logging endpoints and ages, binary failure indicators and a common integer failure-cost ratio greater than one. The returned exact `Fraction` factors include one. Selection takes no hidden lifetime, survival law, future alarm or life cap. Adversarial witnesses are mathematical compatible completions, not measured lifetimes or imputed predictions.

The implementation checks that `n * (max(H, ages, rho) + 1)` fits in int64, rejecting larger inputs before clock arrays or prefix sums can overflow. Fraction cross-products then use Python arbitrary-precision integers. This computational range restriction is separate from the mathematical theorem and a physical lifetime cap.

```python
from clock_regret.core import select
ages = [8, 12, 16, 24]
r = select([6]*12, [False]*12, ages, 20)
print(ages[r['chosen']], r['scores'][r['chosen']])  # 8, 3
```

`oracles.py` supplies full-clock exhaustion and a separately structured failure-count/exposure-hull state optimizer. `test_core.py` includes 250 exhaustive and 100 generic-state checks; the stored runtime audit adds 120 generic-state checks. Synthetic experiments contain 2,400 independent cohorts, four selectors each. Real replay has 304 cohort tasks, four selectors each. The public records and sealed truth are separate compressed CSVs, with `case` and `unit` as join keys. Pairwise files retain exact numerators, denominators and attaining lifetime witnesses.

Main output paths under `out/clock_regret/`:

- `synthetic_*` and `real_*`: complete records, choices, paired contrasts, statistics and summaries; Battery CV is sensitivity only.
- `independent_oracle_audit.csv`, `oracle_runtime_summary.csv`, `scaling.csv`: exact oracle comparisons and exploratory timing.
- `strict_example.json`, `shared_clock_example.png/.svg`, `synthetic_tradeoff.png/.svg`: mechanism and empirical tradeoff artifacts.
- `protected_before.json`, `plan_sha256.txt`, `verification.json`, `tests.log`, `research_record.json`, `completion_manifest.json`: integrity, tests and internal provenance.

No old CAT, RAMPE, observability or method-validation outputs were modified. No external publication or public priority registration was performed.
