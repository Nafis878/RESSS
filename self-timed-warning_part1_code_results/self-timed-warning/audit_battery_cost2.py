"""Battery maintenance cost under cross-validation by cell AND with one batch held out, including the capacity-trend
baseline (post hoc; exploratory).

Same renewal-reward model, lead times (0, 15, 30, 45 cycles), cost ratios, training-only block length kappa, inner folds and
bootstrap rule as audit_cost.py. All policies of audit_cost.py for the battery are recomputed (the cross-validation rows must
reproduce out/audit/cost_Battery.csv exactly) and three capacity-trend policies are added:
  trend_window      capacity-trend remaining-life extrapolation (to 0.88 Ah) with the self-timed trigger; window length w,
                    span, debounce and shift chosen by the window count on the training cells for each H in {10,...,40}
                    blocks, then H chosen by the training cost rate (as the window-tuned recipe)
  trend_cost        alarm when the smoothed extrapolated remaining life stays <= tau for k blocks; w, span, k, tau chosen
                    to minimise the training cost rate
  trend_cost_1se    the same with the one-standard-error rule
The trend has no fitted parameters, so its settings are chosen on the series of the training cells themselves.
Output: out/audit/cost_battery2.csv
"""
import os, pickle, time
import numpy as np, pandas as pd
import eol_window2 as W
import rev_experiments as R
import audit_confirmations as AC
import audit_cost as CO
import battery_warning as BW

OUT = 'out/audit'; os.makedirs(OUT + '/ckpt', exist_ok=True)
S, Lc = AC.battery_cycles(); cells = np.sort(Lc.index.values); leads_c = [0, 15, 30, 45]; rows = []
splits = [x for x in AC.battery_splits(cells) if x[0] in ('cv123', 'lobo')]
for an, name, train_u, test_u, seed in splits:
    ck = f'{OUT}/ckpt/cost_battery2_{name}.pkl'
    if os.path.exists(ck): rows += pickle.load(open(ck, 'rb')); continue
    t0 = time.time(); n0 = len(rows); idx = int(name[-1])
    kap = AC.kap_rule(Lc[train_u].values); Bf = AC.battery_blocks(S, kap, Lc, train_u)
    def feats(stat_u, use_u, Bf=Bf):
        F, Y = BW.features(Bf[Bf.cell.isin(np.concatenate([stat_u, use_u]))], stat_u)
        F['cap'] = {u: g.QDischarge.values for u, g in Bf[Bf.cell.isin(use_u)].groupby('cell')}
        return F, Y
    inner = np.array_split(np.random.default_rng(seed).permutation(train_u), 5); oof = {}
    for iu in inner:
        p = CO.models_ext(feats, np.setdiff1d(train_u, iu), iu)
        for c in p: oof.setdefault(c, {}).update(p[c])
    fin = CO.models_ext(feats, train_u, test_u)
    Loof = np.array([y[0] + 1 for _, y in oof[W.CAPS[0]].values()]); wts = CO.boot_weights(len(oof[W.CAPS[0]]), 2026 + idx)
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
    WIN = {H: (R.alarm_table({u: (W.smooth(p, sp) + s, y) for u, (p, y) in oof[cap].items()}, k, [H]),
               R.alarm_table({u: (W.smooth(p, sp) + s, y) for u, (p, y) in fin[cap].items()}, k, [H])) for H, (cap, sp, k, s) in stw_sel.items()}
    # capacity-trend series (no fitted parameters): training cells from the out-of-fold capacity entries, test cells from fin
    TR = {w: {u: (AC.trend_rul(q, w, 1), y) for u, (q, y) in oof['CAP'].items()} for w in (10, 20, 40)}
    TE = {w: {u: (AC.trend_rul(q, w, 1), y) for u, (q, y) in fin['CAP'].items()} for w in (10, 20, 40)}
    tsel = {}
    for H in R.HS:
        best = None
        for w in (10, 20, 40):
            for sp in W.SPANS:
                Po = {u: (W.smooth(p, sp), y) for u, (p, y) in TR[w].items()}
                for k in W.KS:
                    tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                    if best is None or tot[j] > best[0]: best = (tot[j], w, sp, k, W.SHIFTS[j])
        tsel[H] = best[1:]
    TWIN = {H: (R.alarm_table({u: (W.smooth(p, sp) + s, y) for u, (p, y) in TR[w].items()}, k, [H]),
                R.alarm_table({u: (W.smooth(p, sp) + s, y) for u, (p, y) in TE[w].items()}, k, [H])) for H, (w, sp, k, s) in tsel.items()}
    def ttab(src_tr, src_te, keys, thr, sign=1.0):
        return {key: (R.alarm_table({u: (sign * W.smooth(p, key[-2]), y) for u, (p, y) in src_tr(key).items()}, key[-1], thr),
                      R.alarm_table({u: (sign * W.smooth(p, key[-2]), y) for u, (p, y) in src_te(key).items()}, key[-1], thr)) for key in keys}
    STW = ttab(lambda key: oof[key[0]], lambda key: fin[key[0]], [(c, sp, k) for c in W.CAPS for sp in W.SPANS for k in W.KS], R.TAUS)
    Q10 = ttab(lambda key: oof['Q10'], lambda key: fin['Q10'], [('q', sp, k) for sp in W.SPANS for k in W.KS], R.TAUS)
    hv = np.concatenate([s[y <= 80] for s, y in oof['HI'].values()]); THETA = np.unique(np.quantile(hv, np.linspace(0.02, 0.995, 120)))
    HI = ttab(lambda key: oof['HI'], lambda key: fin['HI'], [('h', sp, k) for sp in W.SPANS for k in W.KS], -THETA, sign=-1.0)
    qv = np.concatenate([s[y <= 80] for s, y in oof['CAP'].values()]); QT = np.unique(np.quantile(qv, np.linspace(0.02, 0.995, 120)))
    CAPT = ttab(lambda key: oof['CAP'], lambda key: fin['CAP'], [('c', sp, k) for sp in W.SPANS for k in W.KS], QT)
    TRC = ttab(lambda key: TR[key[0]], lambda key: TE[key[0]], [(w, sp, k) for w in (10, 20, 40) for sp in W.SPANS for k in W.KS], R.TAUS)
    Ts = np.arange(1, int(Loof.max()) + 1); Lte = {u: y[0] + 1 for u, (_, y) in fin[W.CAPS[0]].items()}
    for lc in leads_c:
        l = lc / kap
        for rho in CO.RHOS:
            hcost = lambda TAB: (min(R.HS, key=lambda H: (lambda c, u, _: c.sum() / u.sum())(*R.cost_of(*TAB[H][0][1:], l, rho))), 0)
            pols = {'STW_window': (WIN, lambda: hcost(WIN)),
                    'STW_cost': (STW, lambda: CO.select(STW, l, rho, 'plain', wts)),
                    'STW_cost_1se': (STW, lambda: CO.select(STW, l, rho, '1se', wts)),
                    'STW_cost_q80': (STW, lambda: CO.select(STW, l, rho, 'q80', wts)),
                    'Q10_cost': (Q10, lambda: CO.select(Q10, l, rho, 'plain', wts)),
                    'Q10_cost_1se': (Q10, lambda: CO.select(Q10, l, rho, '1se', wts)),
                    'HI_cost': (HI, lambda: CO.select(HI, l, rho, 'plain', wts)),
                    'capacity_cost': (CAPT, lambda: CO.select(CAPT, l, rho, 'plain', wts)),
                    'capacity_cost_1se': (CAPT, lambda: CO.select(CAPT, l, rho, '1se', wts)),
                    'trend_window': (TWIN, lambda: hcost(TWIN)),
                    'trend_cost': (TRC, lambda: CO.select(TRC, l, rho, 'plain', wts)),
                    'trend_cost_1se': (TRC, lambda: CO.select(TRC, l, rho, '1se', wts))}
            for pname, (tab, chooser) in pols.items():
                key, j = chooser(); U, c, use, pl, yat = CO.apply(tab[key][1], j, l, rho)
                for ui, u in enumerate(U):
                    rows.append(dict(analysis=an, split=name, kappa=kap, lead_cycles=lc, rho=rho, policy=pname, unit=u, cost=c[ui], use=use[ui] * kap,
                                     fail=not pl[ui], rul_at_alarm=yat[ui] * kap if np.isfinite(yat[ui]) else np.nan, setting=f'{key}|{j}'))
            cr = np.array([np.where(Loof > T, 1.0, rho).sum() / np.minimum(Loof, T).sum() for T in Ts]); T = Ts[int(np.argmin(cr))]
            for u, Lu in Lte.items():
                rows.append(dict(analysis=an, split=name, kappa=kap, lead_cycles=lc, rho=rho, policy='age', unit=u, cost=1.0 if Lu > T else rho, use=min(Lu, T) * kap, fail=Lu <= T, rul_at_alarm=np.nan, setting=str(T)))
                rows.append(dict(analysis=an, split=name, kappa=kap, lead_cycles=lc, rho=rho, policy='perfect_foresight', unit=u, cost=1.0, use=(Lu - 1) * kap, fail=False, rul_at_alarm=kap, setting=''))
                rows.append(dict(analysis=an, split=name, kappa=kap, lead_cycles=lc, rho=rho, policy='run_to_failure', unit=u, cost=rho, use=Lu * kap, fail=True, rul_at_alarm=0, setting=''))
    pickle.dump(rows[n0:], open(ck + '.tmp', 'wb')); os.replace(ck + '.tmp', ck)
    print(f'{name} done ({time.time() - t0:.0f}s, kappa {kap})', flush=True)
pd.DataFrame(rows).to_csv(f'{OUT}/cost_battery2.csv', index=False)
