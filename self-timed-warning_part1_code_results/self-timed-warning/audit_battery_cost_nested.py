"""Battery maintenance cost with FULLY NESTED preprocessing and the task in cycles (convention C; post hoc, exploratory).
Plan fixed and hashed before the run: kam/PHASE3_4_PLAN.md, section 4a.

Same renewal-reward model, lead times (0, 15, 30, 45 cycles), cost ratios (5, 10, 20, 50), splits (cv1-cv5 by cell,
seed 2026; lobo1-lobo3), inner folds and bootstrap rule as audit_battery_cost2.py (convention B), with two differences:
  1. every inner training subset builds its own blocks, z-score statistics and models with kappa by the protocol rule
     computed from that subset (inner validation cells are predicted in their own blocks); the final models use kappa by
     the rule from the outer training set (as audit_battery_physical.py, 'rule_nested');
  2. the task is in cycles (the engine task scaled by three): H in {30, 45, 60, 90, 120} cycles, window [-39, +6] cycles,
     caps {120, 180, 270} cycles (cap >= H + 60), shifts -36 ... +24 cycles (step 1.5), cost thresholds 3, 6, ..., 180 cycles;
     span and debounce in blocks. A model in blocks of kappa uses every cycle quantity divided by kappa.
Alarm tables are converted to cycles (remaining life at the alarm, alarm cycle and life times the kappa of the model that
produced them) and concatenated over the inner folds, so training cost rates of folds with different kappa are summed in
cycles. Capacity policies fit nothing; their settings are chosen on the training cells in blocks of the outer kappa.
Check R4a: the window-tuned recipe at H = 60 cycles reproduces the per-cell first warnings of audit_battery_physical.py
('rule_nested'); written to out/audit/cost_battery_nested_check.txt.
Output: out/audit/cost_battery_nested.csv (one row per split, lead time, cost ratio, policy and test cell)
Usage: python audit_battery_cost_nested.py
"""
import os, pickle, time
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
import eol_window2 as W
import rev_experiments as R
import audit_confirmations as AC
import audit_cost as CO
import battery_warning as BW

OUT = 'out/audit'; os.makedirs(OUT + '/ckpt', exist_ok=True)
HS_C = [30.0, 45.0, 60.0, 90.0, 120.0]; LO_C, HI_C = -39.0, 6.0
CAPS_C = [120.0, 180.0, 270.0]; SHIFTS_C = np.arange(-36, 24.01, 1.5); TAUS_C = 3.0 * R.TAUS
LEADS_C = [0, 15, 30, 45]; TREND_W = (10, 20, 40)           # x 3 = 30, 60, 120 cycles, as audit_battery_physical.trend_select


def fit_models(S, Lc, kap, tr, tg):
    """blocks, statistics and models from the training cells tr only (as audit_battery_physical.fit_predict, plus the
    health indicator and the 10 % quantile model of audit_cost.models_ext); series in blocks of kap for the target cells"""
    B = AC.battery_blocks(S, kap, Lc, tr); F, Y = BW.features(B[B.cell.isin(np.concatenate([tr, tg]))], tr)
    X = np.vstack([F[u] for u in tr]); y = np.concatenate([Y[u] for u in tr]); out = {}
    for c in CAPS_C:
        m = W.gbm(X, y, c / kap); out[c] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in tg}
    p = (X.shape[1] - 1) // 5
    rows = [(F[u][:, :p], Y[u]) for u in tr]
    Xh = np.vstack([np.vstack([f[:30], f[r <= 5]]) for f, r in rows])
    yh = np.concatenate([np.concatenate([np.zeros(min(30, len(f))), np.ones((r <= 5).sum())]) for f, r in rows])
    A = np.column_stack([Xh, np.ones(len(Xh))]); w = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ yh)
    out['HI'] = {u: (F[u][:-1, :p] @ w[:-1] + w[-1], Y[u][:-1]) for u in tg}
    mq = HistGradientBoostingRegressor(loss='quantile', quantile=0.1, max_iter=500, learning_rate=0.05, max_leaf_nodes=31,
                                       min_samples_leaf=40, random_state=0).fit(X, np.minimum(y, max(CAPS_C) / kap))
    out['Q10'] = {u: (mq.predict(F[u])[:-1], Y[u][:-1]) for u in tg}
    return out


def to_cycles(tab, kap):
    U, ok, ya, ta, L = tab; return list(U), ok, ya * kap, ta * kap, L * kap


def cat(tabs):
    U = sum((list(t[0]) for t in tabs), []); return (U,) + tuple(np.concatenate([t[i] for t in tabs]) for i in range(1, 5))


def counts(P, kap, sp, k, Hc):
    Po = {u: (W.smooth(p, sp), y) for u, (p, y) in P.items()}
    return AC.in_counts_g(Po, Hc / kap, k, LO_C / kap, HI_C / kap, SHIFTS_C / kap)


def run_split(S, Lc, an, name, tr, te, seed):
    t0 = time.time(); idx = int(name[-1])
    inner = np.array_split(np.random.default_rng(seed).permutation(tr), 5)
    assert not set(tr) & set(te) and sorted(np.concatenate(inner).tolist()) == sorted(tr.tolist()), 'E1'
    folds = []
    for iu in inner:
        itr = np.setdiff1d(tr, iu); kap = AC.kap_rule(Lc[itr].values)
        folds.append(dict(units=iu, kap=kap, pred=fit_models(S, Lc, kap, itr, iu)))
    kap_o = AC.kap_rule(Lc[tr].values); fin = fit_models(S, Lc, kap_o, tr, te)
    order = [u for f in folds for u in f['units']]                       # training units in the order of the OOF tables
    wts = CO.boot_weights(len(order), 2026 + idx)

    def oof_tab(src, sp, k, thr_c, sign=1.0, shift_c=0.0):
        return cat([to_cycles(R.alarm_table({u: (sign * W.smooth(p, sp) + shift_c / f['kap'], y) for u, (p, y) in f['pred'][src].items()}, k,
                                            thr_c / f['kap'] if sign > 0 else thr_c), f['kap']) for f in folds])

    def te_tab(src, sp, k, thr_c, sign=1.0, shift_c=0.0):
        return to_cycles(R.alarm_table({u: (sign * W.smooth(p, sp) + shift_c / kap_o, y) for u, (p, y) in fin[src].items()}, k,
                                       thr_c / kap_o if sign > 0 else thr_c), kap_o)

    # ---- window-tuned recipe: per H, cap/span/debounce/shift by the summed inner window count (as audit_battery_physical.select)
    stw_sel = {}
    for Hc in HS_C:
        best = None
        for c in CAPS_C:
            if c < Hc + 60: continue
            for sp in W.SPANS:
                for k in W.KS:
                    tot = sum(counts(f['pred'][c], f['kap'], sp, k, Hc) for f in folds) - 0.001 * np.abs(SHIFTS_C) / 3
                    j = int(np.argmax(tot))
                    if best is None or tot[j] > best[0]: best = (float(tot[j]), c, sp, k, float(SHIFTS_C[j]))
        stw_sel[Hc] = best[1:]
    WIN = {Hc: (oof_tab(c, sp, k, np.array([Hc]), shift_c=s), te_tab(c, sp, k, np.array([Hc]), shift_c=s)) for Hc, (c, sp, k, s) in stw_sel.items()}
    c, sp, k, s = stw_sel[60.0]                                                        # check R4a material
    chk = AC.evaluate_g({u: (W.smooth(p, sp), y) for u, (p, y) in fin[c].items()}, 60.0 / kap_o, k, s / kap_o, LO_C / kap_o, HI_C / kap_o)
    chk = chk.assign(split=name, analysis=an, kappa=kap_o, cap_cycles=c, span=sp, k_db=k, shift_cycles=s)
    # ---- cost-tuned recipe, quantile alarm, health indicator (thresholds in cycles; HI on its own scale)
    STW = {(c, sp, k): (oof_tab(c, sp, k, TAUS_C), te_tab(c, sp, k, TAUS_C)) for c in CAPS_C for sp in W.SPANS for k in W.KS}
    Q10 = {('q', sp, k): (oof_tab('Q10', sp, k, TAUS_C), te_tab('Q10', sp, k, TAUS_C)) for sp in W.SPANS for k in W.KS}
    hv = np.concatenate([s_[y * f['kap'] <= 240] for f in folds for s_, y in f['pred']['HI'].values()])
    THETA = np.unique(np.quantile(hv, np.linspace(0.02, 0.995, 120)))
    HI = {('h', sp, k): (oof_tab('HI', sp, k, -THETA, sign=-1.0), te_tab('HI', sp, k, -THETA, sign=-1.0)) for sp in W.SPANS for k in W.KS}
    # ---- capacity policies on blocks of the outer kappa (nothing fitted; settings on the training cells)
    Bo = AC.battery_blocks(S, kap_o, Lc, tr)
    qtr = {u: (g.QDischarge.values[:-1], g.rul.values[:-1]) for u, g in Bo[Bo.cell.isin(tr)].groupby('cell')}
    qtr = {u: qtr[u] for u in order}
    qte = {u: (g.QDischarge.values[:-1], g.rul.values[:-1]) for u, g in Bo[Bo.cell.isin(te)].groupby('cell')}
    qv = np.concatenate([q[y * kap_o <= 240] for q, y in qtr.values()]); QT = np.unique(np.quantile(qv, np.linspace(0.02, 0.995, 120)))
    capt = lambda P, sp, k, thr: to_cycles(R.alarm_table({u: (W.smooth(q, sp), y) for u, (q, y) in P.items()}, k, thr), kap_o)
    CAPT = {('c', sp, k): (capt(qtr, sp, k, QT), capt(qte, sp, k, QT)) for sp in W.SPANS for k in W.KS}
    TRS = {w: {u: (AC.trend_rul(q, max(5, int(round(w * 3 / kap_o))), 1), y) for u, (q, y) in qtr.items()} for w in TREND_W}
    TES = {w: {u: (AC.trend_rul(q, max(5, int(round(w * 3 / kap_o))), 1), y) for u, (q, y) in qte.items()} for w in TREND_W}
    tsel = {}
    for Hc in HS_C:
        best = None
        for w in TREND_W:
            for sp in W.SPANS:
                for k in W.KS:
                    tot = counts(TRS[w], kap_o, sp, k, Hc) - 0.001 * np.abs(SHIFTS_C) / 3; j = int(np.argmax(tot))
                    if best is None or tot[j] > best[0]: best = (float(tot[j]), w, sp, k, float(SHIFTS_C[j]))
        tsel[Hc] = best[1:]
    trw = lambda P, sp, k, Hc, s: to_cycles(R.alarm_table({u: (W.smooth(p, sp) + s / kap_o, y) for u, (p, y) in P.items()}, k, np.array([Hc / kap_o])), kap_o)
    TWIN = {Hc: (trw(TRS[w], sp, k, Hc, s), trw(TES[w], sp, k, Hc, s)) for Hc, (w, sp, k, s) in tsel.items()}
    w, sp, k, s = tsel[60.0]
    tchk = AC.evaluate_g({u: (W.smooth(p, sp), y) for u, (p, y) in TES[w].items()}, 60.0 / kap_o, k, s / kap_o, LO_C / kap_o, HI_C / kap_o)
    chk = pd.concat([chk.assign(method='recipe'), tchk.assign(split=name, analysis=an, kappa=kap_o, method='capacity_trend', span=sp, k_db=k, shift_cycles=s)])
    trc = lambda P, sp, k: to_cycles(R.alarm_table({u: (W.smooth(p, sp), y) for u, (p, y) in P.items()}, k, TAUS_C / kap_o), kap_o)
    TRC = {(w, sp, k): (trc(TRS[w], sp, k), trc(TES[w], sp, k)) for w in TREND_W for sp in W.SPANS for k in W.KS}
    for tabs in (STW, Q10, HI, CAPT, TRC):                                           # every training table in the same unit order
        for key in tabs: assert list(tabs[key][0][0]) == order, 'unit order'
    for Hc in HS_C: assert list(WIN[Hc][0][0]) == order and list(TWIN[Hc][0][0]) == order

    rows = []; Ltr = Lc[tr].values.astype(float); Ts = np.arange(1, int(Ltr.max()) + 1)
    for lc in LEADS_C:
        for rho in CO.RHOS:
            hcost = lambda TAB: (min(HS_C, key=lambda Hc: (lambda c_, u_, _: c_.sum() / u_.sum())(*R.cost_of(*TAB[Hc][0][1:], lc, rho))), 0)
            pols = {'STW_window': (WIN, lambda: hcost(WIN)),
                    'STW_cost': (STW, lambda: CO.select(STW, lc, rho, 'plain', wts)),
                    'STW_cost_1se': (STW, lambda: CO.select(STW, lc, rho, '1se', wts)),
                    'STW_cost_q80': (STW, lambda: CO.select(STW, lc, rho, 'q80', wts)),
                    'Q10_cost': (Q10, lambda: CO.select(Q10, lc, rho, 'plain', wts)),
                    'Q10_cost_1se': (Q10, lambda: CO.select(Q10, lc, rho, '1se', wts)),
                    'HI_cost': (HI, lambda: CO.select(HI, lc, rho, 'plain', wts)),
                    'capacity_cost': (CAPT, lambda: CO.select(CAPT, lc, rho, 'plain', wts)),
                    'capacity_cost_1se': (CAPT, lambda: CO.select(CAPT, lc, rho, '1se', wts)),
                    'trend_window': (TWIN, lambda: hcost(TWIN)),
                    'trend_cost': (TRC, lambda: CO.select(TRC, lc, rho, 'plain', wts)),
                    'trend_cost_1se': (TRC, lambda: CO.select(TRC, lc, rho, '1se', wts))}
            for pname, (tab, chooser) in pols.items():
                key, j = chooser(); U, c_, use, pl, yat = CO.apply(tab[key][1], j, lc, rho)
                for ui, u in enumerate(U):
                    rows.append(dict(analysis=an, split=name, kappa=kap_o, inner_kappas='/'.join(str(f['kap']) for f in folds), lead_cycles=lc, rho=rho,
                                     policy=pname, unit=u, cost=c_[ui], use=use[ui], fail=not pl[ui], rul_at_alarm=yat[ui], setting=f'{key}|{j}'))
            cr = np.array([np.where(Ltr > T, 1.0, rho).sum() / np.minimum(Ltr, T).sum() for T in Ts]); T = Ts[int(np.argmin(cr))]
            for u in te:
                Lu = float(Lc[u])
                rows.append(dict(analysis=an, split=name, kappa=kap_o, lead_cycles=lc, rho=rho, policy='age', unit=u, cost=1.0 if Lu > T else rho, use=min(Lu, T), fail=Lu <= T, rul_at_alarm=np.nan, setting=str(T)))
                rows.append(dict(analysis=an, split=name, kappa=kap_o, lead_cycles=lc, rho=rho, policy='perfect_foresight', unit=u, cost=1.0, use=Lu - 1, fail=False, rul_at_alarm=1.0, setting=''))
                rows.append(dict(analysis=an, split=name, kappa=kap_o, lead_cycles=lc, rho=rho, policy='run_to_failure', unit=u, cost=rho, use=Lu, fail=True, rul_at_alarm=0.0, setting=''))
    print(f'{name} done ({time.time() - t0:.0f}s; outer kappa {kap_o}, inner {[f["kap"] for f in folds]})', flush=True)
    return rows, chk


if __name__ == '__main__':
    S, Lc = AC.battery_cycles(); cells = np.sort(Lc.index.values); allr, allc = [], []
    for an, name, tr, te, seed in [x for x in AC.battery_splits(cells) if x[0] in ('cv123', 'lobo')]:
        ck = f'{OUT}/ckpt/cost_battery_nested_{name}.pkl'
        if os.path.exists(ck): r, c = pickle.load(open(ck, 'rb'))
        else:
            r, c = run_split(S, Lc, an, name, tr, te, seed); pickle.dump((r, c), open(ck + '.tmp', 'wb')); os.replace(ck + '.tmp', ck)
        allr += r; allc.append(c)
    pd.DataFrame(allr).to_csv(f'{OUT}/cost_battery_nested.csv', index=False)
    C = pd.concat(allc, ignore_index=True); C.to_csv(f'{OUT}/cost_battery_nested_h60.csv', index=False)
    # check R4a against the fully nested window analysis
    ref = None
    for p in ('out/audit/battery_physical_cv.csv', 'results/audit/battery_physical_cv.csv.gz'):
        if os.path.exists(p): ref = pd.concat([pd.read_csv(p), pd.read_csv(p.replace('_cv', '_lobo'))]); break
    lines = []
    for meth, var in (('recipe', 'rule_nested'), ('capacity_trend', None)):
        mine = C[C.method == meth].set_index(['analysis', 'unit']).cls
        if meth == 'recipe': r_ = ref[(ref.variant == 'rule_nested') & (ref.method == 'recipe')]
        else: r_ = ref[(ref.variant == 'fixed_kappa') & (ref.method == 'capacity_trend')].merge(C[C.method == meth][['split', 'kappa']].drop_duplicates(), on=['split', 'kappa'])
        r_ = r_.set_index(['analysis', 'unit']).cls.reindex(mine.index)
        same = bool((mine == r_).all())
        for an in ('cv123', 'lobo'):
            lines.append(f'{"PASS" if same else "FAIL"}  R4a {meth} H = 60 cycles, {an}: {int((mine.xs(an) == "IN").sum())}/{len(mine.xs(an))} in window; '
                         f'reference {int((r_.xs(an) == "IN").sum())}/{len(r_.xs(an))}; per-cell outcomes identical: {same}')
    open(f'{OUT}/cost_battery_nested_check.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
