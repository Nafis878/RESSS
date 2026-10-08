"""Trajectory-similarity RUL (in the spirit of Wang et al., PHM08 2nd place).

Each engine -> causal multivariate health trajectory: regime-normalised sensors,
exponentially smoothed (causal), projected on the top principal components of
the training trajectories.  A test prefix of length t is compared with every
training engine at every end position e using its last W cycles; the best match
per training engine gives a candidate RUL = L_j - e with weight exp(-d/tau).
Output: a RUL probability distribution on GRID (candidates kernel-smoothed).
"""
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from feats import regime_stats, zmat
from countdown_hmm import GRID


class SimilarityRUL:
    def __init__(self, W=60, n_pc=5, span=15, tau_mult=1.0, kernel_sd=6.0, top=30, age_pen=0.0):
        self.W, self.n_pc, self.span, self.tau_mult = W, n_pc, span, tau_mult
        self.kernel_sd, self.top, self.age_pen = kernel_sd, top, age_pen

    def _traj(self, g):
        Z = zmat(g.sort_values('cycle'), self.st, self.keep)
        S = pd.DataFrame(Z).ewm(span=self.span).mean().values
        return (S - self.mu) @ self.V

    def fit(self, df):
        self.st, self.keep = regime_stats(df)
        Zs = {u: pd.DataFrame(zmat(g.sort_values('cycle'), self.st, self.keep)).ewm(span=self.span).mean().values
              for u, g in df.groupby('unit')}
        X = np.vstack(list(Zs.values())); self.mu = X.mean(0)
        _, _, Vt = np.linalg.svd(X - self.mu, full_matrices=False); self.V = Vt[:self.n_pc].T
        self.H = {u: (Z - self.mu) @ self.V for u, Z in Zs.items()}
        return self

    def trajectory(self, g):
        return self._traj(g)

    def distribution(self, Q_full, t):
        """RUL pmf after observing cycles 1..t of a trajectory Q_full (t x n_pc)"""
        W = min(self.W, t); Q = Q_full[t - W:t]
        cands, dists = [], []
        for u, Hj in self.H.items():
            Lj = len(Hj)
            if Lj < W + 1: continue
            win = sliding_window_view(Hj[:Lj - 1], (W, Hj.shape[1]))[:, 0]      # end e = W..Lj-1 (RUL >= 1)
            d = ((win - Q[None]) ** 2).sum((1, 2)) / W
            ends = np.arange(W, Lj)
            if self.age_pen: d = d + self.age_pen * ((ends - t) / 50.0) ** 2
            i = np.argmin(d); cands.append(Lj - ends[i]); dists.append(d[i])
        cands, dists = np.array(cands), np.array(dists)
        order = np.argsort(dists)[:self.top]; c, dd = cands[order], dists[order]
        tau = self.tau_mult * max(np.median(dd), 1e-6)
        w = np.exp(-(dd - dd.min()) / tau)
        p = (w[:, None] * np.exp(-0.5 * ((GRID[None] - c[:, None]) / self.kernel_sd) ** 2)).sum(0)
        return p / p.sum()
