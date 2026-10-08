"""Phase 3: robustness of direct threshold optimisation (their Fig. 9a on my data). Plan: kam/PHASE3_4_PLAN.md, P3.2.
Computed from the per-split series saved by kam_fd001.py (out/kam/ckpt/<ds>_<protocol>_<split>_series.pkl) and the
per-unit outputs (out/kam/<ds>_<protocol>_units.csv); nothing is refitted.

Usage: python kam/kam_fragility.py
Outputs (out/kam/): fragility_p1.csv (policy 1: per test set, ratio and probability model, the optimised thresholds, the
smallest threshold with a training / test failure, test failures and M at p_mid and p_max), fragility_stw.csv (plain and
1-SE cost-tuned STW: selected threshold tau and the largest tau with a test failure), fragility_tally.csv (cells with >= 1
test failure and with M > 50 % per policy, dataset and protocol), fragility_tie.csv (decisions differing between the
'mid' and 'max' tie rules), fragility_verdict.csv (decision rule of the plan), fragility_curve.csv (FD001 fold 1,
c_p/c_c = 0.01: training and test M over the threshold grid), fragility_summary.md
"""
import os, sys, glob, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.getcwd())
import kam_metric as K

DT = 10.0; QS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8]; SMALL = [0.01, 0.02, 0.05, 0.1]
PGRID = np.unique(np.round(np.concatenate([np.logspace(-4, 0, 400), np.arange(1, 1001) / 1000]), 12))
TAUS = np.arange(1, 61, 1.0)
OUT = 'out/kam'; DSS = ['fd001', 'fd002', 'fd003', 'fd004']


def p1_curve(G, L):
    """replacement time of every unit for every threshold in PGRID (first grid point where the running max reaches p)"""
    U = list(G); TR = np.full((len(U), len(PGRID)), np.inf); LL = np.array([L[u] for u in U], float)
    for i, u in enumerate(U):
        g = G[u]
        if len(g):
            cm = np.maximum.accumulate(g); j = np.searchsorted(cm, PGRID, side='left'); TR[i] = np.where(j < len(g), (j + 1) * DT, np.inf)
    return U, TR, LL


def curve_stats(TR, LL, cc):
    prev = TR < LL[:, None]; C = np.where(prev, 1.0, cc).sum(0); T = np.where(prev, TR, LL[:, None]).sum(0)
    Rp = K.r_perfect(LL, DT, 1.0, cc)[0]; return C / T / Rp - 1.0, (~prev).sum(0)


def tie(r):
    rmin = r.min(); t = np.flatnonzero(r <= rmin * (1 + 1e-12)); return t[len(t) // 2], t[-1], t[0]


def main():
    p1, stw, curves = [], [], []
    for f in sorted(glob.glob(f'{OUT}/ckpt/*_series.pkl')):
        b = os.path.basename(f).replace('_series.pkl', ''); ds, prot, split = b.split('_'); split = int(split)
        S = pickle.load(open(f, 'rb')); TF = np.asarray(S['TF'], float)
        Lte = dict(zip(S['test_u'], TF))
        for model in ('cls', 'res'):
            Ut, TRtr, Ltr = p1_curve(S[f'G{model}_oof'], S['Loof'])
            Uv, TRte, Lv = p1_curve(S[f'G{model}_te'], Lte)
            for q in QS:
                cc = 1.0 / q
                mtr, ftr = curve_stats(TRtr, Ltr, cc)
                rtr = (np.where(TRtr < Ltr[:, None], 1.0, cc).sum(0)) / (np.where(TRtr < Ltr[:, None], TRtr, Ltr[:, None]).sum(0))
                jm, jx, jn = tie(rtr); mte, fte = curve_stats(TRte, Lv, cc)
                pf_tr = PGRID[np.argmax(ftr > 0)] if (ftr > 0).any() else np.nan
                pf_te = PGRID[np.argmax(fte > 0)] if (fte > 0).any() else np.nan
                jq = int(np.searchsorted(PGRID, q - 1e-12))
                p1.append(dict(ds=ds, protocol=prot, split=split, q=q, model=model, p_mid=PGRID[jm], p_max=PGRID[jx], p_min=PGRID[jn], n_tied=int(jx - jn + 1),
                               p_fail_train=pf_tr, p_fail_test=pf_te, train_fail_mid=int(ftr[jm]), train_fail_max=int(ftr[jx]),
                               test_fail_mid=int(fte[jm]), test_fail_max=int(fte[jx]), test_fail_q=int(fte[jq]), M_mid=100 * mte[jm], M_max=100 * mte[jx],
                               margin_log10_mid=np.log10(pf_te / PGRID[jm]) if np.isfinite(pf_te) else np.nan,
                               margin_log10_max=np.log10(pf_te / PGRID[jx]) if np.isfinite(pf_te) else np.nan,
                               plateau_to_train_cliff=np.log10(pf_tr / PGRID[jx]) if np.isfinite(pf_tr) else np.nan))
                if ds == 'fd001' and prot == 'cv' and split == 1 and q == 0.01:
                    for j, p in enumerate(PGRID):
                        curves.append(dict(model=model, p=p, M_train=100 * mtr[j], fail_train=int(ftr[j]), M_test=100 * mte[j], fail_test=int(fte[j]),
                                           p_mid=PGRID[jm], p_max=PGRID[jx], p_fail_train=pf_tr, n_train=len(Ltr), n_test=len(Lv)))
        for (name, q), (key, j, ttr, tte) in S['sel'].items():
            U, ok, ya, ta, L = tte; cc = 1.0 / q
            g = np.where(ok, np.ceil(np.nan_to_num(ta, nan=0.0) / DT) * DT, np.inf); g = np.where(g < DT, DT, g)
            fail = (~(ok & (g < L[:, None]))).sum(0)
            jf = np.flatnonzero(fail > 0); tau_fail = float(TAUS[jf.max()]) if len(jf) else np.nan
            stw.append(dict(ds=ds, protocol=prot, split=split, q=q, policy=name, key=str(key), tau_sel=float(TAUS[j]), test_fail=int(fail[j]), tau_fail_test=tau_fail,
                            margin_cycles=float(TAUS[j]) - tau_fail if np.isfinite(tau_fail) else np.nan))
    P1, ST = pd.DataFrame(p1), pd.DataFrame(stw)
    P1.to_csv(f'{OUT}/fragility_p1.csv', index=False); ST.to_csv(f'{OUT}/fragility_stw.csv', index=False)
    pd.DataFrame(curves).to_csv(f'{OUT}/fragility_curve.csv', index=False)

    # ---- tallies from the per-unit outputs
    POL = ['P1_cls_opt_mid', 'P1_cls_opt_max', 'P1_cls_q', 'P1_res_opt_mid', 'P1_res_opt_max', 'P1_res_q', 'STW_cost', 'STW_cost_1se', 'STW_window', 'HI_cost', 'P3_res60', 'age_grid']
    tal, tiecnt = [], []
    for ds in DSS:
        for prot in ('cv', 'rs'):
            fs = sorted(glob.glob(f'{OUT}/{ds}_{prot}*_units.csv'))
            if not fs and ds == 'fd001' and prot == 'rs' and os.path.exists('results/kam/fd001_rs_policies_by_split.csv'):
                # 30 splits not re-run: tallies from the frozen Phase 2 per-split table (same per-split M and failures)
                Fz = pd.read_csv('results/kam/fd001_rs_policies_by_split.csv')
                for r in Fz[Fz.policy.isin(POL)].itertuples(): tal.append(dict(ds=ds, protocol=prot, split=r.split, q=r.q, policy=r.policy, failures=int(r.failures), M_pct=float(r.M_pct)))
                continue
            if not fs: continue
            D = pd.concat([pd.read_csv(x) for x in fs]); D = D[D.protocol == prot]
            for (split, q), g in D.groupby(['split', 'q']):
                TFv = g[g.policy == 'perfect_grid'].sort_values('unit').TF.values
                for pol in POL:
                    h = g[g.policy == pol].sort_values('unit')
                    if not len(h): continue
                    M = K.m_hat(h.cost.values, h.tlc.values, TFv, DT, 1.0, 1.0 / q, f'frag {ds} {pol}')
                    tal.append(dict(ds=ds, protocol=prot, split=split, q=q, policy=pol, failures=int(h.fail.sum()), M_pct=100 * M))
                for m in ('cls', 'res'):
                    a = g[g.policy == f'P1_{m}_opt_mid'].sort_values('unit'); b = g[g.policy == f'P1_{m}_opt_max'].sort_values('unit')
                    tiecnt.append(dict(ds=ds, protocol=prot, split=split, q=q, model=m, decisions=len(a), differ=int((a.TR.values != b.TR.values).sum()),
                                       M_mid=100 * K.m_hat(a.cost.values, a.tlc.values, TFv, DT, 1.0, 1.0 / q), M_max=100 * K.m_hat(b.cost.values, b.tlc.values, TFv, DT, 1.0, 1.0 / q)))
    T = pd.DataFrame(tal); TI = pd.DataFrame(tiecnt)
    TA = T.assign(small=T.q.isin(SMALL)).groupby(['ds', 'protocol', 'policy']).apply(lambda x: pd.Series(dict(
        cells=len(x), cells_fail=int((x.failures > 0).sum()), cells_M50=int((x.M_pct > 50).sum()),
        cells_small=int(x.small.sum()), cells_fail_small=int((x.small & (x.failures > 0)).sum()), cells_M50_small=int((x.small & (x.M_pct > 50)).sum()),
        failures_total=int(x.failures.sum()), M_max=float(x.M_pct.max())))).reset_index()
    TA.to_csv(f'{OUT}/fragility_tally.csv', index=False); T.to_csv(f'{OUT}/fragility_cells.csv', index=False)
    TIs = TI.groupby(['ds', 'protocol', 'model']).agg(decisions=('decisions', 'sum'), differ=('differ', 'sum'), max_abs_M_diff=('M_mid', lambda s: 0.0)).reset_index()
    TIs['max_abs_M_diff'] = [float((TI[(TI.ds == r.ds) & (TI.protocol == r.protocol) & (TI.model == r.model)].eval('M_mid - M_max').abs().max())) for r in TIs.itertuples()]
    TIs.to_csv(f'{OUT}/fragility_tie.csv', index=False)

    # ---- decision rule of the plan (five-fold, ratios <= 0.1)
    V = []
    for ds in DSS:
        for prot in ('cv', 'rs'):
            t = TA[(TA.ds == ds) & (TA.protocol == prot)].set_index('policy')
            if not len(t): continue
            comp = [('P1_cls_opt_mid', 'P1_cls_q'), ('P1_res_opt_mid', 'P1_res_q'), ('STW_cost', 'STW_cost_1se')]
            res = {f'{a}_vs_{b}': f'{int(t.loc[a, "cells_fail_small"])} vs {int(t.loc[b, "cells_fail_small"])}' for a, b in comp}
            sup = all(t.loc[a, 'cells_fail_small'] > t.loc[b, 'cells_fail_small'] for a, b in comp)
            V.append(dict(ds=ds, protocol=prot, **res, verdict=('supported' if sup else 'weakened') + (' (descriptive)' if prot == 'rs' else '')))
    VV = pd.DataFrame(V); VV.to_csv(f'{OUT}/fragility_verdict.csv', index=False)

    L = ['# Phase 3: robustness of direct threshold optimisation (exploratory; plan hashed before the run)', '',
         '## Decision rule (cells with >= 1 test failure at c_p/c_c <= 0.1: optimised vs counterpart)', '', VV.to_markdown(index=False), '',
         '## Tallies', '', TA.to_markdown(index=False), '', '## Tie rules', '', TIs.to_markdown(index=False), '',
         '## Policy 1 thresholds (median over test sets)', '',
         P1.groupby(['ds', 'protocol', 'model', 'q']).agg(p_mid=('p_mid', 'median'), p_max=('p_max', 'median'), p_fail_train=('p_fail_train', 'median'),
                                                          p_fail_test=('p_fail_test', 'median'), sets_fail_mid=('test_fail_mid', lambda s: int((s > 0).sum())),
                                                          sets_fail_max=('test_fail_max', lambda s: int((s > 0).sum())), sets=('split', 'size')).reset_index().to_markdown(index=False), '',
         '## Plain and 1-SE cost-tuned STW thresholds (median)', '',
         ST.groupby(['ds', 'protocol', 'policy', 'q']).agg(tau_sel=('tau_sel', 'median'), tau_fail_test=('tau_fail_test', 'median'), margin=('margin_cycles', 'median'),
                                                          sets_fail=('test_fail', lambda s: int((s > 0).sum())), sets=('split', 'size')).reset_index().to_markdown(index=False)]
    open(f'{OUT}/fragility_summary.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L[:12]))
    if any(v[1] < -K.TOL for v in K.VIOLATIONS if not str(v[0]).startswith('frag')): print('recorded violations:', K.VIOLATIONS)


if __name__ == '__main__':
    main()
