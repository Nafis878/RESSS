"""Summary of the CAT analyses (contrib/PLAN.md): every number of the contribution, with the verdicts of the pre-specified
rules, written to out/contrib/contrib_numbers.json (key 'contrib' of paper7/numbers.json) and readable tables.
Inputs: out/contrib/<ds>_cost.csv, <ds>_M.csv, <ds>_settings.csv, <ds>_scores.csv.gz, Battery_*, Bearing_*, sim_*.csv.
Baseline rows are included in the same-platform cost/M files, as required by Amendment 1.
--frozen: read the CAT outputs from results/contrib/ instead of out/contrib/.
Bootstrap: 2,000 paired resamples of test units (fold, unit), seed 2027 per cell; M: kam_metric.paired_boot_mdiff, seed 2027.
"""
import os, sys, json, math
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'kam')); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np, pandas as pd
from scipy.stats import binom, binomtest
import kam_metric as K
import cat as C

SRC = 'results/contrib' if '--frozen' in ARGS else 'out/contrib'
ENG = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6']
M_DS = ['FD001', 'FD002', 'FD003', 'FD004']
A0 = C.ALPHA_PRIMARY; PRIM = f'CATc_a{A0}'; BARE = f'CAT_a{A0}'
BASE = ['STW_window', 'STW_cost', 'STW_cost_1se', 'age']
r4 = lambda x: None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), 4)


def rd(name):
    p = f'{SRC}/{name}'
    for q in (p, p + '.gz', p.replace('.csv', '.csv.gz')):
        if os.path.exists(q): return pd.read_csv(q)
    raise FileNotFoundError(p)


def binom_p(x, n, a):
    """One-sided exact p-value of H0: failure probability <= a, given x failures in n units."""
    return float(binom.sf(x - 1, n, a)) if x > 0 else 1.0


def cp_ci(x, n):
    from scipy.stats import beta
    return [0.0 if x == 0 else float(beta.ppf(0.025, x, n - x + 1)), 1.0 if x == n else float(beta.ppf(0.975, x + 1, n - x))]


def merged_cost(ds):
    """CAT and same-platform baselines required by Amendment 1; never mix frozen fits."""
    if ds == 'Battery':
        D = rd('Battery_cost.csv').rename(columns={'split': 'fold'})
    else:
        D = rd(f'{ds}_cost.csv')
    D = D[~D.policy.str.startswith('rep_')]
    keep = ['fold', 'lead_cycles', 'rho', 'policy', 'unit', 'cost', 'use', 'fail', 'rul_at_alarm'] + (['analysis'] if ds == 'Battery' else [])
    D = D[keep + [c for c in ('alpha', 'tau', 'certifiable') if c in D]]
    assert not D.duplicated(['fold', 'lead_cycles', 'rho', 'policy', 'unit']).any(), 'Duplicate comparison rows'
    for p in BASE + ['perfect_foresight']:
        assert p in set(D.policy), f'Missing same-platform baseline: {ds}/{p}'
    return D


def validity(X, policy, label_alpha):
    """Pooled test failure rate of a bare policy per lead time (rows of one cost ratio)."""
    out = {}
    g0 = X[(X.policy == policy) & (X.rho == X.rho.min())]
    for lc, g in g0.groupby('lead_cycles'):
        n = len(g); x = int(g.fail.sum()); cert = float(g.certifiable.mean()) if 'certifiable' in g else 1.0
        out[str(int(lc))] = dict(n=n, failures=x, rate=r4(x / n), ci=[r4(v) for v in cp_ci(x, n)], p=r4(binom_p(x, n, label_alpha)),
                                 rejected=bool(binom_p(x, n, label_alpha) < 0.05), certifiable_share=r4(cert),
                                 median_notice=r4(g.rul_at_alarm.median()))
    return out


def cost_compare(X, a, others, folds_key='fold'):
    """Per (lead, rho) cell: cost rate / perfect foresight for a and others; paired bootstrap ratio a / other; failures;
    fold-cells with >= 1 test failure."""
    cells = {}; fragile = {p: 0 for p in [a] + others}; nfc = 0
    for (lc, rho), g in X.groupby(['lead_cycles', 'rho']):
        key = f'{int(lc)}|{int(rho)}'
        pc = g.pivot_table(index=[folds_key, 'unit'], columns='policy', values='cost'); pu = g.pivot_table(index=[folds_key, 'unit'], columns='policy', values='use')
        pf = g.pivot_table(index=[folds_key, 'unit'], columns='policy', values='fail', aggfunc='max')
        assert pc.notna().all().all() and pu.notna().all().all(), 'Unpaired/missing cost units'
        perf = pc['perfect_foresight'].sum() / pu['perfect_foresight'].sum(); n = len(pc)
        idx = np.random.default_rng(2027).integers(0, n, size=(2000, n)); c = {}
        for p in [a] + others:
            if p not in pc: continue
            c[p] = dict(ratio=r4(pc[p].sum() / pu[p].sum() / perf), failures=int(pf[p].sum()))
            ff = g[g.policy == p].groupby(folds_key).fail.sum(); fragile[p] += int((ff > 0).sum())
        nfc += g[folds_key].nunique()
        for p in others:
            if p not in pc: continue
            ra = pc[a].values[idx].sum(1) / pu[a].values[idx].sum(1); rb = pc[p].values[idx].sum(1) / pu[p].values[idx].sum(1)
            r = ra / rb; point = (pc[a].sum() / pu[a].sum()) / (pc[p].sum() / pu[p].sum())
            lo, hi = np.percentile(r, [2.5, 97.5]); c[f'vs_{p}'] = dict(ratio=r4(point), lo=r4(lo), hi=r4(hi), win=bool(hi < 1), loss=bool(lo > 1))
        cells[key] = c
    verdict = {}
    for p in others:
        w = sum(cells[k].get(f'vs_{p}', {}).get('win', False) for k in cells); l_ = sum(cells[k].get(f'vs_{p}', {}).get('loss', False) for k in cells)
        verdict[p] = dict(wins=w, losses=l_, cells=len(cells), verdict='beats' if (w >= 8 and l_ == 0) else ('loses' if (l_ >= 8 and w == 0) else 'mixed'))
    return dict(cells=cells, fragile_fold_cells=fragile, fold_cells=nfc, verdict=verdict)


def m_compare(ds):
    D = rd(f'{ds}_M.csv')
    keep = ['split', 'q', 'policy', 'unit', 'cost', 'tlc', 'TF', 'fail']
    A = D[keep]; out = {}
    assert not A.duplicated(['split', 'q', 'policy', 'unit']).any(), 'Duplicate M rows'
    for q, g in A.groupby('q'):
        piv = {p: h.sort_values(['split', 'unit']) for p, h in g.groupby('policy')}; ref = piv['perfect_grid']; TF = ref.TF.values
        res = {}
        for p in [f'CATg_a{A0}', f'CATgc_a{A0}', f'CATgsplit_a{A0}', f'CATgkmin_a{A0}', 'P1_res_opt_mid', 'P1_cls_opt_mid', 'STW_window', 'STW_cost_1se', 'STW_cost', 'P3_res60', 'age_grid'] + [f'CATgc_a{a}' for a in C.ALPHAS if a != A0]:
            if p not in piv: continue
            h = piv[p]; assert np.array_equal(h.unit.values, ref.unit.values) and np.allclose(h.TF.values, TF)
            M, lo, hi = K.m_with_ci(h.cost.values, h.tlc.values, TF, 10.0, 1.0, 1.0 / q); Mi, loi, hii = C.m_influence_ci(h.cost.values, h.tlc.values, TF, 10.0, 1.0, 1.0 / q)
            res[p] = dict(M=r4(100 * M), eq7=[r4(100 * lo), r4(100 * hi)], influence=[r4(100 * loi), r4(100 * hii)], failures=int(h.fail.sum()))
        for a, b in ((f'CATgc_a{A0}', 'P1_res_opt_mid'), (f'CATgc_a{A0}', 'STW_window'), (f'CATgc_a{A0}', 'STW_cost_1se'), (f'CATgc_a{A0}', 'P1_cls_opt_mid')):
            ha, hb = piv[a], piv[b]
            d, lo, hi = K.paired_boot_mdiff(ha.cost.values, ha.tlc.values, hb.cost.values, hb.tlc.values, TF, 10.0, 1.0, 1.0 / q, B=2000, seed=2027)
            res[f'{a}-{b}'] = dict(diff=r4(100 * d), lo=r4(100 * lo), hi=r4(100 * hi), verdict='CAT' if hi < 0 else ('theirs' if lo > 0 else 'unclear'))
        out[f'{q:g}'] = res
    # validity on the grid (bare certified threshold, lead 0)
    vg = {}
    for p in (f'CATg_a{a}' for a in C.ALPHAS):
        h = D[(D.policy == p) & (D.q == D.q.min())]; a = float(p.split('_a')[1]); x = int(h.fail.sum()); n = len(h)
        vg[p] = dict(n=n, failures=x, rate=r4(x / n), p=r4(binom_p(x, n, a)), rejected=bool(binom_p(x, n, a) < 0.05), certifiable_share=r4(h.certifiable.mean()))
    for p in (f'CATgsplit_a{A0}', f'CATgkmin_a{A0}'):
        h = D[(D.policy == p) & (D.q == D.q.min())]; x = int(h.fail.sum()); n = len(h)
        vg[p] = dict(n=n, failures=x, rate=r4(x / n), p=r4(binom_p(x, n, A0)), rejected=bool(binom_p(x, n, A0) < 0.05), certifiable_share=r4(h.certifiable.mean()))
    return dict(by_q=out, validity=vg)


def plain_edge(ds):
    """Real-data check of the mechanism of Theorem 2: share of plain cost-tuned thresholds (rho = 50) that sit at the
    zero-training-failure edge (= the largest OOF critical threshold of the selected setting), and the test failure rate."""
    if ds == 'Battery': return None
    D = rd(f'{ds}_cost.csv'); Sc = rd(f'{ds}_scores.csv'); Sc = Sc[Sc.dT == 1]
    P = D[(D.policy == 'STW_cost') & (D.rho == 50)]; rows = []
    for (fold, lc), g in P.groupby(['fold', 'lead_cycles']):
        key, j = g.setting.iloc[0].rsplit('|', 1); tau = float(g.tau.iloc[0])
        so = Sc[(Sc.fold == fold) & (Sc.lead_cycles == lc) & (Sc.setting == key) & (Sc.role == 'oof')].score.values
        st = Sc[(Sc.fold == fold) & (Sc.lead_cycles == lc) & (Sc.setting == key) & (Sc.role == 'test')].score.values
        rows.append(dict(fold=fold, lead=lc, edge=bool(np.isfinite(so).all() and tau == so.max()), train_fail=int((so > tau).sum()), test_fail=int((st > tau).sum()), n_test=len(st), n_train=len(so)))
    R_ = pd.DataFrame(rows)
    return dict(cases=len(R_), at_edge=int(R_.edge.sum()), with_train_failures=int((R_.train_fail > 0).sum()), test_fail_rate=r4(R_.test_fail.sum() / R_.n_test.sum()),
                one_over_n1=r4(float((1 / (R_.n_train + 1)).mean())))


def main():
    N = {}
    # ---------------- simulations
    V = pd.read_csv(f'{SRC}/sim_validity.csv'); E = V[(V.scores != 'per-time-step bound') & V.certifiable]
    PT = V[V.scores == 'per-time-step bound']
    N['sim'] = dict(validity_cells=int(len(E)), validity_within=int(E.within.sum()), max_excess_pts=r4(100 * (E.p_fail - E.upper).max()),
                    cont_n200_a05=r4(E[(E.scores == 'continuous') & (E.n == 200) & (E.alpha == 0.05)].p_fail.mean()),
                    grid_range_a05=[r4(E[(E.scores == 'grid') & (E.alpha == 0.05)].p_fail.min()), r4(E[(E.scores == 'grid') & (E.alpha == 0.05)].p_fail.max())],
                    pt_pfail_max=r4(PT.p_fail.max()),
                    pt_threshold_ratio=[r4((PT.set_index(['model', 'lead', 'n', 'alpha']).threshold_mean / E[E.scores == 'continuous'].set_index(['model', 'lead', 'n', 'alpha']).threshold_mean).dropna().min()),
                                        r4((PT.set_index(['model', 'lead', 'n', 'alpha']).threshold_mean / E[E.scores == 'continuous'].set_index(['model', 'lead', 'n', 'alpha']).threshold_mean).dropna().max())],
                    noncert_cells=int((~V[V.scores != 'per-time-step bound'].certifiable.astype(bool)).sum()))
    B = pd.read_csv(f'{SRC}/sim_selection.csv'); hi = B[B.rho == 1000]
    N['sim_sel'] = dict(cells=int(len(hi)), within_bound=int((hi.p_fail_plain <= hi.bound + 3 * hi.mcse).sum()),
                        rows=[{k: (r4(v) if isinstance(v, float) else v) for k, v in r.items()} for r in B.to_dict('records')])
    Cv = pd.read_csv(f'{SRC}/sim_m_coverage.csv'); N['sim_m'] = [{k: (r4(v) if isinstance(v, float) else v) for k, v in r.items()} for r in Cv.to_dict('records')]
    Km = pd.read_csv(f'{SRC}/sim_kmin.csv'); Kmc = Km[Km.certifiable]
    N['sim_kmin'] = dict(cells=len(Kmc), within=int(Kmc.within.sum()), replicates_per_cell=int(Kmc.replicates.min()),
                         max_failure_rate=r4(Kmc.p_fail.max()), lower_bound_claimed=False)
    # ---------------- engines
    N['ds'] = {}
    for ds in ENG + ['Battery']:
        if not (os.path.exists(f'{SRC}/{ds}_cost.csv') or os.path.exists(f'{SRC}/{ds}_cost.csv.gz')): continue
        X = merged_cost(ds); d = {}
        groups = {'all': X} if ds != 'Battery' else {'cv': X[X.analysis == 'cv123'], 'lobo': X[X.analysis == 'lobo']}
        for gname, Xg in groups.items():
            e = {}
            e['validity'] = {p: validity(Xg, p, float(p.split('_a')[1])) for p in [f'CAT_a{a}' for a in C.ALPHAS] + [f'CATsplit_a{A0}', f'CATkmin_a{A0}', f'PT_a{A0}']}
            e['cost'] = cost_compare(Xg, PRIM, [p for p in BASE + ['STW_cost_q80', 'Q10_cost_1se', 'HI_cost', 'trend_window', 'trend_cost_1se', 'capacity_cost_1se', f'CAT_a{A0}', f'CATsplit_a{A0}', f'CATkmin_a{A0}', 'CATc_plainset_a0.05', 'CATc_bonf_a0.05', f'PT_a{A0}'] + [f'CATc_a{a}' for a in C.ALPHAS if a != A0] if p in set(Xg.policy)])
            nt = {}
            for p in [PRIM, BARE, 'STW_window', 'STW_cost', 'STW_cost_1se', f'PT_a{A0}']:
                h = Xg[(Xg.policy == p) & (Xg.lead_cycles == Xg.lead_cycles.min()) & (Xg.rho == 10)]
                if len(h): nt[p] = r4(h.rul_at_alarm.median())
            e['notice_lead0_rho10'] = nt
            S = rd(f'{ds}_settings.csv'); S = S[(S.alpha == A0) & ((S.dT == 1) if 'dT' in S else True)]
            if ds == 'Battery': S = S[S.analysis == ('cv123' if gname == 'cv' else 'lobo')]
            e['certifiable'] = dict(cf=int(S.cert_cf.sum()), split=int(S.cert_split.sum()), kmin=int(S.cert_kmin.sum()), bonf=int(S.cert_bonf.sum()), total=int(len(S)),
                                    n_cf=[int(S.n_cf.min()), int(S.n_cf.max())])
            d[gname] = e
        if ds in M_DS: d['M'] = m_compare(ds)
        pe = plain_edge(ds)
        if pe: d['plain_edge'] = pe
        N['ds'][ds] = d
    if os.path.exists(f'{SRC}/Bearing_units.csv'):
        Bu = pd.read_csv(f'{SRC}/Bearing_units.csv'); Bs = pd.read_csv(f'{SRC}/Bearing_settings.csv'); bb = {}
        for a, g in Bu.groupby('alpha'):
            s = Bs[Bs.alpha == a]; x = int(g.fail.sum()); n = len(g)
            bb[f'{a:g}'] = dict(n=n, failures=x, rate=r4(x / n), certifiable=int(s.cert_cf.sum()), splits=int(len(s)), p=r4(binom_p(x, n, a)),
                                median_notice_snapshots=r4(g.rul_at_alarm_snapshots.median()), median_life=r4(g.life_snapshots.median()))
        N['bearing'] = bb
    # ---------------- pre-specified verdicts
    V_ = {}
    eng = [d for d in ENG if d in N['ds']]
    V_['validity_holds'] = {d: not any(v['rejected'] for v in N['ds'][d]['all']['validity'][BARE].values()) for d in eng}
    V_['validity_holds_count'] = sum(V_['validity_holds'].values())
    # Historical key retained for compatibility; it is a screening outcome, not a certificate.
    V_['validity_screen_not_rejected'] = dict(V_['validity_holds'])
    V_['exact_guarantee_for_implemented_variants_established'] = False
    frag = {}
    for X_ in ('STW_cost', 'STW_cost_1se'):
        lower = {d: N['ds'][d]['all']['cost']['fragile_fold_cells'][PRIM] < N['ds'][d]['all']['cost']['fragile_fold_cells'][X_] for d in eng}
        frag[X_] = dict(lower_on=lower, count=sum(lower.values()), less_fragile=sum(lower.values()) >= 4)
    V_['fragility'] = frag
    V_['cost'] = {X_: {d: N['ds'][d]['all']['cost']['verdict'][X_]['verdict'] for d in eng} for X_ in BASE}
    V_['M'] = {d: {k: N['ds'][d]['M']['by_q']['0.1'][f'{PRIM.replace("CATc", "CATgc")}-{k}']['verdict'] for k in ('P1_res_opt_mid', 'STW_window')} for d in M_DS if d in N['ds']}
    loses_w = sum(v == 'loses' for v in V_['cost']['STW_window'].values())
    win = V_['validity_holds_count'] >= 5 and frag['STW_cost']['less_fragile'] and loses_w == 0
    loss = (len(eng) - V_['validity_holds_count']) >= 2 or loses_w >= 2
    V_['complete_engine_suite'] = len(eng) == len(ENG)
    V_['primary_claim'] = ('win' if win else ('loss' if loss else 'mixed')) if len(eng) == len(ENG) else 'incomplete'
    N['interpretation'] = {'baseline_source': 'same-platform reruns (Amendment 1)',
        'validity_test': 'Failure to reject is not proof of risk control; overlapping CV fits do not give independent Bernoulli outcomes.',
        'implemented_guarantees': 'CF refitting and calibration-dependent setting selection in SPLIT/KMIN preclude the fixed-rule exact theorem; noncertifiable fallbacks carry no certificate.'}
    N['verdicts'] = V_
    os.makedirs('out/contrib', exist_ok=True)
    json.dump(N, open('out/contrib/contrib_numbers.json', 'w', newline='\n'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    print(json.dumps(V_, indent=1, default=str))


if __name__ == '__main__':
    main()
