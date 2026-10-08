"""Aggregate the revision experiments (rev_experiments.py) into tables.
T_R1R2: in-window rates per dataset and H for STW, STW_const, HI_threshold; exact McNemar vs STW; share of warnings with
        >= 13 true cycles left (early limit can bind); reproduction check of STW against the original result files.
T_R3:   pooled long-run cost rate relative to perfect foresight per policy, (lead, rho); paired cluster bootstrap
        (units resampled within dataset, fitted policies fixed) of cost-rate ratios STW_cost / HI_cost and STW_cost / age.
"""
import os, sys, json, numpy as np, pandas as pd
from scipy.stats import binomtest
DS = [d for d in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'Battery'] if os.path.exists(f'out/rev/{d}_window.csv')]
ORIG = {'PHM08': 'results/window/first_warning_v2_PHM08.csv', 'FD001': 'results/window/first_warning_v2_FD001.csv',
        'FD002': 'results/window/first_warning_v2_FD002.csv', 'FD003': 'results/window/first_warning_v2_FD003.csv',
        'FD004': 'results/window/first_warning_v2_FD004.csv'}


def mcn(a, b):
    x = int((a & ~b).sum()); y = int((~a & b).sum())
    return x, y, (float(binomtest(min(x, y), x + y, .5).pvalue) if x + y else 1.0)


def window_tables():
    rows, repro = [], []
    for ds in DS:
        Wd = pd.read_csv(f'out/rev/{ds}_window.csv')
        o = None
        if ds in ORIG: o = pd.read_csv(ORIG[ds])
        elif ds == 'NCMAPSS6':
            o = pd.read_csv('results/ncm/warning_results.csv'); o = o[(o.method == 'warning') & (o.split.str.startswith('cv'))]
        elif ds == 'Battery':
            o = pd.read_csv('results/battery/warning_results.csv'); o = o[(o.method == 'warning') & (o.analysis == 'cv123')]
        if o is not None:
            s = Wd[Wd.method == 'STW']
            m = s.merge(o, on=['unit', 'H'], suffixes=('', '_o'))
            same = (m.cls == m.cls_o).all() and np.allclose(m.pred.fillna(-1), m.pred_o.fillna(-1))
            repro.append(dict(dataset=ds, rows=len(m), identical=bool(same)))
        for H, g in Wd.groupby('H'):
            P = g.pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'
            Y = g.pivot_table(index='unit', columns='method', values='y', aggfunc='first')
            for meth in ['STW', 'STW_const', 'HI_threshold']:
                gm = g[g.method == meth]; n = len(gm); k = int((gm.cls == 'IN').sum())
                r = dict(dataset=ds, H=H, method=meth, n=n, IN=k, pct=round(100 * k / n, 1),
                         late_missed=int(gm.cls.isin(['LATE', 'MISSED']).sum()), early=int((gm.cls == 'EARLY').sum()),
                         median_left=float(gm.y.median()), bind_pct=round(100 * (gm.y >= 13).sum() / max(1, gm.y.notna().sum()), 1))
                if meth != 'STW':
                    x, y, p = mcn(P['STW'], P[meth]); r.update(only_STW=x, only_other=y, p=round(p, 4))
                rows.append(r)
    return pd.DataFrame(rows), pd.DataFrame(repro)


def cost_tables(B=2000, seed=2026):
    rows, boot = [], []
    rng = np.random.default_rng(seed)
    for ds in DS:
        C = pd.read_csv(f'out/rev/{ds}_cost.csv')
        for (l, rho), g in C.groupby(['lead', 'rho']):
            S = g.groupby('policy')[['cost', 'use', 'fail']].sum(); pf = S.loc['perfect_foresight', 'cost'] / S.loc['perfect_foresight', 'use']
            for pol, s in S.iterrows():
                rows.append(dict(dataset=ds, lead=l, rho=rho, policy=pol, rate_vs_pf=round((s.cost / s.use) / pf, 3), failures=int(s.fail), n=int((g.policy == pol).sum())))
            # paired bootstrap over units
            piv_c = g.pivot_table(index=['fold', 'unit'], columns='policy', values='cost'); piv_u = g.pivot_table(index=['fold', 'unit'], columns='policy', values='use')
            n = len(piv_c); idx = rng.integers(0, n, size=(B, n))
            cc, uu = piv_c.values, piv_u.values; cols = list(piv_c.columns)
            def ratio(a, b, I=None):
                ia, ib = cols.index(a), cols.index(b)
                if I is None: return (cc[:, ia].sum() / uu[:, ia].sum()) / (cc[:, ib].sum() / uu[:, ib].sum())
                return (cc[I, ia].sum(1) / uu[I, ia].sum(1)) / (cc[I, ib].sum(1) / uu[I, ib].sum(1))
            for a, b in [('STW_window', 'HI_cost'), ('STW_window', 'age'), ('STW_window', 'STW_cost'), ('STW_cost', 'HI_cost'), ('STW_cost', 'age'), ('HI_cost', 'age')]:
                r = ratio(a, b, idx); lo, hi = np.percentile(r, [2.5, 97.5])
                boot.append(dict(dataset=ds, lead=l, rho=rho, a=a, b=b, ratio=round(ratio(a, b), 3), ci_lo=round(lo, 3), ci_hi=round(hi, 3),
                                 a_better=bool(hi < 1), b_better=bool(lo > 1)))
    return pd.DataFrame(rows), pd.DataFrame(boot)


if __name__ == '__main__':
    os.makedirs('out/rev/tables', exist_ok=True)
    T1, R = window_tables(); T1.to_csv('out/rev/tables/window_controls.csv', index=False); R.to_csv('out/rev/tables/reproduction_check.csv', index=False)
    T3, BT = cost_tables(); T3.to_csv('out/rev/tables/cost_rates.csv', index=False); BT.to_csv('out/rev/tables/cost_bootstrap.csv', index=False)
    pd.set_option('display.width', 250)
    print(R.to_string(index=False))
    print(T1[T1.H.isin([10, 20])].to_string(index=False))
    print(T3.pivot_table(index=['dataset', 'lead', 'rho'], columns='policy', values='rate_vs_pf').loc[(slice(None), [0, 10], slice(None)), :].to_string())
    print(BT[BT.lead.isin([0, 10])].to_string(index=False))
