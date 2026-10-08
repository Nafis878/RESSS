# Paired maintenance-observability research pivot

Read [REPORT.md](REPORT.md) and [LITERATURE.md](LITERATURE.md). **Status: candidate benchmark/empirical contribution; no established novel learning method.** All old CAT and RAMPE outputs are protected and unchanged. No public publishing, messaging, dataset uploading or training-service use was performed.

From the repository root, with the existing pinned Python environment:

```powershell
$env:PYTHONUTF8='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
.venv/Scripts/python.exe observability/run.py
.venv/Scripts/python.exe observability/test_core.py
.venv/Scripts/python.exe observability/analyze.py
.venv/Scripts/python.exe observability/verify.py
```

`run.py` creates or checks a one-time protection manifest. Never reset it after changing old outputs. The first experiment attempt hit an import-name collision before output generation; it is retained in `out/observability_run.log`, and the corrected completed run in `out/observability_run_corrected.log`. The experiment plan hash is retained. Generated CSV gzip byte hashes may change on a value-identical rerun because gzip headers contain write times; compare values when reproducing new outputs, and bytes when checking protected originals.

## Schema and evaluator contract

`out/observability/public_outcomes.csv.gz`: one row per original unit, logger policy, target policy, split, lead and rho. Public columns: `task`, `dataset`, `analysis`, `split`, `lead`, `rho`, `logger`, `target`, `unit`, `logger_endpoint`, `logger_cost`, `logger_fail`, `outcome_observed`, `target_cost`, `target_use`, `target_fail`. Unresolved target fields must be NaN. The observations are coarsened outcome-summary replay, not raw sensor traces. Unit identifier and task settings are metadata; no future RUL is included.

`sealed_truth.csv.gz`: same keys with full target cost/use/failure for scoring. It is separate in the API, but available locally and not secured from benchmark participants. It must not be an input to `identify()`, policy choices or point estimators. An evaluator owner would need separate storage and a held-out leaderboard before public competitive benchmarking.

`task_results.csv.gz`:9728 tasks ×3 cap assumptions. `information_budget.csv.gz`:9728 tasks ×10 seeds ×5 information-release fractions. Releases are retrospective evaluator information, not feasible physical inspections.

Headline summaries exclude self-policy comparisons and use cap5000. Every pair/setting and cap result remains available; no task is discarded for poor results. Rate intervals concern ratio-of-total-costs to total-use, not mean individual cost rates. Risk is the finite-cohort failure fraction. Neither is a future population certificate. Missing durations have the continuous-time constraints horizon<use≤cap; the original integer-cycle data fit inside that larger outcome model.

`findings.json` contains counts; pair/domain/setting summaries and `observability.png/.svg` expose the result. `verification.json`, `unit_tests.log`, `completion_manifest.json` record correctness/protection, and [THEORY.md](THEORY.md) proves the stated interval contract. “Sharp” means sharp only in the coarsened continuous-time outcome model; fixed sensor policies can impose additional restrictions.

No model selection, new predictor training, Kaplan–Meier/IPCW superiority, deployment claim, operational counterfactual effect, conformal guarantee or RL result is implied. The resource builds on existing public/retrospective data, whose source licenses and original attribution still govern redistribution. It remains a local research artifact; a public release requires a source-license and provenance review.
