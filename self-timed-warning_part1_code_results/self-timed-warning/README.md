# Self-timed end-of-life warnings: code, data and frozen results

Reproduction package for the third revision of the manuscript, *"Evaluating end-of-life alarms: observation time, alarm
timing, maintenance cost and transfer"* (`paper5/`), and for its earlier versions (`paper4/`, `paper3/`, `paper2/`). Every
number, table and figure of every version can be regenerated from this repository, and verification scripts check that the
regenerated results are identical to the reference copies.

## CAT contribution analysis

The additional contribution plan is in `contrib/PLAN.md`; its original and amended hashes are preserved.
Run instructions are in [contrib/README.md](contrib/README.md), and implementation and interpretation corrections
are in [docs_contrib/EXECUTION_NOTES.md](docs_contrib/EXECUTION_NOTES.md). The complete suite passed the completion audit
on 8 October 2026. Read [the final assessment](docs_contrib/FINAL_REPORT.md); the numerical snapshot is in
`results/contrib/`, with pairing, input, source and output hashes in `completion_audit.json`.
CAT comparisons use recomputed baselines on the same platform, following Amendment 1. The `paper7` assessment
bundle preserves paper6 evidence and adds these results; it does not replace the historical manuscript.

## Reframed manuscript (paper6)

`paper6/` is the submission version: the same evidence as `paper5/` (identical `numbers.json`, no analysis added or rerun),
with the text reorganised around what an end-of-life alarm score measures. Tables, figures and sections are cross-referenced
automatically, and `reproduce_revision5.sh` also rebuilds `paper6/` and checks it against `paper6/reference/`
(`REFRAMED-MANUSCRIPT REPRODUCTION CHECK PASSED`).

## Third revision (paper5): comparison with the metric M of Kamariotis et al. (2024)

The third revision re-implements the decision-oriented metric *M* of Kamariotis et al. (RESS 242:109723, 2024; from the
preprint arXiv:2306.03759v2, without their code) and evaluates the alarms of this repository and their policies 1 and 3,
built on the same regressor, under their conventions (decision grid ΔT = 10, no lead time). It also adds a calibrated
health-indicator alarm, a fully nested battery cost analysis (convention C), and the matched fixed-time decomposition on
FD004. Every analysis is exploratory; the plans were hashed before the runs (`kam/PHASE2_PLAN.md`, `kam/PHASE3_4_PLAN.md`).
Scripts, run order, seeds and compute are in `kam/README.md`; frozen outputs are in `results/kam/` and `results/audit/`.

```bash
sh reproduce_revision5.sh               # minutes: unit tests, frozen outputs -> numbers, figures, LaTeX; must end with THIRD-REVISION REPRODUCTION CHECK PASSED
sh reproduce_revision5_experiments.sh   # about 6 CPU-hours: reruns every analysis of the third revision, compares with the frozen outputs, rebuilds
```

Run Python single-threaded (`export OMP_NUM_THREADS=1`) when several processes share two cores; the fitted trees are
identical to two-thread runs.

`paper5/build.sh` takes the figures of this revision from `out/paper5_figs/` (written by `python fig_rev5.py --frozen`,
which `reproduce_revision5.sh` runs first) and the other figures from `paper2/`–`paper4/`.

## Second revision (paper4)

The second revision adds three analyses (all post hoc; the manuscript labels them as exploratory or corrected):

| Script | What it does | Frozen output in `results/audit/` |
|---|---|---|
| `audit_fixed_matched.py` (+ `fixed_gbm.py`) | PHM08: fixed-time versus self-timed under matched training data. Every variant is fitted on all outer training engines and calibrated or tuned on inner out-of-fold predictions (cross-fitting); observation time, regressor, calibration and trigger are varied one at a time (Table 4). `fixed_gbm.py` is a verbatim copy of the fixed-time gradient-boosted model of `safe_methods.py` without the numba dependency. | `fixed_matched.json`, `fixed_matched_units.csv` |
| `audit_battery_physical.py cv\|lobo` | Battery cells with the task fixed in cycles (*H* = 60, window [−39, +6]) and fully nested preprocessing: blocks, z-scores and regressor rebuilt inside every inner training subset; κ by the protocol rule per subset, by inner cross-validation, or fixed at 2–6; capacity-trend baseline; cross-validation by cell and leave-one-batch-out (Table 8) | `battery_physical_cv.csv`, `battery_physical_lobo.csv` |
| `audit_battery_cost2.py` | Battery cost under cross-validation and with a batch held out, including the capacity trend (window-tuned, cost-tuned, one-standard-error rule); reproduces the earlier battery cost results unit by unit under cross-validation (Table 9) | `cost_battery2.csv` |

`audit_summarize2.py` adds key `rev4` to `paper3/numbers.json` and writes `paper4/numbers.json`; `fig_audit2.py` draws
Figs. 2, 8 and 9 of the second revision; `paper4/build.sh` writes the manuscript and supplement and runs 124 consistency checks.

```bash
sh reproduce_revision2.sh               # minutes: frozen outputs -> numbers, figures, LaTeX; must end with SECOND-REVISION REPRODUCTION CHECK PASSED
sh reproduce_revision2_experiments.sh   # several hours: reruns the three analyses, compares with results/audit (verify_audit.py), rebuilds
```

The scikit-learn version is pinned (`requirements.txt`), because other versions change the fitted trees.

## Revised manuscript (paper3)

The revision adds an audit of the evidence. It corrects a time-scale dependency: the battery and bearing block length κ
was computed from the lives of all units, including test units, and is now computed from training units only. It also
adds new analyses. Everything is in these scripts:

| Script | What it does | Frozen output in `results/audit/` |
|---|---|---|
| `audit_confirmations.py` | Battery and bearing analyses with training-only κ; κ sensitivity with the physical task fixed; battery capacity-threshold and capacity-trend baselines | `battery_corrected`, `battery_sensitivity`, `battery_baselines`, `bearing_corrected`, `bearing_sensitivity` |
| `audit_battery_controls.py` | Battery row of the timing-control table (constant estimate, health-indicator alarm) with training-only κ | `battery_controls` |
| `audit_cost.py` | Cost policies under identical information; shift study for assumption A1 of Proposition 1 | `cost_<dataset>`, `shift_<dataset>` |
| `audit_fixed_time.py` | Fixed-time versus self-timed decomposition on PHM08, from frozen predictions | `fixed_time.json` |

The cost policies are:

- window-tuned STW;
- cost-tuned STW (plain, with a one-standard-error rule, and with the 80th bootstrap percentile);
- a 10% quantile alarm;
- a health-indicator alarm;
- for the battery, a capacity-threshold alarm;
- age replacement.

`audit_summarize.py` collects the results into `paper3/numbers.json`. `fig_audit.py` draws the four new figures.
`paper3/build.sh` writes the manuscript and runs 109 consistency checks.

```bash
sh reproduce_revision.sh               # minutes: frozen audit outputs -> numbers, figures, LaTeX; must end with REVISION REPRODUCTION CHECK PASSED
sh reproduce_revision_experiments.sh   # several hours: reruns every audit from the data, compares with results/audit (verify_audit.py), rebuilds
```

The protocol versions of the battery and bearing analyses (κ = 3 and κ = 7 from all units) remain in `results/battery/` and
`results/bearing/`, and the revised manuscript reports them next to the corrected results.

## Version first prepared for submission (paper2)

Everything runs on a CPU. No GPU is needed.

## Quick start

```bash
python3.11 -m venv .venv && . .venv/bin/activate     # Python 3.11 (original runs) or 3.13 (re-verified)
pip install -r requirements.txt                      # exact versions; do not upgrade
python tools/check_data.py                           # inputs identical to those used for the paper
sh reproduce_numbers.sh                              # Level 1, a few minutes
```

The last line must end with `REPRODUCTION CHECK PASSED`.

## Three levels of reproduction

| Level | Command | Time (2 CPU cores) | What it does | What "identical" means |
|---|---|---|---|---|
| 1 | `sh reproduce_numbers.sh` | minutes | Rebuilds every number of the paper (`paper2/numbers.json`) and the LaTeX manuscript and supplement from the frozen experiment outputs in `results/` | `numbers.json`, `manuscript.tex` and `supplementary.tex` are identical to `paper2/reference/` |
| 2 | `sh reproduce_experiments.sh` | several hours | Reruns, from the data, every experiment that does not involve a neural network: main results, leakage checks, ablation, the three pre-specified confirmations, other windows and cost, theory check, repeated random test sets, timing controls, health-indicator alarm and cost-tuned policies. Then rebuilds the paper | Every rerun output is identical, value by value, to its frozen copy in `results/` (75 files), and the paper is identical to `paper2/reference/` |
| 3 | `sh run_all.sh` | about 12–14 hours | Everything, including the neural networks (LSTM, CNN, Transformer, TCN with GAN augmentation) and all figures | As level 2. Neural-network outputs (12 files) use fixed seeds, but JAX floating-point reductions can differ slightly between CPUs; `verify_reproduction.py` reports such differences without failing |

`python verify_reproduction.py` compares `out/` with `results/` at any time and lists each file as IDENTICAL, DIFFERENT or
not rerun.

**Exact versions matter.** The gradient-boosted models are bit-for-bit reproducible only with the versions in
`requirements.txt`. With scikit-learn 1.9.1, for example, the predictions change and the per-engine results no longer match.

## Requirements

- **Python:** 3.11 or 3.13, with the packages in `requirements.txt`.
- **Node.js:** 18 or later, to build the manuscript text from `numbers.json`. No npm packages are needed.
- **pdfLaTeX with latexmk:** TeX Live 2023 or later, only to compile the PDFs. Without it, the LaTeX sources are still written to `paper2/tex/`.
- **Keras backend:** for level 3, set `KERAS_BACKEND=jax`; `run_all.sh` does this.

## Where each result comes from

| Manuscript | Script(s) | Frozen output in `results/` |
|---|---|---|
| Table 1 (datasets) | `make_paper2_numbers.py` | computed from the data |
| Table 2, Fig. 4 (main first-warning results) | `eol_window2.py` | `window/first_warning_v2_*.csv` |
| Table 3, Supp. Table S6, Fig. S3 (constant-estimate control, health-indicator alarm) | `rev_experiments.py`, `rev_analyze.py` | `rev/*_window.csv`, `rev/tables/window_controls.csv` |
| Table 4, Fig. 5a (identical-protocol comparison, deep networks with the same inputs) | `safe_run.py`, `h2h.py`, `dl_warning.py` | `window/h2h_*.csv`, `window/dl_warning_*.csv` |
| Table 5, Fig. 5b (ablation, oracle-timed control) | `warn_ablation.py`, `oracle_check.py` | `window/ablation_warning_PHM08.*`, `window/oracle_timed_PHM08.csv` |
| Table 6, Fig. 6, Supp. Table S7 (maintenance cost of the alarms) | `rev_experiments.py`, `rev_analyze.py`, `fig_rev.py` | `rev/*_cost.csv`, `rev/tables/cost_*.csv` |
| Table 7, Fig. 7 (pre-specified confirmations) | `ncm_warning.py`, `battery_warning.py`, `battery_cost.py`, `bearing_warning.py` | `ncm/`, `battery/`, `bearing/` |
| Fig. 2 (fixed-time prediction) | `safe_run.py`, `safe_analyze.py`, `collect_base.py`, `bayes_phys.py`, `hybrid_tf.py`, `ablate_hybrid.py`, `tcn_gan.py`, `tcn_eval.py`, `ext_data.py`, `ext_stack.py` | `safe/`, `window/base_preds_PHM08.csv`, `window/tcn_*`, `window/*hybrid*` |
| Fig. 8 (check of Proposition 1) | `theory_check.py` | `theory/theory_check.csv` |
| Supp. S4 (leakage checks E1–E4) | `eol_leakage.py` | `window/eol_leakage_report.md` |
| Supp. S8–S9 (other windows, earlier cost analysis) | `multi_eval.py` | `multi/` |
| Supp. S10 (theory-guided shift STW-T) | `stwt.py`, `stwt_all.py` | `stwt/` |
| Supp. S11, Fig. S2 (thirty random 50-engine test sets) | `rep50.py`, `rep30.py`, `rep30_excel.py` | `rep30/`, `rep50/` |
| Computing time (Section 7.1) | `stw_timing.py` | `window/stw_timing.json` |

`make_paper2_numbers.py` and `make_rev_numbers.py` collect all results into `paper2/numbers.json`. `paper2/build.sh`
writes the manuscript from that file and runs 131 consistency checks; if any statement in the text disagrees with the
results, the build stops. Figure files map to the manuscript as follows:

| Manuscript | File in `paper2/img/` |
|---|---|
| Fig. 1 | `Fig1_STW_architecture.png` |
| Fig. 2 | `Fig2_fixed_time_ceiling.png` |
| Fig. 3 | `Fig4_level_tradeoff.png` |
| Fig. 4 | `Fig5_error_leadtime.png` |
| Fig. 5 | `Fig6_comparison_ablation.png` |
| Fig. 6 | `FigR2_cost_primary.png` |
| Fig. 7 | `Fig7_battery.png` |
| Fig. 8 | `Fig8_theory_check.png` |
| Fig. 9 | `Fig9_future_work.png` |
| Supp. Fig. S1 | `Fig3_example_engines.png` |
| Supp. Fig. S2 | `Fig_rep30.png` |
| Supp. Fig. S3 | `FigR1_timing_vs_estimate.png` |

## Data

All inputs are included, so no download is needed. `tools/check_data.py` verifies them against `tools/DATA_SHA256.json`.

| Folder | Content | Source |
|---|---|---|
| `a/train.txt` | PHM08 challenge training set (218 run-to-failure engines) | NASA Prognostics Center of Excellence data repository |
| `cmapss/` | C-MAPSS FD001–FD004 training, test and RUL files | NASA Prognostics Center of Excellence data repository |
| `ncm/ncmapss_cycle_summary.csv.gz` | N-CMAPSS, one row per engine and flight cycle (mean of the 1 Hz signals), built with `tools/ncmapss_colab_extract.py` | Arias Chao et al. (2021), NASA repository |
| `battery/severson_*` | Per-cycle summary and cell list of the 140 cell records, built with `tools/severson_colab_extract.py` | Severson et al. (2019), https://data.matr.io |
| `bearing/femto_snapshot_features.csv.gz` | Eight features per vibration snapshot of the 17 PRONOSTIA bearings | IEEE PHM 2012 challenge (Nectoux et al., 2012) |

If you replace `a/train.txt` or the C-MAPSS files with a fresh download from NASA, the checker accepts them when their
numerical content is identical, even if the whitespace differs. To rebuild the bearing features from the raw files, put the
`Learning_set` and `Full_Test_Set` folders of the PHM 2012 data in `bearing/femto_repo/` and run `bearing_extract.py`.
Check each provider's terms before redistributing the derived summaries.

## Pre-specified protocols

The three confirmations (N-CMAPSS, battery, bearings) were analysed only after their protocols had been written and hashed:
`ncm/WARNING_PROTOCOL.md`, `battery/BATTERY_PROTOCOL.md` and `bearing/BEARING_PROTOCOL.md`, with the hashes in the
`.sha256` files next to them.

- **N-CMAPSS and battery:** the hash covers the protocol text before the line `## Deviations`, so the deviations recorded later are outside the hashed part.
- **Bearings:** the hash covers the whole file.

The reproduction scripts check these hashes before running each confirmation.

## Repository layout

```
*.py                      experiments, analyses and figure scripts (top level, run from the repository root)
reproduce_numbers.sh      level 1
reproduce_experiments.sh  level 2
run_all.sh                level 3
verify_reproduction.py    exact comparison of out/ with results/ and of the rebuilt paper with paper2/reference/
a/ cmapss/ ncm/ battery/ bearing/   input data and the hashed protocols
results/                  frozen outputs of every experiment, as used in the paper
out/                      fresh outputs (created by the scripts; not tracked)
paper2/                   manuscript build: numbers.json, text sources (*.js), figures (img/), Elsevier CAS class
paper2/reference/         reference copies of numbers.json, manuscript.tex and supplementary.tex
tools/                    data checker, data hashes and the extraction scripts for N-CMAPSS and the battery data
```

## Notes

- **Reproducibility test:** see `REPRODUCIBILITY_TEST.md` for the clean-folder test of levels 1 and 2.

- **Determinism:** the gradient-boosted regressor (`HistGradientBoostingRegressor`, `random_state=0`) and every warning
  rule are deterministic. All selection of settings uses training units only (nested cross-validation by unit), and test
  units are scored once.
- **Interrupted runs:** `rev_experiments.py` saves each outer fold in `out/rev/ckpt/`, so an interrupted run resumes
  where it stopped.
- **Elsevier class files:** `paper2/cas-dc.cls` and `paper2/cas-common.sty` are the Elsevier CAS template files
  (version 2.3, LaTeX Project Public License).
