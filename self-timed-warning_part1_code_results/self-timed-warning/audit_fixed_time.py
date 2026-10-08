"""Decomposition of the fixed-time versus self-timed contrast on PHM08 (post hoc, exploratory; no model is refitted).

The half-life comparison of the manuscript mixes four things: the horizon of the prediction (how much wear is visible),
the calibration of the estimate to the asymmetric window (a shift), the training target, and the choice of the alarm time.
Using only frozen predictions, this script separates them:
  fixed-time models (age, gbm, lstm, cnn, iohmm; trained on the fit engines of each outer fold, results/safe) scored
    (a) raw at 30, 50, 70 and 90 % of life (as in the manuscript),
    (b) with a shift chosen on the calibration engines of the same fold at the same fraction of life (no test information),
  the self-timed model's own calibrated estimate at the cycle where exactly H true cycles remain (oracle-timed control,
    results/window/oracle_timed_PHM08.csv), and the self-timed first warning (results/window/first_warning_v2_PHM08.csv).
Output: out/audit/fixed_time.json
"""
import json, numpy as np, pandas as pd
from scipy.stats import beta, binomtest

LO, HI = -13, 2; SH = np.arange(-30, 30.01, 0.5)


def cp(k, n):
    return [round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0]


cut = pd.read_csv('results/safe/v2_cut_predictions.csv'); cut = cut[(cut.dataset == 'PHM08') & (cut.role == 'test')].copy(); cut['fold'] = cut.fold.astype(int)
base = pd.read_csv('results/window/base_preds_PHM08.csv'); cal = base[base.role == 'cal']
out = {'fixed': {}}
for m in ['age', 'gbm', 'lstm', 'cnn', 'iohmm']:
    for f in [0.3, 0.5, 0.7, 0.9]:
        T = cut[(cut.method == m) & (np.isclose(cut.frac, f))].copy(); T['e'] = T.point - T.true_rul
        hits_cal = []
        for fold, g in T.groupby('fold'):
            c = cal[(cal.fold == fold) & np.isclose(cal.stage, f)]; ec = (c[m] - c.y).values
            cnt = np.array([((ec + s >= LO) & (ec + s <= HI)).sum() for s in SH]) - 1e-3 * np.abs(SH); s = SH[int(np.argmax(cnt))]
            hits_cal += list(((g.e + s >= LO) & (g.e + s <= HI)).values)
        raw = ((T.e >= LO) & (T.e <= HI)); k, kc, n = int(raw.sum()), int(np.sum(hits_cal)), len(T)
        out['fixed'][f'{m}|{f}'] = dict(n=n, raw_IN=k, raw_pct=round(100 * k / n, 1), cal_IN=kc, cal_pct=round(100 * kc / n, 1), cal_ci=cp(kc, n),
                                        median_rul=float(T.true_rul.median()), rul_p05=float(T.true_rul.quantile(.05)), rul_p95=float(T.true_rul.quantile(.95)),
                                        mae=round(float(T.e.abs().mean()), 1))
o = pd.read_csv('results/window/oracle_timed_PHM08.csv'); w = pd.read_csv('results/window/first_warning_v2_PHM08.csv')
for H in (10, 20):
    oo = o[o.H == H]; k = int((oo.cls == 'IN').sum()); out[f'oracle|{H}'] = dict(IN=k, n=len(oo), pct=round(100 * k / len(oo), 1), ci=cp(k, len(oo)))
    ww = w[w.H == H] if 'H' in w else w; k = int((ww.cls == 'IN').sum()); out[f'self|{H}'] = dict(IN=k, n=len(ww), pct=round(100 * k / len(ww), 1), ci=cp(k, len(ww)),
                                                                                                 median_rul=float(ww.y.median()))
# paired comparison: calibrated fixed-time GBM at 90 % of life against the self-timed warning (same engines)
T = cut[(cut.method == 'gbm') & np.isclose(cut.frac, 0.9)].copy(); T['e'] = T.point - T.true_rul; hit = {}
for fold, g in T.groupby('fold'):
    c = cal[(cal.fold == fold) & np.isclose(cal.stage, 0.9)]; ec = (c['gbm'] - c.y).values
    cnt = np.array([((ec + s >= LO) & (ec + s <= HI)).sum() for s in SH]) - 1e-3 * np.abs(SH); s = SH[int(np.argmax(cnt))]
    hit.update(dict(zip(g.unit, ((g.e + s >= LO) & (g.e + s <= HI)).values)))
ws = (w[w.H == 20] if 'H' in w else w).set_index('unit').cls == 'IN'
a = ws.reindex(list(hit)).values.astype(bool); b = np.array(list(hit.values()), bool); x, y = int((a & ~b).sum()), int((~a & b).sum())
out['self20_vs_gbm90cal'] = dict(only_self=x, only_fixed=y, p=float(binomtest(min(x, y), x + y, .5).pvalue))
json.dump(out, open('out/audit/fixed_time.json', 'w'), indent=1)
for k, v in out['fixed'].items(): print(k, v['raw_pct'], v['cal_pct'], v['median_rul'], v['mae'])
print({k: v for k, v in out.items() if k != 'fixed'})
