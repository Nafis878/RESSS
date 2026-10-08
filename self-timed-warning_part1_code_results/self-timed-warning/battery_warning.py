"""Battery confirmation of the self-timed warning model, exactly as fixed in battery/BATTERY_PROTOCOL.md (incl. Deviations D1-D3).

Data: Severson et al. (2019) per-cycle summaries (battery/severson_cycle_summary.csv.gz, battery/severson_cells.csv).
Reuses the model and warning-rule code of eol_window2.py / ncm_warning.py unchanged (gbm, smooth, evaluate, in_counts,
CAPS, KS, SPANS, SHIFTS, kalman). All model quantities are in blocks of kappa cycles.
Splits: primary 5-fold CV by cell (outer_folds, seed 2026; inner seed 100 + fold); secondary leave-one-batch-out (inner seed
100 + batch) and 5-fold CV on the 119-cell set without the providers' four 'noisy' channels.
Output: out/battery/warning_results.csv, out/battery/warning_summary.json
"""
import sys, os, json, numpy as np, pandas as pd
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
from sklearn.neural_network import MLPRegressor
from scipy.stats import binomtest, beta
import eol_window2 as W
from ncm_warning import kalman
from safe_common import outer_folds
from feats import causal_feats
FEAT = ['QDischarge', 'QCharge', 'IR', 'Tavg', 'Tmin', 'Tmax', 'chargetime']
RANGES = {'QDischarge': (0.5, 1.2, True), 'QCharge': (0.5, 1.2, True), 'IR': (0.0, 0.05, False), 'Tavg': (15, 60, True),
          'Tmin': (15, 60, True), 'Tmax': (15, 60, True), 'chargetime': (0.0, 200.0, False)}   # (lo, hi, lo inclusive)
SPLIT_CELLS = ['b1c0', 'b1c1', 'b1c2', 'b1c3', 'b1c4', 'b2c7', 'b2c8', 'b2c9', 'b2c15', 'b2c16']          # D2
NO_EOL = ['b1c8', 'b1c10', 'b1c12', 'b1c13', 'b1c22']                                                     # D3
NOISY = ['b3c2', 'b3c37', 'b3c42', 'b3c43']                                                               # secondary set
HS = [10, 15, 20]; RATIOS = [25, 100, 400]

def load():
    S = pd.read_csv('battery/severson_cycle_summary.csv.gz'); M = pd.read_csv('battery/severson_cells.csv').set_index('cell')
    keep = []
    for c, g in S.groupby('cell'):
        L = M.cycle_life_official[c]
        if not np.isfinite(L) or c in SPLIT_CELLS or c in NO_EOL: continue
        cyc = np.sort(g.cycle.values); L = int(L)
        assert cyc[0] == 1 and np.all(np.diff(cyc) == 1) and cyc[-1] >= L - 1, c          # D1 completeness
        keep.append(c)
    S = S[S.cell.isin(keep)].sort_values(['cell', 'cycle']).copy()
    S['L'] = S.cell.map(M.cycle_life_official).astype(int); S = S[S.cycle <= S.L]                   # rows after L discarded
    for f, (lo, hi, inc) in RANGES.items():
        v = S[f].astype(float); ok = np.isfinite(v) & (v <= hi) & ((v >= lo) if inc else (v > lo))
        S[f] = v.where(ok); S[f] = S.groupby('cell')[f].transform(lambda s: s.ffill().bfill())
    assert S[FEAT].notna().all().all()
    Lc = S.groupby('cell').L.first(); kappa = max(1, int(round(Lc.median() / 209.5)))
    S['block'] = (S.cycle - 1) // kappa + 1; S = S[S.block <= S.L // kappa]
    B = S.groupby(['cell', 'block'])[FEAT].mean().reset_index(); B['L'] = B.cell.map(Lc)
    B['rul'] = (B.L - B.block * kappa) / kappa; B['batch'] = B.cell.str[1].astype(int)
    return B, kappa, Lc

def features(B, stat_cells):
    mu = B[B.cell.isin(stat_cells)][FEAT].mean(); sd = B[B.cell.isin(stat_cells)][FEAT].std().clip(1e-9)
    F, Y = {}, {}
    for c, g in B.groupby('cell'):
        F[c] = causal_feats(((g[FEAT] - mu) / sd).values); Y[c] = g.rul.values.astype(float)
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
            R = W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in final[m][o].items()}, H, k, s)
            rows.append(R.assign(split=name, method=m, H=H, option=o, span=sp, k=k, shift=s))
    return pd.concat(rows)

def summarise(A, kappa, Lc):
    summ = []
    for (an, m, H), g in A.groupby(['analysis', 'method', 'H']):
        c = g.cls.value_counts(); n = len(g); k = int(c.get('IN', 0))
        summ.append(dict(analysis=an, method=m, H=H, n=n, IN=k, pct=round(100 * k / n, 1),
                         ci=[round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0],
                         late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)), missed=int(c.get('MISSED', 0)),
                         median_true_left_blocks=float(g.y.median()), median_true_left_cycles=float(g.y.median() * kappa),
                         median_error_blocks=float((g.pred - g.y).median())))
    return summ

def mcnemar(A, an, H, a, b):
    P = A[(A.analysis == an) & (A.H == H)]; Wd = P.pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'
    x = int((Wd[a] & ~Wd[b]).sum()); y = int((~Wd[a] & Wd[b]).sum())
    return dict(only_warning=x, only_other=y, p=float(binomtest(x, x + y, 0.5).pvalue) if x + y else 1.0)

def main():
    B, kappa, Lc = load(); cells = np.sort(B.cell.unique()); os.makedirs('out/battery', exist_ok=True)
    print(f'{len(cells)} cells, kappa = {kappa}, median life {Lc.median():.0f} cycles, blocks per cell median {B.groupby("cell").size().median():.0f}', flush=True)
    parts = []
    for fold, test_u in enumerate(outer_folds(cells), 1):
        parts.append(run_split(B, f'cv{fold}', np.setdiff1d(cells, test_u), test_u, 100 + fold).assign(analysis='cv123')); print('cv fold', fold, 'done', flush=True)
    for b in (1, 2, 3):
        test_u = np.sort(B[B.batch == b].cell.unique())
        parts.append(run_split(B, f'lobo{b}', np.setdiff1d(cells, test_u), test_u, 100 + b).assign(analysis='lobo')); print('lobo', b, 'done', flush=True)
    c119 = np.setdiff1d(cells, NOISY); B119 = B[B.cell.isin(c119)]
    for fold, test_u in enumerate(outer_folds(c119), 1):
        parts.append(run_split(B119, f'cv119_{fold}', np.setdiff1d(c119, test_u), test_u, 100 + fold).assign(analysis='cv119')); print('cv119 fold', fold, 'done', flush=True)
    A = pd.concat(parts); A['life_cycles'] = A.unit.map(Lc); A['kappa'] = kappa; A.to_csv('out/battery/warning_results.csv', index=False)
    summ = summarise(A, kappa, Lc)
    w = [s for s in summ if s['analysis'] == 'cv123' and s['method'] == 'warning' and s['H'] == 20][0]
    hyp = {'B1_in_window_ge_85pct': dict(value=w['pct'], supported=w['pct'] >= 85),
           'B2_late_plus_missed_le_10pct': dict(value=round(100 * (w['late'] + w['missed']) / w['n'], 1), supported=(w['late'] + w['missed']) / w['n'] <= 0.10),
           'B3_vs_age_only': mcnemar(A, 'cv123', 20, 'warning', 'age_only'), 'B4_vs_mlp_kf': mcnemar(A, 'cv123', 20, 'warning', 'mlp_kf')}
    for h in ('B3_vs_age_only', 'B4_vs_mlp_kf'):
        hyp[h]['supported'] = bool(hyp[h]['p'] < 0.05 and hyp[h]['only_warning'] > hyp[h]['only_other'])
    sec = {f'{an}_H{H}_vs_{o}': mcnemar(A, an, H, 'warning', o) for an in ('cv123', 'lobo', 'cv119') for H in HS for o in ('age_only', 'mlp_kf')}
    json.dump(dict(n_cells=len(cells), kappa=kappa, median_life=float(Lc.median()), summary=summ, hypotheses=hyp, secondary_mcnemar=sec),
              open('out/battery/warning_summary.json', 'w'), indent=1, default=float)
    print(pd.DataFrame(summ).drop(columns=['ci']).to_string(index=False)); print(json.dumps(hyp, indent=1, default=float))

if __name__ == '__main__':
    main()
