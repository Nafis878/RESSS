"""Unit tests of contrib/cat.py (run from the repository root: python contrib/test_cat.py). Writes out/contrib/test_cat.log.
T1 Lemma 1: alarm index non-increasing in the threshold; identical to rev_experiments.first_idx.
T2 Lemma 2: planned(tau) <=> tau >= tau* for every grid threshold; grid score = smallest grid value >= closed form.
T3 lead time and decision grid: planned matrix and costs identical to rev_experiments.cost_of and kam_fd001.grid_cost.
T4 tau_hat on hand examples (including +inf scores and non-certifiable levels).
T5 Theorem 1, Monte Carlo: P(fail) <= alpha for exchangeable scores (continuous: also > alpha - 1/(n+1); ties: <= alpha).
T6 earliest-of-K combination: planned whenever any member is planned.
T7 secondary: influence interval of M equals kam_metric.m_hat at the point, has zero width for the perfect policy.
T8 combined lead/grid: explicit 21-cycle examples, including replacement exactly at failure and infeasible action times.
"""
import os, sys
ARGV = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'kam')); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np
import rev_experiments as R
import kam_metric as K
import cat as C

LOG = []


def check(name, ok):
    LOG.append(f'{"PASS" if ok else "FAIL"}  {name}'); print(LOG[-1], flush=True)
    return ok


def random_unit(rng, L=None):
    """A noisy decreasing estimate of the remaining life with occasional bumps, and the true remaining life."""
    L = int(rng.integers(30, 160)) if L is None else L
    y = (L - 1 - np.arange(L - 1)).astype(float)
    x = np.minimum(y * np.exp(rng.normal(0, 0.25)) + rng.normal(0, 4, len(y)).cumsum() * 0.3 + rng.normal(0, 3, len(y)), 80.0)
    return x, y


def grid_cost_ref(ok, ta, L, cc, DT):
    """Verbatim logic of kam_fd001.grid_cost with DT as an argument (kam_fd001 fixes DT = 10 and loads data on import)."""
    Lb = L[:, None] if np.ndim(ok) == 2 else L
    g = np.where(ok, np.ceil(np.nan_to_num(ta, nan=0.0) / DT) * DT, np.inf); g = np.where(g < DT, DT, g)
    prev = ok & (g < Lb)
    return np.where(prev, 1.0, cc), np.where(prev, g, Lb), prev


def main():
    rng = np.random.default_rng(0); taus = np.arange(1, 61, 1.0); ok_all = True
    # T1
    t1 = True
    for _ in range(300):
        x, y = random_unit(rng); k = int(rng.choice([1, 2, 3, 5]))
        a = C.alarm_index(x, k, taus); b = R.first_idx(x, k, taus)
        t1 &= np.array_equal(a, b) and bool((np.diff(a) <= 0).all())
    ok_all &= check('T1 Lemma 1: alarm index non-increasing in tau and identical to rev_experiments.first_idx (300 random units)', t1)
    # T2 + T3 on alarm tables
    P = {}
    for u in range(200):
        x, y = random_unit(rng); P[u] = (x, y)
    t2 = t3 = True
    for k in (1, 2, 3, 5):
        tab = R.alarm_table(P, k, taus)
        for lead in (0, 5, 10, 15):
            s = C.scores_from_table(tab, taus, lead)
            pl = C.planned_matrix(tab, lead)
            t2 &= np.array_equal(pl, taus[None, :] >= s[:, None])
            cf = np.array([C.critical_threshold(*P[u], k, lead) for u in tab[0]])
            grid = np.array([taus[taus >= v][0] if np.isfinite(v) and (taus >= v).any() else np.inf for v in cf])
            t2 &= np.array_equal(grid, s)
            for rho in (5, 50):
                c1, u1 = C.cost_1cycle(tab, lead, rho); c2, u2, p2 = R.cost_of(*tab[1:], lead, rho)
                t3 &= np.array_equal(c1, c2) and np.allclose(u1, u2) and np.array_equal(pl, p2)
        for dT in (10.0, 5.0):
            s = C.scores_from_table(tab, taus, 0.0, dT); pl = C.planned_matrix(tab, 0.0, dT)
            t2 &= np.array_equal(pl, taus[None, :] >= s[:, None])
            cf = np.array([C.critical_threshold(*P[u], k, 0.0, dT) for u in tab[0]])
            grid = np.array([taus[taus >= v][0] if np.isfinite(v) and (taus >= v).any() else np.inf for v in cf])
            t2 &= np.array_equal(grid, s)
            cg, ug = C.cost_grid(tab, dT, 10.0); cr, ur, pr = grid_cost_ref(tab[1], tab[3], tab[4], 10.0, dT)
            t3 &= np.array_equal(cg, cr) and np.allclose(ug, ur) and np.array_equal(pl, pr)
            if dT == 10.0:                                                   # the original function itself (its DT is 10)
                import kam_fd001 as KF
                ck, uk, pk, _ = KF.grid_cost(tab[1], tab[3], tab[4], 10.0)
                t3 &= np.array_equal(cg, ck) and np.allclose(ug, uk) and np.array_equal(pl, pk)
    ok_all &= check('T2 Lemma 2: planned(tau) <=> tau >= tau*, grid score = closed form rounded up to the grid (leads 0-15, grids 5 and 10)', t2)
    ok_all &= check('T3 planned matrix and costs identical to rev_experiments.cost_of and the grid_cost logic of kam_fd001', t3)
    # T4
    t4 = C.tau_hat([5, 1, 4, 2, 3], 0.2) == (5.0, True) and C.tau_hat([5, 1, 4, 2, 3], 0.34) == (4.0, True)
    t4 &= C.tau_hat([5, 1, 4, 2, 3], 0.1)[1] is False and C.tau_hat([1, 2, np.inf, 3, 4], 0.2)[1] is False
    t4 &= C.tau_hat([1, 2, np.inf, 3, 4], 0.34) == (4.0, True) and C.order_index(19, 0.05) == 19 and C.order_index(80, 0.05) == 77
    t4 &= C.certified_column(taus, 4.0, True) == 3 and C.certified_column(taus, np.nan, False) == 59
    ok_all &= check('T4 tau_hat and order index on hand examples (k = ceil((n+1)(1-alpha)); +inf scores; non-certifiable levels)', t4)
    # T5 Monte Carlo of Theorem 1
    t5 = True; lines = []
    for n, alpha, kind in ((19, 0.05, 'continuous'), (50, 0.10, 'continuous'), (40, 0.05, 'ties'), (100, 0.02, 'ties')):
        R_ = 200000; g = np.random.default_rng(1)
        S = g.random((R_, n + 1)) if kind == 'continuous' else g.integers(0, 8, (R_, n + 1)).astype(float)
        k = C.order_index(n, alpha); th = np.sort(S[:, :n], axis=1)[:, k - 1]; fail = S[:, n] > th
        p = fail.mean(); se = fail.std() / np.sqrt(R_)
        ok = p <= alpha + 3 * se and (kind == 'ties' or p >= alpha - 1 / (n + 1) - 3 * se)
        t5 &= ok; lines.append(f'n={n} alpha={alpha} {kind}: P(fail)={p:.4f} (MCSE {se:.4f}), bound [{alpha - 1 / (n + 1):.4f}, {alpha}]')
    ok_all &= check('T5 Theorem 1 Monte Carlo: ' + '; '.join(lines), t5)
    # T6 earliest-of-K
    t6 = True
    for _ in range(200):
        x, y = random_unit(rng); members = [np.minimum(x + rng.normal(0, 3, len(x)), 80) for _ in range(5)]
        ths = rng.uniform(5, 40, 5); lead = 10
        idx = [int(C.alarm_index(m, 2, [t])[0]) for m, t in zip(members, ths)]
        planned = [i < len(y) and y[i] > lead for i in idx]; i0 = min(idx)
        comb = i0 < len(y) and y[i0] > lead
        t6 &= (comb == any(planned))
    ok_all &= check('T6 earliest-of-K alarm is planned iff at least one member alarm is planned (200 random cases)', t6)
    # T7 influence interval
    g = np.random.default_rng(3); TF = g.normal(225, 40, 300).clip(60); dT, cp, cc = 10.0, 1.0, 10.0
    TR = K.perfect_tr(TF, dT); Cc, Tt = K.lifecycle(TR, TF, cp, cc); M, lo, hi = C.m_influence_ci(Cc, Tt, TF, dT, cp, cc)
    t7 = abs(M) < 1e-12 and abs(hi - lo) < 1e-12
    TR2 = np.where(g.random(300) < 0.9, np.maximum(dT, np.floor((TF - g.uniform(5, 40, 300)) / dT) * dT), np.inf)
    C2, T2 = K.lifecycle(TR2, TF, cp, cc); M2, lo2, hi2 = C.m_influence_ci(C2, T2, TF, dT, cp, cc)
    t7 &= abs(M2 - K.m_hat(C2, T2, TF, dT, cp, cc, 'test')) < 1e-12 and lo2 < M2 < hi2
    ok_all &= check(f'T7 influence interval of M: perfect policy M = {M:.1e}, width {hi - lo:.1e}; other policy M = {100 * M2:.2f}% [{100 * lo2:.2f}, {100 * hi2:.2f}]', t7)
    # T8: independent hand-worked trajectories, strict action deadline.
    x = y = np.arange(20, 0, -1, dtype=float); tt = np.arange(1, 21, dtype=float)
    examples = [(1, 0, 10, 1), (1, 1, 10, 11), (1, 10, 10, 11), (1, 11, 10, np.inf),
                (1, 1, 5, 6), (1, 6, 5, 11), (2, 0, 10, 2), (2, 1, 10, 12)]
    t8 = True
    for k, lead, grid, expected in examples:
        tab = R.alarm_table({1: (x, y)}, k, tt)
        score = C.scores_from_table(tab, tt, lead, grid)[0]
        t8 &= score == expected and C.critical_threshold(x, y, k, lead, grid) == expected
        planned = C.planned_matrix(tab, lead, grid)[0]
        t8 &= np.array_equal(planned, tt >= expected)
    ok_all &= check('T8 combined grid and nonzero lead: eight hand-worked strict-deadline cases, including infeasible actions', bool(t8))
    os.makedirs('out/contrib', exist_ok=True)
    open('out/contrib/test_cat.log', 'w', newline='\n').write('\n'.join(LOG) + f'\n{"ALL TESTS PASSED" if ok_all else "TESTS FAILED"}\n')
    print('ALL TESTS PASSED' if ok_all else 'TESTS FAILED')
    if not ok_all: raise SystemExit(1)


if __name__ == '__main__':
    main()
