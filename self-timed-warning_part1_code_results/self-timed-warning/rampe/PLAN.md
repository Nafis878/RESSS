# RAMPE prototype investigation — 8 October 2026

This is an exploratory, post hoc study, not a preregistered experiment. The previous CAT investigation, source, datasets and outputs are frozen. New code lives in `rampe/`; all generated data live in `out/rampe/`. A one-time protection manifest combines the original protected hashes, original input hashes, and every artifact from the previous investigation. Never reset it after experimentation.

The user explicitly requests implementation even if novelty fails. Implement, test, analyze, search again and reject the prototype if required. Do not rescue CAT-c, invent a deployment certificate or skip negative results.

## Real-data estimand and information budget

The pool is the four existing policies: plain cost, CAT at .05, CAT-c at .05 and 1-SE. The fallback is 1-SE. Each supplies a complete compatible maintenance policy; arbitration selects one policy for a unit, rather than averaging alarm times. Randomized ensembles sample one complete policy per unit.

Use frozen unit outcomes and the original five engine folds/five battery CV folds/three battery batch holdouts. For each fixed outer split, divide its originally held-out units into labelled meta-validation (floor(n/2)) and disjoint meta-test units using seeds 2026–2035. Candidates were fixed using the original outer training data; the new labelled validation budget is additional information, equally available to all new pool selectors. CAT/CAT-c/1-SE remain independent baselines. This is retrospective arbitration with completed validation lives, not zero-label transfer or a replacement for the old evaluation. No new predictor-training seed is implied.

Query context uses the first observed operating regime for engines, first flight class for N-CMAPSS, and publicly known batch for batteries. No lifetime, future trajectory, test outcome or future alarm time enters selection. Context partitions are protocol-defined. Unit outcomes are used only after selecting a policy. Bearing has no comparable four-policy cost pool and is excluded explicitly.

## Prototype and alternatives

For each query context, estimate renewal cost C, bootstrap winning share S, corrected binomial failure upper bound Q, observed context-support indicator T, bootstrap cost SD U, and leave-one-validation-unit winning share D. T measures support, not true transfer reliability. A missing regime cannot be called reliable. Inspect global and local risk estimates separately. The analytic reliability index is the minimum satisfaction of the risk and majority-support requirements, with unsupported context excluded. Select the lowest cost plus one bootstrap SD among eligible candidates; abstain to 1-SE otherwise. Majority .5 is an interpretable heuristic, not a calibrated theorem. Alpha/delta are fixed .05; 100 paired bootstrap draws are a computational accuracy setting.

Compare analytical RAMPE; normalized reliability; learned empirical acceptability; uncertainty-only selection; rank-based reliability. Normalized/rank combinations are explicitly heuristic, not probability estimates. Learned acceptability uses leave-one-dataset-out meta-training, excluding both battery regimes together when battery is evaluated. It must not train on outcomes from its held-out dataset.

Compare original policies, conventional cheapest pool policy, uniform policy ensemble, reliability-weighted policy ensemble, RAMPE and removals of reliability/stability/calibration/context-support/abstention/context, plus random weights and inverse-cost weights. Report identical/redundant removals honestly.

## Experiments

1. All six engines and both battery regimes, all four leads/four costs, ten meta-validation seeds. Report cost rate, individual mean/median/max/variance cost, failures, selected authority, between-unit authority changes (not within-life switching), abstention and paired diagnostic fallback effects. Failure is the existing unplanned-failure proxy; no severity-specific catastrophe data exist.
2. Validation perturbations: fractions .25/.5/1 of the same validation set; additive accounting noise SD 0/.1/1 preventive-cost units; ten seeds. Keep binary outcome labels fixed. This perturbation does not simulate sensor noise. Cost/lead shift fixes policies selected at zero lead/rho10 and changes their economics/required response lead using their existing alarm outcomes. Unseen-context intervention removes known support; it does not invent sensor regimes.
3. Cross-dataset transfer of learned arbitration only; actual predictor/policy transfer between incompatible engines/batteries is not implied. Cross-setting fixed-rule lead/cost tests as above; environmental battery tests retain three holdouts. No verified chronology exists; do not relabel unit order as real temporal transfer.
4. Preserve and read all 247680 previous score-stress rows, reporting a compatibility bridge. Those rows lack all-policy action/cost trajectories, so they cannot be honestly recast as RAMPE cost experiments. Reuse their calibration fractions and seed framework where applicable.
5. Controlled independent synthetic validation/test cohorts: A cheaper in expectation but rare-event/high-variance; B stable preventive fallback; C specializes in a known regime. Vary n=32/128/512/2048, failure cost=10/50, cost-noise SD=0/1, shift magnitude=0/.5/1, source regime imbalance=.1/.5/.9, seeds2026–2055. Target cohorts are independent, with 1000 units. Include unseen-regime and all-policies-fail attacks. The generator and true expected costs are explicit; it is not a maintenance simulator.
6. Evaluate whether reliability actually changes authority when the best policy is uncertain. Report selection error versus synthetic population oracle and ablation effects, not only cost improvements.

## Theory, statistics and gate

State a standard simultaneous conditional-risk selection property under fixed candidates, fixed finite strata and iid calibration, including fallback limitation. Derive a standard uniform-estimation selection-regret result with explicit assumptions; do not claim original mathematics. The empirical bootstrap/stability index is heuristic. Arbitrary conditional shift remains unidentified.

Descriptive real-data resampling SDs/intervals are conditional on reused frozen units/models. Use one seed for disjoint per-split unit paired tests; do not count all repeated splits as independent observations. Correct the family of paired risk comparisons with Holm; use paired cost bootstrap with rare-event caveats. Synthetic independent-cohort seed pairs permit Monte Carlo paired inference. Include mean/SD/median/effect sizes/W/T/L and all negative results.

Search before novelty claims, covering dynamic ensemble selection/META-DES, mixture-of-experts/gating, calibrated multi-expert deferral, safe fallback, robust selection/shift, maintenance ensembles, and bandit/RL arbitration. Search again using the implemented min-gate, binomial-risk constraints, bootstrap/jackknife winning shares and context support. Apply six novelty criteria A–F literally.

RL is implemented only if actions affect subsequent state/information in a justified model. Frozen independent unit outcomes support contextual/offline selection, not an MDP; unit ordering alone is not RL. Document this decision before adding any sequential algorithm.

Deliver the requested 20-section report, all experiment/ablation tables, proofs and assumptions, code/tests, literature overlap/novelty attack, preservation manifest and exactly one A/B/C/D verdict plus YES/NO answer. No positive outcome is presumed.
