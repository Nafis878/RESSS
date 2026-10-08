"""Unit tests of kam_metric.py. Run: python kam/test_kam_metric.py (plain asserts; exits non-zero on failure)."""
import sys, os
from fractions import Fraction as Fr
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import kam_metric as K

ok = []


def check(name, cond):
    print(('PASS  ' if cond else 'FAIL  ') + name); ok.append(bool(cond))


# 1. the perfect policy has M = 0 exactly (dT = 10 and dT = 1)
rng = np.random.default_rng(0); TF = rng.normal(225, 40, 500).clip(30)
for dT in (10, 1):
    C, T = K.lifecycle(K.perfect_tr(TF, dT), TF, 1.0, 20.0)
    check(f'perfect policy gives M = 0 (dT = {dT})', abs(K.m_hat(C, T, TF, dT, 1.0, 20.0)) < 1e-15)

# 2. any policy that acts only on the grid has M >= 0 when the footnote-1 case does not arise (random policies)
viol = 0; used = 0
for rep in range(2000):
    cc = float(rng.choice([1.25, 2, 5, 10, 20, 50, 100])); TFr = rng.normal(225, 40, 20).clip(30)
    TR = np.where(rng.random(20) < 0.15, np.inf, K.grid_point_at_or_after(rng.uniform(1, TFr + 30), 10))
    Ropt, nf = K.perfect_with_failure_option(TFr, 10, 1.0, cc)
    if nf: continue                                   # footnote case: tested separately below
    C, T = K.lifecycle(TR, TFr, 1.0, cc); viol += K.m_hat(C, T, TFr, 10, 1.0, cc, 'random grid policy') < -K.TOL; used += 1
check(f'M >= 0 for {used} random grid policies (footnote-1 draws excluded: {2000 - used})', viol == 0 and used > 1500)

# 3. hand-computed 3-unit example (dT = 10, c_p = 1, c_c = 5)
#    T_F = (25, 31, 40): perfect replaces at (20, 30, 30): R_perfect = 3/80.
#    Policy: unit 1 replaced at 20, unit 2 not replaced (fails at 31, cost 5), unit 3 replaced at 20.
#    C = (1, 5, 1), T = (20, 31, 20): R = 7/71;  M = (7/71) / (3/80) - 1 = 560/213 - 1 = 347/213.
#    Var[R] (Eq. 3, ddof 1): Var C = 16/3, Var T = 121/3, Cov = 44/3, E C = 7/3, E T = 71/3
#      = (1/3) [ (16/3)/(71/3)^2 + (7/3)^2 (121/3)/(71/3)^4 - 2 (7/3)(44/3)/(71/3)^3 ] = 42849/25411681 = (207/5041)^2
#    Var[M] = Var[R] / (3/80)^2 = 30470400/25411681 = (5520/5041)^2
TF3 = np.array([25., 31., 40.]); TR3 = np.array([20., np.inf, 20.])
check('perfect grid points (20, 30, 30)', np.array_equal(K.perfect_tr(TF3, 10), [20., 30., 30.]))
C3, T3 = K.lifecycle(TR3, TF3, 1.0, 5.0)
check('costs and life-cycles (1,5,1), (20,31,20)', np.array_equal(C3, [1, 5, 1]) and np.array_equal(T3, [20, 31, 20]))
check('R_perfect = 3/80', abs(K.r_perfect(TF3, 10, 1.0, 5.0)[0] - 3 / 80) < 1e-15)
check('R_hat = 7/71', abs(K.r_hat(C3, T3) - 7 / 71) < 1e-15)
check('M_hat = 347/213', abs(K.m_hat(C3, T3, TF3, 10, 1.0, 5.0) - float(Fr(347, 213))) < 1e-14)
check('Var[R_hat] = 42849/25411681', abs(K.var_r_hat(C3, T3) - float(Fr(42849, 25411681))) < 1e-15)
check('Var[M_hat] = 30470400/25411681', abs(K.var_m_hat(C3, T3, TF3, 10, 1.0, 5.0) - float(Fr(30470400, 25411681))) < 1e-12)

# 4. mapping of alarms to the grid; a mapped point at or after failure is a failure at cost c_c
check('grid mapping: 1 -> 10, 10 -> 10, 10.5 -> 20, NaN -> inf',
      np.array_equal(K.grid_point_at_or_after([1, 10, 10.5, np.nan], 10), [10., 10., 20., np.inf]))
C4, T4 = K.lifecycle(K.grid_point_at_or_after([24, 25.5], 10), [30., 30.], 1.0, 9.0)
check('alarm at 24 -> replaced at 30 = T_F counts as failure; alarm at 25.5 -> 30, failure', np.array_equal(C4, [9, 9]) and np.array_equal(T4, [30, 30]))

# 5. a policy acting between grid points can have M < 0 against the grid-perfect policy: recorded, not clipped
n0 = len(K.VIOLATIONS); C5, T5 = K.lifecycle(TF3 - 1, TF3, 1.0, 5.0)
M5 = K.m_hat(C5, T5, TF3, 10, 1.0, 5.0, 'off-grid replacement at T_F - 1')
check(f'off-grid policy: M = {M5:.4f} < 0 is recorded in VIOLATIONS and returned unclipped', M5 < 0 and len(K.VIOLATIONS) == n0 + 1)

# 6. footnote 1: with c_c close to c_p, letting a unit fail can beat the grid-perfect policy
TF6 = np.array([29.9, 200., 200.]); Ropt, nf = K.perfect_with_failure_option(TF6, 10, 1.0, 1.01)
C6, T6 = K.lifecycle(np.array([np.inf, 190., 190.]), TF6, 1.0, 1.01)
M6 = K.m_hat(C6, T6, TF6, 10, 1.0, 1.01, 'footnote-1 example')
check(f'footnote 1: with c_c/c_p = 1.01 failing is optimal for {nf} of 3 units; a policy that lets the first fail has M = {M6:.4f} < 0 (recorded)', nf >= 1 and M6 < 0)

# 7. paired bootstrap of an M difference is zero for identical policies
d, lo, hi = K.paired_boot_mdiff(C3, T3, C3, T3, TF3, 10, 1.0, 5.0, B=200)
check('paired bootstrap: identical policies give difference 0 (0, 0)', d == 0 and lo == 0 and hi == 0)

print(f'{sum(ok)}/{len(ok)} tests passed'); sys.exit(0 if all(ok) else 1)
