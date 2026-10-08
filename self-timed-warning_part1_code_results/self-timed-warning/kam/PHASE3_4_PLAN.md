# Phases 3 and 4: plan fixed before the runs

Status of every analysis below: **exploratory, post hoc, plan fixed and hashed before the run** (SHA-256 in
`PHASE3_4_PLAN.sha256`). Nothing in the recipe, its grids or the window [-13, +2] changes. Every setting is selected on
training units only; test units are scored once. Stop rules as in Phase 2: a failed leakage check, a failed unit test, or a
grid-mapped M < 0 stops the run.

Approval: the author's instruction of 2026-10-06 ("Complete all the phase and re-write the paper") covers Phases 3, 4 and 5.
Compute choice made by me under that instruction: five-fold runs on FD002-FD004 (about 2 CPU-hours); the 30 random
splits are run on FD001 only (about 4.5 extra hours would be needed for FD002-FD004 and are not spent).

## R0. Reproduction of Phase 2 (container reset)

The per-unit outputs and checkpoints of Phase 2 were lost when the workspace was reset; only the summary tables were kept
(`results/kam/fd001_*`). `kam/kam_fd001.py` is re-run unchanged in its decisions (FD001: five-fold, leakage checks E2-E4,
30 splits). The only code change is additive: per split it also saves the probability series and the alarm tables of the
selected cost-tuned settings (`*_series.pkl`) for the fragility analysis, and a `--ds` argument selects the dataset
(default FD001). **Check R0:** the regenerated `fd001_cv_table.csv`, `fd001_cv_pairs.csv`, `fd001_rs_policies.csv` and
`fd001_rs_pairs.csv` must equal the frozen Phase 2 files to the printed precision. If they do not, the difference is
reported and the frozen tables are not silently replaced.

## Phase 3. Robustness of direct threshold optimisation

### P3.1 Runs

- FD002, FD003, FD004: `kam/kam_fd001.py cv --ds FDxxx` followed by `leak --ds FDxxx`. Identical code path, settings and
  seeds as Phase 2 with amendment 1: existing outer folds (seed 2026), inner seed 100 + fold, 1-SE bootstrap seed 2026 + fold,
  ΔT = 10, ℓ = 0, c_p = 1, c_p/c_c ∈ {0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8} (chosen to span the ranges shown in their figures),
  P-cls (isotonic on inner OOF), P-res (cap-60 regressor, bins on inner OOF, ≥ 200 rows per bin, PAVA), policy 3 with cap 60
  and cap 125 (sensitivity), tie rules "mid" (primary) and "max", grid-mapped re-selection of my policies, an alarm mapped to
  a grid point at or beyond failure counts as a failure. "Beats": paired bootstrap 95% interval (2,000 resamples, seed 2027)
  of the M difference excludes 0, five-fold run. Primary ratio 0.1; the other ratios are descriptive.
- ΔT = 10 on FD002-FD004: lives are 128-543 cycles, so a grid step is at most 7.8% of the shortest life, as on FD001.
- **Not included:** N-CMAPSS (lives 48-100 flight cycles; ΔT = 10 would be 10-21% of a life, so no M is reported for it with
  ΔT = 10, and no other ΔT is introduced here); PHM08 (not requested; compute).

### P3.2 Fragility analysis (their Fig. 9a on my data)

Computed from the saved series without refitting (`kam/kam_fragility.py`).

1. **Training curve (Fig. 9a analogue).** For policy 1 (P-cls and P-res) in every training set and ratio: training M̂ as a
   function of p_thres over the Phase 2 grid PGRID; the tied minimising set [p_min, p_max]; p_fail,train = the smallest
   p_thres with ≥ 1 training failure. A figure shows FD001 fold 1 at c_p/c_c = 0.01 (training and test curves), with p_mid,
   p_max and p_fail,train marked; the fold and ratio are fixed here, not chosen after looking.
2. **Test outcome.** For every test set (5 folds × FD001-FD004; 30 FD001 splits) and ratio: test failures and M̂ at
   p_mid and p_max; p_fail,test = the smallest p_thres with ≥ 1 test failure; margin log10(p_fail,test / p_opt).
3. **Same for my plain cost-tuned STW**, in its threshold τ (cycles) for the selected (cap, span, debounce):
   τ_fail,test = the largest τ with ≥ 1 test failure; margin τ_sel - τ_fail,test (cycles).
4. **Tallies.** For each policy, the number of (test set, ratio) cells with ≥ 1 test failure, and with M̂ > 50%, by dataset
   (five-fold) and over the 30 FD001 splits; for all ratios and for ratios ≤ 0.1 (where one failure dominates M).
   Policies: P1-cls and P1-res optimised (mid, max), P1-cls and P1-res with p = c_p/c_c, STW plain cost-tuned, STW 1-SE,
   STW window-tuned, HI cost-tuned.
5. **Tie rules.** Number of test decisions (unit × ratio) that differ between "mid" and "max", per dataset; M̂ under both,
   side by side.

**Decision rule, fixed now.** The manuscript's claim that direct cost tuning is fragile is called *supported* on a dataset
if, at ratios ≤ 0.1, each plainly optimised policy (P1-cls opt, P1-res opt, STW plain) has more cells with ≥ 1 test
failure than its regularised or heuristic counterpart (P1 with p = c_p/c_c for the same probability model; STW 1-SE), and
*weakened* otherwise. Over the 30 FD001 splits the same comparison is reported descriptively. Whatever the result, it is
reported.

## Phase 4. Open weaknesses

### 4a. Battery cost, fully nested (convention C)

`audit_battery_cost_nested.py`. Splits cv1-cv5 (by cell, seed 2026) and lobo1-lobo3, inner seed as in
`audit_confirmations.battery_splits`.

- Every inner training subset builds its own blocks with κ by the protocol rule from that subset, its own z-score statistics
  and its own models; inner validation cells are predicted in their own blocks. The final models use κ by the rule from the
  outer training set. No life outside a training subset enters any time scale or setting (convention C).
- Task in cycles (the engine task scaled by three, as in the fully nested window analysis): warning levels
  H ∈ {30, 45, 60, 90, 120} cycles, window [-39, +6] cycles, caps {120, 180, 270} cycles (cap ≥ H + 60), shifts
  -36 ... +24 cycles (step 1.5), cost thresholds τ ∈ {3, 6, ..., 180} cycles; span and debounce in blocks. A model in
  blocks of κ uses every cycle quantity divided by κ.
- Alarm tables are converted to cycles (remaining life at the alarm, alarm cycle and life multiplied by the κ of the
  model that produced them) and concatenated over inner folds, so the training cost rates of different-κ folds are summed
  in cycles. Lead times ℓ ∈ {0, 15, 30, 45} cycles, ρ ∈ {5, 10, 20, 50}; perfect foresight = replacement at L - 1 cycles.
- Policies (as in the convention-B analysis): recipe window-tuned (settings per H by the summed inner window count, H by
  training cost), recipe cost-tuned (plain, 1-SE, 80th percentile), 10% quantile alarm (plain, 1-SE), health-indicator
  alarm (plain), capacity threshold (plain, 1-SE), capacity trend window-tuned and cost-tuned (plain, 1-SE), optimal age
  replacement (training lives in cycles). Capacity policies fit nothing; their settings are chosen on the training cells in
  the outer-κ blocks.
- **Check R4a:** at H = 60 cycles the window-tuned recipe must reproduce the per-cell first-warning outcomes of the fully
  nested window analysis ("rule, nested": 117/123 under cross-validation, 98/123 with a batch held out), because the inner
  folds, κ, grids and selection are the same.
- Outputs replace the convention-B battery entries of the cost tables (Tables 7 and 9, Fig. 9), which are then labelled
  convention C. Convention-B results remain in the supplement for provenance.

### 4b. Calibrated health-indicator alarm (engines)

`audit_hi_calibrated.py`, on PHM08, FD001-FD004 and N-CMAPSS, existing outer folds (seed 2026), inner seed 100 + fold.
The linear health indicator of the existing health-indicator alarm (same features and fit, on each inner training subset
for out-of-fold values and on all outer training units for test units) is mapped to cycles by an isotonic, decreasing
regression of min(r, c) on the indicator value, fitted on the pooled inner out-of-fold values of the training units, for
each cap c ∈ {40, 60, 90}. The mapped series then goes through the recipe's trigger with the recipe's grids and selection
rule (caps c ≥ H + 20, spans, debounces, shifts; most correct out-of-fold first warnings, ties to smaller |s|), for every
H ∈ {10, 15, 20, 30, 40}. Test units are scored once. The battery is not included (its timing-control row is under
convention B, and the capacity baselines already provide a domain baseline there).

Reported: in-window rate per dataset and H; paired exact McNemar against the recipe (Holm over the six datasets at H = 20)
and against the uncalibrated health-indicator alarm; notice at the alarm. **Interpretation fixed now:** if the calibrated
indicator is not significantly below the recipe on a dataset at H = 20, the sentence "what the regressor contributes is a
health indicator calibrated in cycles to failure" is changed to attribute the timing to calibration in cycles, not to the
gradient-boosted regressor, for that dataset; if it is significantly below on a dataset, the regressor adds timing
information beyond a calibrated linear indicator there.

### 4c. Capacity-trend baseline in the key-numbers table

From the existing fully nested window analysis (`results/audit/battery_physical_{cv,lobo}.csv.gz`) and the new 4a cost
outputs; no new run.

### 4d. Q1 decomposition on a second dataset (FD004)

`audit_fixed_matched.py --ds FD004`: the matched cross-fitted variants of the PHM08 analysis (fixed-time GBM at 50% and 90%
of life and at 20 true cycles left, the fixed-time model with the trigger, the recipe regressor at 90% of life and at 20
cycles left, the self-timed recipe) with the same seeds; the 75/25 rows exist only for PHM08 and are not produced.
**Check R4d:** the self-timed recipe must reproduce the FD004 H = 20 result of Table 5 (206/249) unit by unit.
**The PHM08 conclusion is said to repeat** if (i) the calibrated fixed-time model at 50% of life is at least 30 points
below the same model at 90% of life, and (ii) the self-timed recipe is not significantly above its own regressor at 90% of
life (exact McNemar, p ≥ 0.05). Otherwise the paper says it does not repeat, and how.

## Phase 5 (manuscript)

Rewrite per the brief and `changes.md`; every new number from `numbers.json` key `rev5` (built by
`kam/make_rev5_numbers.py` from the result files above), with build checks.
