"""STW-T (theory-guided shift, bearing/BEARING_PROTOCOL.md Part B) on the datasets seen before the rule was written.
Descriptive only. Same folds, seeds, regressors and count-based selection of cap/span/k as the main analyses; the standard
model's results are recomputed alongside and must reproduce the stored main results.
Output: out/stwt/<ds>.csv (one row per unit, H and method in {'warning', 'warning_T'})."""
import sys, os, numpy as np, pandas as pd
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
import eol_window2 as W
from safe_common import load_dataset, outer_folds
from feats import causal_feats
from stwt import shift_T
import multi_eval as ME
HS = [10, 15, 20]

def battery_pred():
    import battery_warning as BWm
    B, kappa, _ = BWm.load()
    def pred(train_u, target_u):
        F, Y = BWm.features(B, train_u); X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u])
        return {cap: {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u} for cap in W.CAPS for m in [W.gbm(X, y, cap)]}
    return np.sort(B.cell.unique()), pred

def setup(ds):
    if ds == 'Battery': return battery_pred()
    if ds == 'NCMAPSS6':
        tr, sensors = ME.ncm_frame(ME.NCM6); return np.sort(tr.unit.unique()), lambda a, b: ME.predict_generic(tr, sensors, a, b)
    tr, _, _ = load_dataset(ds); return np.sort(tr.unit.unique()), lambda a, b: W.predict_all(tr, a, b, a)

def main(ds):
    units, pred = setup(ds); rows = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        train_u = np.setdiff1d(units, test_u); inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5); oof = {c: {} for c in W.CAPS}
        for iu in inner:
            p = pred(np.setdiff1d(train_u, iu), iu)
            for c in W.CAPS: oof[c].update(p[c])
        final = pred(train_u, test_u)
        for H in HS:
            best = None
            for cap in W.CAPS:
                if cap < H + 20: continue
                for sp in W.SPANS:
                    Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
                    for k in W.KS:
                        tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                        if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
            _, cap, sp, k, s = best
            sT = shift_T({u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}, H, k, W.SHIFTS)
            Pt = {u: (W.smooth(p, sp), y) for u, (p, y) in final[cap].items()}
            rows.append(W.evaluate(Pt, H, k, s).assign(fold=fold, H=H, method='warning', shift=s, cap=cap, span=sp, k=k))
            rows.append(W.evaluate(Pt, H, k, sT).assign(fold=fold, H=H, method='warning_T', shift=sT, cap=cap, span=sp, k=k))
        print(ds, 'fold', fold, 'done', flush=True)
    A = pd.concat(rows); os.makedirs('out/stwt', exist_ok=True); A.to_csv(f'out/stwt/{ds}.csv', index=False)
    print(A.groupby(['H', 'method']).cls.apply(lambda s: round(100 * (s == 'IN').mean(), 1)).unstack().to_string(), flush=True)

if __name__ == '__main__':
    for ds in ARGS: main(ds)
