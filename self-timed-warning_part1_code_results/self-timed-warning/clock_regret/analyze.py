"""Independent-cohort statistics and complete real-domain summaries."""
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from clock_regret.run import OUT
from clock_regret.core import select, worst_pair
from method_validation.run import holm


def paired(x, source):
    a = x[x.method == 'exact_shared_clock'].set_index('case')
    rows = []
    for baseline in ['sharp_rectangle', 'upper_rate', 'complete_case']:
        b = x[x.method == baseline].set_index('case').loc[a.index]
        assert a.index.equals(b.index)
        meta = a.drop(columns='method').copy()
        meta['baseline'] = baseline
        meta['relative_regret_difference'] = a.realized_relative_regret - b.realized_relative_regret
        meta['rate_difference'] = a.cost_rate - b.cost_rate
        meta['risk_difference'] = a.risk - b.risk
        meta['guaranteed_factor_reduction'] = b.exact_worst_relative_regret - a.exact_worst_relative_regret
        meta['choice_differs'] = a.selected_age != b.selected_age
        meta['baseline_selected_age'] = b.selected_age
        assert (meta.guaranteed_factor_reduction >= -1e-10).all()
        rows.append(meta.reset_index())
    p = pd.concat(rows, ignore_index=True)
    p.to_csv(OUT / f'{source}_paired.csv.gz', index=False)
    return p


def main():
    syn = pd.read_csv(OUT / 'synthetic_results.csv.gz')
    real = pd.read_csv(OUT / 'real_results.csv.gz', dtype={'split': str})
    sp = paired(syn, 'synthetic')
    rp = paired(real, 'real')
    tests = []
    rng = np.random.default_rng(9102026)
    for (setting, baseline), g in sp[sp.baseline != 'complete_case'].groupby(['setting_id', 'baseline']):
        delta = g.relative_regret_difference.to_numpy()
        wins = int((delta < -1e-12).sum())
        losses = int((delta > 1e-12).sum())
        total = wins + losses
        p = binomtest(wins, total, .5).pvalue if total else 1.
        resample = delta[rng.integers(0, len(delta), size=(2000, len(delta)))].mean(1)
        low, high = np.quantile(resample, [.025, .975])
        q = g.iloc[0]
        tests.append(dict(setting_id=int(setting), baseline=baseline, n=int(q.n),
                          logging_age=int(q.logging_age), rho=int(q.evaluation_rho), law=q.dataset,
                          independent_cohorts=len(delta), wins=wins, losses=losses, ties=len(delta) - total,
                          mean_relative_regret_difference=float(delta.mean()),
                          nominal_bootstrap_low=low, nominal_bootstrap_high=high,
                          mean_rate_difference=float(g.rate_difference.mean()),
                          mean_risk_difference=float(g.risk_difference.mean()),
                          mean_guaranteed_factor_reduction=float(g.guaranteed_factor_reduction.mean()),
                          choices_differ=int(g.choice_differs.sum()), p_raw=p,
                          null='independent balanced signs among nonzero paired cohort differences'))
    tests = pd.DataFrame(tests)
    assert len(tests) == 48
    tests['p_holm'] = holm(tests.p_raw)
    tests.to_csv(OUT / 'synthetic_paired_tests.csv', index=False)
    metrics = ['cost_rate', 'risk', 'realized_relative_regret', 'exact_worst_relative_regret', 'rectangle_worst_upper']
    syn.groupby(['dataset', 'n', 'logging_age', 'evaluation_rho', 'method'])[metrics].agg(['mean', 'std', 'median', 'min', 'max']).to_csv(OUT / 'synthetic_all_setting_summary.csv')
    syn.groupby(['dataset', 'method'])[metrics].mean().reset_index().to_csv(OUT / 'synthetic_law_summary.csv', index=False)
    real.groupby(['dataset', 'analysis', 'method'])[metrics].mean().reset_index().to_csv(OUT / 'real_domain_summary.csv', index=False)
    summary_metrics = ['relative_regret_difference', 'rate_difference', 'risk_difference',
                       'guaranteed_factor_reduction', 'choice_differs']
    rp.groupby(['dataset', 'analysis', 'baseline'])[summary_metrics].mean().reset_index().to_csv(OUT / 'real_paired_domain_summary.csv', index=False)
    # One contrast per outer group after averaging repeated cost/logging settings.
    splits = rp.groupby(['dataset', 'analysis', 'split', 'baseline'])[summary_metrics].mean().reset_index()
    splits.to_csv(OUT / 'real_outer_split_contrasts.csv', index=False)
    group_tests = []
    for (ds, an, baseline), g in splits.groupby(['dataset', 'analysis', 'baseline']):
        d = g.relative_regret_difference.to_numpy()
        wins = int((d < -1e-12).sum())
        losses = int((d > 1e-12).sum())
        nz = wins + losses
        group_tests.append(dict(dataset=ds, analysis=an, baseline=baseline,
                                primary_regime=not (ds == 'Battery' and an == 'cv123'),
                                outer_splits=len(g), wins=wins, losses=losses, ties=len(g) - nz,
                                mean_relative_regret_difference=float(d.mean()),
                                p_raw=binomtest(wins, nz, .5).pvalue if nz else 1.))
    gt = pd.DataFrame(group_tests)
    for flag in [True, False]:
        mask = gt.primary_regime == flag
        gt.loc[mask, 'p_holm'] = holm(gt.loc[mask, 'p_raw'])
    gt.to_csv(OUT / 'real_outer_split_tests.csv', index=False)

    audit = pd.read_csv(OUT / 'independent_oracle_audit.csv')
    # Representative constant-time/kernel timing, not a statistical speed theorem.
    audit['generic_over_fast_runtime'] = audit.generic_seconds / audit.fast_seconds
    audit.groupby('n')[['fast_seconds', 'generic_seconds', 'generic_over_fast_runtime', 'count_cases', 'generic_transitions']].median().reset_index().to_csv(OUT / 'oracle_runtime_summary.csv', index=False)
    scaling = []
    rng2 = np.random.default_rng(20261010)
    for n in [10, 20, 40, 80, 160]:
        for repeat in range(5):
            h = rng2.integers(1, 25, n)
            failed = rng2.random(n) < .2
            start = time.perf_counter()
            ans = worst_pair(h, failed, 40, 20, 20)
            seconds = time.perf_counter() - start
            scaling.append(dict(n=n, repeat=repeat, seconds=seconds, count_cases=ans.count_cases,
                                worst_factor=float(ans.ratio)))
    pd.DataFrame(scaling).to_csv(OUT / 'scaling.csv', index=False)
    findings = dict(
        synthetic_independent_cohorts=2400, synthetic_tests=48,
        synthetic_holm_significant_better=int(((tests.p_holm < .05) & (tests.mean_relative_regret_difference < 0)).sum()),
        synthetic_holm_significant_worse=int(((tests.p_holm < .05) & (tests.mean_relative_regret_difference > 0)).sum()),
        synthetic_holm_not_significant=int((tests.p_holm >= .05).sum()),
        synthetic_choices_differ_rectangle=int(sp[sp.baseline == 'sharp_rectangle'].choice_differs.sum()),
        synthetic_choices_differ_upper_rate=int(sp[sp.baseline == 'upper_rate'].choice_differs.sum()),
        real_cases=int(real.case.nunique()),
        real_choices_differ_rectangle=int(rp[rp.baseline == 'sharp_rectangle'].choice_differs.sum()),
        real_choices_differ_upper_rate=int(rp[rp.baseline == 'upper_rate'].choice_differs.sum()),
        real_primary_group_tests_significant=int(((gt.p_holm < .05) & gt.primary_regime).sum()),
        generic_oracle_matches=120, protected_artifacts='read-only inputs',
        population_superiority_established=False, specific_algorithm_priority_established=False)
    (OUT / 'findings.json').write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print(json.dumps(findings, indent=2))
    print(tests.groupby('baseline')[['mean_relative_regret_difference', 'mean_guaranteed_factor_reduction']].mean().to_string())


if __name__ == '__main__':
    main()
