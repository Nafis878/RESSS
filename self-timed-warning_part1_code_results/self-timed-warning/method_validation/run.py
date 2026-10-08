"""Conditional paired inference and an independent generic LP mechanism audit."""
from pathlib import Path
import hashlib
import json
import time
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.stats import binomtest

OUT = Path('out/method_validation')
OLD = Path('out/observability')
B = 2000
SEED = 20261008
ENDPOINTS = ['rate_low', 'rate_high', 'risk_low', 'risk_high']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protect():
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / 'protected_before.json'
    if dest.exists():
        hashes = json.loads(dest.read_text())
    else:
        hashes = json.loads((OLD / 'protected_before.json').read_text())
        for folder in [Path('observability'), OLD]:
            for p in folder.rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:
                    hashes[p.as_posix()] = sha(p)
        dest.write_text(json.dumps(hashes, indent=1), encoding='utf-8')
        (OUT / 'plan_sha256.txt').write_text(sha('method_validation/PLAN.md'))
    changed = [p for p, h in hashes.items() if sha(p) != h]
    if changed:
        raise AssertionError(('protected files changed', changed))
    return len(hashes)


def holm(p):
    p = np.asarray(p, float)
    idx = np.argsort(p)
    result = np.empty(len(p))
    result[idx] = np.minimum(1, np.maximum.accumulate(p[idx] * (len(p) - np.arange(len(p)))))
    return result


def generic_lp(c_known, t_known, fail_known, m, h_unknown, rho, cap, n):
    """Standard linear-fractional extrema over a rectangular feasible set.

    z=unknown failures, u=unknown total exposure, s=1/(t_known+u).
    Charnes-Cooper variables are (z*s, u*s, s). Binary z can be
    relaxed here because monotonicity puts both optima at integer endpoints.
    Strict u>sum(H) is replaced by its closure: upper is a supremum.
    """
    if not m:
        return np.array([c_known / t_known] * 2 + [fail_known / n] * 2)
    obj = np.array([rho - 1., 0., c_known + m])
    inequalities = [[1., 0., -m], [0., -1., h_unknown], [0., 1., -m * cap]]
    equality = [[0., 1., t_known]]
    options = {'threads': 1}
    # SciPy forwards this HiGHS option, but warns that it is not a SciPy option.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Unrecognized options detected')
        low = linprog(obj, A_ub=inequalities, b_ub=[0.] * 3,
                      A_eq=equality, b_eq=[1.], bounds=(0., None), method='highs', options=options)
        high = linprog(-obj, A_ub=inequalities, b_ub=[0.] * 3,
                       A_eq=equality, b_eq=[1.], bounds=(0., None), method='highs', options=options)
    if not low.success or not high.success:
        raise RuntimeError((low.message, high.message))
    return np.array([low.fun, -high.fun, fail_known / n, (fail_known + m) / n])


def matrix(g, field, units, tasks):
    return g.pivot(index='unit', columns='task', values=field).loc[units, tasks].to_numpy(float)


def summarize(sums, rho, n):
    kc, kt, kf, missing, missing_h, lc, lt, tc, tt, tf = sums
    logger = lc / lt
    truth = tc / tt
    upper = (kc + rho * missing) / (kt + missing_h)
    observed = n - missing
    with np.errstate(divide='ignore', invalid='ignore'):
        cc_rate = kc / kt
        cc_risk = kf / observed
    healthy_rate = (kc + missing) / (kt + missing_h)
    truth_gain = truth < logger - 1e-12
    cert_gain = upper < logger - 1e-12
    risk = tf / n
    hidden = (tf - kf) / n
    misses = truth_gain & ~cert_gain
    values = {
        'observed_fraction': observed / n,
        'hidden_failure_fraction': hidden,
        'true_gain_fraction': truth_gain,
        'certified_gain_fraction': cert_gain,
        'missed_gain_fraction': misses,
        'healthy_false_safe_fraction': (kf / n <= .05) & (risk > .05),
        'complete_case_false_safe_fraction': (cc_risk <= .05) & (risk > .05),
        'healthy_false_gain_fraction': (healthy_rate < logger - 1e-12) & ~truth_gain,
        'complete_case_false_gain_fraction': (cc_rate < logger - 1e-12) & ~truth_gain,
    }
    return {name: np.asarray(value, float).sum(axis=-1) for name, value in values.items()}


def main():
    start = time.monotonic()
    protected = protect()
    p = pd.read_csv(OLD / 'public_outcomes.csv.gz', dtype={'unit': str, 'split': str})
    t = pd.read_csv(OLD / 'sealed_truth.csv.gz', dtype={'unit': str, 'split': str})
    assert p[['task', 'unit']].equals(t[['task', 'unit']])
    for key in ['logger', 'target', 'dataset', 'analysis', 'split', 'lead', 'rho']:
        assert p[key].equals(t[key])
    p = p.join(t[['true_target_cost', 'true_target_use', 'true_target_fail']])
    assert p.loc[p.outcome_observed == 0, ['target_cost', 'target_use', 'target_fail']].isna().all().all()
    frozen = pd.read_csv(OLD / 'task_results.csv.gz')
    off = p[p.logger != p.target].copy()
    rng = np.random.default_rng(SEED)
    tests = []
    ci = []
    bootstrap_frames = []
    units_frames = []
    checks = []
    domain_sizes = {}

    for (dataset, analysis), d in off.groupby(['dataset', 'analysis'], sort=True):
        primary = not (dataset == 'Battery' and analysis == 'cv123')
        assert d.groupby('unit').split.nunique().max() == 1
        logger_means = d.groupby(['unit', 'logger']).outcome_observed.mean().unstack()
        unit_order = logger_means.index.to_numpy()
        n_assets = len(unit_order)
        domain_sizes[f'{dataset}/{analysis}'] = n_assets
        deltas = np.column_stack([logger_means['1SE'] - logger_means[other] for other in ['plain', 'CAT', 'CATc']])
        split_by_unit = d[['unit', 'split']].drop_duplicates().set_index('unit').loc[unit_order, 'split']
        weights = np.zeros((B, n_assets), dtype=np.int64)
        accumulated = None
        point = None
        total_tasks = 0
        for split, g in d.groupby('split', sort=True):
            units = np.sort(g.unit.unique())
            tasks = np.sort(g.task.unique())
            assert len(tasks) == 192
            assert len(g) == len(units) * len(tasks)
            n = len(units)
            w = rng.multinomial(n, np.full(n, 1 / n), size=B)
            positions = np.flatnonzero(split_by_unit.to_numpy() == split)
            assert np.array_equal(unit_order[positions], units)
            weights[:, positions] = w
            meta = g.drop_duplicates('task').set_index('task').loc[tasks]
            rho = meta.rho.to_numpy(float)
            o = matrix(g, 'outcome_observed', units, tasks)
            h = matrix(g, 'logger_endpoint', units, tasks)
            arrays = [
                np.nan_to_num(matrix(g, 'target_cost', units, tasks)),
                np.nan_to_num(matrix(g, 'target_use', units, tasks)),
                np.nan_to_num(matrix(g, 'target_fail', units, tasks)),
                1 - o, (1 - o) * h,
                matrix(g, 'logger_cost', units, tasks), h,
                matrix(g, 'true_target_cost', units, tasks),
                matrix(g, 'true_target_use', units, tasks),
                matrix(g, 'true_target_fail', units, tasks),
            ]
            sums = [a.sum(axis=0) for a in arrays]
            current_point = summarize(sums, rho, n)
            current_boot = summarize([w @ a for a in arrays], rho, n)
            if accumulated is None:
                accumulated = {k: np.zeros(B) for k in current_boot}
                point = {k: 0. for k in current_point}
            for name in current_point:
                point[name] += float(current_point[name])
                accumulated[name] += current_boot[name]
            total_tasks += len(tasks)

        delta_boot = weights @ deltas / n_assets
        for j, other in enumerate(['plain', 'CAT', 'CATc']):
            delta = deltas[:, j]
            positive = int((delta > 1e-12).sum())
            negative = int((delta < -1e-12).sum())
            nonzero = positive + negative
            pval = binomtest(positive, nonzero, .5).pvalue if nonzero else 1.
            lower, upper = np.quantile(delta_boot[:, j], [.025, .975])
            tests.append(dict(dataset=dataset, analysis=analysis, primary=primary,
                              contrast=f'1SE_minus_{other}', assets=n_assets,
                              positive=positive, negative=negative, ties=n_assets - nonzero,
                              mean_difference=float(delta.mean()), ci_low=lower, ci_high=upper,
                              p_raw=pval, null='P(positive | nonzero)=0.5', alternative='two-sided'))
            for unit, value in zip(unit_order, delta):
                units_frames.append(dict(dataset=dataset, analysis=analysis, unit=unit,
                                         split=split_by_unit.loc[unit], contrast=f'1SE_minus_{other}', value=value))

        for name in point:
            point[name] /= total_tasks
            accumulated[name] /= total_tasks
        point['missed_share_of_true_gains'] = point['missed_gain_fraction'] / point['true_gain_fraction']
        accumulated['missed_share_of_true_gains'] = accumulated['missed_gain_fraction'] / accumulated['true_gain_fraction']
        frame = pd.DataFrame(accumulated).assign(dataset=dataset, analysis=analysis, draw=np.arange(B))
        bootstrap_frames.append(frame)
        for name, value in point.items():
            lower, upper = np.quantile(accumulated[name], [.025, .975])
            ci.append(dict(dataset=dataset, analysis=analysis, primary=primary, metric=name,
                           estimate=value, lower=lower, upper=upper, assets=n_assets, tasks=total_tasks, draws=B,
                           interval_type=('nominal conditional 95% bootstrap CI' if name in
                                          ['observed_fraction', 'hidden_failure_fraction'] else
                                          'central 95% resampling sensitivity range'),
                           bootstrap_mean=float(accumulated[name].mean()),
                           point_outside_range=bool(value < lower or value > upper)))
        original = frozen[(frozen.dataset == dataset) & (frozen.analysis == analysis) &
                          (frozen.logger != frozen.target) & (frozen.cap == 5000)]
        for ours, theirs in [('observed_fraction', 'observed_fraction'),
                             ('certified_gain_fraction', 'certified_improvement'),
                             ('healthy_false_safe_fraction', 'healthy_false_safe'),
                             ('complete_case_false_safe_fraction', 'complete_case_false_safe'),
                             ('healthy_false_gain_fraction', 'healthy_false_improvement'),
                             ('complete_case_false_gain_fraction', 'complete_case_false_improvement')]:
            error = abs(point[ours] - original[theirs].mean())
            assert error < 1e-12, (dataset, analysis, ours, error)
            checks.append(dict(check='frozen_summary_agreement', dataset=dataset, analysis=analysis, metric=ours, error=error))
        print(f'Bootstrap complete: {dataset}/{analysis}; {n_assets} assets, {total_tasks} fixed tasks', flush=True)

    tests = pd.DataFrame(tests)
    for is_primary in [True, False]:
        mask = tests.primary == is_primary
        tests.loc[mask, 'p_holm'] = holm(tests.loc[mask, 'p_raw'])
        tests.loc[mask, 'family_size'] = int(mask.sum())
    assert (tests.primary.sum(), (~tests.primary).sum()) == (21, 3)
    tests.to_csv(OUT / 'paired_sign_tests.csv', index=False)
    pd.DataFrame(ci).to_csv(OUT / 'bootstrap_summary.csv', index=False)
    pd.DataFrame(units_frames).to_csv(OUT / 'paired_asset_contrasts.csv', index=False)
    boot = pd.concat(bootstrap_frames, ignore_index=True)
    boot.to_csv(OUT / 'bootstrap_draws.csv.gz', index=False)
    pd.DataFrame(checks).to_csv(OUT / 'point_summary_checks.csv', index=False)

    # Domain-balanced fixed-domain composite, excluding reused Battery CV cells.
    primary_boot = boot[~((boot.dataset == 'Battery') & (boot.analysis == 'cv123'))]
    metrics = [c for c in accumulated if c != 'missed_share_of_true_gains']
    composite = primary_boot.groupby('draw')[metrics].mean()
    composite['missed_share_of_true_gains'] = composite.missed_gain_fraction / composite.true_gain_fraction
    intervals = pd.DataFrame(ci)
    primary_points = intervals[intervals.primary].pivot(index=['dataset', 'analysis'], columns='metric', values='estimate')
    comp_point = primary_points[metrics].mean().to_dict()
    comp_point['missed_share_of_true_gains'] = comp_point['missed_gain_fraction'] / comp_point['true_gain_fraction']
    comp = []
    for name, value in comp_point.items():
        lower, upper = np.quantile(composite[name], [.025, .975])
        comp.append(dict(metric=name, estimate=value, lower=lower, upper=upper,
                         assets=1149, fixed_domains=7, draws=B,
                         interval_type=('nominal conditional 95% bootstrap CI' if name in
                                        ['observed_fraction', 'hidden_failure_fraction'] else
                                        'central 95% resampling sensitivity range'),
                         bootstrap_mean=float(composite[name].mean()),
                         point_outside_range=bool(value < lower or value > upper)))
    pd.DataFrame(comp).to_csv(OUT / 'fixed_domain_composite_summary.csv', index=False)

    # Independent optimization reconstruction of every earlier cap evaluation.
    p['known_c'] = p.target_cost.fillna(0)
    p['known_t'] = p.target_use.fillna(0)
    p['known_f'] = p.target_fail.fillna(0)
    p['missing'] = 1 - p.outcome_observed
    p['missing_h'] = p.missing * p.logger_endpoint
    stats = p.groupby('task').agg(c=('known_c', 'sum'), t=('known_t', 'sum'),
                                  f=('known_f', 'sum'), m=('missing', 'sum'),
                                  h=('missing_h', 'sum'), n=('unit', 'size'))
    audit = []
    for i, row in enumerate(frozen.itertuples(index=False), 1):
        s = stats.loc[row.task]
        values = generic_lp(s.c, s.t, s.f, s.m, s.h, row.rho, row.cap, s.n)
        old_values = np.array([getattr(row, name) for name in ENDPOINTS])
        error = np.max(np.abs(values - old_values))
        assert np.allclose(values, old_values, rtol=1e-8, atol=1e-10), (row.task, row.cap, error)
        cert_gain = bool(values[1] < row.logger_rate - 1e-12)
        cert_safe = bool(values[3] <= .05)
        assert cert_gain == row.certified_improvement and cert_safe == row.certified_safe
        audit.append(dict(task=row.task, cap=row.cap, max_abs_error=error,
                          generic_certified_improvement=cert_gain, generic_certified_safe=cert_safe,
                          lp_used=bool(s.m), **dict(zip(ENDPOINTS, values))))
        if i % 4000 == 0:
            print(f'Generic LP equivalence checked: {i}/{len(frozen)} cap evaluations', flush=True)
    audit = pd.DataFrame(audit)
    audit.to_csv(OUT / 'generic_lp_equivalence.csv.gz', index=False)
    result = dict(bootstrap_draws=B, seed=SEED, primary_sign_tests=21, sensitivity_sign_tests=3,
                  significant_primary_holm=int(((tests.p_holm < .05) & tests.primary).sum()),
                  primary_assets=1149, primary_domains=7, domain_sizes=domain_sizes,
                  lp_comparisons=len(audit), lp_solved_pairs=int(audit.lp_used.sum()),
                  endpoint_max_absolute_error=float(audit.max_abs_error.max()),
                  certification_mismatches=0, protected_files_unchanged=protect(),
                  prior_art_method_reproduced=True, methodological_novelty_established=False,
                  inference='post hoc, fixed-policy, asset-within-outer-split conditional inference',
                  elapsed_seconds=time.monotonic() - start)
    (OUT / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
