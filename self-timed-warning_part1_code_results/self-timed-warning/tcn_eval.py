"""Evaluate TCN, TCN+GAN and the stacked hybrid with TCN/TCN+GAN added (window [-13, +2], half of life, PHM08).
Reuses the stacker definitions of ablate_hybrid.py (trained on calibration rows only, shift by engine-grouped CV)."""
import json, numpy as np, pandas as pd
src = open('ablate_hybrid.py').read().split("T = D[D.role == 'test']")[0]
exec(src)                                                     # defines D, GROUPS, hit, summ, decode_q, fit_predict, with_shift, run
Tn = pd.read_csv('out/window/tcn_preds_PHM08.csv')
D = D.merge(Tn.drop(columns=['y']), on=['fold', 'unit', 'role', 'stage', 't'], how='left'); assert D.tcn_q50.notna().all()
T = D[D.role == 'test']; res = {'single': {}}
QS3 = [0.05, 0.5, 0.95]
def decode3(Q):
    Q = np.sort(Q, 1); cs = np.arange(0, 400, 0.5); out = np.empty(len(Q)); p = np.array([0, .05, .5, .95, 1])
    for i, q in enumerate(Q):
        x = np.array([q[0] - (q[1] - q[0]) * 0.1, q[0], q[1], q[2], q[2] + (q[2] - q[1]) * 0.1]); x = np.maximum.accumulate(x + np.arange(5) * 1e-6)
        out[i] = cs[np.argmax(np.interp(cs - LO, x, p) - np.interp(cs - HI, x, p))]
    return out
for m in ('tcn', 'tcngan', 'tstr'):
    res['single'][f'{m}_median'] = summ(T[f'{m}_q50'], T.y)
    res['single'][f'{m}_window'] = summ(decode3(T[[f'{m}_q05', f'{m}_q50', f'{m}_q95']].values), T.y)
    res['single'][f'{m}_90pct_interval'] = dict(width=round(float((T[f'{m}_q95'] - T[f'{m}_q05']).median()), 1),
                                                coverage=round(100 * float(((T.y >= T[f'{m}_q05']) & (T.y <= T[f'{m}_q95'])).mean()), 1))
GROUPS['tcn'] = ['tcn_q05', 'tcn_q50', 'tcn_q95']; GROUPS['tcn_gan'] = ['tcngan_q05', 'tcngan_q50', 'tcngan_q95']
ALL = sum(GROUPS.values(), []); OLD = [c for c in ALL if not c.startswith('tcn')]
res['hybrid_previous'] = summ(*[(P.pred, P.y) for P in [run(OLD, 'gbm_quantile')[0]]][0])
P, cv = run(ALL, 'gbm_quantile'); res['hybrid_with_tcn_and_gan'] = dict(cal_cv_hit=round(100 * cv, 1), **summ(P.pred, P.y))
P.to_csv('out/window/hybrid_tcn_gan_half_PHM08.csv', index=False)
res['hybrid_plus_tcn_only'] = summ(*[(P.pred, P.y) for P in [run([c for c in ALL if not c.startswith('tcngan')], 'gbm_quantile')[0]]][0])
res['hybrid_plus_tcngan_only'] = summ(*[(P.pred, P.y) for P in [run([c for c in ALL if c not in GROUPS['tcn']], 'gbm_quantile')[0]]][0])
json.dump(res, open('out/window/tcn_gan_results_PHM08.json', 'w'), indent=1); print(json.dumps(res, indent=1))
