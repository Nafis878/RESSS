"""Re-implementation of the decision-oriented metric M of Kamariotis, Tatsis, Chatzi, Goebel & Straub (2024),
Reliability Engineering & System Safety 242, 109723 (arXiv:2306.03759v2), replacement-only decision setting (their
Section 2.3). Equation numbers refer to arXiv v2. This is a re-implementation from the paper; the authors' code is not
available, and nothing here reproduces their numbers.

Conventions (theirs):
  * decisions only at t_k = k * dT, k = 1, 2, ...; a preventive replacement decided at t_k happens at t_k;
  * cost c_p for a preventive replacement at T_R < T_F, c_c for a corrective replacement at the failure time T_F;
  * life-cycle length T_lc = min(T_R, T_F)                                                        (Eq. 8)
  * R_hat = mean(C_m) / mean(T_lc)                                                                 (Eq. 2)
  * perfect policy: preventive replacement at the last grid point strictly before T_F               (Sec. 2.3.1, Eq. 4)
  * M_hat = (R_hat - R_perfect) / R_perfect                                                        (Eq. 6, 9)
  * Var[R_hat] by the first-order (delta-method) formula                                           (Eq. 3)
  * Var[M_hat] = Var[R_hat] / R_perfect^2, the variance of R_perfect being neglected               (Eq. 7)
Sample moments use ddof = 1 (the paper does not state the estimator).

M >= 0 is NOT enforced: m_hat() records every negative value in VIOLATIONS (with a label) and returns it unchanged.
A negative M arises (i) for a policy that acts between grid points, and (ii) in the case of their footnote 1, when c_c is
so close to c_p that letting a unit fail beats replacing it at the last grid point; perfect_with_failure_option() checks
(ii) explicitly.
"""
import math
import numpy as np

VIOLATIONS = []                     # (label, M_hat) for every M_hat < -TOL computed through m_hat()
TOL = 1e-12


def grid_point_at_or_after(t, dT):
    """Map an alarm raised at cycle t (any real t > 0; NaN/inf = no alarm) to the first decision point k*dT >= t, k >= 1."""
    t = np.asarray(t, float); k = np.ceil(t / dT); k = np.where(k < 1, 1, k)
    return np.where(np.isfinite(t), k * dT, np.inf)


def perfect_tr(TF, dT):
    """Perfect policy: last grid point strictly before failure, T_R = k*dT with k = ceil(T_F/dT) - 1; inf if k < 1."""
    TF = np.asarray(TF, float); k = np.ceil(TF / dT) - 1
    return np.where(k >= 1, k * dT, np.inf)


def lifecycle(TR, TF, cp, cc):
    """Cost and length of one life-cycle (Eq. 8): preventive if T_R < T_F, otherwise corrective at T_F.
    A decision point at or beyond the failure time therefore counts as a failure at cost c_c."""
    TR = np.asarray(TR, float); TF = np.asarray(TF, float)
    prev = np.isfinite(TR) & (TR < TF)
    return np.where(prev, cp, cc).astype(float), np.where(prev, TR, TF).astype(float)


def r_hat(C, T):
    """Eq. (2)."""
    return float(np.mean(C) / np.mean(T))


def var_r_hat(C, T):
    """Eq. (3): first-order approximation of Var[R_hat] with sample moments (ddof = 1)."""
    C = np.asarray(C, float); T = np.asarray(T, float); n = len(C)
    EC, ET = C.mean(), T.mean(); VC, VT = C.var(ddof=1), T.var(ddof=1); CCT = np.cov(C, T, ddof=1)[0, 1]
    return float((VC / ET ** 2 + EC ** 2 * VT / ET ** 4 - 2 * EC * CCT / ET ** 3) / n)


def r_perfect(TF, dT, cp, cc):
    """Eq. (4) for the perfect policy of Sec. 2.3.1; returns (R_perfect, number of units with no grid point before T_F)."""
    C, T = lifecycle(perfect_tr(TF, dT), TF, cp, cc)
    return r_hat(C, T), int((C != cp).sum())


def m_hat(C, T, TF, dT, cp, cc, label=''):
    """Eq. (6)/(9). Negative values are recorded in VIOLATIONS and returned unchanged (never clipped)."""
    Rp, _ = r_perfect(TF, dT, cp, cc); M = (r_hat(C, T) - Rp) / Rp
    if M < -TOL: VIOLATIONS.append((label, M))
    return M


def var_m_hat(C, T, TF, dT, cp, cc):
    """Eq. (7)."""
    Rp, _ = r_perfect(TF, dT, cp, cc)
    return var_r_hat(C, T) / Rp ** 2


def m_with_ci(C, T, TF, dT, cp, cc, label=''):
    """M_hat with the normal 95% interval of Eq. (7)."""
    M = m_hat(C, T, TF, dT, cp, cc, label); s = math.sqrt(max(var_m_hat(C, T, TF, dT, cp, cc), 0.0))
    return M, M - 1.959964 * s, M + 1.959964 * s


def paired_boot_mdiff(Ca, Ta, Cb, Tb, TF, dT, cp, cc, B=2000, seed=0):
    """Paired bootstrap over units of M_a - M_b (R_perfect recomputed in every resample). Returns (diff, lo, hi)."""
    Ca, Ta, Cb, Tb, TF = (np.asarray(x, float) for x in (Ca, Ta, Cb, Tb, TF)); n = len(TF)
    Cp, Tp = lifecycle(perfect_tr(TF, dT), TF, cp, cc)
    point = (Ca.sum() / Ta.sum() - Cb.sum() / Tb.sum()) / (Cp.sum() / Tp.sum())
    idx = np.random.default_rng(seed).integers(0, n, size=(B, n))
    d = (Ca[idx].sum(1) / Ta[idx].sum(1) - Cb[idx].sum(1) / Tb[idx].sum(1)) / (Cp[idx].sum(1) / Tp[idx].sum(1))
    return float(point), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def perfect_with_failure_option(TF, dT, cp, cc, iters=100):
    """Their footnote 1: allow each unit either the preventive replacement at the last grid point or a corrective
    replacement at T_F, and minimise the long-run cost rate over these choices (Dinkelbach iteration on the ratio).
    Returns (R_opt, number of units for which failing is optimal). If R_opt < R_perfect, M can be negative."""
    TF = np.asarray(TF, float); TRp = perfect_tr(TF, dT)
    cP = np.where(np.isfinite(TRp), cp, cc); tP = np.where(np.isfinite(TRp), TRp, TF)
    lam = cP.sum() / tP.sum()
    for _ in range(iters):
        fail = (cc - lam * TF) < (cP - lam * tP)
        C = np.where(fail, cc, cP); T = np.where(fail, TF, tP); new = C.sum() / T.sum()
        if abs(new - lam) < 1e-15: break
        lam = new
    return float(lam), int(fail.sum())
