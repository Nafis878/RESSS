"""Phase 1: ground-truth checks of the certified alarm threshold (CAT) on simulated data (contrib/PLAN.md, Phase 1).

Part A  Theorem 1 (validity). Calibration units and new units are drawn i.i.d. from a large simulated pool, so the
        failure probability of a calibrated threshold is known exactly under the pool distribution: P(S > tau_hat).
        A1  virtual RUL simulator of Kamariotis et al. (their Sec. 3; T_F ~ N(225, 40), correlated lognormal errors,
            decisions at t_k = 10k), point estimate = median of the predictive distribution, lead l in {0, 10}.
        A2  monotone-degradation model (below), 1-cycle decisions, lead l in {0, 5, 10, 15}, one setting.
        n in {20, 50, 100, 200}, alpha in {0.01, 0.02, 0.05, 0.10}, 20,000 replicates per cell; scores on the threshold
        grid (ties; Theorem 1 gives P <= alpha) and continuous (also P > alpha - 1/(n+1)). Criterion (plan): realised
        P in [alpha - 1/(n+1) - 3 MCSE, alpha + 3 MCSE] (lower end for continuous scores only). Descriptive: the
        per-time-step conformal lower bound (threshold l + q_{1-alpha} of the residuals x_t - r_t over all cycles).
Part B  Theorem 2 (fragility as selection), degradation model: plain minimisation of the training cost rate over G
        settings (G in {1, 4, 12, 36}, nested subsets of 36 correlated settings, or G independent noise realisations of
        one setting) and the threshold grid, rho in {50, 1000}, l in {0, 10}; realised P(fail) of the selected policy
        against min(1, G/(n+1)) and 1/(n+1); true cost rates of plain tuning and of CAT-c (alpha = 0.05, one setting).
Part C  Secondary: coverage of 95% intervals for M (simulator A1, sigma = 0.4): their Eq. 7, the paired influence
        interval and the paired bootstrap (2,000 resamples), n in {20, 100}, 5,000 replicates, truth from n = 200,000.

Monotone-degradation model (fixed before the run): life L ~ round(N(200, 40)) clipped to [100, 400]; shape
beta ~ U(1.5, 3); degradation D_t = (t / L)^beta reaches 1 at failure; observation z_t = D_t + 0.04 e_t, e_t ~ N(0, 1).
Estimate of the remaining life at t: least-squares line through the last w observations (fewer than 3 points or slope
<= 1e-4: 300), RUL_hat = clip((1 - fitted level at t) / slope, 0, 300); causal EWM span m; debounce k. Settings
w in {10, 20, 40}, m in {1, 3, 6}, k in {1, 2, 3, 5} (36, like the recipe's 3 x 3 x 4 grid); primary setting (20, 3, 2).
Seeds: A1 2026 (sigma = 0.4) and 2027 (sigma = 0.15); degradation pools 9000 (correlated settings) and 9001 (independent
realisations); replicate draws 9100 + cell index; Part C 9200. Outputs in out/contrib/: sim_validity.csv,
sim_selection.csv, sim_m_coverage.csv, sim_checks.txt.
Usage: python contrib/cat_sim.py [A|B|C ...]   (default: all)
"""
import os, sys, time, itertools
ARGS = sys.argv[1:] or ['A', 'B', 'C']; sys.argv = sys.argv[:1]
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'kam')); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np, pandas as pd
from scipy.special import ndtr
import kam_metric as K
import cat as C

OUT = 'out/contrib'; os.makedirs(OUT, exist_ok=True)
NS = [20, 50, 100, 200]; ALPHAS = C.ALPHAS; REPS = int(os.environ.get("CAT_SIM_REPS", 20000))   # env override only for smoke tests
DT, MU_F, SD_F, CORR_L = 10.0, 225.0, 40.0, 50.0
TGRID = np.arange(DT, 500 + DT, DT)
TAU_A1 = np.arange(1.0, 151.0)                      # threshold grid (cycles) for the simulator
TAU_DEG = np.arange(2.0, 121.0, 2.0)                # threshold grid (cycles) for the degradation model
SETTINGS = [(w, m, k) for w in (10, 20, 40) for m in (1, 3, 6) for k in (1, 2, 3, 5)]
PRIMARY = (20, 3, 2)
CHECKS = []


def chk(name, ok):
    CHECKS.append(f'{"PASS" if ok else "FAIL"}  {name}'); print(CHECKS[-1], flush=True); return ok


# ------------------------------------------------------------------ pools
def sim_pool(sigma, n, seed):
    """Kamariotis simulator: T_F, median point estimates x_k = (T_F - t_k) eps_k at valid decision points."""
    rng = np.random.default_rng(seed); TF = rng.normal(MU_F, SD_F, n)
    Sig = sigma ** 2 * np.exp(-np.abs(TGRID[:, None] - TGRID[None, :]) / CORR_L); Lc = np.linalg.cholesky(Sig)
    eps = rng.standard_normal((n, len(TGRID))) @ Lc.T
    valid = TGRID[None, :] < TF[:, None]
    x = np.where(valid, np.maximum(TF[:, None] - TGRID[None, :], 1e-9) * np.exp(eps), np.inf)
    return TF, x, valid, eps


def sim_scores(TF, x, valid, lead):
    """k = 1: runmin over decision points; admissible t_k + lead < T_F; score = runmin at the last admissible point."""
    m = np.minimum.accumulate(x, axis=1)
    adm = valid & (TGRID[None, :] + lead < TF[:, None]); has = adm.any(1)
    last = np.where(has, adm.shape[1] - 1 - np.argmax(adm[:, ::-1], axis=1), 0)
    return np.where(has, m[np.arange(len(TF)), last], np.inf)


def deg_units(n, rng):
    L = np.clip(np.round(rng.normal(200, 40, n)), 100, 400).astype(int); beta = rng.uniform(1.5, 3.0, n)
    T = int(L.max()); t = np.arange(1, T + 1)[None, :]
    D = (t / L[:, None]) ** beta[:, None]
    return L, D


def deg_estimate(L, D, w, noise):
    """RUL_hat over cycles 1..L-1 (padded with +inf beyond), local linear trend of the last w noisy observations."""
    n, T = D.shape; z = D + noise; t = np.arange(1, T + 1, dtype=float)[None, :].repeat(n, 0)
    def csum(a): return np.concatenate([np.zeros((n, 1)), np.cumsum(a, axis=1)], axis=1)
    S1, St, Sz, Stt, Stz = csum(np.ones_like(z)), csum(t), csum(z), csum(t * t), csum(t * z)
    hi = np.arange(1, T + 1); lo = np.maximum(0, hi - w)
    g = lambda S: S[:, hi] - S[:, lo]
    nn, st, sz, stt, stz = g(S1), g(St), g(Sz), g(Stt), g(Stz)
    den = nn * stt - st ** 2
    with np.errstate(divide='ignore', invalid='ignore'):
        b = np.where(den > 0, (nn * stz - st * sz) / den, 0.0); a = (sz - b * st) / nn
        lev = a + b * t
        r = np.where((nn >= 3) & (b > 1e-4), np.clip((1 - lev) / b, 0, 300), 300.0)
    r[t >= L[:, None]] = np.inf                                          # cycles 1..L-1 only
    return r


def ewm_rows(a, span):
    if span == 1: return a
    fin = np.where(np.isfinite(a), a, np.nan)
    out = pd.DataFrame(fin.T).ewm(span=span).mean().values.T
    return np.where(np.isfinite(a), out, np.inf)


def runmin_rows(a, k):
    if k == 1: mk = a
    else:
        mk = pd.DataFrame(np.where(np.isfinite(a), a, np.nan).T).rolling(k, min_periods=k).max().values.T
        mk = np.where(np.isnan(mk), np.inf, mk)
    return np.minimum.accumulate(mk, axis=1)


def deg_pool(n_units, seed, settings, independent=False, leads=(0, 5, 10, 15), chunk=2000):
    """Scores (continuous and on TAU_DEG) per setting and lead, and alarm index per threshold of TAU_DEG (lead-free).
    independent=True: every 'setting' is a separate noise realisation of the primary setting."""
    rng = np.random.default_rng(seed); Ls, sc, ai = [], {}, []
    for a in range(0, n_units, chunk):
        nb = min(chunk, n_units - a); L, D = deg_units(nb, rng); Ls.append(L); T = D.shape[1]
        base_noise = 0.04 * rng.standard_normal(D.shape)
        A = np.zeros((nb, len(settings), len(TAU_DEG)), np.int16)
        for gi, s in enumerate(settings):
            w, m, k = PRIMARY if independent else s
            noise = 0.04 * rng.standard_normal(D.shape) if (independent and gi > 0) else base_noise
            x = ewm_rows(deg_estimate(L, D, w, noise), m); mm = runmin_rows(x, k)
            idx = (mm[:, :, None] > TAU_DEG[None, None, :]).sum(1)                  # first index with m <= tau
            A[:, gi, :] = np.minimum(idx, 32000)
            for lead in leads:
                last = L - lead - 2                                                 # cycle L - lead - 1, index - 1
                s_c = np.where(last >= 0, mm[np.arange(nb), np.clip(last, 0, T - 1)], np.inf)
                sc.setdefault((gi, lead), []).append(s_c)
        ai.append(A)
    L = np.concatenate(Ls); A = np.concatenate(ai)
    S = {key: np.concatenate(v) for key, v in sc.items()}
    return L, S, A


def grid_up(s, taus):
    j = np.searchsorted(taus, s - 1e-12, side='left')
    return np.where(np.isfinite(s) & (j < len(taus)), taus[np.minimum(j, len(taus) - 1)], np.inf)


# ------------------------------------------------------------------ Part A
def validity_cells(pool_scores, label, seed0, rows):
    """pool_scores: {(lead, kind): scores}; exact failure probability under the pool for each replicate."""
    ci = 0
    for (lead, kind), S in pool_scores.items():
        Ss = np.sort(S); N = len(S)
        for n in NS:
            for alpha in ALPHAS:
                ci += 1; rng = np.random.default_rng(seed0 + ci)
                k = C.order_index(n, alpha); cert = k <= n
                if not cert:
                    rows.append(dict(model=label, lead=lead, scores=kind, n=n, alpha=alpha, certifiable=False)); continue
                draw = S[rng.integers(0, N, size=(REPS, n))]
                th = np.partition(draw, k - 1, axis=1)[:, k - 1]
                pf = np.where(np.isfinite(th), 1 - np.searchsorted(Ss, th, side='right') / N, np.nan)
                ok_rep = np.isfinite(th).mean()
                p = np.nanmean(pf); se = np.nanstd(pf) / np.sqrt(np.isfinite(pf).sum())
                rows.append(dict(model=label, lead=lead, scores=kind, n=n, alpha=alpha, certifiable=True, cert_rate=ok_rep,
                                 p_fail=p, mcse=se, lower=alpha - 1 / (n + 1), upper=alpha, threshold_mean=float(np.nanmean(np.where(np.isfinite(th), th, np.nan))),
                                 within=bool(p <= alpha + 3 * se and (kind == 'grid' or p >= alpha - 1 / (n + 1) - 3 * se))))


def per_time_cells(res_by_unit, S_cont, lead, label, seed0, rows, reps=2000):
    """Per-time-step conformal lower bound: threshold lead + q_{1-alpha}(x_t - r_t over all cycles of n units)."""
    N = len(S_cont); Ss = np.sort(S_cont)
    for n in NS:
        for alpha in ALPHAS:
            rng = np.random.default_rng(seed0 + n + int(1000 * alpha)); pf = []; thr = []
            for _ in range(reps):
                u = rng.integers(0, N, n); v = np.concatenate([res_by_unit[i] for i in u])
                q = C.conformal_quantile(v, alpha); pf.append(1 - np.searchsorted(Ss, lead + q, side='right') / N); thr.append(lead + q)
            pf = np.array(pf)
            rows.append(dict(model=label, lead=lead, scores='per-time-step bound', n=n, alpha=alpha, certifiable=True, cert_rate=1.0,
                             p_fail=pf.mean(), mcse=pf.std() / np.sqrt(reps), lower=np.nan, upper=alpha, within=np.nan,
                             threshold_mean=float(np.mean(thr))))


def part_a():
    t0 = time.time(); rows = []
    for si, sigma in enumerate((0.4, 0.15)):
        TF, x, valid, eps = sim_pool(sigma, 400000, 2026 + si); pool = {}
        for lead in (0, 10):
            s = sim_scores(TF, x, valid, lead); pool[(lead, 'continuous')] = s; pool[(lead, 'grid')] = grid_up(s, TAU_A1)
        validity_cells(pool, f'simulator sigma={sigma}', 9100 + 100 * si, rows)
        r = x[:50000] - np.where(valid[:50000], TF[:50000, None] - TGRID[None, :], np.nan)
        res = [ri[np.isfinite(ri)] for ri in r]
        for lead in (0, 10): per_time_cells(res, pool[(lead, 'continuous')][:50000], lead, f'simulator sigma={sigma}', 9150 + 100 * si, rows)
        print(f'A1 sigma={sigma} done ({time.time() - t0:.0f}s)', flush=True)
    L, S, A = deg_pool(200000, 9000, [PRIMARY], leads=(0, 5, 10, 15)); pool = {}
    for lead in (0, 5, 10, 15):
        pool[(lead, 'continuous')] = S[(0, lead)]; pool[(lead, 'grid')] = grid_up(S[(0, lead)], TAU_DEG)
    validity_cells(pool, 'degradation (20, 3, 2)', 9300, rows)
    # per-time-step bound on the degradation model (10,000 units)
    rng = np.random.default_rng(9002); Ld, D = deg_units(10000, rng)
    x2 = ewm_rows(deg_estimate(Ld, D, 20, 0.04 * rng.standard_normal(D.shape)), 3)
    mm = runmin_rows(x2, 2); Tm = D.shape[1]; res = []
    for i in range(len(Ld)):
        xi = x2[i, :Ld[i] - 1]; res.append(xi - (Ld[i] - np.arange(1, Ld[i])))
    for lead in (0, 10):
        last = Ld - lead - 2; sc = np.where(last >= 0, mm[np.arange(len(Ld)), np.clip(last, 0, Tm - 1)], np.inf)
        per_time_cells(res, sc, lead, 'degradation (20, 3, 2)', 9350, rows)
    V = pd.DataFrame(rows); V.to_csv(f'{OUT}/sim_validity.csv', index=False)
    E = V[(V.scores != 'per-time-step bound') & V.certifiable]
    chk(f'A Theorem 1: realised P(fail) within [alpha - 1/(n+1) - 3 MCSE (continuous only), alpha + 3 MCSE] in {int(E.within.sum())}/{len(E)} certifiable cells '
        f'(largest excess over alpha {1e2 * (E.p_fail - E.upper).max():+.2f} points)', bool(E.within.all()))
    PT = V[V.scores == 'per-time-step bound']
    chk(f'A descriptive: per-time-step conformal bound, unit-level P(fail) / alpha ranges {PT.p_fail.div(PT.alpha).min():.2f}-{PT.p_fail.div(PT.alpha).max():.2f} '
        f'(not controlled at alpha in {int((PT.p_fail > PT.alpha + 3 * PT.mcse).sum())}/{len(PT)} cells)', True)
    print(f'Part A done ({time.time() - t0:.0f}s)', flush=True)


# ------------------------------------------------------------------ Part B
def part_b():
    t0 = time.time(); rows = []; NP = 30000
    order = [PRIMARY] + [s for s in np.array(SETTINGS, dtype=object)[np.random.default_rng(9000).permutation(len(SETTINGS))].tolist() if tuple(s) != PRIMARY]
    order = [tuple(s) for s in order]
    pools = {'correlated settings': deg_pool(NP, 9000, order, leads=(0, 10)),
             'independent realisations': deg_pool(NP, 9001, order, independent=True, leads=(0, 10))}
    print(f'B pools built ({time.time() - t0:.0f}s)', flush=True)
    ci = 0
    RHOS_B = (50, 1000)
    for typ, (L, S, A) in pools.items():
        Sg = {key: grid_up(v, TAU_DEG) for key, v in S.items()}
        perf_rate = len(L) / (L - 1).sum(); NG = len(order)
        for lead in (0, 10):
            SG = np.stack([Sg[(g, lead)] for g in range(NG)], 1)                                  # (N, G) grid scores
            # true (pool) failure probability and cost rate of every (setting, threshold): planned iff tau >= score
            pf_true = np.zeros((NG, len(TAU_DEG))); use_mean = np.zeros((NG, len(TAU_DEG)))
            for g in range(NG):
                Pg = TAU_DEG[None, :] >= SG[:, g][:, None]
                pf_true[g] = 1 - Pg.mean(0); use_mean[g] = np.where(Pg, A[:, g, :] + 1.0 + lead, L[:, None]).mean(0)
            rate_true = {rho: ((1 - pf_true) + rho * pf_true) / use_mean for rho in RHOS_B}
            for G in (1, 4, 12, 36):
                if typ == 'independent realisations' and G == 1: continue
                for n in NS:
                    ci += 1; rng = np.random.default_rng(9400 + ci)
                    acc = {rho: dict(pf=[], rr=[], pf_cat=[], rr_cat=[]) for rho in RHOS_B}
                    for _ in range(REPS):
                        u = rng.integers(0, len(L), n)
                        Pl = TAU_DEG[None, None, :] >= SG[u, :G][:, :, None]                       # (n, G, T)
                        use = np.where(Pl, A[u, :G, :] + 1.0 + lead, L[u][:, None, None]).sum(0)
                        nf = (~Pl).sum(0)
                        if G == 1:
                            th, cert = C.tau_hat(SG[u, 0], 0.05); j0 = C.certified_column(TAU_DEG, th, cert)
                        for rho in RHOS_B:
                            r = (n - nf + rho * nf) / use; g, j = np.unravel_index(int(np.argmin(r)), r.shape)
                            a = acc[rho]; a['pf'].append(pf_true[g, j]); a['rr'].append(rate_true[rho][g, j] / perf_rate)
                            if G == 1:
                                rc = np.where(np.arange(len(TAU_DEG)) >= j0, r[0], np.inf); j1 = int(np.argmin(rc))
                                a['pf_cat'].append(pf_true[0, j1]); a['rr_cat'].append(rate_true[rho][0, j1] / perf_rate)
                    for rho in RHOS_B:
                        a = acc[rho]; pf = np.array(a['pf']); rr = np.array(a['rr'])
                        row = dict(type=typ, lead=lead, rho=rho, G=G, n=n, p_fail_plain=pf.mean(), mcse=pf.std() / np.sqrt(REPS),
                                   bound=min(1.0, G / (n + 1)), single=1 / (n + 1), cost_plain=rr.mean(), cost_plain_p95=np.quantile(rr, 0.95),
                                   best_fixed_cost=float(rate_true[rho][:G].min() / perf_rate))
                        if G == 1:
                            row.update(p_fail_cat=np.mean(a['pf_cat']), mcse_cat=np.std(a['pf_cat']) / np.sqrt(REPS),
                                       cost_cat=np.mean(a['rr_cat']), cost_cat_p95=np.quantile(a['rr_cat'], 0.95))
                        rows.append(row)
                    print(f'B {typ} lead {lead} G {G} n {n} done ({time.time() - t0:.0f}s)', flush=True)
    B = pd.DataFrame(rows); B.to_csv(f'{OUT}/sim_selection.csv', index=False)
    hi = B[B.rho == 1000]
    chk(f'B Theorem 2 (rho = 1000): realised P(fail) of plain minimisation <= min(1, G/(n+1)) + 3 MCSE in '
        f'{int((hi.p_fail_plain <= hi.bound + 3 * hi.mcse).sum())}/{len(hi)} cells', bool((hi.p_fail_plain <= hi.bound + 3 * hi.mcse).all()))
    one = hi[hi.G == 1]
    chk(f'B Theorem 2, single setting (rho = 1000): P(fail) <= 1/(n+1) + 3 MCSE in {int((one.p_fail_plain <= one.single + 3 * one.mcse).sum())}/{len(one)} cells',
        bool((one.p_fail_plain <= one.single + 3 * one.mcse).all()))
    print(f'Part B done ({time.time() - t0:.0f}s)', flush=True)


# ------------------------------------------------------------------ Part C
def part_c():
    t0 = time.time(); rows = []; sigma = 0.4
    def policy_tr(mu, valid, TF, kind, ratio):
        if kind == 'P1 p=c_p/c_c':
            p1 = ndtr((np.log(DT) - mu) / sigma); f = (p1 >= ratio) & valid
        else:                                                    # age replacement on the grid at T = 180 (fixed)
            f = (TGRID[None, :] >= 180) & valid
        k = np.argmax(f, axis=1); return np.where(f.any(1), TGRID[k], np.inf)
    TFb, xb, vb, eb = sim_pool(sigma, 200000, 9200); mub = np.log(np.where(vb, TFb[:, None] - TGRID[None, :], 1.0)) + eb
    for kind, ratio in (('P1 p=c_p/c_c', 0.1), ('P1 p=c_p/c_c', 0.01), ('age T=180', 0.1)):
        cp, cc = 1.0, 1.0 / ratio
        Cb, Tb = K.lifecycle(policy_tr(mub, vb, TFb, kind, ratio), TFb, cp, cc); Mtrue = K.m_hat(Cb, Tb, TFb, DT, cp, cc, 'truth')
        for n in (20, 100):
            rng = np.random.default_rng(9200 + n + int(100 * ratio)); cov = {'Eq. 7': [], 'influence': [], 'bootstrap': []}; wid = {k: [] for k in cov}
            for r in range(5000):
                u = rng.integers(0, len(TFb), n); TF = TFb[u]; Cc, Tt = Cb[u], Tb[u]
                M, lo, hi = K.m_with_ci(Cc, Tt, TF, DT, cp, cc, 'cov'); cov['Eq. 7'].append(lo <= Mtrue <= hi); wid['Eq. 7'].append(hi - lo)
                M, lo, hi = C.m_influence_ci(Cc, Tt, TF, DT, cp, cc); cov['influence'].append(lo <= Mtrue <= hi); wid['influence'].append(hi - lo)
                Cp, Tp = K.lifecycle(K.perfect_tr(TF, DT), TF, cp, cc); idx = rng.integers(0, n, (2000, n))
                bm = (Cc[idx].sum(1) / Tt[idx].sum(1)) / (Cp[idx].sum(1) / Tp[idx].sum(1)) - 1
                lo, hi = np.percentile(bm, [2.5, 97.5]); cov['bootstrap'].append(lo <= Mtrue <= hi); wid['bootstrap'].append(hi - lo)
            for k in cov:
                rows.append(dict(policy=kind, cp_over_cc=ratio, n=n, interval=k, M_true_pct=100 * Mtrue, coverage=np.mean(cov[k]),
                                 mcse=np.std(cov[k]) / np.sqrt(5000), mean_width_pct=100 * np.mean(wid[k])))
            print(f'C {kind} ratio {ratio} n {n} done ({time.time() - t0:.0f}s)', flush=True)
    # perfect policy: M = 0 by definition
    for n in (20, 100):
        rng = np.random.default_rng(9290 + n); wid7, widi = [], []
        for r in range(1000):
            TF = TFb[rng.integers(0, len(TFb), n)]; Cc, Tt = K.lifecycle(K.perfect_tr(TF, DT), TF, 1.0, 10.0)
            M, lo, hi = K.m_with_ci(Cc, Tt, TF, DT, 1.0, 10.0); wid7.append(hi - lo); M, lo, hi = C.m_influence_ci(Cc, Tt, TF, DT, 1.0, 10.0); widi.append(hi - lo)
        rows.append(dict(policy='perfect', cp_over_cc=0.1, n=n, interval='Eq. 7', M_true_pct=0.0, coverage=1.0, mcse=0.0, mean_width_pct=100 * np.mean(wid7)))
        rows.append(dict(policy='perfect', cp_over_cc=0.1, n=n, interval='influence', M_true_pct=0.0, coverage=1.0, mcse=0.0, mean_width_pct=100 * np.mean(widi)))
    Cv = pd.DataFrame(rows); Cv.to_csv(f'{OUT}/sim_m_coverage.csv', index=False)
    print(Cv.round(4).to_string(index=False))
    chk('C descriptive: coverage of the three intervals for M written to sim_m_coverage.csv', True)
    print(f'Part C done ({time.time() - t0:.0f}s)', flush=True)


if __name__ == '__main__':
    for p in ARGS: {'A': part_a, 'B': part_b, 'C': part_c}[p]()
    with open(f'{OUT}/sim_checks_{"".join(ARGS)}.txt', 'w', newline='\n') as f: f.write('\n'.join(CHECKS) + '\n')
