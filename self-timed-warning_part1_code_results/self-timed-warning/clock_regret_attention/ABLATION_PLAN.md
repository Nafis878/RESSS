# Follow-up ablations fixed before new training and confirmation data

This follows the original four-test experiment and the exploratory greedy
challenger. It is not the original preregistered plan and was not publicly
registered. Previous held-out results motivated this study; preserve them.

1. Retrain three seeds of a DeepSets-style mean-pooling ranker with 9,053
   parameters, same 12 features, and an attention ranker with all six broadcast
   pair-context features zeroed (8,993 parameters). The latter still sees
   pair-conditioned asset normalization and eligibility; call it removal of
   broadcast context, not removal of every pair input. Use the original 1,600
   training/200 validation cohorts and identical 25-epoch Adam/BCE schedule.
2. Evaluate original held-out cohorts descriptively for these two ablations.
   Do not add these comparisons to the original four-test family or retune.
3. On validation, compare ensemble mean logits for the three seeds of attention,
   pointwise MLP, pooled ranker and no-broadcast-context attention, plus premium,
   singleton, premium/use, horizon and sequential greedy. Select the smallest
   mean log(exact/focused) at focus budget four; fixed lexical method-name tie
   break. Save the choice before generating fresh confirmation cohorts.
4. Fresh confirmation: 300 ID/300 shift with seeds 20261403/20261404 using the
   unchanged generator. Compare the selected selector against premium and
   sequential greedy, four two-sided paired sign-flip tests (9,999 draws,
   seed 20261500), Holm family four, bootstrap 2,000 cohorts, nominal 95% CI.
   If the winner is greedy, its comparison to itself is a structural tie.
   These are new finite-synthetic proposal tests, not novelty/maintenance tests.
5. Budget removal study on the original held-out inputs: k=0,1,2,4,8 for
   premium, sequential greedy and original attention ensembles. Report mean
   log gap, certificate factor, coverage and actual proposal subset evaluations.
   No universal runtime or scaling conclusion from eight eligible assets.
6. Omission-certificate removal: retain and verify the explicit false-certificate
   counterexample. Full-focus enumeration establishes an exact ceiling, while
   the previous full solver remains the mathematical fallback.
7. Reconcile all previous phases in a failure/limitations ledger with source
   paths, retaining negative outcomes. Do not combine incompatible metrics,
   select favorable test cases, or claim best-of-test as independent validation.

The deliverable is a precise certified method with optional learned guidance,
not a guaranteed positive novelty verdict. Architectural attention and generic
scenario reduction are prior art. The specific omitted-premium theorem and
sharpness are candidate contributions pending historical/external scrutiny.
