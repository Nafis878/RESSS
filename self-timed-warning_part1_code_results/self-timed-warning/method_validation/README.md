# Statistical and method validation

Read [REPORT.md](REPORT.md) for the verdict and [LITERATURE.md](LITERATURE.md) for primary sources. This is a new audit of frozen results, not a modification of CAT, RAMPE or the previous observability benchmark.

From the repository root in PowerShell:

```powershell
$env:PYTHONUTF8='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
.venv/Scripts/python.exe -m method_validation.run
.venv/Scripts/python.exe -m method_validation.sensitivity
.venv/Scripts/python.exe -m method_validation.report
.venv/Scripts/python.exe -m unittest method_validation.test_validation -v
.venv/Scripts/python.exe -m method_validation.verify
```

The main run takes about40seconds here. Outputs are written only under `out/method_validation/`. Protection hashes are checked before and after. If protected input bytes differ, stop and investigate rather than resetting the hashes. `PLAN.initial.md` preserves the initial pre-run plan; `PLAN.md` adds transparent interpretation and exploratory sensitivity amendments.

`paired_sign_tests.csv`: 21 Holm-corrected primary tests, three separate Battery CV sensitivity tests, one full paired contrast per asset. Mean-effect confidence intervals are nominal, conditional, not simultaneous.

`bootstrap_summary.csv`, `fixed_domain_composite_summary.csv`: linear means have nominal conditional bootstrap intervals; threshold metrics have **resampling sensitivity ranges**. `point_outside_range` flags nonregular behavior. Do not turn those ranges into inferential confidence intervals. Older premature labels are archived in `diagnostics_initial/` and excluded from the final evidence tables.

`bootstrap_draws.csv.gz`: all resampling draws; `paired_asset_contrasts.csv`: exact assets and contrasts; `outer_group_sign_sensitivity.csv`: explicitly exploratory group-level sensitivity, not independent retraining validation; `generic_lp_equivalence.csv.gz`: independent box-constrained linear-fractional baseline reconstruction for all29,184 cap evaluations.

`verification.json` and `completion_manifest.json`: checks and artifact hashes. Read the scopes in the report before reusing any p-value or interval. Statistical significance does not establish priority; the method verdict isNO.
