// ---------------------------------------------------------------- front matter
const TITLE = 'What does an end-of-life alarm score measure? Separating prediction accuracy, alarm timing, maintenance cost and transfer';
const SHORTTITLE = 'What an end-of-life alarm score measures';
must(Math.abs(pc.STW_const.pct - pc.STW.pct) < 5, 'abstract: constant estimate within a few points pooled');
const abLost = KDS.filter(d => kpr(d, 0.1, 'STW_window', 'P1_res_opt_mid').v === 'mine');
must(abLost.length >= 1 && new Set(KDS.map(d => bestM(d).ours)).size === 2, 'abstract: their policy 1 (P-res) loses to our window-tuned alarm on at least one dataset, and the lowest M comes from different families on different datasets');
must(kpr('fd001', 0.1, 'STW_window', 'P1_res_opt_mid').v === 'theirs', 'abstract: their policy 1 beats our window-tuned alarm on FD001');
must(ageWinDS.length === 6, 'abstract: window-tuned alarms cheaper than age replacement on six of seven datasets');
const ABSTRACT = `End-of-life alarms trigger replacements but are often judged by a single acceptance score. We ask what such a score measures and whether optimising it yields good maintenance decisions. On eight run-to-failure datasets, with a deliberately simple alarm and training-only selection, we separate long-range prediction, near-failure estimation, alarm timing, maintenance cost and transfer. With matched training and calibration, one fixed-time model placed ${f1(FMV.fixed_f50.pct)}% of PHM08 estimates in an asymmetric window at half of life and ${f1(FMV.fixed_f90.pct)}% at 90% of life; the self-timed alarm reached ${f1(FMV.recipe_self.pct)}%, no more than its regressor at 90% of life${f4rep1 && f4rep2 ? ', and FD004 repeated this' : ''}. A constant estimate at the alarm times scored within ${f1(Math.max(...ctrlDS.map(d => Math.abs(CT[d]['20'].STW_const.pct - CT[d]['20'].STW.pct))))} points of the model's estimate, so the score mainly rewarded timing and concealed notice and cost. Window-tuned alarms beat age replacement in most cost settings on six of seven datasets, but no tuning rule was cheapest everywhere: under the re-implemented metric of Kamariotis et al., their threshold policy on our regressor won on FD001 and lost on ${andList(abLost.map(d => d.toUpperCase()))}. With a battery batch held out, accuracy fell from ${f1(BRc.pct)}% to ${f1(BRl.pct)}% (${f1(Math.min(...kapVals('lobo')))}–${f1(Math.max(...kapVals('lobo')))}% across time scales) and a capacity trend did better; on bearings the alarm failed. These properties should be reported separately.`;
const HIGHLIGHTS = [
  'Prediction, alarm timing, maintenance cost and transfer of alarms are separated',
  'Observation time, not self-timing, explains most of the fixed-time vs alarm gap',
  'A constant estimate at the alarm times scores like the model: windows reward timing',
  'Window-tuned alarms are not cost-optimal; no policy family won on every dataset',
  `Batteries: accuracy fell on a held-out batch; a simple capacity trend did better${must(BRl.pct < BRc.pct, 'highlight: battery held-out rate below the within-batch rate') || ''}`];
must(HIGHLIGHTS.every(h => h.length <= 85), 'highlights at most 85 characters: ' + HIGHLIGHTS.map(h => h.length).join(','));
must(ABSTRACT.split(/\s+/).length <= 250, 'abstract at most 250 words (' + ABSTRACT.split(/\s+/).length + ')');
const KEYWORDS = 'Remaining useful life; Predictive maintenance; Alarm evaluation; Alarm timing; Decision-oriented metric; Distribution shift; Lithium-ion battery';
