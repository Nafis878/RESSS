"""Collect the revision experiments (out/rev) into paper2/numbers.json under key 'rev2' (the other keys are untouched)."""
import json, numpy as np, pandas as pd
from scipy.stats import binomtest, beta
import rev_analyze as RA

def cp(k, n):
    return [round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0]

T1, R = RA.window_tables(); T3, BT = RA.cost_tables()
out = {'datasets': RA.DS, 'repro': {r.dataset: bool(r.identical) for r in R.itertuples()}, 'window': {}, 'pooled': {}, 'cost': {}, 'boot': {}}
for r in T1.itertuples():
    d = out['window'].setdefault(r.dataset, {}).setdefault(str(r.H), {})
    d[r.method] = dict(IN=int(r.IN), n=int(r.n), pct=float(r.pct), ci=cp(int(r.IN), int(r.n)), late_missed=int(r.late_missed), early=int(r.early),
                       median_left=float(r.median_left), bind_pct=float(r.bind_pct))
    if r.method != 'STW':
        d[r.method].update(only_stw=int(r.only_STW), only_other=int(r.only_other), p=float(r.p))
ENG = [d for d in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'] if d in RA.DS]
for H in ['10', '15', '20', '30', '40']:
    for m in ['STW', 'STW_const', 'HI_threshold']:
        k = sum(out['window'][d][H][m]['IN'] for d in ENG); n = sum(out['window'][d][H][m]['n'] for d in ENG)
        out['pooled'].setdefault(H, {})[m] = dict(IN=k, n=n, pct=round(100 * k / n, 1))
    # pooled McNemar over the engine datasets
    a = b = 0
    for d in ENG:
        W = pd.read_csv(f'out/rev/{d}_window.csv'); g = W[W.H == int(H)]
        P = g.pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'
        a += int((P.STW & ~P.STW_const).sum()); b += int((~P.STW & P.STW_const).sum())
    out['pooled'][H]['const_vs_stw'] = dict(only_stw=a, only_const=b, p=float(binomtest(min(a, b), a + b, .5).pvalue) if a + b else 1.0)
for r in T3.itertuples():
    out['cost'].setdefault(r.dataset, {}).setdefault(f'{r.lead}|{r.rho}', {})[r.policy] = dict(ratio=float(r.rate_vs_pf), failures=int(r.failures), n=int(r.n))
for r in BT.itertuples():
    out['boot'].setdefault(r.dataset, {}).setdefault(f'{r.lead}|{r.rho}', {})[f'{r.a}|{r.b}'] = dict(ratio=float(r.ratio), lo=float(r.ci_lo), hi=float(r.ci_hi))
# summary counts used in the text: in how many (dataset, lead, rho) cells is STW_cost significantly cheaper than X
summ = {}
for pair in ['STW_window|HI_cost', 'STW_window|age', 'STW_window|STW_cost', 'STW_cost|HI_cost', 'STW_cost|age', 'HI_cost|age']:
    cells = [(d, k, v[pair]) for d, dd in out['boot'].items() for k, v in dd.items()]
    summ[pair] = dict(cells=len(cells), a_sig_better=sum(c[2]['hi'] < 1 for c in cells), b_sig_better=sum(c[2]['lo'] > 1 for c in cells),
                      a_point_better=sum(c[2]['ratio'] < 1 for c in cells),
                      lead0_a_sig_better=sum(c[2]['hi'] < 1 for c in cells if c[1].startswith('0|')), lead0_cells=sum(c[1].startswith('0|') for c in cells))
out['cost_summary'] = summ
N = json.load(open('paper2/numbers.json')); N['rev2'] = out
json.dump(N, open('paper2/numbers.json', 'w'), indent=1, default=float)
print(json.dumps({'repro': out['repro'], 'pooled': out['pooled'], 'cost_summary': summ}, indent=1))
# worked example for the text: PHM08, lead 10, rho 50
X = pd.read_csv('out/rev/PHM08_cost.csv'); x = X[(X.lead == 10) & (X.rho == 50)]
N = json.load(open('paper2/numbers.json'))
N['rev2']['example'] = {p: dict(fail=int(g.fail.sum()), med_lead=float(g.lead_true.median())) for p, g in x[x.policy.isin(['STW_cost', 'STW_window'])].groupby('policy')}
json.dump(N, open('paper2/numbers.json', 'w'), indent=1, default=float)
