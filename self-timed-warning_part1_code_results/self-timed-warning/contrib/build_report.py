"""Build the final contribution report, tables and figure from a verified full suite."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('out/contrib')
ENG = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6']


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(str(x) for x in row) + ' |' for row in rows])


def main():
    audit = json.loads((ROOT / 'completion_audit.json').read_text())
    assert audit['complete'], 'Refusing to write a final verdict for an incomplete suite'
    n = json.loads((ROOT / 'contrib_numbers.json').read_text()); v = n['verdicts']
    risk, frag, costs, ms, feasibility = [], [], [], [], []
    for ds in ENG:
        d = n['ds'][ds]['all']
        for lead, r in d['validity']['CAT_a0.05'].items():
            risk.append([ds, lead, r['n'], r['failures'], round(100*r['rate'], 2), r['p'],
                         round(100*r['certifiable_share'], 1), 'rejected' if r['rejected'] else 'not rejected'])
        f = d['cost']['fragile_fold_cells']
        s = d['certifiable']
        feasibility.append([ds, f"{s['n_cf'][0]}–{s['n_cf'][1]}"] + [f"{s[k]}/{s['total']}" for k in ['cf','split','kmin','bonf']])
        frag.append([ds, d['cost']['fold_cells'], f['CATc_a0.05'], f['STW_cost'], f['STW_cost_1se'], f['STW_window']])
        costs.append([ds] + [f"{d['cost']['verdict'][p]['verdict']} ({d['cost']['verdict'][p]['wins']} wins, {d['cost']['verdict'][p]['losses']} losses)"
                              for p in ['STW_window', 'STW_cost', 'STW_cost_1se', 'age']])
        if 'M' in n['ds'][ds]:
            q = n['ds'][ds]['M']['by_q']['0.1']
            for p in ['P1_res_opt_mid', 'STW_window']:
                z = q[f'CATgc_a0.05-{p}']
                ms.append([ds, p, q['CATgc_a0.05']['M'], q[p]['M'], z['diff'], f"[{z['lo']}, {z['hi']}]", z['verdict']])
    risk_headers = ['Dataset', 'Lead', 'Units', 'Failures', 'Rate %', 'Screen p', 'Finite order statistic %', 'Screen']
    frag_headers = ['Dataset', 'Fold/cost cells', 'CAT-c', 'Plain cost', '1-SE', 'Window']
    cost_headers = ['Dataset', 'Versus window', 'Versus plain', 'Versus 1-SE', 'Versus age']
    m_headers = ['Dataset', 'Comparator', 'CAT-c M %', 'Comparator M %', 'Difference points', 'Paired 95% interval', 'Plan verdict']
    for name, h, rows in [('risk', risk_headers, risk), ('fragility', frag_headers, frag), ('cost_verdicts', cost_headers, costs), ('metric_M', m_headers, ms),
                           ('feasibility',['Dataset','CF calibration n','CF finite','SPLIT finite','KMIN finite','Bonferroni finite'],feasibility)]:
        pd.DataFrame(rows, columns=h).to_csv(ROOT / f'final_{name}.csv', index=False)
    b = []
    for group in ['cv', 'lobo']:
        d = n['ds']['Battery'][group]
        for lead, r in d['validity']['CAT_a0.05'].items():
            b.append([group, lead, r['n'], r['failures'], round(100*r['rate'], 2), round(100*r['certifiable_share'], 1),
                      'rejected' if r['rejected'] else 'not rejected'])
    bearing = [[a, z['n'], z['failures'], round(100*z['rate'], 2), f"{z['certifiable']}/{z['splits']}"] for a, z in n['bearing'].items()]
    sim = n['sim']; sm = pd.DataFrame(n['sim_m'])
    rare = sm[sm.policy.str.startswith('P1')]
    cm = rare.groupby('interval').coverage.agg(['min', 'max']).round(4)
    cov_table = table(['Interval', 'Minimum coverage %', 'Maximum coverage %'],
                      [[k, round(100*z['min'], 2), round(100*z['max'], 2)] for k,z in cm.iterrows()])
    validity_fails = len(ENG) - v['validity_holds_count']
    summary = (f"The pre-specified empirical verdict is **{v['primary_claim']}**. The 5% bare-CAT screening did not reject on "
               f"{v['validity_holds_count']}/6 engine datasets at every lead; it rejected on {validity_fails}/6. "
               f"CAT-c had fewer failure-containing cells than plain cost tuning on {v['fragility']['STW_cost']['count']}/6 datasets "
               f"and than 1-SE tuning on {v['fragility']['STW_cost_1se']['count']}/6.")
    text = f'''# Unit-level calibration of end-of-life alarms: contribution assessment

Completed {datetime.now(timezone(timedelta(hours=6))).strftime('%d %B %Y')} (Asia/Dhaka).

## Answer to the novelty question

**No confirmed novel methodological contribution is established by the current package.** There is a defensible empirical contribution and a potentially useful maintenance-specific trajectory formulation. Those should be claimed precisely. A new name, a new dataset comparison, or a passing synthetic conformal-rank check does not establish a new general method.

{summary}

The empirical plan verdict and the novelty verdict answer different questions. An empirical win would not make established conformal mathematics new; an empirical loss can still support a useful negative-result paper.

## Completed phases

| Phase | Completion and evidence |
| --- | --- |
| 0: contribution selection and prior-work check | `docs_contrib/LITERATURE_AUDIT.md`; primary papers/publisher pages checked on 7 October 2026. |
| 1: theory, unit tests and synthetic checks | Eight CAT tests passed. Saved simulation outputs/check logs retained and audited: {sim['validity_within']}/{sim['validity_cells']} certifiable validity cells within the specified MC tolerance; {n['sim_sel']['within_bound']}/{n['sim_sel']['cells']} high-cost selection cells within the bound. Added explicit KMIN check: {n['sim_kmin']['within']}/{n['sim_kmin']['cells']} cells at {n['sim_kmin']['replicates_per_cell']} replicates each. |
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

All real-data analyses are exploratory, with a plan hashed before the original run, not a formal preregistration. Outer folds use seed 2026; inner engine folds use 100+fold. Models are capped absolute-error gradient-boosted regressors with 500 iterations and causal regime-normalized features. Settings are chosen on training units. Costs use planned replacement cost 1, failure cost rho in {{5,10,20,50}}, engine lead times {{0,5,10,15}}, and corresponding battery leads in cycles. Primary alpha is 0.05. M uses a 10-cycle decision grid, zero lead and primary preventive/corrective cost ratio 0.1.

Every comparator is recomputed on the same Windows/Python platform as CAT, following Amendment 1. Frozen Linux baseline rows are not combined with the new fits. Three principal safeguards are compared: window tuning, the 1-SE cost rule, and trajectory calibration. Age replacement, health-indicator and quantile alarms, probability policies, per-time-step residual calibration and the remaining planned variants are in the machine-readable results.

### Engine risk screening at alpha = 0.05

{table(risk_headers, risk)}

These are the pre-specified one-sided binomial screens. “Not rejected” means insufficient evidence against the null in that screen; it does not prove the failure risk is at most 5%. Overlapping CV fits induce dependence, so pooled binomial p-values and intervals lack the usual independent-Bernoulli justification. A finite order statistic is an implementation flag, not proof that exchangeability holds.

### Calibration feasibility of the planned variants

{table(['Dataset','CF calibration n','CF finite','SPLIT finite','KMIN finite','Bonferroni finite'], feasibility)}

Counts are over the five folds and four lead times at alpha 0.05, before cost-ratio selection. KMIN requires enough calibration units in every member under the implementation's conservative flag. A maximum-threshold fallback may show zero failures while replacing very early; it is not a successful risk certificate. SPLIT/KMIN validity and their cost comparisons are retained in the full JSON. These comparisons and the original setting-selection/Bonferroni ablations do not change the primary verdict rules.

### Failure-containing fold/cost cells

{table(frag_headers, frag)}

Each dataset has five folds times sixteen lead/cost combinations. Counts compare robustness over this finite grid, not independent replications. The pre-specified criterion requires fewer cells on at least four of the six engine datasets.

### Paired cost comparisons

{table(cost_headers, costs)}

Per cell, a win/loss requires the paired 95% bootstrap interval for CAT-c/comparator cost-rate ratio to lie wholly below/above 1. “Beats” requires at least eight wins and no losses; “loses” requires at least eight losses and no wins; other patterns are mixed. All 16 individual ratios and intervals are in `contrib_numbers.json`. The bootstrap conditions on the realized fitted predictions, does not include training-set uncertainty, and has no across-cell multiplicity adjustment. Sparse failures can make percentile intervals unreliable, as the synthetic coverage study illustrates.

### Metric M at the primary ratio

{table(m_headers, ms)}

Negative differences favor CAT-c. Grid-perfect reference units are paired with each policy. These numbers belong to the new platform comparison and should not silently replace the historical values in paper6.

## Battery transfer and bearing sample size

{table(['Battery analysis', 'Lead cycles', 'Units', 'Failures', 'Rate %', 'Finite order statistic %', 'Screen'], b)}

Held-out battery batches probe distribution shift. The exchangeability assumption is not justified across manufacturing/test batches, regardless of whether a screen rejects. Fully nested preprocessing reconstructs each training subset's blocks and normalization; it avoids borrowing a held-out cell's life to set the time scale.

{table(['Bearing alpha', 'Units', 'Failures', 'Rate %', 'Finite-statistic folds'], bearing)}

With only 13–14 calibration bearings per outer fold, alpha 0.05 cannot be certified by the finite rank: at least 19 calibration units are needed. Fallback outcomes are therefore not evidence for a 5% guarantee. The bearing experiment is a small-sample limitation, not a confirmatory safety study.

## Secondary interval result

The paired influence interval for M keeps covariance with the grid-perfect reference, using standard ratio-estimator linearization. Its width is zero for the perfect policy, whose metric is identically zero. It did not solve rare-failure uncertainty. Across the saved probability-policy cases:

{cov_table}

These are nominal 95% intervals; low coverage is a negative finding. The same rare-failure issue affects the percentile bootstrap. The ratio linearization is not a novel theorem and should remain supplementary.

## Prior work and claim boundary

[Conformal Risk Control](https://arxiv.org/html/2208.02814v4) already treats monotone risks. [Conformal Lesion Segmentation](https://arxiv.org/abs/2510.17897) already calibrates critical thresholds per example. In maintenance, [Kumar et al.](https://link.springer.com/chapter/10.1007/978-3-032-29501-9_23) describe economic threshold selection within a conformal safe region, and [Almeida et al.](https://journals.sagepub.com/doi/10.1177/14759217261445819) optimize maintenance subject to a miss-rate constraint. Their publisher abstracts were accessible; their subscription full methods remain to be compared. Consequently, a broad first-method claim is unsupported.

The remaining candidate distinction is the explicit entire-life alarm score, with lead time and action-grid feasibility, evaluated against matched-information operational policies across domains. The package adds empirical evidence on the difference between alarm-window success, operational failure, renewal cost, finite-sample feasibility and transfer. That is a worthwhile empirical formulation and audit; it should not be sold as a new conformal rank theorem or as deployment certification for these implementations.

## Recommended manuscript claim

“We formulate trajectory-level critical scores for end-of-life threshold alarms and evaluate conformal calibration alongside window and cost tuning. A standard conformal rank argument gives a marginal guarantee for independently fixed alarm rules under exchangeability and feasible actions. Matched-information experiments examine where practical OOF/refitted variants reduce threshold fragility, where they incur cost or failure tradeoffs, and where small calibration samples or batch transfer invalidate a certification interpretation.”

The current evidence supports a careful empirical/negative-result contribution. A stronger methodological claim requires a fully independent calibration implementation and a detailed closest-method comparison, not additional test-set tuning. Publication suitability remains an editorial judgment.

## Reproduce and inspect

Use `.venv/Scripts/python.exe` with the pinned requirements and `OMP_NUM_THREADS=1`. `contrib/README.md` gives the run order. `out/contrib/completion_audit.json` records completeness checks and hashes. Per-unit cost/M rows, calibration settings/scores, selected settings, checkpoints, baseline equivalence and leakage logs are retained. `paper7/numbers.json` joins the historical evidence to the new contribution data with an explicit provenance key; the original paper6 evidence is preserved.
'''
    Path('docs_contrib/FINAL_REPORT.md').write_text(text, encoding='utf-8')
    p = Path('paper7'); p.mkdir(exist_ok=True)
    (p / 'contribution_assessment.md').write_text(text, encoding='utf-8')
    old = json.loads(Path('paper6/numbers.json').read_text())
    old['contrib'] = n; old['contrib_provenance'] = {'platform': 'Windows, Python 3.12.4; pinned numerical packages',
        'primary_plan': 'contrib/PLAN.md Amendment 1', 'guarantee_scope': n['interpretation'], 'audit': audit,
        'methodological_novelty_established': False}
    (p / 'numbers.json').write_text(json.dumps(old, indent=1) + '\n', encoding='utf-8')
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8), constrained_layout=True)
    for i, ds in enumerate(ENG):
        values = n['ds'][ds]['all']['validity']['CAT_a0.05']
        axes[0].plot([int(x) for x in values], [100*z['rate'] for z in values.values()], marker='o', label=ds)
    axes[0].axhline(5, color='black', linestyle='--', lw=1, label='Target 5%')
    axes[0].set(xlabel='Maintenance lead (cycles)', ylabel='Observed bare-CAT failure rate (%)', title='Empirical risk; exact certification not established')
    axes[0].set_xticks([0,5,10,15]); axes[0].legend(fontsize=8, ncol=2); axes[0].grid(alpha=.18)
    xx=np.arange(len(ENG)); width=.19
    for j,(key,label) in enumerate([('CATc_a0.05','CAT-c'),('STW_cost','Plain cost'),('STW_cost_1se','1-SE'),('STW_window','Window')]):
        vals=[n['ds'][d]['all']['cost']['fragile_fold_cells'][key] for d in ENG]
        axes[1].bar(xx+(j-1.5)*width,vals,width,label=label)
    axes[1].set_xticks(xx,ENG,rotation=25); axes[1].set(ylabel='Fold/cost cells with at least one failure',title='Fragility over 80 cells per dataset')
    axes[1].legend(fontsize=8); axes[1].grid(axis='y',alpha=.18); axes[1].set_axisbelow(True)
    fig.savefig(ROOT/'final_risk_fragility.png',dpi=180); fig.savefig(ROOT/'final_risk_fragility.svg'); plt.close(fig)
    (p/'README.md').write_text('# Contribution assessment\n\n`contribution_assessment.md` is the final research assessment, not a submission-ready rewrite. `numbers.json` retains all paper6 evidence and adds the `contrib` results with provenance. The historical manuscript is in `paper6/`; its text reproduced identically.\n', encoding='utf-8')
    print(summary)
    print('Final report, five tables, plot and paper7 evidence bundle written.')


if __name__ == '__main__': main()
