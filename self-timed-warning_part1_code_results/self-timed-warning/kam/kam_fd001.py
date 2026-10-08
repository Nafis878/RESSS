"""Phase 2: alarm policies of this repository and policies 1 and 3 of Kamariotis et al. (2024) on FD001, evaluated with
their metric M (re-implementation, kam_metric.py) on a decision grid dT = 10, replacement-only setting, lead time 0.
Plan fixed and hashed before the run: kam/PHASE2_PLAN.md (with amendment 1), kam/PHASE2_PLAN.sha256. Exploratory.

Usage (from the repository root; add --ds FD002|FD003|FD004 for Phase 3, default FD001):
  python kam/kam_fd001.py cv                 protocol (B): five-fold CV, existing FD001 folds (seed 2026, inner 100 + fold)
  python kam/kam_fd001.py splits [s0 s1]     protocol (A): random 80/20 splits s0..s1 (default 1..30), seed 31000 + s
  python kam/kam_fd001.py leak               leakage checks E2-E4 on fold 1 of protocol (B) (E1 runs inside every split)
Outputs (out/kam/): fd001_<protocol>_units.csv (one row per protocol, split, cost ratio, policy, test unit),
fd001_<protocol>_settings.csv, fd001_<protocol>_bins.csv, fd001_leakage.txt; checkpoints in out/kam/ckpt/.
"""
import os, sys, time, pickle
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
DS = 'FD001'                                                    # Phase 3: --ds FD002|FD003|FD004 runs the identical code path
if '--ds' in ARGS: i = ARGS.index('--ds'); DS = ARGS[i + 1]; del ARGS[i:i + 2]
TAG = DS.lower()
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
import eol_window2 as W
import rev_experiments as R
from safe_common import load_dataset, outer_folds
from feats import regime_stats, zmat, causal_feats
import kam_metric as K

DT = 10.0; QS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8]; Q_PRIMARY = 0.1
PGRID = np.unique(np.round(np.concatenate([np.logspace(-4, 0, 400), np.arange(1, 1001) / 1000]), 12))
CAP_RES, CAP_SENS, NBINS, MINBIN, NB = 60, 125, 20, 200, 200
OUT = 'out/kam'; os.makedirs(OUT + '/ckpt', exist_ok=True)
UNITS, FEATS = R.adapter(DS)


# ------------------------------------------------------------------ models
def classifier():
    return HistGradientBoostingClassifier(loss='log_loss', max_iter=500, learning_rate=0.05, max_leaf_nodes=31,
                                          min_samples_leaf=40, random_state=0)


def fit_models(train_u, target_u, feats=FEATS):
    """Regressors for caps 40/60/90 (recipe) and 125 (sensitivity), the linear HI of rev_experiments, and the
    classifier of 1{RUL <= dT}; each returns, per target unit, (series over cycles 1..L-1, true RUL over cycles 1..L-1)."""
    F, Y = feats(train_u, np.unique(np.concatenate([train_u, target_u])))
    X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u]); out = {}
    for cap in W.CAPS + [CAP_SENS]:
        m = W.gbm(X, y, cap); out[cap] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
    p = (X.shape[1] - 1) // 5
    rows = [(F[u][:, :p], Y[u]) for u in train_u]
    Xh = np.vstack([np.vstack([f[:30], f[r <= 5]]) for f, r in rows])
    yh = np.concatenate([np.concatenate([np.zeros(min(30, len(f))), np.ones((r <= 5).sum())]) for f, r in rows])
    A = np.column_stack([Xh, np.ones(len(Xh))]); w = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ yh)
    out['HI'] = {u: (F[u][:-1, :p] @ w[:-1] + w[-1], Y[u][:-1]) for u in target_u}
    c = classifier().fit(X, (y <= DT).astype(int))
    out['CLS'] = {u: (c.predict_proba(F[u])[:-1, 1], Y[u][:-1]) for u in target_u}
    return out


# ------------------------------------------------------------------ grid-mapped cost and selection
def grid_cost(ok, ta, L, cc):
    """Alarm at cycle ta acts at the first grid point >= ta; preventive only if that point is before failure L."""
    Lb = L[:, None] if np.ndim(ok) == 2 else L
    g = np.where(ok, np.ceil(np.nan_to_num(ta, nan=0.0) / DT) * DT, np.inf); g = np.where(g < DT, DT, g)
    prev = ok & (g < Lb)
    return np.where(prev, 1.0, cc), np.where(prev, g, Lb), prev, np.where(prev, Lb - g, 0.0)


def boot_weights(n, seed):
    idx = np.random.default_rng(seed).integers(0, n, size=(NB, n)); w = np.zeros((NB, n))
    for b in range(NB): w[b] = np.bincount(idx[b], minlength=n)
    return w


def select_grid(tabs, cc, rule, wts):
    """As audit_cost.select, with the grid-mapped cost; 1-SE: largest mean remaining life at the replacement point."""
    stats = []
    for key, ((U, ok, ya, ta, L), _) in tabs.items():
        c, use, _, notice = grid_cost(ok, ta, L, cc); r = c.sum(0) / use.sum(0)
        rb = (wts @ c) / (wts @ use) if rule == '1se' else None
        stats.append((key, r, rb, notice.mean(0)))
    kmin, jmin, rmin = min(((k, int(np.argmin(r)), r.min()) for k, r, _, _ in stats), key=lambda t: t[2])
    if rule == 'plain': return kmin, jmin
    se = [rb[:, jmin] for k, r, rb, _ in stats if k == kmin][0].std()
    cand = [(lead[j], -r[j], k, j) for k, r, rb, lead in stats for j in np.flatnonzero(r <= rmin + se)]
    _, _, k, j = max(cand)
    return k, int(j)


def select_1cycle(tabs, rho, rule, wts):
    """Unmapped 1-cycle selection (lead 0), identical to audit_cost.select for 'plain' and '1se'."""
    stats = []
    for key, ((U, ok, ya, ta, L), _) in tabs.items():
        c, use, _ = R.cost_of(ok, ya, ta, L, 0, rho); r = c.sum(0) / use.sum(0)
        rb = (wts @ c) / (wts @ use) if rule == '1se' else None
        stats.append((key, r, rb, np.where(ok, ya, 0.0).mean(0)))
    kmin, jmin, rmin = min(((k, int(np.argmin(r)), r.min()) for k, r, _, _ in stats), key=lambda t: t[2])
    if rule == 'plain': return kmin, jmin
    se = [rb[:, jmin] for k, r, rb, _ in stats if k == kmin][0].std()
    cand = [(lead[j], -r[j], k, j) for k, r, rb, lead in stats for j in np.flatnonzero(r <= rmin + se)]
    _, _, k, j = max(cand)
    return k, int(j)


# ------------------------------------------------------------------ probability models
def grid_series(P):
    """{u: (series over cycles 1..L-1, rul)} -> {u: values at grid points t_k = 10k <= L-1}, L"""
    G, L = {}, {}
    for u, (s, y) in P.items():
        Lu = int(y[0] + 1); kmax = int((Lu - 1) // DT); idx = (np.arange(1, kmax + 1) * DT).astype(int) - 1
        G[u] = s[idx]; L[u] = Lu
    return G, L


def make_bins(yhat, r):
    """Equal-count bins of the OOF estimates (20 quantile edges), merging bins with fewer than MINBIN rows."""
    edges = np.unique(np.quantile(yhat, np.linspace(0, 1, NBINS + 1)[1:-1]))
    while True:
        b = np.searchsorted(edges, yhat, side='right'); cnt = np.bincount(b, minlength=len(edges) + 1)
        small = np.flatnonzero(cnt < MINBIN)
        if not len(small) or not len(edges): break
        i = small[0]; j = int(np.argmax(cnt))
        edges = np.delete(edges, i if i < j else i - 1)        # merge bin i with its neighbour towards the bulk
    return edges


def res_model(oof_cap, cap):
    """P-res: per-bin empirical distribution of the true RUL of OOF cycles (RUL above the cap set to the cap)."""
    yh = np.concatenate([s for s, _ in oof_cap.values()]); r = np.concatenate([y for _, y in oof_cap.values()])
    uid = np.concatenate([np.full(len(s), u) for u, (s, _) in oof_cap.items()])
    edges = make_bins(yh, r); b = np.searchsorted(edges, yh, side='right'); nb = len(edges) + 1
    rt = np.minimum(r, cap)
    cnt = np.bincount(b, minlength=nb).astype(float); p10 = np.bincount(b, weights=(r <= DT).astype(float), minlength=nb) / cnt
    p10_iso = IsotonicRegression(increasing=False).fit(np.arange(nb), p10, sample_weight=cnt).predict(np.arange(nb))
    dists = [rt[b == i] for i in range(nb)]
    diag = [dict(bin=i, lo=float(edges[i - 1]) if i else -np.inf, hi=float(edges[i]) if i < nb - 1 else np.inf, rows=int(cnt[i]),
                 units=int(len(np.unique(uid[b == i]))), p10_raw=float(p10[i]), p10_iso=float(p10_iso[i])) for i in range(nb)]
    return dict(edges=edges, p10=p10_iso, dists=dists, cap=cap, diag=diag)


def res_prob(model, s):
    return model['p10'][np.searchsorted(model['edges'], s, side='right')]


def cls_calibrator(oof_cls):
    p = np.concatenate([s for s, _ in oof_cls.values()]); lab = np.concatenate([(y <= DT) for _, y in oof_cls.values()]).astype(float)
    return IsotonicRegression(increasing=True, y_min=0.0, y_max=1.0, out_of_bounds='clip').fit(p, lab)


# ------------------------------------------------------------------ policy 1 and policy 3
def p1_first(G, thr):
    """First grid point (time) at which the probability series reaches thr; inf if never."""
    return {u: ((int(np.argmax(g >= thr)) + 1) * DT if (g >= thr).any() else np.inf) for u, g in G.items()}


def p1_optimise(G, L, cc):
    """Training cost rate for every threshold in PGRID; minimising set; 'mid' and 'max' tie rules."""
    C = np.zeros(len(PGRID)); T = np.zeros(len(PGRID))
    for u, g in G.items():
        cm = np.maximum.accumulate(g) if len(g) else np.array([]); i = np.searchsorted(cm, PGRID, side='left')
        tr = np.where(i < len(g), (i + 1) * DT, np.inf); prev = tr < L[u]
        C += np.where(prev, 1.0, cc); T += np.where(prev, tr, L[u])
    r = C / T; rmin = r.min(); tie = np.flatnonzero(r <= rmin * (1 + 1e-12))
    return dict(mid=float(PGRID[tie[len(tie) // 2]]), max=float(PGRID[tie[-1]]), min=float(PGRID[tie[0]]), n_tied=len(tie), r_train=float(rmin))


def lam_bar(Ltrain, cc):
    """Option 1 of their Sec. 2.3.4: optimal age-replacement cost rate on the empirical training lives."""
    Ls = np.asarray(Ltrain, float); Ts = np.arange(1, int(Ls.max()) + 1)
    return float(min(np.where(Ls > T, 1.0, cc).sum() / np.minimum(Ls, T).sum() for T in Ts))


def p3_flags(model, lam, cc):
    """Per bin: replace now if the minimiser x* of Eq. (14) over x = 0..cap is <= dT."""
    xs = np.arange(0, model['cap'] + 1); fl = []
    for d in model['dists']:
        if not len(d): fl.append(False); continue
        surv = (d[None, :] > xs[:, None]).mean(1); beyond = np.maximum(d[None, :] - xs[:, None], 0).mean(1)
        f = surv * 1.0 + (1 - surv) * cc + lam * beyond; fl.append(bool(xs[int(np.argmin(f))] <= DT))
    return np.array(fl)


def p3_first(model, flags, Gs):
    return {u: ((int(np.argmax(flags[np.searchsorted(model['edges'], g, side='right')])) + 1) * DT
                if flags[np.searchsorted(model['edges'], g, side='right')].any() else np.inf) for u, g in Gs.items()}


# ------------------------------------------------------------------ one split
def run_split(train_u, test_u, inner_seed, boot_seed, protocol, split, feats=FEATS):
    train_u = np.sort(train_u); test_u = np.sort(test_u)
    inner = np.array_split(np.random.default_rng(inner_seed).permutation(train_u), 5)
    # E1: disjoint test / training / inner sets
    assert not set(train_u) & set(test_u), 'E1: test units in training set'
    assert sorted(np.concatenate(inner).tolist()) == sorted(train_u.tolist()), 'E1: inner folds do not partition the training units'
    oof = {}
    for iu in inner:
        assert not set(iu) & set(test_u)
        p = fit_models(np.setdiff1d(train_u, iu), iu, feats)
        for c in p: oof.setdefault(c, {}).update(p[c])
    fin = fit_models(train_u, test_u, feats)
    Loof = np.array([y[0] + 1 for _, y in oof[W.CAPS[0]].values()]); Lte = {u: y[0] + 1 for u, (_, y) in fin[W.CAPS[0]].items()}
    TF = np.array([Lte[u] for u in test_u], float); wts = boot_weights(len(Loof), boot_seed)
    rows, sets, bins = [], [], []
    series = dict(test_u=test_u, TF=TF, sel={})

    # ---- window-tuned STW: settings per H by the window count (recipe unchanged)
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

    def ttab(src, keys, thr, sign=1.0):
        return {key: (R.alarm_table({u: (sign * W.smooth(p, key[-2]), y) for u, (p, y) in oof[src(key)].items()}, key[-1], thr),
                      R.alarm_table({u: (sign * W.smooth(p, key[-2]), y) for u, (p, y) in fin[src(key)].items()}, key[-1], thr)) for key in keys}
    STW = ttab(lambda key: key[0], [(c, sp, k) for c in W.CAPS for sp in W.SPANS for k in W.KS], R.TAUS)
    hv = np.concatenate([s[y <= 80] for s, y in oof['HI'].values()]); THETA = np.unique(np.quantile(hv, np.linspace(0.02, 0.995, 120)))
    HIT = ttab(lambda key: 'HI', [('h', sp, k) for sp in W.SPANS for k in W.KS], -THETA, sign=-1.0)

    # ---- probability models (training OOF only)
    cal = cls_calibrator(oof['CLS'])
    Gcls_oof, Loof_d = grid_series({u: (cal.predict(s), y) for u, (s, y) in oof['CLS'].items()})
    Gcls_te, _ = grid_series({u: (cal.predict(s), y) for u, (s, y) in fin['CLS'].items()})
    RES = {cap: res_model(oof[cap], cap) for cap in (CAP_RES, CAP_SENS)}
    for cap, m in RES.items():
        for d in m['diag']: bins.append(dict(protocol=protocol, split=split, cap=cap, n_bins=len(m['diag']), **d))
    Gres_oof, _ = grid_series({u: (res_prob(RES[CAP_RES], s), y) for u, (s, y) in oof[CAP_RES].items()})
    Gres_te, _ = grid_series({u: (res_prob(RES[CAP_RES], s), y) for u, (s, y) in fin[CAP_RES].items()})
    Graw_te = {cap: grid_series(fin[cap])[0] for cap in (CAP_RES, CAP_SENS)}
    series.update(Gcls_oof=Gcls_oof, Gcls_te=Gcls_te, Gres_oof=Gres_oof, Gres_te=Gres_te, Loof=Loof_d)

    def emit(policy, q, TRd, setting, mapped=True):
        TR = np.array([TRd[u] for u in test_u], float); C, T = K.lifecycle(TR, TF, 1.0, 1.0 / q)
        for i, u in enumerate(test_u):
            rows.append(dict(protocol=protocol, split=split, q=q, policy=policy, unit=int(u), cost=C[i], tlc=T[i], TF=TF[i], TR=TR[i], fail=bool(C[i] != 1.0), mapped=mapped, setting=setting))

    def emit_tab(policy, q, tab, j, setting, mapped=True):
        U, ok, ya, ta, L = tab
        if mapped:
            _, _, prev, _ = grid_cost(ok[:, j], ta[:, j], L, 1.0 / q); g = np.where(ok[:, j], np.ceil(np.nan_to_num(ta[:, j]) / DT) * DT, np.inf)
            TRd = {u: (g[i] if g[i] >= DT else DT) if ok[i, j] else np.inf for i, u in enumerate(U)}
        else:
            TRd = {u: (ta[i, j] if ok[i, j] else np.inf) for i, u in enumerate(U)}
        emit(policy, q, TRd, setting, mapped)

    Ltr_lives = Loof
    for q in QS:
        cc = 1.0 / q; rho = cc
        # STW window-tuned: H by the grid-mapped training cost
        Hg = min(R.HS, key=lambda H: (lambda c, u: c.sum() / u.sum())(*grid_cost(WIN[H][0][1][:, 0], WIN[H][0][3][:, 0], WIN[H][0][4], cc)[:2]))
        emit_tab('STW_window', q, WIN[Hg][1], 0, f'H={Hg}|{stw_sel[Hg]}')
        for name, rule in (('STW_cost', 'plain'), ('STW_cost_1se', '1se')):
            key, j = select_grid(STW, cc, rule, wts); emit_tab(name, q, STW[key][1], j, f'{key}|tau={R.TAUS[j]}')
            series['sel'][(name, q)] = (key, j, STW[key][0], STW[key][1])     # training OOF and test alarm tables, all thresholds
        key, j = select_grid(HIT, cc, 'plain', wts); emit_tab('HI_cost', q, HIT[key][1], j, f'{key}|{j}')
        # unmapped 1-cycle versions (selected under the 1-cycle objective, lead 0)
        H1 = min(R.HS, key=lambda H: (lambda c, u, _: c.sum() / u.sum())(*R.cost_of(*WIN[H][0][1:], 0, rho)))
        emit_tab('STW_window_unmapped', q, WIN[H1][1], 0, f'H={H1}', mapped=False)
        for name, rule in (('STW_cost_unmapped', 'plain'), ('STW_cost_1se_unmapped', '1se')):
            key, j = select_1cycle(STW, rho, rule, wts); emit_tab(name, q, STW[key][1], j, f'{key}|tau={R.TAUS[j]}', mapped=False)
        # their policy 1 on my models
        for tag, Go, Gt in (('cls', Gcls_oof, Gcls_te), ('res', Gres_oof, Gres_te)):
            emit(f'P1_{tag}_q', q, p1_first(Gt, q), f'p={q}')
            o = p1_optimise(Go, Loof_d, cc)
            for rule in ('mid', 'max'): emit(f'P1_{tag}_opt_{rule}', q, p1_first(Gt, o[rule]), f'p={o[rule]}')
            sets.append(dict(protocol=protocol, split=split, q=q, model=tag, p_mid=o['mid'], p_max=o['max'], p_min=o['min'], n_tied=o['n_tied'], r_train=o['r_train']))
        # their policy 3 with the P-res distribution (cap 60 primary, 125 sensitivity)
        lam = lam_bar(Ltr_lives, cc)
        for cap in (CAP_RES, CAP_SENS):
            fl = p3_flags(RES[cap], lam, cc); emit(f'P3_res{cap}', q, p3_first(RES[cap], fl, Graw_te[cap]), f'lam={lam:.6g}|bins_replace={int(fl.sum())}/{len(fl)}')
        # age replacement on the grid, perfect, run-to-failure
        Ts = np.arange(DT, Ltr_lives.max() + DT, DT)
        cr = [np.where(Ltr_lives > T, 1.0, cc).sum() / np.minimum(Ltr_lives, T).sum() for T in Ts]; Ta = Ts[int(np.argmin(cr))]
        emit('age_grid', q, {u: Ta for u in test_u}, f'T={Ta}')
        emit('perfect_grid', q, dict(zip(test_u, K.perfect_tr(TF, DT))), '')
        emit('run_to_failure', q, {u: np.inf for u in test_u}, '')
        sets.append(dict(protocol=protocol, split=split, q=q, model='STW_window', p_mid=np.nan, p_max=np.nan, p_min=np.nan, n_tied=np.nan, r_train=np.nan, H_grid=Hg, H_1cycle=H1, age_T=Ta, lam=lam))
    return rows, sets, bins, series


def check_split(rows):
    """Stop rule: no grid-mapped policy may have M < 0 on the test units of a split."""
    D = pd.DataFrame(rows)
    for (q, pol), g in D[D.mapped].groupby(['q', 'policy']):
        M = K.m_hat(g['cost'].values, g['tlc'].values, g['TF'].values, DT, 1.0, 1.0 / q, f'{pol} q={q} split={g.split.iloc[0]}')
        if M < -K.TOL: raise SystemExit(f'STOP: grid-mapped policy {pol} has M = {M:.6f} < 0 at q = {q} (split {g.split.iloc[0]})')


def run_protocol(name, splits):
    t0 = time.time(); allr, alls, allb = [], [], []
    for (split, train_u, test_u, inner_seed, boot_seed) in splits:
        ck = f'{OUT}/ckpt/{TAG}_{name}_{split}.pkl'
        if os.path.exists(ck): r, s, b = pickle.load(open(ck, 'rb'))
        else:
            r, s, b, ser = run_split(train_u, test_u, inner_seed, boot_seed, name, split); check_split(r)
            pickle.dump(ser, open(ck.replace('.pkl', '_series.pkl') + '.tmp', 'wb')); os.replace(ck.replace('.pkl', '_series.pkl') + '.tmp', ck.replace('.pkl', '_series.pkl'))
            pickle.dump((r, s, b), open(ck + '.tmp', 'wb')); os.replace(ck + '.tmp', ck)
        allr += r; alls += s; allb += b; print(f'{name} split {split} done ({time.time() - t0:.0f}s)', flush=True)
    return pd.DataFrame(allr), pd.DataFrame(alls), pd.DataFrame(allb)


def cv_splits():
    out = []
    for fold, test_u in enumerate(outer_folds(UNITS), 1):
        out.append((fold, np.setdiff1d(UNITS, test_u), test_u, 100 + fold, 2026 + fold))
    return out


def random_splits(s0=1, s1=30):
    out = []
    for s in range(s0, s1 + 1):
        perm = np.random.default_rng(31000 + s).permutation(np.sort(UNITS)); out.append((s, np.sort(perm[20:]), np.sort(perm[:20]), 3100 + s, 2026 + s))
    return out


def write(name, D, S, Bn):
    D.to_csv(f'{OUT}/{TAG}_{name}_units.csv', index=False); S.to_csv(f'{OUT}/{TAG}_{name}_settings.csv', index=False); Bn.to_csv(f'{OUT}/{TAG}_{name}_bins.csv', index=False)


# ------------------------------------------------------------------ leakage checks E2-E4 (fold 1 of protocol B)
def leak():
    lines = []; fold, train_u, test_u, isd, bsd = cv_splits()[0]
    tr, _, _ = load_dataset(DS); st, keep = regime_stats(tr[tr.unit.isin(train_u)])
    F, Y = FEATS(train_u, np.concatenate([train_u, test_u]))
    X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u])
    reg = W.gbm(X, y, CAP_RES); cls = classifier().fit(X, (y <= DT).astype(int))
    # E2 causality
    rng = np.random.default_rng(0); md = 0.0
    for u in test_u[:15]:
        g = tr[tr.unit == u]; Z = causal_feats(zmat(g, st, keep)); fr, fc = reg.predict(Z), cls.predict_proba(Z)[:, 1]
        assert np.allclose(Z, F[u]), 'feature construction differs from the adapter'
        for t in rng.integers(5, len(g), 6):
            Zp = causal_feats(zmat(g.iloc[:t], st, keep))
            md = max(md, abs(reg.predict(Zp)[-1] - fr[t - 1]), abs(cls.predict_proba(Zp)[-1, 1] - fc[t - 1]))
    lines.append((f'E2 causality (regressor cap 60 and classifier): max |prefix - full| = {md:.2e} over 90 checks', md < 1e-9))
    # E3 negative control: classifier trained on labels from lives permuted across training units; policy 1 with p = c_p/c_c
    lives = tr.groupby('unit').cycle.max(); perm = dict(zip(train_u, np.random.default_rng(0).permutation(lives[train_u].values)))
    yp = np.concatenate([np.maximum(perm[u] - np.arange(1, len(Y[u]) + 1), 0) for u in train_u])
    TF = np.array([Y[u][0] + 1 for u in test_u], float); q = Q_PRIMARY; Ms = {}
    for tag, lab in (('real', y), ('permuted', yp)):
        c = classifier().fit(X, (lab <= DT).astype(int)); G, _ = grid_series({u: (c.predict_proba(F[u])[:-1, 1], Y[u][:-1]) for u in test_u})
        TRd = p1_first(G, q); C, T = K.lifecycle(np.array([TRd[u] for u in test_u], float), TF, 1.0, 1 / q); Ms[tag] = K.m_hat(C, T, TF, DT, 1.0, 1 / q, 'E3')
    lines.append((f'E3 permuted-life labels: policy 1 (classifier, p = 0.1) M = {100 * Ms["permuted"]:.1f}% vs real labels {100 * Ms["real"]:.1f}%', Ms['permuted'] > Ms['real']))
    # E4 rerun of fold 1 reproduces every decision
    ck = f'{OUT}/ckpt/{TAG}_cv_1.pkl'
    if os.path.exists(ck):
        r1 = pd.DataFrame(pickle.load(open(ck, 'rb'))[0]); r2 = pd.DataFrame(run_split(train_u, test_u, isd, bsd, 'cv', 1)[0])
        same = r1[['q', 'policy', 'unit', 'TR', 'cost', 'tlc']].equals(r2[['q', 'policy', 'unit', 'TR', 'cost', 'tlc']])
        lines.append(('E4 rerun of fold 1 reproduces every decision of every policy and cost ratio', same))
    else:
        lines.append(('E4 not run: fold 1 checkpoint missing', False))
    txt = '\n'.join(f'{"PASS" if ok else "FAIL"}  {s}' for s, ok in lines); open(f'{OUT}/{TAG}_leakage.txt', 'w').write(txt + '\n'); print(txt)
    if not all(ok for _, ok in lines): raise SystemExit('STOP: leakage check failed')


if __name__ == '__main__':
    mode = ARGS[0] if ARGS else 'cv'
    if mode == 'cv':
        D, S, Bn = run_protocol('cv', cv_splits()); write('cv', D, S, Bn)
    elif mode == 'splits':
        s0, s1 = (int(ARGS[1]), int(ARGS[2])) if len(ARGS) > 2 else (1, 30)
        D, S, Bn = run_protocol('rs', random_splits(s0, s1)); write(f'rs_{s0}_{s1}', D, S, Bn)
    elif mode == 'leak':
        leak()
