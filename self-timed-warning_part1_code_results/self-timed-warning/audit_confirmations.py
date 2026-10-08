"""Audit reruns of the battery and bearing confirmations (post hoc corrections; not part of the hashed protocols).

Correction 1 (time scale): the protocols set the block length kappa = max(1, round(median life / 209.5)) from the lives of ALL
included units, so held-out lives entered the time scale (and, through it, the warning level H = 20 blocks and the window
[-13, +2] blocks). Here kappa is computed from the lives of the TRAINING units of each outer split only; inner folds use the
kappa of their outer split (inner validation units belong to the outer training set). The test units never influence it.
Correction 2 (battery filling): invalid per-cycle values are forward-filled only; a block mean uses the valid cycles of the
block (leading invalid values at cycle 1 are no longer back-filled from cycle 2). With kappa = 1 a block can be empty; it is
then filled with the median of the training units' first-block values.
Everything else (model, grids, rules, seeds, splits) is unchanged from battery_warning.py / bearing_warning.py.

Modes (outputs in out/audit/, one checkpoint per split):
  battery_corrected      all three pre-specified methods, analyses cv123, lobo, cv119, training-only kappa
  battery_sens K [K..]   self-timed model only, cv123, PHYSICAL task fixed: H = 60 cycles, window [-39, +6] cycles,
                         caps {120, 180, 270} cycles, shift grid [-36, +24] cycles; only the aggregation kappa varies
  battery_baselines      capacity-threshold alarm and capacity-trend extrapolation (to 0.88 Ah = 80 % of nominal),
                         window evaluation, cv123 and lobo, training-only kappa
  bearing_corrected      all methods incl. STW-T, cv and official split, training-only kappa
  bearing_sens K [K..]   self-timed model only, cv, physical task fixed: H = 140 snapshots, window [-91, +14] snapshots
"""
import sys, os, json, pickle, time
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
import numpy as np, pandas as pd
import eol_window2 as W
import battery_warning as BW
import bearing_warning as GW
from safe_common import outer_folds
from feats import causal_feats

OUT = 'out/audit'; os.makedirs(OUT + '/ckpt', exist_ok=True)
kap_rule = lambda lives: max(1, int(round(float(np.median(lives)) / 209.5)))


def ckpt(name, fn):
    p = f'{OUT}/ckpt/{name}.pkl'
    if os.path.exists(p):
        return pickle.load(open(p, 'rb'))
    r = fn(); pickle.dump(r, open(p + '.tmp', 'wb')); os.replace(p + '.tmp', p); return r


# ------------------------------------------------------------------ battery data
def battery_cycles():
    S = pd.read_csv('battery/severson_cycle_summary.csv.gz'); M = pd.read_csv('battery/severson_cells.csv').set_index('cell')
    keep = [c for c in S.cell.unique() if np.isfinite(M.cycle_life_official[c]) and c not in BW.SPLIT_CELLS and c not in BW.NO_EOL]
    S = S[S.cell.isin(keep)].sort_values(['cell', 'cycle']).copy()
    S['L'] = S.cell.map(M.cycle_life_official).astype(int); S = S[S.cycle <= S.L]
    for f, (lo, hi, inc) in BW.RANGES.items():
        v = S[f].astype(float); ok = np.isfinite(v) & (v <= hi) & ((v >= lo) if inc else (v > lo))
        S[f] = v.where(ok); S[f] = S.groupby('cell')[f].transform(lambda s: s.ffill())          # forward only
    return S, S.groupby('cell').L.first()


def battery_blocks(S, kappa, Lc, train_u):
    S = S.copy(); S['block'] = (S.cycle - 1) // kappa + 1; S = S[S.block <= S.L // kappa]
    B = S.groupby(['cell', 'block'])[BW.FEAT].mean().reset_index()                              # mean of valid cycles
    for f in BW.FEAT:
        if B[f].isna().any():
            B.loc[B[f].isna(), f] = B[B.cell.isin(train_u) & (B.block == 1)][f].median()
    B['L'] = B.cell.map(Lc); B['rul'] = (B.L - B.block * kappa) / kappa; B['batch'] = B.cell.str[1].astype(int)
    return B


def battery_splits(cells):
    out = []
    for f, te in enumerate(outer_folds(cells), 1): out.append(('cv123', f'cv{f}', np.setdiff1d(cells, te), np.sort(te), 100 + f))
    for b in (1, 2, 3):
        te = np.array(sorted(c for c in cells if c.startswith(f'b{b}'))); out.append(('lobo', f'lobo{b}', np.setdiff1d(cells, te), te, 100 + b))
    c119 = np.setdiff1d(cells, BW.NOISY)
    for f, te in enumerate(outer_folds(c119), 1): out.append(('cv119', f'cv119_{f}', np.setdiff1d(c119, te), np.sort(te), 100 + f))
    return out


# ------------------------------------------------------------------ bearing data
def bearing_snapshots():
    S = pd.read_csv('bearing/femto_snapshot_features.csv.gz').sort_values(['bearing', 'snapshot'])
    for f in GW.FEAT:
        S[f] = S[f].where(np.isfinite(S[f])); S[f] = S.groupby('bearing')[f].transform(lambda s: s.ffill())
    assert S[GW.FEAT].notna().all().all()
    return S, S.groupby('bearing').snapshot.max()


def bearing_blocks(S, kappa, L):
    S = S.copy(); S['block'] = (S.snapshot - 1) // kappa + 1; S['L'] = S.bearing.map(L); S = S[S.block <= S.L // kappa]
    B = S.groupby(['bearing', 'block']).agg({**{f: 'mean' for f in GW.FEAT}, 'condition': 'first', 'set': 'first', 'L': 'first'}).reset_index()
    B['rul'] = (B.L - B.block * kappa) / kappa
    return B


# ------------------------------------------------------------------ generic self-timed model on a block frame (for sensitivity)
def in_counts_g(P, H, k, lo, hi, shifts):
    thr = H - shifts; tot = np.zeros(len(shifts))
    for p, y in P.values():
        mk = pd.Series(p).rolling(k, min_periods=k).max().values; mk = np.where(np.isnan(mk), np.inf, mk); rm = np.minimum.accumulate(mk)
        i = np.searchsorted(-rm, -thr, side='left'); ok = i < len(p); ii = np.minimum(i, len(p) - 1)
        e = p[ii] + shifts - y[ii]; tot += ok & (e >= lo) & (e <= hi)
    return tot


def evaluate_g(P, H, k, s, lo, hi):
    R = pd.DataFrame([(u,) + W.warn(p + s, y, H, k) for u, (p, y) in P.items()], columns=['unit', 'pred', 'y', 'cycle']); e = R.pred - R.y
    R['cls'] = np.where(R.pred.isna(), 'MISSED', np.where(e > hi, 'LATE', np.where(e < lo, 'EARLY', 'IN'))); return R


def stw_split(feats_fn, B, train_u, test_u, seed, H, lo, hi, caps, shifts, capmin):
    def fit(tr, tg):
        F, Y = feats_fn(B, tr); X = np.vstack([F[u] for u in tr]); y = np.concatenate([Y[u] for u in tr])
        return {c: (lambda m: {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in tg})(W.gbm(X, y, c)) for c in caps}
    oof = {c: {} for c in caps}
    for iu in np.array_split(np.random.default_rng(seed).permutation(train_u), 5):
        if len(iu) == 0: continue
        p = fit(np.setdiff1d(train_u, iu), iu)
        for c in caps: oof[c].update(p[c])
    fin = fit(train_u, test_u); best = None
    for c in caps:
        if c < capmin: continue
        for sp in W.SPANS:
            Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[c].items()}
            for k in W.KS:
                tot = in_counts_g(Po, H, k, lo, hi, shifts) - 0.001 * np.abs(shifts); j = int(np.argmax(tot))
                if best is None or tot[j] > best[0]: best = (tot[j], c, sp, k, shifts[j])
    _, c, sp, k, s = best
    return evaluate_g({u: (W.smooth(p, sp), y) for u, (p, y) in fin[c].items()}, H, k, s, lo, hi).assign(cap=c, span=sp, k=k, shift=s)


# ------------------------------------------------------------------ battery-specific baselines (no fitted regressor)
def capacity_series(B, units):
    return {u: (g.QDischarge.values[:-1], g.rul.values[:-1]) for u, g in B[B.cell.isin(units)].groupby('cell')}


def trend_rul(q, w, kap):
    """causal least-squares slope of capacity over the last w blocks; extrapolated blocks until 0.88 Ah (80 % of 1.1 Ah)"""
    n = len(q); out = np.full(n, 1e3)
    for i in range(n):
        a = max(0, i - w + 1)
        if i - a + 1 >= 5:
            x = np.arange(a, i + 1); sl = np.polyfit(x, q[a:i + 1], 1)[0]
            if sl < 0: out[i] = min(1e3, max(0.0, (q[i] - 0.88) / (-sl)))
    return out


def baselines_split(B, train_u, test_u, H=20, lo=-13, hi=2):
    rows = []; tr, te = capacity_series(B, train_u), capacity_series(B, test_u)
    # capacity threshold alarm, constant estimate c in [H-6, H]
    qv = np.concatenate([q[y <= 80] for q, y in tr.values()]); TH = np.unique(np.quantile(qv, np.linspace(0.02, 0.995, 120)))
    cg = np.arange(H - 6, H + 0.01, 0.5); best = None
    for sp in W.SPANS:
        for k in W.KS:
            ya = []
            for q, y in tr.values():
                qs = W.smooth(q, sp); mk = pd.Series(qs).rolling(k, min_periods=k).max().values; mk = np.where(np.isnan(mk), np.inf, mk); rm = np.minimum.accumulate(mk)
                i = np.searchsorted(-rm, -TH, side='left'); ok = i < len(q); ya.append(np.where(ok, y[np.minimum(i, len(q) - 1)], np.nan))
            ya = np.array(ya); d = cg[None, None, :] - ya[:, :, None]; n = ((d >= lo) & (d <= hi)).sum(0)
            j = np.unravel_index(int(np.argmax(n)), n.shape)
            if best is None or n[j] > best[0]: best = (n[j], sp, k, TH[j[0]], cg[j[1]])
    _, sp, k, th, c = best
    for u, (q, y) in te.items():
        _, yy, cyc = W.warn(W.smooth(q, sp), y, th, k)
        pred = np.nan if np.isnan(yy) else c; e = pred - yy
        rows.append(dict(unit=u, pred=pred, y=yy, cycle=cyc, method='capacity_threshold', cls='MISSED' if np.isnan(pred) else ('LATE' if e > hi else ('EARLY' if e < lo else 'IN')), setting=f'{sp}|{k}|{th:.4f}|{c}'))
    # capacity-trend extrapolation with the self-timed trigger (span, debounce, shift selected on training units)
    best = None
    for w in (10, 20, 40):
        Ptr = {u: (trend_rul(q, w, 1), y) for u, (q, y) in tr.items()}
        for sp in W.SPANS:
            Po = {u: (W.smooth(p, sp), y) for u, (p, y) in Ptr.items()}
            for k in W.KS:
                tot = in_counts_g(Po, H, k, lo, hi, W.SHIFTS) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                if best is None or tot[j] > best[0]: best = (tot[j], w, sp, k, W.SHIFTS[j])
    _, w, sp, k, s = best
    R = evaluate_g({u: (W.smooth(trend_rul(q, w, 1), sp), y) for u, (q, y) in te.items()}, H, k, s, lo, hi)
    rows += [dict(unit=r.unit, pred=r.pred, y=r.y, cycle=r.cycle, method='capacity_trend', cls=r.cls, setting=f'{w}|{sp}|{k}|{s}') for r in R.itertuples()]
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ modes
def battery_corrected():
    S, Lc = battery_cycles(); cells = np.sort(Lc.index.values); parts = []
    for an, name, tr, te, seed in battery_splits(cells):
        kap = kap_rule(Lc[tr].values)
        def run():
            B = battery_blocks(S, kap, Lc, tr); return BW.run_split(B, name, tr, te, seed)
        R = ckpt(f'battery_corrected_{name}', run).assign(analysis=an, kappa=kap)
        R['life_cycles'] = R.unit.map(Lc); parts.append(R); print(f'battery {name}: kappa {kap}', flush=True)
    A = pd.concat(parts); A.to_csv(f'{OUT}/battery_corrected.csv', index=False); return A


def battery_sens(kappas):
    S, Lc = battery_cycles(); cells = np.sort(Lc.index.values); parts = []
    for kap in kappas:
        for an, name, tr, te, seed in [x for x in battery_splits(cells) if x[0] == 'cv123']:
            def run():
                B = battery_blocks(S, kap, Lc, tr)
                return stw_split(BW.features, B, tr, te, seed, H=60 / kap, lo=-39 / kap, hi=6 / kap, caps=[120 / kap, 180 / kap, 270 / kap],
                                 shifts=np.arange(-36, 24.01, 1.5) / kap, capmin=120 / kap)
            parts.append(ckpt(f'battery_sens_k{kap}_{name}', run).assign(kappa=kap, split=name)); print(f'battery sens kappa {kap} {name}', flush=True)
        A = pd.concat(parts); A['life_cycles'] = A.unit.map(Lc); A.to_csv(f'{OUT}/battery_sensitivity.csv', index=False)


def battery_baselines():
    S, Lc = battery_cycles(); cells = np.sort(Lc.index.values); parts = []
    for an, name, tr, te, seed in [x for x in battery_splits(cells) if x[0] in ('cv123', 'lobo')]:
        kap = kap_rule(Lc[tr].values)
        parts.append(ckpt(f'battery_baselines_{name}', lambda: baselines_split(battery_blocks(S, kap, Lc, tr), tr, te)).assign(analysis=an, split=name, kappa=kap))
        print(f'battery baselines {name}', flush=True)
    A = pd.concat(parts); A.to_csv(f'{OUT}/battery_baselines.csv', index=False)


def bearing_corrected():
    S, L = bearing_snapshots(); units = np.sort(L.index.values); parts = []
    splits = [(f'cv{f}', np.setdiff1d(units, te), np.sort(te), 100 + f, 'cv') for f, te in enumerate(outer_folds(units), 1)]
    sets = S.drop_duplicates('bearing').set_index('bearing').set
    splits.append(('official', np.sort(sets[sets == 'Learning_set'].index.values), np.sort(sets[sets == 'Full_Test_Set'].index.values), 106, 'official'))
    for name, tr, te, seed, an in splits:
        kap = kap_rule(L[tr].values)
        R = ckpt(f'bearing_corrected_{name}', lambda: GW.run_split(bearing_blocks(S, kap, L), name, tr, te, seed)).assign(analysis=an, kappa=kap)
        R['life_snapshots'] = R.unit.map(L); parts.append(R); print(f'bearing {name}: kappa {kap}', flush=True)
    A = pd.concat(parts); A.to_csv(f'{OUT}/bearing_corrected.csv', index=False)


def bearing_sens(kappas):
    S, L = bearing_snapshots(); units = np.sort(L.index.values); parts = []
    for kap in kappas:
        for f, te in enumerate(outer_folds(units), 1):
            tr = np.setdiff1d(units, te); name = f'cv{f}'
            run = lambda: stw_split(GW.features, bearing_blocks(S, kap, L), tr, np.sort(te), 100 + f, H=140 / kap, lo=-91 / kap, hi=14 / kap,
                                    caps=[280 / kap, 420 / kap, 630 / kap], shifts=np.arange(-84, 56.01, 3.5) / kap, capmin=280 / kap)
            parts.append(ckpt(f'bearing_sens_k{kap}_{name}', run).assign(kappa=kap, split=name)); print(f'bearing sens kappa {kap} {name}', flush=True)
    A = pd.concat(parts); A['life_snapshots'] = A.unit.map(L); A.to_csv(f'{OUT}/bearing_sensitivity.csv', index=False)


if __name__ == '__main__':
    t0 = time.time(); mode = ARGS[0]; ks = [int(x) for x in ARGS[1:]]
    {'battery_corrected': battery_corrected, 'battery_baselines': battery_baselines, 'bearing_corrected': bearing_corrected,
     'battery_sens': lambda: battery_sens(ks), 'bearing_sens': lambda: bearing_sens(ks)}[mode]()
    print(f'{mode} done in {time.time() - t0:.0f}s')
