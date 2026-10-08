"""Fixed-time gradient-boosted trees of safe_methods.py (functions _roll_slope_expanding, gbm_features and class GBM copied
verbatim, lines 18-46), so that they can be used without numba, which safe_methods.py imports only for the
hidden Markov model. audit_fixed_matched.py checks that this copy reproduces the frozen predictions of results/safe/."""
import numpy as np, pandas as pd


def _roll_slope_expanding(Y):
    n, p = Y.shape; t = np.arange(n, dtype=float); out = np.zeros((n, p))
    c1 = np.cumsum(Y, 0); ct = np.cumsum(t); ctt = np.cumsum(t * t); cty = np.cumsum(Y * t[:, None], 0)
    k = np.arange(1, n + 1, dtype=float)[:, None]
    den = k * ctt[:, None] - ct[:, None] ** 2
    with np.errstate(divide='ignore', invalid='ignore'):
        out = np.where(den > 0, (k * cty - ct[:, None] * c1) / den, 0.0)
    out[:4] = 0.0
    return out

def gbm_features(Z):
    n = len(Z); b = np.array([Z[:min(20, i + 1)].mean(0) for i in range(n)]); Yc = Z - b
    D, Dc = pd.DataFrame(Z), pd.DataFrame(Yc)
    lvl = Dc.expanding().mean().values; sd = D.expanding(min_periods=2).std().fillna(0).values
    recent = Dc.ewm(span=5).mean().values; hi = recent.mean(1, keepdims=True)
    return np.hstack([recent, lvl, _roll_slope_expanding(Z), sd, hi, np.arange(1, n + 1)[:, None], b])

class GBM:
    name = 'Gradient-boosted trees (ours)'
    def fit(self, E):
        from sklearn.ensemble import HistGradientBoostingRegressor
        X = np.vstack([gbm_features(v[0]) for v in E.values()]); y = np.concatenate([v[2] for v in E.values()])
        self.m = HistGradientBoostingRegressor(loss='absolute_error', max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
                                               min_samples_leaf=40, random_state=0).fit(X, y)
        return self
    def predict(self, Z, reg):
        return self.m.predict(gbm_features(Z))
