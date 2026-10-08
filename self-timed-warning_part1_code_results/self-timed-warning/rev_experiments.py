"""Revision experiments for the STW manuscript (exploratory; added after the original results were known).

R1  Constant-estimate control: keep the STW warning time, replace its reported estimate by one constant c chosen on
    the training engines' out-of-fold (OOF) warnings. If R1 ~= STW, the in-window rate measures alarm timing.
R2  Health-indicator (HI) threshold alarm baseline (no RUL regressor): a linear HI in the style of Wang et al. (2008),
    least squares of the EWM(10) baseline-removed regime-normalised sensors onto 1 (last 5 cycles) / 0 (first 30
    cycles); causal EWM smoothing m, alarm when HI >= theta for k consecutive cycles, reported estimate = constant c
    with H-6 <= c <= H (the range of estimates STW reports at level H). theta, m, k, c chosen on training OOF only.
R3  Cost-primary evaluation (renewal-reward, as manuscript Sec. 5.6): each alarm policy is tuned on training OOF to
    minimise the long-run cost rate for each (lead l, cost ratio rho); STW-cost (threshold tau on the smoothed
    estimate, no window), STW-window (window-tuned STW, H chosen per (l, rho): the manuscript's analysis),
    HI-cost, optimal age replacement, perfect foresight, run-to-failure.
Splits, seeds, model, grids: identical to eol_window2.py (outer 5-fold seed 2026, inner 5-fold seed 100+fold).
Usage: python rev_experiments.py DATASET [DATASET ...]   (PHM08 FD001 FD002 FD003 FD004 NCMAPSS6 Battery)
Output: out/rev/<ds>_window.csv (per test unit, per method and H), out/rev/<ds>_cost.csv (per test unit, per policy, l, rho)
"""
import sys, os, time, numpy as np, pandas as pd
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
import eol_window2 as W
from safe_common import load_dataset, outer_folds
from feats import regime_stats, zmat, causal_feats

HS = [10, 15, 20, 30, 40]; LO, HI_ = -13, 2
LEADS = [0, 5, 10, 15]; RHOS = [5, 10, 20, 50]
TAUS = np.arange(1, 61, 1.0)
CGRID = np.arange(0, 50.5, 0.5)


# ------------------------------------------------------------------ data adapters
def adapter(ds):
    """returns units, feats(stat_units, units) -> (F, Y); F[u] causal features (last column = age), Y[u] true RUL"""
    if ds in ('PHM08', 'FD001', 'FD002', 'FD003', 'FD004'):
        tr, _, _ = load_dataset(ds); G = dict(list(tr.groupby('unit')))
        def feats(stat_u, use_u):
            st, keep = regime_stats(tr[tr.unit.isin(stat_u)])
            return ({u: causal_feats(zmat(G[u], st, keep)) for u in use_u}, {u: G[u].rul.values.astype(float) for u in use_u})
        return np.sort(tr.unit.unique()), feats
    if ds == 'NCMAPSS6':
        import ncm_warning as N
        D = N.load(); G = dict(list(D.groupby('uid')))
        def feats(stat_u, use_u):
            F, Y = N.features(D[D.uid.isin(np.concatenate([stat_u, use_u]))], stat_u)
            return {u: F[u] for u in use_u}, {u: Y[u] for u in use_u}
        return np.sort(D.uid.unique()), feats
    if ds == 'Battery':
        import battery_warning as B
        Bd, kappa, Lc = B.load()
        def feats(stat_u, use_u):
            F, Y = B.features(Bd[Bd.cell.isin(np.concatenate([stat_u, use_u]))], stat_u)
            return {u: F[u] for u in use_u}, {u: Y[u] for u in use_u}
        return np.sort(Bd.cell.unique()), feats
    raise ValueError(ds)


def models(feats, train_u, target_u):
    """GBM predictions for the three caps (as eol_window2) and the linear HI; series over cycles with RUL >= 1"""
    F, Y = feats(train_u, np.unique(np.concatenate([train_u, target_u])))
    X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u])
    out = {}
    for cap in W.CAPS:
        m = W.gbm(X, y, cap); out[cap] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
    p = (X.shape[1] - 1) // 5                              # block 0 = EWM(10) of baseline-removed signals
    rows = [(F[u][:, :p], Y[u]) for u in train_u]
    Xh = np.vstack([np.vstack([f[:30], f[r <= 5]]) for f, r in rows])
    yh = np.concatenate([np.concatenate([np.zeros(min(30, len(f))), np.ones((r <= 5).sum())]) for f, r in rows])
    A = np.column_stack([Xh, np.ones(len(Xh))]); w = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ yh)
    out['HI'] = {u: (F[u][:-1, :p] @ w[:-1] + w[-1], Y[u][:-1]) for u in target_u}
    return out


# ------------------------------------------------------------------ alarm machinery
def first_idx(s, k, thr):
    """first index i at which s has been <= thr for k consecutive cycles, for every thr (len(s) if never)"""
    mk = pd.Series(s).rolling(k, min_periods=k).max().values; mk = np.where(np.isnan(mk), np.inf, mk)
    nrm = -np.minimum.accumulate(mk)
    return np.searchsorted(nrm, -np.asarray(thr), side='left')


def alarm_table(P, k, thr):
    """P: {u: (s, y)} -> arrays (U, T): ok, y at alarm, cycle at alarm; L (U,) life in model units"""
    U = list(P); ok, ya, ta, L = [], [], [], []
    for u in U:
        s, y = P[u]; i = first_idx(s, k, thr); o = i < len(s); ii = np.minimum(i, len(s) - 1)
        ok.append(o); ya.append(np.where(o, y[ii], np.nan)); ta.append(np.where(o, ii + 1, np.nan)); L.append(y[0] + 1)
    return U, np.array(ok), np.array(ya), np.array(ta), np.array(L)


def cost_of(ok, ya, ta, L, l, rho):
    planned = ok & (ya > l)
    c = np.where(planned, 1.0, rho); use = np.where(planned, ta + l, L[:, None] if ok.ndim == 2 else L)
    return c, use, planned


def cls_of(pred, y):
    e = pred - y
    return np.where(np.isnan(pred), 'MISSED', np.where(e > HI_, 'LATE', np.where(e < LO, 'EARLY', 'IN')))


# ------------------------------------------------------------------ one dataset
def run(ds):
    t0 = time.time(); units, feats = adapter(ds); wrows, crows, sel = [], [], []
    import pickle; os.makedirs('out/rev/ckpt', exist_ok=True)
    for fold, test_u in enumerate(outer_folds(units), 1):
        ck = f'out/rev/ckpt/{ds}_fold{fold}.pkl'
        if os.path.exists(ck):
            a, b, c = pickle.load(open(ck, 'rb')); wrows += a; crows += b; sel += c; print(f'{ds} fold {fold} loaded from checkpoint', flush=True); continue
        n0 = (len(wrows), len(crows), len(sel))
        train_u = np.setdiff1d(units, test_u)
        inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5)
        oof = {c: {} for c in W.CAPS + ['HI']}
        for iu in inner:
            p = models(feats, np.setdiff1d(train_u, iu), iu)
            for c in oof: oof[c].update(p[c])
        fin = models(feats, train_u, test_u)
        # HI threshold grid from training OOF HI values near the end of life
        hv = np.concatenate([s[y <= 80] for s, y in oof['HI'].values()])
        THETA = np.unique(np.quantile(hv, np.linspace(0.02, 0.995, 120)))
        Loof = {u: y[0] + 1 for u, (_, y) in oof[W.CAPS[0]].items()}; Lte = {u: y[0] + 1 for u, (_, y) in fin[W.CAPS[0]].items()}

        # ---------- R0 / R1: STW window selection (identical to eol_window2) + constant-estimate control
        stw_sel = {}
        for H in HS:
            best = None
            for cap in W.CAPS:
                if cap < H + 20: continue
                for sp in W.SPANS:
                    Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
                    for k in W.KS:
                        tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                        if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
            _, cap, sp, k, s = best; stw_sel[H] = (cap, sp, k, s)
            R = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in fin[cap].items()}, H, k, s)
            Ro = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}, H, k, s)
            ow = Ro.dropna(subset=['pred'])
            cnt = np.array([(((c - ow.y) >= LO) & ((c - ow.y) <= HI_)).sum() for c in CGRID]) - 1e-3 * np.abs(CGRID - ow.pred.median())
            c = CGRID[int(np.argmax(cnt))]
            for _, r in R.iterrows():
                wrows.append(dict(fold=fold, H=H, method='STW', unit=r.unit, pred=r.pred, y=r.y, cycle=r.cycle, cls=r.cls))
                pc = np.nan if np.isnan(r.pred) else c
                wrows.append(dict(fold=fold, H=H, method='STW_const', unit=r.unit, pred=pc, y=r.y, cycle=r.cycle, cls=cls_of(np.array([pc]), np.array([r.y]))[0]))
            sel.append(dict(fold=fold, H=H, method='STW', cap=cap, span=sp, k=k, shift=s, const=c))

        # ---------- R2: HI threshold alarm, constant estimate c in [H-6, H]
        HItab = {}
        for sp in W.SPANS:
            Po = {u: (-W.smooth(s, sp), y) for u, (s, y) in oof['HI'].items()}
            Pt = {u: (-W.smooth(s, sp), y) for u, (s, y) in fin['HI'].items()}
            for k in W.KS:
                HItab[(sp, k)] = (alarm_table(Po, k, -THETA), alarm_table(Pt, k, -THETA))
        for H in HS:
            cg = np.arange(H - 6, H + 0.01, 0.5); best = None
            for (sp, k), ((U, ok, ya, ta, L), _) in HItab.items():
                d = cg[None, None, :] - ya[:, :, None]
                n = (ok[:, :, None] & (d >= LO) & (d <= HI_)).sum(0)            # (T, C)
                j = np.unravel_index(int(np.argmax(n)), n.shape)
                if best is None or n[j] > best[0]: best = (n[j], sp, k, j[0], cg[j[1]])
            _, sp, k, ti, c = best; U, ok, ya, ta, L = HItab[(sp, k)][1]
            for ui, u in enumerate(U):
                pc = c if ok[ui, ti] else np.nan
                wrows.append(dict(fold=fold, H=H, method='HI_threshold', unit=u, pred=pc, y=ya[ui, ti], cycle=ta[ui, ti],
                                  cls=cls_of(np.array([pc]), np.array([ya[ui, ti]]))[0]))
            sel.append(dict(fold=fold, H=H, method='HI_threshold', span=sp, k=k, theta=THETA[ti], const=c))

        # ---------- R3: cost-primary policies
        STWtab = {}
        for cap in W.CAPS:
            for sp in W.SPANS:
                Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
                Pt = {u: (W.smooth(p, sp), y) for u, (p, y) in fin[cap].items()}
                for k in W.KS:
                    STWtab[(cap, sp, k)] = (alarm_table(Po, k, TAUS), alarm_table(Pt, k, TAUS))
        # window-tuned STW warnings for each H (train OOF and test), the manuscript's cost analysis
        WIN = {}
        for H, (cap, sp, k, s) in stw_sel.items():
            Po = {u: (W.smooth(p, sp) + s, y) for u, (p, y) in oof[cap].items()}; Pt = {u: (W.smooth(p, sp) + s, y) for u, (p, y) in fin[cap].items()}
            WIN[H] = (alarm_table(Po, k, [H]), alarm_table(Pt, k, [H]))
        Ltr = np.array(list(Loof.values())); Ts = np.arange(1, int(Ltr.max()) + 1)
        for l in LEADS:
            for rho in RHOS:
                def pick(tab):
                    best = None
                    for key, ((U, ok, ya, ta, L), _) in tab.items():
                        c, use, _ = cost_of(ok, ya, ta, L, l, rho); r = c.sum(0) / use.sum(0); j = int(np.argmin(r))
                        if best is None or r[j] < best[0]: best = (r[j], key, j)
                    return best
                for name, tab in (('STW_cost', STWtab), ('HI_cost', HItab), ('STW_window', WIN)):
                    _, key, j = pick(tab); U, ok, ya, ta, L = tab[key][1]
                    c, use, pl = cost_of(ok[:, j], ya[:, j], ta[:, j], L, l, rho)
                    for ui, u in enumerate(U):
                        crows.append(dict(fold=fold, lead=l, rho=rho, policy=name, unit=u, cost=c[ui], use=use[ui], fail=not pl[ui],
                                          lead_true=ya[ui, j], setting=str(key) + f'|{j}'))
                # optimal age replacement on training lives (Barlow-Hunter), test lives
                cr = np.array([np.where(Ltr > T, 1.0, rho).sum() / np.minimum(Ltr, T).sum() for T in Ts]); T = Ts[int(np.argmin(cr))]
                for u, Lu in Lte.items():
                    crows.append(dict(fold=fold, lead=l, rho=rho, policy='age', unit=u, cost=1.0 if Lu > T else rho, use=min(Lu, T), fail=Lu <= T, lead_true=np.nan, setting=str(T)))
                    crows.append(dict(fold=fold, lead=l, rho=rho, policy='perfect_foresight', unit=u, cost=1.0, use=Lu - 1, fail=False, lead_true=1, setting=''))
                    crows.append(dict(fold=fold, lead=l, rho=rho, policy='run_to_failure', unit=u, cost=rho, use=Lu, fail=True, lead_true=0, setting=''))
        pickle.dump((wrows[n0[0]:], crows[n0[1]:], sel[n0[2]:]), open(ck + '.tmp', 'wb')); os.replace(ck + '.tmp', ck)
        print(f'{ds} fold {fold} done  ({time.time() - t0:.0f}s)', flush=True)
    os.makedirs('out/rev', exist_ok=True)
    pd.DataFrame(wrows).to_csv(f'out/rev/{ds}_window.csv', index=False)
    pd.DataFrame(crows).to_csv(f'out/rev/{ds}_cost.csv', index=False)
    pd.DataFrame(sel).to_csv(f'out/rev/{ds}_selected.csv', index=False)
    Wd = pd.DataFrame(wrows)
    print(Wd.groupby(['H', 'method']).cls.apply(lambda s: f'{(s == "IN").sum()}/{len(s)}').unstack().to_string())


if __name__ == '__main__':
    for ds in ARGS: run(ds)
