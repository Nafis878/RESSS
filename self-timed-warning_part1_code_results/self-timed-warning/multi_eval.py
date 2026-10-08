"""Tolerance-window sensitivity and maintenance-cost analysis of the self-timed warning model.

For each dataset: outer 5-fold engine CV (seed 2026) and inner 5-fold OOF predictions (seed 100 + fold) exactly as
eol_window2.py; the regressors are fitted once per fold and reused for all windows and warning levels.
(1) Windows [-10,+2], [-13,+2], [-20,+5], [-30,+10]: settings (cap, span, k, shift) re-selected for each window and level.
(2) Cost analysis (window [-13,+2]): a warning at t* triggers a planned replacement l cycles later (logistics lead time
    l in {0, 5, 10, 15}); if the engine fails first (true remaining life at the warning <= l) or is never warned, it fails.
    Cost per engine: 1 for a planned replacement, rho in {5, 10, 20, 50} for a failure; cost rate = total cost / total
    cycles operated (renewal-reward). The warning level H in {10, 15, 20, 30, 40} is chosen per (l, rho) on the training
    engines' out-of-fold warnings, then applied to the test engines. Baselines: age-based replacement with the age T chosen
    on the training engines' lives (classical optimal age replacement), run-to-failure, and perfect foresight
    (replacement one cycle before failure).
Datasets: PHM08, FD001-FD004, N-CMAPSS (six sensors as pre-specified) and, exploratory, N-CMAPSS with all 14 sensors.
Output: out/multi/<ds>_windows.csv, <ds>_cost.csv, <ds>_warnings.csv
"""
import sys, os, numpy as np, pandas as pd
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]          # eol_window2 parses sys.argv at import
import eol_window2 as W
from safe_common import load_dataset, outer_folds
from feats import causal_feats
WINDOWS = [(-10, 2), (-13, 2), (-20, 5), (-30, 10)]; HS = [10, 15, 20, 30, 40]
LEADS = [0, 5, 10, 15]; RHOS = [5, 10, 20, 50]
NCM6 = ['T24', 'T30', 'T48', 'T50', 'Nf', 'Nc']
NCM14 = ['T24', 'T30', 'T48', 'T50', 'P15', 'P2', 'P21', 'P24', 'Ps30', 'P40', 'P50', 'Nf', 'Nc', 'Wf']

def prep(P, k):
    """per unit: (p, y, running minimum of the k-cycle rolling maximum); computed once per (cap, span, k)"""
    out = []
    for p, y in P.values():
        mk = pd.Series(p).rolling(k, min_periods=k).max().values; mk = np.where(np.isnan(mk), np.inf, mk)
        out.append((p, y, -np.minimum.accumulate(mk)))
    return out

def in_counts(Q, H, lo, hi):
    """identical rule to eol_window2.in_counts, on prepared units"""
    thr = -(H - W.SHIFTS); tot = np.zeros(len(W.SHIFTS))
    for p, y, nrm in Q:
        i = np.searchsorted(nrm, thr, side='left'); ok = i < len(p); ii = np.minimum(i, len(p) - 1)
        e = p[ii] + W.SHIFTS - y[ii]; tot += ok & (e >= lo) & (e <= hi)
    return tot

def warnings(P, H, k, s):
    out = {}
    for u, (p, y) in P.items():
        q = p + s; run = np.convolve((q <= H).astype(int), np.ones(k, int), 'full')[:len(q)] >= k; i = np.flatnonzero(run)
        out[u] = (q[i[0]], y[i[0]], i[0] + 1) if len(i) else (np.nan, np.nan, np.nan)
    return out

def ncm_frame(sensors):
    R = pd.read_csv('ncm/ncmapss_cycle_summary.csv.gz'); key = R.subset + '|' + R.part + '|' + R.unit.astype(int).astype(str)
    ids = {k: i + 1 for i, k in enumerate(sorted(key.unique()))}; R['unit'] = key.map(ids); R['regime'] = R.Fc.round().astype(int)
    R = R.sort_values(['unit', 'cycle']).reset_index(drop=True); R['life'] = R.groupby('unit').cycle.transform('max'); R['rul'] = R.life - R.cycle
    return R, sensors

def predict_generic(tr, sensors, train_u, target_u):
    st = {s: tr[tr.unit.isin(train_u)].groupby('regime')[s].agg(['mean', 'std']) for s in sensors}; F, Y = {}, {}
    for u, g in tr[tr.unit.isin(np.concatenate([train_u, target_u]))].groupby('unit'):
        Z = np.nan_to_num(np.column_stack([(g[s].values - g.regime.map(st[s]['mean']).values) / g.regime.map(st[s]['std']).values.clip(1e-6) for s in sensors]))
        F[u] = causal_feats(Z); Y[u] = g.rul.values.astype(float)
    X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u]); out = {}
    for cap in W.CAPS:
        m = W.gbm(X, y, cap); out[cap] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
    return out

def main(ds):
    if ds.startswith('NCMAPSS'):
        tr, sensors = ncm_frame(NCM14 if ds.endswith('14') else NCM6); pred = lambda a, b: predict_generic(tr, sensors, a, b)
    else:
        tr, _, _ = load_dataset(ds); pred = lambda a, b: W.predict_all(tr, a, b, a)
    units = np.sort(tr.unit.unique()); life = tr.groupby('unit').cycle.max(); wrows, crow, warn_rows = [], [], []
    for fold, test_u in enumerate(outer_folds(units), 1):
        train_u = np.setdiff1d(units, test_u); inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5); oof = {c: {} for c in W.CAPS}
        for iu in inner:
            p = pred(np.setdiff1d(train_u, iu), iu)
            for c in W.CAPS: oof[c].update(p[c])
        final = pred(train_u, test_u)
        PREP = {(cap, sp, k): prep({u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}, k) for cap in W.CAPS for sp in W.SPANS for k in W.KS}
        for lo, hi in WINDOWS:
            for H in HS:
                best = None
                for cap in W.CAPS:
                    if cap < H + 20: continue
                    for sp in W.SPANS:
                        for k in W.KS:
                            tot = in_counts(PREP[(cap, sp, k)], H, lo, hi) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                            if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
                _, cap, sp, k, s = best
                te = warnings({u: (W.smooth(p, sp), y) for u, (p, y) in final[cap].items()}, H, k, s)
                for u, (pw, yw, cw) in te.items():
                    e = pw - yw; cls = 'MISSED' if np.isnan(pw) else ('LATE' if e > hi else ('EARLY' if e < lo else 'IN'))
                    wrows.append(dict(fold=fold, lo=lo, hi=hi, H=H, unit=u, pred=pw, y=yw, cycle=cw, life=life[u], cls=cls, cap=cap, span=sp, k=k, shift=s))
                if (lo, hi) == (-13, 2):
                    tw = warnings({u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}, H, k, s)
                    for u, (pw, yw, cw) in tw.items(): warn_rows.append(dict(fold=fold, role='train_oof', H=H, unit=u, pred=pw, y=yw, cycle=cw, life=life[u]))
                    for u, (pw, yw, cw) in te.items(): warn_rows.append(dict(fold=fold, role='test', H=H, unit=u, pred=pw, y=yw, cycle=cw, life=life[u]))
        print(ds, 'fold', fold, 'done', flush=True)
    os.makedirs('out/multi', exist_ok=True)
    WR = pd.DataFrame(wrows); WR.to_csv(f'out/multi/{ds}_windows.csv', index=False); WN = pd.DataFrame(warn_rows); WN.to_csv(f'out/multi/{ds}_warnings.csv', index=False)
    # ---------------- cost analysis
    def policy_cost(df, l, rho):
        planned = df.pred.notna() & (df.y > l); use = np.where(planned, df.cycle + l, df.life); cost = np.where(planned, 1.0, rho)
        return cost.sum(), use.sum(), int((~planned).sum())
    rows = []
    for fold in sorted(WN.fold.unique()):
        trn = WN[(WN.fold == fold) & (WN.role == 'train_oof')]; tst = WN[(WN.fold == fold) & (WN.role == 'test')]
        Ltr = life[np.setdiff1d(units, tst.unit.unique())].values; Lte = life[tst.unit.unique()].values
        for l in LEADS:
            for rho in RHOS:
                bestH = min(HS, key=lambda H: (lambda c, u, f: c / u)(*policy_cost(trn[trn.H == H], l, rho)))
                c, u, nf = policy_cost(tst[tst.H == bestH], l, rho)
                # optimal age replacement on training lives
                Ts = np.arange(1, Ltr.max() + 1); cr = [((np.where(Ltr > T, 1.0, rho)).sum()) / np.minimum(Ltr, T).sum() for T in Ts]; T = Ts[int(np.argmin(cr))]
                ca = np.where(Lte > T, 1.0, rho); ua = np.minimum(Lte, T)
                rows.append(dict(fold=fold, lead=l, rho=rho, H=bestH, stw_cost=c, stw_use=u, stw_fail=nf, age_T=int(T), age_cost=ca.sum(), age_use=ua.sum(), age_fail=int((Lte <= T).sum()),
                                 rtf_cost=rho * len(Lte), rtf_use=Lte.sum(), pf_cost=float(len(Lte)), pf_use=float((Lte - 1).sum()), n=len(Lte)))
    C = pd.DataFrame(rows); C.to_csv(f'out/multi/{ds}_cost.csv', index=False)
    S = C.groupby(['lead', 'rho']).sum(numeric_only=True)
    for p in ('stw', 'age', 'rtf', 'pf'): S[p + '_rate'] = S[p + '_cost'] / S[p + '_use']
    print(S[['stw_rate', 'age_rate', 'rtf_rate', 'pf_rate', 'stw_fail', 'age_fail']].round(4).to_string())
    print(WR.groupby(['lo', 'hi', 'H']).cls.apply(lambda s: round(100 * (s == 'IN').mean(), 1)).unstack().to_string())

if __name__ == '__main__':
    for ds in ARGS: main(ds)
