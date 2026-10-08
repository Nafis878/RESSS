"""External-knowledge experiments at half of life, window [-13, +2], PHM08 test engines (same folds as the main study).

E-A  Extra training engines: NASA C-MAPSS FD002 (260 engines) and FD004 (249 engines) were simulated under the same six
     operating conditions as PHM08. They are added to the FIT engines of every fold (PHM08 test engines stay unseen).
     Models: gradient-boosted trees (causal features, uncapped RUL) and the physics-informed Bayesian degradation model.
E-B  Selective prediction: the stacked hybrid answers only for engines whose predicted probability of landing in the
     window is highest; accuracy vs coverage.
E-C  Relative window (alpha-lambda idea, Saxena et al. 2010): correct if error in [-13 %, +2 %] ... [-30 %, +10 %] of the true RUL.
"""
import numpy as np, pandas as pd, json
from sklearn.ensemble import HistGradientBoostingRegressor
from safe_common import load_dataset, outer_folds, fit_cal_split
from feats import regime_stats, zmat, causal_feats
from bayes_phys import BayesDeg
LO, HI = -13, 2
def hit(p, y): e = np.asarray(p) - np.asarray(y); return (e >= LO) & (e <= HI)

phm, _, _ = load_dataset('PHM08'); ext = {}
for k, off in (('FD002', 10000), ('FD004', 20000)):
    d, _, _ = load_dataset(k); d = d.copy(); d['unit'] += off; ext[k] = d
print('sensor means per regime, PHM08 vs FD002 vs FD004 (s3, s9, s14 at cruise 42040):')
for nm, d in (('PHM08', phm), ('FD002', ext['FD002']), ('FD004', ext['FD004'])):
    print(nm, d[d.regime == 42040][['s3', 's9', 's14']].mean().round(2).to_dict(), 'life median', d.groupby('unit').cycle.max().median())
units = np.sort(phm.unit.unique()); res = {}
for variant, extra in (('PHM08 only', []), ('+FD002', ['FD002']), ('+FD002+FD004', ['FD002', 'FD004'])):
    rows = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        fit_u, cal_u = fit_cal_split(np.setdiff1d(units, test_u))
        tr = pd.concat([phm] + [ext[k] for k in extra]); fit_all = np.concatenate([fit_u] + [ext[k].unit.unique() for k in extra])
        F = tr[tr.unit.isin(fit_all)]; st, keep = regime_stats(F)
        Z = {u: np.nan_to_num(zmat(g, st, keep)) for u, g in tr[tr.unit.isin(np.concatenate([fit_all, test_u]))].groupby('unit')}
        X = np.vstack([causal_feats(Z[u]) for u in fit_all]); y = np.concatenate([tr[tr.unit == u].rul.values for u in fit_all])
        m = HistGradientBoostingRegressor(loss='absolute_error', max_iter=400, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=40, random_state=0).fit(X, y)
        Xh, yh = [], []
        for u in fit_all:
            L = len(Z[u]); f = np.arange(1, L + 1) / L; m0, m1 = f <= 0.2, f >= 0.95; Xh += [Z[u][m0], Z[u][m1]]; yh += [np.zeros(m0.sum()), np.ones(m1.sum())]
        Xh, yh = np.vstack(Xh), np.concatenate(yh); w = np.linalg.solve(Xh.T @ Xh + np.eye(Xh.shape[1]), Xh.T @ (yh - yh.mean()))
        c0 = np.mean(np.concatenate([Z[u][:20] @ w for u in fit_all])); H = {u: Z[u] @ w - c0 for u in Z}
        bd = BayesDeg().fit({u: H[u] for u in fit_all})
        for u in test_u:
            L = len(Z[u]); t = L // 2; r, wt = bd.rul_dist(H[u][:t]); o = np.argsort(r)
            rows.append(dict(fold=fold, unit=u, y=L - t, gbm=m.predict(causal_feats(Z[u])[t - 1:t])[0],
                             bayes=float(np.interp(0.5, np.cumsum(wt[o]), r[o]))))
        print(variant, 'fold', fold, 'fit engines', len(fit_all), flush=True)
    R = pd.DataFrame(rows); res[variant] = {c: dict(in_window=int(hit(R[c], R.y).sum()), pct=round(100 * hit(R[c], R.y).mean(), 1),
                                                   mae=round(float((R[c] - R.y).abs().mean()), 1)) for c in ('gbm', 'bayes')}
    print(variant, res[variant], flush=True)

# E-B selective prediction with the stacked hybrid
P = pd.read_csv('out/window/final_hybrid_half_PHM08.csv').sort_values('mass', ascending=False)
P['ok'] = hit(P.pred, P.y); sel = {}
for cov in (0.1, 0.2, 0.3, 0.5, 1.0):
    k = int(round(cov * len(P))); sel[f'{int(cov*100)}%'] = dict(engines=k, in_window=int(P.ok.iloc[:k].sum()), pct=round(100 * P.ok.iloc[:k].mean(), 1))
res['selective'] = sel
# E-C relative windows on the stacked hybrid and on the cautious-free LSTM
B = pd.read_csv('out/window/base_preds_PHM08.csv'); B = B[B.role == 'test']
rel = {}
for lo, hi in ((0.13, 0.02), (0.2, 0.05), (0.3, 0.1)):
    for nm, p, y in (('hybrid', P.pred.values, P.y.values), ('lstm', B.lstm.values, B.y.values)):
        e = (p - y) / y; rel[f'{nm} [-{int(lo*100)}%, +{int(hi*100)}%]'] = round(100 * float(((e >= -lo) & (e <= hi)).mean()), 1)
res['relative_window'] = rel
json.dump(res, open('out/window/external_results_PHM08.json', 'w'), indent=1); print(json.dumps(res, indent=1))
