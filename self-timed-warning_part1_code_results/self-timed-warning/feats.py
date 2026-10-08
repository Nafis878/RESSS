import numpy as np, pandas as pd
from countdown_hmm import load, SENS

def regime_stats(df):
    st = {}; keep = []
    for s in SENS:
        g = df.groupby('regime')[s].agg(['mean', 'std'])
        if (g['std'] > 1e-6).all(): st[s] = g; keep.append(s)
    return st, keep

def zmat(g, st, keep):
    return np.column_stack([(g[s].values - g.regime.map(st[s]['mean']).values) / g.regime.map(st[s]['std']).values for s in keep])

def causal_feats(Z, base=20):
    """per-cycle causal features for one engine prefix (uses only cycles <= i)"""
    n, p = Z.shape
    b = np.array([Z[:min(base, i + 1)].mean(0) for i in range(n)])      # baseline at each time
    zc = Z - b
    df = pd.DataFrame(zc)
    feats = [df.ewm(span=10).mean().values, df.ewm(span=30).mean().values, b]
    for W in (15, 40):
        sl = np.zeros((n, p))
        for i in range(n):
            a = max(0, i - W + 1)
            if i - a + 1 >= 5:
                x = np.arange(a, i + 1); x = x - x.mean()
                sl[i] = x @ (Z[a:i + 1] - Z[a:i + 1].mean(0)) / (x @ x)
        feats.append(pd.DataFrame(sl).ewm(span=5).mean().values)
    age = np.arange(1, n + 1)[:, None]
    return np.hstack(feats + [age])
