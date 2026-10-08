"""Fair deep-learning competitors under the first-warning protocol (PHM08), same inputs and target options as our model.

Identical to the protocol of h2h.py (outer folds seed 2026; fit 75% / calibration 25% engines, seed 7; warning settings
m, k, s and the cap chosen on calibration engines; shift grid -15..+10; H = 10 and 20; window [-13, +2]), but every
network sees the SAME 15 regime-normalised sensors as our model plus the age, and chooses its target cap from {40, 60, 90},
exactly like our model:
  lstm15   two-layer LSTM (64, 64) on 30-cycle windows (Zheng et al. 2017 architecture), MSE on min(RUL, c)/c
  cnn15    Li et al. (2018) CNN on 30-cycle windows
  tf15     hybrid Transformer (hybrid_tf.build): 40-cycle sequence of the 15 sensors + regime indicators and the causal
           features of Section 4.2; median of the quantile output; pinball loss on min(RUL, c)/100
Output: out/window/dl_warning_PHM08.csv (one row per method, H, test engine) and the chosen settings.
"""
import os, sys, json, time, numpy as np, pandas as pd
os.environ.setdefault('KERAS_BACKEND', 'jax')
from safe_common import load_dataset, outer_folds, fit_cal_split
from safe_methods import DeepNet
from feats import regime_stats, zmat, causal_feats
import hybrid_tf as HT
import h2h
CAPS = [40, 60, 90]; HS = [10, 20]

def main():
    import keras
    tr, _, _ = load_dataset('PHM08'); units = np.sort(tr.unit.unique()); rows, cfgs = [], []
    for fold, test_u in enumerate(outer_folds(units), 1):
        t0 = time.time(); fit_u, cal_u = fit_cal_split(np.setdiff1d(units, test_u)); both = np.concatenate([cal_u, test_u])
        G = {u: g for u, g in tr.groupby('unit')}; st, keep = regime_stats(tr[tr.unit.isin(fit_u)]); regs = np.sort(tr.regime.unique())
        Z = {u: np.nan_to_num(zmat(G[u], st, keep)) for u in G}; CF = {u: causal_feats(Z[u]) for u in G}
        Y = {u: G[u].rul.values[:-1].astype(float) for u in both}
        E = {u: (np.hstack([Z[u], (np.arange(1, len(Z[u]) + 1) / 100.0)[:, None]]).astype('float32'), None, G[u].rul.values) for u in G}
        variants = {'lstm15': [], 'cnn15': [], 'tf15': []}
        for cap in CAPS:
            for kind in ('lstm', 'cnn'):
                net = DeepNet(kind, w=30, cap=cap).fit({u: E[u] for u in fit_u})
                variants[kind + '15'].append((f'cap {cap}', {u: net.predict(E[u][0], None)[:-1] for u in both}))
            keras.utils.set_random_seed(fold)
            ET = {u: (HT.seq_windows(np.hstack([Z[u], (G[u].regime.values[:, None] == regs[None]).astype(float)])).astype('float32'),
                      CF[u].astype('float32'), np.minimum(G[u].rul.values, cap).astype('float32')) for u in G}
            mu = np.vstack([ET[u][1] for u in fit_u]).mean(0); sd = np.vstack([ET[u][1] for u in fit_u]).std(0) + 1e-6
            def mk(us, stride):
                X1 = np.concatenate([ET[u][0][::stride] for u in us]); X2 = np.concatenate([(ET[u][1][::stride] - mu) / sd for u in us]).astype('float32')
                yy = np.concatenate([ET[u][2][::stride] for u in us]) / HT.SCALE; return [X1, X2], np.repeat(yy[:, None], len(HT.QS), 1).astype('float32')
            vu = np.random.default_rng(0).choice(fit_u, max(1, len(fit_u) // 10), replace=False)      # validation engines from FIT only
            Xtr, ytr = mk(np.setdiff1d(fit_u, vu), 2); Xva, yva = mk(vu, 3)
            m = HT.build(Xtr[0].shape[2], Xtr[1].shape[1])
            m.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=40, batch_size=256, verbose=0,
                  callbacks=[keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True), keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=3, min_lr=1e-5)])
            pt = {}
            for u in both:
                q = np.sort(m.predict([ET[u][0], ((ET[u][1] - mu) / sd).astype('float32')], verbose=0, batch_size=4096) * HT.SCALE, 1); pt[u] = q[:, 4][:-1]
            variants['tf15'].append((f'cap {cap}', pt))
        for meth, opts in variants.items():
            for H in HS:
                best = None
                for oname, P in opts:
                    for span in h2h.SPANS:
                        Pc = {u: (h2h.smooth(P[u], span), Y[u]) for u in cal_u}
                        for k in h2h.KS:
                            tot = h2h.in_counts(Pc, H, k) - 1e-3 * np.abs(h2h.SHIFTS); j = int(np.argmax(tot))
                            if best is None or tot[j] > best[0]: best = (tot[j], oname, span, k, h2h.SHIFTS[j])
                _, oname, span, k, s = best; P = dict(opts)[oname]
                cfgs.append(dict(fold=fold, method=meth, H=H, option=oname, span=span, k=k, shift=s, cal_in=round(best[0] / len(cal_u), 3)))
                for u in test_u:
                    pw, yw = h2h.first_warning(h2h.smooth(P[u], span) + s, Y[u], H, k); e = pw - yw
                    rows.append(dict(fold=fold, method=meth, H=H, unit=u, pred=pw, y=yw,
                                     cls='MISSED' if np.isnan(pw) else ('LATE' if e > h2h.HI else ('EARLY' if e < h2h.LO else 'IN'))))
        pd.DataFrame(rows).to_csv('out/window/dl_warning_PHM08.csv', index=False); pd.DataFrame(cfgs).to_csv('out/window/dl_warning_cfg_PHM08.csv', index=False)
        print(f'fold {fold} done in {time.time() - t0:.0f}s', flush=True)
    R = pd.DataFrame(rows)
    print(R.groupby(['H', 'method']).cls.apply(lambda s: f"{(s == 'IN').sum()}/{len(s)} = {100 * (s == 'IN').mean():.1f}%").to_string())

if __name__ == '__main__':
    main()
