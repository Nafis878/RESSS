"""Second revision: summarise the matched fixed-time comparison (audit_fixed_matched.py), the battery analyses with a common
physical task and fully nested preprocessing (audit_battery_physical.py) and the battery cost analysis with the capacity-trend
baseline (audit_battery_cost2.py) into paper4/numbers.json = paper3/numbers.json + key 'rev4'.
Usage: python audit_summarize2.py [--frozen]   (fresh outputs in out/audit, or frozen copies in results/audit)
"""
import os, sys, json, gzip
import numpy as np, pandas as pd
from scipy.stats import binomtest, beta

A = 'results/audit' if '--frozen' in sys.argv else 'out/audit'


def F_(name):
    for c in (f'{A}/{name}', f'{A}/{name}.gz'):
        if os.path.exists(c): return c
    return None


def cp(k, n):
    return [round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0]


def mcn(a, b):
    x = int((a & ~b).sum()); y = int((~a & b).sum())
    return dict(only_a=x, only_b=y, p=float(binomtest(min(x, y), x + y, .5).pvalue) if x + y else 1.0)


R4 = {}
# ---------------------------------------------------------------- matched fixed-time comparison
if F_('fixed_matched.json'): R4['fixed_matched'] = json.load(open(F_('fixed_matched.json')))

# ---------------------------------------------------------------- battery, physical task, fully nested
NOTICE = [15, 30, 45, 60]
def bsumm(g):
    n = len(g); c = g.cls.value_counts(); k = int(c.get('IN', 0)); a = g[g.cls != 'MISSED']
    o = dict(IN=k, n=n, pct=round(100 * k / n, 1), ci=cp(k, n), late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)), missed=int(c.get('MISSED', 0)))
    if len(a):
        o.update(r_median=float(a.r_cycles.median()), r_p10=float(a.r_cycles.quantile(.1)), r_p90=float(a.r_cycles.quantile(.9)),
                 gross_early=int(((a.pred_cycles - a.r_cycles) < -39 - 30).sum()))
    for N in NOTICE:
        o[f'notice_ge{N}'] = round(100 * float(((g.cls != 'MISSED') & (g.r_cycles >= N)).mean()), 1)
        o[f'correct_notice_ge{N}'] = round(100 * float(((g.cls == 'IN') & (g.r_cycles >= N)).mean()), 1)
    return o

parts = [pd.read_csv(f) for f in (F_('battery_physical.csv'), F_('battery_physical_cv.csv'), F_('battery_physical_lobo.csv')) if f]
if parts:
    Bp = pd.concat(parts).drop_duplicates(subset=['analysis', 'split', 'variant', 'method', 'kappa', 'unit']); bp = {}
    rule = Bp[Bp.variant == 'rule_nested'].drop_duplicates('split').set_index('split').kappa.astype(int).to_dict()
    for (an, var, m, kap), g in Bp[Bp.variant == 'fixed_kappa'].groupby(['analysis', 'variant', 'method', 'kappa']):
        bp[f'{an}|fixed_kappa|{m}|{int(kap)}'] = bsumm(g)
    for (an, var), g in Bp[(Bp.variant != 'fixed_kappa') & (Bp.method == 'recipe')].groupby(['analysis', 'variant']):
        bp[f'{an}|{var}|recipe'] = bsumm(g); bp[f'{an}|{var}|recipe']['kappas'] = g.drop_duplicates('split').set_index('split').kappa.astype(int).to_dict()
        for sp, h in g.groupby('split'): bp[f'{an}|{var}|recipe|{sp}'] = bsumm(h)
    # capacity trend at the rule kappa of each outer split (same blocks as the rule-nested recipe)
    T = pd.concat([Bp[(Bp.variant == 'fixed_kappa') & (Bp.method == 'capacity_trend') & (Bp.split == sp) & (Bp.kappa == k)] for sp, k in rule.items()])
    for an, g in T.groupby('analysis'):
        bp[f'{an}|rule_kappa|capacity_trend'] = bsumm(g)
        for sp, h in g.groupby('split'): bp[f'{an}|rule_kappa|capacity_trend|{sp}'] = bsumm(h)
    for an in Bp.analysis.unique():
        a = Bp[(Bp.analysis == an) & (Bp.variant == 'rule_nested') & (Bp.method == 'recipe')].set_index('unit').cls == 'IN'
        b = T[T.analysis == an].set_index('unit').cls == 'IN'
        bp[f'{an}|rule_nested_vs_trend'] = mcn(a, b.reindex(a.index))
        for var in ('cv_selected',):
            c = Bp[(Bp.analysis == an) & (Bp.variant == var) & (Bp.method == 'recipe')].set_index('unit').cls == 'IN'
            bp[f'{an}|rule_nested_vs_{var}'] = mcn(a, c.reindex(a.index))
    bp['rule_kappa'] = rule
    # within-batch (CV by cell) against held-out batch, paired by cell, for every kappa convention
    for key, sel in (('rule_nested', lambda D: D[(D.variant == 'rule_nested') & (D.method == 'recipe')]),
                     ('cv_selected', lambda D: D[(D.variant == 'cv_selected') & (D.method == 'recipe')]),
                     *[(f'fixed_{k}', (lambda k: lambda D: D[(D.variant == 'fixed_kappa') & (D.method == 'recipe') & (D.kappa == k)])(k)) for k in (2, 3, 4, 5, 6)]):
        g = sel(Bp); a = g[g.analysis == 'cv123'].set_index('unit').cls == 'IN'; b = g[g.analysis == 'lobo'].set_index('unit').cls == 'IN'
        bp[f'cv_vs_lobo|{key}'] = mcn(a, b.reindex(a.index))
    # median life of each batch (cells b1*, b2*, b3*), exact
    lv = Bp.drop_duplicates('unit').set_index('unit').life_cycles
    bp['batch_life_median'] = {b: float(lv[lv.index.str.startswith(f'b{b}')].median()) for b in ('1', '2', '3')}
    rn = Bp[(Bp.variant == 'rule_nested') & (Bp.method == 'recipe')].drop_duplicates('split').set_index('split')
    bp['inner_kappas'] = rn.inner_kappas.astype(str).to_dict() if 'inner_kappas' in rn else {}
    R4['battery_physical'] = bp

# ---------------------------------------------------------------- battery cost with the capacity trend, CV and held-out batch
f = F_('cost_battery2.csv')
if f:
    C = pd.read_csv(f); rng = np.random.default_rng(2027); cb = {'verify_cv': None}
    old = F_('cost_Battery.csv')
    if old:
        O = pd.read_csv(old); a = C[C.analysis == 'cv123']; ok = True
        for pol in O.policy.unique():
            x = a[a.policy == pol].sort_values(['split', 'lead_cycles', 'rho', 'unit']); y = O[O.policy == pol].sort_values(['fold', 'lead_cycles', 'rho', 'unit'])
            ok &= len(x) == len(y) and np.allclose(x.cost.values, y.cost.values) and np.allclose(x.use.values, y.use.values)
        cb['verify_cv'] = bool(ok)
    POLS = ['STW_window', 'STW_cost', 'STW_cost_1se', 'Q10_cost_1se', 'capacity_cost', 'capacity_cost_1se', 'trend_window', 'trend_cost', 'trend_cost_1se', 'age']
    for an, ga in C.groupby('analysis'):
        cells = {}; pairs = {}
        for (lc, rho), g in ga.groupby(['lead_cycles', 'rho']):
            S = g.groupby('policy')[['cost', 'use', 'fail']].sum(); pf = S.loc['perfect_foresight', 'cost'] / S.loc['perfect_foresight', 'use']
            key = f'{int(lc)}|{int(rho)}'; cells[key] = {p: dict(ratio=round(float(s.cost / s.use / pf), 6), failures=int(s.fail)) for p, s in S.iterrows()}
            pc = g.pivot_table(index=['split', 'unit'], columns='policy', values='cost'); pu = g.pivot_table(index=['split', 'unit'], columns='policy', values='use')
            n = len(pc); idx = rng.integers(0, n, size=(2000, n))
            for a_, b_ in (('trend_cost_1se', 'STW_window'), ('trend_cost_1se', 'STW_cost_1se'), ('trend_cost', 'STW_cost'), ('trend_window', 'STW_window'), ('trend_cost_1se', 'capacity_cost_1se'), ('STW_window', 'age'), ('trend_cost_1se', 'age')):
                ra = pc[a_].values[idx].sum(1) / pu[a_].values[idx].sum(1); rb = pc[b_].values[idx].sum(1) / pu[b_].values[idx].sum(1); r = ra / rb
                point = (pc[a_].sum() / pu[a_].sum()) / (pc[b_].sum() / pu[b_].sum())
                pairs.setdefault(f'{a_}|{b_}', {})[key] = dict(ratio=round(float(point), 6), lo=round(float(np.percentile(r, 2.5)), 6), hi=round(float(np.percentile(r, 97.5)), 6))
        summ = {}
        for pr, d in pairs.items():
            v = sorted(x['ratio'] for x in d.values())
            summ[pr] = dict(a_sig_cheaper=sum(x['hi'] < 1 for x in d.values()), a_sig_dearer=sum(x['lo'] > 1 for x in d.values()), a_point_cheaper=sum(x['ratio'] < 1 for x in d.values()),
                            median=round((v[7] + v[8]) / 2, 6), min=v[0], max=v[-1])
        lead = {}
        for p in POLS:
            g = ga[(ga.policy == p) & (ga.lead_cycles == 0) & (ga.rho == 10)]
            if len(g) and p != 'age':
                r = g.rul_at_alarm.dropna(); lead[p] = dict(median=float(r.median()), p10=float(r.quantile(.1)), p90=float(r.quantile(.9)), failures=int(g.fail.sum()), n=len(g))
        cb[an] = dict(cells=cells, pairs=pairs, summary=summ, lead_0_10=lead,
                      failures_by_lead={p: {str(int(lc)): int(ga[(ga.policy == p) & (ga.lead_cycles == lc) & (ga.rho == 50)].fail.sum()) for lc in sorted(ga.lead_cycles.unique())} for p in POLS})
    R4['battery_cost2'] = cb

N = json.load(open('paper3/numbers.json')); N['rev4'] = R4
os.makedirs('paper4', exist_ok=True); json.dump(N, open('paper4/numbers.json', 'w'), indent=1, default=float)
print(json.dumps({k: (list(v.keys())[:12] if isinstance(v, dict) else v) for k, v in R4.items()}, indent=1, default=str)[:3000])
