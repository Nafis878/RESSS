"""Per-snapshot features of the FEMTO/PRONOSTIA bearings, as fixed in bearing/BEARING_PROTOCOL.md.
For each acc_*.csv snapshot (2560 samples, horizontal and vertical acceleration): per channel (mean removed) RMS, peak, kurtosis
(Fisher), crest factor. Output: bearing/femto_snapshot_features.csv.gz (one row per bearing and snapshot)."""
import os, glob, numpy as np, pandas as pd
from scipy.stats import kurtosis
from concurrent.futures import ProcessPoolExecutor
ROOT = 'bearing/femto_repo'
COND = {'1': 1, '2': 2, '3': 3}

def read(f):
    with open(f) as fh: first = fh.readline()
    sep = ';' if first.count(';') > first.count(',') else ','
    return pd.read_csv(f, sep=sep, header=None).values[:, 4:6].astype(float)

def feats(f):
    x = read(f); x = x - x.mean(0); rms = np.sqrt((x ** 2).mean(0)); pk = np.abs(x).max(0)
    return np.r_[rms, pk, kurtosis(x, axis=0, fisher=True), pk / np.where(rms > 0, rms, np.nan)]

def bearing(d):
    files = sorted(glob.glob(f'{d}/acc_*.csv')); idx = [int(os.path.basename(f)[4:9]) for f in files]
    assert idx == list(range(1, len(files) + 1)), d
    F = np.array([feats(f) for f in files]); name = os.path.basename(d)
    df = pd.DataFrame(F, columns=[f'{s}_{c}' for s in ('rms', 'peak', 'kurt', 'crest') for c in ('h', 'v')])
    df.insert(0, 'snapshot', idx); df.insert(0, 'condition', COND[name[7]]); df.insert(0, 'set', d.split('/')[-2]); df.insert(0, 'bearing', name)
    return df

if __name__ == '__main__':
    dirs = sorted(glob.glob(f'{ROOT}/Learning_set/Bearing*')) + sorted(glob.glob(f'{ROOT}/Full_Test_Set/Bearing*'))
    with ProcessPoolExecutor(2) as ex: out = list(ex.map(bearing, dirs))
    D = pd.concat(out, ignore_index=True); D.to_csv('bearing/femto_snapshot_features.csv.gz', index=False)
    print(D.groupby('bearing').snapshot.max().to_string()); print(D.shape, 'non-finite:', int((~np.isfinite(D.iloc[:, 4:].values)).sum()))
