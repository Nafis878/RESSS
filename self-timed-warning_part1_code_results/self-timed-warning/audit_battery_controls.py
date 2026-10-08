"""Battery row of the timing-control table (constant-estimate control, health-indicator threshold alarm) rerun with the
training-only block length of audit_confirmations.py. Identical to rev_experiments.run (R0, R1, R2) except that the block
length kappa is computed from the training cells of each outer fold and the per-cycle data are forward-filled only.
Output: out/audit/battery_controls.csv (per test cell, method, H; same columns as out/rev/<ds>_window.csv plus kappa)
"""
import os, pickle, numpy as np, pandas as pd
import eol_window2 as W
import rev_experiments as R
import audit_confirmations as AC
import battery_warning as BW
from safe_common import outer_folds

OUT = 'out/audit'; os.makedirs(OUT + '/ckpt', exist_ok=True)
S, Lc = AC.battery_cycles(); units = np.sort(Lc.index.values); rows = []
for fold, test_u in enumerate(outer_folds(units), 1):
    ck = f'{OUT}/ckpt/battery_controls_fold{fold}.pkl'
    if os.path.exists(ck): rows += pickle.load(open(ck, 'rb')); continue
    n0 = len(rows); train_u = np.setdiff1d(units, test_u)
    kap = AC.kap_rule(Lc[train_u].values); Bf = AC.battery_blocks(S, kap, Lc, train_u)
    def feats(stat_u, use_u):
        F, Y = BW.features(Bf[Bf.cell.isin(np.concatenate([stat_u, use_u]))], stat_u)
        return {u: F[u] for u in use_u}, {u: Y[u] for u in use_u}
    inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5)
    oof = {c: {} for c in W.CAPS + ['HI']}
    for iu in inner:
        p = R.models(feats, np.setdiff1d(train_u, iu), iu)
        for c in oof: oof[c].update(p[c])
    fin = R.models(feats, train_u, test_u)
    hv = np.concatenate([s[y <= 80] for s, y in oof['HI'].values()]); THETA = np.unique(np.quantile(hv, np.linspace(0.02, 0.995, 120)))
    for H in R.HS:
        best = None
        for cap in W.CAPS:
            if cap < H + 20: continue
            for sp in W.SPANS:
                Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
                for k in W.KS:
                    tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                    if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
        _, cap, sp, k, s = best
        Rt = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in fin[cap].items()}, H, k, s)
        Ro = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}, H, k, s); ow = Ro.dropna(subset=['pred'])
        cnt = np.array([(((c - ow.y) >= R.LO) & ((c - ow.y) <= R.HI_)).sum() for c in R.CGRID]) - 1e-3 * np.abs(R.CGRID - ow.pred.median())
        c = R.CGRID[int(np.argmax(cnt))]
        for _, r in Rt.iterrows():
            rows.append(dict(fold=fold, kappa=kap, H=H, method='STW', unit=r.unit, pred=r.pred, y=r.y, cycle=r.cycle, cls=r.cls))
            pc = np.nan if np.isnan(r.pred) else c
            rows.append(dict(fold=fold, kappa=kap, H=H, method='STW_const', unit=r.unit, pred=pc, y=r.y, cycle=r.cycle, cls=R.cls_of(np.array([pc]), np.array([r.y]))[0]))
    HItab = {}
    for sp in W.SPANS:
        Po = {u: (-W.smooth(s, sp), y) for u, (s, y) in oof['HI'].items()}; Pt = {u: (-W.smooth(s, sp), y) for u, (s, y) in fin['HI'].items()}
        for k in W.KS: HItab[(sp, k)] = (R.alarm_table(Po, k, -THETA), R.alarm_table(Pt, k, -THETA))
    for H in R.HS:
        cg = np.arange(H - 6, H + 0.01, 0.5); best = None
        for (sp, k), ((U, ok, ya, ta, L), _) in HItab.items():
            d = cg[None, None, :] - ya[:, :, None]; n = (ok[:, :, None] & (d >= R.LO) & (d <= R.HI_)).sum(0)
            j = np.unravel_index(int(np.argmax(n)), n.shape)
            if best is None or n[j] > best[0]: best = (n[j], sp, k, j[0], cg[j[1]])
        _, sp, k, ti, c = best; U, ok, ya, ta, L = HItab[(sp, k)][1]
        for ui, u in enumerate(U):
            pc = c if ok[ui, ti] else np.nan
            rows.append(dict(fold=fold, kappa=kap, H=H, method='HI_threshold', unit=u, pred=pc, y=ya[ui, ti], cycle=ta[ui, ti], cls=R.cls_of(np.array([pc]), np.array([ya[ui, ti]]))[0]))
    pickle.dump(rows[n0:], open(ck + '.tmp', 'wb')); os.replace(ck + '.tmp', ck); print(f'battery controls fold {fold} kappa {kap}', flush=True)
pd.DataFrame(rows).to_csv(f'{OUT}/battery_controls.csv', index=False)
