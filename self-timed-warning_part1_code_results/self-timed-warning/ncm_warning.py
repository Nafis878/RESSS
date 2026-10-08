"""N-CMAPSS confirmation of the end-of-life warning model, exactly as fixed in ncm/WARNING_PROTOCOL.md.
Reuses the warning-rule code of eol_window2.py unchanged (gbm, smooth, evaluate, in_counts, CAPS, KS, SPANS, SHIFTS)."""
import json, numpy as np, pandas as pd
from sklearn.neural_network import MLPRegressor
from scipy.stats import binomtest, beta
import eol_window2 as W
from safe_common import outer_folds
from feats import causal_feats
SENS = ['T24', 'T30', 'T48', 'T50', 'Nf', 'Nc']; HS = [10, 15, 20]; RATIOS = [25, 100, 400]

def load():
    R = pd.read_csv('ncm/ncmapss_cycle_summary.csv.gz')
    key = R.subset + '|' + R.part + '|' + R.unit.astype(int).astype(str); ids = {k: i + 1 for i, k in enumerate(sorted(key.unique()))}
    R['uid'] = key.map(ids); R['regime'] = R.Fc.round().astype(int); R = R.sort_values(['uid', 'cycle']).reset_index(drop=True)
    R['life'] = R.groupby('uid').cycle.transform('max'); R['rul'] = R.life - R.cycle; assert np.allclose(R.rul, R.RUL)
    return R

def kalman(z, q, r):
    out = np.empty(len(z)); x, P = z[0], r
    for i, zi in enumerate(z):
        if i: x, P = x - 1.0, P + q
        K = P / (P + r); x = x + K * (zi - x); P = (1 - K) * P; out[i] = x
    return out

def features(D, stat_units):
    st = {s: D[D.uid.isin(stat_units)].groupby('regime')[s].agg(['mean', 'std']) for s in SENS}
    F, Y = {}, {}
    for u, g in D.groupby('uid'):
        Z = np.nan_to_num(np.column_stack([(g[s].values - g.regime.map(st[s]['mean']).values) / g.regime.map(st[s]['std']).values.clip(1e-6) for s in SENS]))
        F[u] = causal_feats(Z); Y[u] = g.rul.values.astype(float)
    return F, Y

def predict(D, train_u, target_u):
    """returns {method: {option: {unit: (raw prediction over cycles with RUL >= 1, true RUL)}}}"""
    F, Y = features(D, train_u); X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u])
    out = {'warning': {}, 'age_only': {}, 'mlp_kf': {}}
    for cap in W.CAPS:
        m = W.gbm(X, y, cap); out['warning'][cap] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
        ma = W.gbm(X[:, -1:], y, cap); out['age_only'][cap] = {u: (ma.predict(F[u][:, -1:])[:-1], Y[u][:-1]) for u in target_u}
    mu, sd = X.mean(0), X.std(0) + 1e-9
    mlp = MLPRegressor(hidden_layer_sizes=(64, 32), alpha=1e-3, early_stopping=True, max_iter=200, random_state=0).fit((X - mu) / sd, np.minimum(y, 125) / 100)
    raw = {u: mlp.predict((F[u] - mu) / sd)[:-1] * 100 for u in target_u}
    for r in RATIOS: out['mlp_kf'][r] = {u: (kalman(p, 1.0, r), Y[u][:-1]) for u, p in raw.items()}
    return out

def run_split(D, name, train_u, test_u, seed):
    inner = np.array_split(np.random.default_rng(seed).permutation(train_u), 5); oof = None
    for iu in inner:
        p = predict(D, np.setdiff1d(train_u, iu), iu)
        if oof is None: oof = {m: {o: {} for o in p[m]} for m in p}
        for m in p:
            for o in p[m]: oof[m][o].update(p[m][o])
    final = predict(D, train_u, test_u); rows = []
    for m in final:
        for H in HS:
            best = None
            for o in final[m]:
                if m != 'mlp_kf' and o < H + 20: continue
                for sp in W.SPANS:
                    Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[m][o].items()}
                    for k in W.KS:
                        tot = W.in_counts(Po, H, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                        if best is None or tot[j] > best[0]: best = (tot[j], o, sp, k, W.SHIFTS[j])
            _, o, sp, k, s = best
            R = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in final[m][o].items()}, H, k, s)
            rows.append(R.assign(split=name, method=m, H=H, option=o, span=sp, k=k, shift=s))
    return pd.concat(rows)

def main():
    D = load(); units = np.sort(D.uid.unique()); dev = np.sort(D[D.part == 'dev'].uid.unique()); tst = np.sort(D[D.part == 'test'].uid.unique())
    parts = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        parts.append(run_split(D, f'cv{fold}', np.setdiff1d(units, test_u), test_u, 100 + fold)); print('fold', fold, 'done', flush=True)
    parts.append(run_split(D, 'official', dev, tst, 106)); print('official done', flush=True)
    A = pd.concat(parts); A['primary'] = A.split.str.startswith('cv'); A.to_csv('out/ncm/warning_results.csv', index=False)
    summ = []
    for (prim, m, H), g in A.groupby(['primary', 'method', 'H']):
        c = g.cls.value_counts(); n = len(g); k = int(c.get('IN', 0))
        summ.append(dict(split='cv (primary)' if prim else 'official', method=m, H=H, n=n, IN=k, pct=round(100 * k / n, 1),
                         ci=[round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0],
                         late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)), missed=int(c.get('MISSED', 0)),
                         median_true_left=float(g.y.median()), median_error=float((g.pred - g.y).median())))
    P = A[A.primary & (A.H == 20)]; Wd = P.pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'
    def mcn(a, b):
        x = int((Wd[a] & ~Wd[b]).sum()); y = int((~Wd[a] & Wd[b]).sum()); return dict(only_warning=x, only_other=y, p=binomtest(x, x + y, 0.5).pvalue if x + y else 1.0)
    w = [s for s in summ if s['split'].startswith('cv') and s['method'] == 'warning' and s['H'] == 20][0]
    hyp = {'W1_in_window_ge_85pct': dict(value=w['pct'], supported=w['pct'] >= 85),
           'W2_late_plus_missed_le_10pct': dict(value=round(100 * (w['late'] + w['missed']) / w['n'], 1), supported=(w['late'] + w['missed']) / w['n'] <= 0.10),
           'W3_vs_age_only': dict(**mcn('warning', 'age_only')), 'W4_vs_mlp_kf': dict(**mcn('warning', 'mlp_kf'))}
    for h in ('W3_vs_age_only', 'W4_vs_mlp_kf'):
        hyp[h]['supported'] = bool(hyp[h]['p'] < 0.05 and hyp[h]['only_warning'] > hyp[h]['only_other'])
    json.dump(dict(summary=summ, hypotheses=hyp), open('out/ncm/warning_summary.json', 'w'), indent=1, default=float)
    print(pd.DataFrame(summ).to_string(index=False)); print(json.dumps(hyp, indent=1, default=float))

if __name__ == '__main__':
    main()
