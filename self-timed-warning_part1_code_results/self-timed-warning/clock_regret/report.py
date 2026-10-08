"""Generate the scientific report, a method-distinguishing example and figures."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from clock_regret.core import select
from clock_regret.run import OUT


def main():
    ages = [8, 12, 16, 24]
    answer = select([6] * 12, [False] * 12, ages, 20)
    exact = np.array([[float(p.ratio) for p in row] for row in answer['pairs']])
    marg = answer['marginal_intervals']
    rect = np.array([[1. if i == j else float(marg[i][1] / marg[j][0])
                      for j in range(4)] for i in range(4)])
    demo = dict(n=12, horizon=6, logger_failed=False, rho=20, ages=ages,
                exact_selected_age=ages[answer['chosen']],
                rectangle_selected_age=ages[answer['rectangle']],
                upper_rate_selected_age=ages[answer['upper_rate']],
                exact_scores=[str(x) for x in answer['scores']],
                rectangle_scores=[str(x) for x in answer['rectangle_scores']],
                pairwise_exact=[[str(p.ratio) for p in row] for row in answer['pairs']],
                pairwise_witnesses=[[p.witness.tolist() for p in row] for row in answer['pairs']])
    (OUT / 'strict_example.json').write_text(json.dumps(demo, indent=2), encoding='utf-8')
    plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.9), layout='constrained')
    limit = max(rect.max(), exact.max())
    for ax, matrix, title in zip(axes, [rect, exact],
                                  ['Independent sharp marginal rectangle', 'Exact shared-lifetime comparison']):
        im = ax.imshow(matrix, cmap='Blues', vmin=1, vmax=limit)
        ax.set_xticks(range(4), ages)
        ax.set_yticks(range(4), ages)
        ax.set_xlabel('Comparator replacement age b')
        ax.set_ylabel('Candidate replacement age a')
        ax.set_title(title, fontsize=12)
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f'{matrix[i,j]:.2f}', ha='center', va='center',
                        color='white' if matrix[i,j] > limit * .6 else 'black')
    fig.colorbar(im, ax=axes, shrink=.85, label='Worst cost-rate ratio / upper bound')
    fig.suptitle('Same censored records: 12 assets, H = 6, failure cost = 20', fontsize=14)
    fig.savefig(OUT / 'shared_clock_example.png', dpi=180)
    fig.savefig(OUT / 'shared_clock_example.svg')
    plt.close(fig)

    law = pd.read_csv(OUT / 'synthetic_law_summary.csv')
    labels = ['short', 'mixture', 'long']
    methods = ['exact_shared_clock', 'sharp_rectangle', 'upper_rate']
    names = ['Exact shared clock', 'Sharp rectangle', 'Upper cost rate']
    colors = ['#235789', '#E07A5F', '#7A9E7E']
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5), layout='constrained')
    x = np.arange(3)
    for ax, metric, title in zip(axes,
            ['realized_relative_regret', 'exact_worst_relative_regret'],
            ['Realized cost-rate factor', 'Exact worst-case factor of selected age']):
        for j, (method, name, color) in enumerate(zip(methods, names, colors)):
            values = law[law.method == method].set_index('dataset').loc[labels, metric].to_numpy()
            bars = ax.bar(x + (j - 1) * .25, values, .24, label=name, color=color)
            ax.bar_label(bars, fmt='%.2f', padding=3, fontsize=9)
        ax.axhline(1, color='#777777', linestyle='--', linewidth=.8)
        ax.set_xticks(x, ['Short life', 'Mixture', 'Long life'])
        ax.set_ylim(0, 3.05 if metric == 'realized_relative_regret' else 8.3)
        ax.set_ylabel('Factor above the same-cohort oracle (lower is better)')
        ax.set_title(title, fontsize=12)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc='outside lower center', ncol=3, frameon=False)
    fig.suptitle('2,400 independent synthetic cohorts: 800 per lifetime law', fontsize=14)
    fig.savefig(OUT / 'synthetic_tradeoff.png', dpi=180)
    fig.savefig(OUT / 'synthetic_tradeoff.svg')
    plt.close(fig)

    sp = pd.read_csv(OUT / 'synthetic_paired.csv.gz')
    delta = sp.groupby('baseline').relative_regret_difference.mean()
    guarantee = sp.groupby('baseline').guaranteed_factor_reduction.mean()
    rp = pd.read_csv(OUT / 'real_paired_domain_summary.csv')
    real_table = ['| Domain / replay | Delta vs rectangle | Delta vs upper rate |',
                  '|---|---:|---:|']
    for (ds, an), g in rp.groupby(['dataset', 'analysis']):
        q = g.set_index('baseline').relative_regret_difference
        real_table.append(f'| {ds} / {an} | {q.sharp_rectangle:+.6f} | {q.upper_rate:+.6f} |')
    counts = pd.read_csv(OUT / 'real_policy_provenance.csv').deduplicated_ages.str.count(r'\|').add(1).value_counts()
    methods_table = ['| Lifetime law | Exact factor | Rectangle factor | Upper-rate factor | Exact failure fraction | Upper-rate failure fraction |',
                     '|---|---:|---:|---:|---:|---:|']
    for label in labels:
        q = law[law.dataset == label].set_index('method')
        methods_table.append(f'| {label} | {q.loc[methods[0],"realized_relative_regret"]:.6f} | '
            f'{q.loc[methods[1],"realized_relative_regret"]:.6f} | {q.loc[methods[2],"realized_relative_regret"]:.6f} | '
            f'{q.loc[methods[0],"risk"]:.6f} | {q.loc[methods[2],"risk"]:.6f} |')
    report = f'''# Exact shared-lifetime regret: final scientific assessment

**Outcome B: POTENTIALLY NOVEL BUT INSUFFICIENTLY ESTABLISHED.** A concrete exact method has been added and its correctness established under an explicit finite-cohort model. Its first-in-literature status and public scientific priority remain unestablished. The strict answer to "Have we established a genuinely novel method?" is **NO** at present. This is a substantive mathematical candidate, rather than another renamed ensemble; it is not yet a certified original contribution.

## 1. Scientific problem discovered

Preventive replacement hides an asset's failure time. Independently bounding several policies can make incompatible assumptions about that same asset: one policy's bound assumes early failure while another's assumes survival past it. The scientific target is a sharp comparison that respects their shared latent failure clock. The scope here is finite cohorts and fixed integer replacement ages.

## 2. Why existing CAT/CAT-c cannot solve this problem

CAT/CAT-c address calibration and constrained selection using established conformal ideas. They do not derive the joint feasible lifetime completions or the exact ratio-of-cohort-rates optimum below. RAMPE was previously rejected as a novel mechanism. Those conclusions and all 809 protected files are preserved. This authorized pivot does not rescue CAT, add an ensemble or claim that broad uncertainty-aware arbitration is new.

## 3. Mathematical formulation

Each asset has public integer endpoint H_i and observed-failure indicator delta_i. Compatible lifetimes satisfy L_i=H_i for observed failures and L_i>=H_i+1 otherwise. Every policy uses the same L_i. At fixed age d, failure is 1{{L_i<=d}}, use is min(L_i,d), and cost is 1+(rho-1)failure, with common rho>1. Failure exactly at the deadline is charged as failure.

Define R_d(L)=sum(cost)/sum(use), G(a,b)=sup_L R_a(L)/R_b(L), and W(a)=max_b G(a,b). Choose argmin_a W(a), breaking exact ties by the earliest age. Stored regret factors include one; excess relative regret is factor minus one. Neither E[cost/use] nor future-population renewal cost is the objective.

## 4. Algorithm and pseudocode

```
for every candidate age a and comparator age b:
    compute known outcomes and the joint-survival totals
    if a == b: G = 1
    if a < b:
        sort censored records eligible to fail by a
        enumerate the shared-failure count x
        place those x failures at their earliest compatible times
    if a > b:
        split censored records into early and middle phases
        sort later-only exposure gains and form prefix sums
        enumerate shared-failure count x and later-only count y
        set shared failures at b and later-only failures as early as allowed
    retain the largest exact rational ratio and its attaining lifetimes
select the age with the smallest maximum pairwise ratio
```

All pairwise maxima and the minimax recommendation are exact. Arithmetic-operation complexity is O(K^2(n^2+n log n)); a single pair needs O(n) working arrays. Retaining all witnesses takes O(K^2 n) space. Integer bit complexity is not constant. Code accepts common integer rho for exact fractions; the formulas apply to common real rho>1. Inputs whose possible cohort totals exceed int64 capacity are rejected before clock arithmetic; Fraction cross-products use arbitrary-precision integers. This computational range restriction is separate from a physical lifespan cap.

## 5. Sequential or RL extension

None is justified or implemented. The method is an offline finite-cohort robust comparison. It does not learn online, control a dynamic environment or solve sensor-triggered policy arbitration. Existing nested-feedback replacement bandits are prior art, not an extension to label as novel here.

## 6. Theoretical analysis

[THEORY.md](THEORY.md) gives a no-cap representation lemma, two constructive ordered failure-phase/count theorems and the exact finite-policy minimax corollary. For a<b, later-only failures can be removed; common failures occur at H+1 and a sorted prefix gives the optimum at each count. For a>b, shared failures occur at b, later-only failures at max(H+1,b+1), and sorted exposure gains solve each two-count case. These witnesses attain the claimed bounds.

The proof does not assume iid assets, noninformative censoring, a fitted survival distribution or bounded physical lifespan. It does assume the Cartesian lifetime-completion model, a common failure cost and constant ordered ages. Population safety, continuous clocks and heterogeneous costs are outside the proved scope.

## 7. Experimental results

All predeclared new experiments were completed: 2,400 independent synthetic cohorts across 24 cells, 304 frozen real cohort tasks across 38 original outer splits, and 120 additional generic-state exact comparisons. The 12 unit-test groups include 250 full-clock exhaustive checks and another 100 generic-state comparisons. In total there are 220 generic-state comparisons across tests and the timing audit. Every comparison matched exactly; all 39,448 stored pairwise witnesses are checked by the completion verifier.

Synthetic ages were fixed at 8,12,16,24; n=12/24, logging age=6/10, rho=5/20, short lifetimes uniform integers4..14, long18..40, and their 50/50 mixture. There are 100 independent cohorts per setting and 800 per law. The selector receives only public censored records, ages and rho; hidden lifetimes are stored separately for evaluation.

{chr(10).join(methods_table)}

Across the fixed setting mix, exact minus rectangle mean realized regret factor is {delta.sharp_rectangle:+.6f}; exact minus upper-rate is {delta.upper_rate:+.6f}. Thus the method improves the rectangle comparison on this average, but is worse than the stronger upper-rate selector on average. These are absolute factor differences, not percentage improvements. Short-life cost and failure risk worsen against upper-rate selection. There is no universal empirical advantage.

Real ages come from the four previously fitted conventional age baselines at source cost ratios5,10,20,50, deduplicated independently of evaluation lifetimes. Source hashes and schedules are recorded. Of the 38 outer groups, {counts.get(1,0)} have one unique age, {counts.get(2,0)} have two and {counts.get(3,0)} have three; many groups offer little arbitration headroom.

{chr(10).join(real_table)}

Real deltas average the paired cohort regret-factor differences over four cost ratios and two loggers. Battery CV reuses the battery cells and is sensitivity only. Primary results include six engine datasets and Battery LOBO. These frozen-fit retrospective cohort comparisons do not constitute a prospective maintenance deployment study.

## 8. Mechanism ablation

The sharp rectangle drops only cross-policy lifetime compatibility, retaining the same public inputs and individually sharp marginal bounds. It is the direct coupling ablation. Upper-rate selection retains censoring-aware bounds but optimizes absolute worst-case rate rather than relative regret. Complete-case selection discards unresolved outcomes and is a diagnostic, not the sole headline comparator. All four methods are stored for every case.

In the strict example with 12 unknown lifetimes, H=6, rho20 and ages8,12,16,24, exact selection chooses age8 with W=3; the sharp rectangle chooses age24, whose exact W=320/17, approximately18.824. Upper-rate selection chooses8 too. Therefore the distinction is strict against rectangular comparisons, but not a claim that every conventional selector must choose differently. Synthetic choices differ from rectangle in 1,463/2,400 cases and from upper-rate in 624/2,400; real choices differ in 32/304 and 23/304 respectively, including the CV sensitivity cases.

## 9. Stress tests and failure conditions

Checks cover equal and duplicate ages, permutation of assets and policies, exact deadline failures, fully observed collapse, public-only selection, unbounded compatible lifetimes and invalid inputs. Fully observed cohorts reduce to ordinary minimum-rate selection. A general endpoint-state optimizer reproduces the exact result without the specialized sorted-count formulas.

The method can be conservative when the Cartesian uncertainty set permits implausible lifetimes. Worst-case regret optimization can deliberately sacrifice actual average cost or failure risk, as the short-life experiments show. It cannot fix a poor candidate pool; with K=1 it has no headroom. Asset-specific ages and heterogeneous costs invalidate the count-only proof unless separately extended. These are identifiable limitations, not completed extensions.

## 10. Transfer findings

Battery LOBO shows no gain against either principal selector. No new-batch generalization or deployment guarantee is established. The deterministic certificate concerns the recorded cohort's compatible completions, not a fresh population or future batch. The earlier failed battery transfer remains a negative result.

## 11. Statistical analysis

The primary synthetic family has 48 two-sided paired sign tests: 24 setting cells times rectangle/upper-rate. Ties within 1e-12 are removed; the null is balanced signs among nonzero independent-cohort differences. Holm correction controls the family. At adjusted p<.05, 13 contrasts favor exact selection, 15 favor the baseline, and20 are not significant. These tests concern direction probabilities, not a null of equal means or scientific originality.

Each paired mean difference also has a 2,000-resample cohort bootstrap percentile interval, seed9102026. These intervals are nominal, not simultaneous, and conditional on each specified synthetic law/setting. Full means, standard deviations, medians, extremes, effects, wins/ties/losses and raw/adjusted p-values are retained in the output tables.

Real diagnostics average repeated cost/logger settings into one contrast per outer split. There are21 primary group comparisons and3 Battery CV sensitivity comparisons, corrected separately. None of the21 primary contrasts is significant. Source fits share training data across folds; these low-power conditional diagnostics are not an independent retraining or population transfer experiment.

Optimal W cannot be higher than W of a baseline's choice by construction. Average guaranteed factor reductions are {guarantee.sharp_rectangle:.6f} versus rectangle and {guarantee.upper_rate:.6f} versus upper-rate; they are deterministic objective differences, not evidence of statistical superiority.

## 12. Literature overlap

[LITERATURE.md](LITERATURE.md) compares ten primary works with formulation, overlap, differences and inspection limits. Minimax age replacement, nonparametric predictive replacement, shared trajectories, relative regret, robust policy comparison and fractional optimization are established. The July2026 block-replacement preprint already exploits censored lifetimes and nested observation; those ideas are not new claims here. No inspected source was found to give the exact ordered count formulas for this finite-cohort quotient, but that is not proof of priority.

## 13. Novelty attack

The strongest attack is that this is a structured special case of existing robust fractional optimization. That is true at the framework level. A defensible algorithm paper would need to establish that the exact two-count solution and its complexity for this model were not already derived, and that the restricted model matters. Generic optimization reproduction does not refute a specialized algorithm, but it prevents claiming a new general decision principle. The mechanism cannot be reproduced by the trivial sharp rectangle; the strict example demonstrates this limited distinction.

Timing is exploratory: generic/ordered median ratios are .44 at n4,1.43 at n8 and3.51 at n12. The specialized Python code is slower on the smallest cases. Larger ordered-count scaling is recorded to n160; it is not a controlled systems benchmark or evidence of a general practical speedup.

## 14. Final novelty verdict

**B: POTENTIALLY NOVEL BUT INSUFFICIENTLY ESTABLISHED.** Correctness and a method distinction have been established for the stated model. Historical originality and public priority have not. The strict final YES/NO answer is **NO: a genuinely novel method is not yet established to the required standard.** This reflects priority uncertainty and limited external validation, not a failed exactness test. Earlier rejected methods remain rejected.

## 15. Exact contribution statement

The project now contains an exact ordered failure-phase/count algorithm for finite-cohort minimax multiplicative replacement cost-rate regret from right-censored integer lifetimes, jointly coupling age policies through each asset's latent failure time and returning sharp attaining witnesses in O(K^2(n^2+n log n)) arithmetic operations. This is the precise **candidate computational contribution**; external novelty attribution remains provisional.

## 16. Proposed manuscript title

**Exact Relative-Regret Age Replacement from Censored Cohorts via Shared Failure Clocks**.

## 17. Draft abstract

Preventive replacement censors asset lifetimes, and separately bounded policy rates may combine incompatible failure-time completions. We study minimax multiplicative cost-rate regret among fixed integer age-replacement policies on a censored finite cohort. With a common failure-cost ratio, we derive exact pairwise adversarial comparisons by ordered failure phases and one or two failure counts, yielding a quadratic-in-cohort-size arithmetic search and attaining shared-lifetime witnesses without a physical life cap. Exhaustive enumeration and a separate general-state optimizer agree with the implementation. Evaluation on2,400 independent synthetic cohorts and304 frozen real tasks shows narrower worst-case comparisons and changed decisions, but mixed realized cost and risk outcomes:13 corrected synthetic comparisons favor the method and15 favor competing selectors. The result is a specialized exact robust optimizer, with historical priority and future-population performance requiring further validation.

## 18. Proposed paper contributions

1. A joint finite-cohort censored lifetime formulation exposing the incompatibility of separately attained marginal cost-rate bounds.
2. Two exact ordered failure-phase/count reductions with constructive adversarial witnesses and an explicit arithmetic-operation bound.
3. A reproducible exactness audit, coupling ablation and independent-cohort statistical evaluation that includes negative cost and risk results.

These are contributions of the current work product; the claim that they are original in the literature remains pending.

## 19. Reviewer objections and responses

- **Only a special case of robust optimization?** Yes. The proposed value is its exact structure, witnesses and complexity for a restricted maintenance model.
- **Why relative regret instead of mean cost?** It protects against choosing far above the same-world best candidate; it can lose on average. Use depends on the decision objective.
- **Why fixed ages rather than sensors?** Fixed ages make shared-clock compatibility observable and support the ordering proof. A sensor-policy extension is not proved.
- **Why no iid survival estimate?** The certificate is conditional and deterministic. Distributional prediction would answer a different question.
- **Why no established originality claim?** The targeted audit found no matching reduction, but its coverage is incomplete and no independent specialist has reviewed it.
- **Are real tests independent?** Repeated settings are aggregated and shared source-training dependence is disclosed. Prospective validation remains necessary.

## 20. Minimum remaining work for an established contribution

The conceptual pivot has been made; another ensemble or a better p-value is not the missing ingredient. The decisive remaining steps are an independent proof/equivalence audit in reliability and robust fractional optimization, a stronger runtime comparison against established exact solvers on realistically larger candidate pools, and prospective external-data evaluation of the chosen robust objective. A reviewed public disclosure with actual authorship is needed for an externally verifiable priority date. The [priority dossier](PRIORITY_DOSSIER.md) and hashed internal record make the present work reviewable but do not establish public priority.

Reproduction and completed integrity checks are documented in [README.md](README.md) and `out/clock_regret/completion_manifest.json`.
'''
    Path('clock_regret/REPORT.md').write_text(report, encoding='utf-8')
    print('Generated REPORT.md, strict_example.json and two PNG/SVG scientific figures.')


if __name__ == '__main__':
    main()
