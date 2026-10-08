"""Third revision (comparison with the metric M of Kamariotis et al., 2024, and Phases 3-4): collect every number used by the
rewritten manuscript into paper5/numbers.json = paper4/numbers.json + key 'rev5'.
Sources (fresh outputs in out/, or with --frozen the frozen copies in results/):
  results/kam/   kam_grid_effect.py, kam_simulator.py (Phase 1); kam_fd001.py + kam_fd001_summarize.py (Phases 2-3);
                 kam_fragility.py (Phase 3); check_r0.py (re-run check)
  results/audit/ audit_hi_calibrated.py (4b), audit_battery_cost_nested.py (4a), audit_fixed_matched.py --ds FD004 (4d)
Usage: python kam/make_rev5_numbers.py [--frozen]
"""
import os, sys, json, glob, re
import numpy as np, pandas as pd
from scipy.stats import binomtest, beta

FROZEN = '--frozen' in sys.argv
K_ = 'results/kam' if FROZEN else 'out/kam'
A_ = 'results/audit' if FROZEN else 'out/audit'
QS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8]


def F_(d, name):
    for c in (f'{d}/{name}', f'{d}/{name}.gz', f'results/kam/{name}', f'results/kam/{name}.gz'):
        if os.path.exists(c): return c
    return None


def rd(d, name):
    f = F_(d, name); return pd.read_csv(f) if f else None


def cp(k, n):
    return [round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0]


def mcn(a, b):
    x = int((a & ~b).sum()); y = int((~a & b).sum())
    return dict(only_a=x, only_b=y, p=float(binomtest(min(x, y), x + y, .5).pvalue) if x + y else 1.0)


def holm(ps):
    ps = np.asarray(ps, float); o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for r, i in enumerate(o): run = max(run, (m - r) * ps[i]); adj[i] = min(1.0, run)
    return adj.tolist()


R5 = {}
# ---------------------------------------------------------------- plans
R5['plans'] = {}
for nm in ('PHASE2_PLAN', 'PHASE3_4_PLAN'):
    t = open(f'kam/{nm}.sha256').read(); R5['plans'][nm] = re.findall(r'^([0-9a-f]{64})', t, re.M)[-1]

# ---------------------------------------------------------------- Phase 1: grid effect and simulator
g = pd.read_csv('results/kam/grid_effect_summary.csv')
R5['grid_effect'] = {f'{r.dataset}|{int(r.dT)}': float(r.grid_effect_pct) for r in g.itertuples()}
gp = pd.read_csv('results/kam/grid_effect_policies.csv'); gp = gp[gp.policy != 'run_to_failure']
R5['grid_diff'] = {'cmapss': [float(gp[gp.dataset.isin(['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'])].difference.min()), float(gp[gp.dataset.isin(['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'])].difference.max())],
                   'ncmapss': [float(gp[gp.dataset == 'NCMAPSS6'].difference.min()), float(gp[gp.dataset == 'NCMAPSS6'].difference.max())]}
neg = gp[gp.M_negative]
R5['grid_negative'] = dict(n=int(len(neg)), min_pct=float(neg.M_grid_pct.min()) if len(neg) else None,
                           cases=[dict(dataset=r.dataset, dT=int(r.dT), rho=int(r.rho), policy=r.policy, M_pct=float(r.M_grid_pct)) for r in neg.itertuples()])
sim = open('results/kam/sim_checks.txt').read()
R5['sim'] = {'p1_lowest': re.findall(r'sigma=([0-9.]+): optimised P1 lowest M at (\d)/7', sim), 'p3_lt_p2': re.findall(r'sigma=([0-9.]+): P3 < P2 at (\d)/7', sim),
             'pstar_lt': re.findall(r'sigma=([0-9.]+): p\* < c_p/c_c at (\d)/7', sim), 'violations': 'M violations (M < 0): []' in sim}
st = pd.read_csv('results/kam/sim_results.csv')
R5['sim_table'] = {f'{r.sigma}|{r.cp_over_cc}|{r.policy}': dict(M=round(r.M_pct, 3), lo=round(r.lo_pct, 3), hi=round(r.hi_pct, 3), failures=int(r.failures),
                                                                 p=None if pd.isna(r.p_thres) else float(r.p_thres)) for r in st.itertuples()}

# ---------------------------------------------------------------- Phases 2-3: M on FD001-FD004 (five-fold) and FD001 30 splits
R5['kam'] = {}
for ds in ('fd001', 'fd002', 'fd003', 'fd004'):
    T = rd(K_, f'{ds}_cv_table.csv'); P = rd(K_, f'{ds}_cv_pairs.csv')
    if T is None: continue
    o = {'table': {}, 'pairs': {}, 'tally': {}}
    for r in T.itertuples():
        o['table'][f'{r.q}|{r.policy}'] = dict(M=round(r.M_pct, 4), eq7=[round(r.eq7_lo, 4), round(r.eq7_hi, 4)], boot=[round(r.boot_lo, 4), round(r.boot_hi, 4)],
                                               failures=int(r.failures), n=int(r.n), ratio1=round(r.ratio_vs_1cycle_perfect, 6))
    for r in P.itertuples():
        o['pairs'][f'{r.q}|{r.a}|{r.b}'] = dict(d=round(r.diff_pct, 4), lo=round(r.lo, 4), hi=round(r.hi, 4), v=('mine' if r.hi < 0 else 'theirs' if r.lo > 0 else 'unclear'))
    for (a, b), gg in P.groupby(['a', 'b']):
        o['tally'][f'{a}|{b}'] = dict(mine=int((gg.hi < 0).sum()), theirs=int((gg.lo > 0).sum()), unclear=int(((gg.hi >= 0) & (gg.lo <= 0)).sum()))
    lk = F_(K_, f'{ds}_leakage.txt'); o['leakage'] = open(lk).read().strip().split('\n') if lk else []
    o['grid_negative'] = int((T.mapped & (T.M_pct < -1e-10)).sum())
    B = rd(K_, f'{ds}_bins_summary.csv'); C = rd(K_, f'{ds}_bins_count.csv'); S = rd(K_, f'{ds}_thresholds.csv')
    if B is not None:
        b = B[(B.protocol == 'cv') & (B.cap == 60)]
        o['bins'] = dict(units_min=int(b.units_min.min()), units_max=int(b.units_median.max()), rows_min=int(b.rows_min.min()),
                         hi=[float(x) for x in b.sort_values('bin').hi_median.values])
    if C is not None:
        c = C[C.protocol == 'cv']; o['bins_count'] = {str(int(r.cap)): [int(r['min']), float(r['median']), int(r['max'])] for _, r in c.iterrows()}
    if S is not None:
        s = S[S.protocol == 'cv']; o['thresholds'] = {f'{r.q}|{r.model}': dict(mid=float(r.p_mid_median), max=float(r.p_max_median), n_tied=float(r.n_tied_median)) for r in s.itertuples()}
    R5['kam'][ds] = o
rp = rd(K_, 'fd001_rs_policies.csv'); rq = rd(K_, 'fd001_rs_pairs.csv')
R5['rs'] = {'policies': {f'{r.q}|{r.policy}': dict(med=round(r.M_median, 4), q25=round(r.M_q25, 4), q75=round(r.M_q75, 4), min=round(r.M_min, 4), max=round(r.M_max, 4),
                                                     fail_splits=int(r.splits_with_failure), splits=int(r.splits)) for r in rp.itertuples()},
            'pairs': {f'{r.q}|{r.a}|{r.b}': dict(med=round(r.diff_median, 4), share_a=round(r.share_a_lower, 4), below=int(r.n_interval_below0), above=int(r.n_interval_above0))
                      for r in rq.itertuples()}}
r0 = F_(K_, 'r0_check.txt'); R5['r0'] = open(r0).read().strip().split('\n') if r0 else []

# ---------------------------------------------------------------- Phase 3: fragility
fr = {}
TA = rd(K_, 'fragility_tally.csv'); V = rd(K_, 'fragility_verdict.csv'); TI = rd(K_, 'fragility_tie.csv'); P1 = rd(K_, 'fragility_p1.csv'); STf = rd(K_, 'fragility_stw.csv')
if TA is not None:
    fr['tally'] = {f'{r.ds}|{r.protocol}|{r.policy}': dict(cells=int(r.cells), fail=int(r.cells_fail), M50=int(r.cells_M50), small=int(r.cells_small), fail_small=int(r.cells_fail_small),
                                                         M50_small=int(r.cells_M50_small), failures=int(r.failures_total), Mmax=round(float(r.M_max), 2)) for r in TA.itertuples()}
    fr['verdict'] = {f'{r.ds}|{r.protocol}': r.verdict for r in V.itertuples()}
    fr['verdict_detail'] = {f'{r.ds}|{r.protocol}': {c: getattr(r, c) for c in V.columns if '_vs_' in c} for r in V.itertuples()}
    fr['tie'] = {f'{r.ds}|{r.protocol}|{r.model}': dict(decisions=int(r.decisions), differ=int(r.differ), max_abs_M_diff=round(float(r.max_abs_M_diff), 6)) for r in TI.itertuples()}
    cv = P1[P1.protocol == 'cv']
    fr['p1'] = {}
    for (ds, m, q), gg in cv.groupby(['ds', 'model', 'q']):
        fr['p1'][f'{ds}|{m}|{q}'] = dict(p_mid=float(gg.p_mid.median()), p_max=float(gg.p_max.median()), p_fail_train=float(gg.p_fail_train.median()),
                                          p_fail_test=float(gg.p_fail_test.median()), sets_fail_mid=int((gg.test_fail_mid > 0).sum()), sets_fail_max=int((gg.test_fail_max > 0).sum()),
                                          sets=int(len(gg)), max_at_train_cliff=int((gg.plateau_to_train_cliff.fillna(9) < 0.05).sum()))
    st = STf[STf.protocol == 'cv']
    fr['stw'] = {f'{r[0]}|{r[1]}|{r[2]}': dict(tau_sel=float(gg.tau_sel.median()), margin=float(gg.margin_cycles.median()) if gg.margin_cycles.notna().any() else None,
                                                 sets_fail=int((gg.test_fail > 0).sum()), sets=int(len(gg))) for r, gg in st.groupby(['ds', 'policy', 'q'])}
    sm = st[st.q <= 0.1]
    fr['stw_margin'] = {p: dict(median=float(g.margin_cycles.median()), q25=float(g.margin_cycles.quantile(.25)), n=int(g.margin_cycles.notna().sum())) for p, g in sm.groupby('policy')}
    CU = rd(K_, 'fragility_curve.csv')
    if CU is not None:
        fr['curve'] = {}
        for m, gg in CU.groupby('model'):
            gg = gg.sort_values('p'); pm, px, pf = gg.p_mid.iloc[0], gg.p_max.iloc[0], gg.p_fail_train.iloc[0]
            at = lambda p: gg.iloc[int(np.argmin(np.abs(gg.p.values - p)))]
            nxt = gg[gg.p > px].iloc[0] if (gg.p > px).any() else None
            fr['curve'][m] = dict(p_mid=float(pm), p_max=float(px), p_fail_train=float(pf), M_train_mid=float(at(pm).M_train), M_train_max=float(at(px).M_train),
                                  M_test_mid=float(at(pm).M_test), M_test_max=float(at(px).M_test), fail_test_mid=int(at(pm).fail_test),
                                  next_p=float(nxt.p) if nxt is not None else None, M_train_next=float(nxt.M_train) if nxt is not None else None,
                                  fail_train_next=int(nxt.fail_train) if nxt is not None else None, n_train=int(gg.n_train.iloc[0]), n_test=int(gg.n_test.iloc[0]))
R5['fragility'] = fr

# ---------------------------------------------------------------- 4b: calibrated health indicator
hc = {}; RN = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6']
for ds in RN:
    D = rd(A_, f'hi_calibrated_{ds}.csv'); W = pd.read_csv(f'results/rev/{ds}_window.csv')
    if D is None: continue
    hc[ds] = {}
    for H in (10, 15, 20, 30, 40):
        a = D[(D.H == H) & (D.method == 'HI_calibrated')].set_index('unit')
        s = W[(W.H == H) & (W.method == 'STW')].set_index('unit').cls.reindex(a.index) == 'IN'
        h = W[(W.H == H) & (W.method == 'HI_threshold')].set_index('unit').cls.reindex(a.index) == 'IN'
        ai = a.cls == 'IN'; c = a.cls.value_counts(); nn = a[a.cls != 'MISSED']
        hc[ds][str(H)] = dict(IN=int(ai.sum()), n=len(a), pct=round(100 * ai.mean(), 1), ci=cp(int(ai.sum()), len(a)), late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)),
                              missed=int(c.get('MISSED', 0)), vs_recipe=mcn(s, ai), vs_hi=mcn(ai, h), recipe_IN=int(s.sum()), hi_IN=int(h.sum()),
                              median_left=float(nn.y.median()) if len(nn) else None)
    chk = F_(A_, 'hi_calibrated_check.txt')
if hc:
    ph = holm([hc[d]['20']['vs_recipe']['p'] for d in RN if d in hc])
    for d, p in zip([d for d in RN if d in hc], ph): hc[d]['20']['vs_recipe']['p_holm'] = p
    hc['check'] = [l for l in open(F_(A_, 'hi_calibrated_check.txt')).read().strip().split('\n') if l]
R5['hi_cal'] = hc

# ---------------------------------------------------------------- 4a: battery cost, fully nested (convention C)
f = F_(A_, 'cost_battery_nested.csv')
if f:
    C = pd.read_csv(f); rng = np.random.default_rng(2027); bn = {}
    PAIRS = [('trend_cost_1se', 'STW_window'), ('trend_cost_1se', 'STW_cost_1se'), ('trend_cost', 'STW_cost'), ('trend_window', 'STW_window'), ('trend_cost_1se', 'capacity_cost_1se'),
             ('STW_window', 'age'), ('trend_cost_1se', 'age')] + [('STW_window', o) for o in ('HI_cost', 'STW_cost', 'STW_cost_1se', 'STW_cost_q80', 'Q10_cost', 'Q10_cost_1se', 'capacity_cost', 'capacity_cost_1se')]
    for an, ga in C.groupby('analysis'):
        cells, pairs = {}, {}
        for (lc, rho), g2 in ga.groupby(['lead_cycles', 'rho']):
            S = g2.groupby('policy')[['cost', 'use', 'fail']].sum(); pf = S.loc['perfect_foresight', 'cost'] / S.loc['perfect_foresight', 'use']
            key = f'{int(lc)}|{int(rho)}'; cells[key] = {p: dict(ratio=round(float(s.cost / s.use / pf), 6), failures=int(s.fail)) for p, s in S.iterrows()}
            pc = g2.pivot_table(index=['split', 'unit'], columns='policy', values='cost'); pu = g2.pivot_table(index=['split', 'unit'], columns='policy', values='use')
            n = len(pc); idx = rng.integers(0, n, size=(2000, n))
            for a_, b_ in PAIRS:
                ra = pc[a_].values[idx].sum(1) / pu[a_].values[idx].sum(1); rb = pc[b_].values[idx].sum(1) / pu[b_].values[idx].sum(1); r = ra / rb
                point = (pc[a_].sum() / pu[a_].sum()) / (pc[b_].sum() / pu[b_].sum())
                pairs.setdefault(f'{a_}|{b_}', {})[key] = dict(ratio=round(float(point), 6), lo=round(float(np.percentile(r, 2.5)), 6), hi=round(float(np.percentile(r, 97.5)), 6))
        summ = {}
        for pr, d in pairs.items():
            v = sorted(x['ratio'] for x in d.values())
            summ[pr] = dict(a_sig_cheaper=sum(x['hi'] < 1 for x in d.values()), a_sig_dearer=sum(x['lo'] > 1 for x in d.values()), a_point_cheaper=sum(x['ratio'] < 1 for x in d.values()),
                            median=round((v[7] + v[8]) / 2, 6), min=v[0], max=v[-1])
        kap = ga.drop_duplicates('split').set_index('split')
        bn[an] = dict(cells=cells, pairs=pairs, summary=summ, kappa_outer=kap.kappa.astype(int).to_dict(), kappa_inner=kap.inner_kappas.astype(str).to_dict() if 'inner_kappas' in kap else {},
                      failures_by_lead={p: {str(int(lc)): int(ga[(ga.policy == p) & (ga.lead_cycles == lc) & (ga.rho == 50)].fail.sum()) for lc in sorted(ga.lead_cycles.unique())}
                                        for p in ('STW_window', 'STW_cost_1se', 'capacity_cost_1se', 'trend_window', 'trend_cost_1se', 'age')})
    bn['check'] = open(F_(A_, 'cost_battery_nested_check.txt')).read().strip().split('\n')
    R5['battery_cost_nested'] = bn
    # mean excess cost over the cheapest condition-based policy per cell (as audit_summarize.py), battery now under convention C
    N4 = json.load(open('paper4/numbers.json')); CO3 = N4['rev3']['cost']
    POL = ['STW_window', 'STW_cost', 'STW_cost_1se', 'STW_cost_q80', 'Q10_cost', 'Q10_cost_1se', 'HI_cost', 'capacity_cost', 'capacity_cost_1se', 'age']
    reg = []
    for ds in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'Battery']:
        cells = CO3[ds] if ds != 'Battery' else {k: {p: dict(ratio=round(v[p]['ratio'], 4)) for p in v} for k, v in bn['cv123']['cells'].items()}
        for key, c in cells.items():
            best = min(c[p]['ratio'] for p in POL if p in c and p != 'age')
            for p in POL:
                if p in c: reg.append(dict(ds=ds, cell=key, policy=p, regret=c[p]['ratio'] / best - 1))
    REG = pd.DataFrame(reg); rg = {}
    for p, g2 in REG.groupby('policy'):
        rg[p] = dict(mean=round(100 * g2.regret.mean(), 1), max=round(100 * g2.regret.max(), 1), by_ds={d: round(100 * h.regret.mean(), 1) for d, h in g2.groupby('ds')},
                     cells=len(g2), max_ds=str(g2.loc[g2.regret.idxmax(), 'ds']), max_cell=str(g2.loc[g2.regret.idxmax(), 'cell']))
    R5['regret'] = rg

# ---------------------------------------------------------------- 4d: matched decomposition on FD004
f = F_(A_, 'fixed_matched_FD004.json')
if f:
    fm = json.load(open(f)); fm.pop('selection', None); R5['fixed_matched_FD004'] = fm

N = json.load(open('paper4/numbers.json')); N['rev5'] = R5
os.makedirs('paper5', exist_ok=True); json.dump(N, open('paper5/numbers.json', 'w'), indent=1, default=float)
print(json.dumps({k: (list(v.keys())[:10] if isinstance(v, dict) else v) for k, v in R5.items()}, indent=1, default=str)[:4000])
