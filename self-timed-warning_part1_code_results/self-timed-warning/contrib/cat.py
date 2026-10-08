"""Certified alarm thresholds (CAT): unit-level conformal calibration of threshold-crossing end-of-life alarms.

Plan fixed and hashed before any run: contrib/PLAN.md, contrib/PLAN.sha256. Exploratory, plan hashed before the run.

A threshold-crossing alarm with smoothed estimate x_1, x_2, ... and debounce k fires at the first t at which x has stayed
<= tau for k consecutive cycles (rev_experiments.first_idx). With m_t = min_{s <= t} max(x_{s-k+1}, ..., x_s) (the
debounced running minimum), the alarm for tau fires at the first t with m_t <= tau, so the alarm time is non-increasing in
tau (Lemma 1). A replacement is planned iff the alarm leaves more than the lead time l (and, on a decision grid of step dT,
iff the next decision point is before failure); the set of admissible alarm times is {t <= t_max}. Hence

    unplanned failure at threshold tau  <=>  tau < tau*,   tau* = m_{t_max}   (critical threshold; Lemma 2)

and the order statistic tau_hat = S_(ceil((n+1)(1-alpha))) of the critical thresholds of n exchangeable calibration units
gives P(failure of a new unit) <= alpha (Theorem 1). Everything here works on the alarm tables of rev_experiments
(U, ok, ya, ta, L) so that every decision and every cost is identical to the existing cost code.
"""
import math
import numpy as np
import pandas as pd

ALPHAS = [0.01, 0.02, 0.05, 0.10]
ALPHA_PRIMARY = 0.05


# ------------------------------------------------------------------ alarm mechanics
def runmin(x, k):
    """Debounced running minimum m_t = min_{s<=t} max(x_{s-k+1..s}); +inf before k values exist."""
    mk = pd.Series(np.asarray(x, float)).rolling(k, min_periods=k).max().values
    mk = np.where(np.isnan(mk), np.inf, mk)
    return np.minimum.accumulate(mk)


def alarm_index(x, k, thr):
    """Index of the first alarm for every threshold in thr (len(x) if never); identical to rev_experiments.first_idx."""
    return np.searchsorted(-runmin(x, k), -np.asarray(thr, float), side='left')


def last_admissible(y, lead=0.0, dT=None, scale=1.0):
    """Largest index i at which an alarm still gives a planned replacement, -1 if none.
    y: true remaining life at cycles 1..L-1 (model units; strictly decreasing); scale converts model units to cycles
    (battery blocks); lead in cycles. dT None: planned iff y_i * scale > lead (rev_experiments.cost_of).
    dT given: planned iff g(t_i) + lead < L with t_i = (i + 1) * scale,
    g(t) = max(dT, ceil(t/dT) dT). At lead 0 this is kam_fd001.grid_cost."""
    y = np.asarray(y, float)
    if dT is None:
        ok = y * scale > lead
    else:
        t = (np.arange(len(y)) + 1) * scale; L = (y[0] + 1) * scale
        g = np.maximum(dT, np.ceil(t / dT) * dT); ok = g + lead < L
    idx = np.flatnonzero(ok)
    return int(idx[-1]) if len(idx) else -1


def critical_threshold(x, y, k, lead=0.0, dT=None, scale=1.0):
    """Closed form of Lemma 2: tau* = m_{t_max} (continuous), +inf if no admissible alarm time."""
    i = last_admissible(y, lead, dT, scale)
    return float(runmin(x, k)[i]) if i >= 0 else np.inf


def planned_matrix(tab, lead=0.0, dT=None):
    """(U, T) boolean: planned replacement for every unit and every threshold column of an alarm table (cycles)."""
    U, ok, ya, ta, L = tab
    if dT is None:
        return ok & (np.nan_to_num(ya, nan=-np.inf) > lead)
    g = np.where(ok, np.ceil(np.nan_to_num(ta, nan=0.0) / dT) * dT, np.inf); g = np.where(g < dT, dT, g)
    return ok & (g + lead < L[:, None])


def scores_from_table(tab, taus, lead=0.0, dT=None):
    """Critical threshold on the grid: smallest tau in taus with a planned replacement (+inf if none). Checks Lemma 1."""
    pl = planned_matrix(tab, lead, dT)
    assert (np.diff(pl.astype(np.int8), axis=1) >= 0).all(), 'Lemma 1 violated: planned not monotone in tau'
    j = np.argmax(pl, axis=1); has = pl.any(axis=1)
    return np.where(has, np.asarray(taus, float)[j], np.inf)


# ------------------------------------------------------------------ calibration
def order_index(n, alpha):
    """k = ceil((n+1)(1-alpha)) (1-based), guarded against floating-point error."""
    return int(math.ceil((n + 1) * (1 - alpha) - 1e-9))


def tau_hat(scores, alpha):
    """Conformal threshold: k-th smallest score. Returns (tau_hat, certifiable). Not certifiable when k > n or the
    k-th score is +inf (no finite threshold in the grid certifies the level)."""
    s = np.sort(np.asarray(scores, float)); n = len(s); k = order_index(n, alpha)
    if k > n or k < 1 or not np.isfinite(s[k - 1]): return np.nan, False
    return float(s[k - 1]), True


def certified_column(taus, th, certifiable):
    """Column index of the certified threshold in the grid (fallback: largest threshold when not certifiable)."""
    taus = np.asarray(taus, float)
    if not certifiable: return len(taus) - 1
    return int(np.flatnonzero(taus >= th - 1e-9)[0])


def cost_aware_column(tab, taus, j0, lead, rho, cost_fn):
    """CAT-c: column minimising the training cost rate among thresholds >= the certified one (ties: smallest tau)."""
    c, use = cost_fn(tab, lead, rho)
    r = c.sum(0) / use.sum(0); r = np.where(np.arange(len(taus)) >= j0, r, np.inf)
    return int(np.argmin(r))


def cost_1cycle(tab, lead, rho):
    """Renewal-reward cost of every threshold column (rev_experiments.cost_of, 1-cycle decisions)."""
    U, ok, ya, ta, L = tab; planned = ok & (np.nan_to_num(ya, nan=-np.inf) > lead)
    c = np.where(planned, 1.0, rho); use = np.where(planned, np.nan_to_num(ta, nan=0.0) + lead, L[:, None])
    return c, use


def cost_grid(tab, dT, cc):
    """Grid-mapped cost of every column (kam_fd001.grid_cost, lead 0): cost 1 or cc, life-cycle length g or L."""
    U, ok, ya, ta, L = tab; pl = planned_matrix(tab, 0.0, dT)
    g = np.where(ok, np.ceil(np.nan_to_num(ta, nan=0.0) / dT) * dT, np.inf); g = np.where(g < dT, dT, g)
    return np.where(pl, 1.0, cc), np.where(pl, g, L[:, None])


def conformal_quantile(v, alpha):
    """Upper conformal quantile: the ceil((N+1)(1-alpha))-th smallest value (+inf if beyond N)."""
    v = np.sort(np.asarray(v, float)); k = order_index(len(v), alpha)
    return float(v[k - 1]) if k <= len(v) else np.inf


# ------------------------------------------------------------------ secondary: paired influence interval for M
def m_influence_ci(C, T, TF, dT, cp, cc, z=1.959964):
    """M = R / R_p - 1 with R = sum C / sum T and R_p the grid-perfect rate on the same units. First-order (influence
    function) variance that keeps the covariance between the policy and the perfect reference:
    psi_i = [ (C_i - R T_i) / mean(T) - (R / R_p) (Cp_i - R_p Tp_i) / mean(Tp) ] / R_p,  Var(M_hat) ~ sum psi_i^2 / n^2."""
    import kam_metric as K
    C, T, TF = (np.asarray(a, float) for a in (C, T, TF)); n = len(C)
    Cp, Tp = K.lifecycle(K.perfect_tr(TF, dT), TF, cp, cc)
    R = C.sum() / T.sum(); Rp = Cp.sum() / Tp.sum(); M = R / Rp - 1
    psi = ((C - R * T) / T.mean() - (R / Rp) * (Cp - Rp * Tp) / Tp.mean()) / Rp
    se = math.sqrt(max(float((psi ** 2).sum()) / n ** 2, 0.0))
    return M, M - z * se, M + z * se
