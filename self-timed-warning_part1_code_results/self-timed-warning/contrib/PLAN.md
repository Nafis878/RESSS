# Contribution plan: certified alarm thresholds (CAT), with a paired interval for the metric M

Plan fixed and hashed before any run on real or synthetic data (`contrib/PLAN.sha256`). Exploratory, plan hashed
before the run; this is not a formal preregistration. Later changes are recorded under "## Amendments" with reasons.
Phase 0 analysis (problem list, literature map, candidate scores, choice) is in the report to the authors; this file fixes
the method, grids, seeds, baselines, datasets, metrics, comparisons and verdict rules.

## Problem addressed
Plain minimisation of the empirical cost rate selects alarm thresholds at the edge of a failure cliff (paper6 §7.5:
>= 1 test failure in 24 of 80 fold-ratio cells for plain cost tuning, 4 for the 1-SE rule; PHM08, lead 10, rho = 50: 1.75 vs
1.10 times perfect foresight with 3 failures; their Fig. 9a on our data: training M 3.02% -> 129.9% one grid step later).
The safeguards in use (1-SE rule, p_thres = c_p/c_c, window tuning) are heuristics without a stated failure guarantee, a
point regressor gives no failure probability (P-cls and P-res give different verdicts), and the alarm is not designed for
the lead time or the decision grid (FD001: M 3.93% -> 8.08% when mapped to the grid).

## Method: certified alarm threshold (CAT)
- Signal: the recipe's capped GBM estimate, causally smoothed, x_t = EWM_m(yhat)_t (no shift; the threshold replaces it).
- Alarm for threshold tau, debounce k: t*(tau) = first t with x_{t-k+1..t} <= tau (`rev_experiments.first_idx`).
  Replacement at g(t*) = t* (decision grid dT = 1) or ceil(t*/dT) dT (grid); planned iff L - g(t*) > l (lead time l);
  unplanned failure otherwise, or if no alarm is raised.
- Lemma 1 (monotonicity): for fixed (cap, m, k), t*(tau) is non-increasing in tau, hence fail_i(tau) is non-increasing.
- Score: tau_i* = min{tau in T : fail_i(tau) = 0}, +inf if none (T = threshold grid TAUS = 1..60 cycles; battery 3..180
  cycles, step 3). Then fail_i(tau) = 1{tau < tau_i*}.
- Calibration: tau_hat_alpha = ceil((n+1)(1-alpha))-th smallest of {tau_i*} over the n calibration units. If the index
  exceeds n or the order statistic is +inf: "not certifiable" (reported), fall back to max T.
- Theorem 1 (to prove in Phase 1): if the n calibration scores and the test score are exchangeable,
  P(fail_{n+1}(tau_hat_alpha)) <= alpha, and > alpha - 1/(n+1) when the scores are a.s. distinct; for any l >= 0 and any
  grid dT. Corollary: expected cost per renewal <= 1 + (rho - 1) alpha; any data-dependent tau' >= tau_hat_alpha also has
  P(fail) <= alpha (pointwise monotonicity).
- Cost-aware CAT (CAT-c): tau' = argmin over tau >= tau_hat_alpha (tau in T) of the training (OOF) cost rate at (l, rho),
  or of the grid-mapped training cost for M. Ties: smallest tau.
- Theorem 2 (fragility as selection, to prove): plain minimisation over G settings that, for rho large enough, selects the
  setting-wise zero-training-failure threshold has P(test failure) <= min(1, G/(n+1)), and = 1/(n+1) for a single setting
  with distinct scores; quantified on the simulator. If the hoped-for statement fails, the correct weaker statement is
  reported instead.
- Calibration variants (exchangeability):
  - CAT-CF (primary, practical): scores tau_i* from inner five-fold OOF predictions of all outer training units; test
    alarms from the model refitted on all outer training units. Guarantee approximate (model refit); checked empirically.
  - CAT-SPLIT (exact): final regressor fitted on a random 50% of the outer training units (seed 500 + fold); scores from
    the other 50% under that regressor.
  - CAT-KMIN (exact): five inner models, each calibrated on its own held-out inner fold at level alpha; the test alarm is
    the earliest of the five alarms (a failure needs all five to fail, so P(fail) <= alpha).
- Setting (cap, m, k): taken from the existing window-tuned selection at H = 20 of the fold (no new search). Ablations:
  setting chosen by plain training cost; Bonferroni over the G = 27 settings (level alpha/G).
- Clarification of the validity test: validity is tested on the bare certified threshold tau_hat_alpha of CAT-CF, which
  depends on (l, dT) but not on rho; CAT-c failure rates are reported per cell, descriptively (bounded by Theorem 1).

## Baselines (same splits, information, lead times and cost ratios)
Window-tuned STW; cost-tuned STW plain, 1-SE and 80th percentile (`audit_cost.select`); quantile alarm (1-SE);
health-indicator alarm (cost-tuned); optimal age replacement; per-time-step conformal lower bound (closest PHM practice:
replace at the first cycle at which yhat_t - q_{1-alpha}(OOF residuals yhat - r over all cycles of the training units) <= l).
Under M: their policy 1 (P-res, P-cls; p = c_p/c_c and optimised), policy 3, window-tuned and 1-SE STW (mapped), as in
`kam/kam_fd001.py`.

## Datasets, protocol, seeds
PHM08, FD001-FD004, N-CMAPSS (cost only; no M, as in paper6), battery convention C (cross-validation by cell and the three
held-out batches), bearings (validity of the guarantee only, and window counts). Outer folds `safe_common.outer_folds`
(seed 2026); inner folds seed 100 + fold (battery as `audit_battery_cost_nested.py`); split seed 500 + fold; paired
bootstrap 2,000 resamples, seed 2027; GBMs random_state 0; simulator seeds 2026 (sigma = 0.4), 2027 (sigma = 0.15) and
9000 + r for Monte-Carlo replicate r.
alpha in {0.01, 0.02, 0.05, 0.10}; primary alpha = 0.05. Lead times l in {0, 5, 10, 15} cycles (battery {0, 15, 30, 45}
cycles); cost ratios rho in {5, 10, 20, 50}. Under M: dT = 10, l = 0, c_p/c_c in {0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8},
primary 0.1.

## Phase 1: synthetic check with ground truth
Simulator of Kamariotis et al. (`kam/kam_simulator.py`) and a monotone-degradation synthetic model; n in
{20, 50, 100, 200}; alpha as above; 20,000 replicates per cell. Realised P(fail) of CAT-SPLIT and CAT-KMIN must lie in
[alpha - 1/(n+1) - 3 MCSE, alpha + 3 MCSE] (lower bound only where scores are a.s. distinct). Theorem 2: realised failure
probability of plain minimisation over G in {1, 4, 12, 36} settings against the bound.
Unit tests (`contrib/test_cat.py`): Lemma 1 on random series; equivalence fail_i(tau) = 1{tau < tau_i*}; tau_hat on hand
examples; grid and lead mapping identical to `kam_fd001.grid_cost` and `rev_experiments.cost_of`.

## Metrics
(1) Validity: pooled test unplanned-failure rate per dataset and lead time, exact one-sided binomial test against alpha.
(2) Fragility: number of fold-cell combinations (5 folds x 16 cells) with >= 1 test failure.
(3) Cost: rate relative to perfect foresight; paired bootstrap ratio CAT-c / X per cell.
(4) M and paired-bootstrap Delta M on FD001-FD004.
(5) Notice: median true remaining life at the alarm.

## Primary comparison and verdict rules
- Validity holds on a dataset if, at alpha = 0.05 for CAT-CF, the one-sided exact binomial test of "failure rate <= 0.05"
  is not rejected at level 0.05 for any lead time; otherwise validity fails there (reported as a loss).
- Fragility: CAT-c (alpha = 0.05) is less fragile than X if its count of fold-cell combinations with >= 1 test failure is
  lower than X's on >= 4 of the 6 engine datasets (PHM08, FD001-FD004, N-CMAPSS); X in {plain cost-tuned STW, 1-SE STW}.
- Cost: per cell, "win" if the paired 95% bootstrap interval of the cost-rate ratio CAT-c / X lies below 1, "loss" if above
  1. CAT-c beats X on a dataset if wins >= 8 of 16 and losses = 0; loses if losses >= 8 and wins = 0; otherwise mixed.
  X in {window-tuned STW (primary), plain cost-tuned STW, 1-SE STW, age replacement}.
- Under M (c_p/c_c = 0.1, five-fold): "beats" only if the paired-bootstrap interval of Delta M excludes 0, per dataset,
  against policy 1 P-res optimised (primary) and window-tuned STW (mapped).
- Primary claim test = validity on the six engine datasets + fragility against plain cost tuning + cost against window
  tuning.

## What will be claimed
- Win (validity on >= 5 of 6 engine datasets, less fragile than plain cost tuning, and cost not "loses" against window
  tuning on any engine dataset): "a distribution-free certified threshold controls the unplanned-failure rate at the stated
  level and removes most of the fragility of cost tuning, at a cost comparable to window tuning."
- Mixed: each component is reported separately; the guarantee is claimed only where validity holds; the fragility theory
  only as far as the simulator confirms it.
- Loss (validity fails on >= 2 engine datasets, or cost loses to window tuning on >= 2): reported in the abstract and the
  conclusion as a negative result (certification at alpha >= 1/(n+1) is too coarse, or exchangeability fails); Theorem 1 and
  the simulator check remain the contribution. Battery held-out batch: a violation of the guarantee is expected and will be
  reported as evidence that exchangeability, not the method, limits transfer.
- No further tuning after test results are seen.

## Compute (2 cores, OMP_NUM_THREADS=1, at most two processes)
Phase 1 synthetic: about 20 min. Phase 2 (FD001-FD004 cost and M, reusing the `kam_fd001.run_split` path): about 2.2
CPU-hours, to be confirmed with the authors before running. Phase 3 (PHM08, N-CMAPSS, battery C, bearings, ablations
including CAT-SPLIT and CAT-KMIN refits): about 2.5 CPU-hours, to be confirmed before running.

## Secondary (supplement only): paired interval for M
M = R/R_p - 1 with R = sum C / sum T and R_p the grid-perfect rate on the same units. Influence function
psi_i = [ (C_i - R T_i)/mean(T) - (R/R_p) (C_p,i - R_p T_p,i)/mean(T_p) ] / R_p; Var(M_hat) ~ sum psi_i^2 / n^2 (zero for the
perfect policy). Coverage of 95% intervals on the simulator (n = 20 and 100; 5,000 replicates; truth from n = 200,000) for
the interval of their Eq. 7, the paired influence interval and the paired bootstrap.

## Leakage checks
E1-E4 of `eol_leakage.py` / `kam/kam_fd001.py leak` rerun on the CAT code path (disjoint units, causality, permuted-life
negative control, exact reproduction of a refitted fold). Any failure stops the work.

## Amendments

### Amendment 1 (2026-10-07, after the first real-data run on FD001, before any CAT result was looked at)
Reason. The frozen results were produced on Linux (Intel Xeon). The only machine available for this analysis is Windows 11,
AMD Ryzen 7 5700G, Python 3.12.4 with the pinned numpy 2.4.4, pandas 3.0.2, scikit-learn 1.8.0 and scipy 1.17.1
(single-threaded). On it, refitting the unchanged gradient-boosted models does not reproduce the frozen predictions bit for
bit: the unmodified `eol_window2.py FD001` selects in fold 1 the setting (cap 90, span 1, debounce 5, shift -4.5) where the
frozen run selected (cap 90, span 1, debounce 3, shift -2.5), exactly as the CAT code path does, so the difference comes from
the platform, not from the new code. The level-1 reproduction (frozen outputs -> numbers -> manuscript) is unaffected. The
reproduction checks R0/R1 of `cat_run.py`, which compared the CAT code path with the frozen rows, therefore stopped the run
(stop rule), and CAT cannot be paired unit by unit with frozen baseline rows.
Change. Every baseline used in a CAT comparison is recomputed in the same run, from the same predictions as CAT, with code
copied from `audit_cost.py` (window-tuned, plain, 1-SE and 80th-percentile cost-tuned STW, quantile alarm plain and 1-SE,
health-indicator alarm, age replacement, perfect foresight), from `kam/kam_fd001.py` (under M: mapped window-tuned,
plain and 1-SE STW, health-indicator alarm, policy 1 P-res and P-cls with p = c_p/c_c and optimised, policy 3, age
replacement on the grid) and, for the batteries, by running `audit_battery_cost_nested.run_split` itself. The checks R0/R1
against frozen rows are replaced by: (i) the platform check (the unmodified `eol_window2.py FD001` rerun on this machine,
compared with the CAT code path's window-tuned first warnings at H = 20: must be identical); (ii) equivalence checks
that the copied baseline code gives the same decisions as the original scripts run on this machine (`audit_cost.run`
restricted to fold 1 of FD001; `kam_fd001.run_split` on fold 1 of FD001; for the batteries the rows of
`audit_battery_cost_nested.run_split` are used directly and the CAT run must reproduce its window-tuned and cost-tuned
policies). Method, grids, seeds, metrics, verdict rules and claims are unchanged. The baseline numbers in the CAT
comparisons differ from the frozen numbers of paper6 by this platform effect; the paper reports both and says why.
