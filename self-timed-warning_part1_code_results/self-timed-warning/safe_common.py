"""Shared protocol for the safety-constrained early-prediction study.

Datasets : PHM08 training set (218 run-to-failure engines) and C-MAPSS FD001-FD004 training sets.
Protocol : 5-fold cross-validation by engine (seed 2026). Inside each outer-training part the engines are
           split 75 / 25 into FIT engines (train the point model) and CALIBRATION engines (build the
           cautious layer) -- split-conformal style, identical for every method.
           Official C-MAPSS test sets: fit/calibrate on the full training set (same 75/25 split).
Inputs   : temperatures T24, T30, T50 and shaft speeds Nf, Nc, NRf, NRc (s2, s3, s4, s8, s9, s13, s14),
           z-scored per operating regime with statistics of the FIT engines only.
"""
import numpy as np, pandas as pd

SENS7 = ['s2', 's3', 's4', 's8', 's9', 's13', 's14']
COLS = ['unit', 'cycle', 'os1', 'os2', 'os3'] + [f's{i}' for i in range(1, 22)]
DATASETS = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']
FRACTIONS = [0.3, 0.5, 0.7, 0.9]
QGRID = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50])
EARLY_LIM, LATE_LIM, LATE_TARGET = -10, 5, 0.03    # on-time window [-10, +5]; calibrate late rate <= 3 %


def _read(path):
    df = pd.read_csv(path, sep=r'\s+', header=None, names=COLS)
    df['regime'] = df.os1.round(0).astype(int) * 1000 + df.os3.round(0).astype(int)
    return df.sort_values(['unit', 'cycle']).reset_index(drop=True)


def load_dataset(name):
    """returns train df (with life, rul), official test df or None, official true RUL dict or None"""
    if name == 'PHM08':
        tr, te, true = _read('a/train.txt'), None, None
    else:
        tr = _read(f'cmapss/train_{name}.txt'); te = _read(f'cmapss/test_{name}.txt')
        r = np.loadtxt(f'cmapss/RUL_{name}.txt'); true = {u: float(r[i]) for i, u in enumerate(sorted(te.unit.unique()))}
    tr['life'] = tr.groupby('unit').cycle.transform('max'); tr['rul'] = tr.life - tr.cycle
    return tr, te, true


def outer_folds(units, k=5):
    return np.array_split(np.random.default_rng(2026).permutation(np.sort(units)), k)


def fit_cal_split(units, frac_cal=0.25):
    p = np.random.default_rng(7).permutation(np.sort(units)); n = int(round(frac_cal * len(p)))
    return np.sort(p[n:]), np.sort(p[:n])


def regime_norm(fit_df):
    st = {s: fit_df.groupby('regime')[s].agg(['mean', 'std']) for s in SENS7}
    def Z(df):
        out = np.column_stack([(df[s].values - df.regime.map(st[s]['mean']).values) / df.regime.map(st[s]['std']).values.clip(1e-6) for s in SENS7])
        return np.nan_to_num(out)
    return Z


def engines(df, Zfun):
    """dict unit -> (Z (T x 7), regime codes (T,), rul (T,) or None)"""
    out = {}
    Zall = Zfun(df)
    for u, idx in df.groupby('unit').indices.items():
        out[u] = (Zall[idx], df.regime.values[idx], df.rul.values[idx] if 'rul' in df else None)
    return out


# ------------------------------------------------------------------ cautious layer
class CautiousLayer:
    """Empirical distribution of the TRUE remaining life among the K calibration cases most similar in
    (point prediction, age); the cautious prediction is its q-quantile."""
    def __init__(self, K=200, age_scale=3.0):
        self.K, self.s = K, age_scale

    def fit(self, P, A, Y, U, L=None):
        from sklearn.neighbors import NearestNeighbors
        self.P, self.A, self.Y, self.U = map(np.asarray, (P, A, Y, U)); self.L = None if L is None else np.asarray(L)
        self.K = int(min(self.K, max(30, len(P) // 20)))
        self.nn = NearestNeighbors().fit(np.column_stack([self.P, self.A / self.s]))
        return self

    def quantiles(self, p, a, qs=QGRID, exclude_units=None):
        p, a = np.asarray(p, float), np.asarray(a, float)
        extra = 0 if exclude_units is None else 3 * self.K
        _, idx = self.nn.kneighbors(np.column_stack([p, a / self.s]), n_neighbors=min(self.K + extra, len(self.P)))
        out = np.zeros((len(p), len(qs)))
        for i, row in enumerate(idx):
            if exclude_units is not None: row = row[self.U[row] != exclude_units[i]]
            out[i] = np.quantile(self.Y[row[:self.K]], qs)
        return out

    def calibrate(self, target=LATE_TARGET, stride=2, mode='all'):
        """largest q whose late rate (error > +5) on the calibration engines (leave-own-engine-out) <= target.
        mode='all'  : late rate pooled over all cycles (version 1, pre-specified)
        mode='stage': late rate <= target in EVERY life-stage band 25-35, 45-55, 65-75, 85-95 % (version 2, amended)"""
        sel = np.arange(0, len(self.P), stride)
        Q = self.quantiles(self.P[sel], self.A[sel], exclude_units=self.U[sel])
        L = (Q - self.Y[sel, None]) > LATE_LIM
        if mode == 'all':
            late = L.mean(0)
        else:
            fr = self.A[sel] / self.L[sel]
            late = np.max([L[np.abs(fr - f) <= 0.05].mean(0) for f in FRACTIONS], axis=0)
        ok = np.where(late <= target)[0]
        self.q_index = int(ok.max()) if len(ok) else 0
        self.cal_late = late
        return QGRID[self.q_index]


def classify(err):
    return np.where(err < EARLY_LIM, 'EARLY', np.where(err > LATE_LIM, 'LATE', 'ON-TIME'))


def clopper_pearson(k, n, a=0.05):
    from scipy.stats import beta
    lo = 0.0 if k == 0 else beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - a / 2, k + 1, n - k)
    return lo, hi
