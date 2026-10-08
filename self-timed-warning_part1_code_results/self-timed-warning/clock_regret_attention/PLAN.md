# Attention investigation: plan fixed before training outcomes

Goal: determine whether attention can add a distinct, useful scientific mechanism
to the censored-cohort method. Do not claim novelty for a Transformer, survival
prediction, learned combinatorial ranking or scenario selection: primary papers
already establish these ideas. All 1,025 earlier artifacts are protected.

## Mechanism to test

Use pair-conditioned set self-attention to rank unresolved assets for a small
exact adversarial subset search in earlier-versus-later comparisons. Keep every
asset in all baseline costs and uses. Unfocused assets are excluded only from
the proposed search, not silently removed from the true uncertainty set.

Derive a data-dependent omitted-premium certificate for any focus selector,
including wrong/adversarial attention. Attempt to prove its sharpness and compare
its worst-case factor with sorting by premium. Reject attention weights as
failure probabilities, evidence of causality or valid uncertainty restrictions.

## Fixed experiment

- Training: 1,600 independently generated cohorts; validation: 200; held-out ID:
  300; held-out shifted costs/horizons: 300. Separate fixed seeds 20261101-04.
  Each pair a<b, eight censored eligible assets and two observed failures. Public
  horizons/premiums and observed failures are features. Labels are exact robust
  subset membership from the observable optimization problem, not hidden future
  lifetimes. No test cases or real sealed outcomes are used for training.
- Three model seeds 11,22,33. A two-head, width-32 set attention encoder with
  one attention block; a pointwise MLP ablation receiving the same public token
  and pair-context features. Attention has no positional embedding. Adam,
  learning rate 0.002, batch 64, 25 fixed epochs; validation membership BCE
  selects the checkpoint within that fixed schedule. No test-based tuning.
- Baselines: largest premium; earliest horizon; premium divided by earliest use;
  immediate singleton objective improvement; deterministic random ranking; MLP.
  Exact restricted search over top four assets for all selectors. The full
  eight-asset exact search is an evaluation oracle, not a selection input.
- Primary metric: mean log(G_exact/g_focus), averaged over the three model seeds
  at each held-out cohort. Compare attention with premium sorting and matched
  MLP, separately ID and shift: four tests, paired sign flips of mean differences,
  9,999 random sign-flip draws, Holm correction. Report raw effect sizes,
  cohort-bootstrap 95% intervals (2,000 draws), ties/wins/losses and all baselines.
  These tests assess solver-proposal quality, not historical novelty or deployment.
- Secondary metrics: certificate factor, full-optimum coverage, exact-focus
  witness feasibility, validation loss, and inference time (descriptive only).
  Report parameter counts and the different model capacities; no runtime claim
  without measuring the whole pipeline and no independence claim across seeds.
- Deterministic mathematical checks: 500 full-clock tiny cases with arbitrary
  focus sets, 500 random eight-asset cases, sharpness sequences, attention
  permutation equivariance, malformed proposals and a failure counterexample
  for naive omission. Validity must not depend on trained attention quality.

If the statistical/literature gate fails, retain the mathematical result where
valid, reject the attention novelty claim and leave the stronger prior method
intact. A better score cannot substitute for an established new mechanism.
