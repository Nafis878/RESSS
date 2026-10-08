"""Ablation study and stacked hybrid for the [-13, +2] window at half of life (PHM08).

Input: out/window/base_preds_PHM08.csv (collect_base.py). The stacker is trained on CALIBRATION rows only
(calibration engines at 16 life stages); its type and decoder are chosen by engine-grouped 4-fold CV inside the
calibration rows, pooled over all stages (never on test engines, never tuned to the half-life point).
Test engines (one row each at half of life) are scored once per configuration.
"""
import sys, json, numpy as np, pandas as pd, warnings
from sklearn.linear_model import QuantileRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
warnings.filterwarnings('ignore')
LO, HI = -13, 2; QS = [0.1, 0.25, 0.5, 0.75, 0.9]
D = pd.read_csv('out/window/base_preds_PHM08.csv')
GROUPS = {'age': ['age'], 'gbm': ['gbm'], 'lstm': ['lstm'], 'cnn': ['cnn'], 'iohmm': ['iohmm'],
          'bayes': ['bayes_q05', 'bayes_q50', 'bayes_q95'], 'transformer': ['tf_q05', 'tf_q50', 'tf_q95'], 'similarity': ['sim'],
          'sensor_baseline': ['g_base'], 'sensor_trend': ['g_trend']}

def hit(p, y): e = np.asarray(p) - np.asarray(y); return (e >= LO) & (e <= HI)
def summ(p, y):
    e = np.asarray(p) - np.asarray(y); return dict(in_window=int(hit(p, y).sum()), pct=round(100 * hit(p, y).mean(), 1),
                                                   late=int((e > HI).sum()), early=int((e < LO).sum()), mae=round(float(np.abs(e).mean()), 1))
def decode_q(Q):
    """window-optimal choice from predicted quantiles (piecewise-linear CDF)"""
    Q = np.sort(Q, 1); cs = np.arange(0, 400, 0.5); out, mass = np.empty(len(Q)), np.empty(len(Q))
    p = np.concatenate([[0], QS, [1]])
    for i, q in enumerate(Q):
        x = np.concatenate([[q[0] - 2 * (q[1] - q[0])], q, [q[-1] + 2 * (q[-1] - q[-2])]]); x = np.maximum.accumulate(x + np.arange(len(x)) * 1e-6)
        m = np.interp(cs - LO, x, p) - np.interp(cs - HI, x, p); j = int(np.argmax(m)); out[i], mass[i] = cs[j], m[j]
    return out, mass

def fit_predict(kind, C, T, cols):
    Xc, Xt, y = C[cols + ['t']].values, T[cols + ['t']].values, C.y.values
    if kind == 'gbm_point':
        m = HistGradientBoostingRegressor(loss='absolute_error', max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20, random_state=0).fit(Xc, y)
        return m.predict(Xt), None
    if kind == 'linear_quantile':
        mu, sd = Xc.mean(0), Xc.std(0) + 1e-9
        Q = np.column_stack([QuantileRegressor(quantile=q, alpha=0.001, solver='highs').fit((Xc - mu) / sd, y).predict((Xt - mu) / sd) for q in QS])
        return decode_q(Q)
    if kind == 'gbm_quantile':
        Q = np.column_stack([HistGradientBoostingRegressor(loss='quantile', quantile=q, max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                                           min_samples_leaf=20, random_state=0).fit(Xc, y).predict(Xt) for q in QS])
        return decode_q(Q)

def with_shift(kind, C, T, cols):
    """shift for the window, chosen by engine-grouped CV inside the calibration rows"""
    oof = np.empty(len(C))
    for a, b in GroupKFold(4).split(C, groups=C.unit):
        oof[b] = fit_predict(kind, C.iloc[a], C.iloc[b], cols)[0]
    grid = np.arange(-15, 15.5, 0.5); sc = [hit(oof + s, C.y).mean() for s in grid]; s = grid[int(np.argmax(sc))]
    p, mass = fit_predict(kind, C, T, cols); return p + s, mass, max(sc), s

def run(cols, kind):
    P, M, CV = [], [], []
    for f in sorted(D.fold.unique()):
        C, T = D[(D.fold == f) & (D.role == 'cal')], D[(D.fold == f) & (D.role == 'test')]
        p, mass, cv, s = with_shift(kind, C, T, cols); P.append(pd.DataFrame({'unit': T.unit, 'y': T.y, 'pred': p, 'mass': mass if mass is not None else np.nan})); CV.append(cv)
    return pd.concat(P), float(np.mean(CV))

T = D[D.role == 'test']; res = {}
# ---- Ablation A: every base model alone, raw prediction on test at half of life
res['A_single_raw'] = {c: summ(T[c], T.y) for c in ['age', 'gbm', 'lstm', 'cnn', 'iohmm', 'bayes_q50', 'tf_q50', 'sim']}
# ---- Ablation B: information sources (GBM on feature subsets)
res['B_information'] = {c: summ(T[c], T.y) for c in ['g_age', 'g_base', 'g_level', 'g_trend', 'g_noage', 'g_all']}
# ---- choose the stacker type on calibration CV (all base models)
ALL = sum(GROUPS.values(), [])
choice = {}
for kind in ('gbm_point', 'linear_quantile', 'gbm_quantile'):
    P, cv = run(ALL, kind); choice[kind] = dict(cal_cv_hit=round(100 * cv, 1), **summ(P.pred, P.y)); print(kind, choice[kind], flush=True)
res['C_stacker_type'] = choice
best = max(choice, key=lambda k: choice[k]['cal_cv_hit']); res['chosen_stacker'] = best
P, cv = run(ALL, best); res['final_hybrid'] = dict(cal_cv_hit=round(100 * cv, 1), **summ(P.pred, P.y))
if P.mass.notna().any():
    res['final_hybrid']['self_assessed_expected_hit_pct'] = round(100 * P.mass.mean(), 1)
P.to_csv('out/window/final_hybrid_half_PHM08.csv', index=False)
# ---- Ablation D: leave one model group out / only one group, with the chosen stacker
res['D_leave_one_out'] = {}
for g, cols in GROUPS.items():
    Pg, _ = run([c for c in ALL if c not in cols], best); res['D_leave_one_out'][g] = summ(Pg.pred, Pg.y); print('without', g, res['D_leave_one_out'][g], flush=True)
res['D_only'] = {}
for g, cols in GROUPS.items():
    Pg, _ = run(cols, best); res['D_only'][g] = summ(Pg.pred, Pg.y); print('only', g, res['D_only'][g], flush=True)
json.dump(res, open('out/window/ablation_results_PHM08.json', 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('A_single_raw', 'B_information', 'C_stacker_type', 'final_hybrid')}, indent=1))
