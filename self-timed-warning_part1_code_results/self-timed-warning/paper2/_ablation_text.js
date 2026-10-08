function ABLATION_TEXT() {
  const a = k => ab[`${k}|H20`], t = k => N.ablation_mcnemar['20'][k], ov = N.oracle_vs_self['20'];
  must(t('no_shift').p_holm < 0.001 && t('uncapped').p_holm < 0.01 && t('sensors7').p_holm < 0.05 && t('sensors_no_age').p_holm < 0.05 && t('untuned_rule').p_holm < 0.001, 'ablation: shift, cap, sensors, age, tuning significant');
  must(t('cap125').p_holm > 0.05 && t('no_debounce').p_holm > 0.05 && t('no_smoothing').p_holm > 0.05, 'ablation: cap value, debounce, smoothing not significant');
  must(ov.p > 0.05 && abFull.pct > abOr.pct, 'self-timed not worse than oracle-timed (difference not significant)');
  return `Table 5 and Fig. 5b isolate the components on PHM08 at *H* = 20. The full model reproduced the main result exactly (${abFull.IN}/${abFull.n}). ` +
    `Removing the window-centring shift caused the largest loss: ${a('no_shift').IN} engines (${f1(a('no_shift').pct)}%), with ${a('no_shift').late} late warnings, because about half of the unshifted errors are positive and every error above +2 is late, while the wide early side of the window goes unused (Holm-adjusted *p* ${fmtp(t('no_shift').p_holm)}). ` +
    `An untuned rule (cap 60, no smoothing, no debounce, no shift) reached ${f1(a('untuned_rule').pct)}%. Training without a target cap gave ${f1(a('uncapped').pct)}% (*p* = ${fmtp(t('uncapped').p_holm)}), ` +
    `but the conventional cap of 125 gave ${f1(a('cap125').pct)}%, statistically indistinguishable from the selected caps (${t('cap125').full_only} against ${t('cap125').variant_only} discordant engines, *p* = ${fmtp(t('cap125').p_holm)}). ` +
    `Smoothing (${f1(a('no_smoothing').pct)}% without) and debouncing (${f1(a('no_debounce').pct)}% without) made no significant difference. ` +
    `The inputs mattered: the seven temperature and shaft-speed sensors (with age) gave ${f1(a('sensors7').pct)}% (*p* = ${fmtp(t('sensors7').p_holm)}), sensor features without the age gave ${f1(a('sensors_no_age').pct)}% (*p* = ${fmtp(t('sensors_no_age').p_holm)}), ` +
    `and age alone gave ${f1(a('age_only').pct)}%, with ${a('age_only').missed} engines never warned. ` +
    `Finally, the oracle-timed control, which evaluates the same calibrated estimate at the cycle where exactly 20 true cycles remain, reached ${f1(abOr.pct)}%. ` +
    `Letting the model choose its own moment therefore did not cost accuracy relative to being told the true moment (${ov.self_only} against ${ov.oracle_only} discordant engines, *p* = ${fmtp(ov.p)}).`;
}
