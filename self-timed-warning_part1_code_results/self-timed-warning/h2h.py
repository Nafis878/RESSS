"""Head-to-head: our end-of-life warning model vs re-implementations of the three published PHM08 challenge approaches,
all under ONE identical first-warning protocol (window [-13, +2], error = prediction - true RUL).

Protocol (same for every method), per outer fold of the main study (seeds 2026 / 7):
  FIT engines  -> train the RUL model
  CAL engines  -> choose the warning settings: smoothing span, debounce k, shift s (+ the method's own option below)
  TEST engines -> first warning = first cycle where the smoothed, shifted prediction stays <= H for k cycles; scored once.
Methods
  ours       capped gradient-boosted trees on causal features of 15 sensors; cap in {40, 60, 90} chosen on CAL
  similarity trajectory-similarity RUL, in the spirit of Wang et al. (2008)   [median of the RUL distribution]
  rnn        LSTM network (stored predictions of the main pipeline), in the spirit of Heimes (2008)
  mlp_kf     multilayer perceptron + Kalman filter over time, in the spirit of Peel (2008); filter noise ratio chosen on CAL
  cnn        1-D CNN (stored predictions; later deep-learning baseline, Li et al. 2018 style)
These are re-implementations in the spirit of the published methods, not the original code.
"""
import sys, os, json, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from safe_common import load_dataset, outer_folds, fit_cal_split
from feats import regime_stats, zmat, causal_feats
from similarity import SimilarityRUL
from countdown_hmm import GRID
LO, HI = -13, 2
HS = [10, 20]; KS = [1, 2, 3, 5]; SPANS = [1, 3, 6]; SHIFTS = np.arange(-15, 10.5, 0.5)
DS = sys.argv[1] if len(sys.argv) > 1 else 'PHM08'

def smooth(p, span): return p if span == 1 else pd.Series(p).ewm(span=span).mean().values
def kalman(z, q, r):
    out = np.empty(len(z)); x, P = z[0], r
    for i, zi in enumerate(z):
        if i: x, P = x - 1.0, P + q
        K = P / (P + r); x = x + K * (zi - x); P = (1 - K) * P; out[i] = x
    return out
def in_counts(P, H, k):
    thr = H - SHIFTS; tot = np.zeros(len(SHIFTS))
    for p, y in P.values():
        mk = pd.Series(p).rolling(k, min_periods=k).max().values; mk = np.where(np.isnan(mk), np.inf, mk)
        rm = np.minimum.accumulate(mk); i = np.searchsorted(-rm, -thr, side='left'); ok = i < len(p); ii = np.minimum(i, len(p) - 1)
        e = p[ii] + SHIFTS - y[ii]; tot += ok & (e >= LO) & (e <= HI)
    return tot
def first_warning(p, y, H, k):
    run = np.convolve((p <= H).astype(int), np.ones(k, int), 'full')[:len(p)] >= k; i = np.flatnonzero(run)
    return (p[i[0]], y[i[0]]) if len(i) else (np.nan, np.nan)

def main(ds):
    tr, _, _ = load_dataset(ds); units = np.sort(tr.unit.unique())
    stored = {m: pd.read_csv(f'out/safe/preds_{ds}_{m}.csv') for m in ('lstm', 'cnn')}
    rows, cfgs = [], []
    for fold, test_u in enumerate(outer_folds(units), 1):
        fit_u, cal_u = fit_cal_split(np.setdiff1d(units, test_u)); both = np.concatenate([cal_u, test_u])
        G = {u: g for u, g in tr.groupby('unit')}; st, keep = regime_stats(tr[tr.unit.isin(fit_u)])
        CF = {u: causal_feats(np.nan_to_num(zmat(G[u], st, keep))) for u in np.concatenate([fit_u, both])}
        Y = {u: G[u].rul.values[:-1].astype(float) for u in both}                    # cycles with RUL >= 1
        X = np.vstack([CF[u] for u in fit_u]); y = np.concatenate([G[u].rul.values for u in fit_u])
        variants = {}                                                                  # method -> list of (option, {unit: raw preds})
        variants['ours'] = []
        for cap in (40, 60, 90):
            m = HistGradientBoostingRegressor(loss='absolute_error', max_iter=500, learning_rate=0.05, max_leaf_nodes=31,
                                              min_samples_leaf=40, random_state=0).fit(X, np.minimum(y, cap))
            variants['ours'].append((f'cap {cap}', {u: m.predict(CF[u])[:-1] for u in both}))
        mu, sd = X.mean(0), X.std(0) + 1e-9
        mlp = MLPRegressor(hidden_layer_sizes=(64, 32), alpha=1e-3, early_stopping=True, max_iter=200, random_state=0).fit((X - mu) / sd, np.minimum(y, 125) / 100)
        raw = {u: mlp.predict((CF[u] - mu) / sd)[:-1] * 100 for u in both}
        variants['mlp_kf'] = [(f'kalman q/r=1/{r}', {u: kalman(p, 1.0, r) for u, p in raw.items()}) for r in (25, 100, 400)]
        sim = SimilarityRUL().fit(tr[tr.unit.isin(fit_u)]); sp = {}
        for u in both:
            Q = sim.trajectory(G[u]); sp[u] = np.array([GRID[np.searchsorted(np.cumsum(sim.distribution(Q, t)), 0.5)] for t in range(1, len(G[u]))], float)
        variants['similarity'] = [('median', sp)]
        for m in ('lstm', 'cnn'):
            S = stored[m][stored[m].fold == fold].sort_values(['unit', 't'])
            variants['rnn' if m == 'lstm' else 'cnn'] = [('stored', {u: g.point.values[:-1] for u, g in S[S.unit.isin(both)].groupby('unit')})]
        for meth, opts in variants.items():
            for H in HS:
                best = None
                for oname, P in opts:
                    for span in SPANS:
                        Pc = {u: (smooth(P[u], span), Y[u]) for u in cal_u}
                        for k in KS:
                            tot = in_counts(Pc, H, k) - 1e-3 * np.abs(SHIFTS); j = int(np.argmax(tot))
                            if best is None or tot[j] > best[0]: best = (tot[j], oname, span, k, SHIFTS[j])
                _, oname, span, k, s = best; P = dict(opts)[oname]
                cfgs.append(dict(fold=fold, method=meth, H=H, option=oname, span=span, k=k, shift=s, cal_in=round(best[0] / len(cal_u), 3)))
                for u in test_u:
                    pw, yw = first_warning(smooth(P[u], span) + s, Y[u], H, k); e = pw - yw
                    rows.append(dict(fold=fold, method=meth, H=H, unit=u, pred=pw, y=yw,
                                     cls='MISSED' if np.isnan(pw) else ('LATE' if e > HI else ('EARLY' if e < LO else 'IN'))))
        print(f'fold {fold} done', flush=True)
        pd.DataFrame(rows).to_csv(f'out/window/h2h_{ds}.csv', index=False); pd.DataFrame(cfgs).to_csv(f'out/window/h2h_cfg_{ds}.csv', index=False)
    R = pd.DataFrame(rows); summ = []
    for (m, H), g in R.groupby(['method', 'H']):
        c = g.cls.value_counts(); summ.append(dict(method=m, H=H, n=len(g), IN=int(c.get('IN', 0)), pct=round(100 * c.get('IN', 0) / len(g), 1),
                                                   late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)), missed=int(c.get('MISSED', 0))))
    S = pd.DataFrame(summ).sort_values(['H', 'pct'], ascending=[True, False]); S.to_csv(f'out/window/h2h_summary_{ds}.csv', index=False); print(S.to_string(index=False))

if __name__ == '__main__':
    main(DS)
