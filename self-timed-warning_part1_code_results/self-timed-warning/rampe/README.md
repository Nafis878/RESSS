# Reproduce the completed RAMPE investigation

Start in the repository root `self-timed-warning_part1_code_results/self-timed-warning`. New sources live in `rampe/`; new outputs in `out/rampe/`. Read [FINAL_REPORT.md](FINAL_REPORT.md) for the verdict and scope. This experiment does not retrain predictors, modify original results, implement RL or establish deployment safety.

The existing `.venv/Scripts/python.exe` is Python 3.12.4 with NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, scikit-learn 1.8.0 and Matplotlib 3.10.9. The manifest records actual runtime versions. No package update is required.

Set thread limits in PowerShell and execute each command separately:

```powershell
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:PYTHONUTF8='1'
.venv/Scripts/python.exe rampe/test_core.py
.venv/Scripts/python.exe rampe/real.py
.venv/Scripts/python.exe rampe/synthetic.py
.venv/Scripts/python.exe rampe/stress.py
.venv/Scripts/python.exe rampe/temporal.py
.venv/Scripts/python.exe rampe/statistics.py
.venv/Scripts/python.exe rampe/build_report.py
.venv/Scripts/python.exe rampe/verify.py
```

Experiments are substantial; run at most two worker processes simultaneously. Outputs are regenerated only in `out/rampe/`. `prepare.py` was run once to capture protection hashes and causal contexts before experiments. **Do not reset `frozen_before.json` or rerun preparation against a changed baseline.** The script refuses to reset an existing baseline. The plan hash verifies that the saved protocol was not silently rewritten after observing results.

For a quick integrity/test audit, run only `verify.py`. It reruns current RAMPE unit tests and writes current RAMPE verification files. Do not run old project verification scripts that overwrite protected logs. The old manifests and their outputs must remain intact.

Core input files are seven frozen `results/contrib/*_cost.csv` tables, original causal context inputs, and previous manifests. `load_groups()` aligns all four policy outcomes by original unit, split, lead and cost. Labels for additional meta-validation are disjoint from meta-test, but consume held-out completed lives. Learned meta-training excludes its entire held-out dataset; it has an additional other-domain label budget and is not an information-free transfer method.

Outputs:

- `real_results.csv.gz`: 6080 episodes ×20 methods. Paired units, partitions, meta-features, learned probabilities and model coefficients permit leakage/authority checks.
- `synthetic_results.csv.gz`: 288 conditions ×30 seeds plus two attacks ×30 seeds, all ×18 methods. Known population rate/risk and fractional oracle included.
- `validation_stress.csv.gz`: 329080 method cases; `fixed_rule_shift.csv.gz`:45600 method cases.
- `temporal_reference.csv.gz`:8640 full-information reference outcomes. No bandit/RL result is implied.
- Summary, paired-test, conditional-bootstrap and fragility CSVs retain all conditions. `statistical_scope.json` states actual test-family sizes.
- `legacy_stress_bridge.json`: every old score-stress row was read/preserved, with an explicit incompatibility statement.
- `verification.json`, `unit_tests.log`, `run_manifest.json`: integrity/test/scope evidence. Logs named `statistics.log`, `statistics_final.log` and `statistics_reviewed.log` retain successive analysis attempts; only the final reviewed outputs support the report.

Mean episode rates are descriptive averages of repeated splits/settings. Real bootstrap intervals condition on fixed rules/authorities and one seed; no independence across repeated partitions is assumed. Synthetic inference applies to independent simulated validation cohorts and does not establish real-world performance. RNG settings are in the source and plan; compressed CSV file bytes may differ across reruns because gzip headers can encode write time, even when values are identical. Preservation is checked against the original bytes, while reproduction of new results should compare values.
