
// ================================================================ revision text blocks (cost, deep-learning competitors)
function rng(vals, d = 2) { const a = Math.min(...vals), b = Math.max(...vals); return a.toFixed(d) === b.toFixed(d) ? a.toFixed(d) : `${a.toFixed(d)}–${b.toFixed(d)}`; }
function COST_TEXT() {
  const R = [5, 10, 20, 50], ENG = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'];
  const s = (d, l, k = 'stw_rel_pf') => R.map(r => (d === 'Battery' ? BC : CO[d])[`${l}|${r}`][k]);
  const engWin = ENG.every(d => [0, 5, 10].every(l => R.every(r => CO[d][`${l}|${r}`].stw_rel_pf < CO[d][`${l}|${r}`].age_rel_pf)));
  must(engWin, 'cost: self-timed warning cheaper than optimal age replacement on PHM08 and FD001-FD004 for every rho and lead time up to 10 cycles');
  const nc0 = R.map(r => CO.NCMAPSS6[`0|${r}`]), ncWins = R.filter(r => CO.NCMAPSS6[`0|${r}`].stw_rel_pf < CO.NCMAPSS6[`0|${r}`].age_rel_pf).length;
  const bWin = [0, 15, 30].every(l => R.every(r => BC[`${l}|${r}`].stw_rel_pf < BC[`${l}|${r}`].age_rel_pf));
  must(bWin && BC['45|20'].stw_rel_pf > BC['45|20'].age_rel_pf && BC['45|5'].stw_rel_pf < BC['45|5'].age_rel_pf && BC['45|10'].stw_rel_pf < BC['45|10'].age_rel_pf && BC['45|50'].stw_rel_pf > BC['45|50'].age_rel_pf, 'battery cost: cheaper than age replacement up to 30 cycles of lead time, not at 45 cycles with H fixed');
  const sav = ENG.flatMap(d => R.map(r => CO[d][`0|${r}`].stw_saving_vs_age_pct));
  return `Table 8 and Fig. 9b give the cost analysis. Without lead time, the self-timed warnings brought the long-run cost rate on PHM08 to ${rng(s('PHM08', 0))} times that of perfect foresight for ρ from 5 to 50, against ${rng(s('PHM08', 0, 'age_rel_pf'))} for optimal age replacement and ${rng(s('PHM08', 0, 'rtf_rel_pf'), 1)} for run-to-failure. ` +
    `On PHM08 and FD001–FD004 the warnings were cheaper than age replacement for every cost ratio and for lead times up to 10 cycles, with savings of ${Math.round(Math.min(...sav))}–${Math.round(Math.max(...sav))}% without lead time. On PHM08 the saving grew from ${Math.round(CO.PHM08['0|5'].stw_saving_vs_age_pct)}% at ρ = 5 to ${Math.round(CO.PHM08['0|50'].stw_saving_vs_age_pct)}% at ρ = 50, because age replacement must replace early to avoid expensive failures, whereas the warnings adapt to each unit. ` +
    `With a lead time the warning level selected on training engines rose, and the cost stayed close to the no-lead case (PHM08 with 10 cycles of lead time: ${rng(s('PHM08', 10))}). ` +
    `On N-CMAPSS, where the error was least concentrated, the warnings were cheaper than age replacement for ${ncWins} of 4 cost ratios without lead time (${rng(nc0.map(x => x.stw_rel_pf))} against ${rng(nc0.map(x => x.age_rel_pf))} times perfect foresight), a much smaller advantage than on the other data. ` +
    `On the batteries, with the warning level fixed at 20 blocks, the rate was ${rng(s('Battery', 0))} times perfect foresight, against ${rng(s('Battery', 0, 'age_rel_pf'))} for age replacement, and the warnings stayed cheaper up to a lead time of 30 cycles. With 45 cycles of lead time, however, ${BC['45|10'].stw_fail} of ${BC['45|10'].n} cells failed before the planned replacement, because a fixed warning about ${Math.round(BW.median_left_cycles)} cycles before failure leaves too little margin, and the warnings were cheaper than age replacement only for ρ = 5 and 10; the warning level must grow with the lead time, as it did automatically on the engine data. On the engine datasets the warning level was chosen on the same out-of-fold predictions that had been used to tune the other settings, which may make the choice slightly optimistic, although the test units were never used.`;
}
function DL_TEXT() {
  const d = N.dl, m = N.dl_mcnemar;
  must(m['20'].lstm15.p_holm7 < 0.05 && m['20'].cnn15.p_holm7 < 0.05 && m['20'].tf15.p_holm7 > 0.05 && d['tf15|20'].pct > h2['ours|20'].pct, 'equal inputs: LSTM and CNN worse at H=20, Transformer not significantly different (numerically higher)');
  must(m['10'].cnn15.p_holm7 < 0.05 && m['10'].lstm15.p_holm7 > 0.05 && d['tf15|10'].IN === h2['ours|10'].IN, 'equal inputs at H=10: only the CNN significantly worse; Transformer equal');
  must(d['lstm15|20'].pct > h2['rnn|20'].pct && d['cnn15|20'].pct > h2['cnn|20'].pct, 'equal inputs raise LSTM and CNN rates');
  const t = k => `${d[k].IN}/${d[k].n} (${f1(d[k].pct)}%)`;
  return `The lower block of Table 4 removes the differences in inputs and target. Given the same 15 regime-normalised sensors and the age as our model, and choosing their target cap from the same set, the networks improved markedly: at *H* = 20 the LSTM rose from ${f1(h2['rnn|20'].pct)}% to ${f1(d['lstm15|20'].pct)}% and the CNN from ${f1(h2['cnn|20'].pct)}% to ${f1(d['cnn15|20'].pct)}%. Both remained significantly below our model at *H* = 20 (Holm-adjusted *p* = ${fmtp(m['20'].lstm15.p_holm7)} and ${fmtp(m['20'].cnn15.p_holm7)}); at *H* = 10 only the CNN did. ` +
    `The hybrid Transformer, which also receives our causal features, reached ${t('tf15|20')} at *H* = 20, slightly more than our model's ${h2['ours|20'].IN}/218, and ${t('tf15|10')} at *H* = 10, the same as ours; neither difference was significant (${m['20'].tf15.ours_only} against ${m['20'].tf15.other_only} discordant engines at *H* = 20, *p* = ${fmtp(m['20'].tf15.p_holm7)}). ` +
    `Much of the gap to the original re-implementations is therefore due to their inputs and targets; with our inputs, one of the three networks, the Transformer, matched gradient boosting.`;
}
function ABS_COMPARE() { return `; under an identical protocol on PHM08 (our model ${f1(h2['ours|20'].pct)}%), re-implemented challenge approaches reached ${f1(h2['similarity|20'].pct)}–${f1(h2['mlp_kf|20'].pct)}% and a Transformer given our inputs ${f1(N.dl['tf15|20'].pct)}% (not significantly different)`; }
function CONCL_COMPARE() { return `; under an identical protocol it outperformed re-implementations of the three winning PHM08 challenge approaches (significantly for two of them), and a Transformer given the same inputs did about as well`; }
function COMPETITOR_LIMITATION() { return `• **Competitors.** The challenge approaches are re-implementations in the spirit of the published methods, not the original code. The networks' architectures were taken from the literature and only their target cap was tuned; more extensive tuning could improve them.`; }
function ABS_COST() {
  const R = [5, 10, 20, 50], p = R.map(r => CO.PHM08[`0|${r}`].stw_rel_pf), a = R.map(r => CO.PHM08[`0|${r}`].age_rel_pf);
  return `${Math.round(100 * (Math.min(...p) - 1))}–${Math.round(100 * (Math.max(...p) - 1))}% of perfect foresight, against ${Math.round(100 * (Math.min(...a) - 1))}–${Math.round(100 * (Math.max(...a) - 1))}% for optimal age replacement`;
}
function HL_COST() {
  const R = [5, 10, 20, 50]; const all = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6'];
  const win = all.filter(d => R.every(r => CO[d][`0|${r}`].stw_rel_pf < CO[d][`0|${r}`].age_rel_pf)).length + (R.every(r => BC[`0|${r}`].stw_rel_pf < BC[`0|${r}`].age_rel_pf) ? 1 : 0);
  return `With no lead time, warnings cost less than age replacement on ${['no', 'one', 'two', 'three', 'four', 'five', 'six', 'all seven'][win]}${win < 7 ? ' of seven' : ''} datasets`;
}
function COST_SHORT() {
  const R = [5, 10, 20, 50], ENG = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'];
  const s = (d, k = 'stw_rel_pf') => R.map(r => (d === 'Battery' ? BC : CO[d])[`0|${r}`][k]);
  const sav = ENG.flatMap(d => R.map(r => CO[d][`0|${r}`].stw_saving_vs_age_pct));
  const ncWins = R.filter(r => CO.NCMAPSS6[`0|${r}`].stw_rel_pf < CO.NCMAPSS6[`0|${r}`].age_rel_pf).length;
  return `In the renewal–reward analysis without lead time (Fig. 9b; Supplementary Section S9), the warnings brought the long-run cost rate on PHM08 to ${rng(s('PHM08'))} times that of perfect foresight for ρ from 5 to 50, against ${rng(s('PHM08', 'age_rel_pf'))} for optimal age replacement; on PHM08 and FD001–FD004 they were cheaper than age replacement for every cost ratio and for lead times up to 10 cycles (savings of ${Math.round(Math.min(...sav))}–${Math.round(Math.max(...sav))}% without lead time). On the batteries the rate was ${rng(s('Battery'))} times perfect foresight against ${rng(s('Battery', 'age_rel_pf'))} for age replacement; on N-CMAPSS the warnings were cheaper for only ${ncWins} of 4 cost ratios.`;
}
