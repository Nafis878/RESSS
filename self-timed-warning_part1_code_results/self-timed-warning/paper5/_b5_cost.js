
// ================================================================ cost section (6.6), its discussion (7.2) and supplementary tables
// battery entries replaced by the fully nested run (convention C, kam/PHASE3_4_PLAN.md 4a); engine entries unchanged (audit_cost.py)
const BALT = ['age', 'HI_cost', 'STW_cost', 'STW_cost_1se', 'STW_cost_q80', 'Q10_cost', 'Q10_cost_1se', 'capacity_cost', 'capacity_cost_1se'];
const CO3 = Object.assign({}, R3.cost, { Battery: BN.cv123.cells });
const CB3 = Object.assign({}, R3.cost_boot, { Battery: Object.fromEntries(Object.keys(BN.cv123.cells).map(k => [k, Object.fromEntries(BALT.map(o => [o, BN.cv123.pairs[`STW_window|${o}`][k]]))])) });
const CBD = Object.assign({}, R3.cost_by_ds, { Battery: Object.fromEntries(BALT.map(o => { const s = BN.cv123.summary[`STW_window|${o}`];
  return [o, { cells: 16, window_sig_cheaper: s.a_sig_cheaper, window_sig_dearer: s.a_sig_dearer, window_point_cheaper: s.a_point_cheaper }]; })) });
const LEADS_E = [0, 5, 10, 15], LEADS_B = [0, 15, 30, 45], RHOS = [5, 10, 20, 50];
const leadsOf = d => d === 'Battery' ? LEADS_B : LEADS_E;
const cellKeys = d => leadsOf(d).flatMap(l => RHOS.map(r => `${l}|${r}`));
must(RDS.every(d => CO3[d] && Object.keys(CO3[d]).length === 16), 'cost analysis complete: 16 lead-time and cost-ratio cells on all seven datasets (battery fully nested)');
must(['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6'].every(d => R3.cost_verify[d]), 'cost audit reproduces the window-tuned, cost-tuned, health-indicator, age and perfect-foresight results of an earlier, separate run unit by unit on the six engine datasets');
const POLN = { STW_window: 'STW, window-tuned', STW_cost: 'STW, cost-tuned', STW_cost_1se: 'STW, cost-tuned, 1-SE', STW_cost_q80: 'STW, cost-tuned, 80th percentile', Q10_cost: 'Quantile alarm, cost-tuned', Q10_cost_1se: 'Quantile alarm, 1-SE', HI_cost: 'Health-indicator alarm', capacity_cost: 'Capacity threshold, cost-tuned', capacity_cost_1se: 'Capacity threshold, 1-SE', age: 'Age replacement' };
const ALT = ['age', 'HI_cost', 'STW_cost', 'STW_cost_1se', 'STW_cost_q80', 'Q10_cost', 'Q10_cost_1se'];
const ratioRange = (d, other) => { const v = cellKeys(d).map(k => CB3[d][k][other].ratio).sort((a, b) => a - b); return { min: v[0], max: v[v.length - 1], med: (v[7] + v[8]) / 2 }; };
const sigc = (d, other) => CBD[d][other];
const cellTxt = (d, o) => { const r = ratioRange(d, o), s = sigc(d, o); return `${r.med.toFixed(2)} (${r.min.toFixed(2)}–${r.max.toFixed(2)}); ${s.window_sig_cheaper}/${s.window_sig_dearer}`; };
const sumOver = (dss, o, k) => dss.reduce((a, d) => a + (CBD[d][o] ? CBD[d][o][k] : 0), 0);
const ENG6 = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6'];

function COST_TABLE() {
  return table('Cost of the window-tuned alarms relative to each alternative policy, by dataset. Each entry: median (minimum–maximum) over the 16 lead-time and cost-ratio cells of the ratio of cost rates (window-tuned / alternative; below 1 favours the window-tuned policy); then the number of cells in which the paired 95% bootstrap interval lies entirely below 1 / entirely above 1.',
    ['Dataset', 'Age replacement', 'Health-indicator alarm', 'STW, cost-tuned', 'STW, cost-tuned, 1-SE', 'STW, cost-tuned, 80th pct.', 'Quantile alarm, cost-tuned', 'Quantile alarm, 1-SE'],
    RDS.map(d => [RNAME[d], ...ALT.map(o => cellTxt(d, o))]),
    [1100, 1150, 1150, 1150, 1150, 1150, 1150, 1176], `Five-fold cross-validation; lead times ℓ ∈ {0, 5, 10, 15} cycles (battery 0, 15, 30, 45 cycles) and failure-cost ratios ρ ∈ {5, 10, 20, 50}. The 16 cells of a dataset share units and alarms and are not independent; the counts are descriptive. Battery: cross-validation by cell, fully nested preprocessing with the task in cycles (convention C); the battery policies under a held-out batch, including the capacity trend, are in Table 10. The cost rates relative to perfect foresight for every cell are in Supplementary Section S11.`);
}

function COST_SECTION() {
  B.push(H2('6.3. Q3: Window tuning and direct cost optimisation'));
  B.push(...COST_TABLE());
  COST_TEXT3().forEach(t => B.push(P(t)));
  B.push(...figure(__dirname + '/img/FigR3_cost_audit5.png', 'Long-run cost rate relative to perfect foresight (1.00 = replacement one cycle before every failure) for policies tuned on training units: (a) without lead time and ρ = 10; (b) with a lead time of 10 cycles (30 cycles for the battery) and ρ = 50. Five-fold cross-validation; battery fully nested, with the task in cycles (convention C). Off-scale values are labelled.'));
}

const spName = k => k.startsWith('lobo') ? `batch ${k.slice(4)} held out` : k.startsWith('cv119_') ? `fold ${k.slice(6)} of the 119-cell analysis` : `fold ${k.slice(2)}`;
function BATTERY_SUPP_TEXT() {
  const ps = BT.per_split, sp3 = Object.keys(ps).filter(k => ps[k].kappa === ps[k].protocol_kappa), sp4 = Object.keys(ps).filter(k => ps[k].kappa !== ps[k].protocol_kappa);
  const d3 = sp3.map(k => ps[k].warning.IN - ps[k].protocol_IN), d4 = sp4.map(k => ps[k].warning.IN - ps[k].protocol_IN);
  must(Math.max(...d3.map(Math.abs)) <= 3, 'battery splits with unchanged kappa differ from the protocol by at most 3 cells (fill change only)');
  const lb = k => `${ps[k].warning.IN}/${ps[k].warning.n}`;
  return `Training-only κ differed from the protocol value (κ = 3) in ${sp4.length} of the ${Object.keys(ps).length} battery splits (${sp4.map(spName).join(', ')}; κ = 4 in each). In those splits the number of correct first warnings changed by ${d4.map(x => (x > 0 ? '+' : '') + fm(x)).join(', ')} cells. In the splits where κ was unchanged, the only difference from the protocol analysis is the first-block value of the cells with a missing first cycle (forward instead of backward filling). Even so, counts changed by up to ${Math.max(...d3.map(Math.abs))} cells (${sp3.filter(k => ps[k].warning.IN !== ps[k].protocol_IN).map(k => `${spName(k)}: ${ps[k].protocol_IN} → ${ps[k].warning.IN}`).join('; ')}). This sensitivity of refitted trees to small input changes is a source of variability that the binomial intervals do not cover. With a batch held out, batch 1 gave ${lb('lobo1')}, batch 2 ${lb('lobo2')} (${ps.lobo2.warning.late} late; MLP with Kalman filter ${ps.lobo2.mlp_kf.IN}/${ps.lobo2.mlp_kf.n}) and batch 3 ${lb('lobo3')}. The 119-cell analysis without the four noisy channels gave ${B119c.IN}/${B119c.n} (${f1(B119c.pct)}%; protocol analysis ${f1(B119o.pct)}%). In this intermediate analysis, the capacity-trend baseline uses the least-squares slope of block-mean discharge capacity over the last *w* ∈ {10, 20, 40} blocks (in the fully nested analysis, the last 30, 60 or 120 cycles); its extrapolated remaining life to 0.88 Ah goes through the same smoothing, debounce and shift grid, with all settings chosen on training cells. The capacity-threshold baseline alarms when smoothed capacity stays below a threshold (120 quantiles of training values) for *k* blocks and reports a constant in [*H* − 6, *H*].`;
}
