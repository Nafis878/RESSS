"""Writes key_numbers.md for the third revision from paper5/numbers.json: every number used in the abstract, the key-numbers
table and the conclusion of the rewritten manuscript, with the script and result file that produce it.
Usage: python kam/make_key_numbers.py > key_numbers.md
"""
import json
N = json.load(open('paper5/numbers.json')); R3, R4, R5 = N['rev3'], N['rev4'], N['rev5']
f1 = lambda x: f'{x:.1f}'
f2 = lambda x: f'{x:.2f}'
FM, FMP = R4['fixed_matched']['variants'], R4['fixed_matched']['paired']
F4, F4P = R5['fixed_matched_FD004']['variants'], R5['fixed_matched_FD004']['paired']
BP = R4['battery_physical']; BN = R5['battery_cost_nested']; HC = R5['hi_cal']; KM = R5['kam']; FR = R5['fragility']
CT = R3['controls']; RDS = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'Battery']
gap = max(abs(CT[d]['20']['STW_const']['pct'] - CT[d]['20']['STW']['pct']) for d in RDS)
kv = lambda an: [BP[f'{an}|fixed_kappa|recipe|{k}']['pct'] for k in (2, 3, 4, 5, 6)]
bd = N['battery_detail']; B3 = R3['battery']['summary']
t = lambda d, p, q=0.1: KM[d]['table'][f'{q}|{p}']
pr = lambda d, a, b, q=0.1: dict(KM[d]['pairs'][f'{q}|{a}|{b}'], v={'mine': 'ours', 'theirs': 'theirs', 'unclear': 'unclear'}[KM[d]['pairs'][f'{q}|{a}|{b}']['v']])
L = []
w = L.append
w('# Key numbers (third revision)\n')
w('Every number below is computed by a script and stored in `paper5/numbers.json`, from which the manuscript is built; the build checks the text against it (`paper5/tex/build_checks.txt`). Frozen result files are in `results/kam/` and `results/audit/`. Status: every analysis of this revision is exploratory, with its plan hashed before the run (`kam/PHASE2_PLAN.md`, `kam/PHASE3_4_PLAN.md`).\n')
w('## A. Battery: one analysis, five conventions (primary: C)\n')
w('| Conv. | κ from | Task | Recipe, CV by cell | Recipe, batch held out | Capacity trend, CV / held out | Cost analysis | Source |')
w('|---|---|---|---|---|---|---|---|')
w(f"| A. Protocol (provenance only) | all cells (κ = 3) | blocks | {bd['cv123|warning|20']['IN']}/123 ({f1(bd['cv123|warning|20']['pct'])}%) | {bd['lobo|warning|20']['IN']}/123 ({f1(bd['lobo|warning|20']['pct'])}%) | – | – | `battery_warning.py` → `results/battery/` |")
w(f"| B. Intermediate | outer training cells | blocks | {B3['cv123|warning|20']['IN']}/123 ({f1(B3['cv123|warning|20']['pct'])}%) | {B3['lobo|warning|20']['IN']}/123 ({f1(B3['lobo|warning|20']['pct'])}%) | {R3['battery_baselines']['cv123|capacity_trend']['pct']}% / {R3['battery_baselines']['lobo|capacity_trend']['pct']}% | supplement S11 (provenance) | `audit_confirmations.py`, `audit_battery_cost2.py` |")
rc, rl = BP['cv123|rule_nested|recipe'], BP['lobo|rule_nested|recipe']; tc, tl = BP['cv123|rule_kappa|capacity_trend'], BP['lobo|rule_kappa|capacity_trend']
w(f"| **C. Fully nested, κ by rule (primary)** | each training subset | cycles | **{rc['IN']}/123 ({f1(rc['pct'])}%)** | **{rl['IN']}/123 ({f1(rl['pct'])}%)** | {tc['IN']}/123 ({f1(tc['pct'])}%) / {tl['IN']}/123 ({f1(tl['pct'])}%) | **main text Tables 8 and 10, Fig. 9** | `audit_battery_physical.py`, `audit_battery_cost_nested.py` |")
w(f"| D. κ by inner CV | selected in 2–6 | cycles | {f1(BP['cv123|cv_selected|recipe']['pct'])}% | {f1(BP['lobo|cv_selected|recipe']['pct'])}% | – | – | `audit_battery_physical.py` |")
w(f"| E. Fixed κ = 2–6 | fixed | cycles | {f1(min(kv('cv123')))}–{f1(max(kv('cv123')))}% | {f1(min(kv('lobo')))}–{f1(max(kv('lobo')))}% | – | – | `audit_battery_physical.py` |\n")
w(f"Wherever the primary held-out-batch rate ({f1(rl['pct'])}%) appears, the paper gives next to it the fixed-κ range ({f1(min(kv('lobo')))}–{f1(max(kv('lobo')))}%), κ by inner CV ({f1(BP['lobo|cv_selected|recipe']['pct'])}%), convention A ({f1(bd['lobo|warning|20']['pct'])}%) and convention B ({f1(B3['lobo|warning|20']['pct'])}%). Still on convention B (labelled in the paper): the battery timing-control row (Table 7) and the battery shift study (Fig. 6).\n")
w('## B. Numbers in the abstract, the key-numbers table (Table 1) and the conclusion\n')
w('| Number | Value | Script → result file | Key in `numbers.json` |')
w('|---|---|---|---|')
w(f"| PHM08, same calibrated fixed-time model at 50% / 90% of life (matched) | {FM['fixed_f50']['IN']}/218 ({f1(FM['fixed_f50']['pct'])}%) / {FM['fixed_f90']['IN']}/218 ({f1(FM['fixed_f90']['pct'])}%) | `audit_fixed_matched.py` → `fixed_matched.json` | `rev4.fixed_matched` |")
w(f"| PHM08, self-timed recipe vs its regressor at 90% of life | {f1(FM['recipe_self']['pct'])}% vs {f1(FM['recipe_f90']['pct'])}% (discordant {FMP['recipe_self|recipe_f90']['only_a']}/{FMP['recipe_self|recipe_f90']['only_b']}, p = {FMP['recipe_self|recipe_f90']['p']:.3f}) | same | same |")
w(f"| FD004, fixed-time model at 50% / 90% of life; recipe self-timed vs regressor at 90% | {f1(F4['fixed_f50']['pct'])}% / {f1(F4['fixed_f90']['pct'])}%; {f1(F4['recipe_self']['pct'])}% vs {f1(F4['recipe_f90']['pct'])}% (discordant {F4P['recipe_self|recipe_f90']['only_a']}/{F4P['recipe_self|recipe_f90']['only_b']}, p = {F4P['recipe_self|recipe_f90']['p']:.3f}); reproduces Table 6 FD004 unit by unit: {R5['fixed_matched_FD004']['recipe_self_reproduces_main']} | `audit_fixed_matched.py --ds FD004` → `fixed_matched_FD004.json` | `rev5.fixed_matched_FD004` |")
w(f"| Constant estimate vs model estimate, largest gap at H = 20 (7 datasets; battery conv. B) | {f1(gap)} points | `rev_experiments.py`, `audit_battery_controls.py` | `rev3.controls` |")
he = [HC[d]['20']['pct'] for d in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']]
w(f"| Calibrated health indicator, H = 20: PHM08 and FD001–FD004 / N-CMAPSS | {f1(min(he))}–{f1(max(he))}% / {f1(HC['NCMAPSS6']['20']['pct'])}% (recipe {f1(CT['NCMAPSS6']['20']['STW']['pct'])}%; Holm p = {HC['NCMAPSS6']['20']['vs_recipe']['p_holm']:.3f}) | `audit_hi_calibrated.py` → `hi_calibrated_<ds>.csv` | `rev5.hi_cal` |")
cb = R3['cost_by_ds']
w(f"| Window-tuned vs age replacement, cells significantly cheaper (of 16) | PHM08 {cb['PHM08']['age']['window_sig_cheaper']}, FD001 {cb['FD001']['age']['window_sig_cheaper']}, FD002 {cb['FD002']['age']['window_sig_cheaper']}, FD003 {cb['FD003']['age']['window_sig_cheaper']}, FD004 {cb['FD004']['age']['window_sig_cheaper']}, N-CMAPSS {cb['NCMAPSS6']['age']['window_sig_cheaper']}, battery (conv. C) {BN['cv123']['summary']['STW_window|age']['a_sig_cheaper']} | `audit_cost.py`, `audit_battery_cost_nested.py` | `rev3.cost_by_ds`, `rev5.battery_cost_nested` |")
w(f"| M on FD001, c_p/c_c = 0.1: their policy 1 (P-res) / our 1-SE / our window-tuned | {f2(t('fd001', 'P1_res_opt_mid')['M'])}% / {f2(t('fd001', 'STW_cost_1se')['M'])}% / {f2(t('fd001', 'STW_window')['M'])}% | `kam/kam_fd001.py`, `kam_fd001_summarize.py` → `fd001_cv_table.csv` | `rev5.kam.fd001.table` |")
for d in ('fd001', 'fd002', 'fd003', 'fd004'):
    a, b = pr(d, 'STW_window', 'P1_res_opt_mid'), pr(d, 'STW_cost_1se', 'P1_res_opt_mid')
    w(f"| {d.upper()}, c_p/c_c = 0.1: window-tuned − policy 1 (P-res); 1-SE − policy 1 (P-res) | {a['d']:+.2f} pp ({a['lo']:+.2f}, {a['hi']:+.2f}), {a['v']}; {b['d']:+.2f} pp ({b['lo']:+.2f}, {b['hi']:+.2f}), {b['v']} | `kam/kam_fd001.py --ds`, `kam_fd001_summarize.py --ds` → `{d}_cv_pairs.csv` | `rev5.kam.{d}.pairs` |")
MP = ['P1_res_opt_mid', 'P1_res_q', 'P1_cls_opt_mid', 'P1_cls_q', 'P3_res60', 'P3_res125', 'STW_window', 'STW_cost_1se', 'STW_cost', 'HI_cost', 'age_grid']
best = {d: min(MP, key=lambda p: t(d, p)['M']) for d in ('fd001', 'fd002', 'fd003', 'fd004')}
w('| Lowest M at c_p/c_c = 0.1 (grid-mapped policies) | ' + '; '.join(f"{d.upper()} {best[d]} {f2(t(d, best[d])['M'])}%" for d in best) + ' | `kam_fd001_summarize.py` → `<ds>_cv_table.csv` | `rev5.kam.<ds>.table` |')
w('| Window-tuned − policy 1 (P-cls), c_p/c_c = 0.1 | ' + '; '.join(f"{d.upper()} {pr(d, 'STW_window', 'P1_cls_opt_mid')['d']:+.2f} pp, {pr(d, 'STW_window', 'P1_cls_opt_mid')['v']}" for d in ('fd001', 'fd002', 'fd003', 'fd004')) + ' | `<ds>_cv_pairs.csv` | `rev5.kam.<ds>.pairs` |')
st = lambda p: sum(FR['tally'][f'{d}|cv|{p}']['fail_small'] for d in ('fd001', 'fd002', 'fd003', 'fd004'))
w(f"| Fold–ratio cells with ≥ 1 test failure, c_p/c_c ≤ 0.1, FD001–FD004 (of 80): P1 P-cls opt / p = c_p/c_c; STW plain / 1-SE / window | {st('P1_cls_opt_mid')} / {st('P1_cls_q')}; {st('STW_cost')} / {st('STW_cost_1se')} / {st('STW_window')} | `kam/kam_fragility.py` → `fragility_tally.csv` | `rev5.fragility.tally` |")
rt = lambda p: FR['tally'][f'fd001|rs|{p}']['fail_small']
if 'fd001|rs|STW_window' in FR['tally']:
    w(f"| Split–ratio cells with ≥ 1 test failure, c_p/c_c ≤ 0.1, thirty FD001 splits (of 120): P1 P-cls opt / P-res opt / P-cls p = c_p/c_c / P-res p = c_p/c_c; STW plain / 1-SE / window | {rt('P1_cls_opt_mid')} / {rt('P1_res_opt_mid')} / {rt('P1_cls_q')} / {rt('P1_res_q')}; {rt('STW_cost')} / {rt('STW_cost_1se')} / {rt('STW_window')} | same → `fragility_tally.csv` | `rev5.fragility.tally` |")
w(f"| Decision rule for 'direct cost tuning is fragile' | {', '.join(f'{k}: {v}' for k, v in FR['verdict'].items())} | same → `fragility_verdict.csv` | `rev5.fragility.verdict` |")
w(f"| Battery recipe, conv. C: CV / batch held out | {f1(rc['pct'])}% / {f1(rl['pct'])}% (held out: fixed κ {f1(min(kv('lobo')))}–{f1(max(kv('lobo')))}%, κ by inner CV {f1(BP['lobo|cv_selected|recipe']['pct'])}%, conv. A {f1(bd['lobo|warning|20']['pct'])}%, conv. B {f1(B3['lobo|warning|20']['pct'])}%) | `audit_battery_physical.py` | `rev4.battery_physical` |")
w(f"| Capacity trend, conv. C: CV / batch held out | {f1(tc['pct'])}% / {f1(tl['pct'])}% | same | same |")
s = BN['lobo']['summary']
w(f"| Battery cost, conv. C, batch held out: trend significantly cheaper than the recipe (cells of 16; never dearer) | window-tuned pair {s['trend_window|STW_window']['a_sig_cheaper']}; cost-tuned trend 1-SE vs window-tuned recipe {s['trend_cost_1se|STW_window']['a_sig_cheaper']}; 1-SE pair {s['trend_cost_1se|STW_cost_1se']['a_sig_cheaper']}; plain pair {s['trend_cost|STW_cost']['a_sig_cheaper']} | `audit_battery_cost_nested.py` → `cost_battery_nested.csv` | `rev5.battery_cost_nested` |")
w(f"| N-CMAPSS (pre-specified) / bearings | {N['ncm_detail_H20']['IN']}/99 ({f1(100 * N['ncm_detail_H20']['IN'] / 99)}%) / 0 of 17 | `ncm_warning.py`, `bearing_warning.py`, `audit_confirmations.py` | `ncm`, `bearing_detail`, `rev3.bearing` |\n")
w('## C. Re-implementation of the metric and checks\n')
ge = R5['grid_effect']
w(f"- **Reference-grid effect** (ΔT = 10): " + ', '.join(f"{d} {ge[d + '|10']:.2f}%" for d in ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'Battery']) + f"; battery ΔT = 30: {ge['Battery|30']:.2f}%. Source: `kam/kam_grid_effect.py` → `grid_effect_summary.csv`.")
w(f"- **Unmapped M < 0**: {R5['grid_negative']['n']} cases, minimum {R5['grid_negative']['min_pct']:.2f}% (battery, ΔT = 30). Same source (`grid_effect_policies.csv`).")
w(f"- **Simulator check**: optimised policy 1 lowest at {', '.join(f'{c}/7 (σ = {s_})' for s_, c in R5['sim']['p1_lowest'])}; policy 3 < policy 2 at {', '.join(f'{c}/7 (σ = {s_})' for s_, c in R5['sim']['p3_lt_p2'])}. Source: `kam/kam_simulator.py` → `sim_checks.txt`.")
w(f"- **Re-run after the workspace reset (check R0)**: " + '; '.join(R5['r0']))
for d in ('fd001', 'fd002', 'fd003', 'fd004'): w(f"- **Leakage {d.upper()}**: " + '; '.join(KM[d]['leakage']))
w('- **Battery cost R4a**: ' + '; '.join(BN['check']))
w('- **Calibrated indicator R4b**: ' + '; '.join(HC['check']))
w(f"- **Tie rules** (decisions differing between 'mid' and 'max'): " + ', '.join(f"{k}: {v['differ']} of {v['decisions']}" for k, v in FR['tie'].items()))
print('\n'.join(L))
