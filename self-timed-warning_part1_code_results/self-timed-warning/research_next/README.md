# Completed mechanism investigation

Read [FINAL_SCIENTIFIC_REPORT.md](FINAL_SCIENTIFIC_REPORT.md) for the verdict and all ten phases/16 pitch items, [MATHEMATICAL_STATUS.md](MATHEMATICAL_STATUS.md) for derivations, and [LITERATURE_AUDIT.md](LITERATURE_AUDIT.md) for prior-work scope.

**Novelty gate: not passed.** This module implements diagnostic replay and established reference calculations; it does not implement a novel optimizer. The user's explicit negative-novelty fallback is followed. No new-method benchmark or component-removal result is fabricated. All diagnostics are post hoc.

## Environment and commands

Run from the repository root using the existing pinned `.venv` (Python 3.12.4, NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, scikit-learn 1.8.0). Fix numeric-library threads:

```powershell
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:PYTHONUTF8='1'
.venv/Scripts/python.exe research_next/reconstruct_battery.py 0
.venv/Scripts/python.exe research_next/reconstruct_battery.py 1
.venv/Scripts/python.exe research_next/stress.py
.venv/Scripts/python.exe research_next/statistics_audit.py
.venv/Scripts/python.exe research_next/build_report.py
.venv/Scripts/python.exe research_next/verify.py
```

The two reconstruction queues cover disjoint original splits and may run concurrently, with at most two workers. Each fits only the original selected cap/setting and asserts all frozen CAT/CAT-c unit decisions. Subsequent scripts read these isolated scores. Calibration permutations/noise use seeds 2026–2035; paired cost bootstrap uses seed 2027 and 2,000 resamples. Original fitting/preprocessing seeds are retained. The verifier reruns the 11 unit-test groups and writes an UTF-8 log and completion manifest.

`audit.py` was run once before new fitting to create the protected-file baseline and inventories. **Do not rerun its inventory entry point on the current workspace to reset that baseline.** For a clean independent reproduction, copy the original frozen project before producing any new outputs and run `audit.py` there first; retain the original baseline when validating this workspace. Its output includes complete CSV/JSON parsing and source symbol inventories, not a manual review claim for every ancillary script.

## Output map

| Output in `out/research_next/` | Meaning |
| --- | --- |
| `protected_before.json` | Pre-investigation SHA-256 of 591 existing files |
| `source_inventory.csv`, `source_symbols.json` | 168 source files, 90 Python ASTs, symbols/imports |
| `frozen_output_inventory.csv` | 284 existing artifact hashes and parsing metadata |
| `policy_cells.csv`, `paired_effects.csv`, `battery_by_batch.csv` | Existing outcomes, paired effects and batch heterogeneity |
| `setting_confound.csv`, `catc_changes.csv`, `score_shift.csv` | Setting mismatch, threshold changes and full engine score audit |
| `battery/*_scores.csv`, `*_tables.npz`, `*_check.txt` | Eight original battery splits; source/target scores, alarm tables and exact replay checks |
| `calibration_stress.csv.gz`, `calibration_stress_summary.csv` | All 247,680 fixed-signal stress rows and mean/SD/median/availability summaries |
| `noise_stress_summary.csv` | Full-calibration, unshifted-target noise summary |
| `battery_score_shift.csv` | Common-threshold source OOF/inner-target/refit-target tails |
| `target_label_reference.csv`, `target_label_reference_summary.csv` | 1,920 completed-target-life calibration cases, with held-out evaluation |
| `cost_matrix_stress.csv` | 640 fixed-policy economic stress cells, with selection rho=10 |
| `lobo_paired_validation.csv` | 96 paired risk comparisons; full-family Holm; approximate paired cost intervals |
| `all_dataset_effects.csv`, `fold_effects*.csv`, `win_tie_loss.csv` | All-engine/battery effect sizes, descriptive fold statistics and qualified legacy verdicts |
| `*_table.md`, `battery_diagnostics.png/svg` | Generated readable tables and standalone scientific figure |
| `unit_tests.log`, `completion_manifest.json` | New test/check status, environment, hashes and explicit phase/novelty status |

The target-label reference calibrates source-trained fixed rules using completed target lives. It is established rank calibration, not a new method; at small budgets its maximum-grid fallback is not a certificate. Scores/noise are operational critical-score perturbations, not raw-sensor corruption. Seed variation resamples calibration; it does not retrain independent models. Cost cells reuse units. Original bearing/M/synthetic experiments stay frozen and are interpreted in the report rather than newly rerun.
