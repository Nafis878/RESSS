"""Leakage checks E1-E4 on the CAT code path (contrib/PLAN.md, 'Leakage checks'), FD001 fold 1 (as kam/kam_fd001.py leak).
E1 disjoint unit sets: asserted inside every split of cat_run.py, cat_battery.py and cat_bearing.py; repeated here for the
   five FD001 folds, including the CAT-SPLIT halves.
E2 causality: (a) regressor prediction at cycle t from the prefix 1..t equals the full-series prediction (90 checks);
   (b) the CAT alarm on the full series fires at the same cycle when every cycle after the alarm is deleted, and does not
   fire on the series truncated just before it (all test units, certified threshold, lead 10).
E3 negative control: inner and final regressors trained on lives permuted across the training units (calibration on the
   true training lives, as allowed); CAT-c (alpha 0.05, lead 10, rho 10) must cost more than with the real labels.
E4 rerun of fold 1 from scratch reproduces every stored CAT decision (cost and M rows) of out/contrib/ckpt/FD001_fold1.pkl.
Usage: python contrib/cat_leak.py      Output: out/contrib/cat_leakage.txt
"""
import os, sys, pickle
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'kam')); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np, pandas as pd
import eol_window2 as W
import rev_experiments as R
from safe_common import load_dataset, outer_folds
from feats import regime_stats, zmat, causal_feats
import cat as C
import cat_run as CR

DS = 'FD001'


def main():
    lines = []; units, feats = R.adapter(DS); folds = outer_folds(units)
    ok = True
    for fold, te in enumerate(folds, 1):
        tr = np.setdiff1d(units, te); inner = np.array_split(np.random.default_rng(100 + fold).permutation(tr), 5)
        perm = np.random.default_rng(500 + fold).permutation(tr); A, B = perm[:len(perm) // 2], perm[len(perm) // 2:]
        ok &= not set(tr) & set(te) and set(np.concatenate(inner)) == set(tr) and not set(A) & set(B) and set(A) | set(B) == set(tr)
    lines.append(('E1 disjoint outer test, outer training, inner and CAT-SPLIT unit sets (5 FD001 folds)', ok))
    fold = 1; te = np.sort(folds[0]); tr = np.setdiff1d(units, te)
    sel = pd.read_csv(f'out/contrib/{DS}_selected.csv').iloc[0]; cap, sp, k = int(sel.cap), int(sel.span), int(sel.k)
    sets = pd.read_csv(f'out/contrib/{DS}_settings.csv'); srow = sets[(sets.fold == 1) & (sets.lead_cycles == 10) & (sets.dT == 1) & (sets.alpha == 0.05)].iloc[0]
    tau = float(srow.tau_cf)
    # E2 (a) prefix predictions
    trd, _, _ = load_dataset(DS); st, keep = regime_stats(trd[trd.unit.isin(tr)])
    F, Y = feats(tr, np.concatenate([tr, te])); X = np.vstack([F[u] for u in tr]); y = np.concatenate([Y[u] for u in tr]); m = W.gbm(X, y, cap)
    rng = np.random.default_rng(0); md = 0.0
    for u in te[:15]:
        g = trd[trd.unit == u]; full = m.predict(causal_feats(zmat(g, st, keep)))
        assert np.allclose(causal_feats(zmat(g, st, keep)), F[u])
        for t in rng.integers(5, len(g), 6): md = max(md, abs(m.predict(causal_feats(zmat(g.iloc[:t], st, keep)))[-1] - full[t - 1]))
    lines.append((f'E2a causality of the regressor (cap {cap}): max |prefix - full| = {md:.2e} over 90 checks', md < 1e-9))
    # E2 (b) alarm causality
    okb = True; nal = 0
    for u in te:
        x = W.smooth(m.predict(F[u])[:-1], sp); i = int(C.alarm_index(x, k, [tau])[0])
        if i < len(x):
            nal += 1; xs = W.smooth(m.predict(F[u][:i + 1])[:i + 1], sp)
            okb &= int(C.alarm_index(xs, k, [tau])[0]) == i and int(C.alarm_index(xs[:i], k, [tau])[0]) == i
    lines.append((f'E2b causality of the CAT alarm: identical alarm cycle with the future deleted, no alarm before it ({nal} alarms)', bool(okb)))
    # E3 negative control
    lives = {u: Y[u][0] + 1 for u in tr}; pl = dict(zip(tr, np.random.default_rng(0).permutation([lives[u] for u in tr])))
    def feats_perm(stat_u, use_u):
        F_, Y_ = feats(stat_u, use_u)
        return F_, {u: (np.maximum(pl[u] - np.arange(1, len(Y_[u]) + 1), 0).astype(float) if u in pl else Y_[u]) for u in use_u}
    def cat_c_cost(fe):
        inner = np.array_split(np.random.default_rng(100 + fold).permutation(tr), 5); oof = {}
        for iu in inner:
            P = CR.fit_all(fe, np.setdiff1d(tr, iu), iu, caps=[cap])[cap]
            oof.update({u: (P[u][0], Y[u][:-1]) for u in iu})                 # calibration on the true training lives
        P = CR.fit_all(fe, tr, te, caps=[cap])[cap]; fin = {u: (P[u][0], Y[u][:-1]) for u in te}
        to = CR.tab_of(oof, sp, k, R.TAUS); tt = CR.tab_of(fin, sp, k, R.TAUS)
        th, cert = C.tau_hat(C.scores_from_table(to, R.TAUS, 10), 0.05); j0 = C.certified_column(R.TAUS, th, cert)
        j1 = C.cost_aware_column(to, R.TAUS, j0, 10, 10, C.cost_1cycle); c, use, pl_ = R.cost_of(*CR.col(tt, j1)[1:], 10, 10)
        perf = len(te) / sum(Y[u][0] for u in te)
        return (c.sum() / use.sum()) / perf, int((~pl_).sum()), float(np.nanmedian(np.where(pl_, CR.col(tt, j1)[2], np.nan)))
    real = cat_c_cost(feats); perm_ = cat_c_cost(feats_perm)
    lines.append((f'E3 permuted-life labels: CAT-c cost rate / perfect {perm_[0]:.3f} ({perm_[1]} failures, median notice {perm_[2]:.0f}) '
                  f'vs real labels {real[0]:.3f} ({real[1]} failures, median notice {real[2]:.0f})', perm_[0] > real[0]))
    # E4 rerun
    ck = f'out/contrib/ckpt/{DS}_fold1.pkl'
    if os.path.exists(ck):
        old = pickle.load(open(ck, 'rb')); new = CR.run_fold(DS, units, feats, 1, te, [0, 5, 10, 15])
        cols = ['policy', 'lead_cycles', 'rho', 'unit', 'cost', 'use', 'fail']
        a = pd.DataFrame(old[0])[cols].reset_index(drop=True); b = pd.DataFrame(new[0])[cols].reset_index(drop=True)
        ma = pd.DataFrame(old[1])[['policy', 'q', 'unit', 'cost', 'tlc']].reset_index(drop=True); mb = pd.DataFrame(new[1])[['policy', 'q', 'unit', 'cost', 'tlc']].reset_index(drop=True)
        lines.append((f'E4 rerun of fold 1 reproduces every stored CAT decision ({len(a)} cost rows, {len(ma)} M rows)', a.equals(b) and ma.equals(mb)))
    else:
        lines.append(('E4 not run: fold 1 checkpoint missing', False))
    txt = '\n'.join(f'{"PASS" if o else "FAIL"}  {s}' for s, o in lines)
    open('out/contrib/cat_leakage.txt', 'w', newline='\n').write(txt + '\n'); print(txt)
    if not all(o for _, o in lines): raise SystemExit('STOP: leakage check failed')


if __name__ == '__main__':
    main()
