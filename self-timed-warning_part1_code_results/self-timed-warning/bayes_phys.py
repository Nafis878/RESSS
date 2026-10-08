"""Physics-informed Bayesian degradation model (exponential degradation path, Gebraeel-style) for the [-13, +2] window.

Health indicator (HI): linear combination of regime-normalised sensors, learned on FIT engines so that HI ~ 0 early in life
and ~ 1 at failure. Physics: HI(s) = a + exp(theta + beta * s) + noise; the engine fails when the path reaches its
failure level D. Population prior over (a, theta, beta, log D) = multivariate normal fitted to per-engine least-squares fits
of the FIT engines. For a test engine observed up to cycle t, posterior by importance sampling (likelihood of the observed HI
path, and the constraint that it has not yet failed); RUL distribution = crossing time - t. Window decoder chooses c maximising
P(c - 2 <= RUL <= c + 13). Calibration engines choose the noise scale (tempering) and a decoder shift, pooled over 30/50/70/90 %.
Same engine-level folds as the main study; test engines are scored once at t = floor(L/2).
"""
import sys, os, numpy as np, pandas as pd
from scipy.optimize import curve_fit
from safe_common import load_dataset, outer_folds, fit_cal_split
from feats import regime_stats, zmat
LO, HI_ = -13, 2
DS = sys.argv[1] if len(sys.argv) > 1 else 'PHM08'
M = 20000; RNG = np.random.default_rng(0)

def hit(p, y):
    e = np.asarray(p) - np.asarray(y); return (e >= LO) & (e <= HI_)

def path(s, a, th, be):
    return a + np.exp(np.clip(th + be * s, -30, 5))

def decode(r, w):
    cs = np.arange(0, 400, 0.5); o = np.argsort(r); r, cw = r[o], np.cumsum(w[o])
    F = lambda v: np.interp(v, r, cw, left=0, right=1)
    return cs[np.argmax(F(cs - LO) - F(cs - HI_ - 1e-9))]

class BayesDeg:
    def fit(self, H):                                    # H: dict unit -> HI array (full life)
        P = []
        for u, h in H.items():
            s = np.arange(1, len(h) + 1, dtype=float); L = len(h)
            try:
                p, _ = curve_fit(path, s, h, p0=[0.0, -5.0, 4.0 / L], maxfev=20000)
            except RuntimeError:
                continue
            D = path(L, *p) - p[0]
            if D > 0 and p[2] > 0: P.append([p[0], p[1], p[2], np.log(D)])
        P = np.array(P); self.mu, self.C = P.mean(0), np.cov(P.T)
        res = [h - path(np.arange(1, len(h) + 1.0), *p[:3]) for (u, h), p in zip(H.items(), P)]
        self.sigma = float(np.median([np.std(r) for r in res])); self.n_fit = len(P)
        self.S = RNG.multivariate_normal(self.mu, self.C, M)
        self.S[:, 2] = np.abs(self.S[:, 2]) + 1e-5
        return self

    def rul_dist(self, h_obs, temp=1.0):
        a, th, be, lD = self.S.T; t = len(h_obs); s = np.arange(1, t + 1, dtype=float)
        T = (np.log(np.exp(lD)) - th) / be                                     # crossing time of a + exp(th + be s) = a + D
        alive = T > t
        pred = a[:, None] + np.exp(np.clip(th[:, None] + be[:, None] * s[None], -30, 5))
        ll = -((pred - h_obs[None]) ** 2).sum(1) / (2 * (self.sigma * temp) ** 2)
        ll[~alive] = -np.inf; w = np.exp(ll - ll.max()); w /= w.sum()
        return T - t, w

def main(ds):
    tr, _, _ = load_dataset(ds); units = np.sort(tr.unit.unique()); rows = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        fit_u, cal_u = fit_cal_split(np.setdiff1d(units, test_u))
        st, keep = regime_stats(tr[tr.unit.isin(fit_u)])
        Z = {u: np.nan_to_num(zmat(g, st, keep)) for u, g in tr.groupby('unit')}
        # HI weights: ridge regression of early (0) vs late (1) cycles on FIT engines
        X, y = [], []
        for u in fit_u:
            L = len(Z[u]); f = np.arange(1, L + 1) / L; m0, m1 = f <= 0.2, f >= 0.95
            X += [Z[u][m0], Z[u][m1]]; y += [np.zeros(m0.sum()), np.ones(m1.sum())]
        X, y = np.vstack(X), np.concatenate(y); w = np.linalg.solve(X.T @ X + 1.0 * np.eye(X.shape[1]), X.T @ (y - y.mean()))
        c0 = np.mean(np.concatenate([Z[u][:20] @ w for u in fit_u]))
        H = {u: Z[u] @ w - c0 for u in Z}
        model = BayesDeg().fit({u: H[u] for u in fit_u})
        def at(us, fr, temp):
            out = []
            for u in us:
                L = len(H[u])
                for f in fr:
                    t = int(np.floor(f * L)); r, wt = model.rul_dist(H[u][:t], temp)
                    ess = 1 / (wt ** 2).sum()
                    out.append((u, f, t, L - t, decode(r, wt), float(np.sum(r * wt)), ess,
                                *np.interp([0.05, 0.5, 0.95], np.cumsum(wt[np.argsort(r)]), np.sort(r))))
            return pd.DataFrame(out, columns=['unit', 'frac', 't', 'y', 'win', 'mean', 'ess', 'q05', 'q50', 'q95'])
        best = None
        for temp in (1.0, 2.0, 4.0):
            Cc = at(cal_u, [0.3, 0.5, 0.7, 0.9], temp); grid = np.arange(-20, 20.5, 0.5)
            sc = [hit(Cc.win + s, Cc.y).mean() for s in grid]; j = int(np.argmax(sc))
            if best is None or sc[j] > best[0]: best = (sc[j], temp, grid[j])
        T = at(test_u, [0.5], best[1]); T['win_shift'] = T.win + best[2]; T['fold'] = fold
        rows.append(T)
        print(f'fold {fold}: prior from {model.n_fit} engines, noise sd {model.sigma:.3f}, temp {best[1]}, shift {best[2]:+.1f}, '
              f'median ESS {T.ess.median():.0f}; test hit win {hit(T.win, T.y).mean():.3f} shifted {hit(T.win_shift, T.y).mean():.3f}', flush=True)
    A = pd.concat(rows); os.makedirs('out/window', exist_ok=True); A.to_csv(f'out/window/bayes_phys_half_{ds}.csv', index=False)
    n = len(A); print(f'\n{ds}: physics-informed Bayesian model, {n} engines at half of life, window [{LO}, +{HI_}]')
    for c in ['win', 'win_shift', 'q50', 'mean']:
        e = A[c] - A.y
        print(f'{c:10s} in-window {hit(A[c], A.y).sum():4d}/{n} = {100*hit(A[c], A.y).mean():5.1f}%  late {(e>HI_).sum():4d}  early {(e<LO).sum():4d}  MAE {e.abs().mean():5.1f}')
    print(f'90% credible interval: median width {(A.q95-A.q05).median():.1f} cycles, coverage {100*((A.y>=A.q05)&(A.y<=A.q95)).mean():.0f}%')

if __name__ == '__main__':
    main(DS)
