"""Phase 2 summary tables from the per-unit outputs of kam_fd001.py (plan: kam/PHASE2_PLAN.md with amendment 1); with
--ds FD002|FD003|FD004 the same tables for the Phase 3 five-fold runs (plan: kam/PHASE3_4_PLAN.md), files <ds>_* instead of fd001_*.
Usage: python kam/kam_fd001_summarize.py [--ds FDxxx] [--frozen]   (reads out/kam or, with --frozen, results/kam)
Outputs (out/kam/): fd001_cv_table.csv (M per policy and cost ratio, Eq. 7 and bootstrap intervals, failures),
fd001_cv_pairs.csv (paired differences, 'beats' flags), fd001_rs_policies.csv, fd001_rs_pairs.csv (distribution across
the 30 random splits), fd001_bins_summary.csv, fd001_thresholds.csv, fd001_summary.md
"""
import os, sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kam_metric as K
SRC = 'results/kam' if '--frozen' in sys.argv else 'out/kam'; OUT = 'out/kam'; os.makedirs(OUT, exist_ok=True)
TAG = sys.argv[sys.argv.index('--ds') + 1].lower() if '--ds' in sys.argv else 'fd001'
DT, B, SEED = 10.0, 2000, 2027
MINE = ['STW_window', 'STW_cost', 'STW_cost_1se']
THEIRS = ['P1_cls_q', 'P1_cls_opt_mid', 'P1_cls_opt_max', 'P1_res_q', 'P1_res_opt_mid', 'P1_res_opt_max', 'P3_res60', 'age_grid']
ORDER = MINE + THEIRS + ['P3_res125', 'HI_cost', 'STW_window_unmapped', 'STW_cost_unmapped', 'STW_cost_1se_unmapped', 'run_to_failure', 'perfect_grid']


def read(pattern):
    fs = sorted(glob.glob(f'{SRC}/{pattern}') + glob.glob(f'{SRC}/{pattern}.gz')); return pd.concat([pd.read_csv(f) for f in fs]) if fs else None


def m_boot(c, t, TF, cc, rng):
    Cp, Tp = K.lifecycle(K.perfect_tr(TF, DT), TF, 1.0, cc); n = len(TF); idx = rng.integers(0, n, size=(B, n))
    m = (c[idx].sum(1) / t[idx].sum(1)) / (Cp[idx].sum(1) / Tp[idx].sum(1)) - 1
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def piv(D, q):
    g = D[D.q == q]; units = np.sort(g.unit.unique())
    P = {p: h.set_index('unit').reindex(units) for p, h in g.groupby('policy')}
    return units, P


cv = read(f'{TAG}_cv_units.csv'); rs = read(f'{TAG}_rs_*_units.csv')
rows, prs = [], []
for q in sorted(cv.q.unique()):
    cc = 1 / q; units, P = piv(cv, q); TF = P['perfect_grid'].TF.values
    R1 = len(TF) / (TF - 1).sum()                                                # 1-cycle perfect policy
    for p in ORDER:
        if p not in P: continue
        c, t = P[p]['cost'].values, P[p]['tlc'].values
        M, lo, hi = K.m_with_ci(c, t, TF, DT, 1.0, cc, f'cv {p} q={q}')
        blo, bhi = m_boot(c, t, TF, cc, np.random.default_rng(SEED))
        rows.append(dict(q=q, policy=p, mapped=bool(P[p].mapped.iloc[0]), M_pct=100 * M, eq7_lo=100 * lo, eq7_hi=100 * hi, boot_lo=100 * blo, boot_hi=100 * bhi,
                         failures=int(P[p].fail.sum()), n=len(TF), mean_tlc=float(t.mean()), ratio_vs_1cycle_perfect=float((c.sum() / t.sum()) / R1)))
    for a in MINE:
        for b in THEIRS + ['P3_res125', 'HI_cost']:
            d, lo, hi = K.paired_boot_mdiff(P[a]['cost'].values, P[a]['tlc'].values, P[b]['cost'].values, P[b]['tlc'].values, TF, DT, 1.0, cc, B=B, seed=SEED)
            prs.append(dict(q=q, a=a, b=b, diff_pct=100 * d, lo=100 * lo, hi=100 * hi,
                            verdict=f'{a} beats {b}' if hi < 0 else (f'{b} beats {a}' if lo > 0 else 'unclear')))
T = pd.DataFrame(rows); PR = pd.DataFrame(prs)
T.to_csv(f'{OUT}/{TAG}_cv_table.csv', index=False); PR.to_csv(f'{OUT}/{TAG}_cv_pairs.csv', index=False)
grid_neg = T[T.mapped & (T.M_pct < -1e-10)]

# ---- protocol (A): 30 random splits
if rs is not None:
    pol, pp = [], []
    for (q, s), g in rs.groupby(['q', 'split']):
        cc = 1 / q; units, P = piv(g, q); TF = P['perfect_grid'].TF.values
        for p in ORDER:
            if p in P: pol.append(dict(q=q, split=s, policy=p, M_pct=100 * K.m_hat(P[p]['cost'].values, P[p]['tlc'].values, TF, DT, 1.0, cc, f'rs{s} {p} q={q}'), failures=int(P[p].fail.sum())))
        for a in MINE:
            for b in THEIRS:
                d, lo, hi = K.paired_boot_mdiff(P[a]['cost'].values, P[a]['tlc'].values, P[b]['cost'].values, P[b]['tlc'].values, TF, DT, 1.0, cc, B=B, seed=SEED + int(s))
                pp.append(dict(q=q, split=s, a=a, b=b, diff_pct=100 * d, lo=100 * lo, hi=100 * hi))
    RP = pd.DataFrame(pol); RQ = pd.DataFrame(pp)
    RPs = RP.groupby(['q', 'policy']).agg(M_median=('M_pct', 'median'), M_q25=('M_pct', lambda x: x.quantile(.25)), M_q75=('M_pct', lambda x: x.quantile(.75)),
                                          M_min=('M_pct', 'min'), M_max=('M_pct', 'max'), splits=('M_pct', 'size'), splits_with_failure=('failures', lambda x: int((x > 0).sum())),
                                          failures_total=('failures', 'sum')).reset_index()
    RQs = RQ.groupby(['q', 'a', 'b']).agg(diff_median=('diff_pct', 'median'), diff_q25=('diff_pct', lambda x: x.quantile(.25)), diff_q75=('diff_pct', lambda x: x.quantile(.75)),
                                          diff_min=('diff_pct', 'min'), diff_max=('diff_pct', 'max'), share_a_lower=('diff_pct', lambda x: float((x < 0).mean())),
                                          share_b_lower=('diff_pct', lambda x: float((x > 0).mean())), n_interval_below0=('hi', lambda x: int((x < 0).sum())),
                                          splits=('diff_pct', 'size')).reset_index()
    RQs['n_interval_above0'] = RQ.groupby(['q', 'a', 'b']).lo.apply(lambda x: int((x > 0).sum())).values
    RP.to_csv(f'{OUT}/{TAG}_rs_policies_by_split.csv', index=False); RPs.to_csv(f'{OUT}/{TAG}_rs_policies.csv', index=False); RQs.to_csv(f'{OUT}/{TAG}_rs_pairs.csv', index=False)

# ---- bins and thresholds
Bn = read(f'{TAG}_*_bins.csv')
if Bn is not None:
    low = Bn[Bn.bin <= 2].groupby(['protocol', 'cap', 'bin']).agg(rows_min=('rows', 'min'), rows_median=('rows', 'median'), units_min=('units', 'min'),
                                                                 units_median=('units', 'median'), hi_median=('hi', 'median')).reset_index()
    nb = Bn.groupby(['protocol', 'cap', 'split']).n_bins.first().groupby(level=[0, 1]).agg(['min', 'median', 'max']).reset_index()
    low.to_csv(f'{OUT}/{TAG}_bins_summary.csv', index=False); nb.to_csv(f'{OUT}/{TAG}_bins_count.csv', index=False)
S = read(f'{TAG}_*_settings.csv')
if S is not None:
    th = S[S.model.isin(['cls', 'res'])].groupby(['protocol', 'q', 'model']).agg(p_mid_median=('p_mid', 'median'), p_max_median=('p_max', 'median'),
                                                                            p_mid_min=('p_mid', 'min'), p_mid_max=('p_mid', 'max'), n_tied_median=('n_tied', 'median')).reset_index()
    th.to_csv(f'{OUT}/{TAG}_thresholds.csv', index=False)

# ---- markdown summary (primary ratio first)
L = [f'# {TAG.upper()} under the conventions of Kamariotis et al. (exploratory; plan hashed before the run)', '']
for q in [0.1] + [x for x in sorted(T.q.unique()) if x != 0.1]:
    t = T[T.q == q].copy()
    L.append(f'## c_p/c_c = {q}' + ('  (primary)' if q == 0.1 else '  (descriptive)'))
    L.append('| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |'); L.append('|---|---|---|---|---|---|')
    for _, r in t.iterrows():
        L.append(f'| {r.policy}{"" if r.mapped else " (unmapped)"} | {r.M_pct:.2f} | {r.eq7_lo:.2f} to {r.eq7_hi:.2f} | {r.boot_lo:.2f} to {r.boot_hi:.2f} | {r.failures} | {r.ratio_vs_1cycle_perfect:.4f} |')
    p = PR[PR.q == q]; L.append(''); L.append('| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |'); L.append('|---|---|---|---|---|')
    for _, r in p.iterrows(): L.append(f'| {r.a} | {r.b} | {r.diff_pct:+.2f} | {r.lo:+.2f} to {r.hi:+.2f} | {r.verdict} |')
    L.append('')
L.append(f'Grid-mapped policies with M < 0: {len(grid_neg)}. Recorded violations (all, incl. unmapped): {len(K.VIOLATIONS)}.')
open(f'{OUT}/{TAG}_summary.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L[:60]))
