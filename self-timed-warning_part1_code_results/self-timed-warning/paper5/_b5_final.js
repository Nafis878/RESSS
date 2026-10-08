
// ================================================================ cost narrative, discussion of cost, conclusion and front matter
const ALLC = d => cellKeys(d).map(k => CO3[d][k]);
const rngTxt = v => { const a = Math.min(...v), b = Math.max(...v); return a.toFixed(2) === b.toFixed(2) ? a.toFixed(2) : `${a.toFixed(2)}–${b.toFixed(2)}`; };
const dsList = arr => arr.map(d => RNAME[d]).join(', ');
const ageWinDS = RDS.filter(d => CBD[d].age.window_sig_cheaper >= 12);
const ageNoneDS = RDS.filter(d => CBD[d].age.window_sig_cheaper === 0);
const sig = (o, k) => RDS.map(d => [d, CBD[d][o] ? CBD[d][o][k] : 0]);
const fmtSig = (o, k) => sig(o, k).filter(([, v]) => v > 0).map(([d, v]) => `${RNAME[d]} ${v}`).join(', ');
const tot = (o, k) => sig(o, k).reduce((a, [, v]) => a + v, 0);
const RG3 = R5.regret;                       // battery cells from the fully nested run (kam/make_rev5_numbers.py)
const andList = a => a.length > 1 ? a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1] : a[0];
const cellsList = (o, k) => { const pos = RDS.filter(d => CBD[d][o] && CBD[d][o][k] > 0), zero = RDS.filter(d => CBD[d][o] && CBD[d][o][k] === 0);
  const nm = d => d === 'Battery' ? 'the batteries' : RNAME[d];
  if (!pos.length) return 'no cell on any dataset';
  if (pos.length === 1) return `${CBD[pos[0]][o][k]} of the 16 cells on ${nm(pos[0])} (none elsewhere)`;
  return `${andList(pos.map(d => CBD[d][o][k]))} of the 16 cells on ${andList(pos.map(nm))}${zero.length ? ` (none on ${andList(zero.map(nm))})` : ''}`; };
const POLL = { STW_window: 'window-tuned STW', STW_cost: 'cost-tuned STW', STW_cost_1se: 'cost-tuned STW with the 1-SE rule', STW_cost_q80: 'cost-tuned STW (80th percentile)', Q10_cost: 'cost-tuned quantile alarm', Q10_cost_1se: 'quantile alarm with the 1-SE rule', HI_cost: 'health-indicator alarm', capacity_cost: 'cost-tuned capacity threshold', capacity_cost_1se: 'capacity threshold with the 1-SE rule' };
const bestByDS = RDS.map(d => { const ps = ['STW_window', 'STW_cost', 'STW_cost_1se', 'STW_cost_q80', 'Q10_cost', 'Q10_cost_1se', 'HI_cost'].concat(d === 'Battery' ? ['capacity_cost', 'capacity_cost_1se'] : []);
  const m = ps.map(p => [p, RG3[p].by_ds[d]]).sort((a, b) => a[1] - b[1]); return [d, m[0][0], m[0][1]]; });

function COST_NCM_PHRASE() { return ', and its alarms were not significantly cheaper than age replacement in any cost setting'; }

function COST_TEXT3() {
  must(RG3.STW_cost_1se.max < RG3.STW_window.max && RG3.STW_window.max < RG3.STW_cost.max && RG3.Q10_cost.max > RG3.STW_window.max, 'largest excess cost: 1-SE < window < plain cost tuning; quantile alarm above window'); must(ageNoneDS.length === 1 && ageNoneDS[0] === 'NCMAPSS6', 'window-tuned alarms never significantly cheaper than age replacement on N-CMAPSS, and significantly cheaper in at least 12 of 16 cells on every other dataset');
  must(RDS.every(d => CBD[d].age.window_sig_dearer === 0), 'window-tuned alarms never significantly more expensive than age replacement');
  const ex = CO3.PHM08['10|50'];
  const p = [
    `Table 8 and Fig. 7 compare the policies under identical splits, information, lead times and cost ratios. Against optimal age replacement, the window-tuned alarms were cheaper with a paired interval excluding equality in ${ageWinDS.map(d => `${CBD[d].age.window_sig_cheaper}`).join(', ')} of 16 cells on ${dsList(ageWinDS)}, respectively. Their cost rate was ${rngTxt(ALLC('PHM08').map(c => c.STW_window.ratio))} times that of perfect foresight on PHM08, against ${rngTxt(ALLC('PHM08').map(c => c.age.ratio))} for age replacement. N-CMAPSS was the exception: in no cell did the interval exclude equality, and the point estimate favoured age replacement in ${16 - CBD.NCMAPSS6.age.window_point_cheaper} of 16 cells.`,
    `Against policies tuned directly to cost the results depend on the dataset (Table 8). Plain cost tuning of the same regressor was significantly cheaper than window tuning in ${cellsList('STW_cost', 'window_sig_dearer')}, and significantly more expensive in ${cellsList('STW_cost', 'window_sig_cheaper')}. Its occasional large losses remain. On PHM08 with ℓ = 10 and ρ = 50 it cost ${ex.STW_cost.ratio.toFixed(2)} times perfect foresight, against ${ex.STW_window.ratio.toFixed(2)} for window tuning, with ${ex.STW_cost.failures} test failures against ${ex.STW_window.failures}. The one-standard-error rule reduced that loss to ${ex.STW_cost_1se.ratio.toFixed(2)}, still above window tuning there. Across cells it was significantly cheaper than window tuning in ${cellsList('STW_cost_1se', 'window_sig_dearer')}, and significantly more expensive in ${cellsList('STW_cost_1se', 'window_sig_cheaper')}. The cost-tuned 10% quantile alarm was significantly cheaper than window tuning in ${cellsList('Q10_cost', 'window_sig_dearer')}, and more expensive in ${cellsList('Q10_cost', 'window_sig_cheaper')}. The health-indicator alarm was usually the more expensive: window tuning was significantly cheaper in ${cellsList('HI_cost', 'window_sig_cheaper')}, and more expensive in ${cellsList('HI_cost', 'window_sig_dearer')}. On the batteries, the cost-tuned capacity-threshold policy was significantly cheaper than window tuning in ${CBD.Battery.capacity_cost.window_sig_dearer} cells and never significantly more expensive.`,
    `Relative to the cheapest condition-based policy in each cell, the mean excess cost over the 112 cells was ${f1(RG3.STW_window.mean)}% for window tuning, ${f1(RG3.STW_cost.mean)}% for plain cost tuning, ${f1(RG3.STW_cost_1se.mean)}% with the one-standard-error rule, ${f1(RG3.Q10_cost.mean)}% for the quantile alarm (${f1(RG3.Q10_cost_1se.mean)}% with the one-standard-error rule), ${f1(RG3.HI_cost.mean)}% for the health-indicator alarm and ${f1(RG3.age.mean)}% for age replacement. These means are descriptive, because the cells are correlated. The policy with the lowest mean excess cost differed between datasets: ${bestByDS.map(([d, pp]) => `${POLL[pp]} on ${RNAME[d]}`).join(', ')}. The largest single excess cost was ${f1(RG3.STW_cost.max)}% for plain cost tuning (${RNAME[RG3.STW_cost.max_ds]}), ${f1(RG3.STW_window.max)}% for window tuning (${RNAME[RG3.STW_window.max_ds]}, ℓ = ${RG3.STW_window.max_cell.split('|')[0]}, ρ = ${RG3.STW_window.max_cell.split('|')[1]}), ${f1(RG3.STW_cost_1se.max)}% with the one-standard-error rule (${RNAME[RG3.STW_cost_1se.max_ds]}) and ${f1(RG3.Q10_cost.max)}% for the quantile alarm (${RNAME[RG3.Q10_cost.max_ds]}). Window tuning thus avoided the largest losses of plain cost tuning on several datasets, plausibly through the margin that the narrow late side of the window builds in, but that mechanism was not tested and it did not hold on N-CMAPSS. No tuning rule was cheapest on every dataset, and window tuning is not a reliable surrogate for cost optimisation.`];
  return p;
}

function COST_DISC() {
  must(CBD.FD003.STW_cost_1se.window_sig_cheaper >= 12 && CBD.Battery.STW_cost_1se.window_sig_cheaper >= 12, 'window tuning significantly cheaper than the 1-SE rule in most cells on FD003 and the batteries');
  return [`Kamariotis et al. (2024) argue that prognostic algorithms and the policies built on them should be judged and tuned by the long-run cost of the decisions they induce. Our results support evaluating alarms by cost, with a qualification about how the cost is minimised. Minimising the empirical cost rate over about two thousand settings sometimes selected alarms with too little margin and produced large losses when failures were expensive. A one-standard-error rule reduced the largest losses, a lower quantile was often cheaper but did not avoid them, and no tuning rule was cheapest on every dataset. Window tuning was cheaper than the one-standard-error rule on FD003 and the batteries and more expensive on several other datasets. Its settings other than the warning level do not depend on cost ratios, which are often uncertain in practice. The window is best regarded as an operational specification, not a proxy for cost. Where cost ratios and lead times can be estimated, tuning to the cost with a safeguard against selection noise should be compared with it on the fleet's own history.`];
}

function COST_SUPP_TEXT() {
  return `The tables of this section give, for every dataset, lead time ℓ (cycles) and cost ratio ρ, the long-run cost rate of each policy relative to perfect foresight (1.00 = replacement one cycle before every failure). All policies were tuned on the same out-of-fold predictions of the training units of each outer fold and applied once to its test units. The window-tuned, plain cost-tuned, health-indicator, age-replacement and perfect-foresight results reproduce those of an earlier, separate run unit by unit on the six engine datasets; the battery results are from the fully nested analysis with the task in cycles (convention C). Run-to-failure cost ${rngTxt(RDS.flatMap(d => ALLC(d).filter((c, i) => i % 4 === 0).map(c => c.run_to_failure.ratio)))} times perfect foresight at ρ = 5 and up to ${Math.max(...RDS.flatMap(d => ALLC(d).map(c => c.run_to_failure.ratio))).toFixed(1)} at ρ = 50.`;
}
function COST_SUPP_TABLES() {
  return RDS.map(d => { const ps = ['STW_window', 'STW_cost', 'STW_cost_1se', 'STW_cost_q80', 'Q10_cost', 'Q10_cost_1se', 'HI_cost'].concat(d === 'Battery' ? ['capacity_cost', 'capacity_cost_1se'] : []).concat(['age']);
    const short = { STW_window: 'STW window', STW_cost: 'STW cost', STW_cost_1se: 'STW cost 1-SE', STW_cost_q80: 'STW cost q80', Q10_cost: 'Q10 cost', Q10_cost_1se: 'Q10 cost 1-SE', HI_cost: 'HI cost', capacity_cost: 'Capacity cost', capacity_cost_1se: 'Capacity 1-SE', age: 'Age' };
    return tableS(`Cost rate relative to perfect foresight, ${RNAME[d]}${d === 'Battery' ? ' (fully nested, convention C; cross-validation by cell; ℓ in cycles)' : ''}.`, ['ℓ', 'ρ', ...ps.map(p => short[p])],
      cellKeys(d).map(k => { const [l, r] = k.split('|'); return [l, r, ...ps.map(p => CO3[d][k][p].ratio.toFixed(2))]; }),
      [500, 500, ...ps.map(() => Math.round(8000 / ps.length))]); });
}

// ---------------------------------------------------------------- key-numbers table (Table 1), placed early in the paper
function KEY_TABLE() {
  const CT5 = R3.controls, gaps = RDS.map(d => CT5[d]['20'].STW_const.pct - CT5[d]['20'].STW.pct), gmax = Math.max(...gaps.map(Math.abs));
  const HCe = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'].map(d => HC[d]['20'].pct), Fe = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'].map(d => CT5[d]['20'].STW.pct);
  const t1 = kt('fd001', 0.1, 'P1_res_opt_mid'), s1 = kt('fd001', 0.1, 'STW_cost_1se'), w1 = kt('fd001', 0.1, 'STW_window');
  const thW = KDS.filter(d => kpr(d, 0.1, 'STW_window', 'P1_res_opt_mid').v === 'theirs').map(d => d.toUpperCase());
  const unW = KDS.filter(d => kpr(d, 0.1, 'STW_window', 'P1_res_opt_mid').v === 'unclear').map(d => d.toUpperCase());
  const miW = KDS.filter(d => kpr(d, 0.1, 'STW_window', 'P1_res_opt_mid').v === 'mine').map(d => d.toUpperCase());
  const ftal = p => KDS.reduce((a, d) => a + FRG.tally[`${d}|cv|${p}`].fail_small, 0);
  const lk = BN.lobo.summary['trend_cost_1se|STW_window'], lw = BN.lobo.summary['trend_window|STW_window'];
  const F4 = FM4.variants;
  return table('Key numbers of this study and the analysis behind each. Status: see Table 3; every exploratory analysis was added after the main results were known. Battery conventions (Section 5.2): A, κ = 3 from all cells, as in the protocol; B, κ from the outer training cells, task in blocks; C, fully nested, task in cycles (primary).',
    ['Question', 'Result', 'Value', 'Analysis and status', 'Where'],
    [['Q1', 'Same calibrated fixed-time model at half and at 90% of life (PHM08)', `${f1(FMV.fixed_f50.pct)}% vs ${f1(FMV.fixed_f90.pct)}% in the window`, 'Matched, cross-fitted; exploratory', 'Table 5'],
     ['Q1', 'Self-timed recipe vs its regressor at 90% of life (PHM08)', `${f1(FMV.recipe_self.pct)}% vs ${f1(FMV.recipe_f90.pct)}% (${peq(FMP['recipe_self|recipe_f90'].p)})`, 'As above', 'Table 5'],
     ['Q1', 'The same two comparisons on FD004', `${f1(F4.fixed_f50.pct)}% vs ${f1(F4.fixed_f90.pct)}%; ${f1(F4.recipe_self.pct)}% vs ${f1(F4.recipe_f90.pct)}% (${peq(FM4.paired['recipe_self|recipe_f90'].p)})`, 'As above; plan hashed before the run', 'Table 5'],
     ['Q2', 'Constant estimate at the recipe\'s alarm times: largest difference from the model\'s estimate', `${f1(gmax)} points (7 datasets, none significant)`, 'Timing control; exploratory (battery: convention B)', 'Table 7'],
     ['Q2', 'Health-indicator alarm calibrated to cycles, recipe\'s trigger: PHM08 and FD001–FD004 / N-CMAPSS', `${f1(Math.min(...HCe))}–${f1(Math.max(...HCe))}% (recipe ${f1(Math.min(...Fe))}–${f1(Math.max(...Fe))}%) / ${f1(HC.NCMAPSS6['20'].pct)}% (recipe ${f1(CT5.NCMAPSS6['20'].STW.pct)}%)`, 'Exploratory; plan hashed before the run', 'Table 7'],
     ['Q3', 'Window-tuned alarms significantly cheaper than age replacement (cells of 16)', `${ageWinDS.length} of 7 datasets in ≥ 12 cells; N-CMAPSS in ${CBD.NCMAPSS6.age.window_sig_cheaper}`, 'Renewal–reward model; exploratory (battery: convention C)', 'Table 8'],
     ['Q3', '*M* on FD001 at *c*_{p}/*c*_{c} = 0.1 (Δ*T* = 10): their policy 1 on our regressor / our 1-SE / our window-tuned alarm', `${pct2(t1.M)}% / ${pct2(s1.M)}% / ${pct2(w1.M)}%`, 'Re-implementation of *M*, five-fold; plan hashed before the run', 'Table 12'],
     ['Q3', 'Lowest *M* at *c*_{p}/*c*_{c} = 0.1, by dataset (FD001–FD004)', bestTxt().map(x => x.replace(/^their /, 'their ').replace(/^our /, 'our ')).join('; '), 'As above', 'Table 12'],
     ['Q3', 'Their policy 1 (P-res) beats our window-tuned alarm at 0.1 (paired bootstrap)', `${thW.length ? thW.join(', ') : 'none'}${unW.length ? `; unclear on ${unW.join(', ')}` : ''}${miW.length ? `; ours wins on ${miW.join(', ')}` : ''}`, 'As above', 'Table 13'],
     ['Q3', 'Fold–ratio cells with ≥ 1 test failure at *c*_{p}/*c*_{c} ≤ 0.1, FD001–FD004 (of 80): policy 1 P-cls optimised vs *p* = *c*_{p}/*c*_{c}; STW plain vs 1-SE', `${ftal('P1_cls_opt_mid')} vs ${ftal('P1_cls_q')}; ${ftal('STW_cost')} vs ${ftal('STW_cost_1se')}`, 'Fragility analysis; plan hashed before the run', 'Section 7.4'],
     ['Q3', 'Window-tuned alarm vs policy 1 (P-res, optimised), cells with ≥ 1 test failure at *c*_{p}/*c*_{c} ≤ 0.1: five-fold FD001–FD004 (of 80) / thirty FD001 splits (of 120)', `${ftal('STW_window')} vs ${ftal('P1_res_opt_mid')} / ${FRG.tally['fd001|rs|STW_window'].fail_small} vs ${FRG.tally['fd001|rs|P1_res_opt_mid'].fail_small}`, 'As above', 'Section 7.4'],
     ['Q4', 'Battery recipe: cross-validation by cell / one batch held out (convention C)', `${f1(BRc.pct)}% / ${f1(BRl.pct)}% (held out: fixed κ ${f1(Math.min(...kapVals('lobo')))}–${f1(Math.max(...kapVals('lobo')))}%, κ by inner CV ${f1(BSl.pct)}%, convention A ${f1(BLo.pct)}%, B ${f1(BLc.pct)}%)`, 'Corrected (post hoc)', 'Table 9'],
     ['Q4', 'Capacity-trend baseline: cross-validation / batch held out (convention C)', `${f1(BTc.pct)}% / ${f1(BTl.pct)}%`, 'Exploratory', 'Table 9'],
     ['Q4', 'Trend cheaper than the window-tuned recipe with a batch held out (cells of 16; convention C)', `window-tuned trend ${lw.a_sig_cheaper}, cost-tuned trend (1-SE) ${lk.a_sig_cheaper}`, 'Fully nested cost; plan hashed before the run', 'Table 10'],
     ['Q4', 'N-CMAPSS / rolling bearings, *H* = 20', `${f1(NW.pct)}% / ${FGc.IN} of ${FGc.n}`, 'Pre-specified (bearings: time scale corrected)', 'Table 11']],
    [750, 2900, 2550, 1900, 926]);
}
