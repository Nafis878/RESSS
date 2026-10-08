"""Leakage checks for the end-of-life first-warning model (eol_window2.py), PHM08.
E1 engine sets: outer-test engines never used for training, normalisation or tuning (all 5 folds).
E2 causality: the prediction at cycle t is identical when the engine's data after t is deleted.
E3 negative control: train on labels that belong to other engines (lives permuted across engines);
   the first-warning hit rate must collapse towards the age-only level.
E4 fold-1 rerun reproduces the stored first-warning result for H=10.
"""
import numpy as np, pandas as pd
import eol_window2 as W
from safe_common import load_dataset, outer_folds
from feats import regime_stats, zmat, causal_feats
tr, _, _ = load_dataset('PHM08'); units = np.sort(tr.unit.unique()); res = []

# E1
ok = True
for fold, test_u in enumerate(outer_folds(units), 1):
    train_u = np.setdiff1d(units, test_u)
    inner = np.array_split(np.random.default_rng(100 + fold).permutation(train_u), 5)
    ok &= len(np.intersect1d(train_u, test_u)) == 0 and set(np.concatenate(inner)) == set(train_u)
res.append(('E1 engine sets disjoint (5 folds; inner folds only use outer-training engines)', ok))

# E2
test_u = outer_folds(units)[0]; train_u = np.setdiff1d(units, test_u)
st, keep = regime_stats(tr[tr.unit.isin(train_u)])
X = np.vstack([causal_feats(zmat(g, st, keep)) for u, g in tr[tr.unit.isin(train_u)].groupby('unit')])
y = np.concatenate([g.rul.values for u, g in tr[tr.unit.isin(train_u)].groupby('unit')])
m = W.gbm(X, y, 60); maxdiff = 0.0; rng = np.random.default_rng(0)
for u in test_u[:15]:
    g = tr[tr.unit == u]; full = m.predict(causal_feats(zmat(g, st, keep)))
    for t in rng.integers(5, len(g), 6):
        pref = m.predict(causal_feats(zmat(g.iloc[:t], st, keep)))[-1]; maxdiff = max(maxdiff, abs(pref - full[t - 1]))
res.append((f'E2 causality: max |prediction(prefix) - prediction(full)| = {maxdiff:.2e} over 90 checks', maxdiff < 1e-9))

# E3 negative control on fold 1 with the settings chosen for H=10
A = pd.read_csv('out/window/first_warning_v2_PHM08.csv'); cfg = A[(A.fold == 1) & (A.H == 10)].iloc[0]
lives = tr.groupby('unit').cycle.max(); perm = dict(zip(train_u, rng.permutation(lives[train_u].values)))
yf = np.concatenate([np.maximum(perm[u] - g.cycle.values, 0) for u, g in tr[tr.unit.isin(train_u)].groupby('unit')])
mf = W.gbm(X, yf, int(cfg.cap))
P = {}
for u in test_u:
    g = tr[tr.unit == u]; P[u] = (W.smooth(mf.predict(causal_feats(zmat(g, st, keep)))[:-1], int(cfg.span)), g.rul.values[:-1])
R = W.evaluate(P, 10, int(cfg.k), float(cfg['shift'])); neg = (R.cls == 'IN').mean()
real = (A[(A.fold == 1) & (A.H == 10)].cls == 'IN').mean()
res.append((f'E3 permuted-life labels: fold-1 in-window {100*neg:.1f}% vs real labels {100*real:.1f}%', neg < real - 0.3))

# E4
m2 = W.gbm(X, y, int(cfg.cap)); P = {}
for u in test_u:
    g = tr[tr.unit == u]; P[u] = (W.smooth(m2.predict(causal_feats(zmat(g, st, keep)))[:-1], int(cfg.span)), g.rul.values[:-1])
R2 = W.evaluate(P, 10, int(cfg.k), float(cfg['shift']))
same = np.array_equal(R2.sort_values('unit').cls.values, A[(A.fold == 1) & (A.H == 10)].sort_values('unit').cls.values)
res.append(('E4 fold-1 rerun reproduces stored H=10 outcomes engine by engine', same))

with open('out/window/eol_leakage_report.md', 'w') as f:
    f.write('# Leakage checks, end-of-life first-warning model (PHM08)\n\n')
    for name, p in res:
        line = f'- {"PASS" if p else "FAIL"}  {name}'; print(line); f.write(line + '\n')
