"""Checks of Amendment 1 (contrib/PLAN.md): the baselines that cat_run.py recomputes from the same predictions as CAT are
faithful copies of the original scripts, run on this machine, and the difference from the frozen results is a platform
effect, not a code effect.
P1 platform check: the window-tuned first warnings at H = 20 of the CAT code path (out/contrib/FD001_window20.csv) are
   identical, unit by unit, to those of the unmodified eol_window2.py run on this machine (PLATFORM_FILE, written by
   'python eol_window2.py FD001 20'); the deviation from the frozen results/rev/FD001_window.csv is reported.
P2 audit_cost.run (unmodified) restricted to fold 1 of FD001 gives the same decisions as the copies in cat_run.py for every
   cost policy, lead time and cost ratio.
P3 kam_fd001.run_split (unmodified) on fold 1 of FD001 gives the same decisions as the copies in cat_run.py for every
   policy under the metric M (mapped policies) and every cost ratio.
Usage: python contrib/cat_equiv.py [PLATFORM_FILE]      Output: out/contrib/cat_equiv.txt
"""
import os, sys
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'kam')); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np, pandas as pd
import audit_cost as CO
import kam_fd001 as KF
from safe_common import outer_folds

PLATFORM_FILE = ARGS[0] if ARGS else 'out/window/first_warning_v2_FD001.csv'


def main():
    lines = []
    mine = pd.read_csv('out/contrib/FD001_window20.csv').set_index(['fold', 'unit']).cls
    if os.path.exists(PLATFORM_FILE):
        plat = pd.read_csv(PLATFORM_FILE); plat = plat[plat.H == 20].set_index(['fold', 'unit']).cls.reindex(mine.index)
        lines.append((f'P1 CAT code path = unmodified eol_window2.py on this machine, FD001 H = 20, unit by unit ({int((mine == "IN").sum())}/{len(mine)} in window)', bool((mine == plat).all())))
    else:
        lines.append((f'P1 not run: {PLATFORM_FILE} missing', False))
    froz = pd.read_csv('results/rev/FD001_window.csv'); froz = froz[(froz.method == 'STW') & (froz.H == 20)].set_index(['fold', 'unit']).cls.reindex(mine.index)
    lines.append((f'P1 (information) frozen Linux run: {int((froz == "IN").sum())}/{len(froz)} in window; units with a different outcome on this machine: {int((froz != mine).sum())}', True))
    # P2: audit_cost.run on fold 1 only
    orig_folds = CO.outer_folds; CO.outer_folds = lambda u: [orig_folds(u)[0]]
    CO.OUT = 'out/contrib/equiv'; os.makedirs(CO.OUT + '/ckpt', exist_ok=True)
    if not os.path.exists(f'{CO.OUT}/cost_FD001.csv'): CO.run('FD001')
    A = pd.read_csv(f'{CO.OUT}/cost_FD001.csv'); D = pd.read_csv('out/contrib/FD001_cost.csv'); D = D[D.fold == 1]
    ok2 = True; n2 = 0
    for pol, g in A.groupby('policy'):
        a = g.sort_values(['lead_cycles', 'rho', 'unit']); b = D[D.policy == pol].sort_values(['lead_cycles', 'rho', 'unit'])
        ok2 &= len(a) == len(b) and np.array_equal(a.unit.values, b.unit.values) and np.allclose(a.cost.values, b.cost.values) and np.allclose(a.use.values, b.use.values)
        n2 += len(a)
    lines.append((f'P2 cost policies of cat_run.py = unmodified audit_cost.run, FD001 fold 1 ({A.policy.nunique()} policies, {n2} decisions)', bool(ok2)))
    # P3: kam_fd001.run_split on fold 1
    units = KF.UNITS; te = np.sort(outer_folds(units)[0]); tr = np.setdiff1d(units, te)
    rows, _, _, _ = KF.run_split(tr, te, 101, 2027, 'cv', 1)
    Kr = pd.DataFrame(rows); Kr = Kr[Kr.mapped]; M = pd.read_csv('out/contrib/FD001_M.csv'); M = M[M.split == 1]
    ok3 = True; n3 = 0; pols = []
    for pol, g in Kr.groupby('policy'):
        b = M[M.policy == pol].sort_values(['q', 'unit']); a = g.sort_values(['q', 'unit'])
        if not len(b): continue
        pols.append(pol); n3 += len(a)
        ok3 &= len(a) == len(b) and np.array_equal(a.unit.values, b.unit.values) and np.allclose(a.cost.values, b.cost.values) and np.allclose(a.tlc.values, b.tlc.values)
    lines.append((f'P3 policies under M of cat_run.py = unmodified kam_fd001.run_split, FD001 fold 1 ({len(pols)} policies, {n3} decisions)', bool(ok3) and len(pols) >= 14))
    txt = '\n'.join(f'{"PASS" if o else "FAIL"}  {s}' for s, o in lines)
    open('out/contrib/cat_equiv.txt', 'w', newline='\n').write(txt + '\n'); print(txt)
    if not all(o for _, o in lines): raise SystemExit('STOP: equivalence check failed')


if __name__ == '__main__':
    main()
