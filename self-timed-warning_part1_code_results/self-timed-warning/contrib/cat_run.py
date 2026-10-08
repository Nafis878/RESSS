"""Phases 2-3: certified alarm thresholds (CAT) on the engine datasets (contrib/PLAN.md with Amendment 1; exploratory, plan
hashed before the run). Same outer folds (seed 2026), inner folds (seed 100 + fold), regressor, features and cost model as
rev_experiments.py / audit_cost.py / kam/kam_fd001.py.

Amendment 1: the gradient-boosted fits of this machine differ in floating point from the frozen (Linux) fits, so CAT is
compared with baselines recomputed here from the SAME predictions, with code copied from audit_cost.py (cost policies) and
kam/kam_fd001.py (policies under the metric M). contrib/cat_equiv.py checks that the copies give the same decisions as
the original scripts run on this machine (FD001, fold 1).

Per outer fold:
  * inner models (fitted on four inner folds) predict their held-out inner fold (out-of-fold, OOF) and, for CAT-KMIN, the
    outer test units; final models are refitted on all outer training units; CAT-SPLIT fits the selected cap on a random
    half of the training units (seed 500 + fold) and calibrates on the other half;
  * models: capped GBM 40/60/90, 10 % quantile GBM and linear health indicator (audit_cost.models_ext); FD001-FD004 also
    cap 125 and the classifier of RUL <= 10 (kam_fd001.fit_models);
  * window-tuned settings for every H; the CAT setting (cap, span, debounce) is the window-tuned setting at H = 20;
  * cost policies of audit_cost.py for every lead time and cost ratio; CAT variants for every lead time and alpha: bare
    certified threshold (CAT-CF primary, CAT-SPLIT, CAT-KMIN), cost-aware CAT-c (CF), per-time-step conformal lower bound
    (PT), ablations 'setting chosen by plain training cost' and 'Bonferroni over the 27 settings (alpha / 27)';
  * FD001-FD004: the policies of kam_fd001.py and the CAT variants under the conventions of M (grid 10, lead 0).
Usage: python contrib/cat_run.py DATASET     (PHM08 FD001 FD002 FD003 FD004 NCMAPSS6)
Outputs (out/contrib/): <ds>_cost.csv, <ds>_M.csv (FD001-FD004), <ds>_settings.csv, <ds>_scores.csv.gz, <ds>_selected.csv,
<ds>_window20.csv; checkpoints out/contrib/ckpt/<ds>_fold<f>.pkl.
"""
import os, sys, time, pickle
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'kam')); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
import eol_window2 as W
import rev_experiments as R
import audit_cost as CO
import kam_metric as K
import kam_fd001 as KF
from safe_common import outer_folds
import cat as C

OUT = 'out/contrib'; os.makedirs(OUT + '/ckpt', exist_ok=True)
H_CAT = 20; DT = KF.DT; QS = KF.QS; M_DS = ('FD001', 'FD002', 'FD003', 'FD004')
SETS = [(c, sp, k) for c in W.CAPS for sp in W.SPANS for k in W.KS]


def fit_all(feats, train_u, target_u, with_m=False, caps=None):
    """audit_cost.models_ext (caps 40/60/90, HI, Q10) and, with_m, kam_fd001.fit_models extras (cap 125, classifier);
    caps given: only those capped regressors. Statistics and models from train_u; series over cycles with RUL >= 1."""
    F, Y = feats(train_u, np.unique(np.concatenate([train_u, target_u])))
    X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u]); out = {}
    for cap in (caps if caps is not None else W.CAPS + ([KF.CAP_SENS] if with_m else [])):
        m = W.gbm(X, y, cap); out[cap] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
    if caps is not None: return out
    p = (X.shape[1] - 1) // 5
    rows = [(F[u][:, :p], Y[u]) for u in train_u]
    Xh = np.vstack([np.vstack([f[:30], f[r <= 5]]) for f, r in rows])
    yh = np.concatenate([np.concatenate([np.zeros(min(30, len(f))), np.ones((r <= 5).sum())]) for f, r in rows])
    A = np.column_stack([Xh, np.ones(len(Xh))]); w = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ yh)
    out['HI'] = {u: (F[u][:-1, :p] @ w[:-1] + w[-1], Y[u][:-1]) for u in target_u}
    mq = HistGradientBoostingRegressor(loss='quantile', quantile=0.1, max_iter=500, learning_rate=0.05, max_leaf_nodes=31,
                                       min_samples_leaf=40, random_state=0).fit(X, np.minimum(y, max(W.CAPS)))
    out['Q10'] = {u: (mq.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
    if with_m:
        c = KF.classifier().fit(X, (y <= DT).astype(int))
        out['CLS'] = {u: (c.predict_proba(F[u])[:-1, 1], Y[u][:-1]) for u in target_u}
    return out


def window_select(oof, H):
    best = None
    for cap in W.CAPS:
        if cap < H + 20: continue
        for sp in W.SPANS:
            Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
            for k in W.KS:
                tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
    return best[1:]


def tab_of(P, sp, k, thr, shift=0.0, sign=1.0):
    return R.alarm_table({u: (sign * W.smooth(p, sp) + shift, y) for u, (p, y) in P.items()}, k, thr)


def col(tab, j):
    U, ok, ya, ta, L = tab; return U, ok[:, j], ya[:, j], ta[:, j], L


def combine_earliest(cols):
    """Earliest of several single-threshold alarms (same unit order): (U, ok, ya, ta, L)."""
    U = cols[0][0]; L = cols[0][4]
    ta = np.stack([np.where(t[1], t[3], np.inf) for t in cols], 1); ya = np.stack([np.where(t[1], t[2], -np.inf) for t in cols], 1)
    j = np.argmin(ta, axis=1); ok = np.isfinite(ta[np.arange(len(U)), j])
    return U, ok, np.where(ok, ya[np.arange(len(U)), j], np.nan), np.where(ok, ta[np.arange(len(U)), j], np.nan), L


def run_fold(ds, units, feats, fold, test_u, leads):
    t0 = time.time(); train_u = np.setdiff1d(units, test_u); with_m = ds in M_DS
    inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5)
    assert not set(train_u) & set(test_u) and sorted(np.concatenate(inner).tolist()) == sorted(train_u.tolist()), 'E1'
    oof = {}; inner_test = []; inner_units = []
    for iu in inner:
        itr = np.setdiff1d(train_u, iu); assert not set(itr) & set(test_u) and not set(itr) & set(iu), 'E1'
        P = fit_all(feats, itr, np.concatenate([iu, test_u]), with_m)
        for c in P: oof.setdefault(c, {}).update({u: P[c][u] for u in iu})
        inner_test.append({c: {u: P[c][u] for u in test_u} for c in W.CAPS}); inner_units.append(iu)
    fin = fit_all(feats, train_u, test_u, with_m)
    wts = CO.boot_weights(len(oof[W.CAPS[0]]), 2026 + fold)
    Loof = np.array([y[0] + 1 for _, y in oof[W.CAPS[0]].values()]); Lte = {u: y[0] + 1 for u, (_, y) in fin[W.CAPS[0]].items()}
    stw_sel = {H: window_select(oof, H) for H in R.HS}
    cap, sp, k, s20 = stw_sel[H_CAT]; g0 = (cap, sp, k)
    perm = np.random.default_rng(500 + fold).permutation(train_u); A_u = np.sort(perm[:len(perm) // 2]); B_u = np.sort(perm[len(perm) // 2:])
    assert not set(A_u) & set(B_u) and not (set(A_u) | set(B_u)) ^ set(train_u) and not (set(A_u) | set(B_u)) & set(test_u), 'E1 split'
    SP = fit_all(feats, A_u, np.concatenate([B_u, test_u]), caps=[cap])[cap]
    sp_cal = {u: SP[u] for u in B_u}; sp_test = {u: SP[u] for u in test_u}

    # ---- tables (audit_cost.py / kam_fd001.py)
    w20 = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in fin[cap].items()}, H_CAT, k, s20).assign(fold=fold)
    WIN = {H: (tab_of(oof[c], spp, kk, [H], s), tab_of(fin[c], spp, kk, [H], s)) for H, (c, spp, kk, s) in stw_sel.items()}
    STW = {key: (tab_of(oof[key[0]], key[1], key[2], R.TAUS), tab_of(fin[key[0]], key[1], key[2], R.TAUS)) for key in SETS}
    Q10 = {('q', spp, kk): (tab_of(oof['Q10'], spp, kk, R.TAUS), tab_of(fin['Q10'], spp, kk, R.TAUS)) for spp in W.SPANS for kk in W.KS}
    hv = np.concatenate([s[y <= 80] for s, y in oof['HI'].values()]); THETA = np.unique(np.quantile(hv, np.linspace(0.02, 0.995, 120)))
    HIT = {('h', spp, kk): (tab_of(oof['HI'], spp, kk, -THETA, sign=-1.0), tab_of(fin['HI'], spp, kk, -THETA, sign=-1.0)) for spp in W.SPANS for kk in W.KS}
    tab_o, tab_t = STW[g0]
    kmin_cal = [tab_of({u: oof[cap][u] for u in iu}, sp, k, R.TAUS) for iu in inner_units]
    kmin_test = [tab_of(it[cap], sp, k, R.TAUS) for it in inner_test]
    split_cal = tab_of(sp_cal, sp, k, R.TAUS); split_test = tab_of(sp_test, sp, k, R.TAUS)
    resid = np.concatenate([W.smooth(p, sp) - y for p, y in oof[cap].values()])
    TF = np.array([Lte[u] for u in tab_t[0]], float)
    for t_ in kmin_test + [split_test]: assert list(t_[0]) == list(tab_t[0]), 'unit order'
    rows, mrows, sets, scs = [], [], [], []

    def emit(name, tab1, lead, rho, extra):
        U, ok, ya, ta, L = tab1; c, use, pl = R.cost_of(ok, ya, ta, L, lead, rho)
        for i, u in enumerate(U):
            rows.append(dict(fold=fold, lead_cycles=lead, rho=rho, policy=name, unit=u, cost=c[i], use=use[i], fail=not pl[i],
                             rul_at_alarm=ya[i] if ok[i] else np.nan, **extra))

    def emit_TR(name, q, TRd, extra):
        TR = np.array([TRd[u] for u in tab_t[0]], float); Cc, T = K.lifecycle(TR, TF, 1.0, 1.0 / q)
        for i, u in enumerate(tab_t[0]):
            mrows.append(dict(protocol='cv', split=fold, q=q, policy=name, unit=u, cost=Cc[i], tlc=T[i], TF=TF[i], TR=TR[i], fail=bool(Cc[i] != 1.0), mapped=True, **extra))

    def emit_m(name, tab1, q, extra):
        U, ok, ya, ta, L = tab1; assert list(U) == list(tab_t[0])
        g = np.where(ok, np.ceil(np.nan_to_num(ta, nan=0.0) / DT) * DT, np.inf); g = np.where(g < DT, DT, g)
        emit_TR(name, q, {u: (g[i] if ok[i] else np.inf) for i, u in enumerate(U)}, extra)

    # ---- cost policies (copy of audit_cost.run, engines: kappa = 1)
    Ts = np.arange(1, int(Loof.max()) + 1)
    for lead in leads:
        for rho in CO.RHOS:
            pols = {'STW_window': (WIN, lambda: (min(R.HS, key=lambda H: (lambda c_, u_, _: c_.sum() / u_.sum())(*R.cost_of(*WIN[H][0][1:], lead, rho))), 0)),
                    'STW_cost': (STW, lambda: CO.select(STW, lead, rho, 'plain', wts)),
                    'STW_cost_1se': (STW, lambda: CO.select(STW, lead, rho, '1se', wts)),
                    'STW_cost_q80': (STW, lambda: CO.select(STW, lead, rho, 'q80', wts)),
                    'Q10_cost': (Q10, lambda: CO.select(Q10, lead, rho, 'plain', wts)),
                    'Q10_cost_1se': (Q10, lambda: CO.select(Q10, lead, rho, '1se', wts)),
                    'HI_cost': (HIT, lambda: CO.select(HIT, lead, rho, 'plain', wts))}
            for name, (tab, chooser) in pols.items():
                key, j = chooser(); emit(name, col(tab[key][1], j), lead, rho, dict(setting=f'{key}|{j}', tau=R.TAUS[j] if tab is not WIN and tab is not HIT else np.nan))
            cr = np.array([np.where(Loof > T, 1.0, rho).sum() / np.minimum(Loof, T).sum() for T in Ts]); T = Ts[int(np.argmin(cr))]
            for u, Lu in Lte.items():
                rows.append(dict(fold=fold, lead_cycles=lead, rho=rho, policy='age', unit=u, cost=1.0 if Lu > T else rho, use=min(Lu, T), fail=Lu <= T, rul_at_alarm=np.nan, setting=str(T)))
                rows.append(dict(fold=fold, lead_cycles=lead, rho=rho, policy='perfect_foresight', unit=u, cost=1.0, use=Lu - 1, fail=False, rul_at_alarm=1.0, setting=''))
                rows.append(dict(fold=fold, lead_cycles=lead, rho=rho, policy='run_to_failure', unit=u, cost=rho, use=Lu, fail=True, rul_at_alarm=0.0, setting=''))

    # ---- CAT (1-cycle decisions)
    for lead in leads:
        S_all = {key: (C.scores_from_table(STW[key][0], R.TAUS, lead), C.scores_from_table(STW[key][1], R.TAUS, lead)) for key in SETS}
        for key, (so, st) in S_all.items():
            scs += [dict(fold=fold, lead_cycles=lead, dT=1, setting=str(key), selected=key == g0, role='oof', unit=u, score=v) for u, v in zip(STW[key][0][0], so)]
            scs += [dict(fold=fold, lead_cycles=lead, dT=1, setting=str(key), selected=key == g0, role='test', unit=u, score=v) for u, v in zip(STW[key][1][0], st)]
        S_cf = S_all[g0][0]; S_sp = C.scores_from_table(split_cal, R.TAUS, lead)
        for alpha in C.ALPHAS:
            th, cert = C.tau_hat(S_cf, alpha); j0 = C.certified_column(R.TAUS, th, cert)
            ths, certs = C.tau_hat(S_sp, alpha); js = C.certified_column(R.TAUS, ths, certs)
            km = [C.tau_hat(C.scores_from_table(kc, R.TAUS, lead), alpha) for kc in kmin_cal]
            jk = [C.certified_column(R.TAUS, t, c_) for t, c_ in km]; certk = all(c_ for _, c_ in km)
            kmin_tab = combine_earliest([col(kt, j) for kt, j in zip(kmin_test, jk)])
            q_pt = C.conformal_quantile(resid, alpha); pt_tab = col(tab_of(fin[cap], sp, k, [lead + q_pt]), 0)
            thb, certb = C.tau_hat(S_cf, alpha / len(SETS))
            sets.append(dict(fold=fold, lead_cycles=lead, dT=1, alpha=alpha, setting=str(g0), n_cf=len(S_cf), tau_cf=th, cert_cf=cert,
                             n_split=len(S_sp), tau_split=ths, cert_split=certs, n_kmin='/'.join(str(len(iu)) for iu in inner_units),
                             tau_kmin='/'.join(f'{t:g}' for t, _ in km), cert_kmin=certk, q_pt=q_pt, tau_pt=lead + q_pt, tau_bonf=thb, cert_bonf=certb,
                             n_inf_cf=int(np.isinf(S_cf).sum())))
            ex = dict(alpha=alpha)
            for rho in CO.RHOS:
                emit(f'CAT_a{alpha}', col(tab_t, j0), lead, rho, dict(ex, tau=R.TAUS[j0], certifiable=cert))
                emit(f'CATsplit_a{alpha}', col(split_test, js), lead, rho, dict(ex, tau=R.TAUS[js], certifiable=certs))
                emit(f'CATkmin_a{alpha}', kmin_tab, lead, rho, dict(ex, tau=np.nan, certifiable=certk))
                emit(f'PT_a{alpha}', pt_tab, lead, rho, dict(ex, tau=lead + q_pt, certifiable=True))
                j1 = C.cost_aware_column(tab_o, R.TAUS, j0, lead, rho, C.cost_1cycle)
                emit(f'CATc_a{alpha}', col(tab_t, j1), lead, rho, dict(ex, tau=R.TAUS[j1], certifiable=cert))
                if alpha == C.ALPHA_PRIMARY:
                    jb = C.certified_column(R.TAUS, thb, certb); jb1 = C.cost_aware_column(tab_o, R.TAUS, jb, lead, rho, C.cost_1cycle)
                    emit('CATc_bonf_a0.05', col(tab_t, jb1), lead, rho, dict(ex, tau=R.TAUS[jb1], certifiable=certb))
                    kp, _ = CO.select(STW, lead, rho, 'plain', wts); thp, certp = C.tau_hat(S_all[kp][0], alpha)
                    jp = C.certified_column(R.TAUS, thp, certp); jp1 = C.cost_aware_column(STW[kp][0], R.TAUS, jp, lead, rho, C.cost_1cycle)
                    emit('CATc_plainset_a0.05', col(STW[kp][1], jp1), lead, rho, dict(ex, tau=R.TAUS[jp1], certifiable=certp, setting=str(kp)))

    # ---- metric M (copy of kam_fd001.run_split policies, mapped) and CAT on the grid
    if with_m:
        cal = KF.cls_calibrator(oof['CLS'])
        Gcls_oof, Loof_d = KF.grid_series({u: (cal.predict(s), y) for u, (s, y) in oof['CLS'].items()})
        Gcls_te, _ = KF.grid_series({u: (cal.predict(s), y) for u, (s, y) in fin['CLS'].items()})
        RES = {c: KF.res_model(oof[c], c) for c in (KF.CAP_RES, KF.CAP_SENS)}
        Gres_oof, _ = KF.grid_series({u: (KF.res_prob(RES[KF.CAP_RES], s), y) for u, (s, y) in oof[KF.CAP_RES].items()})
        Gres_te, _ = KF.grid_series({u: (KF.res_prob(RES[KF.CAP_RES], s), y) for u, (s, y) in fin[KF.CAP_RES].items()})
        Graw_te = {c: KF.grid_series(fin[c])[0] for c in (KF.CAP_RES, KF.CAP_SENS)}
        for q in QS:
            cc = 1.0 / q
            Hg = min(R.HS, key=lambda H: (lambda c_, u_: c_.sum() / u_.sum())(*KF.grid_cost(WIN[H][0][1][:, 0], WIN[H][0][3][:, 0], WIN[H][0][4], cc)[:2]))
            emit_m('STW_window', col(WIN[Hg][1], 0), q, dict(setting=f'H={Hg}'))
            for name, rule in (('STW_cost', 'plain'), ('STW_cost_1se', '1se')):
                key, j = KF.select_grid(STW, cc, rule, wts); emit_m(name, col(STW[key][1], j), q, dict(setting=f'{key}|tau={R.TAUS[j]}'))
            key, j = KF.select_grid(HIT, cc, 'plain', wts); emit_m('HI_cost', col(HIT[key][1], j), q, dict(setting=f'{key}|{j}'))
            for tag, Go, Gt in (('cls', Gcls_oof, Gcls_te), ('res', Gres_oof, Gres_te)):
                emit_TR(f'P1_{tag}_q', q, KF.p1_first(Gt, q), dict(setting=f'p={q}'))
                o = KF.p1_optimise(Go, Loof_d, cc)
                for rule in ('mid', 'max'): emit_TR(f'P1_{tag}_opt_{rule}', q, KF.p1_first(Gt, o[rule]), dict(setting=f'p={o[rule]}'))
            lam = KF.lam_bar(Loof, cc)
            for c in (KF.CAP_RES, KF.CAP_SENS):
                fl = KF.p3_flags(RES[c], lam, cc); emit_TR(f'P3_res{c}', q, KF.p3_first(RES[c], fl, Graw_te[c]), dict(setting=f'lam={lam:.6g}'))
            Tg = np.arange(DT, Loof.max() + DT, DT)
            crg = [np.where(Loof > T, 1.0, cc).sum() / np.minimum(Loof, T).sum() for T in Tg]; Ta = Tg[int(np.argmin(crg))]
            emit_TR('age_grid', q, {u: Ta for u in tab_t[0]}, dict(setting=f'T={Ta}'))
            emit_TR('perfect_grid', q, dict(zip(tab_t[0], K.perfect_tr(TF, DT))), dict(setting=''))
            emit_TR('run_to_failure', q, {u: np.inf for u in tab_t[0]}, dict(setting=''))
        S_all = {key: (C.scores_from_table(STW[key][0], R.TAUS, 0.0, DT), C.scores_from_table(STW[key][1], R.TAUS, 0.0, DT)) for key in SETS}
        for key, (so, st) in S_all.items():
            scs += [dict(fold=fold, lead_cycles=0, dT=DT, setting=str(key), selected=key == g0, role='oof', unit=u, score=v) for u, v in zip(STW[key][0][0], so)]
            scs += [dict(fold=fold, lead_cycles=0, dT=DT, setting=str(key), selected=key == g0, role='test', unit=u, score=v) for u, v in zip(STW[key][1][0], st)]
        S_cf = S_all[g0][0]; S_sp = C.scores_from_table(split_cal, R.TAUS, 0.0, DT)
        for alpha in C.ALPHAS:
            th, cert = C.tau_hat(S_cf, alpha); j0 = C.certified_column(R.TAUS, th, cert)
            ths, certs = C.tau_hat(S_sp, alpha); js = C.certified_column(R.TAUS, ths, certs)
            km = [C.tau_hat(C.scores_from_table(kc, R.TAUS, 0.0, DT), alpha) for kc in kmin_cal]
            jk = [C.certified_column(R.TAUS, t, c_) for t, c_ in km]; certk = all(c_ for _, c_ in km)
            kmin_tab = combine_earliest([col(kt, j) for kt, j in zip(kmin_test, jk)])
            sets.append(dict(fold=fold, lead_cycles=0, dT=DT, alpha=alpha, setting=str(g0), n_cf=len(S_cf), tau_cf=th, cert_cf=cert, n_split=len(S_sp),
                             tau_split=ths, cert_split=certs, tau_kmin='/'.join(f'{t:g}' for t, _ in km), cert_kmin=certk, n_inf_cf=int(np.isinf(S_cf).sum())))
            for q in QS:
                ex = dict(alpha=alpha)
                emit_m(f'CATg_a{alpha}', col(tab_t, j0), q, dict(ex, tau=R.TAUS[j0], certifiable=cert))
                emit_m(f'CATgsplit_a{alpha}', col(split_test, js), q, dict(ex, tau=R.TAUS[js], certifiable=certs))
                emit_m(f'CATgkmin_a{alpha}', kmin_tab, q, dict(ex, tau=np.nan, certifiable=certk))
                j1 = C.cost_aware_column(tab_o, R.TAUS, j0, 0.0, None, lambda t_, l_, r_: C.cost_grid(t_, DT, 1.0 / q))
                emit_m(f'CATgc_a{alpha}', col(tab_t, j1), q, dict(ex, tau=R.TAUS[j1], certifiable=cert))
    sel = dict(fold=fold, cap=cap, span=sp, k=k, shift20=s20, n_train=len(train_u), n_test=len(test_u), n_split_cal=len(B_u))
    print(f'{ds} fold {fold} done ({time.time() - t0:.0f}s; setting {g0})', flush=True)
    return rows, mrows, sets, scs, w20, sel


def main(ds):
    t0 = time.time(); units, feats = R.adapter(ds); leads = [0, 5, 10, 15]; parts = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        ck = f'{OUT}/ckpt/{ds}_fold{fold}.pkl'
        if os.path.exists(ck):
            res = pickle.load(open(ck, 'rb')); check_grid(res[1]); parts.append(res)
            print(f'{ds} fold {fold} from checkpoint', flush=True); continue
        res = run_fold(ds, units, feats, fold, np.sort(test_u), leads)
        check_grid(res[1])
        pickle.dump(res, open(ck + '.tmp', 'wb')); os.replace(ck + '.tmp', ck); parts.append(res)
    rows = sum((p[0] for p in parts), []); mrows = sum((p[1] for p in parts), []); sets = sum((p[2] for p in parts), []); scs = sum((p[3] for p in parts), [])
    pd.DataFrame(rows).to_csv(f'{OUT}/{ds}_cost.csv', index=False)
    if mrows: pd.DataFrame(mrows).to_csv(f'{OUT}/{ds}_M.csv', index=False)
    pd.DataFrame(sets).to_csv(f'{OUT}/{ds}_settings.csv', index=False)
    pd.DataFrame(scs).to_csv(f'{OUT}/{ds}_scores.csv.gz', index=False)
    pd.concat([p[4] for p in parts]).to_csv(f'{OUT}/{ds}_window20.csv', index=False)
    pd.DataFrame([p[5] for p in parts]).to_csv(f'{OUT}/{ds}_selected.csv', index=False)
    print(f'{ds} finished in {time.time() - t0:.0f}s', flush=True)


def check_grid(rows):
    """Enforce the plan's negative-M stop rule before accepting a fold/checkpoint."""
    if not rows: return
    D = pd.DataFrame(rows)
    for (q, policy), g in D.groupby(['q', 'policy']):
        value = K.m_hat(g.cost.values, g.tlc.values, g.TF.values, DT, 1.0, 1.0 / q,
                        f'CAT run {policy}, q={q}')
        assert value >= -1e-12, f'STOP: negative grid-mapped M ({policy}, q={q}, M={value})'


if __name__ == '__main__':
    for ds in ARGS: main(ds)
