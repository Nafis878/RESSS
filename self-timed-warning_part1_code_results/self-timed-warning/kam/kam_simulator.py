"""Phase 1b: check of the metric re-implementation on the virtual RUL simulator of Kamariotis et al. (2024), Section 3
(arXiv:2306.03759v2), replacement-only setting. Qualitative comparison with their Figs. 4 and 5 only.

Simulator (their Eqs. 21-25): T_F ~ N(225, 40); decision points t_k = 10k; ln RUL_pred,k ~ N(mu_k, sigma) with
mu_k = ln(T_F - t_k) + ln eps_k, (ln eps_1, ...) ~ MVN(0, Sigma), Sigma_ij = sigma^2 exp(-|t_i - t_j| / 50);
sigma = 0.4 (their Fig. 4) and 0.15 (Fig. 5); n = 2000 components; c_p = 1, c_c = c_p / ratio.
Policies (their Sec. 2.3.2-2.3.4):
  1  replace at t_k if Pr(RUL_pred,k <= dT) >= p_thres, with p_thres = c_p/c_c and with p_thres minimising M on the same
     2000 components (in-sample, as in their Sec. 3.2);
  2  replace at t_k if the minimiser T_R* of Eq. (12) satisfies T_R* <= t_k + dT;
  3  as 2 with the objective of Eq. (14), E[C]/E[T] of the population set by their option 1 (optimal age replacement for
     N(225, 40)).
T_R is optimised on a log-spaced grid of x = T_R - t_k (400 points from 0.05 to 5000 cycles plus every 0.05 cycle in
[9, 11]); the decision only depends on whether the minimiser lies at or below dT.
Output: out/kam/sim_results.csv (one row per sigma, ratio, policy), out/kam/sim_pthres.csv, out/kam/sim_checks.txt
"""
import os, sys, math, time
import numpy as np, pandas as pd
from scipy.stats import norm
from scipy.special import ndtr
sys.path.insert(0, os.path.dirname(__file__)); import kam_metric as K
OUT = 'out/kam'; os.makedirs(OUT, exist_ok=True)
SEED, N, MU_F, SD_F, DT, CORR_L = 2026, 2000, 225.0, 40.0, 10.0, 50.0
RATIOS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8]
TGRID = np.arange(DT, 500 + DT, DT)                                             # decision points 10 ... 500
XG = np.unique(np.concatenate([np.logspace(np.log10(0.05), np.log10(5000), 400), np.arange(9, 11.0001, 0.05)]))
PGRID = np.unique(np.concatenate([np.logspace(-4, 0, 400), np.linspace(0, 1, 1001)[1:]]))


def age_replacement_rate(cp, cc):
    """Option 1 of their Sec. 2.3.4: optimal long-run cost rate of age replacement for T_F ~ N(225, 40),
    min_T [c_p S(T) + c_c F(T)] / int_0^T S(t) dt, on a 0.25-cycle grid (trapezoidal integral)."""
    T = np.arange(0.0, 600.0, 0.25); S = norm.sf(T, MU_F, SD_F)
    integ = np.concatenate([[0.0], np.cumsum(0.5 * (S[1:] + S[:-1]) * np.diff(T))])
    return float(np.min((cp * S[1:] + cc * (1 - S[1:])) / integ[1:]))


def simulate(sigma, rng):
    TF = rng.normal(MU_F, SD_F, N)
    Sig = sigma ** 2 * np.exp(-np.abs(TGRID[:, None] - TGRID[None, :]) / CORR_L)
    eps = rng.multivariate_normal(np.zeros(len(TGRID)), Sig, size=N, method='cholesky')
    valid = TGRID[None, :] < TF[:, None]
    mu = np.log(np.where(valid, TF[:, None] - TGRID[None, :], 1.0)) + eps
    return TF, mu, valid


def first_tr(flag, valid):
    """Replacement time = first valid decision point at which flag is True; inf if never."""
    f = flag & valid; k = np.argmax(f, axis=1); has = f.any(axis=1)
    return np.where(has, TGRID[k], np.inf)


def policy_23(mu, valid, sigma, cp, cc, kind, lam_bar, chunk=200):
    """Flag (unit, step) where the minimiser of Eq. (12) (kind 2) or Eq. (14) (kind 3) lies at x <= dT."""
    flag = np.zeros(mu.shape, bool); lx = np.log(XG); near = XG <= DT
    m1 = np.exp(sigma ** 2 / 2)
    for a in range(0, mu.shape[0], chunk):
        M = mu[a:a + chunk][:, :, None]; t = TGRID[None, :, None]
        z = (lx[None, None, :] - M) / sigma
        F = ndtr(z); PE = np.exp(M) * m1 * ndtr(z - sigma)                       # E[U 1{U <= x}], U lognormal
        P = 1 - F
        if kind == 2:
            f = (P * cp + F * cc) / (t + P * XG[None, None, :] + PE)
        else:
            beyond = np.exp(M) * m1 - PE - XG[None, None, :] * P                 # E[(U - x)+]
            f = P * cp + F * cc + lam_bar * beyond
        j = np.argmin(f, axis=2); flag[a:a + chunk] = near[j]
    return flag & valid


def main():
    t0 = time.time(); rows, prow, ckl = [], [], []
    for si, sigma in enumerate((0.4, 0.15)):
        rng = np.random.default_rng(SEED + si); TF, mu, valid = simulate(sigma, rng)
        p1 = ndtr((np.log(DT) - mu) / sigma)                                    # Pr(RUL_pred <= dT)
        cm = np.maximum.accumulate(np.where(valid, p1, -1.0), axis=1)            # first crossing of p >= thr
        Rp = {}
        for ratio in RATIOS:
            cp, cc = 1.0, 1.0 / ratio; lam = age_replacement_rate(cp, cc)
            Ropt, nf = K.perfect_with_failure_option(TF, DT, cp, cc)
            res = {}
            def add(name, TR, extra=None):
                C, T = K.lifecycle(TR, TF, cp, cc); M, lo, hi = K.m_with_ci(C, T, TF, DT, cp, cc, f'sim sigma={sigma} ratio={ratio} {name}')
                res[name] = (C, T); rows.append(dict(sigma=sigma, cp_over_cc=ratio, policy=name, M_pct=100 * M, lo_pct=100 * lo, hi_pct=100 * hi,
                                                    failures=int((C == cc).sum()), mean_T=float(T.mean()), p_thres=extra, footnote1_units=nf))
            add('P1, p_thres = c_p/c_c', first_tr(p1 >= ratio, valid), ratio)
            # optimised threshold (in-sample over the same 2000 components, as in their Sec. 3.2)
            best = None
            for thr in PGRID:
                k = np.argmax(cm >= thr, axis=1); has = (cm >= thr).any(axis=1)
                C, T = K.lifecycle(np.where(has, TGRID[k], np.inf), TF, cp, cc); R = C.sum() / T.sum()
                if best is None or R < best[0] - 1e-15: best = (R, thr)
            add('P1, optimised p_thres', first_tr(p1 >= best[1], valid), best[1]); prow.append(dict(sigma=sigma, cp_over_cc=ratio, p_star=best[1]))
            add('P2 (Eq. 12)', first_tr(policy_23(mu, valid, sigma, cp, cc, 2, lam), valid))
            add('P3 (Eq. 14, option 1)', first_tr(policy_23(mu, valid, sigma, cp, cc, 3, lam), valid))
            # paired bootstrap of P3 - P2 and P1opt - P3
            for a, b in (('P3 (Eq. 14, option 1)', 'P2 (Eq. 12)'), ('P1, optimised p_thres', 'P3 (Eq. 14, option 1)')):
                d, lo, hi = K.paired_boot_mdiff(*res[a], *res[b], TF, DT, cp, cc, B=1000, seed=7)
                ckl.append(dict(sigma=sigma, cp_over_cc=ratio, pair=f'{a} minus {b}', diff_pct=100 * d, lo_pct=100 * lo, hi_pct=100 * hi))
            print(f'sigma={sigma} ratio={ratio} done ({time.time() - t0:.0f}s)', flush=True)
    R = pd.DataFrame(rows); P = pd.DataFrame(prow); D = pd.DataFrame(ckl)
    R.to_csv(f'{OUT}/sim_results.csv', index=False); P.to_csv(f'{OUT}/sim_pthres.csv', index=False); D.to_csv(f'{OUT}/sim_pairs.csv', index=False)
    # qualitative checks against their Figs. 4-5
    L = []
    for sigma, g in R.groupby('sigma'):
        piv = g.pivot(index='cp_over_cc', columns='policy', values='M_pct')
        best = piv.idxmin(axis=1)
        L.append(f'sigma={sigma}: optimised P1 lowest M at {int((best == "P1, optimised p_thres").sum())}/{len(piv)} ratios; lowest by ratio: {best.to_dict()}')
        L.append(f'sigma={sigma}: P3 < P2 at {int((piv["P3 (Eq. 14, option 1)"] < piv["P2 (Eq. 12)"]).sum())}/{len(piv)} ratios')
        L.append(f'sigma={sigma}: P2 and P3 < P1(c_p/c_c) at {int(((piv["P2 (Eq. 12)"] < piv["P1, p_thres = c_p/c_c"]) & (piv["P3 (Eq. 14, option 1)"] < piv["P1, p_thres = c_p/c_c"])).sum())}/{len(piv)} ratios')
        pp = P[P.sigma == sigma]; L.append(f'sigma={sigma}: p* < c_p/c_c at {int((pp.p_star < pp.cp_over_cc).sum())}/{len(pp)} ratios; p* = {dict(zip(pp.cp_over_cc, pp.p_star.round(4)))}')
    L.append('M violations (M < 0): ' + str([v for v in K.VIOLATIONS if v[0].startswith('sim')]))
    open(f'{OUT}/sim_checks.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L)); print(R.round(3).to_string(index=False))


if __name__ == '__main__':
    main()
