"""Check R0 of kam/PHASE3_4_PLAN.md: the re-run of Phase 2 (after the workspace reset) must reproduce the frozen Phase 2
summary tables in results/kam/ (written before the reset). Compares the freshly summarised tables in out/kam/ with the
frozen ones, column by column (numerical tolerance 1e-9, relative), and writes out/kam/r0_check.txt.
Usage: python kam/kam_fd001_summarize.py && python kam/check_r0.py
"""
import os, sys
import numpy as np, pandas as pd

FILES = [('fd001_cv_table.csv', ['q', 'policy']), ('fd001_cv_pairs.csv', ['q', 'a', 'b']),
         ('fd001_rs_policies.csv', ['q', 'policy']), ('fd001_rs_pairs.csv', ['q', 'a', 'b']),
         ('fd001_rs_policies_by_split.csv', ['q', 'split', 'policy']), ('fd001_thresholds.csv', ['protocol', 'q', 'model']),
         ('fd001_bins_summary.csv', ['protocol', 'cap', 'bin'])]
lines = []
for f, keys in FILES:
    a, b = f'out/kam/{f}', f'results/kam/{f}'
    if not os.path.exists(a):
        lines.append(f'NOT RUN  {f}: no fresh output'); continue
    A = pd.read_csv(a).sort_values(keys).reset_index(drop=True); B = pd.read_csv(b).sort_values(keys).reset_index(drop=True)
    if 'protocol' in keys and set(A.protocol) != set(B.protocol):             # only the protocols that were re-run
        A = A[A.protocol.isin(B.protocol)]; B = B[B.protocol.isin(A.protocol)]; A, B = A.reset_index(drop=True), B.reset_index(drop=True)
    ok = len(A) == len(B) and list(A.columns) == list(B.columns) and A[keys].astype(str).equals(B[keys].astype(str))
    worst = 0.0
    if ok:
        for c in A.columns:
            if c in keys: continue
            if A[c].dtype.kind in 'fi' and B[c].dtype.kind in 'fi':
                x, y = A[c].values.astype(float), B[c].values.astype(float)
                same = np.isclose(x, y, rtol=1e-9, atol=1e-9) | (np.isnan(x) & np.isnan(y)); ok &= bool(same.all())
                d = np.abs(x - y); d = d[np.isfinite(d)]; worst = max(worst, float(d.max()) if len(d) else 0.0)
            else:
                ok &= A[c].astype(str).equals(B[c].astype(str))
    lines.append(f'{"PASS" if ok else "FAIL"}  {f}: {len(A)} rows; largest absolute difference {worst:.2e}')
open('out/kam/r0_check.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
