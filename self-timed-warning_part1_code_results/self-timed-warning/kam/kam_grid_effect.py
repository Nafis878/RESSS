"""Phase 1a: reference-grid effect. For every existing policy of the cost analysis (audit_cost.py, frozen outputs
results/audit/cost_<ds>.csv.gz), at lead time 0 only, compute its long-run cost rate relative to
  (a) the 1-cycle perfect policy (replacement at L - 1), as reported in the manuscript, and
  (b) the grid-perfect policy of Kamariotis et al. (last decision point k*dT strictly before failure), dT = 10 cycles,
and the difference. The policies are NOT re-mapped to the grid here: they act at any cycle ("unmapped 1-cycle results"),
so (b) - 1 is M_hat of an off-grid policy and can be negative; every negative value is listed, not clipped.
Battery: convention B of key_numbers.md (task in blocks, kappa from the outer training cells), lives in cycles from the
fully nested run, dT = 10 and 30 cycles.
Output: out/kam/grid_effect_policies.csv, out/kam/grid_effect_summary.csv
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__)); import kam_metric as K
A = 'results/audit'; OUT = 'out/kam'; os.makedirs(OUT, exist_ok=True)
DS = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'Battery']
POL = ['STW_window', 'STW_cost', 'STW_cost_1se', 'STW_cost_q80', 'Q10_cost', 'Q10_cost_1se', 'HI_cost', 'capacity_cost', 'capacity_cost_1se', 'age', 'run_to_failure']
rows, summ = [], []
blife = pd.concat([pd.read_csv(f'{A}/battery_physical_{s}.csv.gz') for s in ('cv', 'lobo')]).drop_duplicates('unit').set_index('unit').life_cycles
for ds in DS:
    C = pd.read_csv(f'{A}/cost_{ds}.csv.gz'); C = C[C.lead_cycles == 0]
    pf = C[(C.policy == 'perfect_foresight')].drop_duplicates('unit').set_index('unit')
    if ds == 'Battery': L = blife.reindex(pf.index).astype(float)              # true lives in cycles
    else: L = (pf.use + 1).astype(float)                                       # perfect foresight uses L - 1 cycles
    for dT in ((10, 30) if ds == 'Battery' else (10,)):
        R1 = len(L) / (L - 1).sum()                                            # 1-cycle perfect policy, cost 1 per unit
        for rho, g in C.groupby('rho'):
            Rg, nfail_grid = K.r_perfect(L.values, dT, 1.0, float(rho))
            Ropt, nf = K.perfect_with_failure_option(L.values, dT, 1.0, float(rho))
            if rho == C.rho.min():
                summ.append(dict(dataset=ds, dT=dT, n_units=len(L), mean_life=round(float(L.mean()), 2), mean_T_perfect_1=round(float((L - 1).mean()), 3),
                                 mean_T_perfect_grid=round(float(np.mean(K.lifecycle(K.perfect_tr(L.values, dT), L.values, 1, rho)[1])), 3),
                                 grid_effect_pct=round(100 * (Rg / R1 - 1), 3), units_without_grid_point=nfail_grid, footnote1_units=nf))
            for p in POL:
                h = g[g.policy == p]
                if not len(h): continue
                h = h.set_index('unit').reindex(L.index)
                Rp = h.cost.sum() / h.use.sum()
                M = K.m_hat(h.cost.values, h.use.values, L.values, dT, 1.0, float(rho), f'{ds} {p} rho={rho} dT={dT} (unmapped)')
                rows.append(dict(dataset=ds, dT=dT, rho=int(rho), cp_over_cc=round(1 / rho, 4), policy=p, ratio_vs_1cycle_perfect=round(Rp / R1, 4),
                                 one_plus_M_grid=round(1 + M, 4), difference=round(Rp / R1 - (1 + M), 4), M_grid_pct=round(100 * M, 2), M_negative=bool(M < -K.TOL),
                                 failures=int(h.fail.sum()), footnote1_units=nf))
P = pd.DataFrame(rows); S = pd.DataFrame(summ)
P.to_csv(f'{OUT}/grid_effect_policies.csv', index=False); S.to_csv(f'{OUT}/grid_effect_summary.csv', index=False)
print(S.to_string(index=False)); print('\nnegative M (unmapped policies):', int(P.M_negative.sum()), 'of', len(P))
print(P[P.policy.isin(['STW_window', 'STW_cost_1se', 'age'])].to_string(index=False))
