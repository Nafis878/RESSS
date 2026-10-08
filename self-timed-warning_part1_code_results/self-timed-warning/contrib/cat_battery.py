"""Phase 3: certified alarm thresholds (CAT) on the battery cells, convention C (fully nested preprocessing, task in cycles),
cross-validation by cell (cv1-cv5) and with each batch held out (lobo1-lobo3). Exploratory, plan hashed before the run
(contrib/PLAN.md).

Same splits, inner folds, block lengths (kappa by the protocol rule per training subset), regressor, thresholds in cycles
(3, 6, ..., 180), lead times (0, 15, 30, 45 cycles) and cost ratios as audit_battery_cost_nested.py, whose functions are
reused. The CAT setting (cap, span, debounce) is the window-tuned setting at H = 60 cycles (the primary physical task).
Reproduction check: STW_window, STW_cost and STW_cost_1se recomputed here equal the original nested script rerun on this
platform, cell by cell (Amendment 1). CAT-KMIN: each inner model, in its own blocks, calibrated on its own held-out cells; CAT-SPLIT: half of the
training cells (seed 500 + split index), kappa by the rule from that half.
Usage: python contrib/cat_battery.py      Outputs: out/contrib/Battery_cost.csv, Battery_settings.csv, Battery_check.txt
"""
import os, sys, time, pickle
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np, pandas as pd
import eol_window2 as W
import rev_experiments as R
import audit_confirmations as AC
import audit_cost as CO
import battery_warning as BW
import audit_battery_cost_nested as BN
import cat as C

OUT = 'out/contrib'; os.makedirs(OUT + '/ckpt', exist_ok=True)
H_CAT = 60.0; TAUS = BN.TAUS_C; SETS = [(c, sp, k) for c in BN.CAPS_C for sp in W.SPANS for k in W.KS]


def fit_caps(S, Lc, kap, tr, tg):
    """As audit_battery_cost_nested.fit_models, regressors only (identical X, y and model)."""
    B = AC.battery_blocks(S, kap, Lc, tr); F, Y = BW.features(B[B.cell.isin(np.concatenate([tr, tg]))], tr)
    X = np.vstack([F[u] for u in tr]); y = np.concatenate([Y[u] for u in tr]); out = {}
    for c in BN.CAPS_C:
        m = W.gbm(X, y, c / kap); out[c] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in tg}
    return out


def tab_c(P, kap, sp, k, thr_c, shift_c=0.0):
    return BN.to_cycles(R.alarm_table({u: (W.smooth(p, sp) + shift_c / kap, y) for u, (p, y) in P.items()}, k, np.asarray(thr_c) / kap), kap)


def col(tab, j):
    U, ok, ya, ta, L = tab; return U, ok[:, j], ya[:, j], ta[:, j], L


def run_split(S, Lc, an, name, tr, te, seed):
    t0 = time.time(); idx = int(name[-1])
    inner = np.array_split(np.random.default_rng(seed).permutation(tr), 5)
    assert not set(tr) & set(te) and sorted(np.concatenate(inner).tolist()) == sorted(tr.tolist()), 'E1'
    folds, kmt = [], []
    for iu in inner:
        itr = np.setdiff1d(tr, iu); kap = AC.kap_rule(Lc[itr].values); P = fit_caps(S, Lc, kap, itr, np.concatenate([iu, te]))
        folds.append(dict(units=iu, kap=kap, pred={c: {u: P[c][u] for u in iu} for c in BN.CAPS_C}))
        kmt.append(dict(kap=kap, pred={c: {u: P[c][u] for u in te} for c in BN.CAPS_C}))
    kap_o = AC.kap_rule(Lc[tr].values); fin = fit_caps(S, Lc, kap_o, tr, te)
    order = [u for f in folds for u in f['units']]; wts = CO.boot_weights(len(order), 2026 + idx)
    oof_tab = lambda c, sp, k, thr, s=0.0: BN.cat([tab_c(f['pred'][c], f['kap'], sp, k, thr, s) for f in folds])
    te_tab = lambda c, sp, k, thr, s=0.0: tab_c(fin[c], kap_o, sp, k, thr, s)
    stw_sel = {}
    for Hc in BN.HS_C:
        best = None
        for c in BN.CAPS_C:
            if c < Hc + 60: continue
            for sp in W.SPANS:
                for k in W.KS:
                    tot = sum(BN.counts(f['pred'][c], f['kap'], sp, k, Hc) for f in folds) - 0.001 * np.abs(BN.SHIFTS_C) / 3
                    j = int(np.argmax(tot))
                    if best is None or tot[j] > best[0]: best = (float(tot[j]), c, sp, k, float(BN.SHIFTS_C[j]))
        stw_sel[Hc] = best[1:]
    WIN = {Hc: (oof_tab(c, sp, k, [Hc], s), te_tab(c, sp, k, [Hc], s)) for Hc, (c, sp, k, s) in stw_sel.items()}
    STW = {key: (oof_tab(*key, TAUS), te_tab(*key, TAUS)) for key in SETS}
    for key in STW: assert list(STW[key][0][0]) == order
    c0, sp0, k0, _ = stw_sel[H_CAT]; g0 = (c0, sp0, k0); tab_o, tab_t = STW[g0]
    kmin_cal = [tab_c(f['pred'][c0], f['kap'], sp0, k0, TAUS) for f in folds]
    kmin_test = [tab_c(m['pred'][c0], m['kap'], sp0, k0, TAUS) for m in kmt]
    perm = np.random.default_rng(500 + idx + (10 if an == 'lobo' else 0)).permutation(tr)
    A_u, B_u = np.sort(perm[:len(perm) // 2]), np.sort(perm[len(perm) // 2:]); kap_a = AC.kap_rule(Lc[A_u].values)
    SPp = fit_caps(S, Lc, kap_a, A_u, np.concatenate([B_u, te]))[c0]
    split_cal = tab_c({u: SPp[u] for u in B_u}, kap_a, sp0, k0, TAUS); split_test = tab_c({u: SPp[u] for u in te}, kap_a, sp0, k0, TAUS)
    resid = np.concatenate([(W.smooth(p, sp0) - y) * f['kap'] for f in folds for p, y in f['pred'][c0].values()])
    for t_ in kmin_test + [split_test]: assert list(t_[0]) == list(tab_t[0]), 'unit order'
    rows, sets = [], []

    def emit(pname, tab1, lead, rho, extra):
        U, ok, ya, ta, L = tab1; c, use, pl = R.cost_of(ok, ya, ta, L, lead, rho)
        for i, u in enumerate(U):
            rows.append(dict(analysis=an, split=name, kappa=kap_o, lead_cycles=lead, rho=rho, policy=pname, unit=u, cost=c[i], use=use[i],
                             fail=not pl[i], rul_at_alarm=ya[i] if ok[i] else np.nan, **extra))

    for lead in BN.LEADS_C:
        S_all = {key: C.scores_from_table(STW[key][0], TAUS, lead) for key in SETS}; S_cf = S_all[g0]
        S_sp = C.scores_from_table(split_cal, TAUS, lead)
        for alpha in C.ALPHAS:
            th, cert = C.tau_hat(S_cf, alpha); j0 = C.certified_column(TAUS, th, cert)
            ths, certs = C.tau_hat(S_sp, alpha); js = C.certified_column(TAUS, ths, certs)
            km = [C.tau_hat(C.scores_from_table(kc, TAUS, lead), alpha) for kc in kmin_cal]
            jk = [C.certified_column(TAUS, t, c_) for t, c_ in km]; certk = all(c_ for _, c_ in km)
            kmin_tab = _earliest([col(kt, j) for kt, j in zip(kmin_test, jk)])
            q_pt = C.conformal_quantile(resid, alpha); pt_tab = col(te_tab(c0, sp0, k0, [lead + q_pt]), 0)
            thb, certb = C.tau_hat(S_cf, alpha / len(SETS))
            sets.append(dict(analysis=an, split=name, lead_cycles=lead, alpha=alpha, setting=str(g0), kappa=kap_o, n_cf=len(S_cf), tau_cf=th, cert_cf=cert,
                             n_split=len(S_sp), tau_split=ths, cert_split=certs, kappa_split=kap_a, tau_kmin='/'.join(f'{t:g}' for t, _ in km), cert_kmin=certk,
                             q_pt=q_pt, tau_pt=lead + q_pt, tau_bonf=thb, cert_bonf=certb, n_inf_cf=int(np.isinf(S_cf).sum())))
            ex = dict(alpha=alpha)
            for rho in CO.RHOS:
                emit(f'CAT_a{alpha}', col(tab_t, j0), lead, rho, dict(ex, tau=TAUS[j0], certifiable=cert))
                emit(f'CATsplit_a{alpha}', col(split_test, js), lead, rho, dict(ex, tau=TAUS[js], certifiable=certs))
                emit(f'CATkmin_a{alpha}', kmin_tab, lead, rho, dict(ex, tau=np.nan, certifiable=certk))
                emit(f'PT_a{alpha}', pt_tab, lead, rho, dict(ex, tau=lead + q_pt, certifiable=True))
                j1 = C.cost_aware_column(tab_o, TAUS, j0, lead, rho, C.cost_1cycle)
                emit(f'CATc_a{alpha}', col(tab_t, j1), lead, rho, dict(ex, tau=TAUS[j1], certifiable=cert))
                if alpha == C.ALPHA_PRIMARY:
                    jb = C.certified_column(TAUS, thb, certb); jb1 = C.cost_aware_column(tab_o, TAUS, jb, lead, rho, C.cost_1cycle)
                    emit('CATc_bonf_a0.05', col(tab_t, jb1), lead, rho, dict(ex, tau=TAUS[jb1], certifiable=certb))
                    kp, _ = CO.select(STW, lead, rho, 'plain', wts); thp, certp = C.tau_hat(S_all[kp], alpha)
                    jp = C.certified_column(TAUS, thp, certp); jp1 = C.cost_aware_column(STW[kp][0], TAUS, jp, lead, rho, C.cost_1cycle)
                    emit('CATc_plainset_a0.05', col(STW[kp][1], jp1), lead, rho, dict(ex, tau=TAUS[jp1], certifiable=certp, setting=str(kp)))
        for rho in CO.RHOS:
            Hs = min(BN.HS_C, key=lambda Hc: (lambda c_, u_, _: c_.sum() / u_.sum())(*R.cost_of(*WIN[Hc][0][1:], lead, rho)))
            emit('rep_STW_window', col(WIN[Hs][1], 0), lead, rho, dict(setting=f'{Hs}|0'))
            for pname, rule in (('rep_STW_cost', 'plain'), ('rep_STW_cost_1se', '1se')):
                key, j = CO.select(STW, lead, rho, rule, wts); emit(pname, col(STW[key][1], j), lead, rho, dict(setting=f'{key}|{j}', tau=TAUS[j]))
    print(f'{name} done ({time.time() - t0:.0f}s; outer kappa {kap_o}, inner {[f["kap"] for f in folds]}, setting {g0})', flush=True)
    return rows, sets


def _earliest(cols):
    U = cols[0][0]; L = cols[0][4]
    ta = np.stack([np.where(t[1], t[3], np.inf) for t in cols], 1); ya = np.stack([np.where(t[1], t[2], -np.inf) for t in cols], 1)
    j = np.argmin(ta, axis=1); ok = np.isfinite(ta[np.arange(len(U)), j])
    return U, ok, np.where(ok, ya[np.arange(len(U)), j], np.nan), np.where(ok, ta[np.arange(len(U)), j], np.nan), L


def main():
    t0 = time.time(); S, Lc = AC.battery_cycles(); cells = np.sort(Lc.index.values); rows, sets, baselines = [], [], []
    for an, name, tr, te, seed in [x for x in AC.battery_splits(cells) if x[0] in ('cv123', 'lobo')]:
        ck = f'{OUT}/ckpt/Battery_{name}.pkl'
        if os.path.exists(ck): r, s = pickle.load(open(ck, 'rb')); print(f'{name} from checkpoint', flush=True)
        else:
            r, s = run_split(S, Lc, an, name, tr, te, seed); pickle.dump((r, s), open(ck + '.tmp', 'wb')); os.replace(ck + '.tmp', ck)
        rows += r; sets += s
        bc = f'{OUT}/ckpt/Battery_baseline_{name}.pkl'
        if os.path.exists(bc): br, _ = pickle.load(open(bc, 'rb'))
        else:
            br, check = BN.run_split(S, Lc, an, name, tr, te, seed)
            pickle.dump((br, check), open(bc + '.tmp', 'wb')); os.replace(bc + '.tmp', bc)
        baselines += br
    D = pd.concat([pd.DataFrame(rows), pd.DataFrame(baselines)], ignore_index=True)
    D.to_csv(f'{OUT}/Battery_cost.csv', index=False); pd.DataFrame(sets).to_csv(f'{OUT}/Battery_settings.csv', index=False)
    Fz = pd.DataFrame(baselines); lines = []
    for pol in ('STW_window', 'STW_cost', 'STW_cost_1se'):
        a = D[D.policy == f'rep_{pol}'].sort_values(['split', 'lead_cycles', 'rho', 'unit']); b = Fz[Fz.policy == pol].sort_values(['split', 'lead_cycles', 'rho', 'unit'])
        same = len(a) == len(b) and np.array_equal(a.unit.values, b.unit.values) and np.allclose(a.cost.values, b.cost.values) and np.allclose(a.use.values, b.use.values)
        lines.append((f'R1 battery {pol}: every test decision identical to the original nested script rerun on this platform ({len(a)} rows)', bool(same)))
    txt = '\n'.join(f'{"PASS" if ok else "FAIL"}  {s}' for s, ok in lines); open(f'{OUT}/Battery_check.txt', 'w', newline='\n').write(txt + '\n'); print(txt)
    print(f'Battery finished in {time.time() - t0:.0f}s')
    if not all(ok for _, ok in lines): raise SystemExit('STOP: existing battery results not reproduced on the CAT code path')


if __name__ == '__main__':
    main()
