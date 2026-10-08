"""Stacked hybrid with external training engines (C-MAPSS FD002 added to the FIT engines of every fold).
Adds two base models -- GBM(+FD002) and physics-informed Bayesian(+FD002) -- computed on the same calibration rows
(16 life stages) and test rows (half of life) as base_preds_PHM08.csv, then reruns the stacker of ablate_hybrid.py."""
import json, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from safe_common import load_dataset, outer_folds, fit_cal_split
from feats import regime_stats, zmat, causal_feats
from bayes_phys import BayesDeg
phm, _, _ = load_dataset('PHM08'); fd2, _, _ = load_dataset('FD002'); fd2 = fd2.copy(); fd2['unit'] += 10000
B = pd.read_csv('out/window/base_preds_PHM08.csv'); units = np.sort(phm.unit.unique()); out = []
for fold, test_u in enumerate(outer_folds(units), 1):
    fit_u, cal_u = fit_cal_split(np.setdiff1d(units, test_u)); tr = pd.concat([phm, fd2])
    fit_all = np.concatenate([fit_u, fd2.unit.unique()]); st, keep = regime_stats(tr[tr.unit.isin(fit_all)])
    Z = {u: np.nan_to_num(zmat(g, st, keep)) for u, g in tr.groupby('unit')}
    X = np.vstack([causal_feats(Z[u]) for u in fit_all]); y = np.concatenate([tr[tr.unit == u].rul.values for u in fit_all])
    m = HistGradientBoostingRegressor(loss='absolute_error', max_iter=400, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=40, random_state=0).fit(X, y)
    Xh, yh = [], []
    for u in fit_all:
        L = len(Z[u]); f = np.arange(1, L + 1) / L; m0, m1 = f <= 0.2, f >= 0.95; Xh += [Z[u][m0], Z[u][m1]]; yh += [np.zeros(m0.sum()), np.ones(m1.sum())]
    Xh, yh = np.vstack(Xh), np.concatenate(yh); w = np.linalg.solve(Xh.T @ Xh + np.eye(Xh.shape[1]), Xh.T @ (yh - yh.mean()))
    c0 = np.mean(np.concatenate([Z[u][:20] @ w for u in fit_all])); H = {u: Z[u] @ w - c0 for u in Z}
    bd = BayesDeg().fit({u: H[u] for u in fit_all})
    R = B[B.fold == fold][['fold', 'unit', 'role', 'stage', 't']].copy(); CF = {}
    g2, q = [], []
    for u, t in zip(R.unit, R.t):
        if u not in CF: CF[u] = causal_feats(Z[u])
        g2.append(m.predict(CF[u][t - 1:t])[0]); r, wt = bd.rul_dist(H[u][:t]); o = np.argsort(r); q.append(np.interp([0.05, 0.5, 0.95], np.cumsum(wt[o]), r[o]))
    R['gbm_x'] = g2; R[['bayes_x_q05', 'bayes_x_q50', 'bayes_x_q95']] = np.array(q); out.append(R); print('fold', fold, flush=True)
X_ = pd.concat(out); X_.to_csv('out/window/ext_preds_PHM08.csv', index=False)
src = open('ablate_hybrid.py').read().split("T = D[D.role == 'test']")[0]; exec(src)
D = D.merge(X_, on=['fold', 'unit', 'role', 'stage', 't']); assert D.gbm_x.notna().all()
GROUPS['gbm_ext'] = ['gbm_x']; GROUPS['bayes_ext'] = ['bayes_x_q05', 'bayes_x_q50', 'bayes_x_q95']
ALL = sum(GROUPS.values(), []); res = {}
T = D[D.role == 'test']; res['single_gbm_ext'] = summ(T.gbm_x, T.y); res['single_bayes_ext'] = summ(T.bayes_x_q50, T.y)
P, cv = run(ALL, 'gbm_quantile'); res['hybrid_with_external'] = dict(cal_cv_hit=round(100 * cv, 1), **summ(P.pred, P.y))
P.to_csv('out/window/hybrid_external_half_PHM08.csv', index=False)
Pw = P.sort_values('mass', ascending=False); Pw['ok'] = hit(Pw.pred, Pw.y)
res['selective'] = {f'{int(c*100)}%': round(100 * Pw.ok.iloc[:int(round(c * len(Pw)))].mean(), 1) for c in (0.1, 0.2, 0.3, 0.5, 1.0)}
json.dump(res, open('out/window/hybrid_external_PHM08.json', 'w'), indent=1); print(json.dumps(res, indent=1))
