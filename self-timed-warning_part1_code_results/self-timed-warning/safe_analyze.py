"""Cautious layer + metrics for every (dataset, method). Reads out/safe/preds_*.csv, writes out/safe/results_*.csv"""
import glob, sys, numpy as np, pandas as pd
MODE = sys.argv[1] if len(sys.argv) > 1 else 'all'; OUT = 'out/safe/' if MODE == 'all' else 'out/safe/v2_'
from scipy.stats import wilcoxon
from safe_common import CautiousLayer, QGRID, FRACTIONS, classify, clopper_pearson, EARLY_LIM, LATE_LIM

NAMES = {'age': 'Age-only (no sensors)', 'iohmm': 'IOHMM (thesis method, corrected)', 'cnn': 'CNN (Li et al. 2018)',
         'lstm': 'LSTM (Zheng et al. 2017)', 'gbm': 'Gradient-boosted trees (ours)'}
ORDER = ['age', 'iohmm', 'cnn', 'lstm', 'gbm']

def process(path):
    D = pd.read_csv(path); ds, method = path.split('preds_')[1][:-4].split('_'); recs, cal_info = [], []
    for fold, g in D.groupby('fold'):
        c = g[g.role == 'cal']; layer = CautiousLayer().fit(c.point, c.t, c.true_rul, c.unit, c.life); q = layer.calibrate(mode=MODE)
        cal_info.append(dict(dataset=ds, method=method, fold=fold, q_star=q, cal_late=layer.cal_late[layer.q_index], K=layer.K))
        if fold == 'official':
            T = g[g.role == 'official'].copy(); T['frac'] = np.nan
        else:
            T = g[g.role == 'test']; parts = []
            for f in FRACTIONS:
                h = T[T.t == np.maximum(1, np.floor(f * T.life)).astype(int)].copy(); h['frac'] = f; parts.append(h)
            T = pd.concat(parts)
        Qs = layer.quantiles(T.point.values, T.t.values)
        T = T.assign(dataset=ds, method=method, q_star=q, safe=Qs[:, layer.q_index])
        for j, qq in enumerate(QGRID): T[f'q{qq:.2f}'] = Qs[:, j]
        recs.append(T)
    return pd.concat(recs, ignore_index=True), pd.DataFrame(cal_info)

def summarise(R, col='safe'):
    e = R[col] - R.true_rul; n = len(e); k = int((e > LATE_LIM).sum()); lo, hi = clopper_pearson(k, n)
    return dict(n=n, late=k, late_pct=100 * k / n, late_ci_lo=100 * lo, late_ci_hi=100 * hi,
                early_or_ontime_pct=100 * (e <= LATE_LIM).mean(), ontime_pct=100 * ((e >= EARLY_LIM) & (e <= LATE_LIM)).mean(),
                early_pct=100 * (e < EARLY_LIM).mean(), mean_cycles_early=float(-e.mean()), median_cycles_early=float(-e.median()),
                worst_late=float(e.max()), point_MAE=float((R.point - R.true_rul).abs().mean()),
                point_late_pct=100 * float(((R.point - R.true_rul) > LATE_LIM).mean()))

if __name__ == '__main__':
    allR, allC = [], []
    for p in sorted(glob.glob('out/safe/preds_*.csv')):
        R, C = process(p); allR.append(R); allC.append(C)
    R = pd.concat(allR, ignore_index=True); C = pd.concat(allC, ignore_index=True)
    R['method_name'] = R.method.map(NAMES); R.to_csv(OUT + 'cut_predictions.csv', index=False); C.to_csv(OUT + 'calibration.csv', index=False)
    cv = R[R.fold != 'official']
    S = pd.DataFrame([dict(dataset=d, method=m, frac=f, **summarise(g)) for (d, m, f), g in cv.groupby(['dataset', 'method', 'frac'])])
    S_all = pd.DataFrame([dict(dataset=d, method=m, frac='all', **summarise(g)) for (d, m), g in cv.groupby(['dataset', 'method'])])
    S = pd.concat([S, S_all]); S.to_csv(OUT + 'results_cv.csv', index=False)
    O = pd.DataFrame([dict(dataset=d, method=m, **summarise(g)) for (d, m), g in R[R.fold == 'official'].groupby(['dataset', 'method'])])
    O.to_csv(OUT + 'results_official.csv', index=False)
    # trade-off curves (reporting only; q* was fixed on calibration engines)
    rows = []
    for (d, m, f), g in cv.groupby(['dataset', 'method', 'frac']):
        for qq in QGRID:
            e = g[f'q{qq:.2f}'] - g.true_rul
            rows.append(dict(dataset=d, method=m, frac=f, q=qq, late_pct=100 * (e > LATE_LIM).mean(), mean_cycles_early=float(-e.mean())))
    Cu = pd.DataFrame(rows); Cu.to_csv(OUT + 'tradeoff_curves.csv', index=False)
    # wasted life at a matched 4 % late rate (linear interpolation along each curve)
    M = []
    for (d, m, f), g in Cu.groupby(['dataset', 'method', 'frac']):
        g = g.sort_values('q'); x, y = g.late_pct.values, g.mean_cycles_early.values
        M.append(dict(dataset=d, method=m, frac=f, early_at_4pct_late=float(np.interp(4.0, x, y)) if x.min() <= 4 <= x.max() else np.nan))
    pd.DataFrame(M).to_csv(OUT + 'matched_4pct.csv', index=False)
    # paired significance: ours vs each other method, cycles early per engine (same engines, same cut)
    T = []
    for (d, f), g in cv.groupby(['dataset', 'frac']):
        W = g.pivot_table(index='unit', columns='method', values='safe') .sub(g.groupby('unit').true_rul.first(), axis=0)
        L = g.assign(late=(g.safe - g.true_rul) > LATE_LIM).pivot_table(index='unit', columns='method', values='late')
        for m in [x for x in ORDER if x != 'gbm' and x in W]:
            if 'gbm' not in W: continue
            diff = (-W[m]) - (-W['gbm'])
            p = wilcoxon(-W[m], -W['gbm']).pvalue if (diff != 0).any() else 1.0
            T.append(dict(dataset=d, frac=f, other=m, n=len(diff), extra_cycles_early_vs_ours_mean=float(diff.mean()),
                          extra_cycles_early_vs_ours_median=float(diff.median()), wilcoxon_p=float(p),
                          late_ours=int(L['gbm'].sum()), late_other=int(L[m].sum())))
    pd.DataFrame(T).to_csv(OUT + 'significance.csv', index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
    print(C.groupby(['dataset', 'method']).q_star.agg(list))
    print(S[S.frac == 0.5][['dataset', 'method', 'n', 'late', 'late_pct', 'late_ci_hi', 'early_or_ontime_pct', 'ontime_pct', 'mean_cycles_early', 'point_MAE']].round(1).to_string(index=False))
    print(O[['dataset', 'method', 'n', 'late', 'late_pct', 'early_or_ontime_pct', 'mean_cycles_early']].round(1).to_string(index=False))
