"""Hybrid Transformer + engineered-feature model, and distributional GBM, for the [-13, +2] window at half of life.

Error = prediction - true RUL; correct iff -13 <= error <= +2  <=>  true RUL in [pred - 2, pred + 13].
Protocol: same engine-level 5-fold CV and fit/calibration split as the main study (seeds 2026 / 7).
  FIT engines  : train models (all cycles, uncapped RUL target)
  CAL engines  : early stopping of the network; choice of decoder shift
  TEST engines : scored once at t = floor(L/2).
Both models predict 9 quantiles of the RUL; the window decoder picks the prediction c that maximises the predicted
probability P(c - 2 <= RUL <= c + 13) (Bayes-optimal for the window). No step sees a test engine's total life.
"""
import os, sys, numpy as np, pandas as pd
os.environ.setdefault('KERAS_BACKEND', 'jax')
from sklearn.ensemble import HistGradientBoostingRegressor
from safe_common import load_dataset, outer_folds, fit_cal_split
from feats import regime_stats, zmat, causal_feats
LO, HI = -13, 2
DS = sys.argv[1] if len(sys.argv) > 1 else 'PHM08'
QS = np.array([0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95]); W = 40; SCALE = 100.0

def hit(p, y):
    e = np.asarray(p) - np.asarray(y); return (e >= LO) & (e <= HI)

def window_decode(Q):
    """Q: (n, 9) sorted quantiles. Piecewise-linear CDF (tails extended linearly); maximise F(c+13) - F(c-2)."""
    Q = np.sort(Q, 1); out = np.empty(len(Q)); cs = np.arange(0, 400, 0.5)
    for i, q in enumerate(Q):
        x = np.concatenate([[q[0] - (q[1] - q[0]) * 0.05 / 0.05], q, [q[-1] + (q[-1] - q[-2])]]); p = np.concatenate([[0.0], QS, [1.0]])
        x = np.maximum.accumulate(x + np.arange(len(x)) * 1e-6)
        F = lambda v: np.interp(v, x, p)
        out[i] = cs[np.argmax(F(cs - LO) - F(cs - HI))]
    return out

def seq_windows(S):
    P = np.vstack([np.repeat(S[:1], W - 1, 0), S])
    return np.lib.stride_tricks.sliding_window_view(P, (W, S.shape[1]))[:, 0]

def build(p_seq, p_stat):
    import keras; from keras import layers, ops
    si = keras.Input((W, p_seq)); ti = keras.Input((p_stat,))
    x = layers.Dense(32)(si)
    pos = layers.Embedding(W, 32)(ops.arange(W)); x = x + pos
    for _ in range(2):
        a = layers.MultiHeadAttention(4, 8, dropout=0.1)(x, x); x = layers.LayerNormalization()(x + a)
        f = layers.Dense(64, activation='gelu')(x); f = layers.Dense(32)(f); x = layers.LayerNormalization()(x + layers.Dropout(0.1)(f))
    x = layers.Concatenate()([layers.GlobalAveragePooling1D()(x), x[:, -1]])
    t = layers.Dense(64, activation='gelu')(ti); t = layers.Dropout(0.1)(t)
    h = layers.Dense(64, activation='gelu')(layers.Concatenate()([x, t]))
    base = layers.Dense(1)(h); inc = layers.Dense(len(QS) - 1, activation='softplus')(h)
    out = layers.Concatenate()([base, base + ops.cumsum(inc, axis=1)])          # monotone quantiles
    m = keras.Model([si, ti], out)
    q = ops.convert_to_tensor(QS.astype('float32'))
    def pinball(y, yp):
        e = y - yp; return ops.mean(ops.maximum(q * e, (q - 1) * e))
    m.compile(keras.optimizers.Adam(1e-3), pinball); return m

def main(ds):
    import keras
    tr, _, _ = load_dataset(ds); units = np.sort(tr.unit.unique()); rows = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        keras.utils.set_random_seed(fold)
        fit_u, cal_u = fit_cal_split(np.setdiff1d(units, test_u))
        st, keep = regime_stats(tr[tr.unit.isin(fit_u)])
        regs = np.sort(tr.regime.unique())
        E = {}
        for u, g in tr.groupby('unit'):
            Z = np.nan_to_num(zmat(g, st, keep)); R = (g.regime.values[:, None] == regs[None]).astype(float)
            E[u] = (seq_windows(np.hstack([Z, R])).astype('float32'), causal_feats(Z).astype('float32'), g.rul.values.astype('float32'))
        Sf = np.vstack([E[u][1] for u in fit_u]); mu, sd = Sf.mean(0), Sf.std(0) + 1e-6
        def mk(us, stride):
            X1 = np.concatenate([E[u][0][::stride] for u in us]); X2 = np.concatenate([(E[u][1][::stride] - mu) / sd for u in us])
            y = np.concatenate([E[u][2][::stride] for u in us]) / SCALE; return [X1, X2.astype('float32')], y[:, None].astype('float32')
        Xtr, ytr = mk(fit_u, 2); Xva, yva = mk(cal_u, 3)
        m = build(Xtr[0].shape[2], Xtr[1].shape[1])
        h = m.fit(Xtr, np.repeat(ytr, len(QS), 1), validation_data=(Xva, np.repeat(yva, len(QS), 1)), epochs=40, batch_size=256, verbose=0,
                  callbacks=[keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True),
                             keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=3, min_lr=1e-5)])
        # distributional GBM on the same engineered features
        Xg = np.vstack([E[u][1] for u in fit_u]); yg = np.concatenate([E[u][2] for u in fit_u])
        gq = [HistGradientBoostingRegressor(loss='quantile', quantile=q, max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
                                            min_samples_leaf=40, random_state=0).fit(Xg, yg) for q in QS]
        def at(us, fracs):
            idx = [(u, int(np.floor(f * len(E[u][2])))) for u in us for f in fracs]
            X1 = np.stack([E[u][0][t - 1] for u, t in idx]); X2 = np.stack([(E[u][1][t - 1] - mu) / sd for u, t in idx]).astype('float32')
            X3 = np.stack([E[u][1][t - 1] for u, t in idx]); y = np.array([E[u][2][t - 1] for u, t in idx])
            Qt = m.predict([X1, X2], verbose=0) * SCALE; Qg = np.column_stack([g.predict(X3) for g in gq])
            return idx, y, Qt, Qg
        # decoder shift chosen on calibration engines, pooled over 30/50/70/90 % of life (not tuned to the half-life point)
        _, yc, Qtc, Qgc = at(cal_u, [0.3, 0.5, 0.7, 0.9]); grid = np.arange(-20, 20.5, 0.5)
        dt_c, dg_c = window_decode(Qtc), window_decode(Qgc)
        s_t = grid[np.argmax([hit(dt_c + s, yc).mean() for s in grid])]; s_g = grid[np.argmax([hit(dg_c + s, yc).mean() for s in grid])]
        idx, y, Qt, Qg = at(test_u, [0.5])
        R = pd.DataFrame({'fold': fold, 'unit': [u for u, _ in idx], 't': [t for _, t in idx], 'y': y,
                          'tf_median': Qt[:, 4], 'tf_window': window_decode(Qt), 'tf_window_shift': window_decode(Qt) + s_t,
                          'gbmq_median': Qg[:, 4], 'gbmq_window': window_decode(Qg), 'gbmq_window_shift': window_decode(Qg) + s_g,
                          'tf_q05': Qt[:, 0], 'tf_q95': Qt[:, -1], 'gbmq_q05': Qg[:, 0], 'gbmq_q95': Qg[:, -1]})
        R['hybrid_window'] = window_decode((Qt + Qg) / 2)
        rows.append(R)
        print(f'fold {fold}: epochs {len(h.history["loss"])}, shifts tf {s_t:+.1f} gbmq {s_g:+.1f}; '
              f'test hit tf {hit(R.tf_window, R.y).mean():.3f} gbmq {hit(R.gbmq_window, R.y).mean():.3f} hybrid {hit(R.hybrid_window, R.y).mean():.3f}', flush=True)
    A = pd.concat(rows); os.makedirs('out/window', exist_ok=True); A.to_csv(f'out/window/hybrid_tf_half_{ds}.csv', index=False)
    n = len(A); print(f'\n{ds}: {n} engines at half of life, window [{LO}, +{HI}]')
    for c in ['tf_median', 'tf_window', 'tf_window_shift', 'gbmq_median', 'gbmq_window', 'gbmq_window_shift', 'hybrid_window']:
        e = A[c] - A.y
        print(f'{c:18s} in-window {hit(A[c], A.y).sum():4d}/{n} = {100*hit(A[c], A.y).mean():5.1f}%  late {(e>HI).sum():4d}  early {(e<LO).sum():4d}  MAE {e.abs().mean():5.1f}')
    for c in ['tf', 'gbmq']:
        w = (A[f'{c}_q95'] - A[f'{c}_q05']).median(); cov = ((A.y >= A[f'{c}_q05']) & (A.y <= A[f'{c}_q95'])).mean()
        print(f'{c}: median 90% prediction-interval width {w:.1f} cycles (coverage {100*cov:.0f}%)')

if __name__ == '__main__':
    main(DS)
