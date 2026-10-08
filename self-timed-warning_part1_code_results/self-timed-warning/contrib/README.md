# Complete CAT analysis

Run from the repository root, using the numerical package versions in `requirements.txt`, Python 3.12.4 for this platform and `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`. At most two experiment processes may run concurrently. Checkpoints resume completed folds; do not reuse them after changing the numerical environment or decision code.

The current user's completion instruction authorizes the remaining analyses. The original plan and Amendment 1 hashes are preserved. `docs_contrib/EXECUTION_NOTES.md` records implementation repairs and claim corrections.

1. `python contrib/verify_plan.py`, `python tools/check_data.py`, `python contrib/test_cat.py`.
2. Synthetic phase: `python contrib/cat_sim.py A C`, `python contrib/cat_sim.py B`. Saved complete outputs supplied with this workspace are retained. Supplement with `python contrib/cat_kmin_sim.py` (explicit fixed-rule earliest-of-five check, 20,000 replicates per certifiable cell). KMIN has no general single-rule lower bound.
3. `python contrib/cat_run.py FD001` if the completed FD001 outputs are absent. Then `python eol_window2.py FD001 20`, `python contrib/cat_equiv.py`, `python contrib/cat_leak.py`. Any failed integrity check stops subsequent real-data runs.
4. Run `python contrib/run_remaining.py a` and `python contrib/run_remaining.py b` concurrently. Queue a: FD002, FD004. Queue b: FD003, PHM08, N-CMAPSS, battery and bearings. Each queue writes per-stage logs and status JSON, and stops on failure. Battery/bearing checks use the original scripts on this platform, following Amendment 1.
5. `python contrib/cat_summarize.py`, `python contrib/verify_completion.py`, `python contrib/build_report.py`.

Main deliverable: `docs_contrib/FINAL_REPORT.md`. Numerical evidence: `out/contrib/contrib_numbers.json`, per-unit CSVs, tables, figure and `completion_audit.json`. The `paper7` evidence bundle adds contribution results to the earlier manuscript's numbers. It is a research assessment, not a submission-ready manuscript rewrite.

The statistical guarantee is for a fixed alarm rule with exchangeable calibration/test scores and feasible actions. OOF refitting and calibration-dependent setting selection in the implemented variants do not automatically inherit it. Finite-statistic flags and non-rejection of pooled CV binomial screens are not certification of a deployed model.
