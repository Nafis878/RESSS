"""Compare the fresh audit outputs in out/audit/ with the frozen copies in results/audit/ (gzip-aware).
CSV and JSON files must be byte-identical after decompression; pickles must contain identical arrays."""
import os, sys, gzip, glob, pickle
import numpy as np


def eq(x, y):
    x, y = np.asarray(x), np.asarray(y)
    return np.array_equal(x, y, equal_nan=x.dtype.kind == 'f' and y.dtype.kind == 'f')

ok = True
for fz in sorted(glob.glob('results/audit/*')):
    name = os.path.basename(fz); plain = name[:-3] if name.endswith('.gz') else name; fo = f'out/audit/{plain}'
    if not os.path.exists(fo): print(f'not rerun   {plain}'); continue
    a = gzip.open(fz, 'rb').read() if name.endswith('.gz') else open(fz, 'rb').read(); b = open(fo, 'rb').read()
    if plain.endswith('.pkl'):
        A, B = pickle.loads(a), pickle.loads(b)
        same = np.array_equal(A['shifts'], B['shifts']) and len(A['rec']) == len(B['rec']) and all(
            all(eq(x[k], y[k]) for k in x) for x, y in zip(A['rec'], B['rec']))
    else:
        same = a == b
    print(f"{'IDENTICAL' if same else 'DIFFERENT'}   {plain}"); ok &= same
print('AUDIT REPRODUCTION CHECK ' + ('PASSED' if ok else 'FAILED')); sys.exit(0 if ok else 1)
