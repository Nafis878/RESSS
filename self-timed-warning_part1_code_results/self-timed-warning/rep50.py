"""Supervisor's protocol, repeated: 20 random splits of the 218 PHM08 engines into 50 test / 168 training engines.

Per repetition r (seed 1000 + r):
  A  50 test engines drawn at random;  B  the other 168 train the model
  warning model (eol_window2.py): settings (target cap, smoothing, debounce k, shift) chosen on out-of-fold predictions of an inner
  5-fold split of the 168 training engines; models refit on all 168; applied once to the 50 test engines, warning level H = 20
  C  actual life of each test engine
  D  predicted life = cycle at which the warning is issued + predicted cycles left at that moment
  E  error = D - C (= predicted - true cycles left); correct if -13 <= E <= +2; no warning before failure = missed (late)
Output: out/rep50/rep50_results.csv (one row per engine per repetition), rep50_log.txt
"""
import os, sys, numpy as np, pandas as pd
import eol_window2 as W
from safe_common import load_dataset
H = 20; NREP = int(sys.argv[1]) if len(sys.argv) > 1 else 20

def run():
    tr, _, _ = load_dataset('PHM08'); units = np.sort(tr.unit.unique()); life = tr.groupby('unit').cycle.max()
    os.makedirs('out/rep50', exist_ok=True); rows = []
    for r in range(1, NREP + 1):
        rng = np.random.default_rng(1000 + r); test_u = np.sort(rng.choice(units, 50, replace=False)); train_u = np.setdiff1d(units, test_u)
        inner = np.array_split(np.random.default_rng(2000 + r).permutation(train_u), 5); oof = {c: {} for c in W.CAPS}
        for iu in inner:
            tu = np.setdiff1d(train_u, iu); p = W.predict_all(tr, tu, iu, tu)
            for c in W.CAPS: oof[c].update(p[c])
        final = W.predict_all(tr, train_u, test_u, train_u)
        best = None
        for cap in W.CAPS:
            for sp in W.SPANS:
                Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
                for k in W.KS:
                    tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                    if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j], round(tot[j]) / len(Po))
        _, cap, sp, k, s, oof_in = best
        R = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in final[cap].items()}, H, k, s)
        for x in R.itertuples():
            C = int(life[x.unit]); D = np.nan if np.isnan(x.pred) else x.cycle + x.pred
            rows.append(dict(repetition=r, engine=int(x.unit), actual_life_C=C, warning_cycle=x.cycle, predicted_cycles_left=x.pred,
                             true_cycles_left=x.y, predicted_life_D=D, error_E=None if np.isnan(D) else D - C, result=x.cls,
                             cap=cap, span=sp, k=k, shift=s))
        n_in = int((R.cls == 'IN').sum())
        msg = f'repetition {r:2d}: {n_in}/50 in window  (late {int((R.cls=="LATE").sum())}, early {int((R.cls=="EARLY").sum())}, missed {int((R.cls=="MISSED").sum())})  settings cap {cap} span {sp} k {k} shift {s:+.1f}, inner-OOF {oof_in:.3f}'
        print(msg, flush=True); open('out/rep50/rep50_log.txt', 'a').write(msg + '\n')
        pd.DataFrame(rows).to_csv('out/rep50/rep50_results.csv', index=False)

if __name__ == '__main__':
    run()
