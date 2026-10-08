
// ================================================================ numbers (all from numbers.json; N.rev3 = audit reruns of this revision)
const cv = N.cv, pool = N.cv_pooled, ncm = N.ncm, nd = N.ncm_detail_H20, h2 = N.h2h, mc = N.h2h_mcnemar, half = N.half, ab = N.ablation;
const R2 = N.rev2, R3 = N.rev3, FT = R3.fixed_time;
const DS = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004'];
const P08 = cv.PHM08['20'];
const ci = o => `${f1(o.ci[0])}–${f1(o.ci[1])}%`;
const fmtp = p => p < 0.001 ? '< 0.001' : p.toFixed(3);
const peq = p => p < 0.001 ? '*p* < 0.001' : `*p* = ${p.toFixed(3)}`;
const ncmRow = (m, H, split = 'cv (primary)') => ncm.summary.find(s => s.method === m && s.H === H && s.split === split);
const NW = ncmRow('warning', 20), NM = ncmRow('mlp_kf', 20), NA = ncmRow('age_only', 20), NWo = ncmRow('warning', 20, 'official');
const hy = ncm.hypotheses;
const halfItems = [half.single.age, half.single.iohmm, half.single.sim, half.single.gbm, half.tcn, half.tcn_gan, half.single.tf_q50, half.single.cnn, half.single.bayes_q50, half.single.lstm, half.hybrid];
const halfMax = Math.max(...halfItems.map(x => x.pct));
must(halfItems.length === 11 && halfMax === half.hybrid.pct && halfMax === 33.5, 'eleven fixed-time models; the stacked hybrid is the best at half of life (33.5%)');
must(P08.pct === 91.7 && P08.IN === 200 && P08.n === 218, 'PHM08 H=20: 200/218 = 91.7%');
must(pool['20'].IN === 836 && pool['20'].n === 927 && pool['20'].pct === 90.2, 'pooled H=20: 836/927 = 90.2%');
must(NW.IN === nd.IN && NW.n === 99 && NW.pct === 68.7, 'N-CMAPSS primary: 68/99 = 68.7%');
// ---- fixed-time decomposition (audit_fixed_time.py)
const G50 = FT.fixed['gbm|0.5'], G90 = FT.fixed['gbm|0.9'], OR20 = FT['oracle|20'], SELF20 = FT['self|20'];
must(SELF20.IN === P08.IN && OR20.IN === ab['oracle_timed|H20'].IN, 'decomposition uses the main self-timed result and the oracle-timed control');
must(G90.cal_pct > G90.raw_pct && G90.cal_pct < SELF20.pct && G50.cal_pct < 30, 'calibrated fixed-time GBM at 90% of life between raw and self-timed; at half of life below 30%');
const FTsig = FT.self20_vs_gbm90cal;
// ---- battery and bearings, training-only block length (audit_confirmations.py)
const BT = R3.battery, BS = BT.summary, GT = R3.bearing, GS = GT.summary;
const bw = (an, m = 'warning', H = 20) => BS[`${an}|${m}|${H}`];
const BWc = bw('cv123'), BLc = bw('lobo'), B119c = bw('cv119');
const BD = N.battery_data, bdo = N.battery_detail, GD = N.bearing_data, gbo = N.bearing_detail;
const BWo = bdo['cv123|warning|20'], BLo = bdo['lobo|warning|20'], B119o = bdo['cv119|warning|20'];
must(BWo.pct === 97.6 && BLo.pct === 69.9 && gbo['cv|warning|20'].IN === 0 && gbo['cv|warning|20'].n === 17, 'protocol results as submitted: battery CV 97.6%, leave-one-batch-out 69.9%, bearings 0/17');
const FGc = GS['cv|warning|20'];
must(FGc.IN === 0 && FGc.n === 17, 'bearings with training-only block length: still 0 of 17');
const kapB = BT.kappa, kapG = GT.kappa;
const kset = o => [...new Set(Object.values(o))].sort((a, b) => a - b);
const kList = (o, keys) => keys.map(k => o[k]).join(', ');
const RNAME = { PHM08: 'PHM08', FD001: 'FD001', FD002: 'FD002', FD003: 'FD003', FD004: 'FD004', NCMAPSS6: 'N-CMAPSS', Battery: 'Battery' };
const RDS = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'Battery'];
// ---- second revision (N.rev4): matched fixed-time comparison, fully nested physical battery task, battery cost with the capacity trend
const R4 = N.rev4, FM = R4.fixed_matched, FMV = FM.variants, FMP = FM.paired, BP = R4.battery_physical, BC2 = R4.battery_cost2;
must(FM.recipe_self_reproduces_main && FMV.recipe_self.IN === P08.IN, 'matched analysis: the cross-fitted recipe reproduces the main PHM08 result engine by engine');
must(FMV.fixed_f90_7525.IN === Math.round(G90.cal_pct * 218 / 100) && FMV.recipe_self_7525.IN === h2['ours|20'].IN, 'matched analysis: frozen 75/25 variants equal the earlier figures');
must(BC2.verify_cv, 'battery cost rerun reproduces the earlier cross-validation cost results unit by unit for every shared policy');
const BPinner = BP.inner_kappas;
const kapVals = an => [2, 3, 4, 5, 6].map(k => BP[`${an}|fixed_kappa|recipe|${k}`].pct);
const kapIN = an => [2, 3, 4, 5, 6].map(k => BP[`${an}|fixed_kappa|recipe|${k}`].IN);
const BPkapRange = { cv: 100 * (Math.max(...kapIN('cv123')) - Math.min(...kapIN('cv123'))) / 123, lobo: 100 * (Math.max(...kapIN('lobo')) - Math.min(...kapIN('lobo'))) / 123 };
const BRc = BP['cv123|rule_nested|recipe'], BRl = BP['lobo|rule_nested|recipe'], BSc = BP['cv123|cv_selected|recipe'], BSl = BP['lobo|cv_selected|recipe'];
const BTc = BP['cv123|rule_kappa|capacity_trend'], BTl = BP['lobo|rule_kappa|capacity_trend'];
