"""End-of-life first-warning model, version 2 (window [-13, +2], error = prediction - true RUL).

Changes from version 1: all outer-training engines are used. Settings (target cap, prediction smoothing, debounce k,
shift s) are chosen on OUT-OF-FOLD predictions from an inner 5-fold split of the outer-training engines (~174 engines),
then models are refit on all outer-training engines and applied once to the outer-test engines.
Warning rule: first cycle at which the smoothed, shifted prediction has been <= H for k consecutive cycles.
No step uses the total life of a test engine. Engines never warned before failure count as MISSED (late).
"""
import sys, os, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from safe_common import load_dataset, outer_folds
from feats import regime_stats, zmat, causal_feats
LO, HI = -13, 2
DS = sys.argv[1] if len(sys.argv) > 1 else 'PHM08'
CAPS = [40, 60, 90]
HS = [int(h) for h in (sys.argv[2] if len(sys.argv) > 2 else '10,15,20,30,40').split(',')]
KS = [1, 2, 3, 5]
SPANS = [1, 3, 6]
SHIFTS = np.arange(-12, 8.5, 0.5)

def gbm(X, y, cap):
    return HistGradientBoostingRegressor(loss='absolute_error', max_iter=500, learning_rate=0.05, max_leaf_nodes=31,
                                         min_samples_leaf=40, random_state=0).fit(X, np.minimum(y, cap))

def smooth(p, span):
    return p if span == 1 else pd.Series(p).ewm(span=span).mean().values        # causal

def warn(p, y, H, k):
    run = np.convolve((p <= H).astype(int), np.ones(k, int), 'full')[:len(p)] >= k
    i = np.flatnonzero(run)
    return (p[i[0]], y[i[0]], i[0] + 1) if len(i) else (np.nan, np.nan, np.nan)

def evaluate(P, H, k, s):
    R = pd.DataFrame([(u,) + warn(p + s, y, H, k) for u, (p, y) in P.items()], columns=['unit', 'pred', 'y', 'cycle'])
    e = R.pred - R.y
    R['cls'] = np.where(R.pred.isna(), 'MISSED', np.where(e > HI, 'LATE', np.where(e < LO, 'EARLY', 'IN')))
    return R

def in_counts(P, H, k):
    """vectorised over SHIFTS: number of engines whose first warning lands in the window (same rule as evaluate)"""
    thr = H - SHIFTS; tot = np.zeros(len(SHIFTS))
    for p, y in P.values():
        mk = pd.Series(p).rolling(k, min_periods=k).max().values; mk = np.where(np.isnan(mk), np.inf, mk)
        rm = np.minimum.accumulate(mk)
        i = np.searchsorted(-rm, -thr, side='left'); ok = i < len(p); ii = np.minimum(i, len(p) - 1)
        e = p[ii] + SHIFTS - y[ii]; tot += ok & (e >= LO) & (e <= HI)
    return tot

def predict_all(tr, train_u, target_u, st_from):
    st, keep = regime_stats(tr[tr.unit.isin(st_from)])
    feats = {u: causal_feats(zmat(g, st, keep)) for u, g in tr[tr.unit.isin(np.concatenate([train_u, target_u]))].groupby('unit')}
    rul = {u: g.rul.values for u, g in tr[tr.unit.isin(np.concatenate([train_u, target_u]))].groupby('unit')}
    X = np.vstack([feats[u] for u in train_u]); y = np.concatenate([rul[u] for u in train_u])
    out = {}
    for cap in CAPS:
        m = gbm(X, y, cap); out[cap] = {u: (m.predict(feats[u])[:-1], rul[u][:-1]) for u in target_u}
    return out

def main(ds):
    tr, _, _ = load_dataset(ds); units = np.sort(tr.unit.unique()); rows = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        train_u = np.setdiff1d(units, test_u)
        inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5)
        oof = {c: {} for c in CAPS}
        for iu in inner:
            tu = np.setdiff1d(train_u, iu); p = predict_all(tr, tu, iu, tu)
            for c in CAPS: oof[c].update(p[c])
        final = predict_all(tr, train_u, test_u, train_u)
        for H in HS:
            best = None
            for cap in CAPS:
                if cap < H + 20: continue
                for sp in SPANS:
                    Po = {u: (smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
                    for k in KS:
                        tot = in_counts(Po, H, k) - 0.001 * np.abs(SHIFTS)
                        j = int(np.argmax(tot))
                        if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, SHIFTS[j], round(tot[j]) / len(Po))
            _, cap, sp, k, s, cal_in = best
            R = evaluate({u: (smooth(p, sp), y) for u, (p, y) in final[cap].items()}, H, k, s)
            R = R.assign(fold=fold, H=H, cap=cap, span=sp, k=k, shift=s); rows.append(R)
            print(f'fold {fold} H={H:3d}: cap {cap} span {sp} k {k} shift {s:+.1f}  inner-OOF in {cal_in:.3f}  test in {(R.cls=="IN").mean():.3f}', flush=True)
    A = pd.concat(rows); os.makedirs('out/window', exist_ok=True); A.to_csv(f'out/window/first_warning_v2_{ds}.csv', index=False)
    print(f'\n{ds}: first-warning results v2, {A.unit.nunique()} test engines, window [{LO}, +{HI}]')
    for H, g in A.groupby('H'):
        c = g.cls.value_counts()
        print(f'H={H:3d}: IN {c.get("IN",0):3d}/{len(g)} = {100*c.get("IN",0)/len(g):5.1f}%  late {c.get("LATE",0):3d}  early {c.get("EARLY",0):3d}  '
              f'missed {c.get("MISSED",0):3d}  median true RUL at warning {g.y.median():.0f} (5-95%: {g.y.quantile(.05):.0f}-{g.y.quantile(.95):.0f})')

if __name__ == '__main__':
    main(DS)
