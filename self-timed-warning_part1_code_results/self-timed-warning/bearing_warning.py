"""Bearing confirmation of the self-timed warning model (FEMTO / PRONOSTIA), exactly as fixed in bearing/BEARING_PROTOCOL.md.
Part A: standard model + age-only + MLP/Kalman; Part B: theory-guided shift rule STW-T (method 'warning_T').
Inputs: bearing/femto_snapshot_features.csv.gz (bearing_extract.py). All model quantities in blocks of kappa snapshots.
Output: out/bearing/warning_results.csv, out/bearing/warning_summary.json
"""
import sys, os, json, numpy as np, pandas as pd
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
from sklearn.neural_network import MLPRegressor
from scipy.stats import binomtest, beta
import eol_window2 as W
from ncm_warning import kalman
from safe_common import outer_folds
from feats import causal_feats
from stwt import shift_T
FEAT = [f'{s}_{c}' for s in ('rms', 'peak', 'kurt', 'crest') for c in ('h', 'v')]
HS = [10, 15, 20]; RATIOS = [25, 100, 400]

def load():
    S = pd.read_csv('bearing/femto_snapshot_features.csv.gz').sort_values(['bearing', 'snapshot'])
    for f in FEAT:
        S[f] = S[f].where(np.isfinite(S[f])); S[f] = S.groupby('bearing')[f].transform(lambda s: s.ffill().bfill())
    L = S.groupby('bearing').snapshot.max(); assert (S.groupby('bearing').snapshot.count() == L).all()
    kappa = max(1, int(round(L.median() / 209.5)))
    S['block'] = (S.snapshot - 1) // kappa + 1; S['L'] = S.bearing.map(L); S = S[S.block <= S.L // kappa]
    B = S.groupby(['bearing', 'block']).agg({**{f: 'mean' for f in FEAT}, 'condition': 'first', 'set': 'first', 'L': 'first'}).reset_index()
    B['rul'] = (B.L - B.block * kappa) / kappa
    return B, kappa, L

def features(B, train_u):
    T = B[B.bearing.isin(train_u)]; pooled = (T[FEAT].mean(), T[FEAT].std().clip(1e-9)); F, Y = {}, {}
    st = {c: (g[FEAT].mean(), g[FEAT].std().clip(1e-9)) if g.bearing.nunique() >= 1 and len(g) > 1 else pooled for c, g in T.groupby('condition')}
    for u, g in B.groupby('bearing'):
        mu, sd = st.get(g.condition.iloc[0], pooled)
        F[u] = causal_feats(((g[FEAT] - mu) / sd).values); Y[u] = g.rul.values.astype(float)
    return F, Y

def predict(B, train_u, target_u):
    F, Y = features(B, train_u); X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u])
    out = {'warning': {}, 'age_only': {}, 'mlp_kf': {}}
    for cap in W.CAPS:
        m = W.gbm(X, y, cap); out['warning'][cap] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
        ma = W.gbm(X[:, -1:], y, cap); out['age_only'][cap] = {u: (ma.predict(F[u][:, -1:])[:-1], Y[u][:-1]) for u in target_u}
    mu, sd = X.mean(0), X.std(0) + 1e-9
    mlp = MLPRegressor(hidden_layer_sizes=(64, 32), alpha=1e-3, early_stopping=True, max_iter=200, random_state=0).fit((X - mu) / sd, np.minimum(y, 125) / 100)
    raw = {u: mlp.predict((F[u] - mu) / sd)[:-1] * 100 for u in target_u}
    for r in RATIOS: out['mlp_kf'][r] = {u: (kalman(p, 1.0, r), Y[u][:-1]) for u, p in raw.items()}
    return out

def run_split(B, name, train_u, test_u, seed):
    inner = np.array_split(np.random.default_rng(seed).permutation(train_u), 5); oof = None
    for iu in inner:
        if len(iu) == 0: continue
        p = predict(B, np.setdiff1d(train_u, iu), iu)
        if oof is None: oof = {m: {o: {} for o in p[m]} for m in p}
        for m in p:
            for o in p[m]: oof[m][o].update(p[m][o])
    final = predict(B, train_u, test_u); rows = []
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
            Pt = {u: (W.smooth(p, sp), y) for u, (p, y) in final[m][o].items()}
            rows.append(W.evaluate(Pt, H, k, s).assign(split=name, method=m, H=H, option=o, span=sp, k=k, shift=s))
            if m == 'warning':
                sT = shift_T({u: (W.smooth(p, sp), y) for u, (p, y) in oof[m][o].items()}, H, k, W.SHIFTS)
                rows.append(W.evaluate(Pt, H, k, sT).assign(split=name, method='warning_T', H=H, option=o, span=sp, k=k, shift=sT))
    return pd.concat(rows)

def summarise(A, kappa):
    out = []
    for (an, m, H), g in A.groupby(['analysis', 'method', 'H']):
        c = g.cls.value_counts(); n = len(g); k = int(c.get('IN', 0)); gv = g.dropna(subset=['pred'])
        out.append(dict(analysis=an, method=m, H=int(H), n=n, IN=k, pct=round(100 * k / n, 1),
                        ci=[round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0],
                        late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)), missed=int(c.get('MISSED', 0)),
                        median_left_blocks=float(gv.y.median()) if len(gv) else None, median_left_minutes=float(gv.y.median() * kappa * 10 / 60) if len(gv) else None,
                        median_error_blocks=float((gv.pred - gv.y).median()) if len(gv) else None))
    return out

def mcnemar(A, an, H, a, b):
    P = A[(A.analysis == an) & (A.H == H)]; Wd = P.pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'
    x = int((Wd[a] & ~Wd[b]).sum()); y = int((~Wd[a] & Wd[b]).sum())
    return dict(only_first=x, only_second=y, p=float(binomtest(x, x + y, 0.5).pvalue) if x + y else 1.0)

def main():
    B, kappa, L = load(); units = np.sort(B.bearing.unique()); os.makedirs('out/bearing', exist_ok=True)
    print(f'{len(units)} bearings, kappa = {kappa}, median life {L.median():.0f} snapshots, blocks per bearing {B.groupby("bearing").size().to_dict()}', flush=True)
    parts = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        parts.append(run_split(B, f'cv{fold}', np.setdiff1d(units, test_u), test_u, 100 + fold).assign(analysis='cv')); print('cv fold', fold, 'done', flush=True)
    tr = np.sort(B[B.set == 'Learning_set'].bearing.unique()); te = np.sort(B[B.set == 'Full_Test_Set'].bearing.unique())
    parts.append(run_split(B, 'official', tr, te, 106).assign(analysis='official')); print('official done', flush=True)
    A = pd.concat(parts); A['life_snapshots'] = A.unit.map(L); A['kappa'] = kappa; A.to_csv('out/bearing/warning_results.csv', index=False)
    summ = summarise(A, kappa); w = [s for s in summ if s['analysis'] == 'cv' and s['method'] == 'warning' and s['H'] == 20][0]
    hyp = {'F1_in_window_ge_85pct': dict(value=w['pct'], supported=w['pct'] >= 85),
           'F2_late_plus_missed_le_10pct': dict(value=round(100 * (w['late'] + w['missed']) / w['n'], 1), supported=(w['late'] + w['missed']) / w['n'] <= 0.10),
           'F3_vs_age_only': mcnemar(A, 'cv', 20, 'warning', 'age_only'), 'F4_vs_mlp_kf': mcnemar(A, 'cv', 20, 'warning', 'mlp_kf')}
    for h in ('F3_vs_age_only', 'F4_vs_mlp_kf'):
        hyp[h]['supported'] = bool(hyp[h]['p'] < 0.05 and hyp[h]['only_first'] > hyp[h]['only_second'])
    t = [s for s in summ if s['analysis'] == 'cv' and s['method'] == 'warning_T' and s['H'] == 20][0]
    hyp['T1_stwt_not_worse_by_5pts'] = dict(stwt=t['pct'], stw=w['pct'], supported=t['pct'] >= w['pct'] - 5, **mcnemar(A, 'cv', 20, 'warning_T', 'warning'))
    json.dump(dict(n_bearings=len(units), kappa=kappa, median_life=float(L.median()), summary=summ, hypotheses=hyp), open('out/bearing/warning_summary.json', 'w'), indent=1, default=float)
    print(pd.DataFrame(summ).drop(columns=['ci']).to_string(index=False)); print(json.dumps(hyp, indent=1, default=float))

if __name__ == '__main__':
    main()
