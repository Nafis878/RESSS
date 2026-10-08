"""Summarise the audit reruns (audit_confirmations.py, audit_battery_controls.py, audit_cost.py, audit_fixed_time.py) into
paper3/numbers.json: the numbers of the submitted version (paper2/numbers.json) plus the key 'rev3'.
Usage: python audit_summarize.py            (reads the fresh outputs in out/audit)
       python audit_summarize.py --frozen   (reads the frozen outputs in results/audit)
Also writes plain tables to out/audit/tables/ and checks the reproduction of earlier results where the rerun should
reproduce them exactly (engine datasets: window-tuned, cost-tuned, health-indicator and age policies)."""
import os, json, pickle, glob, gzip
import numpy as np, pandas as pd
from scipy.stats import binomtest, beta

import sys
A = 'results/audit' if '--frozen' in sys.argv else 'out/audit'


def F_(name):
    """path of an audit output, plain or gzip-compressed; None if absent"""
    for c in (f'{A}/{name}', f'{A}/{name}.gz'):
        if os.path.exists(c): return c
    return None
DS = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'Battery']
POL = ['STW_window', 'STW_cost', 'STW_cost_1se', 'STW_cost_q80', 'Q10_cost', 'Q10_cost_1se', 'HI_cost', 'capacity_cost', 'capacity_cost_1se', 'age']


def cp(k, n):
    return [round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0]


def summ(g):
    n = len(g); c = g.cls.value_counts(); k = int(c.get('IN', 0)); gv = g.dropna(subset=['pred'])
    return dict(IN=k, n=n, pct=round(100 * k / n, 1), ci=cp(k, n), late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)), missed=int(c.get('MISSED', 0)),
                median_left=float(gv.y.median()) if len(gv) else None,
                median_left_units=float((gv.y * gv.kappa).median()) if len(gv) and 'kappa' in gv else None,
                limit_active_pct=round(100 * float((gv.y >= 13).mean()), 1) if len(gv) else None)


def mcn(a, b):
    x = int((a & ~b).sum()); y = int((~a & b).sum())
    return dict(only_a=x, only_b=y, p=float(binomtest(min(x, y), x + y, .5).pvalue) if x + y else 1.0)


def holm(ps):
    o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (m - r) * ps[i])); adj[i] = run
    return adj.tolist()


R3 = {}
# ------------------------------------------------------------------ confirmations with training-only kappa
for name, f, orig, unitcol in [('battery', F_('battery_corrected.csv'), 'results/battery/warning_results.csv', 'cv123'),
                               ('bearing', F_('bearing_corrected.csv'), 'results/bearing/warning_results.csv', 'cv')]:
    if f is None: continue
    C = pd.read_csv(f); O = pd.read_csv(orig); out = {'kappa': C.drop_duplicates('split').set_index('split').kappa.astype(int).to_dict(), 'summary': {}}
    for (an, m, H), g in C.groupby(['analysis', 'method', 'H']):
        out['summary'][f'{an}|{m}|{int(H)}'] = summ(g)
    prim = unitcol
    P = C[(C.analysis == prim) & (C.H == 20)].pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'
    w = out['summary'][f'{prim}|warning|20']
    out['hyp'] = {'in_window_ge_85': dict(value=w['pct'], supported=w['pct'] >= 85),
                  'late_missed_le_10': dict(value=round(100 * (w['late'] + w['missed']) / w['n'], 1), supported=(w['late'] + w['missed']) / w['n'] <= .10)}
    for o in ('age_only', 'mlp_kf'):
        r = mcn(P['warning'], P[o]); r['supported'] = bool(r['p'] < .05 and r['only_a'] > r['only_b']); out['hyp'][f'vs_{o}'] = r
    # splits whose corrected kappa equals the original one: are the warnings identical?
    same = {}
    for sp, g in C.groupby('split'):
        go = O[O.split == sp]
        if len(go) == 0: continue
        mm = g.merge(go, on=['unit', 'method', 'H'], suffixes=('', '_o'))
        same[sp] = bool(len(mm) == len(g) and (mm.cls == mm.cls_o).all() and np.allclose(mm.pred.fillna(-9), mm.pred_o.fillna(-9)))
    out['identical_to_original'] = same
    ps = {}
    for sp, g in C[C.H == 20].groupby('split'):
        ps[sp] = {m: summ(h) for m, h in g.groupby('method')}; ps[sp]['kappa'] = int(g.kappa.iloc[0])
        go = O[(O.split == sp) & (O.H == 20) & (O.method == 'warning')]; ps[sp]['protocol_IN'] = int((go.cls == 'IN').sum()); ps[sp]['protocol_kappa'] = int(O.kappa.iloc[0])
    out['per_split'] = ps
    sec = {}
    for an in C.analysis.unique():
        P2 = C[(C.analysis == an) & (C.H == 20)].pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'
        for o in [m for m in P2.columns if m != 'warning']: sec[f'{an}|{o}'] = mcn(P2['warning'], P2[o])
    out['mcnemar_H20'] = sec
    R3[name] = out

# ------------------------------------------------------------------ sensitivity to the block length (physical task fixed)
for name, f, scale in [('battery_sens', F_('battery_sensitivity.csv'), 'cycles'), ('bearing_sens', F_('bearing_sensitivity.csv'), 'snapshots')]:
    if f is None: continue
    S = pd.read_csv(f); R3[name] = {}
    for kap, g in S.groupby('kappa'):
        s = summ(g); s['median_left_' + scale] = s['median_left'] * kap if s['median_left'] is not None else None; R3[name][str(int(kap))] = s

# ------------------------------------------------------------------ battery-specific baselines
f = F_('battery_baselines.csv')
if f is not None and 'battery' in R3:
    Bb = pd.read_csv(f); C = pd.read_csv(F_('battery_corrected.csv')); R3['battery_baselines'] = {}
    for an in ('cv123', 'lobo'):
        stw = C[(C.analysis == an) & (C.method == 'warning') & (C.H == 20)].set_index('unit').cls == 'IN'
        for m, g in Bb[Bb.analysis == an].groupby('method'):
            s = summ(g); b = g.set_index('unit').cls == 'IN'; s['vs_stw'] = mcn(stw, b.reindex(stw.index)); R3['battery_baselines'][f'{an}|{m}'] = s

# ------------------------------------------------------------------ cost audit
cost, boot, bydat, verify = {}, {}, {}, {}
rng = np.random.default_rng(2026)
reg_rows = []
for ds in DS:
    f = F_(f'cost_{ds}.csv')
    if f is None: continue
    C = pd.read_csv(f); cost[ds] = {}; boot[ds] = {}
    if ds != 'Battery' and os.path.exists(f'results/rev/{ds}_cost.csv'):        # reproduction of the earlier policies
        O = pd.read_csv(f'results/rev/{ds}_cost.csv').rename(columns={'lead': 'lead_cycles'})
        ok = True
        for pol in ('STW_window', 'STW_cost', 'HI_cost', 'age', 'perfect_foresight'):
            a = C[C.policy == pol].sort_values(['fold', 'lead_cycles', 'rho', 'unit']); b = O[O.policy == pol].sort_values(['fold', 'lead_cycles', 'rho', 'unit'])
            ok &= len(a) == len(b) and np.allclose(a.cost.values, b.cost.values) and np.allclose(a.use.values, b.use.values)
        verify[ds] = bool(ok)
    for (lc, rho), g in C.groupby(['lead_cycles', 'rho']):
        key = f'{int(lc)}|{int(rho)}'; S = g.groupby('policy')[['cost', 'use', 'fail']].sum(); pf = S.loc['perfect_foresight', 'cost'] / S.loc['perfect_foresight', 'use']
        cost[ds][key] = {p: dict(ratio=round(float(s.cost / s.use / pf), 4), failures=int(s.fail)) for p, s in S.iterrows()}
        pc = g.pivot_table(index=['fold', 'unit'], columns='policy', values='cost'); pu = g.pivot_table(index=['fold', 'unit'], columns='policy', values='use')
        n = len(pc); idx = rng.integers(0, n, size=(2000, n)); boot[ds][key] = {}
        for other in [p for p in POL if p in pc.columns and p != 'STW_window']:
            ra = pc['STW_window'].values[idx].sum(1) / pu['STW_window'].values[idx].sum(1); rb = pc[other].values[idx].sum(1) / pu[other].values[idx].sum(1)
            r = ra / rb; point = (pc['STW_window'].sum() / pu['STW_window'].sum()) / (pc[other].sum() / pu[other].sum())
            boot[ds][key][other] = dict(ratio=round(float(point), 4), lo=round(float(np.percentile(r, 2.5)), 4), hi=round(float(np.percentile(r, 97.5)), 4))
        best = min(cost[ds][key][p]['ratio'] for p in POL if p in cost[ds][key] and p != 'age')
        for p in POL:
            if p in cost[ds][key]: reg_rows.append(dict(ds=ds, cell=key, policy=p, regret=cost[ds][key][p]['ratio'] / best - 1))
    bydat[ds] = {}
    for other in [p for p in POL if p != 'STW_window' and p in next(iter(boot[ds].values()))]:
        bs = [boot[ds][k][other] for k in boot[ds]]
        bydat[ds][other] = dict(cells=len(bs), window_sig_cheaper=sum(b['hi'] < 1 for b in bs), window_sig_dearer=sum(b['lo'] > 1 for b in bs),
                                window_point_cheaper=sum(b['ratio'] < 1 for b in bs))
REG = pd.DataFrame(reg_rows)
regret = {}
if len(REG):
    for p, g in REG.groupby('policy'):
        regret[p] = dict(mean=round(100 * g.regret.mean(), 1), median=round(100 * g.regret.median(), 1), max=round(100 * g.regret.max(), 1),
                         by_ds={d: round(100 * h.regret.mean(), 1) for d, h in g.groupby('ds')}, cells=len(g),
                         max_ds=str(g.loc[g.regret.idxmax(), 'ds']), max_cell=str(g.loc[g.regret.idxmax(), 'cell']),
                         max_by_ds={d: round(100 * h.regret.max(), 1) for d, h in g.groupby('ds')})
R3.update(cost=cost, cost_boot=boot, cost_by_ds=bydat, regret=regret, cost_verify=verify)

# ------------------------------------------------------------------ assumption A1: alarm time and error as the shift varies
shift = {}
for ds in DS:
    f = F_(f'shift_{ds}.pkl')
    if f is None: continue
    d = pickle.load(gzip.open(f, 'rb') if f.endswith('.gz') else open(f, 'rb')); sh = np.asarray(d['shifts']); rec = d['rec']; lo, hi = -13, 2
    offs = np.arange(-4, 4.01, 0.5); pa, pf, mrul, meps, n_alarm = [], [], [], [], []
    for off in offs:
        act, a1, ruls, epss = [], [], [], []
        for r in rec:
            j0 = int(np.argmin(np.abs(sh - r['s_sel']))); j = int(np.argmin(np.abs(sh - (r['s_sel'] + off))))
            if abs(sh[j] - (r['s_sel'] + off)) > 1e-9: continue
            e_act = r['eps'][j] + sh[j]; act.append(bool(r['ok'][j]) and lo <= e_act <= hi)
            e_fix = r['eps'][j0] + sh[j]; a1.append(bool(r['ok'][j0]) and lo <= e_fix <= hi)        # A1: error distribution of the selected shift
            if r['ok'][j]: ruls.append(r['y'][j]); epss.append(r['eps'][j])
        pa.append(100 * np.mean(act)); pf.append(100 * np.mean(a1)); mrul.append(float(np.median(ruls))); meps.append(float(np.median(epss))); n_alarm.append(len(act))
    shift[ds] = dict(offsets=offs.tolist(), realised=np.round(pa, 1).tolist(), a1_prediction=np.round(pf, 1).tolist(), median_rul_at_alarm=np.round(mrul, 2).tolist(),
                     median_eps=np.round(meps, 2).tolist(), max_abs_gap=round(float(np.max(np.abs(np.array(pa) - np.array(pf)))), 1), max_abs_gap_2=round(float(np.max(np.abs(np.array(pa) - np.array(pf))[np.abs(offs) <= 2])), 1), n_units=len(rec),
                     rate_range=[float(min(pa)), float(max(pa))],
                     rul_change_per_unit_shift=round(float(np.polyfit(offs, mrul, 1)[0]), 2), eps_change_per_unit_shift=round(float(np.polyfit(offs, meps, 1)[0]), 2))
R3['shift'] = shift

# ------------------------------------------------------------------ fixed-time decomposition (audit_fixed_time.py)
if F_('fixed_time.json'): R3['fixed_time'] = json.load(open(F_('fixed_time.json')))

# ------------------------------------------------------------------ timing controls: battery row with training-only kappa; Holm over datasets
N0 = json.load(open('paper2/numbers.json')); R2w = N0['rev2']['window']
ctrl = {}
for d in DS:
    if d == 'Battery':
        f = F_('battery_controls.csv')
        if f is None: continue
        C = pd.read_csv(f); ctrl[d] = {}
        for H, g in C.groupby('H'):
            P = g.pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'; o = {}
            for m in ('STW', 'STW_const', 'HI_threshold'): o[m] = dict(IN=int(P[m].sum()), n=len(P), pct=round(100 * P[m].mean(), 1))
            for m in ('STW_const', 'HI_threshold'):
                r = mcn(P['STW'], P[m]); o[m].update(only_stw=r['only_a'], only_other=r['only_b'], p=r['p'])
            ctrl[d][str(int(H))] = o
    else:
        ctrl[d] = {H: {m: dict(v) for m, v in R2w[d][H].items()} for H in R2w[d]}
for m in ('STW_const', 'HI_threshold'):
    ds_ = [d for d in DS if d in ctrl and '20' in ctrl[d]]; ps = [ctrl[d]['20'][m]['p'] for d in ds_]
    for d, ph in zip(ds_, holm(ps)): ctrl[d]['20'][m]['p_holm'] = ph
R3['controls'] = ctrl
if 'Battery' in ctrl and 'battery' in R3:
    R3['controls_battery_matches_confirmation'] = all(ctrl['Battery'][H]['STW']['IN'] == R3['battery']['summary'][f'cv123|warning|{H}']['IN'] for H in ('10', '15', '20') if f'cv123|warning|{H}' in R3['battery']['summary'])

# ------------------------------------------------------------------ spread of the reported estimate and of the true remaining life at the alarm (PHM08, H = 20)
w = pd.read_csv('results/window/first_warning_v2_PHM08.csv'); w = w[(w.H == 20) & w.pred.notna()]
R3['alarm_spread'] = dict(pred_sd=round(float(w.pred.std()), 2), y_sd=round(float(w.y.std()), 2), pred_p05=round(float(w.pred.quantile(.05)), 1), pred_p95=round(float(w.pred.quantile(.95)), 1),
                          y_p05=float(w.y.quantile(.05)), y_p95=float(w.y.quantile(.95)), band_lo=round(float(w.pred.quantile(.05)) - 2, 1), band_hi=round(float(w.pred.quantile(.95)) + 13, 1))

N = json.load(open('paper2/numbers.json')); N['rev3'] = R3
os.makedirs('paper3', exist_ok=True); json.dump(N, open('paper3/numbers.json', 'w'), indent=1, default=float)
print(json.dumps({k: (v if k in ('cost_verify', 'regret', 'battery_sens', 'bearing_sens') else '...') for k, v in R3.items()}, indent=1, default=float)[:3000])
for nm in ('battery', 'bearing'):
    if nm in R3: print(nm, R3[nm]['kappa'], {k: v['pct'] for k, v in R3[nm]['summary'].items() if k.endswith('|20')}, R3[nm]['hyp'], R3[nm]['identical_to_original'])
if 'battery_baselines' in R3: print({k: (v['IN'], v['n'], v['vs_stw']) for k, v in R3['battery_baselines'].items()})
for ds, s in shift.items(): print(ds, 'max gap', s['max_abs_gap'], 'RUL/shift', s['rul_change_per_unit_shift'], 'eps/shift', s['eps_change_per_unit_shift'])
for ds, v in bydat.items(): print(ds, {k: (x['window_sig_cheaper'], x['window_sig_dearer']) for k, x in v.items()})
