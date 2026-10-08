"""Per-engine oracle-timed control (PHM08): the full model's calibrated estimate at the cycle where the true remaining life
equals H, with the settings the nested selection chose in warn_ablation.py. Writes out/window/oracle_timed_PHM08.csv and
checks that the totals equal those stored in ablation_warning_PHM08.json."""
import json, numpy as np, pandas as pd
import eol_window2 as W
from safe_common import load_dataset, outer_folds
from feats import regime_stats, zmat, causal_feats
tr, _, _ = load_dataset('PHM08'); units = np.sort(tr.unit.unique()); AB = pd.read_csv('out/window/ablation_warning_PHM08.csv')
rows = []
for fold, test_u in enumerate(outer_folds(units), 1):
    train_u = np.setdiff1d(units, test_u); st, keep = regime_stats(tr[tr.unit.isin(train_u)])
    F = {u: causal_feats(zmat(g, st, keep)) for u, g in tr.groupby('unit')}; rul = {u: g.rul.values for u, g in tr.groupby('unit')}
    X = np.vstack([F[u] for u in train_u]); y = np.concatenate([rul[u] for u in train_u]); models = {}
    for H in (10, 20):
        cfg = AB[(AB.variant == 'full') & (AB.H == H) & (AB.fold == fold)].iloc[0]; cap = int(cfg.cap)
        if cap not in models: models[cap] = W.gbm(X, y, cap)
        for u in test_u:
            q = W.smooth(models[cap].predict(F[u])[:-1], int(cfg.span)) + cfg['shift']; i = np.flatnonzero(rul[u][:-1] == H)
            if len(i): rows.append(dict(fold=fold, H=H, unit=u, pred=q[i[0]], y=H))
O = pd.DataFrame(rows); O['cls'] = np.where(O.pred - O.y > 2, 'LATE', np.where(O.pred - O.y < -13, 'EARLY', 'IN')); O.to_csv('out/window/oracle_timed_PHM08.csv', index=False)
J = json.load(open('out/window/ablation_warning_PHM08.json'))
for H in (10, 20):
    k = int((O[O.H == H].cls == 'IN').sum()); print(H, k, J[f'oracle_timed|H{H}']['IN']); assert k == J[f'oracle_timed|H{H}']['IN']
print('ok')
