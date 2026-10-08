# Mechanism investigation, 8 October 2026

This is a post hoc investigation using already observed CAT results. It is not preregistered or confirmatory. Existing source files, datasets, plans, manuscripts and frozen results are protected by `out/research_next/protected_before.json`. New outputs go only in `out/research_next/`.

## Order and scientific gate

1. Inventory and parse existing source and frozen outputs; reconstruct selection mathematics and operational effects.
2. Investigate three explanations: uncertainty in validation cost; confounding of alarm settings and conservatism; source-to-target score shift versus predictor refitting.
3. Compare precise candidate mechanisms with primary literature on sample-variance penalization, stability-adjusted CV, Learn then Test/Pareto Testing, safe policy improvement and shift-aware tuning. A generic penalty, fallback, independent split or weighted conformal quantile is not accepted as algorithmic novelty.
4. Derive only results whose assumptions can be stated and proved. Separate deterministic mechanics, standard rank/concentration results and unsupported deployment claims.
5. Implement an isolated diagnostic/replay module and tests. A new optimizer proceeds only if a distinct mechanism survives the novelty gate. If none does, record that outcome and do not fabricate a new-method benchmark or ablation result.
6. Use existing setting-choice and alpha ablations to examine the claimed failure mechanism. They do not identify all causal effects of retraining.
7. Reconstruct battery scores from the frozen selected alarm setting, using the original preprocessing, splits, seeds and GBM. Check every primary CAT/CAT-c unit decision against frozen rows. Compare OOF, inner-model target and refitted-model target scores. This is diagnostic replay, not a replacement experiment.
8. Stress calibration using fixed frozen signals: source-calibration sample sizes 25/50/100 percent; score noise 0/3/6 cycles (battery multiplied by three); additive target critical-score shifts 0/3/6/12 cycles (battery multiplied by three); resampling seeds 2026–2035; alpha 0.01/0.02/0.05/0.10. Report finite-threshold availability and actual fallback outcomes. These are calibration resamples/score perturbations, not freshly trained model seeds or raw-sensor corruptions.
9. For battery transfer, compare source calibration with labelled-target calibration at budgets 5/10/19/25 completed target lives, using seeds 2026–2035 and evaluating only the remaining cells. This is an existing split-conformal reference with an explicit information cost, not a novel algorithm or an operational online result.
10. Report all datasets, batch heterogeneity, mean/SD/median, paired effects and descriptive conditional intervals. Treat overlapping CV fits, repeated use of units and the already inspected benchmark as limitations. Do not count cost cells or calibration resamples as independent dataset replications. Perform no test-result tuning.

## Final deliverables

`FINAL_SCIENTIFIC_REPORT.md`: phases 1–10, audit A–E, ranked directions, exact novelty gate, mathematical status, pseudocode and all 16 requested pitch items. Tables and diagnostic outputs, test results and a preservation/completion manifest accompany it. An honest negative novelty verdict is an acceptable final scientific outcome. A proposed but unvalidated algorithm must not be described as implemented, validated or submission-ready.
