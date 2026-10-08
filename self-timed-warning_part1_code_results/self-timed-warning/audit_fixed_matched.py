"""Fixed-time versus self-timed comparison on PHM08 with MATCHED training data and calibration (post hoc; exploratory).

Every variant below uses the same outer folds (seed 2026) and the same cross-fitting: inner five-fold out-of-fold (OOF)
predictions of the outer training engines (seed 100 + fold; normalisation statistics from each inner training subset) are
used for every calibration or selection step, and the final model is then refitted on ALL outer training engines.
Outer test engines never enter fitting, calibration or selection.
  fixed_f{50,90}   fixed-time gradient-boosted trees (safe_methods.GBM: no target cap, features of the seven temperature
                   and speed sensors) scored at 50 % / 90 % of each test engine's life, t = floor(f L); a shift chosen on
                   the OOF errors of the training engines at the same fraction (grid -30 ... +30, step 0.5)
  fixed_r20        the same model scored at the cycle with exactly 20 true cycles left (oracle observation time),
                   shift chosen on OOF errors at r = 20
  fixed_trigger    the same model with the self-timed trigger (H = 20; span, debounce and shift chosen on OOF alarms;
                   shift grid -20 ... +10): alarm timing added, target and features unchanged
  recipe_f90       the recipe's regressor (capped target, recipe features) at 90 % of life; cap and shift chosen on OOF
  recipe_r20       the recipe's regressor at r = 20 (oracle observation time); cap and shift chosen on OOF at r = 20
  recipe_self      the recipe (self-timed, H = 20), selection exactly as eol_window2.py: must reproduce the main result
The fit-on-75 % / calibrate-on-25 % comparison of the earlier analysis is added from frozen outputs:
  fixed_f90_7525   fixed-time GBM at 90 % of life, shift on the calibration engines (audit_fixed_time.py)
  recipe_self_7525 the recipe fitted on the same 75 % and tuned on the same 25 % (identical-protocol comparison, h2h.py)
Output: out/audit/fixed_matched.json, out/audit/fixed_matched_units.csv
"""
import os, sys, json, numpy as np, pandas as pd
DS = 'PHM08'                                    # Phase 4d: --ds FD004 runs the cross-fitted variants on a second dataset
if '--ds' in sys.argv: DS = sys.argv[sys.argv.index('--ds') + 1]
sys.argv = sys.argv[:1]                        # eol_window2 reads sys.argv[2] as warning levels
SUF = '' if DS == 'PHM08' else f'_{DS}'
from scipy.stats import binomtest, beta
import eol_window2 as W
import rev_experiments as R
import audit_confirmations as AC
from safe_common import load_dataset, outer_folds, regime_norm, engines
from fixed_gbm import GBM

OUT = 'out/audit'; LO, HI = -13, 2
SH_FIX = np.arange(-30, 30.01, 0.5); SH_TRIG = np.arange(-20, 10.01, 0.5)


def cp(k, n):
    return [round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0]


def best_shift(e, grid):
    cnt = np.array([((e + s >= LO) & (e + s <= HI)).sum() for s in grid]) - 1e-3 * np.abs(grid); return float(grid[int(np.argmax(cnt))])


def at_time(P, when):
    """P: {u: (pred per cycle, rul per cycle)} -> {u: (pred, rul)} at the chosen cycle (index t-1)"""
    out = {}
    for u, (p, y) in P.items():
        L = int(y[0]) + 1
        t = int(np.floor(when * L)) if when < 1 else int(L - when)          # fraction of life, or cycle with `when` cycles left
        out[u] = (p[t - 1], y[t - 1])
    return out


tr, _, _ = load_dataset(DS); units = np.sort(tr.unit.unique()); _, feats = R.adapter(DS)
rows, sel = [], []
for fold, test_u in enumerate(outer_folds(units), 1):
    train_u = np.setdiff1d(units, test_u); inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5)

    def fixed_fit(fit_u, tgt):
        E = engines(tr, regime_norm(tr[tr.unit.isin(fit_u)])); m = GBM().fit({u: E[u] for u in fit_u})
        return {u: (m.predict(E[u][0], E[u][1])[:-1], E[u][2][:-1].astype(float)) for u in tgt}
    oof_fix, oof_rec = {}, {c: {} for c in W.CAPS}
    for iu in inner:
        itr = np.setdiff1d(train_u, iu); oof_fix.update(fixed_fit(itr, iu))
        p = R.models(feats, itr, iu)
        for c in W.CAPS: oof_rec[c].update(p[c])
    fin_fix = fixed_fit(train_u, test_u); fin_rec = R.models(feats, train_u, test_u)
    res = {}
    # fixed-time model at fixed observation times
    for name, when in (('fixed_f50', 0.5), ('fixed_f90', 0.9), ('fixed_r20', 20)):
        o = at_time(oof_fix, when); s = best_shift(np.array([p - y for p, y in o.values()]), SH_FIX)
        res[name] = {u: (p + s, y) for u, (p, y) in at_time(fin_fix, when).items()}; sel.append(dict(fold=fold, variant=name, shift=s))
    # recipe regressor at fixed observation times (cap and shift on OOF)
    for name, when in (('recipe_f90', 0.9), ('recipe_r20', 20)):
        best = None
        for c in W.CAPS:
            e = np.array([p - y for p, y in at_time(oof_rec[c], when).values()]); s = best_shift(e, SH_FIX)
            n = (((e + s) >= LO) & ((e + s) <= HI)).sum()
            if best is None or n > best[0]: best = (n, c, s)
        _, c, s = best; res[name] = {u: (p + s, y) for u, (p, y) in at_time(fin_rec[c], when).items()}; sel.append(dict(fold=fold, variant=name, cap=c, shift=s))
    # fixed-time model with the self-timed trigger
    best = None
    for sp in W.SPANS:
        Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof_fix.items()}
        for k in W.KS:
            tot = AC.in_counts_g(Po, 20, k, LO, HI, SH_TRIG) - 0.001 * np.abs(SH_TRIG); j = int(np.argmax(tot))
            if best is None or tot[j] > best[0]: best = (tot[j], sp, k, SH_TRIG[j])
    _, sp, k, s = best; Rt = AC.evaluate_g({u: (W.smooth(p, sp), y) for u, (p, y) in fin_fix.items()}, 20, k, s, LO, HI)
    res['fixed_trigger'] = {r.unit: (r.pred, r.y) for r in Rt.itertuples()}; sel.append(dict(fold=fold, variant='fixed_trigger', span=sp, k=k, shift=s))
    # recipe, self-timed (as eol_window2.py)
    best = None
    for c in W.CAPS:
        if c < 40: continue
        for sp in W.SPANS:
            Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof_rec[c].items()}
            for k in W.KS:
                tot = W.in_counts(Po, 20, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                if best is None or tot[j] > best[0]: best = (tot[j], c, sp, k, W.SHIFTS[j])
    _, c, sp, k, s = best; Rs = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in fin_rec[c].items()}, 20, k, s)
    res['recipe_self'] = {r.unit: (r.pred, r.y) for r in Rs.itertuples()}; sel.append(dict(fold=fold, variant='recipe_self', cap=c, span=sp, k=k, shift=s))
    for name, d in res.items():
        for u, (p, y) in d.items():
            e = p - y if np.isfinite(p) else np.nan
            rows.append(dict(fold=fold, variant=name, unit=u, pred=p, y=y, IN=bool(np.isfinite(e) and LO <= e <= HI), missed=not np.isfinite(p)))
    print('fold', fold, 'done', flush=True)

U = pd.DataFrame(rows)
# frozen 75 / 25 comparison (PHM08 only)
if DS == 'PHM08':
  cut = pd.read_csv('results/safe/v2_cut_predictions.csv'); cut = cut[(cut.dataset == 'PHM08') & (cut.role == 'test') & (cut.method == 'gbm') & np.isclose(cut.frac, 0.9)].copy(); cut['fold'] = cut.fold.astype(int)
  base = pd.read_csv('results/window/base_preds_PHM08.csv'); cal = base[(base.role == 'cal') & np.isclose(base.stage, 0.9)]
  for fold, g in cut.groupby('fold'):
      s = best_shift((cal[cal.fold == fold].gbm - cal[cal.fold == fold].y).values, SH_FIX)
      for r in g.itertuples():
          e = r.point + s - r.true_rul; rows.append(dict(fold=fold, variant='fixed_f90_7525', unit=r.unit, pred=r.point + s, y=r.true_rul, IN=bool(LO <= e <= HI), missed=False))
  h = pd.read_csv('results/window/h2h_PHM08.csv'); h = h[(h.method == 'ours') & (h.H == 20)]
  for r in h.itertuples(): rows.append(dict(fold=r.fold, variant='recipe_self_7525', unit=r.unit, pred=r.pred, y=r.y, IN=r.cls == 'IN', missed=r.cls == 'MISSED'))
U = pd.DataFrame(rows); U.to_csv(f'{OUT}/fixed_matched_units{SUF}.csv', index=False)

P = U.pivot_table(index='unit', columns='variant', values='IN', aggfunc='first').astype(bool)
out = {'variants': {}, 'paired': {}, 'selection': sel}
for v in P.columns:
    k = int(P[v].sum()); n = int(P[v].notna().sum()); out['variants'][v] = dict(IN=k, n=n, pct=round(100 * k / n, 1), ci=cp(k, n))
pairs = [('fixed_trigger', 'fixed_f90'), ('recipe_f90', 'fixed_f90'), ('recipe_self', 'fixed_trigger'), ('recipe_self', 'recipe_f90'), ('recipe_self', 'fixed_f90'),
         ('recipe_r20', 'fixed_r20'), ('recipe_self', 'recipe_r20'), ('fixed_trigger', 'fixed_r20'), ('recipe_self_7525', 'fixed_f90_7525'), ('fixed_f90', 'fixed_f90_7525'), ('recipe_self', 'recipe_self_7525')]
pairs = [(a, b) for a, b in pairs if a in P.columns and b in P.columns]
for a, b in pairs:
    x = int((P[a] & ~P[b]).sum()); y = int((~P[a] & P[b]).sum())
    out['paired'][f'{a}|{b}'] = dict(only_a=x, only_b=y, p=float(binomtest(min(x, y), x + y, .5).pvalue) if x + y else 1.0)
main = pd.read_csv(f'results/window/first_warning_v2_{DS}.csv'); main = main[main.H == 20].set_index('unit').cls == 'IN'
out['recipe_self_reproduces_main'] = bool((P['recipe_self'].reindex(main.index) == main).all())
# lead time (true cycles left) at the alarm for the self-timed variants
for v in ('fixed_trigger', 'recipe_self'):
    g = U[(U.variant == v) & ~U.missed]; out['variants'][v].update(median_left=float(g.y.median()), left_p05=float(g.y.quantile(.05)), left_p95=float(g.y.quantile(.95)), missed=int(U[(U.variant == v)].missed.sum()))
json.dump(out, open(f'{OUT}/fixed_matched{SUF}.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'selection'}, indent=1))
