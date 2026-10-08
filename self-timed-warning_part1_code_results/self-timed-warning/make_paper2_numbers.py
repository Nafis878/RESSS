"""Collect every number used in the warning-model manuscript into paper2/numbers.json (nothing is typed by hand)."""
import json, os, re, numpy as np, pandas as pd
from scipy.stats import beta, binomtest
from safe_common import load_dataset
os.makedirs('paper2', exist_ok=True)
def cp(k, n): return [round(100 * beta.ppf(.025, k, n - k + 1), 1) if k else 0.0, round(100 * beta.ppf(.975, k + 1, n - k), 1) if k < n else 100.0]
def phm(d): d = np.asarray(d, float); return np.where(d < 0, np.exp(-d / 13) - 1, np.exp(d / 10) - 1)
N = {}

# ---- datasets
N['data'] = {}
for ds in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']:
    tr, _, _ = load_dataset(ds); L = tr.groupby('unit').cycle.max()
    N['data'][ds] = dict(engines=int(len(L)), rows=int(len(tr)), life_min=int(L.min()), life_max=int(L.max()), life_median=float(L.median()), regimes=int(tr.regime.nunique()))
R = pd.read_csv('ncm/ncmapss_cycle_summary.csv.gz'); key = R.subset + '|' + R.part + '|' + R.unit.astype(str); Lm = R.groupby(key).cycle.max()
N['data']['N-CMAPSS'] = dict(engines=int(len(Lm)), rows=int(len(R)), life_min=int(Lm.min()), life_max=int(Lm.max()), life_median=float(Lm.median()), regimes=int(R.Fc.round().nunique()),
                             dev=int(R[R.part == 'dev'].groupby(['subset', 'unit']).ngroups), test=int(R[R.part == 'test'].groupby(['subset', 'unit']).ngroups))

# ---- main cross-validated results (eol_window2.py)
def summarise(g):
    c = g.cls.value_counts(); n = len(g); k = int(c.get('IN', 0)); gv = g.dropna(subset=['pred']); e = gv.pred - gv.y
    return dict(n=n, IN=k, pct=round(100 * k / n, 1), ci=cp(k, n), late=int(c.get('LATE', 0)), early=int(c.get('EARLY', 0)), missed=int(c.get('MISSED', 0)),
                late_or_missed_pct=round(100 * (c.get('LATE', 0) + c.get('MISSED', 0)) / n, 1),
                median_left=float(gv.y.median()), left_p05=float(gv.y.quantile(.05)), left_p95=float(gv.y.quantile(.95)),
                median_error=round(float(e.median()), 1), error_iqr=[round(float(e.quantile(.25)), 1), round(float(e.quantile(.75)), 1)],
                early_limit_active_pct=round(100 * float((gv.y >= 13).mean()), 1), in_when_active=round(100 * float(((gv.y >= 13) & (e >= -13) & (e <= 2)).sum() / max(1, (gv.y >= 13).sum())), 1),
                phm_score_mean=round(float(phm(e).mean()), 2), per50=round(50 * k / n, 1), gross_early=int((e < -30).sum()), max_left=float(gv.y.max()), min_error=round(float(e.min()), 1), max_error=round(float(e.max()), 1))
N['cv'] = {}
for ds in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']:
    A = pd.read_csv(f'out/window/first_warning_v2_{ds}.csv'); N['cv'][ds] = {str(H): summarise(g) for H, g in A.groupby('H')}
    N['cv'][ds]['settings_H20'] = A[A.H == 20].groupby('fold')[['cap', 'span', 'k', 'shift']].first().to_dict('records')
pool = {H: [N['cv'][d][str(H)] for d in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']] for H in (10, 15, 20)}
N['cv_pooled'] = {str(H): dict(IN=sum(x['IN'] for x in v), n=sum(x['n'] for x in v), pct=round(100 * sum(x['IN'] for x in v) / sum(x['n'] for x in v), 1)) for H, v in pool.items()}

# ---- N-CMAPSS confirmation
W = json.load(open('out/ncm/warning_summary.json')); N['ncm'] = W
N['ncm_protocol'] = dict(sha256=open('ncm/WARNING_PROTOCOL.sha256').read().split()[0], written=open('ncm/WARNING_PROTOCOL.sha256').read().split('written ')[1].strip())
A = pd.read_csv('out/ncm/warning_results.csv'); g = A[A.primary & (A.method == 'warning') & (A.H == 20)]
N['ncm_detail_H20'] = summarise(g); N['ncm_settings_H20'] = g.groupby('split')[['option', 'span', 'k', 'shift']].first().reset_index().to_dict('records')

# ---- head-to-head on PHM08 (h2h.py)
H2 = pd.read_csv('out/window/h2h_PHM08.csv'); N['h2h'] = {}
for (m, H), g in H2.groupby(['method', 'H']): N['h2h'][f'{m}|{H}'] = summarise(g)
N['h2h_mcnemar'] = {}
for H in (10, 20):
    w = H2[H2.H == H].pivot_table(index='unit', columns='method', values='cls', aggfunc='first') == 'IN'
    for m in ['mlp_kf', 'rnn', 'similarity', 'cnn']:
        b = int((w.ours & ~w[m]).sum()); c = int((~w.ours & w[m]).sum()); N['h2h_mcnemar'][f'{m}|{H}'] = dict(ours_only=b, other_only=c, p=float(binomtest(b, b + c, .5).pvalue))
# Holm correction over the four comparisons at each H
for H in (10, 20):
    ks = [f'{m}|{H}' for m in ['mlp_kf', 'rnn', 'similarity', 'cnn']]; ps = sorted((N['h2h_mcnemar'][k]['p'], k) for k in ks); run = 0
    for i, (p, k) in enumerate(ps): run = max(run, min(1, p * (len(ps) - i))); N['h2h_mcnemar'][k]['p_holm'] = run

# ---- repeated random 50/168 splits (rep50.py)
RP = pd.read_csv('out/rep50/rep50_results.csv'); c = RP.groupby('repetition').result.apply(lambda s: int((s == 'IN').sum()))
N['rep50'] = dict(reps=int(RP.repetition.nunique()), counts=c.tolist(), mean=round(float(c.mean()), 2), sd=round(float(c.std()), 2), min=int(c.min()), max=int(c.max()),
                  n_ge48=int((c >= 48).sum()), n_ge46=int((c >= 46).sum()), pooled_pct=round(100 * float((RP.result == 'IN').mean()), 1),
                  late_mean=round(float(RP.groupby('repetition').result.apply(lambda s: (s == 'LATE').sum()).mean()), 2),
                  early_mean=round(float(RP.groupby('repetition').result.apply(lambda s: (s == 'EARLY').sum()).mean()), 2),
                  missed_total=int((RP.result == 'MISSED').sum()), engines_covered=int(RP.engine.nunique()), median_error=round(float(RP.error_E.median()), 1))

# ---- leakage checks
lk = open('out/window/eol_leakage_report.md').read(); N['leakage'] = dict(passed=lk.count('- PASS'), total=lk.count('- PASS') + lk.count('- FAIL'),
                                                                           lines=[l[2:] for l in lk.splitlines() if l.startswith('- ')])

# ---- fixed-time (half of life) ceiling, window [-13, +2]
AB = json.load(open('out/window/ablation_results_PHM08.json')); TG = json.load(open('out/window/tcn_gan_results_PHM08.json'))
EX = json.load(open('out/window/hybrid_external_PHM08.json'))
N['half'] = dict(single=AB['A_single_raw'], info=AB['B_information'], hybrid=AB['final_hybrid'], leave_one_out=AB['D_leave_one_out'],
                 tcn=TG['single']['tcn_median'], tcn_gan=TG['single']['tcngan_median'], hybrid_tcn_gan=TG['hybrid_plus_tcngan_only'],
                 hybrid_external=EX['hybrid_with_external'])
d = pd.read_csv('out/safe/v2_cut_predictions.csv'); d = d[(d.role == 'test') & (d.dataset == 'PHM08') & (d.method.isin(['gbm', 'lstm', 'cnn', 'age']))]
d['hit'] = ((d.point - d.true_rul) >= -13) & ((d.point - d.true_rul) <= 2)
N['fixed_fraction'] = {m: {str(f): round(100 * float(g.hit.mean()), 1) for f, g in dm.groupby('frac')} for m, dm in d.groupby('method')}
# signal-to-noise of the wear signal at half-life vs end of life (dataset_profile logic)
from safe_common import SENS7
tr, _, _ = load_dataset('PHM08'); stw = {s_: tr.groupby('regime')[s_].agg(['mean', 'std']) for s_ in SENS7}
Zw = np.column_stack([(tr[s_] - tr.regime.map(stw[s_]['mean'])) / tr.regime.map(stw[s_]['std']) for s_ in SENS7]); tr['hi'] = Zw.mean(1)
tr['hs'] = tr.groupby('unit').hi.transform(lambda x: x.ewm(span=10).mean()); tr['drift'] = tr.hs - tr.unit.map(tr[tr.cycle <= 20].groupby('unit').hi.mean())
noise = float(tr[tr.cycle <= 40].groupby('unit').hi.std().median()); fr_ = tr.cycle / tr.life
N['wear_signal'] = dict(half_life=round(float(tr[(fr_ - 0.5).abs() < 0.01].drift.median()), 2), rul20=round(float(tr[tr.rul == 20].drift.median()), 2),
                        rul10=round(float(tr[tr.rul == 10].drift.median()), 2), noise=round(noise, 2))

# ---- ablation (warn_ablation.py), if available
if os.path.exists('out/window/ablation_warning_PHM08.json'):
    N['ablation'] = json.load(open('out/window/ablation_warning_PHM08.json'))
    AB = pd.read_csv('out/window/ablation_warning_PHM08.csv'); N['ablation_mcnemar'] = {}
    for H in (10, 20):
        w = AB[AB.H == H].pivot_table(index='unit', columns='variant', values='cls', aggfunc='first') == 'IN'
        vs = [v for v in w.columns if v != 'full']; tmp = {}
        for v in vs:
            b_ = int((w.full & ~w[v]).sum()); c_ = int((~w.full & w[v]).sum()); tmp[v] = dict(full_only=b_, variant_only=c_, p=float(binomtest(b_, b_ + c_, .5).pvalue) if b_ + c_ else 1.0)
        ps = sorted((tmp[v]['p'], v) for v in vs); run = 0
        for i, (p, v) in enumerate(ps): run = max(run, min(1, p * (len(ps) - i))); tmp[v]['p_holm'] = run
        N['ablation_mcnemar'][str(H)] = tmp
    O = pd.read_csv('out/window/oracle_timed_PHM08.csv'); N['oracle_vs_self'] = {}
    for H in (10, 20):
        f_ = AB[(AB.variant == 'full') & (AB.H == H)].set_index('unit').cls == 'IN'; o_ = O[O.H == H].set_index('unit').cls == 'IN'; f_, o_ = f_.align(o_, join='inner')
        b_ = int((f_ & ~o_).sum()); c_ = int((~f_ & o_).sum()); N['oracle_vs_self'][str(H)] = dict(self_only=b_, oracle_only=c_, n=int(len(f_)), p=float(binomtest(b_, b_ + c_, .5).pvalue))
from feats import regime_stats as _rs
N['sensors_kept'] = {ds: len(_rs(load_dataset(ds)[0])[1]) for ds in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']}
A_ = pd.read_csv('out/ncm/warning_results.csv'); N['ncm_detail'] = {str(H): summarise(g) for H, g in A_[A_.primary & (A_.method == 'warning')].groupby('H')}
N['phm08_shift_range_H20'] = [float(min(x['shift'] for x in N['cv']['PHM08']['settings_H20'])), float(max(x['shift'] for x in N['cv']['PHM08']['settings_H20']))]
N['k5_share'] = {ds: float(np.mean([x['k'] == 5 for x in N['cv'][ds]['settings_H20']])) for ds in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']}
# ================================================================ revision: fair DL, windows, cost, theory, battery
# ---- fair deep-learning competitors on the same 15 sensors (dl_warning.py), paired with our model from h2h.py
if os.path.exists('out/window/dl_warning_PHM08.csv'):
    DL = pd.read_csv('out/window/dl_warning_PHM08.csv'); N['dl'] = {f'{m}|{H}': summarise(g) for (m, H), g in DL.groupby(['method', 'H'])}
    N['dl_mcnemar'] = {}
    for H in (10, 20):
        ours = H2[(H2.H == H) & (H2.method == 'ours')].set_index('unit').cls == 'IN'; tmp = {}
        for m in sorted(DL.method.unique()):
            o = DL[(DL.H == H) & (DL.method == m)].set_index('unit').cls == 'IN'; a_, b_ = ours.align(o, join='inner')
            x = int((a_ & ~b_).sum()); y = int((~a_ & b_).sum()); tmp[m] = dict(ours_only=x, other_only=y, n=int(len(a_)), p=float(binomtest(x, x + y, .5).pvalue) if x + y else 1.0)
        ps = sorted((tmp[m]['p'], m) for m in tmp); run = 0
        for i, (p, m) in enumerate(ps): run = max(run, min(1, p * (len(ps) - i))); tmp[m]['p_holm'] = run
        N['dl_mcnemar'][str(H)] = tmp
        # Holm over all seven competitors (four challenge-style re-implementations + three equal-input networks)
        allp = [(N['h2h_mcnemar'][f'{m}|{H}']['p'], 'h2h', m) for m in ['mlp_kf', 'rnn', 'similarity', 'cnn']] + [(tmp[m]['p'], 'dl', m) for m in tmp]; run = 0
        for i, (p, src, m) in enumerate(sorted(allp)):
            run = max(run, min(1, p * (len(allp) - i)))
            (N['h2h_mcnemar'][f'{m}|{H}'] if src == 'h2h' else tmp[m])['p_holm7'] = run
    N['dl_cfg'] = pd.read_csv('out/window/dl_warning_cfg_PHM08.csv').groupby(['method', 'H']).option.agg(lambda s: sorted(set(s))).reset_index().to_dict('records')

if os.path.exists('out/window/stw_timing.json'):
    lg = open('out/window/dl_warning.log').read(); N['compute'] = dict(stw_s=json.load(open('out/window/stw_timing.json'))['stw_seconds_per_fold'],
                                                                     dl_s=[int(x) for x in re.findall(r'fold \d done in (\d+)s', lg)])
# ---- tolerance windows and maintenance cost (multi_eval.py)
MDS = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'NCMAPSS14']
N['windows'] = {}; N['cost'] = {}
for ds in MDS:
    if not os.path.exists(f'out/multi/{ds}_windows.csv'): continue
    WR = pd.read_csv(f'out/multi/{ds}_windows.csv')
    N['windows'][ds] = {f'{lo}|{hi}|{H}': dict(pct=round(100 * float((g.cls == 'IN').mean()), 1), IN=int((g.cls == 'IN').sum()), n=int(len(g)),
                                                late_or_missed=int(g.cls.isin(['LATE', 'MISSED']).sum()), early=int((g.cls == 'EARLY').sum()), median_left=float(g.y.median()))
                        for (lo, hi, H), g in WR.groupby(['lo', 'hi', 'H'])}
    C = pd.read_csv(f'out/multi/{ds}_cost.csv'); S = C.groupby(['lead', 'rho']).sum(numeric_only=True); res = {}
    for (l, r), s in S.iterrows():
        rate = {p: float(s[p + '_cost'] / s[p + '_use']) for p in ('stw', 'age', 'rtf', 'pf')}
        res[f'{int(l)}|{int(r)}'] = dict(**{p + '_rate': round(v, 5) for p, v in rate.items()},
                                          stw_rel_pf=round(rate['stw'] / rate['pf'], 3), age_rel_pf=round(rate['age'] / rate['pf'], 3), rtf_rel_pf=round(rate['rtf'] / rate['pf'], 3),
                                          stw_saving_vs_age_pct=round(100 * (1 - rate['stw'] / rate['age']), 1), stw_fail=int(s.stw_fail), age_fail=int(s.age_fail), n=int(s.n),
                                          H_chosen=sorted(set(C[(C.lead == l) & (C.rho == r)].H.astype(int))))
    N['cost'][ds] = res
# reproduction check: window [-13, +2] of multi_eval equals the main results
N['windows_repro'] = {ds: [N['windows'][ds][f'-13|2|{H}']['IN'] == N['cv'][ds][str(H)]['IN'] for H in (10, 15, 20)] for ds in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'] if ds in N['windows']}
if 'NCMAPSS6' in N['windows']: N['windows_repro']['NCMAPSS6'] = [N['windows']['NCMAPSS6'][f'-13|2|{H}']['IN'] == N['ncm_detail'][str(H)]['IN'] for H in (10, 15, 20)]

# ---- window-centring theory check (theory_check.py)
if os.path.exists('out/theory/theory_check.csv'):
    T = pd.read_csv('out/theory/theory_check.csv'); N['theory'] = T.to_dict('records')
    N['theory_summary'] = dict(mean_abs_gap_realised_centred=round(float((T.realised_pct - T.centred_bound_pct).abs().mean()), 2),
                               max_abs_gap_realised_centred=round(float((T.realised_pct - T.centred_bound_pct).abs().max()), 2),
                               corr_realised_centred=round(float(np.corrcoef(T.realised_pct, T.centred_bound_pct)[0, 1]), 3),
                               mean_shift_minus_sstar=round(float((T.shift_mean - T.s_star).mean()), 2), n_rows=int(len(T)), n_above=int((T.realised_pct > T.centred_bound_pct).sum()))
    Tn = T[T.dataset != 'Bearing']; N['theory_summary'].update(mean_abs_gap_nb=round(float((Tn.realised_pct - Tn.centred_bound_pct).abs().mean()), 2), max_abs_gap_nb=round(float((Tn.realised_pct - Tn.centred_bound_pct).abs().max()), 2))

# ---- battery confirmation (battery_warning.py)
if os.path.exists('out/battery/warning_summary.json'):
    BS = json.load(open('out/battery/warning_summary.json')); N['battery'] = BS
    BA = pd.read_csv('out/battery/warning_results.csv'); N['battery_detail'] = {}
    for (an, m, H), g in BA.groupby(['analysis', 'method', 'H']):
        d_ = summarise(g); d_['median_left_cycles'] = float(g.y.median() * BS['kappa']); N['battery_detail'][f'{an}|{m}|{H}'] = d_
    N['battery_settings_H20'] = BA[(BA.analysis == 'cv123') & (BA.method == 'warning') & (BA.H == 20)].groupby('split')[['option', 'span', 'k', 'shift']].first().reset_index().to_dict('records')
    N['battery_lobo_H20'] = {s: dict(n=int(len(g)), IN=int((g.cls == 'IN').sum()), late=int((g.cls == 'LATE').sum()), early=int((g.cls == 'EARLY').sum()), missed=int((g.cls == 'MISSED').sum()))
                             for s, g in BA[(BA.analysis == 'lobo') & (BA.method == 'warning') & (BA.H == 20)].groupby('split')}
    Mb = pd.read_csv('battery/severson_cells.csv'); Lb = BA.drop_duplicates('unit').set_index('unit').life_cycles
    N['battery_data'] = dict(cells_total=int(len(Mb)), cells_used=int(BS['n_cells']), life_min=int(Lb.min()), life_max=int(Lb.max()), life_median=float(Lb.median()), kappa=int(BS['kappa']),
                             by_batch={int(b): int(n) for b, n in Lb.index.str[1].astype(int).value_counts().sort_index().items()},
                             policies=int(Mb[Mb.cell.isin(Lb.index)].policy.str.replace('-newstructure', '').nunique()),
                             protocol_sha256=open('battery/BATTERY_PROTOCOL.sha256').read().split()[0], protocol_written=open('battery/BATTERY_PROTOCOL.sha256').read().split('written ')[1].split(' (')[0])
    mb = Mb[Mb.cell.isin(Lb.index)].assign(pol=lambda x: x.policy.str.replace('-newstructure', '')); Pb = {b: set(g.pol) for b, g in mb.groupby('batch')}
    N['battery_batches'] = dict(policies={str(b): len(p) for b, p in Pb.items()}, shared={str(b): len(p & set.union(*[Pb[c] for c in Pb if c != b])) for b, p in Pb.items()},
                                life_median={str(b): int(round(float(Lb[Lb.index.str[1] == str(b)].median()))) for b in Pb})
    Sb = pd.read_csv('battery/severson_cycle_summary.csv.gz'); Sb = Sb[Sb.cell.isin(Lb.index)]; N['battery_rows'] = int((Sb.cycle <= Sb.cell.map(Lb)).sum())
if os.path.exists('out/battery/cost.csv'):
    C = pd.read_csv('out/battery/cost.csv'); S = C.groupby(['lead_cycles', 'rho']).sum(numeric_only=True); N['battery_cost'] = {}
    for (l, r), s in S.iterrows():
        rate = {p: float(s[p + '_cost'] / s[p + '_use']) for p in ('stw', 'age', 'rtf', 'pf')}
        N['battery_cost'][f'{int(l)}|{int(r)}'] = dict(stw_rel_pf=round(rate['stw'] / rate['pf'], 3), age_rel_pf=round(rate['age'] / rate['pf'], 3), rtf_rel_pf=round(rate['rtf'] / rate['pf'], 3),
                                                       stw_saving_vs_age_pct=round(100 * (1 - rate['stw'] / rate['age']), 1), stw_fail=int(s.stw_fail), age_fail=int(s.age_fail), n=int(s.n))
# ---- bearing confirmation (bearing_warning.py), STW-T (stwt_all.py), 30 iterations (rep30.py)
if os.path.exists('out/bearing/warning_summary.json'):
    BG = json.load(open('out/bearing/warning_summary.json')); N['bearing'] = BG
    N['bearing_detail'] = {f"{s['analysis']}|{s['method']}|{s['H']}": s for s in BG['summary']}
    FA = pd.read_csv('out/bearing/warning_results.csv'); Lg = FA.drop_duplicates('unit').set_index('unit').life_snapshots
    N['bearing_data'] = dict(n=int(BG['n_bearings']), kappa=int(BG['kappa']), life_min=int(Lg.min()), life_max=int(Lg.max()), life_median=float(Lg.median()),
                             protocol_sha256=open('bearing/BEARING_PROTOCOL.sha256').read().split()[0], protocol_written=open('bearing/BEARING_PROTOCOL.sha256').read().split('written ')[1].split(' (')[0])
    import bearing_warning as _BWg
    _B, _k, _ = _BWg.load(); onset = []
    for b_, g_ in _B.groupby('bearing'):
        r_ = (g_.rms_h + g_.rms_v).values; base_ = r_[:20].mean(); ab_ = r_ > 1.5 * base_
        st_ = next((len(r_) - i for i in range(len(r_)) if ab_[i:].all()), 0); onset.append(st_)
    BW20 = FA[(FA.analysis == 'cv') & (FA.method == 'warning') & (FA.H == 20)].set_index('unit'); blk = _B.groupby('bearing').size(); cond = _B.groupby('bearing').condition.first()
    N['bearing_table'] = [dict(bearing=b_, condition=int(cond[b_]), life=int(Lg[b_]), blocks=int(blk[b_]), onset=int(o_), cls=str(BW20.cls[b_]), left=None if pd.isna(BW20.y[b_]) else float(BW20.y[b_]))
                          for b_, o_ in zip(sorted(_B.bearing.unique()), onset)]
    N['bearing_rows'] = int(pd.read_csv('bearing/femto_snapshot_features.csv.gz').shape[0])
    onset = np.array(onset); N['bearing_onset'] = dict(n_le6=int((onset <= 6).sum()), n_ge20=int((onset >= 20).sum()), median=float(np.median(onset)), values=onset.tolist())
if os.path.isdir('out/stwt'):
    N['stwt'] = {}
    for f in sorted(os.listdir('out/stwt')):
        A_ = pd.read_csv('out/stwt/' + f); ds_ = f[:-4]; d_ = {}
        for H_, g_ in A_.groupby('H'):
            w_ = g_[g_.method == 'warning'].set_index('unit').cls == 'IN'; t_ = g_[g_.method == 'warning_T'].set_index('unit').cls == 'IN'; w_, t_ = w_.align(t_, join='inner')
            x_ = int((t_ & ~w_).sum()); y_ = int((~t_ & w_).sum())
            d_[str(H_)] = dict(stw=round(100 * float(w_.mean()), 1), stwt=round(100 * float(t_.mean()), 1), n=int(len(w_)), t_only=x_, s_only=y_, p=float(binomtest(x_, x_ + y_, .5).pvalue) if x_ + y_ else 1.0,
                               shift_stw=round(float(g_[g_.method == 'warning']['shift'].mean()), 2), shift_stwt=round(float(g_[g_.method == 'warning_T']['shift'].mean()), 2))
        N['stwt'][ds_] = d_
    BF = pd.read_csv('out/bearing/warning_results.csv'); N['stwt']['Bearing'] = {}
    for H_, g_ in BF[BF.analysis == 'cv'].groupby('H'):
        N['stwt']['Bearing'][str(H_)] = dict(stw=round(100 * float((g_[g_.method == 'warning'].cls == 'IN').mean()), 1), stwt=round(100 * float((g_[g_.method == 'warning_T'].cls == 'IN').mean()), 1), n=int((g_.method == 'warning').sum()))
if os.path.exists('out/rep30/rep30_results_all.csv'):
    R3 = pd.read_csv('out/rep30/rep30_results_all.csv'); T3 = pd.read_csv('out/rep30/per_iteration.csv')
    N['rep30_table'] = [dict(it=int(r.repetition), IN=int(r.IN), acc=float(r.acc), late=int(r.late), early=int(r.early), missed=int(r.missed), left=float(r.mean_left)) for r in T3.itertuples()]
    g3 = R3.groupby('repetition'); c3 = g3.result.apply(lambda s: int((s == 'IN').sum())); ml = g3.true_cycles_left.mean()
    N['rep30'] = dict(reps=int(R3.repetition.nunique()), counts=c3.tolist(), mean=round(float(c3.mean()), 2), sd=round(float(c3.std()), 2), min=int(c3.min()), max=int(c3.max()),
                      acc_mean=round(float(100 * c3.mean() / 50), 1), acc_sd=round(float(100 * c3.std() / 50), 1), n_ge48=int((c3 >= 48).sum()), n_ge46=int((c3 >= 46).sum()),
                      late_mean=round(float(g3.result.apply(lambda s: s.isin(['LATE', 'MISSED']).sum()).mean()), 2), early_mean=round(float(g3.result.apply(lambda s: (s == 'EARLY').sum()).mean()), 2),
                      missed_total=int((R3.result == 'MISSED').sum()), left_mean=round(float(ml.mean()), 1), left_min=round(float(ml.min()), 1), left_max=round(float(ml.max()), 1),
                      engines_covered=int(R3.engine.nunique()), same_as_rep20=bool((R3[R3.repetition <= 20].merge(pd.read_csv('out/rep50/rep50_results.csv'), on=['repetition', 'engine']).pipe(lambda m: (m.result_x == m.result_y).all()))))
def _clean(o):
    if isinstance(o, dict): return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_clean(v) for v in o]
    if isinstance(o, (float, np.floating)) and not np.isfinite(o): return None
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    return o
N = _clean(N)
json.dump(N, open('paper2/numbers.json', 'w'), indent=1, default=float, allow_nan=False); print('keys', list(N))
print(json.dumps({k: N[k] for k in ('cv_pooled', 'rep50')}, indent=0))
print({ds: (N['cv'][ds]['20']['pct'], N['cv'][ds]['20']['early_limit_active_pct'], N['cv'][ds]['20']['in_when_active']) for ds in N['cv']})
