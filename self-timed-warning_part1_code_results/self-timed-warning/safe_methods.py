"""Point models. Each: fit(E_fit) with E = {unit: (Z, regimes, rul)}; predict(Z, regimes) -> point RUL after every cycle
(causal: the value at cycle t uses cycles 1..t only)."""
import os, numpy as np, pandas as pd
import numba as nb


# ------------------------------------------------------------------ 1. age only (no sensors)
class AgeOnly:
    name = 'Age-only (no sensors)'
    def fit(self, E):
        self.lives = np.array([len(v[0]) for v in E.values()]); return self
    def predict(self, Z, reg):
        t = np.arange(1, len(Z) + 1)
        return np.array([np.mean(self.lives[self.lives > s] - s) if (self.lives > s).any() else 1.0 for s in t])


# ------------------------------------------------------------------ 2. gradient-boosted trees on causal features
def _roll_slope_expanding(Y):
    n, p = Y.shape; t = np.arange(n, dtype=float); out = np.zeros((n, p))
    c1 = np.cumsum(Y, 0); ct = np.cumsum(t); ctt = np.cumsum(t * t); cty = np.cumsum(Y * t[:, None], 0)
    k = np.arange(1, n + 1, dtype=float)[:, None]
    den = k * ctt[:, None] - ct[:, None] ** 2
    with np.errstate(divide='ignore', invalid='ignore'):
        out = np.where(den > 0, (k * cty - ct[:, None] * c1) / den, 0.0)
    out[:4] = 0.0
    return out

def gbm_features(Z):
    n = len(Z); b = np.array([Z[:min(20, i + 1)].mean(0) for i in range(n)]); Yc = Z - b
    D, Dc = pd.DataFrame(Z), pd.DataFrame(Yc)
    lvl = Dc.expanding().mean().values; sd = D.expanding(min_periods=2).std().fillna(0).values
    recent = Dc.ewm(span=5).mean().values; hi = recent.mean(1, keepdims=True)
    return np.hstack([recent, lvl, _roll_slope_expanding(Z), sd, hi, np.arange(1, n + 1)[:, None], b])

class GBM:
    name = 'Gradient-boosted trees (ours)'
    def fit(self, E):
        from sklearn.ensemble import HistGradientBoostingRegressor
        X = np.vstack([gbm_features(v[0]) for v in E.values()]); y = np.concatenate([v[2] for v in E.values()])
        self.m = HistGradientBoostingRegressor(loss='absolute_error', max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
                                               min_samples_leaf=40, random_state=0).fit(X, y)
        return self
    def predict(self, Z, reg):
        return self.m.predict(gbm_features(Z))


# ------------------------------------------------------------------ 3. IOHMM (thesis-style, corrected normalisation)
@nb.njit(cache=True)
def _fb(obs, reg, A, B, pi, N):
    """scaled forward-backward for one sequence of an input-output left-right HMM with absorbing failure.
    A[r] is N x (N+1): column N = probability of failing after the current cycle under input r.
    A single set of scale factors (from the forward pass) is used in both passes."""
    T = len(obs); al = np.zeros((T, N)); be = np.zeros((T, N)); c = np.zeros(T)
    for i in range(N): al[0, i] = pi[i] * B[i, obs[0]]
    c[0] = al[0].sum(); al[0] /= c[0]
    for t in range(1, T):
        r = reg[t - 1]
        for j in range(N):
            s = 0.0
            for i in range(N): s += al[t - 1, i] * A[r, i, j]
            al[t, j] = s * B[j, obs[t]]
        c[t] = al[t].sum(); al[t] /= c[t]
    rT = reg[T - 1]; d = 0.0
    for i in range(N): d += al[T - 1, i] * A[rT, i, N]
    for i in range(N): be[T - 1, i] = A[rT, i, N] / d
    for t in range(T - 2, -1, -1):
        r = reg[t]
        for i in range(N):
            s = 0.0
            for j in range(N): s += A[r, i, j] * B[j, obs[t + 1]] * be[t + 1, j]
            be[t, i] = s / c[t + 1]
    loglik = np.log(c).sum() + np.log(d)
    return al, be, c, d, loglik

@nb.njit(cache=True)
def _accumulate(obs, reg, A, B, pi, N, M, numA, denA, numB):
    al, be, c, d, ll = _fb(obs, reg, A, B, pi, N); T = len(obs)
    for t in range(T):
        g = al[t] * be[t]; g /= g.sum(); r = reg[t]
        for i in range(N):
            denA[r, i] += g[i]; numB[i, obs[t]] += g[i]
        if t < T - 1:
            for i in range(N):
                for j in range(N):
                    numA[r, i, j] += al[t, i] * A[r, i, j] * B[j, obs[t + 1]] * be[t + 1, j] / c[t + 1]
        else:
            for i in range(N): numA[r, i, N] += g[i]
    return ll

@nb.njit(cache=True)
def _filter(obs, reg, A, B, pi, N):
    T = len(obs); al = np.zeros((T, N))
    for i in range(N): al[0, i] = pi[i] * B[i, obs[0]]
    al[0] /= al[0].sum()
    for t in range(1, T):
        r = reg[t - 1]
        for j in range(N):
            s = 0.0
            for i in range(N): s += al[t - 1, i] * A[r, i, j]
            al[t, j] = s * B[j, obs[t]]
        tot = al[t].sum()
        if tot > 0: al[t] /= tot
        else: al[t] = al[t - 1]
    return al

class IOHMM:
    """3 left-right health states (good / degrading / bad), one transition matrix per operating regime (input),
    4 discrete symbols of the first principal component of the normalised sensors (the thesis's health indicator),
    RUL = expected number of cycles until absorption in the failure state, with future regimes drawn from their
    training frequencies (the thesis's mean-time-to-failure prognosis, Eq. 31-33)."""
    name = 'IOHMM (thesis method, corrected)'
    def __init__(self, N=3, M=4, n_iter=40): self.N, self.M, self.n_iter = N, M, n_iter
    def _sym(self, Z): return np.digitize((Z - self.mu) @ self.v, self.edges).astype(np.int64)
    def fit(self, E):
        N, M = self.N, self.M
        X = np.vstack([v[0] for v in E.values()]); self.mu = X.mean(0)
        v = np.linalg.svd(X - self.mu, full_matrices=False)[2][0]
        age = np.concatenate([np.arange(len(e[0])) / len(e[0]) for e in E.values()])
        if np.corrcoef((X - self.mu) @ v, age)[0, 1] < 0: v = -v
        self.v = v; self.edges = np.quantile((X - self.mu) @ v, np.linspace(0, 1, M + 1)[1:-1])
        codes = np.unique(np.concatenate([e[1] for e in E.values()])); self.rmap = {c: i for i, c in enumerate(codes)}; R = len(codes)
        seqs = [(self._sym(e[0]), np.array([self.rmap[c] for c in e[1]], dtype=np.int64)) for e in E.values()]
        self.pr = np.bincount(np.concatenate([s[1] for s in seqs]), minlength=R) / sum(len(s[1]) for s in seqs)
        # initialise from equal thirds of life
        numA = np.full((R, N, N + 1), 1e-3); numB = np.full((N, M), 1.0)
        for o, r in seqs:
            st = np.minimum((np.arange(len(o)) * N) // len(o), N - 1)
            for t in range(len(o)):
                numB[st[t], o[t]] += 1
                if t < len(o) - 1: numA[r[t], st[t], st[t + 1]] += 1
                else: numA[r[t], st[t], N] += 1
        mask = np.zeros((N, N + 1))
        for i in range(N): mask[i, i] = 1; mask[i, i + 1] = 1          # stay or move one step; last state -> failure
        A = numA * mask; A /= A.sum(2, keepdims=True); B = numB / numB.sum(1, keepdims=True); pi = np.zeros(N); pi[0] = 1.0
        prev = -np.inf
        for it in range(self.n_iter):
            nA = np.zeros((R, N, N + 1)); dA = np.zeros((R, N)); nB = np.zeros((N, M)); ll = 0.0
            for o, r in seqs: ll += _accumulate(o, r, A, B, pi, N, M, nA, dA, nB)
            A = (nA + 1e-6 * mask) * mask; A /= A.sum(2, keepdims=True); B = (nB + 1e-3) / (nB + 1e-3).sum(1, keepdims=True)
            if ll - prev < 1e-4 * abs(ll): break
            prev = ll
        self.A, self.B, self.pi, self.loglik, self.iters = A, B, pi, ll, it + 1
        Q = np.tensordot(self.pr, A, 1)[:, :N]                              # average over future regimes
        self.m = np.linalg.solve(np.eye(N) - Q, np.ones(N))                   # expected steps to failure from each state
        return self
    def predict(self, Z, reg):
        r = np.array([self.rmap.get(c, 0) for c in reg], dtype=np.int64)
        al = _filter(self._sym(Z), r, self.A, self.B, self.pi, self.N)
        return al @ self.m - 1.0


# ------------------------------------------------------------------ 4/5. CNN (Li et al. 2018) and LSTM (Zheng et al. 2017)
class DeepNet:
    def __init__(self, kind, w=30, cap=125, stride=2, max_epochs=60, seed=0):
        self.kind, self.w, self.cap, self.stride, self.max_epochs, self.seed = kind, w, cap, stride, max_epochs, seed
        self.name = {'cnn': 'CNN (Li et al. 2018)', 'lstm': 'LSTM (Zheng et al. 2017)'}[kind]
    def _win(self, Z):
        P = np.vstack([np.repeat(Z[:1], self.w - 1, 0), Z])                 # left-pad so every cycle has a window
        return np.lib.stride_tricks.sliding_window_view(P, (self.w, Z.shape[1]))[:, 0]
    def fit(self, E):
        os.environ.setdefault('KERAS_BACKEND', 'jax'); import keras; from keras import layers
        keras.utils.set_random_seed(self.seed)
        units = np.array(sorted(E)); val = np.random.default_rng(self.seed).choice(units, max(1, len(units) // 10), replace=False)
        def mk(us):
            X = [self._win(E[u][0])[::self.stride] for u in us]; y = [np.minimum(E[u][2], self.cap)[::self.stride] / self.cap for u in us]
            return np.concatenate(X).astype('float32'), np.concatenate(y).astype('float32')
        Xtr, ytr = mk(np.setdiff1d(units, val)); Xva, yva = mk(val); p = Xtr.shape[2]; inp = keras.Input((self.w, p))
        if self.kind == 'cnn':
            x = inp
            for _ in range(4): x = layers.Conv1D(10, 10, padding='same', activation='tanh')(x)
            x = layers.Conv1D(1, 3, padding='same', activation='tanh')(x)
            x = layers.Flatten()(x); x = layers.Dropout(0.5)(x); x = layers.Dense(100, activation='tanh')(x)
        else:
            x = layers.LSTM(64, return_sequences=True)(inp); x = layers.Dropout(0.2)(x)
            x = layers.LSTM(64)(x); x = layers.Dropout(0.2)(x)
            x = layers.Dense(8, activation='relu')(x); x = layers.Dense(8, activation='relu')(x)
        m = keras.Model(inp, layers.Dense(1)(x)); m.compile(keras.optimizers.Adam(1e-3), 'mse')
        h = m.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=self.max_epochs, batch_size=512, verbose=0,
                  callbacks=[keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True),
                             keras.callbacks.ReduceLROnPlateau(factor=0.1, patience=5, min_lr=1e-5)])
        self.m, self.epochs = m, len(h.history['loss']); return self
    def predict(self, Z, reg):
        return np.clip(self.m.predict(self._win(Z).astype('float32'), verbose=0, batch_size=4096).ravel() * self.cap, 0, None)


def make(name, dataset):
    w = {'FD002': 21, 'FD004': 19}.get(dataset, 30)
    return {'age': AgeOnly, 'gbm': GBM, 'iohmm': IOHMM}.get(name, lambda: DeepNet(name, w=w))()
