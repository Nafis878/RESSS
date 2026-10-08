"""Final consistency and preservation checks, without rewriting old artifacts."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from method_validation.run import OUT, OLD, B, sha, holm, protect


def main():
    checks = []

    def check(name, condition):
        if not bool(condition):
            raise AssertionError(name)
        checks.append(dict(name=name, passed=True))

    protected = protect()
    check('776_frozen_files_unchanged', protected == 776)
    old_manifest = json.loads((OLD / 'completion_manifest.json').read_text())
    check('prior_observability_manifest_28_hashes_unchanged',
          len(old_manifest['sha256']) == 28 and all(sha(p) == h for p, h in old_manifest['sha256'].items()))
    check('initial_plan_hash_preserved', sha('method_validation/PLAN.initial.md') == (OUT / 'plan_sha256.txt').read_text())
    check('amended_plan_transparent', 'Interpretation amendment' in Path('method_validation/PLAN.md').read_text(encoding='utf-8'))
    t = pd.read_csv(OUT / 'paired_sign_tests.csv')
    a = pd.read_csv(OUT / 'paired_asset_contrasts.csv', dtype={'unit': str, 'split': str})
    check('24_unique_dataset_contrasts', len(t) == 24 and not t.duplicated(['dataset', 'analysis', 'contrast']).any())
    check('primary_family21_sensitivity3', t.primary.sum() == 21 and (~t.primary).sum() == 3)
    primary_assets = a[~((a.dataset == 'Battery') & (a.analysis == 'cv123'))]
    check('1149_primary_unique_assets', len(primary_assets[['dataset', 'unit']].drop_duplicates()) == 1149)
    check('primary_assets_appear_in_exactly_three_contrasts', primary_assets.groupby(['dataset', 'unit']).size().eq(3).all())
    check('asset_split_uniqueness', a.groupby(['dataset', 'analysis', 'unit']).split.nunique().eq(1).all())
    lookup = a.groupby(['dataset', 'analysis', 'contrast'])
    for row in t.itertuples():
        g = lookup.get_group((row.dataset, row.analysis, row.contrast))
        pos = int((g.value > 1e-12).sum())
        neg = int((g.value < -1e-12).sum())
        p = binomtest(pos, pos + neg, .5).pvalue if pos + neg else 1.
        assert pos == row.positive and neg == row.negative
        assert pos + neg + row.ties == row.assets == len(g)
        assert np.isclose(p, row.p_raw, atol=1e-90, rtol=1e-10)
        assert np.isclose(g.value.mean(), row.mean_difference)
    check('24_sign_tests_recomputed_from_assets', True)
    check('holm_primary_correct', np.allclose(t[t.primary].p_holm, holm(t[t.primary].p_raw), rtol=1e-10, atol=1e-90))
    check('holm_sensitivity_correct', np.allclose(t[~t.primary].p_holm, holm(t[~t.primary].p_raw), rtol=1e-10, atol=1e-90))
    check('21_primary_significant_and20_negative',
          (t[t.primary].p_holm < .05).all() and (t[t.primary].mean_difference < 0).sum() == 20)
    b = pd.read_csv(OUT / 'bootstrap_draws.csv.gz')
    check('2000_draws_each_of8_regimes', len(b) == 8 * B and b.groupby(['dataset', 'analysis']).draw.nunique().eq(B).all())
    check('bootstrap_draw_keys_unique', not b.duplicated(['dataset', 'analysis', 'draw']).any())
    check('bootstrap_hidden_risk_nonnegative', (b.hidden_failure_fraction >= -1e-12).all())
    check('bootstrap_certificate_never_exceeds_true_gain', (b.certified_gain_fraction <= b.true_gain_fraction + 1e-12).all())
    summary = pd.read_csv(OUT / 'bootstrap_summary.csv')
    linear = summary.metric.isin(['observed_fraction', 'hidden_failure_fraction'])
    check('only_linear_metrics_labeled_CI', summary.interval_type.str.contains('bootstrap CI').equals(linear))
    check('threshold_ranges_not_claimed_as_confidence_intervals', summary.loc[~linear, 'interval_type'].str.contains('sensitivity range').all())
    composite_summary = pd.read_csv(OUT / 'fixed_domain_composite_summary.csv')
    check('nonregular_diagnostics_retained',
          summary.point_outside_range.any() or composite_summary.point_outside_range.any())
    check('composite_nonregular_ranges_labeled_sensitivity',
          composite_summary.loc[composite_summary.point_outside_range, 'interval_type'].str.contains('sensitivity range').all())
    cluster = pd.read_csv(OUT / 'outer_group_sign_sensitivity.csv')
    check('exploratory_group_tests_none_adjusted_significant', not (cluster.loc[cluster.primary_regime, 'p_holm'] < .05).any())
    check('primary_outer_group_counts3_or5', set(cluster[cluster.primary_regime].outer_groups) == {3, 5})
    agreement = pd.read_csv(OUT / 'point_summary_checks.csv')
    check('48_point_summaries_match_frozen_results', len(agreement) == 48 and agreement.error.max() < 1e-12)
    lp = pd.read_csv(OUT / 'generic_lp_equivalence.csv.gz').set_index(['task', 'cap']).sort_index()
    original = pd.read_csv(OLD / 'task_results.csv.gz').set_index(['task', 'cap']).sort_index()
    check('29184_lp_comparisons_unique_complete', len(lp) == 29184 and lp.index.equals(original.index) and lp.index.is_unique)
    check('generic_lp_endpoints_match_all_frozen_endpoints',
          np.allclose(lp[['rate_low', 'rate_high', 'risk_low', 'risk_high']],
                      original[['rate_low', 'rate_high', 'risk_low', 'risk_high']], rtol=1e-8, atol=1e-10))
    check('both_generic_certifications_match_all_frozen_decisions',
          lp.generic_certified_improvement.eq(original.certified_improvement).all() and
          lp.generic_certified_safe.eq(original.certified_safe).all())
    check('15168_missing_outcome_LP_pairs', lp.lp_used.sum() == 15168)
    tests_bytes = (OUT / 'tests.log').read_bytes()
    tests_log = tests_bytes.decode('utf-16' if tests_bytes.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
    check('8_independent_unit_tests_passed', 'Ran 8 tests' in tests_log and 'OK' in tests_log and 'FAILED' not in tests_log)
    report = Path('method_validation/REPORT.md').read_text(encoding='utf-8')
    check('report_has_explicit_negative_method_verdict', 'NO: the project currently does not have an established novel method.' in report)
    check('report_discloses_posthoc_and_dependency_limits', all(s in report for s in ['post hoc', 'Shared fitted models', 'not a zero-mean hypothesis', 'resampling sensitivity ranges']))
    check('report_has_no_superiority_claim_from_LP_equality', 'No superiority p-value is appropriate' in report)
    verdict = json.loads((OUT / 'verdict.json').read_text())
    check('machine_verdict_NO_and_resource_priority_unestablished', verdict['answer'] == 'NO' and not verdict['benchmark_priority_established'])
    check('scientific_figure_artifacts_present', all((OUT / name).stat().st_size > 10000 for name in ['statistical_effects.png', 'statistical_effects.svg']))
    check('original_CI_label_files_archived_only', all(not (OUT / name).exists() and (OUT / 'diagnostics_initial' / name).exists()
          for name in ['conditional_bootstrap_intervals.csv', 'fixed_domain_composite_intervals.csv']))
    verification = dict(passed=len(checks), failed=0, protected_files_unchanged=protected, checks=checks,
                        figure_review='PNG visually inspected; legend moved clear of data and final image inspected')
    (OUT / 'verification.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
    hashes = {}
    for folder in [Path('method_validation'), OUT]:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.name != 'completion_manifest.json':
                hashes[p.as_posix()] = sha(p)
    manifest = dict(validation_complete=True, desired_established_novel_method_achieved=False,
                    methodological_novelty_established=False, benchmark_candidate_retained=True,
                    new_unit_tests=8, verification_checks=len(checks), protected_files_unchanged=protected,
                    scope='post hoc, fixed-policy paired statistical validation and generic-mechanism equivalence',
                    initial_plan_sha256=(OUT / 'plan_sha256.txt').read_text(),
                    amended_plan_sha256=sha('method_validation/PLAN.md'), sha256=hashes)
    (OUT / 'completion_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'sha256'}, indent=2))


if __name__ == '__main__':
    main()
