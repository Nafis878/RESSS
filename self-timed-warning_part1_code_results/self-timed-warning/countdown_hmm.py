"""
Countdown HMM for remaining-useful-life (RUL) on PHM08 — still a discrete HMM.

States
  r = 0 .. Rc-1 : "r cycles left"   (deterministic countdown r -> r-1)
  H             : "healthy, >= Rc cycles left"  (leaves H with an age-dependent
                  hazard learned from the training engines' lifetimes)
Observations
  one discrete symbol per cycle (1..M): a learned health index (ridge regression
  of all regime-normalised, engine-baseline-corrected sensors onto
  min(RUL, Rc)/Rc), cut into M quantile bins.
Inference
  forward filtering -> posterior over the current state -> full RUL distribution
  (H mass spread using the training life distribution given the engine's age)
Decision
  predicted RUL = value that minimises the EXPECTED PHM08 score under that
  distribution (so it is automatically cautious);  90% interval = 5th..95th pct.
"""
import numpy as np, pandas as pd

GRID = np.arange(0, 451)                     # RUL grid for decisions
_D = GRID[:, None] - GRID[None, :]           # pred - true
PHM = np.where(_D < 0, np.exp(-_D / 13) - 1, np.exp(_D / 10) - 1)   # PHM[p, r]

COLS = ['unit', 'cycle', 'os1', 'os2', 'os3'] + [f's{i}' for i in range(1, 22)]
SENS = [f's{i}' for i in range(1, 22)]


def load(path='a/train.txt'):
    df = pd.read_csv(path, sep=r'\s+', header=None, names=COLS)
    df['regime'] = df.os1.round(0).astype(int) * 1000 + df.os3.astype(int)
    df['life'] = df.groupby('unit').cycle.transform('max')
    df['rul'] = df.life - df.cycle
    return df


def phm_score(pred, true):
    d = np.asarray(pred, float) - np.asarray(true, float)
    return np.where(d < 0, np.exp(-d / 13) - 1, np.exp(d / 10) - 1)


class CountdownHMM:
    def __init__(self, Rc=130, M=20, beta=0.5, base=20, ridge=1.0, sigma_r=3.0,
                 bw_life=12.0, use_baseline=True, eps=0.0, mode='base', Ms=1, W=20):
        # Ms: number of slope bins (1 = level only); W: causal slope window (cycles)
        self.Ms, self.W = Ms, W
        # mode: 'abs'  -> absolute (regime-normalised) sensors
        #       'base' -> change since the engine's own first cycles
        #       'both' -> change since start AND the starting level (initial wear)
        self.mode = mode
        # eps: probability of a 'stay' and of a 'skip' step in the countdown, so the
        # chain can run slower / faster than 1 state per cycle (engine-specific pace)
        self.Rc, self.M, self.beta, self.base, self.eps = Rc, M, beta, base, eps
        self.ridge, self.sigma_r, self.bw_life, self.use_baseline = ridge, sigma_r, bw_life, use_baseline

    # ------------------------------------------------------------ features
    def _z(self, df):
        Z = np.zeros((len(df), len(self.sens)))
        for j, s in enumerate(self.sens):
            m = self.reg_stats[s]
            Z[:, j] = (df[s].values - df.regime.map(m['mean']).values) / df.regime.map(m['std']).values
        return Z

    def _feat(self, Z, t):
        """features for the prefix 1..t of one engine (baseline from first min(base,t) cycles)"""
        Z = Z[:t]; base = Z[:min(self.base, t)].mean(0)
        if self.mode == 'abs':  return Z
        if self.mode == 'base': return Z - base
        return np.hstack([Z - base, np.repeat(base[None], t, 0)])

    def _score_raw(self, eng):
        """per-engine regime-normalised sensor matrix (cycle order)"""
        return self._z(eng)

    def _hi_prefix(self, Z, t):
        return self.b0 + self._feat(Z, t) @ self.w

    def _slope(self, hi):
        """causal least-squares slope of hi over the last W cycles (per cycle)"""
        n = len(hi); out = np.zeros(n); W = self.W
        c0 = np.concatenate([[0], np.cumsum(hi)])
        c1 = np.concatenate([[0], np.cumsum(hi * np.arange(n))])
        for i in range(n):
            a = max(0, i - W + 1); k = i - a + 1
            if k < 5: continue
            x = np.arange(a, i + 1); sx, sxx = x.sum(), (x * x).sum()
            sy, sxy = c0[i + 1] - c0[a], c1[i + 1] - c1[a]
            out[i] = (k * sxy - sx * sy) / (k * sxx - sx * sx)
        return out

    def _symbols(self, hi):
        lvl = np.digitize(hi, self.edges)
        if self.Ms == 1: return lvl
        return lvl * self.Ms + np.digitize(self._slope(hi), self.sedges)

    # ------------------------------------------------------------ fit
    def fit(self, df):
        Rc = self.Rc
        # regime statistics per sensor, informative sensors only
        self.reg_stats, keep = {}, []
        for s in SENS:
            st = df.groupby('regime')[s].agg(['mean', 'std'])
            if (st['std'] > 1e-6).all():
                self.reg_stats[s] = st; keep.append(s)
        self.sens = keep
        # ridge regression health index
        Xs, ys, raw = [], [], {}
        for u, g in df.groupby('unit'):
            Z = self._z(g)
            Xs.append(self._feat(Z, len(Z))); ys.append(np.minimum(g.rul.values, Rc) / Rc)
        X = np.vstack(Xs); y = np.concatenate(ys)
        Xm, ym = X.mean(0), y.mean()
        Xc = X - Xm
        self.w = np.linalg.solve(Xc.T @ Xc + self.ridge * np.eye(X.shape[1]), Xc.T @ (y - ym))
        self.b0 = ym - Xm @ self.w                                   # hi = b0 + w.(z - base)
        # symbols
        his, ruls = [], []
        for u, g in df.groupby('unit'):
            Z = self._score_raw(g); hi = self._hi_prefix(Z, len(Z))
            his.append(hi); ruls.append(g.rul.values)
        hi_all = np.concatenate(his); rul_all = np.concatenate(ruls)
        self.Ml = self.M
        self.edges = np.quantile(hi_all, np.linspace(0, 1, self.Ml + 1)[1:-1])
        if self.Ms > 1:
            sl_all = np.concatenate([self._slope(h) for h in his])
            self.sedges = np.quantile(sl_all, np.linspace(0, 1, self.Ms + 1)[1:-1])
            sym = np.concatenate([self._symbols(h) for h in his])
        else:
            sym = self._symbols(hi_all)
        self.M = self.Ml * self.Ms
        # emissions: state index r (0..Rc-1) or Rc (=H); smoothed over r
        C = np.zeros((Rc + 1, self.M))
        st = np.minimum(rul_all, Rc)
        np.add.at(C, (st, sym), 1)
        rr = np.arange(Rc)
        K = np.exp(-0.5 * ((rr[:, None] - rr[None, :]) / self.sigma_r) ** 2)
        C[:Rc] = K @ C[:Rc]
        C += 0.5
        self.B = C / C.sum(1, keepdims=True)
        # life distribution (KDE) -> initial state and hazard of leaving H
        lives = df.groupby('unit').life.first().values
        L = np.arange(1, 1001)
        f = np.exp(-0.5 * ((L[:, None] - lives[None, :]) / self.bw_life) ** 2).sum(1)
        f /= f.sum(); self.L, self.fL = L, f
        S = np.cumsum(f[::-1])[::-1]                                   # P(life >= L)
        self.S = S
        return self

    def _life_pmf(self, L):
        return self.fL[L - 1] if 1 <= L <= 1000 else 0.0

    def _hazard(self, t):
        """P(leave H at t -> t+1 | in H at t) = P(life = t+Rc | life >= t+Rc)"""
        L = t + self.Rc
        if L > 1000: return 0.05
        s = self.S[L - 1]
        return float(np.clip(self.fL[L - 1] / s, 1e-5, 0.5)) if s > 1e-12 else 0.05

    # ------------------------------------------------------------ inference
    def filter(self, sym):
        """forward filtering; returns posterior (T x Rc+1) over states at each t"""
        Rc, T = self.Rc, len(sym)
        Bp = self.B ** self.beta                                     # tempered emissions
        a = np.zeros(Rc + 1)
        # initial: RUL at cycle 1 = life-1
        for r in range(Rc):
            a[r] = self._life_pmf(r + 1)
        a[Rc] = self.S[Rc] if Rc < 1000 else 0.0                       # life-1 >= Rc
        a = a / a.sum() * Bp[:, sym[0]]; a /= a.sum()
        out = np.zeros((T, Rc + 1)); out[0] = a
        for t in range(1, T):
            h = self._hazard(t)
            e = self.eps
            c = np.concatenate([a[:Rc], [0.0, 0.0]])           # countdown part, padded
            n = np.zeros(Rc + 1)
            n[:Rc] = (1 - 2 * e) * c[1:Rc + 1] + e * c[:Rc] + e * c[2:Rc + 2]
            n[0] += (1 - e) * a[0] + e * a[1]                   # 0 is absorbing
            n[Rc - 1] += a[Rc] * h
            n[Rc] = a[Rc] * (1 - h)
            n *= Bp[:, sym[t]]
            s = n.sum()
            a = n / s if s > 0 else np.full(Rc + 1, 1 / (Rc + 1))
            out[t] = a
        return out

    def rul_distribution(self, post_t, t):
        """full RUL pmf on GRID given state posterior after observing t cycles"""
        p = np.zeros(len(GRID))
        p[:self.Rc] = post_t[:self.Rc]
        # H: RUL = life - t with life >= t + Rc
        Ls = np.arange(t + self.Rc, t + len(GRID))
        w = np.array([self._life_pmf(L) for L in Ls])
        if w.sum() > 0:
            p[Ls - t] += post_t[self.Rc] * w / w.sum()
        else:
            p[self.Rc] += post_t[self.Rc]
        return p / p.sum()

    def predict_from_dist(self, p):
        exp_loss = PHM @ p
        pred = GRID[np.argmin(exp_loss)]
        c = np.cumsum(p)
        lo, hi = GRID[np.searchsorted(c, 0.05)], GRID[min(np.searchsorted(c, 0.95), len(GRID) - 1)]
        return pred, lo, hi

    def engine_scores_raw(self, eng):
        return self._score_raw(eng)

    def predict_prefix(self, s_raw, t, full_post=None):
        """RUL prediction after observing cycles 1..t of an engine"""
        if full_post is not None and t >= self.base:
            post = full_post[t - 1]
        else:
            sym = self._symbols(self._hi_prefix(s_raw, t))
            post = self.filter(sym)[-1]
        return self.predict_from_dist(self.rul_distribution(post, t))

    def full_posterior(self, s_raw):
        sym = self._symbols(self._hi_prefix(s_raw, len(s_raw)))
        return self.filter(sym)


# ---------------------------------------------------------------- evaluation
def make_cuts(lives, test_lengths, rng, per_engine=10):
    cuts = {}
    for u, life in lives.items():
        valid = test_lengths[test_lengths < life]
        k = min(per_engine, len(valid))
        cuts[u] = np.sort(rng.choice(valid, k, replace=False)) if k else np.array([], int)
    return cuts


def evaluate(model, df_eval, cuts, alarm_T=None, alarm_lead=5):
    rows, alarms = [], []
    for u, g in df_eval.groupby('unit'):
        g = g.sort_values('cycle'); life = len(g)
        s_raw = model.engine_scores_raw(g)
        post = model.full_posterior(s_raw)
        for t in cuts[u]:
            pred, lo, hi = model.predict_prefix(s_raw, int(t), post)
            rows.append(dict(unit=u, t=int(t), life=life, true_rul=life - int(t), pred=pred, lo=lo, hi=hi))
        if alarm_T is not None:
            fired = None
            for t in range(1, life + 1):
                pred, lo, hi = model.predict_prefix(s_raw, t, post)
                if pred <= alarm_T:
                    fired = t; break
            true_at_alarm = (life - fired) if fired else -1
            alarms.append(dict(unit=u, alarm_cycle=fired, true_rul_at_alarm=true_at_alarm,
                               in_time=true_at_alarm >= alarm_lead))
    return pd.DataFrame(rows), pd.DataFrame(alarms)


def criteria(res, alarms=None):
    e = res.pred - res.true_rul
    near = res.true_rul <= 50
    out = dict(n=len(res),
               C1_near_MAE=float(e[near].abs().mean()),
               C2_near_late_gt10=float((e[near] > 10).mean()),
               C4_score=float(phm_score(res.pred, res.true_rul).mean()),
               C5_coverage=float(((res.true_rul >= res.lo) & (res.true_rul <= res.hi)).mean()),
               RMSE=float(np.sqrt((e ** 2).mean())), MAE=float(e.abs().mean()),
               late_gt20=float((e > 20).mean()))
    if alarms is not None and len(alarms):
        out.update(C3_in_time=float(alarms.in_time.mean()),
                   C3_median_wasted=float(alarms.true_rul_at_alarm.median()))
    return out


# =====================================================================
# Two-fault-mode version: a single discrete HMM whose state is (fault mode, r).
# No transitions between modes; the forward pass infers the mode from the data.
# Observation = joint symbol of two health indices (one learned per fault mode),
# so both chains share ONE alphabet and their likelihoods are comparable.
# =====================================================================
from sklearn.cluster import KMeans


class MixtureCountdownHMM(CountdownHMM):
    def __init__(self, n_modes=2, Mq=6, **kw):
        super().__init__(**kw)
        self.n_modes, self.Mq = n_modes, Mq

    def _modes_from_signature(self, df):
        sig, us = [], []
        for u, g in df.groupby('unit'):
            Z = self._z(g); d = Z[-20:].mean(0) - Z[:20].mean(0)
            sig.append(d / np.linalg.norm(d)); us.append(u)
        km = KMeans(self.n_modes, n_init=20, random_state=0).fit(np.array(sig))
        return dict(zip(us, km.labels_))

    def _ridge(self, Xs, ys):
        X = np.vstack(Xs); y = np.concatenate(ys); Xm, ym = X.mean(0), y.mean(); Xc = X - Xm
        w = np.linalg.solve(Xc.T @ Xc + self.ridge * np.eye(X.shape[1]), Xc.T @ (y - ym))
        return w, ym - Xm @ w

    def _his(self, Z, t):
        F = self._feat(Z, t)
        return np.column_stack([b + F @ w for w, b in self.hi_models])

    def _joint_symbols(self, H):
        idx = [np.digitize(H[:, k], self.qedges[k]) for k in range(self.n_modes)]
        s = idx[0]
        for k in range(1, self.n_modes):
            s = s * self.Mq + idx[k]
        return s

    def fit(self, df):
        Rc = self.Rc
        self.reg_stats, keep = {}, []
        for s in SENS:
            st = df.groupby('regime')[s].agg(['mean', 'std'])
            if (st['std'] > 1e-6).all():
                self.reg_stats[s] = st; keep.append(s)
        self.sens = keep
        mode_of = self._modes_from_signature(df)
        self.mode_of_train = mode_of
        eng = {u: g.sort_values('cycle') for u, g in df.groupby('unit')}
        Zs = {u: self._z(g) for u, g in eng.items()}
        # one health index per fault mode
        self.hi_models = []
        for k in range(self.n_modes):
            Xs = [self._feat(Zs[u], len(Zs[u])) for u in eng if mode_of[u] == k]
            ys = [np.minimum(eng[u].rul.values, Rc) / Rc for u in eng if mode_of[u] == k]
            self.hi_models.append(self._ridge(Xs, ys))
        Hs = {u: self._his(Zs[u], len(Zs[u])) for u in eng}
        Hall = np.vstack(list(Hs.values()))
        self.qedges = [np.quantile(Hall[:, k], np.linspace(0, 1, self.Mq + 1)[1:-1]) for k in range(self.n_modes)]
        self.M = self.Mq ** self.n_modes
        # per-mode emissions and life distributions
        rr = np.arange(Rc); Kr = np.exp(-0.5 * ((rr[:, None] - rr[None, :]) / self.sigma_r) ** 2)
        L = np.arange(1, 1001); self.L = L
        self.Bk, self.fLk, self.Sk, self.prior = [], [], [], []
        for k in range(self.n_modes):
            us = [u for u in eng if mode_of[u] == k]
            C = np.zeros((Rc + 1, self.M))
            for u in us:
                np.add.at(C, (np.minimum(eng[u].rul.values, Rc), self._joint_symbols(Hs[u])), 1)
            C[:Rc] = Kr @ C[:Rc]; C += 0.5
            self.Bk.append(C / C.sum(1, keepdims=True))
            lives = np.array([len(eng[u]) for u in us])
            f = np.exp(-0.5 * ((L[:, None] - lives[None, :]) / self.bw_life) ** 2).sum(1); f /= f.sum()
            self.fLk.append(f); self.Sk.append(np.cumsum(f[::-1])[::-1]); self.prior.append(len(us) / len(eng))
        return self

    # --------------------------------------------------------- inference
    def _hazard_k(self, k, t):
        L = t + self.Rc
        if L > 1000: return 0.05
        s = self.Sk[k][L - 1]
        return float(np.clip(self.fLk[k][L - 1] / s, 1e-5, 0.5)) if s > 1e-12 else 0.05

    def filter(self, sym):
        Rc, T, K, e = self.Rc, len(sym), self.n_modes, self.eps
        Bp = [B ** self.beta for B in self.Bk]
        a = np.zeros((K, Rc + 1))
        for k in range(K):
            a[k, :Rc] = self.fLk[k][:Rc]                 # life = r+1
            a[k, Rc] = self.Sk[k][Rc]
            a[k] = a[k] / a[k].sum() * self.prior[k] * Bp[k][:, sym[0]]
        a /= a.sum()
        out = np.zeros((T, K, Rc + 1)); out[0] = a
        for t in range(1, T):
            n = np.zeros_like(a)
            for k in range(K):
                h = self._hazard_k(k, t); c = np.concatenate([a[k, :Rc], [0.0, 0.0]])
                n[k, :Rc] = (1 - 2 * e) * c[1:Rc + 1] + e * c[:Rc] + e * c[2:Rc + 2]
                n[k, 0] += (1 - e) * a[k, 0] + e * a[k, 1]
                n[k, Rc - 1] += a[k, Rc] * h
                n[k, Rc] = a[k, Rc] * (1 - h)
                n[k] *= Bp[k][:, sym[t]]
            s = n.sum()
            a = n / s if s > 0 else np.full_like(a, 1 / a.size)
            out[t] = a
        return out

    def rul_distribution(self, post_t, t):
        p = np.zeros(len(GRID))
        for k in range(self.n_modes):
            p[:self.Rc] += post_t[k, :self.Rc]
            Ls = np.arange(t + self.Rc, t + len(GRID))
            w = self.fLk[k][np.clip(Ls - 1, 0, 999)] * (Ls <= 1000)
            if w.sum() > 0: p[Ls - t] += post_t[k, self.Rc] * w / w.sum()
            else: p[self.Rc] += post_t[k, self.Rc]
        return p / p.sum()

    def predict_prefix(self, Z, t, full_post=None):
        if full_post is not None and t >= self.base:
            post = full_post[t - 1]
        else:
            post = self.filter(self._joint_symbols(self._his(Z, t)))[-1]
        return self.predict_from_dist(self.rul_distribution(post, t))

    def full_posterior(self, Z):
        return self.filter(self._joint_symbols(self._his(Z, len(Z))))
