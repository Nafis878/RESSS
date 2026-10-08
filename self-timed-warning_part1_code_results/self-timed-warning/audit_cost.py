"""Audit of the maintenance-cost comparison and of assumption A1 of Proposition 1 (post hoc; exploratory).

Same outer folds, inner folds, seeds, model, features and renewal-reward cost model as rev_experiments.py. For every
(dataset, lead time l, cost ratio rho) the following policies are tuned on the training units' out-of-fold (OOF)
predictions and applied once to the test units:
  age            optimal age replacement, age chosen on training lives
  STW_window     settings (cap, span, debounce, shift) tuned to the window for each warning level H in {10,...,40};
                 H chosen by training cost (the policy therefore also uses cost, but only to choose among 5 levels)
  STW_cost       cap, span, debounce and alarm threshold tau in {1,...,60} chosen to minimise the training cost rate
  STW_cost_1se   same grid; one-standard-error rule: among settings whose training cost rate is within one bootstrap
                 standard error of the minimum, the one with the largest mean true remaining life at the alarm
  STW_cost_q80   same grid; minimise the 80th percentile of the bootstrap distribution of the training cost rate
  Q10_cost       probabilistic alarm: gradient-boosted 10 % quantile of remaining life (pinball loss, same
                 hyperparameters, target capped at the largest cap); alarm when the smoothed quantile stays <= tau for k
                 cycles; span, k, tau chosen to minimise the training cost rate
  Q10_cost_1se   same with the one-standard-error rule
  HI_cost        health-indicator threshold alarm (as rev_experiments.py), cost-tuned
  capacity_cost, capacity_cost_1se   (battery only) threshold on the measured discharge capacity, cost-tuned
  perfect_foresight, run_to_failure  reference bounds
Bootstrap: 200 resamples of the training units (seed 2026 + fold). Battery: training-only block length kappa per fold
(audit_confirmations.py) and lead times in cycles {0, 15, 30, 45}, converted to blocks; engines: lead times {0, 5, 10, 15}.
Assumption A1: for the test units of each fold, with the window-tuned settings at H = 20, the shift is varied over the grid
and the alarm time, the unshifted error eps at the alarm and the realised in-window indicator are recorded.
Usage: python audit_cost.py DATASET [DATASET ...]      Output: out/audit/cost_<ds>.csv, out/audit/shift_<ds>.pkl
"""
import sys, os, pickle, time
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
import eol_window2 as W
import rev_experiments as R
import audit_confirmations as AC
import battery_warning as BW
from safe_common import outer_folds

RHOS = [5, 10, 20, 50]; NB = 200; OUT = 'out/audit'
os.makedirs(OUT + '/ckpt', exist_ok=True)


def models_ext(feats, train_u, target_u):
    """identical to rev_experiments.models, plus a 10 % quantile model"""
    F, Y = feats(train_u, np.unique(np.concatenate([train_u, target_u])))
    X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u]); out = {}
    for cap in W.CAPS:
        m = W.gbm(X, y, cap); out[cap] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
    p = (X.shape[1] - 1) // 5
    rows = [(F[u][:, :p], Y[u]) for u in train_u]
    Xh = np.vstack([np.vstack([f[:30], f[r <= 5]]) for f, r in rows])
    yh = np.concatenate([np.concatenate([np.zeros(min(30, len(f))), np.ones((r <= 5).sum())]) for f, r in rows])
    A = np.column_stack([Xh, np.ones(len(Xh))]); w = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ yh)
    out['HI'] = {u: (F[u][:-1, :p] @ w[:-1] + w[-1], Y[u][:-1]) for u in target_u}
    mq = HistGradientBoostingRegressor(loss='quantile', quantile=0.1, max_iter=500, learning_rate=0.05, max_leaf_nodes=31,
                                       min_samples_leaf=40, random_state=0).fit(X, np.minimum(y, max(W.CAPS)))
    out['Q10'] = {u: (mq.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
    if 'cap' in F:                                           # battery: raw discharge capacity
        out['CAP'] = {u: (F['cap'][u][:-1], Y[u][:-1]) for u in target_u}
    return out


def boot_weights(n, seed):
    rng = np.random.default_rng(seed); idx = rng.integers(0, n, size=(NB, n)); w = np.zeros((NB, n))
    for b in range(NB): w[b] = np.bincount(idx[b], minlength=n)
    return w


def select(tabs, l, rho, rule, wts):
    """tabs: {key: (train table, test table)}; returns (key, column) of the selected setting"""
    stats = []
    for key, ((U, ok, ya, ta, L), _) in tabs.items():
        c, use, _ = R.cost_of(ok, ya, ta, L, l, rho); r = c.sum(0) / use.sum(0)
        rb = (wts @ c) / (wts @ use) if rule != 'plain' else None
        stats.append((key, r, rb, np.where(ok, ya, 0.0).mean(0)))
    if rule == 'plain':
        return min(((k, int(np.argmin(r)), r.min()) for k, r, _, _ in stats), key=lambda t: t[2])[:2]
    if rule == 'q80':
        return min(((k, int(np.argmin(np.quantile(rb, .8, axis=0))), np.quantile(rb, .8, axis=0).min()) for k, r, rb, _ in stats), key=lambda t: t[2])[:2]
    kmin, jmin, rmin = min(((k, int(np.argmin(r)), r.min()) for k, r, _, _ in stats), key=lambda t: t[2])
    se = [rb[:, jmin] for k, r, rb, _ in stats if k == kmin][0].std()
    cand = [(lead[j], -r[j], k, j) for k, r, rb, lead in stats for j in np.flatnonzero(r <= rmin + se)]
    _, _, k, j = max(cand)
    return k, int(j)


def apply(tab, j, l, rho):
    U, ok, ya, ta, L = tab; c, use, pl = R.cost_of(ok[:, j], ya[:, j], ta[:, j], L, l, rho); return U, c, use, pl, ya[:, j]


def run(ds):
    t0 = time.time()
    if ds == 'Battery':
        S, Lc = AC.battery_cycles(); units = np.sort(Lc.index.values); leads_c = [0, 15, 30, 45]
    else:
        units, feats_ds = R.adapter(ds); leads_c = [0, 5, 10, 15]
    rows, shiftrec = [], []
    for fold, test_u in enumerate(outer_folds(units), 1):
        ck = f'{OUT}/ckpt/cost_{ds}_fold{fold}.pkl'
        if os.path.exists(ck):
            a, b = pickle.load(open(ck, 'rb')); rows += a; shiftrec += b; print(f'{ds} fold {fold} from checkpoint', flush=True); continue
        n0, s0 = len(rows), len(shiftrec)
        train_u = np.setdiff1d(units, test_u)
        if ds == 'Battery':
            kap = AC.kap_rule(Lc[train_u].values); Bf = AC.battery_blocks(S, kap, Lc, train_u)
            def feats(stat_u, use_u, Bf=Bf):
                F, Y = BW.features(Bf[Bf.cell.isin(np.concatenate([stat_u, use_u]))], stat_u)
                F['cap'] = {u: g.QDischarge.values for u, g in Bf[Bf.cell.isin(use_u)].groupby('cell')}
                return F, Y
        else:
            kap = 1; feats = feats_ds
        inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5)
        oof = {}
        for iu in inner:
            p = models_ext(feats, np.setdiff1d(train_u, iu), iu)
            for c in p: oof.setdefault(c, {}).update(p[c])
        fin = models_ext(feats, train_u, test_u)
        Loof = np.array([y[0] + 1 for _, y in oof[W.CAPS[0]].values()])
        wts = boot_weights(len(oof[W.CAPS[0]]), 2026 + fold)
        # ---- window-tuned settings per H (identical to rev_experiments)
        stw_sel = {}
        for H in R.HS:
            best = None
            for cap in W.CAPS:
                if cap < H + 20: continue
                for sp in W.SPANS:
                    Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
                    for k in W.KS:
                        tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                        if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
            stw_sel[H] = best[1:]
        WIN = {}
        for H, (cap, sp, k, s) in stw_sel.items():
            WIN[H] = (R.alarm_table({u: (W.smooth(p, sp) + s, y) for u, (p, y) in oof[cap].items()}, k, [H]),
                      R.alarm_table({u: (W.smooth(p, sp) + s, y) for u, (p, y) in fin[cap].items()}, k, [H]))
        # ---- threshold tables
        def ttab(src, keys, thr, sign=1.0):
            return {key: (R.alarm_table({u: (sign * W.smooth(p, key[-2]), y) for u, (p, y) in oof[src(key)].items()}, key[-1], thr),
                          R.alarm_table({u: (sign * W.smooth(p, key[-2]), y) for u, (p, y) in fin[src(key)].items()}, key[-1], thr)) for key in keys}
        STW = ttab(lambda key: key[0], [(c, sp, k) for c in W.CAPS for sp in W.SPANS for k in W.KS], R.TAUS)
        Q10 = ttab(lambda key: 'Q10', [('q', sp, k) for sp in W.SPANS for k in W.KS], R.TAUS)
        hv = np.concatenate([s[y <= 80] for s, y in oof['HI'].values()]); THETA = np.unique(np.quantile(hv, np.linspace(0.02, 0.995, 120)))
        HI = ttab(lambda key: 'HI', [('h', sp, k) for sp in W.SPANS for k in W.KS], -THETA, sign=-1.0)
        if ds == 'Battery':
            qv = np.concatenate([s[y <= 80] for s, y in oof['CAP'].values()]); QT = np.unique(np.quantile(qv, np.linspace(0.02, 0.995, 120)))
            CAPT = ttab(lambda key: 'CAP', [('c', sp, k) for sp in W.SPANS for k in W.KS], QT)
        Ts = np.arange(1, int(Loof.max()) + 1)
        Lte = {u: y[0] + 1 for u, (_, y) in fin[W.CAPS[0]].items()}
        for lc in leads_c:
            l = lc / kap
            for rho in RHOS:
                pols = {'STW_window': (WIN, lambda: (min(R.HS, key=lambda H: (lambda c, u, _: c.sum() / u.sum())(*R.cost_of(*WIN[H][0][1:], l, rho))), 0)),
                        'STW_cost': (STW, lambda: select(STW, l, rho, 'plain', wts)),
                        'STW_cost_1se': (STW, lambda: select(STW, l, rho, '1se', wts)),
                        'STW_cost_q80': (STW, lambda: select(STW, l, rho, 'q80', wts)),
                        'Q10_cost': (Q10, lambda: select(Q10, l, rho, 'plain', wts)),
                        'Q10_cost_1se': (Q10, lambda: select(Q10, l, rho, '1se', wts)),
                        'HI_cost': (HI, lambda: select(HI, l, rho, 'plain', wts))}
                if ds == 'Battery':
                    pols['capacity_cost'] = (CAPT, lambda: select(CAPT, l, rho, 'plain', wts))
                    pols['capacity_cost_1se'] = (CAPT, lambda: select(CAPT, l, rho, '1se', wts))
                for name, (tab, chooser) in pols.items():
                    key, j = chooser(); U, c, use, pl, yat = apply(tab[key][1], j, l, rho)
                    for ui, u in enumerate(U):
                        rows.append(dict(fold=fold, kappa=kap, lead_cycles=lc, rho=rho, policy=name, unit=u, cost=c[ui], use=use[ui] * kap,
                                         fail=not pl[ui], rul_at_alarm=yat[ui] * kap if np.isfinite(yat[ui]) else np.nan, setting=f'{key}|{j}'))
                cr = np.array([np.where(Loof > T, 1.0, rho).sum() / np.minimum(Loof, T).sum() for T in Ts]); T = Ts[int(np.argmin(cr))]
                for u, Lu in Lte.items():
                    rows.append(dict(fold=fold, kappa=kap, lead_cycles=lc, rho=rho, policy='age', unit=u, cost=1.0 if Lu > T else rho, use=min(Lu, T) * kap, fail=Lu <= T, rul_at_alarm=np.nan, setting=str(T)))
                    rows.append(dict(fold=fold, kappa=kap, lead_cycles=lc, rho=rho, policy='perfect_foresight', unit=u, cost=1.0, use=(Lu - 1) * kap, fail=False, rul_at_alarm=kap, setting=''))
                    rows.append(dict(fold=fold, kappa=kap, lead_cycles=lc, rho=rho, policy='run_to_failure', unit=u, cost=rho, use=Lu * kap, fail=True, rul_at_alarm=0, setting=''))
        # ---- assumption A1: vary the shift with the H = 20 window-tuned settings, test units
        cap, sp, k, s_sel = stw_sel[20]
        for u, (p, y) in fin[cap].items():
            sm = W.smooth(p, sp); i = R.first_idx(sm, k, 20 - W.SHIFTS); ok = i < len(sm); ii = np.minimum(i, len(sm) - 1)
            shiftrec.append(dict(fold=fold, unit=u, s_sel=s_sel, ok=ok, cycle=np.where(ok, ii + 1, np.nan), y=np.where(ok, y[ii], np.nan), eps=np.where(ok, sm[ii] - y[ii], np.nan)))
        pickle.dump((rows[n0:], shiftrec[s0:]), open(ck + '.tmp', 'wb')); os.replace(ck + '.tmp', ck)
        print(f'{ds} fold {fold} done ({time.time() - t0:.0f}s, kappa {kap})', flush=True)
    pd.DataFrame(rows).to_csv(f'{OUT}/cost_{ds}.csv', index=False)
    pickle.dump(dict(shifts=W.SHIFTS, rec=shiftrec), open(f'{OUT}/shift_{ds}.pkl', 'wb'))


if __name__ == '__main__':
    for ds in ARGS: run(ds)
