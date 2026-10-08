"""Calibrated health-indicator alarm (post hoc, exploratory; plan fixed and hashed before the run: kam/PHASE3_4_PLAN.md, 4b).

The linear health indicator of the health-indicator threshold alarm (rev_experiments.models: ridge fit separating the first 30
from the last 5 cycles of each training unit, on the first feature block) is mapped to cycles by an isotonic, decreasing
regression of min(r, c) on the indicator value, fitted on the pooled inner out-of-fold values of the training units, for
each cap c in {40, 60, 90}. The mapped series goes through the recipe's trigger with the recipe's grids and selection rule
(caps c >= H + 20, spans, debounces, shifts; most correct out-of-fold first warnings, ties to the smaller |s|), for every
H in {10, 15, 20, 30, 40}. The indicator is refitted on all outer training units for the test units; test units are scored
once. Outer folds seed 2026, inner seed 100 + fold, as rev_experiments.py.

Check R4b: the uncalibrated indicator, put through the selection of the existing health-indicator threshold alarm, must
reproduce the per-unit outcomes of results/rev/<ds>_window.csv (method HI_threshold).
Output: out/audit/hi_calibrated_<ds>.csv (fold, H, method, unit, pred, y, cycle, cls), out/audit/hi_calibrated_check.txt
Usage: python audit_hi_calibrated.py PHM08 FD001 FD002 FD003 FD004 NCMAPSS6
"""
import os, sys, time
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
import numpy as np, pandas as pd
from sklearn.isotonic import IsotonicRegression
import eol_window2 as W
import rev_experiments as R
from safe_common import outer_folds

OUT = 'out/audit'; os.makedirs(OUT, exist_ok=True)


def hi_models(feats, train_u, target_u):
    """the health indicator of rev_experiments.models, without the regressors"""
    F, Y = feats(train_u, np.unique(np.concatenate([train_u, target_u])))
    X = np.vstack([F[u] for u in train_u]); p = (X.shape[1] - 1) // 5
    rows = [(F[u][:, :p], Y[u]) for u in train_u]
    Xh = np.vstack([np.vstack([f[:30], f[r <= 5]]) for f, r in rows])
    yh = np.concatenate([np.concatenate([np.zeros(min(30, len(f))), np.ones((r <= 5).sum())]) for f, r in rows])
    A = np.column_stack([Xh, np.ones(len(Xh))]); w = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ yh)
    return {u: (F[u][:-1, :p] @ w[:-1] + w[-1], Y[u][:-1]) for u in target_u}


def run(ds):
    t0 = time.time(); units, feats = R.adapter(ds); rows = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        train_u = np.setdiff1d(units, test_u)
        inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5); oof = {}
        for iu in inner:
            assert not set(iu) & set(test_u)
            oof.update(hi_models(feats, np.setdiff1d(train_u, iu), iu))
        fin = hi_models(feats, train_u, test_u)
        # (a) uncalibrated indicator with the selection of the existing HI threshold alarm (check R4b)
        hv = np.concatenate([s[y <= 80] for s, y in oof.values()]); THETA = np.unique(np.quantile(hv, np.linspace(0.02, 0.995, 120)))
        tab = {(sp, k): (R.alarm_table({u: (-W.smooth(s, sp), y) for u, (s, y) in oof.items()}, k, -THETA),
                         R.alarm_table({u: (-W.smooth(s, sp), y) for u, (s, y) in fin.items()}, k, -THETA)) for sp in W.SPANS for k in W.KS}
        for H in R.HS:
            cg = np.arange(H - 6, H + 0.01, 0.5); best = None
            for (sp, k), ((U, ok, ya, ta, L), _) in tab.items():
                d = cg[None, None, :] - ya[:, :, None]; n = (ok[:, :, None] & (d >= R.LO) & (d <= R.HI_)).sum(0)
                j = np.unravel_index(int(np.argmax(n)), n.shape)
                if best is None or n[j] > best[0]: best = (n[j], sp, k, j[0], cg[j[1]])
            _, sp, k, ti, c = best; U, ok, ya, ta, L = tab[(sp, k)][1]
            for ui, u in enumerate(U):
                pc = c if ok[ui, ti] else np.nan
                rows.append(dict(fold=fold, H=H, method='HI_threshold', unit=u, pred=pc, y=ya[ui, ti], cycle=ta[ui, ti], cls=R.cls_of(np.array([pc]), np.array([ya[ui, ti]]))[0]))
        # (b) calibrated indicator: isotonic map to min(r, c) on inner out-of-fold values, then the recipe's trigger
        hs = np.concatenate([s for s, _ in oof.values()]); rs = np.concatenate([y for _, y in oof.values()])
        iso = {c: IsotonicRegression(increasing=False, out_of_bounds='clip').fit(hs, np.minimum(rs, c)) for c in W.CAPS}
        Co = {c: {u: (iso[c].predict(s), y) for u, (s, y) in oof.items()} for c in W.CAPS}
        Ct = {c: {u: (iso[c].predict(s), y) for u, (s, y) in fin.items()} for c in W.CAPS}
        for H in R.HS:
            best = None
            for cap in W.CAPS:
                if cap < H + 20: continue
                for sp in W.SPANS:
                    Po = {u: (W.smooth(p, sp), y) for u, (p, y) in Co[cap].items()}
                    for k in W.KS:
                        tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                        if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
            _, cap, sp, k, s = best
            Rt = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in Ct[cap].items()}, H, k, s)
            for r in Rt.itertuples():
                rows.append(dict(fold=fold, H=H, method='HI_calibrated', unit=r.unit, pred=r.pred, y=r.y, cycle=r.cycle, cls=r.cls, cap=cap, span=sp, k=k, shift=s))
        print(f'{ds} fold {fold} done ({time.time() - t0:.0f}s)', flush=True)
    D = pd.DataFrame(rows); D.to_csv(f'{OUT}/hi_calibrated_{ds}.csv', index=False)
    ref = pd.read_csv(f'results/rev/{ds}_window.csv'); ref = ref[ref.method == 'HI_threshold'].set_index(['H', 'unit']).cls
    mine = D[D.method == 'HI_threshold'].set_index(['H', 'unit']).cls.reindex(ref.index)
    ok = bool((mine == ref).all())
    line = f'{"PASS" if ok else "FAIL"}  R4b {ds}: uncalibrated indicator reproduces the HI threshold alarm of results/rev ({int((ref == "IN").sum())} in-window over all H; identical per unit: {ok})'
    print(line, flush=True); return line


if __name__ == '__main__':
    lines = [run(ds) for ds in ARGS]
    open(f'{OUT}/hi_calibrated_check.txt', 'w').write('\n'.join(lines) + '\n')
