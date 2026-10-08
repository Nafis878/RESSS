# Unit-level calibration of end-of-life alarms: contribution assessment

Completed 08 October 2026 (Asia/Dhaka).

## Answer to the novelty question

**No confirmed novel methodological contribution is established by the current package.** There is a defensible empirical contribution and a potentially useful maintenance-specific trajectory formulation. Those should be claimed precisely. A new name, a new dataset comparison, or a passing synthetic conformal-rank check does not establish a new general method.

The pre-specified empirical verdict is **win**. The 5% bare-CAT screening did not reject on 6/6 engine datasets at every lead; it rejected on 0/6. CAT-c had fewer failure-containing cells than plain cost tuning on 5/6 datasets and than 1-SE tuning on 0/6.

The empirical plan verdict and the novelty verdict answer different questions. An empirical win would not make established conformal mathematics new; an empirical loss can still support a useful negative-result paper.

## Completed phases

| Phase | Completion and evidence |
| --- | --- |
| 0: contribution selection and prior-work check | `docs_contrib/LITERATURE_AUDIT.md`; primary papers/publisher pages checked on 7 October 2026. |
| 1: theory, unit tests and synthetic checks | Eight CAT tests passed. Saved simulation outputs/check logs retained and audited: 208/208 certifiable validity cells within the specified MC tolerance; 56/56 high-cost selection cells within the bound. Added explicit KMIN check: 156/156 cells at 20000 replicates each. |
| 2: FD001–FD004 cost and M | All four datasets, five outer folds, four alphas, 16 cost cells, seven M ratios; SPLIT/KMIN, per-time-step and setting-selection ablations present. |
| 3: additional domains | PHM08 and N-CMAPSS cost; fully nested battery cell CV and three held-out batches; five-fold bearing analysis. |
| Integrity and interpretation | Hashed plan and all 21 input files verified; FD001 same-platform original-script equivalence and E1–E4 checks passed; battery/bearing original-script checks passed; complete paired outputs audited. |
| Synthesis | Summary JSON, readable tables, figure, this report, theory corrections and a provenance manifest. Earlier paper6 manuscript and supplement regenerated identically to their reference text; paper5 numbers identical after normalizing line endings. |

Phase 1 simulations were already complete in the supplied package; their full saved outputs and checks were used. The remaining real-data analyses were completed using the restored pinned environment. No primary grids, seeds, thresholds or verdict rules were tuned after test results.

## Problem and trajectory score

A causal regressor supplies estimates at cycles before failure. For a threshold tau, the policy raises its first alarm after k consecutive smoothed estimates are at most tau. Let g(t) be the next allowed decision time and ell the maintenance lead time. Replacement is planned only when g(t)+ell is strictly before failure. Raising tau can only move the alarm earlier. This monotonicity permits a unit-level critical score: the lowest threshold that reaches an admissible alarm time. Equivalently, it is the debounced running minimum evaluated at the latest admissible alarm time, rounded upward on a finite threshold grid.

For a fixed prediction model, preprocessing rule and alarm setting, failure at a finite threshold is exactly the event that the new trajectory's critical score exceeds that threshold. Applying the standard conformal order statistic, rank ceil((n+1)(1-alpha)), to n exchangeable calibration scores controls marginal failure risk under the theorem's feasibility assumptions. Increasing that threshold preserves the binary-risk bound, so cost can be minimized over larger thresholds. This controls cost per renewal in expectation; it does not by itself bound the cost rate, because useful cycle length also changes.

The main practical variant pools inner OOF scores and deploys a refitted model. That is not an exact split-conformal construction. The implemented SPLIT and KMIN variants use calibration-dependent setting selection and are also empirical variants. The corrected theorem applies to an independently fixed rule, not automatically to these runs. Infeasible levels, infinite critical scores and maximum-grid fallbacks carry no general deployment certificate. See `docs_contrib/theory.md` and `EXECUTION_NOTES.md`.

## Evaluation and comparisons

All real-data analyses are exploratory, with a plan hashed before the original run, not a formal preregistration. Outer folds use seed 2026; inner engine folds use 100+fold. Models are capped absolute-error gradient-boosted regressors with 500 iterations and causal regime-normalized features. Settings are chosen on training units. Costs use planned replacement cost 1, failure cost rho in {5,10,20,50}, engine lead times {0,5,10,15}, and corresponding battery leads in cycles. Primary alpha is 0.05. M uses a 10-cycle decision grid, zero lead and primary preventive/corrective cost ratio 0.1.

Every comparator is recomputed on the same Windows/Python platform as CAT, following Amendment 1. Frozen Linux baseline rows are not combined with the new fits. Three principal safeguards are compared: window tuning, the 1-SE cost rule, and trajectory calibration. Age replacement, health-indicator and quantile alarms, probability policies, per-time-step residual calibration and the remaining planned variants are in the machine-readable results.

### Engine risk screening at alpha = 0.05

| Dataset | Lead | Units | Failures | Rate % | Screen p | Finite order statistic % | Screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PHM08 | 0 | 218 | 6 | 2.75 | 0.9636 | 100.0 | not rejected |
| PHM08 | 5 | 218 | 8 | 3.67 | 0.8569 | 100.0 | not rejected |
| PHM08 | 10 | 218 | 9 | 4.13 | 0.7658 | 100.0 | not rejected |
| PHM08 | 15 | 218 | 7 | 3.21 | 0.9225 | 100.0 | not rejected |
| FD001 | 0 | 100 | 2 | 2.0 | 0.9629 | 100.0 | not rejected |
| FD001 | 5 | 100 | 4 | 4.0 | 0.7422 | 100.0 | not rejected |
| FD001 | 10 | 100 | 2 | 2.0 | 0.9629 | 100.0 | not rejected |
| FD001 | 15 | 100 | 1 | 1.0 | 0.9941 | 100.0 | not rejected |
| FD002 | 0 | 260 | 12 | 4.62 | 0.6521 | 100.0 | not rejected |
| FD002 | 5 | 260 | 4 | 1.54 | 0.9991 | 100.0 | not rejected |
| FD002 | 10 | 260 | 11 | 4.23 | 0.7549 | 100.0 | not rejected |
| FD002 | 15 | 260 | 13 | 5.0 | 0.5397 | 100.0 | not rejected |
| FD003 | 0 | 100 | 3 | 3.0 | 0.8817 | 100.0 | not rejected |
| FD003 | 5 | 100 | 5 | 5.0 | 0.564 | 100.0 | not rejected |
| FD003 | 10 | 100 | 2 | 2.0 | 0.9629 | 100.0 | not rejected |
| FD003 | 15 | 100 | 2 | 2.0 | 0.9629 | 100.0 | not rejected |
| FD004 | 0 | 249 | 8 | 3.21 | 0.9333 | 100.0 | not rejected |
| FD004 | 5 | 249 | 10 | 4.02 | 0.8016 | 100.0 | not rejected |
| FD004 | 10 | 249 | 9 | 3.61 | 0.8786 | 100.0 | not rejected |
| FD004 | 15 | 249 | 9 | 3.61 | 0.8786 | 100.0 | not rejected |
| NCMAPSS6 | 0 | 99 | 3 | 3.03 | 0.8775 | 100.0 | not rejected |
| NCMAPSS6 | 5 | 99 | 3 | 3.03 | 0.8775 | 100.0 | not rejected |
| NCMAPSS6 | 10 | 99 | 3 | 3.03 | 0.8775 | 100.0 | not rejected |
| NCMAPSS6 | 15 | 99 | 1 | 1.01 | 0.9938 | 100.0 | not rejected |

These are the pre-specified one-sided binomial screens. “Not rejected” means insufficient evidence against the null in that screen; it does not prove the failure risk is at most 5%. Overlapping CV fits induce dependence, so pooled binomial p-values and intervals lack the usual independent-Bernoulli justification. A finite order statistic is an implementation flag, not proof that exchangeability holds.

### Calibration feasibility of the planned variants

| Dataset | CF calibration n | CF finite | SPLIT finite | KMIN finite | Bonferroni finite |
| --- | --- | --- | --- | --- | --- |
| PHM08 | 174–175 | 20/20 | 20/20 | 20/20 | 0/20 |
| FD001 | 80–80 | 20/20 | 20/20 | 0/20 | 0/20 |
| FD002 | 208–208 | 20/20 | 20/20 | 20/20 | 0/20 |
| FD003 | 80–80 | 20/20 | 20/20 | 0/20 | 0/20 |
| FD004 | 199–200 | 20/20 | 20/20 | 20/20 | 0/20 |
| NCMAPSS6 | 79–80 | 20/20 | 20/20 | 0/20 | 0/20 |

Counts are over the five folds and four lead times at alpha 0.05, before cost-ratio selection. KMIN requires enough calibration units in every member under the implementation's conservative flag. A maximum-threshold fallback may show zero failures while replacing very early; it is not a successful risk certificate. SPLIT/KMIN validity and their cost comparisons are retained in the full JSON. These comparisons and the original setting-selection/Bonferroni ablations do not change the primary verdict rules.

### Failure-containing fold/cost cells

| Dataset | Fold/cost cells | CAT-c | Plain cost | 1-SE | Window |
| --- | --- | --- | --- | --- | --- |
| PHM08 | 80 | 20 | 40 | 8 | 7 |
| FD001 | 80 | 4 | 12 | 0 | 1 |
| FD002 | 80 | 15 | 24 | 8 | 6 |
| FD003 | 80 | 16 | 12 | 0 | 4 |
| FD004 | 80 | 13 | 25 | 12 | 13 |
| NCMAPSS6 | 80 | 11 | 16 | 9 | 21 |

Each dataset has five folds times sixteen lead/cost combinations. Counts compare robustness over this finite grid, not independent replications. The pre-specified criterion requires fewer cells on at least four of the six engine datasets.

### Paired cost comparisons

| Dataset | Versus window | Versus plain | Versus 1-SE | Versus age |
| --- | --- | --- | --- | --- |
| PHM08 | mixed (0 wins, 1 losses) | mixed (0 wins, 0 losses) | loses (0 wins, 8 losses) | beats (14 wins, 0 losses) |
| FD001 | mixed (10 wins, 1 losses) | mixed (0 wins, 4 losses) | mixed (5 wins, 0 losses) | beats (14 wins, 0 losses) |
| FD002 | mixed (6 wins, 0 losses) | mixed (0 wins, 0 losses) | mixed (4 wins, 3 losses) | beats (13 wins, 0 losses) |
| FD003 | beats (8 wins, 0 losses) | loses (0 wins, 16 losses) | mixed (4 wins, 0 losses) | beats (12 wins, 0 losses) |
| FD004 | beats (8 wins, 0 losses) | mixed (0 wins, 0 losses) | mixed (2 wins, 3 losses) | beats (15 wins, 0 losses) |
| NCMAPSS6 | beats (9 wins, 0 losses) | mixed (0 wins, 6 losses) | mixed (2 wins, 3 losses) | beats (10 wins, 0 losses) |

Per cell, a win/loss requires the paired 95% bootstrap interval for CAT-c/comparator cost-rate ratio to lie wholly below/above 1. “Beats” requires at least eight wins and no losses; “loses” requires at least eight losses and no wins; other patterns are mixed. All 16 individual ratios and intervals are in `contrib_numbers.json`. The bootstrap conditions on the realized fitted predictions, does not include training-set uncertainty, and has no across-cell multiplicity adjustment. Sparse failures can make percentile intervals unreliable, as the synthetic coverage study illustrates.

### Metric M at the primary ratio

| Dataset | Comparator | CAT-c M % | Comparator M % | Difference points | Paired 95% interval | Plan verdict |
| --- | --- | --- | --- | --- | --- | --- |
| FD001 | P1_res_opt_mid | 5.8575 | 5.5789 | 0.2786 | [-0.3903, 0.9448] | unclear |
| FD001 | STW_window | 5.8575 | 8.4911 | -2.6336 | [-3.3373, -1.948] | CAT |
| FD002 | P1_res_opt_mid | 7.922 | 5.6554 | 2.2666 | [-1.5709, 9.6873] | unclear |
| FD002 | STW_window | 7.922 | 4.8507 | 3.0713 | [-0.6822, 10.3943] | unclear |
| FD003 | P1_res_opt_mid | 13.6111 | 7.9323 | 5.6788 | [-4.1832, 24.6006] | unclear |
| FD003 | STW_window | 13.6111 | 4.7578 | 8.8533 | [-0.6643, 27.5676] | unclear |
| FD004 | P1_res_opt_mid | 7.102 | 11.2518 | -4.1498 | [-12.0954, -0.0388] | CAT |
| FD004 | STW_window | 7.102 | 8.4405 | -1.3385 | [-1.85, -0.8637] | CAT |

Negative differences favor CAT-c. Grid-perfect reference units are paired with each policy. These numbers belong to the new platform comparison and should not silently replace the historical values in paper6.

## Battery transfer and bearing sample size

| Battery analysis | Lead cycles | Units | Failures | Rate % | Finite order statistic % | Screen |
| --- | --- | --- | --- | --- | --- | --- |
| cv | 0 | 123 | 2 | 1.63 | 100.0 | not rejected |
| cv | 15 | 123 | 4 | 3.25 | 100.0 | not rejected |
| cv | 30 | 123 | 1 | 0.81 | 100.0 | not rejected |
| cv | 45 | 123 | 1 | 0.81 | 100.0 | not rejected |
| lobo | 0 | 123 | 36 | 29.27 | 100.0 | rejected |
| lobo | 15 | 123 | 31 | 25.2 | 100.0 | rejected |
| lobo | 30 | 123 | 42 | 34.15 | 100.0 | rejected |
| lobo | 45 | 123 | 37 | 30.08 | 100.0 | rejected |

Held-out battery batches probe distribution shift. The exchangeability assumption is not justified across manufacturing/test batches, regardless of whether a screen rejects. Fully nested preprocessing reconstructs each training subset's blocks and normalization; it avoids borrowing a held-out cell's life to set the time scale.

| Bearing alpha | Units | Failures | Rate % | Finite-statistic folds |
| --- | --- | --- | --- | --- |
| 0.01 | 17 | 0 | 0.0 | 0/5 |
| 0.02 | 17 | 0 | 0.0 | 0/5 |
| 0.05 | 17 | 0 | 0.0 | 0/5 |
| 0.1 | 17 | 0 | 0.0 | 5/5 |

With only 13–14 calibration bearings per outer fold, alpha 0.05 cannot be certified by the finite rank: at least 19 calibration units are needed. Fallback outcomes are therefore not evidence for a 5% guarantee. The bearing experiment is a small-sample limitation, not a confirmatory safety study.

## Secondary interval result

The paired influence interval for M keeps covariance with the grid-perfect reference, using standard ratio-estimator linearization. Its width is zero for the perfect policy, whose metric is identically zero. It did not solve rare-failure uncertainty. Across the saved probability-policy cases:

| Interval | Minimum coverage % | Maximum coverage % |
| --- | --- | --- |
| Eq. 7 | 10.3 | 80.86 |
| bootstrap | 2.62 | 80.3 |
| influence | 2.5 | 80.86 |

These are nominal 95% intervals; low coverage is a negative finding. The same rare-failure issue affects the percentile bootstrap. The ratio linearization is not a novel theorem and should remain supplementary.

## Prior work and claim boundary

[Conformal Risk Control](https://arxiv.org/html/2208.02814v4) already treats monotone risks. [Conformal Lesion Segmentation](https://arxiv.org/abs/2510.17897) already calibrates critical thresholds per example. In maintenance, [Kumar et al.](https://link.springer.com/chapter/10.1007/978-3-032-29501-9_23) describe economic threshold selection within a conformal safe region, and [Almeida et al.](https://journals.sagepub.com/doi/10.1177/14759217261445819) optimize maintenance subject to a miss-rate constraint. Their publisher abstracts were accessible; their subscription full methods remain to be compared. Consequently, a broad first-method claim is unsupported.

The remaining candidate distinction is the explicit entire-life alarm score, with lead time and action-grid feasibility, evaluated against matched-information operational policies across domains. The package adds empirical evidence on the difference between alarm-window success, operational failure, renewal cost, finite-sample feasibility and transfer. That is a worthwhile empirical formulation and audit; it should not be sold as a new conformal rank theorem or as deployment certification for these implementations.

## Recommended manuscript claim

“We formulate trajectory-level critical scores for end-of-life threshold alarms and evaluate conformal calibration alongside window and cost tuning. A standard conformal rank argument gives a marginal guarantee for independently fixed alarm rules under exchangeability and feasible actions. Matched-information experiments examine where practical OOF/refitted variants reduce threshold fragility, where they incur cost or failure tradeoffs, and where small calibration samples or batch transfer invalidate a certification interpretation.”

The current evidence supports a careful empirical/negative-result contribution. A stronger methodological claim requires a fully independent calibration implementation and a detailed closest-method comparison, not additional test-set tuning. Publication suitability remains an editorial judgment.

## Reproduce and inspect

Use `.venv/Scripts/python.exe` with the pinned requirements and `OMP_NUM_THREADS=1`. `contrib/README.md` gives the run order. `out/contrib/completion_audit.json` records completeness checks and hashes. Per-unit cost/M rows, calibration settings/scores, selected settings, checkpoints, baseline equivalence and leakage logs are retained. `paper7/numbers.json` joins the historical evidence to the new contribution data with an explicit provenance key; the original paper6 evidence is preserved.
