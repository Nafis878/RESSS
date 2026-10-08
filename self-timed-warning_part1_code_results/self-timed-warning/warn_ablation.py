"""Component ablation of the end-of-life warning model (PHM08, same outer folds and inner-CV tuning as eol_window2.py).

Each variant removes or fixes one component; everything not fixed is tuned exactly as in the full model.
  full              cap in {40,60,90}, span, k, shift tuned, 15 sensors + age                 (= eol_window2.py)
  cap125            conventional piecewise-linear target (cap 125) instead of the end-focused caps
  uncapped          no target cap
  no_shift          shift fixed at 0 (no window centring)
  no_debounce       k fixed at 1
  no_smoothing      span fixed at 1
  untuned_rule      cap 60, span 1, k 1, shift 0 (no tuning of the decision rule at all)
  age_only          cycle count as the only input
  sensors_no_age    all sensor features, cycle count removed
  sensors7          temperature and shaft-speed sensors only (s2, s3, s4, s8, s9, s13, s14) + age
Also: oracle-timed control -- the full model's (smoothed, shifted) prediction evaluated at the cycle where the TRUE remaining
life equals H (not deployable; shows the regressor's accuracy at that horizon without self-timing).
Output: out/window/ablation_warning_PHM08.csv / .json
"""
import json, numpy as np, pandas as pd
import eol_window2 as W
from safe_common import load_dataset, outer_folds
from feats import regime_stats, zmat, causal_feats
HS = [10, 20]; S7 = ['s2', 's3', 's4', 's8', 's9', 's13', 's14']; BIG = 10 ** 6

def feats_sets(tr, st_from):
    st, keep = regime_stats(tr[tr.unit.isin(st_from)]); i7 = [keep.index(s) for s in S7]; out = {}
    for u, g in tr.groupby('unit'):
        Z = zmat(g, st, keep); F = causal_feats(Z)
        out[u] = {'all': F, 'age': F[:, -1:], 'noage': F[:, :-1], 's7': causal_feats(Z[:, i7])}
    return out

SETS = {'all': [40, 60, 90, 125, BIG], 'age': [40, 60, 90], 'noage': [40, 60, 90], 's7': [40, 60, 90]}

def predict(tr, train_u, target_u):
    F = feats_sets(tr, train_u); rul = {u: g.rul.values for u, g in tr.groupby('unit')}; y = np.concatenate([rul[u] for u in train_u]); out = {}
    for fs, caps in SETS.items():
        X = np.vstack([F[u][fs] for u in train_u])
        for cap in caps:
            m = W.gbm(X, y, cap); out[(fs, cap)] = {u: (m.predict(F[u][fs])[:-1], rul[u][:-1].astype(float)) for u in target_u}
    return out

VARIANTS = {'full': dict(fs='all', caps=[40, 60, 90]), 'cap125': dict(fs='all', caps=[125]), 'uncapped': dict(fs='all', caps=[BIG]),
            'no_shift': dict(fs='all', caps=[40, 60, 90], shift=0.0), 'no_debounce': dict(fs='all', caps=[40, 60, 90], k=1),
            'no_smoothing': dict(fs='all', caps=[40, 60, 90], span=1), 'untuned_rule': dict(fs='all', caps=[60], span=1, k=1, shift=0.0),
            'age_only': dict(fs='age', caps=[40, 60, 90]), 'sensors_no_age': dict(fs='noage', caps=[40, 60, 90]),
            'sensors7': dict(fs='s7', caps=[40, 60, 90])}

def tune(oof, v, H):
    best = None
    for cap in v['caps']:
        for sp in ([v['span']] if 'span' in v else W.SPANS):
            Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[(v['fs'], cap)].items()}
            for k in ([v['k']] if 'k' in v else W.KS):
                tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS)
                if 'shift' in v: j = int(np.argmin(np.abs(W.SHIFTS - v['shift'])))
                else: j = int(np.argmax(tot))
                if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
    return best[1:]

def main():
    tr, _, _ = load_dataset('PHM08'); units = np.sort(tr.unit.unique()); rows, oracle = [], []
    for fold, test_u in enumerate(outer_folds(units), 1):
        train_u = np.setdiff1d(units, test_u); inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5); oof = {}
        for iu in inner:
            p = predict(tr, np.setdiff1d(train_u, iu), iu)
            for key, d in p.items(): oof.setdefault(key, {}).update(d)
        final = predict(tr, train_u, test_u)
        for name, v in VARIANTS.items():
            for H in HS:
                cap, sp, k, s = tune(oof, v, H)
                R = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in final[(v['fs'], cap)].items()}, H, k, s)
                rows.append(R.assign(fold=fold, variant=name, H=H, cap=cap, span=sp, k=k, shift=s))
                if name == 'full':
                    for u, (p, y) in final[(v['fs'], cap)].items():
                        q = W.smooth(p, sp) + s; i = np.flatnonzero(y == H)
                        if len(i): oracle.append(dict(fold=fold, H=H, unit=u, pred=q[i[0]], y=H))
        print('fold', fold, 'done', flush=True)
    A = pd.concat(rows); A.to_csv('out/window/ablation_warning_PHM08.csv', index=False)
    res = {}
    for (v, H), g in A.groupby(['variant', 'H']):
        c = g.cls.value_counts(); res[f'{v}|H{H}'] = dict(IN=int(c.get('IN', 0)), n=len(g), pct=round(100 * c.get('IN', 0) / len(g), 1),
                                                          late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)), missed=int(c.get('MISSED', 0)),
                                                          median_true_left=float(g.y.median()))
    O = pd.DataFrame(oracle); O['e'] = O.pred - O.y
    for H, g in O.groupby('H'):
        res[f'oracle_timed|H{H}'] = dict(IN=int(((g.e >= -13) & (g.e <= 2)).sum()), n=len(g), pct=round(100 * ((g.e >= -13) & (g.e <= 2)).mean(), 1),
                                         late=int((g.e > 2).sum()), early=int((g.e < -13).sum()))
    json.dump(res, open('out/window/ablation_warning_PHM08.json', 'w'), indent=1)
    for k_, v_ in res.items(): print(k_, v_)

if __name__ == '__main__':
    main()
