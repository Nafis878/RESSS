"""Empirical check of the window-centring proposition.

Model: a warning is raised when the shifted prediction p + s first falls to H; at that moment the unshifted prediction error is
eps = p - r (r = true remaining life), and the reported error is e = eps + s. With eps ~ F (continuous, unimodal, symmetric about
its median m) the probability of a correct first warning is P(s) = F(b - s) - F(a - s); it is maximised at s* = (a + b)/2 - m
(= -5.5 - m for the window [-13, +2]), and the maximum equals P(|eps - m| <= (b - a)/2).
For every dataset and warning level we compute, on the TEST warnings (one per engine), eps = pred - shift - y, its median m, the
implied s*, the shifts actually chosen on training data, the centred bound P(|eps - m| <= 7.5), the best fixed-shift rate
max_s P(a <= eps + s <= b) and the realised in-window rate. Missed engines count as failures in all rates.
Output: out/theory/theory_check.csv
"""
import os, numpy as np, pandas as pd
LO, HI = -13, 2; HALF = (HI - LO) / 2; MID = (LO + HI) / 2
SH = np.arange(-20, 10.01, 0.5)

def rows_for(ds, g):
    out = []
    for H, h in g.groupby('H'):
        n = len(h); v = h.dropna(subset=['pred']); eps = (v.pred - v['shift'] - v.y).values; m = float(np.median(eps))
        best = max(((((eps + s) >= LO) & ((eps + s) <= HI)).sum(), s) for s in SH)
        out.append(dict(dataset=ds, H=int(H), n=n, missed=int(n - len(v)), median_eps=round(m, 2), eps_iqr=round(float(np.subtract(*np.percentile(eps, [75, 25]))), 2),
                        s_star=round(MID - m, 2), shift_mean=round(float(h['shift'].mean()), 2), shift_min=float(h['shift'].min()), shift_max=float(h['shift'].max()),
                        centred_bound_pct=round(100 * float((np.abs(eps - m) <= HALF).sum()) / n, 1),
                        best_fixed_shift_pct=round(100 * best[0] / n, 1), best_fixed_shift=float(best[1]),
                        realised_pct=round(100 * float((h.cls == 'IN').mean()), 1),
                        skew_mean_minus_median=round(float(eps.mean() - m), 2)))
    return out

def main():
    rows = []
    for ds in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']:
        A = pd.read_csv(f'out/window/first_warning_v2_{ds}.csv'); rows += rows_for(ds, A[A.H.isin([10, 15, 20])])
    A = pd.read_csv('out/ncm/warning_results.csv'); rows += rows_for('N-CMAPSS', A[A.primary & (A.method == 'warning')])
    if os.path.exists('out/battery/warning_results.csv'):
        A = pd.read_csv('out/battery/warning_results.csv'); rows += rows_for('Battery', A[(A.analysis == 'cv123') & (A.method == 'warning')])
    if os.path.exists('out/bearing/warning_results.csv'):
        A = pd.read_csv('out/bearing/warning_results.csv'); rows += rows_for('Bearing', A[(A.analysis == 'cv') & (A.method == 'warning')])
    T = pd.DataFrame(rows); os.makedirs('out/theory', exist_ok=True); T.to_csv('out/theory/theory_check.csv', index=False)
    print(T.to_string(index=False))
    print('corr(shift_mean, s_star) =', round(float(np.corrcoef(T.shift_mean, T.s_star)[0, 1]), 3),
          '| mean |realised - best_fixed| =', round(float((T.realised_pct - T.best_fixed_shift_pct).abs().mean()), 2))

if __name__ == '__main__':
    main()
