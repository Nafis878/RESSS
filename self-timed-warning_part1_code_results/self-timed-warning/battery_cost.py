"""Secondary cost analysis on the battery confirmation (listed as secondary in battery/BATTERY_PROTOCOL.md).
Same renewal-reward model as multi_eval.py, but with the warning level fixed at the pre-specified primary H = 20 blocks (no
selection). A warning at block t* triggers a planned replacement l blocks later (l in {0, 5, 10, 15} blocks = 0-45 cycles);
failure if no warning or true remaining life at the warning <= l. Cost 1 per planned replacement, rho per failure; cost rate =
total cost / total cycles used. Age replacement: age T (cycles) chosen per fold on the training cells' lives.
Output: out/battery/cost.csv
"""
import numpy as np, pandas as pd
from safe_common import outer_folds
LEADS = [0, 5, 10, 15]; RHOS = [5, 10, 20, 50]
A = pd.read_csv('out/battery/warning_results.csv'); A = A[(A.analysis == 'cv123') & (A.method == 'warning') & (A.H == 20)]
kappa = int(A.kappa.iloc[0]); life = A.set_index('unit').life_cycles; cells = np.sort(life.index.values); rows = []
for fold, test_u in enumerate(outer_folds(cells), 1):
    t = A[A.unit.isin(test_u)].set_index('unit').loc[test_u]; Ltr = life[np.setdiff1d(cells, test_u)].values; Lte = life[test_u].values.astype(float)
    assert set(t.split) == {f'cv{fold}'}
    for l in LEADS:
        for rho in RHOS:
            planned = t.pred.notna().values & (t.y.values > l); use = np.where(planned, (t.cycle.values + l) * kappa, Lte); cost = np.where(planned, 1.0, rho)
            Ts = np.arange(1, Ltr.max() + 1); cr = [np.where(Ltr > T, 1.0, rho).sum() / np.minimum(Ltr, T).sum() for T in Ts]; T = Ts[int(np.argmin(cr))]
            rows.append(dict(fold=fold, lead_blocks=l, lead_cycles=l * kappa, rho=rho, stw_cost=cost.sum(), stw_use=use.sum(), stw_fail=int((~planned).sum()),
                             age_T=int(T), age_cost=np.where(Lte > T, 1.0, rho).sum(), age_use=np.minimum(Lte, T).sum(), age_fail=int((Lte <= T).sum()),
                             rtf_cost=rho * len(Lte), rtf_use=Lte.sum(), pf_cost=float(len(Lte)), pf_use=float((Lte - 1).sum()), n=len(Lte)))
C = pd.DataFrame(rows); C.to_csv('out/battery/cost.csv', index=False)
S = C.groupby(['lead_cycles', 'rho']).sum(numeric_only=True)
for p in ('stw', 'age', 'rtf', 'pf'): S[p + '_rate'] = S[p + '_cost'] / S[p + '_use']
S['stw_rel_pf'] = S.stw_rate / S.pf_rate; S['age_rel_pf'] = S.age_rate / S.pf_rate
print(S[['stw_rate', 'age_rate', 'rtf_rate', 'pf_rate', 'stw_rel_pf', 'age_rel_pf', 'stw_fail', 'age_fail']].round(4).to_string())
