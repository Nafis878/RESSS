# Phase 2 analysis plan: my alarm policies under the conventions of Kamariotis et al. (2024), FD001

**Status:** exploratory, post hoc. The plan is fixed and hashed before any Phase 2 run. Any amendment is appended below with a date and a new hash, before the run it affects.

**Metric:** `kam/kam_metric.py`, a re-implementation of their Eqs. (2)–(9), replacement-only setting, checked by `kam/test_kam_metric.py` and `kam/kam_simulator.py`.

## Data and conventions

- **Data:** C-MAPSS FD001 training set, 100 run-to-failure units. Life *L* = last cycle; failure time *T*_F = *L*; true RUL *r*_t = *L* − *t*.
- **Decision points:** *t*_k = 10*k* (ΔT = 10). A preventive replacement decided at *t*_k happens at *t*_k, with no lag. **ℓ = 0 only.** My replacement lag ℓ is not used here.
- **Costs:** *c*_p = 1, *c*_c = *c*_p / *q* for *q* = *c*_p/*c*_c ∈ {0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8}. This grid was chosen to span the ranges shown in their figures; it is not stated in their text.
- **Reference policy:** the grid-perfect policy (last grid point strictly before *T*_F). M̂ is computed against it. The 1-cycle perfect policy (*L* − 1) is also reported, to give the reference-grid effect for FD001.
- **Mapping of my alarms:** an alarm raised at cycle *t*\* acts at the first grid point at or after it, ⌈*t*\*/10⌉·10. If that point is at or after *T*_F, the unit counts as failed, at cost *c*_c and life-cycle *T*_F.
- **No clipping of M:** M̂ < 0 is recorded and reported (`kam_metric.VIOLATIONS`).
- **Unmapped 1-cycle results** of my policies are kept for continuity and labelled "unmapped".

## Protocols

- **(B) primary:** five-fold CV by unit over all 100 units, using the existing FD001 outer folds (seed 2026) and inner folds (seed 100 + fold). Each unit is tested once. Inferences are drawn from (B).
- **(A) spread:** 30 random 80/20 splits. Split *s* = 1…30 uses permutation `np.random.default_rng(31000 + s)`; the first 20 units are the test set. Inner folds use seed 3100 + *s*. (A) shows the spread of single 20-unit evaluations and is **not used to claim that one policy beats another.**
- **Selection:** every setting is selected on the training units of each split, using inner five-fold out-of-fold (OOF) predictions. Test units are scored once.

## Prognostic models (fixed, not tuned)

- **Regressor:** the recipe's regressor, unchanged. Features: regime-normalised causal features as in `eol_window2.py`. HistGradientBoosting with absolute loss, 500 iterations, learning rate 0.05, 31 leaves, minimum 40 samples per leaf, seed 0. Target min(*r*, *c*).
- **Probability of failure within the next decision interval, Pr(RUL ≤ 10)** (training units only), two variants:
  - **(P-cls) classifier.**
    - HistGradientBoostingClassifier (log loss, same hyperparameters, seed 0) on the same features.
    - Label 1{*r*_t ≤ 10} on every cycle of the training units.
    - Calibration: isotonic regression (increasing, clipped to [0, 1]) fitted on the inner-OOF probabilities of the training units, then applied to the probabilities of the final classifier trained on all training units.
  - **(P-res) residual distribution.**
    - Recipe regressor with cap *c* = 60, fixed in advance and not selected.
    - The OOF predictions ŷ of the training units are split into 20 equal-count bins.
    - The predictive distribution of RUL for an estimate ŷ is the empirical distribution of the true *r* of the OOF cycles in ŷ's bin. Pr(RUL ≤ 10) is the share with *r* ≤ 10.
- **Probability inputs:** the unsmoothed model output at *t*_k.

## Policies (each per *q*; settings from training OOF, under the grid-mapped cost)

1. **STW window-tuned.**
   - Cap, span, debounce and shift are selected per *H* by the window count (recipe unchanged, window [−13, +2]).
   - *H* ∈ {10, 15, 20, 30, 40} is chosen by the lowest grid-mapped training cost rate.
2. **STW cost-tuned, plain and 1-SE.**
   - Cap, span, debounce and threshold τ ∈ {1…60} (2,160 settings) are chosen by the lowest grid-mapped training cost rate.
   - The 1-SE rule is as in `audit_cost.py`: 200 bootstrap resamples of training units, seed 2026 + split index.
3. **Their policy 1 on my models**, for each probability variant (P-cls, P-res):
   - (i) *p*_thres = *q*;
   - (ii) *p*_thres optimised on training OOF probabilities. The search grid has 400 log-spaced points in [10⁻⁴, 1] plus 0.001…1 in steps of 0.001. The criterion is the lowest training cost rate. Ties are broken by taking the middle grid point of the minimising set.
4. **Their policy 3 (Eq. 14)** with the P-res predictive distribution.
   - *E*[*C*]/*E*[*T*] uses their option 1: the optimal age-replacement cost rate on the empirical training lives.
   - *T*_R is minimised over integer *x* = *T*_R − *t*_k ≥ 0. Replace at *t*_k if *x*\* ≤ 10.
   - Not run with P-cls: the classifier gives one CDF value, not a distribution.
5. **Baselines.**
   - Optimal age replacement: age restricted to multiples of 10, chosen on training lives.
   - Health-indicator alarm, cost-tuned under the grid-mapped cost (as `HI_cost` in `audit_cost.py`).
   - Run-to-failure.

## Outputs per policy and *q*

- M̂;
- the 95% interval by their Eqs. (3)/(7);
- the 95% paired bootstrap interval (2,000 resamples of test units, seed 2027);
- the number of failures;
- the mean life-cycle.

## Paired comparisons

- **Policies compared:** STW window-tuned, STW cost-tuned (plain and 1-SE), each against policy 1 optimised (P-cls and P-res), policy 3 (P-res) and age replacement.
- **Measure:** the difference in M̂, with a paired bootstrap over test units.
- **Definition of "beats":** a policy *beats* another only if, in protocol (B), the paired 95% bootstrap interval of the M̂ difference excludes 0. Otherwise the result is "unclear".
- **Protocol (A):** median difference, and the number of the 30 splits whose interval lies below or above 0. This is descriptive only.
- **Multiplicity:** no adjustment across the 7 cost ratios and the pairs. The cells share units and are correlated, so counts are descriptive.

## Leakage checks on the new code paths

- **(E1)** Test units are disjoint from training and inner units in every split.
- **(E2)** Causality: classifier and regressor predictions from truncated histories equal those from full histories, for 15 test units × 6 cut-offs.
- **(E3)** Negative control: with lives permuted across training units, policy 1 (P-cls, optimised) in fold 1 must lose its advantage.
- **(E4)** Rerunning fold 1 reproduces its decisions exactly.

## Compute estimate

About 2 min per split on 2 cores: (B) about 10 min, (A) about 60–70 min. **This exceeds 1 h, so approval is requested before the run.**

---

## Amendment 1 (2026-10-06, before any Phase 2 run)

The original plan above was hashed at 2026-10-06T06:33:23Z (SHA-256 988737aaeb9d6b6f80c0b2cbb70846396f6cb75a1a29f495922b4f7a3332e5b7). This amendment was agreed after reviewing the Phase 1 report and is hashed together with the original text before any run.

### A1. Regressor used for P-res

- **Not the recipe's regressor.** The P-res regressor has the same features and hyperparameters as the recipe's regressor, but a **fixed cap of 60**. The recipe's own regressor selects its cap from {40, 60, 90} per split by the window count.
- **Truncation.** A capped regressor only says "far from failure" above its cap. In P-res, a true RUL above the cap is set to the cap, so the upper tail becomes a single atom at the cap. Policy 3 therefore works with a **truncated** RUL distribution:
  - Pr(RUL > *x*) is exact for *x* < cap;
  - E[(RUL − *x*)⁺] is understated, so the opportunity-loss term of Eq. (14) is too small;
  - *T*_R is minimised over integer *x* = 0…cap.
- **Sensitivity run.** A cap-125 version of P-res (same construction, tail atom at 125) is run for policy 3 only and labelled as sensitivity. If it changes the ranking of policy 3 against policy 1 at *c*_p/*c*_c = 0.1, that goes in the paper.

### A2. Bins

- **Training data only.** Bin edges and the per-bin empirical RUL distributions are computed from inner out-of-fold predictions of the training units only. Edges are the 20 equal-count quantiles of the OOF estimates.
- **Minimum count.** Each bin must hold at least 200 OOF rows; a smaller bin is merged with its neighbour towards the bulk until it does. Rows within a unit are autocorrelated, so the effective sample size is nearer the number of units.
  - For the lowest three bins, the number of rows and the number of distinct units contributing are reported for every split.
- **Monotonicity.**
  - Pr(RUL ≤ 10) per bin is made non-increasing in the estimate by count-weighted isotonic regression (PAVA), applied to the bins ordered by estimate.
  - The calibrated P-cls probability is non-decreasing in the raw classifier probability, by isotonic calibration.
  - Policy 3 uses the per-bin distributions as estimated.

### A3. Threshold optimisation of policy 1: two tie rules

The minimising set is the set of grid thresholds attaining the minimum training cost rate (relative tolerance 1e-12). Both rules are computed on the same grid:

- **mid (primary):** the middle element, by grid index, of the minimising set;
- **max (secondary):** the largest element of the minimising set, which mirrors their Fig. 9a (p* = 0.85 at the edge of the zero-failure plateau).

Both rules are reported side by side in Phase 2 and Phase 3.

### A4. Confirmations

- **Re-selection.** Window-tuned STW (*H*) and cost-tuned STW, HI and age policies (settings and thresholds) are re-selected on training units under the **grid-mapped** cost, not the 1-cycle objective.
  - The 1-SE rule's "remaining life at the alarm" is the remaining life at the grid point where the replacement happens (0 for a failure).
- **Failures.** An alarm mapped to a grid point at or beyond the failure time is a failure at cost *c*_c with life-cycle *T*_F.
- **Primary ratio.** The primary cost ratio is ***c*_p/*c*_c = 0.1**, the only value their text reports a number for. The other six ratios are descriptive, and counts of cells whose interval excludes 0 are descriptive.
- **Protocol (A).**
  - Report the distribution of M differences across the 30 splits: median, interquartile range, minimum–maximum, and the share of splits favouring each policy.
  - Also report the number of splits whose own paired interval lies below or above 0.
  - Never pool the splits into one interval: they overlap and are not independent.
- **"Beats"** is defined on protocol (B) only, by the paired bootstrap, as stated above.
- **Unmapped versions.** STW policies selected under the 1-cycle objective and evaluated off-grid are reported once more, labelled "unmapped 1-cycle".

### A5. Stop rules

The run stops if a unit test fails, if a leakage check E1–E4 fails, or if any grid-mapped policy has M̂ < 0. Results are written to disk after each stage: (B) first, then (A).

### A6. Scope

Phase 2 is FD001 only with ΔT = 10. ΔT = 10 is not carried over to other datasets (e.g. N-CMAPSS, where 10 cycles are 10–20% of a life) without stating it.
