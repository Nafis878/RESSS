# Completed attention and failure-ablation investigation

The requested ablations and synthesis are complete. The strongest retained
combination is shared-clock heterogeneous relative regret, compatible witnesses,
omitted-premium focus bounds, validation-selected greedy proposals, a
premium-optimal certificate focus and the complete-family FPTAS fallback.
Attention remains optional: it did not establish superiority against greedy.

**Novelty verdict B: a precise, proved candidate contribution exists; historical
originality and scientific priority are not established.** There is no honest
9/10 or established-new-attention-method claim supported by these results.

## What was added

- Selector-independent bound `g_F <= G <= kappa_F*g_F`, where
  `kappa_F=((C_a+Q_tail)*C_b)/(C_a*(C_b+Q_tail))`.
- A sharp pairwise family, a top-premium optimality result and an exact minimum
  certified focus-budget threshold for that bound.
- A complete discrete-family implementation intersecting greedy/learned focus,
  premium focus and the prior FPTAS, retaining a lower-endpoint witness and
  the previous `(1+epsilon)` selected-policy guarantee.
- Twelve trained checkpoints: attention, matched pointwise MLP, pooled set
  context and attention without six broadcast pair-context features; three
  seeds each. The context-removal ablation still includes pair-normalized
  token inputs. No new attention architecture is claimed.
- k=0,1,2,4,8 focus-budget ablations, exact full-focus ceiling, omission-certificate
  counterexample, arbitrary-focus validity checks and complete-family integration.
- A source-linked failure ledger covering CAT/transfer, RAMPE, observability,
  generic LP, shared-clock/linear, heterogeneous fleet and attention phases.

## Experimental findings

Original experiment: 1,600 training, 200 validation, 300 ID and 300 shifted
held-out cohorts; eight eligible unresolved assets plus two known failures.
Focus budget four. Mean log-gap is averaged over three seed metrics per cohort.
Attention gaps are .004706 ID and .015685 shift; premium .005342/.017257;
pointwise MLP .005143/.019922. Holm p-values for attention versus premium are
.0004 on both splits, versus MLP .0195 ID and .0004 shift. Nominal cohort
bootstrap intervals and all wins/ties/losses are saved. These are small proposal
quality effects conditional on fitted models and the specified synthetic laws.

The post-training greedy challenger has smaller means .004608/.015272. It is
explicitly exploratory and is not retroactively inserted into the original
four-test family. The two retrained ablations also do not beat greedy in mean.
The follow-up ensemble protocol averages logits, so its separate table is
not substituted for the original seed-average table.

Validation selects greedy (.003026 versus attention .003065). The choice was
saved before generating 600 fresh confirmation cohorts. Greedy versus premium
has mean differences -.000701 ID (CI[-.001108,-.000379]) and -.001225 shift
(CI[-.001704,-.000795]); Holm p=.0004 in each. Wins/ties/losses are 29/271/0
and 42/258/0. Comparisons to the selected greedy rule itself are structural
ties, not independent evidence. No test choices or model settings were changed
after these confirmation outcomes.

Budget ablations expose failure at k=1,2, where attention has larger mean gaps
than premium. At k=4, attention ensemble coverage is 75.33% ID and 37% shift,
greedy 76.33%/38.33%, premium 72.67%/31%. Mean factors remain about 3 and 11;
premium minimizes that factor. Full focus gives exactness for every selector.
Greedy proposal plus final search uses 188 subset evaluations here versus 16
final evaluations for attention/premium, excluding inference and fallback.
There is no complete-pipeline speedup claim.

## Failure synthesis and limitations

CAT transfer and calibration/refit limits, RAMPE's all-fallback behavior,
generic-LP equivalence and negative engineering findings remain. The final
method uses a deterministic finite-cohort uncertainty set rather than attaching
those empirical risk screens to a deployment safety statement. Failure costs
remain scenario values. Joint physical constraints, adaptive sensor policies,
intervention dynamics, noisy clocks, large-fleet learned generalization and
measured maintenance benefits are untested or outside the model.

Paired sign flips assume null exchangeability/symmetry. Bootstrap intervals
are conditional, nominal and do not include retraining uncertainty. Repeated
seeds are not independent cohort replicates. Novelty/priority is a historical
question, distinct from those tests. Primary-source overlap, inspection limits
and the precise claim are in LITERATURE.md and NOVELTY_CLAIM.md.

## Completed verification

Nine unit-test groups pass, including 500 independent full-clock cases, 100
complete-family cases with deliberately unhelpful proposals, sharpness,
permutation equivariance, minimum certified budget and malformed-input checks.
The verifier regenerates all original exact labels and reproduces 6,600 saved
focused results, 3,600 checkpoint predictions, four original tests, 500 stored
arbitrary-focus cases and 600 greedy cases. Follow-up verification checks 21,000
ablation/confirmation/budget intervals, 6,000 fresh prediction/greedy results,
validation selection, fresh dataset separation, four corrected confirmation
tests and 40 default/trained complete-family comparisons. The resulting total
synthetic dataset has 3,000 cohorts. All 1,025 protected older artifacts remain
byte-identical. Final logs, attributed eight-page PDF, rendered-page review,
environment snapshot and review archive are retained.

The earlier Fox full-text access gap is resolved; the separate moment-robust
full derivation, external equivalence judgment, measured engineering evidence
and actual public disclosure remain unresolved. These limits prevent marking
scientific originality or priority established.
