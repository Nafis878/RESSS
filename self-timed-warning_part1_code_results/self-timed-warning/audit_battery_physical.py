"""Battery analyses with a common PHYSICAL task and fully nested preprocessing (post hoc; exploratory).

Task, in charge-discharge cycles (the protocol task at kappa = 3): warning level H = 60 cycles, acceptance window
[-39, +6] cycles on the error (estimate - true remaining life), caps {120, 180, 270} cycles, shift grid -36 ... +24 cycles
(step 1.5). Smoothing span m and debounce k are counted in blocks. A model working in blocks of kappa cycles uses
H / kappa, [-39 / kappa, +6 / kappa], caps / kappa and shifts / kappa, so every setting has the same meaning in cycles and
every score is the same physical acceptance rule (alarms can only be raised at block ends).

Fully nested: inside each outer training set, every inner training subset builds its own blocks (missing first blocks
filled from that subset), its own z-score statistics and its own regressor; the inner validation units are scored in their
own blocks. Out-of-fold in-window counts of the inner folds are summed per setting (same physical grid). After selection,
blocks, statistics and regressor are rebuilt from the complete outer training set and the outer test units are scored once.

For every outer split (cv1..cv5 by cell, seed 2026; lobo1..lobo3, one batch held out) and every kappa in KS the script
stores the inner out-of-fold predictions and the outer test predictions, then derives:
  fixed_kappa      kappa fixed in advance (2, ..., 6), inner and outer
  rule_nested      kappa = max(1, round(median life / 209.5)) computed from each inner training subset (inner folds) and
                   from the outer training set (final model): no failure life outside a training subset enters its time scale
  cv_selected      kappa chosen among KS by the summed inner out-of-fold count (ties: rule kappa of the outer training set,
                   then smaller kappa)
and, on the same task and blocks, the capacity-trend baseline (extrapolation of block-mean discharge capacity to 0.88 Ah,
same trigger; window length, span, debounce and shift chosen on the training cells).
Output: out/audit/battery_physical.csv (one row per outer split, variant, kappa and test cell)
Usage: python audit_battery_physical.py [cv|lobo|all]
"""
import sys, os, pickle, time
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
import numpy as np, pandas as pd
import eol_window2 as W
import battery_warning as BW
import audit_confirmations as AC

OUT = 'out/audit'; os.makedirs(OUT + '/ckpt', exist_ok=True)
KS_KAPPA = [2, 3, 4, 5, 6]
H_C, LO_C, HI_C = 60.0, -39.0, 6.0
CAPS_C = [120.0, 180.0, 270.0]
SHIFTS_C = np.arange(-36, 24.01, 1.5)


def fit_predict(S, Lc, kap, tr, tg):
    """blocks and statistics from the training cells tr only; predictions (in blocks) for target cells tg, every cap"""
    B = AC.battery_blocks(S, kap, Lc, tr); F, Y = BW.features(B[B.cell.isin(np.concatenate([tr, tg]))], tr)
    X = np.vstack([F[u] for u in tr]); y = np.concatenate([Y[u] for u in tr]); out = {}
    for c in CAPS_C:
        m = W.gbm(X, y, c / kap); out[c] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in tg}
    q = {u: (g.QDischarge.values[:-1], g.rul.values[:-1]) for u, g in B[B.cell.isin(tg)].groupby('cell')}
    return out, q


def split_store(S, Lc, name, tr, te, seed):
    def run():
        inner = np.array_split(np.random.default_rng(seed).permutation(tr), 5); res = {}
        for kap in KS_KAPPA:
            folds = []
            for iu in inner:
                itr = np.setdiff1d(tr, iu); p, q = fit_predict(S, Lc, kap, itr, iu)
                folds.append(dict(units=iu, kappa_rule=AC.kap_rule(Lc[itr].values), pred=p, cap_series=q))
            fin, qte = fit_predict(S, Lc, kap, tr, te)
            Btr = AC.battery_blocks(S, kap, Lc, tr)
            qtr = {u: (g.QDischarge.values[:-1], g.rul.values[:-1]) for u, g in Btr[Btr.cell.isin(tr)].groupby('cell')}
            res[kap] = dict(folds=folds, final=fin, cap_test=qte, cap_train=qtr)
            print(f'  {name} kappa {kap} done', flush=True)
        return res
    return AC.ckpt(f'battery_physical_{name}', run)


def counts(P, kap, sp, k):
    Po = {u: (W.smooth(p, sp), y) for u, (p, y) in P.items()}
    return AC.in_counts_g(Po, H_C / kap, k, LO_C / kap, HI_C / kap, SHIFTS_C / kap)


def select(fold_sets):
    """fold_sets: list of (kappa, {cap: {u: (pred, y)}}); returns (score, cap, span, k, shift_cycles)"""
    best = None
    for c in CAPS_C:
        for sp in W.SPANS:
            for k in W.KS:
                tot = sum(counts(P[c], kap, sp, k) for kap, P in fold_sets) - 0.001 * np.abs(SHIFTS_C) / 3
                j = int(np.argmax(tot))
                if best is None or tot[j] > best[0]: best = (float(tot[j]), c, sp, k, float(SHIFTS_C[j]))
    return best


def score(P, kap, sp, k, s_c, Lc):
    R = AC.evaluate_g({u: (W.smooth(p, sp), y) for u, (p, y) in P.items()}, H_C / kap, k, s_c / kap, LO_C / kap, HI_C / kap)
    R['kappa'] = kap; R['r_cycles'] = R.y * kap; R['pred_cycles'] = R.pred * kap; R['life_cycles'] = R.unit.map(Lc); return R


def trend_select(qtr, kap):
    best = None
    for w in (10, 20, 40):
        Ptr = {u: (AC.trend_rul(q, max(5, int(round(w * 3 / kap))), 1), y) for u, (q, y) in qtr.items()}     # window of 30, 60, 120 cycles
        for sp in W.SPANS:
            for k in W.KS:
                tot = counts(Ptr, kap, sp, k) - 0.001 * np.abs(SHIFTS_C) / 3; j = int(np.argmax(tot))
                if best is None or tot[j] > best[0]: best = (float(tot[j]), w, sp, k, float(SHIFTS_C[j]))
    return best


def analyse(S, Lc, splits):
    rows = []
    for an, name, tr, te, seed in splits:
        t0 = time.time(); D = split_store(S, Lc, name, tr, te, seed); rule_outer = AC.kap_rule(Lc[tr].values)
        sel = {kap: select([(kap, f['pred']) for f in D[kap]['folds']]) for kap in KS_KAPPA}
        for kap in KS_KAPPA:                                                               # fixed kappa
            sc, c, sp, k, s = sel[kap]
            rows.append(score(D[kap]['final'][c], kap, sp, k, s, Lc).assign(analysis=an, split=name, variant='fixed_kappa', method='recipe', cap_cycles=c, span=sp, k_db=k, shift_cycles=s, inner_score=sc))
            tsc, w, tsp, tk, ts = trend_select(D[kap]['cap_train'], kap)
            Pte = {u: (AC.trend_rul(q, max(5, int(round(w * 3 / kap))), 1), y) for u, (q, y) in D[kap]['cap_test'].items()}
            rows.append(score(Pte, kap, tsp, tk, ts, Lc).assign(analysis=an, split=name, variant='fixed_kappa', method='capacity_trend', cap_cycles=np.nan, span=tsp, k_db=tk, shift_cycles=ts, inner_score=tsc))
        # rule-nested: each inner fold at its own rule kappa, final model at the outer rule kappa
        fs = [(f['kappa_rule'], D[f['kappa_rule']]['folds'][i]['pred']) for i, f in enumerate(D[KS_KAPPA[0]]['folds'])]
        sc, c, sp, k, s = select(fs)
        rows.append(score(D[rule_outer]['final'][c], rule_outer, sp, k, s, Lc).assign(analysis=an, split=name, variant='rule_nested', method='recipe', cap_cycles=c, span=sp, k_db=k, shift_cycles=s, inner_score=sc,
                                                                                    inner_kappas='/'.join(str(x[0]) for x in fs)))
        # kappa selected by inner cross-validation
        ks = max(KS_KAPPA, key=lambda kk: (round(sel[kk][0], 6), kk == rule_outer, -kk)); sc, c, sp, k, s = sel[ks]
        rows.append(score(D[ks]['final'][c], ks, sp, k, s, Lc).assign(analysis=an, split=name, variant='cv_selected', method='recipe', cap_cycles=c, span=sp, k_db=k, shift_cycles=s, inner_score=sc))
        print(f'{name}: rule kappa {rule_outer}, inner rule kappas {[x[0] for x in fs]}, cv-selected kappa {ks} ({time.time() - t0:.0f}s)', flush=True)
    return rows


if __name__ == '__main__':
    mode = ARGS[0] if ARGS else 'all'
    S, Lc = AC.battery_cycles(); cells = np.sort(Lc.index.values)
    splits = [x for x in AC.battery_splits(cells) if (x[0] == 'cv123' and mode in ('cv', 'all')) or (x[0] == 'lobo' and mode in ('lobo', 'all'))]
    rows = analyse(S, Lc, splits)
    A = pd.concat(rows, ignore_index=True)
    out = f'{OUT}/battery_physical.csv' if mode == 'all' else f'{OUT}/battery_physical_{mode}.csv'
    A.to_csv(out, index=False); print('written', out)
