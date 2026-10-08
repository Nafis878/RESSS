"""Collect base-model predictions for the ablation study and the stacked hybrid (window [-13, +2]).

Same engine-level folds / fit-calibration split as the main study. For every outer fold:
  CAL rows : calibration engines at 16 life stages (20, 25, ..., 95 % of life)  -> used to learn the stacker
  TEST rows: outer-test engines at t = floor(L/2)                                -> scored once
Base models (all trained on FIT engines only):
  age, gbm, lstm, cnn, iohmm       stored predictions of the main pipeline (same folds)
  bayes_q05/q50/q95                physics-informed Bayesian degradation model (bayes_phys.BayesDeg)
  tf_q05/q50/q95                   hybrid Transformer (hybrid_tf.build), quantile outputs
  sim                              trajectory-similarity median
  g_* (information-source ablation) gradient-boosted trees on feature subsets of causal_feats:
       g_age (cycle count only), g_base (early-life sensor baseline), g_level (recent level vs baseline),
       g_trend (slopes), g_noage (all sensor features, no cycle count), g_all (everything)
Output: out/window/base_preds_PHM08.csv
"""
import os, sys, numpy as np, pandas as pd
os.environ.setdefault('KERAS_BACKEND', 'jax')
from sklearn.ensemble import HistGradientBoostingRegressor
from safe_common import load_dataset, outer_folds, fit_cal_split
from feats import regime_stats, zmat, causal_feats
from bayes_phys import BayesDeg
import hybrid_tf as HT
from similarity import SimilarityRUL
from countdown_hmm import GRID
DS = sys.argv[1] if len(sys.argv) > 1 else 'PHM08'
CAL_STAGES = np.round(np.arange(0.20, 0.951, 0.05), 2)

def main(ds):
    import keras
    tr, _, _ = load_dataset(ds); units = np.sort(tr.unit.unique())
    stored = {m: pd.read_csv(f'out/safe/preds_{ds}_{m}.csv') for m in ('age', 'gbm', 'lstm', 'cnn', 'iohmm')}
    out = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        fit_u, cal_u = fit_cal_split(np.setdiff1d(units, test_u))
        st, keep = regime_stats(tr[tr.unit.isin(fit_u)]); p = len(keep)
        G = {u: g for u, g in tr.groupby('unit')}
        Z = {u: np.nan_to_num(zmat(g, st, keep)) for u, g in G.items()}
        CF = {u: causal_feats(Z[u]) for u in Z}
        rows = [(u, 'cal', s, int(np.floor(s * len(G[u])))) for u in cal_u for s in CAL_STAGES] + \
               [(u, 'test', 0.5, int(np.floor(0.5 * len(G[u])))) for u in test_u]
        R = pd.DataFrame(rows, columns=['unit', 'role', 'stage', 't']); R['fold'] = fold
        R['life'] = R.unit.map({u: len(G[u]) for u in G}); R['y'] = R.life - R.t
        # stored predictions
        for m, S in stored.items():
            R = R.merge(S[S.fold == fold][['unit', 't', 'point']].rename(columns={'point': m}), on=['unit', 't'], how='left')
        # information-source ablation (GBM on feature subsets)
        blocks = {'g_age': [5 * p], 'g_base': list(range(2 * p, 3 * p)), 'g_level': list(range(0, 2 * p)),
                  'g_trend': list(range(3 * p, 5 * p)), 'g_noage': list(range(0, 5 * p)), 'g_all': list(range(0, 5 * p + 1))}
        X = np.vstack([CF[u] for u in fit_u]); y = np.concatenate([G[u].rul.values for u in fit_u])
        Xr = np.stack([CF[u][t - 1] for u, t in zip(R.unit, R.t)])
        for name, cols in blocks.items():
            m = HistGradientBoostingRegressor(loss='absolute_error', max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
                                              min_samples_leaf=40, random_state=0).fit(X[:, cols], y)
            R[name] = m.predict(Xr[:, cols])
        # physics-informed Bayesian model
        Xh, yh = [], []
        for u in fit_u:
            L = len(Z[u]); f = np.arange(1, L + 1) / L; m0, m1 = f <= 0.2, f >= 0.95
            Xh += [Z[u][m0], Z[u][m1]]; yh += [np.zeros(m0.sum()), np.ones(m1.sum())]
        Xh, yh = np.vstack(Xh), np.concatenate(yh); w = np.linalg.solve(Xh.T @ Xh + np.eye(p), Xh.T @ (yh - yh.mean()))
        c0 = np.mean(np.concatenate([Z[u][:20] @ w for u in fit_u])); H = {u: Z[u] @ w - c0 for u in Z}
        bd = BayesDeg().fit({u: H[u] for u in fit_u}); bq = []
        for u, t in zip(R.unit, R.t):
            r, wt = bd.rul_dist(H[u][:t]); o = np.argsort(r)
            bq.append(np.interp([0.05, 0.5, 0.95], np.cumsum(wt[o]), r[o]))
        R[['bayes_q05', 'bayes_q50', 'bayes_q95']] = np.array(bq)
        # similarity
        sim = SimilarityRUL().fit(tr[tr.unit.isin(fit_u)]); Q = {u: sim.trajectory(G[u]) for u in np.concatenate([cal_u, test_u])}
        R['sim'] = [GRID[np.searchsorted(np.cumsum(sim.distribution(Q[u], t)), 0.5)] for u, t in zip(R.unit, R.t)]
        # hybrid Transformer (quantiles)
        keras.utils.set_random_seed(fold); regs = np.sort(tr.regime.unique())
        E = {u: (HT.seq_windows(np.hstack([Z[u], (G[u].regime.values[:, None] == regs[None]).astype(float)])).astype('float32'),
                 CF[u].astype('float32'), G[u].rul.values.astype('float32')) for u in G}
        mu = np.vstack([E[u][1] for u in fit_u]).mean(0); sd = np.vstack([E[u][1] for u in fit_u]).std(0) + 1e-6
        def mk(us, stride):
            X1 = np.concatenate([E[u][0][::stride] for u in us]); X2 = np.concatenate([(E[u][1][::stride] - mu) / sd for u in us]).astype('float32')
            yy = np.concatenate([E[u][2][::stride] for u in us]) / HT.SCALE; return [X1, X2], np.repeat(yy[:, None], len(HT.QS), 1).astype('float32')
        Xtr, ytr = mk(fit_u, 2); Xva, yva = mk(cal_u, 3)
        net = HT.build(Xtr[0].shape[2], Xtr[1].shape[1])
        net.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=40, batch_size=256, verbose=0,
                callbacks=[keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True),
                           keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=3, min_lr=1e-5)])
        X1 = np.stack([E[u][0][t - 1] for u, t in zip(R.unit, R.t)]); X2 = np.stack([(E[u][1][t - 1] - mu) / sd for u, t in zip(R.unit, R.t)]).astype('float32')
        Qt = np.sort(net.predict([X1, X2], verbose=0) * HT.SCALE, 1)
        R['tf_q05'], R['tf_q50'], R['tf_q95'] = Qt[:, 0], Qt[:, 4], Qt[:, -1]
        out.append(R); print(f'fold {fold} done: {len(R)} rows', flush=True)
        pd.concat(out).to_csv(f'out/window/base_preds_{ds}.csv', index=False)

if __name__ == '__main__':
    main(DS)
