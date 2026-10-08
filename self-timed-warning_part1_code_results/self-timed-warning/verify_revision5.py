"""Third revision: compare the outputs of a fresh rerun (out/kam, out/audit) with the frozen copies (results/kam, results/audit).
CSV files are compared column by column (numbers to a relative tolerance of 1e-9, text exactly), JSON files exactly after
parsing, text files line by line. Writes out/verify_revision5.txt and exits with status 1 if anything differs.
Usage: python verify_revision5.py
"""
import os, sys, json
import numpy as np, pandas as pd

KAM = ['grid_effect_summary.csv', 'grid_effect_policies.csv', 'sim_results.csv', 'sim_pthres.csv', 'sim_pairs.csv', 'sim_checks.txt'] + \
      [f'{d}_{f}' for d in ('fd001', 'fd002', 'fd003', 'fd004') for f in ('cv_units.csv', 'cv_table.csv', 'cv_pairs.csv', 'cv_settings.csv', 'cv_bins.csv', 'leakage.txt')] + \
      ['fd001_rs_policies.csv', 'fd001_rs_pairs.csv', 'fd001_rs_policies_by_split.csv',
       'fragility_p1.csv', 'fragility_stw.csv', 'fragility_tally.csv', 'fragility_tie.csv', 'fragility_verdict.csv', 'fragility_curve.csv']
AUD = [f'hi_calibrated_{d}.csv' for d in ('PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6')] + \
      ['cost_battery_nested.csv', 'cost_battery_nested_h60.csv', 'cost_battery_nested_check.txt', 'fixed_matched_FD004.json', 'fixed_matched_units_FD004.csv']


def find(p):
    for c in (p, p + '.gz'):
        if os.path.exists(c): return c
    return None


def same_csv(a, b):
    A, B = pd.read_csv(a), pd.read_csv(b)
    if list(A.columns) != list(B.columns) or len(A) != len(B): return False, 'shape or columns differ'
    for c in A.columns:
        if A[c].dtype.kind in 'fi' and B[c].dtype.kind in 'fi':
            x, y = A[c].values.astype(float), B[c].values.astype(float)
            if not (np.isclose(x, y, rtol=1e-9, atol=1e-12) | (np.isnan(x) & np.isnan(y))).all(): return False, f'column {c} differs'
        elif not A[c].astype(str).equals(B[c].astype(str)): return False, f'column {c} differs'
    return True, f'{len(A)} rows'


lines, bad = [], 0
for sub, files in (('kam', KAM), ('audit', AUD)):
    for f in files:
        a, b = find(f'out/{sub}/{f}'), find(f'results/{sub}/{f}')
        if a is None or b is None: lines.append(f'MISSING  {sub}/{f} (fresh: {bool(a)}, frozen: {bool(b)})'); bad += 1; continue
        if f.endswith('.csv'): ok, msg = same_csv(a, b)
        elif f.endswith('.json'): ok, msg = json.load(open(a)) == json.load(open(b)), 'parsed JSON'
        else: ok, msg = open(a).read().split('\n') == open(b).read().split('\n'), 'text'
        lines.append(f'{"PASS" if ok else "FAIL"}  {sub}/{f}: {msg}'); bad += (not ok)
open('out/verify_revision5.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
print('THIRD-REVISION RERUN IDENTICAL TO FROZEN OUTPUTS' if not bad else f'{bad} files differ or are missing'); sys.exit(1 if bad else 0)
