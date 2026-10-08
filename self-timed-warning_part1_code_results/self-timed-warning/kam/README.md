# Comparison with the decision-oriented metric M of Kamariotis et al. (2024)

Re-implementation of their metric (RESS 242:109723; arXiv:2306.03759v2) and evaluation of the alarm policies of this
repository under their conventions. All analyses here are exploratory and post hoc. The Phase 2 plan was fixed and hashed
before the run (`PHASE2_PLAN.md`, `PHASE2_PLAN.sha256`).

| Order | Script | What it does | Output (frozen copy in `results/kam/`) | Seeds |
|---|---|---|---|---|
| 1 | `kam_metric.py` | Module: their Eqs. (2)–(9), grid-perfect policy, grid mapping, footnote-1 check, paired bootstrap of M differences | – | – |
| 2 | `test_kam_metric.py` | Unit tests: M = 0 for the perfect policy, M ≥ 0 for grid policies, hand-computed 3-unit example, recorded violations | `test_kam_metric.log` | 0 |
| 3 | `kam_grid_effect.py` | Reference-grid effect: existing cost results (ℓ = 0) against the 1-cycle and the 10-cycle-grid perfect policy | `grid_effect_policies.csv`, `grid_effect_summary.csv` | – |
| 4 | `kam_simulator.py` | Their virtual RUL simulator (Sec. 3) with policies 1–3; qualitative check against their Figs. 4–5 | `sim_results.csv`, `sim_pthres.csv`, `sim_pairs.csv`, `sim_checks.txt` | 2026 (σ = 0.4), 2027 (σ = 0.15); bootstrap 7 |

Run from the repository root, e.g. `python kam/test_kam_metric.py`, `python kam/kam_grid_effect.py`, `python kam/kam_simulator.py`
(about 2 min on 2 cores). Outputs go to `out/kam/`.

## Phase 2 (FD001)

| Order | Script | What it does | Output (frozen copy in `results/kam/`) | Seeds |
|---|---|---|---|---|
| 5 | `kam_fd001.py cv` | Protocol (B): five-fold CV, all policies, all seven cost ratios; E1 inside every split | `fd001_cv_units.csv`, `fd001_cv_settings.csv`, `fd001_cv_bins.csv` | outer 2026, inner 100 + fold, 1-SE bootstrap 2026 + fold, GBMs 0 |
| 6 | `kam_fd001.py leak` | Leakage checks E2–E4 on fold 1 | `fd001_leakage.txt` | 0 |
| 7 | `kam_fd001.py splits 1 15`, `splits 16 30` | Protocol (A): 30 random 80/20 splits | `fd001_rs_1_15_*`, `fd001_rs_16_30_*` | permutation 31000 + s, inner 3100 + s, 1-SE bootstrap 2026 + s |
| 8 | `kam_fd001_summarize.py` | Tables: M, Eq. 7 and bootstrap intervals, paired differences and verdicts, spread over splits, bins, thresholds | `fd001_cv_table.csv`, `fd001_cv_pairs.csv`, `fd001_rs_policies*.csv`, `fd001_rs_pairs.csv`, `fd001_bins_*.csv`, `fd001_thresholds.csv`, `fd001_summary.md` | bootstrap 2027 (+ split) |

Each split takes about 3 min on one core; the whole of Phase 2 takes about 105 CPU-minutes. The per-unit outputs are frozen as
`results/kam/fd001_cv_units.csv.gz` and `fd001_rs_*_units.csv.gz` (with `_settings.csv`, `_bins.csv`); `kam_fd001_summarize.py --frozen`
rebuilds every Phase 2 table from them.

## Phase 3 (FD002-FD004, robustness of threshold optimisation) and Phase 4 (open weaknesses)

Plan fixed and hashed before the runs: `PHASE3_4_PLAN.md`, `PHASE3_4_PLAN.sha256`. All analyses exploratory. Run every
process single-threaded (`OMP_NUM_THREADS=1`; the fitted trees are identical to two-thread runs, checked) and at most two at
a time on two cores: several processes with multi-threaded OpenMP on two cores slow each other down by an order of magnitude.

| Order | Script | What it does | Output (frozen copy in `results/kam/` or `results/audit/`) | Seeds |
|---|---|---|---|---|
| 9 | `kam_fd001.py cv --ds FD002` (FD003, FD004), then `leak --ds ...` | The Phase 2 code path on FD002-FD004, five-fold; leakage checks E2-E4 | `<ds>_cv_units.csv`, `<ds>_cv_settings.csv`, `<ds>_cv_bins.csv`, `<ds>_leakage.txt` | as Phase 2 |
| 10 | `kam_fd001_summarize.py --ds FD002` (FD003, FD004) | Tables as Phase 2 | `<ds>_cv_table.csv`, `<ds>_cv_pairs.csv`, `<ds>_bins_*.csv`, `<ds>_thresholds.csv` | bootstrap 2027 |
| 11 | `check_r0.py` | Check R0: the Phase 2 re-run after the workspace reset reproduces the frozen FD001 tables | `r0_check.txt` | – |
| 12 | `kam_fragility.py` | Their Fig. 9a on our data; failures of threshold-optimised policies across test sets; tie rules; decision rule of the plan | `fragility_*.csv`, `fragility_summary.md` | – |
| 13 | `../audit_hi_calibrated.py PHM08 FD001 FD002 FD003 FD004 NCMAPSS6` | 4b: linear health indicator calibrated to cycles (isotonic, inner OOF) with the recipe's trigger | `hi_calibrated_<ds>.csv`, `hi_calibrated_check.txt` | outer 2026, inner 100 + fold |
| 14 | `../audit_battery_cost_nested.py` | 4a: battery cost, fully nested, task in cycles (convention C); check R4a | `cost_battery_nested.csv`, `cost_battery_nested_h60.csv`, `cost_battery_nested_check.txt` | as `audit_battery_cost2.py` |
| 15 | `../audit_fixed_matched.py --ds FD004` | 4d: matched fixed-time vs self-timed decomposition on FD004; check R4d | `fixed_matched_FD004.json`, `fixed_matched_units_FD004.csv` | outer 2026, inner 100 + fold |
| 16 | `make_rev5_numbers.py [--frozen]` | Collects every number of the third revision into `paper5/numbers.json` (key `rev5`) | – | bootstrap 2027 |

The 30 random FD001 splits are run as two processes (`splits 1 15`, `splits 16 30`). Compute on 2 cores, single-threaded:
FD001 five-fold 16 min, each split 3 min, FD002 and FD004 about 45-50 min each, FD003 18 min, each leakage check about one
fold; battery cost 18 min; FD004 decomposition about 50 min; calibrated indicator 5 min.
