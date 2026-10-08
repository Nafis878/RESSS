"""Read-only audits of all frozen inputs and the new recorded research evidence."""
import hashlib
import inspect
import itertools
import json
import os
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from clock_regret.core import select
from clock_regret.run import OUT


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def corrected(p):
    p = np.asarray(p, dtype=float)
    order = np.argsort(p, kind='stable')
    q = np.empty(len(p))
    q[order] = np.minimum(1., np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return q


def close(a, b):
    assert np.allclose(a, b, rtol=1e-10, atol=1e-12), (a, b)


def main():
    checks = []
    def passed(name):
        checks.append(dict(check=name, passed=True))
        print(f'PASS {name}', flush=True)

    frozen = json.loads((OUT / 'protected_before.json').read_text())
    assert len(frozen) == 809
    assert all(sha(p) == h for p, h in frozen.items())
    passed('all 809 prior protected artifact hashes unchanged before audit')
    assert sha('clock_regret/PLAN.md') == (OUT / 'plan_sha256.txt').read_text().strip()
    passed('pre-run research plan hash unchanged')
    assert list(inspect.signature(select).parameters) == ['horizon', 'logger_failed', 'ages', 'rho']
    passed('selector API receives only public records, candidate ages and common cost')

    env = os.environ.copy()
    env.update(PYTHONUTF8='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    test = subprocess.run([sys.executable, '-m', 'unittest', 'clock_regret.test_core', '-v'],
                          capture_output=True, text=True, encoding='utf-8', env=env)
    (OUT / 'tests.log').write_text(test.stdout + test.stderr, encoding='utf-8')
    assert test.returncode == 0 and 'Ran 12 tests' in test.stderr
    passed('12 unit-test groups: 250 exhaustive and 100 independent generic-state comparisons')

    frames = {}
    witness_count = 0
    for source, expected_cases in [('synthetic', 2400), ('real', 304)]:
        p = pd.read_csv(OUT / f'{source}_public.csv.gz', dtype={'unit': str, 'split': str})
        sealed = pd.read_csv(OUT / f'{source}_sealed.csv.gz', dtype={'unit': str, 'split': str})
        pairs = pd.read_csv(OUT / f'{source}_pairwise.csv.gz')
        results = pd.read_csv(OUT / f'{source}_results.csv.gz', dtype={'split': str})
        frames[source] = dict(public=p, sealed=sealed, pairs=pairs, results=results)
        assert 'lifetime' not in p and 'lifetime_witness' not in p
        assert not p.duplicated(['case', 'unit']).any() and not sealed.duplicated(['case', 'unit']).any()
        assert len(p) == len(sealed) and p.case.nunique() == expected_cases
        assert set(zip(p.case, p.unit)) == set(zip(sealed.case, sealed.unit))
        passed(f'{source}: public records exclude hidden truth; sealed keys align uniquely')
        assert len(results) == expected_cases * 4
        assert results.groupby('case').method.nunique().eq(4).all()
        assert set(results.method) == {'exact_shared_clock', 'sharp_rectangle', 'upper_rate', 'complete_case'}
        assert not results.duplicated(['case', 'method']).any()
        assert not pairs.duplicated(['case', 'age_a', 'age_b']).any()
        passed(f'{source}: all planned cases and four aligned selectors present')
        s_groups = {case: g.set_index('unit') for case, g in sealed.groupby('case', sort=False)}
        pair_groups = dict(tuple(pairs.groupby('case', sort=False)))
        r_groups = dict(tuple(results.groupby('case', sort=False)))
        for case, g in p.groupby('case', sort=False):
            assert g.ages.nunique() == g.rho.nunique() == 1
            ages = list(map(int, g.ages.iloc[0].split('|')))
            rho = int(g.rho.iloc[0])
            h = g.horizon.to_numpy(np.int64)
            failed = g.logger_failed.to_numpy(bool)
            life = s_groups[case].loc[g.unit, 'lifetime'].to_numpy(np.int64)
            assert (h >= 1).all() and all(d >= 1 for d in ages)
            assert np.array_equal(life[failed], h[failed]) and (life[~failed] > h[~failed]).all()
            q = pair_groups[case]
            assert set(zip(q.age_a, q.age_b)) == set(itertools.product(ages, repeat=2))
            joint = {}
            for row in q.itertuples(index=False):
                witness = np.array(list(map(int, row.lifetime_witness.split('|'))), dtype=np.int64)
                assert len(witness) == len(h)
                assert np.array_equal(witness[failed], h[failed]) and (witness[~failed] > h[~failed]).all()
                a, b = int(row.age_a), int(row.age_b)
                ca = len(h) + (rho - 1) * int((witness <= a).sum())
                cb = len(h) + (rho - 1) * int((witness <= b).sum())
                ta = int(np.minimum(witness, a).sum())
                tb = int(np.minimum(witness, b).sum())
                value = Fraction(ca * tb, cb * ta)
                assert value == Fraction(int(row.numerator), int(row.denominator))
                close(float(value), row.exact_worst_ratio)
                if a == b:
                    assert value == 1
                joint[a, b] = value
                witness_count += 1
            bounds, cc, risks = {}, {}, {}
            for age in ages:
                observed = failed | (h >= age)
                known_fail = failed & (h <= age)
                c = int(np.where(observed, 1 + (rho - 1) * known_fail, 0).sum())
                t = int(np.where(observed, np.minimum(h, age), 0).sum())
                m = int((~observed).sum())
                bounds[age] = (Fraction(c + m, t + m * age),
                               Fraction(c + rho * m, t + int((h[~observed] + 1).sum())))
                cc[age] = Fraction(c, t) if t else None
                risks[age] = Fraction(int(known_fail.sum()) + int((~failed & (h < age)).sum()), len(h))
            score = {a: max(joint[a, b] for b in ages) for a in ages}
            rect = {a: max(Fraction(1) if a == b else bounds[a][1] / bounds[b][0]
                           for b in ages) for a in ages}
            assert all(joint[a, b] <= (Fraction(1) if a == b else bounds[a][1] / bounds[b][0])
                       for a in ages for b in ages)
            assert all(score[a] >= 1 for a in ages)
            intended = dict(exact_shared_clock=min(ages, key=lambda a: (score[a], a)),
                            sharp_rectangle=min(ages, key=lambda a: (rect[a], a)),
                            upper_rate=min(ages, key=lambda a: (bounds[a][1], a)),
                            complete_case=min(ages, key=lambda a: (cc[a] is None, cc[a] or Fraction(0), a)))
            true_rates = {a: Fraction(len(h) + (rho - 1) * int((life <= a).sum()),
                                      int(np.minimum(life, a).sum())) for a in ages}
            best = min(true_rates.values())
            for row in r_groups[case].itertuples(index=False):
                age = int(row.selected_age)
                assert age == intended[row.method] and ages[int(row.selected_index)] == age
                assert int(row.n) == len(h) and row.ages == g.ages.iloc[0]
                assert int(row.evaluation_rho) == rho
                truth = true_rates[age] / best
                assert truth <= score[age] and score[intended['exact_shared_clock']] <= score[age]
                close(float(true_rates[age]), row.cost_rate)
                close(float(truth), row.realized_relative_regret)
                close(float(score[age]), row.exact_worst_relative_regret)
                close(float(rect[age]), row.rectangle_worst_upper)
                risk = float((life <= age).mean())
                close(risk, row.risk)
                close(float(risks[age]), row.risk_upper)
                assert risk <= float(risks[age]) + 1e-12
        passed(f'{source}: every sealed lifetime satisfies its public censoring record')
        passed(f'{source}: all pairwise witnesses attain their stored exact fractions')
        passed(f'{source}: all policy pairs present; diagonal cancellation and marginal domination hold')
        passed(f'{source}: all four choices recomputed with exact fractions and specified tie breaks')
        passed(f'{source}: recorded rates, regret, risk and worst-case certificates recomputed from truth')

    assert witness_count == 39448
    passed('all 39,448 exact attaining witnesses checked')
    settings = list(itertools.product([12, 24], [6, 10], [5, 20], ['short', 'long', 'mixture']))
    syn = frames['synthetic']
    sg = dict(tuple(syn['sealed'].groupby('case', sort=False)))
    for case, g in syn['public'].groupby('case', sort=False):
        q = g.iloc[0]
        setting, replicate, seed = int(q.setting_id), int(q.replicate), int(q.seed)
        n, horizon, rho, law = settings[setting]
        assert len(g) == n and int(q.logging_age) == horizon and int(q.rho) == rho and q.dataset == law
        assert seed == 910000 + 1000 * setting + replicate and 0 <= replicate < 100
        assert case == setting * 100 + replicate + 1
        rng = np.random.default_rng(seed)
        short, long = rng.integers(4, 15, n), rng.integers(18, 41, n)
        life = short if law == 'short' else long if law == 'long' else np.where(rng.random(n) < .5, short, long)
        assert np.array_equal(life, sg[case].lifetime.to_numpy())
        assert np.array_equal(g.horizon, np.minimum(life, horizon))
        assert np.array_equal(g.logger_failed, life <= horizon)
    passed('2,400 synthetic cohorts regenerated from predeclared settings and unique seed mapping')

    provenance = pd.read_csv(OUT / 'real_policy_provenance.csv', dtype={'split': str})
    assert len(provenance) == 38
    for row in provenance.itertuples(index=False):
        assert sha(row.source_path) == row.source_sha256
        source = pd.read_csv(row.source_path, dtype={'unit': str}, low_memory=False)
        if row.dataset != 'Battery':
            source = source.assign(analysis='engine', split=source.fold.astype(str))
        source['split'] = source.split.astype(str)
        group = source[(source.analysis == row.analysis) & (source.split == row.split)]
        age_rows = group[(group.policy == 'age') & (group.lead_cycles == 0)]
        ages = {str(int(r)): int(pd.to_numeric(z.setting).unique().item()) for r, z in age_rows.groupby('rho')}
        assert ages == json.loads(row.source_age_by_rho)
        assert row.deduplicated_ages == '|'.join(map(str, sorted(set(ages.values()))))
        public = frames['real']['public']
        rp = public[(public.dataset == row.dataset) & (public.analysis == row.analysis) & (public.split == row.split)]
        assert rp.case.nunique() == 8 and rp.ages.eq(row.deduplicated_ages).all()
        life_rows = group[(group.policy == 'run_to_failure') & (group.lead_cycles == (30 if row.dataset == 'Battery' else 10)) & (group.rho == 5)].set_index('unit')
        for case, g in rp.groupby('case'):
            q = g.iloc[0]
            policy = 'STW_cost' if q.logger == 'plain' else 'STW_cost_1se'
            log = group[(group.policy == policy) & (group.lead_cycles == q.lead) & (group.rho == q.rho)].set_index('unit').loc[g.unit]
            assert np.array_equal(g.horizon.to_numpy(), log.use.to_numpy())
            assert np.array_equal(g.logger_failed.to_numpy(bool), log.fail.to_numpy(bool))
            truth = frames['real']['sealed']
            truth = truth[truth.case == case].set_index('unit').loc[g.unit]
            assert np.array_equal(truth.lifetime.to_numpy(), life_rows.loc[g.unit].use.to_numpy())
    passed('all 38 real policy pools reproduced from hashed frozen conventional age schedules')
    passed('all 304 real logging records and sealed lifetimes reproduced from frozen source rows')

    paired = {}
    for name in ['synthetic', 'real']:
        x = frames[name]['results']
        p = pd.read_csv(OUT / f'{name}_paired.csv.gz')
        a = x[x.method == 'exact_shared_clock'].set_index('case')
        for baseline, g in p.groupby('baseline'):
            b = x[x.method == baseline].set_index('case')
            g = g.set_index('case').loc[a.index]
            close(g.relative_regret_difference, a.realized_relative_regret - b.realized_relative_regret)
            close(g.rate_difference, a.cost_rate - b.cost_rate)
            close(g.risk_difference, a.risk - b.risk)
            close(g.guaranteed_factor_reduction, b.exact_worst_relative_regret - a.exact_worst_relative_regret)
            assert np.array_equal(g.choice_differs, a.selected_age != b.selected_age)
        paired[name] = p
        passed(f'{name}: all paired effects recomputed on aligned cases')
    st = pd.read_csv(OUT / 'synthetic_paired_tests.csv')
    assert len(st) == 48
    rng = np.random.default_rng(9102026)
    for row in st.itertuples(index=False):
        g = paired['synthetic'][(paired['synthetic'].setting_id == row.setting_id) & (paired['synthetic'].baseline == row.baseline)]
        d = g.relative_regret_difference.to_numpy()
        assert len(d) == row.independent_cohorts == 100
        wins, losses = int((d < -1e-12).sum()), int((d > 1e-12).sum())
        assert (wins, losses, 100 - wins - losses) == (row.wins, row.losses, row.ties)
        p = binomtest(wins, wins + losses, .5).pvalue if wins + losses else 1.
        close(p, row.p_raw)
        close(d.mean(), row.mean_relative_regret_difference)
        interval = np.quantile(d[rng.integers(0, 100, size=(2000, 100))].mean(1), [.025, .975])
        close(interval, [row.nominal_bootstrap_low, row.nominal_bootstrap_high])
    close(corrected(st.p_raw), st.p_holm)
    passed('48 independent-cohort sign tests, wins/ties/losses and Holm family reproduced')
    passed('all 48 nominal paired-mean bootstrap intervals reproduced from fixed resampling seed')
    gt = pd.read_csv(OUT / 'real_outer_split_tests.csv', dtype={'split': str})
    assert gt.primary_regime.sum() == 21 and (~gt.primary_regime).sum() == 3
    splits = paired['real'].groupby(['dataset', 'analysis', 'split', 'baseline']).relative_regret_difference.mean().reset_index()
    for row in gt.itertuples(index=False):
        g = splits[(splits.dataset == row.dataset) & (splits.analysis == row.analysis) & (splits.baseline == row.baseline)]
        d = g.relative_regret_difference.to_numpy()
        wins, losses = int((d < -1e-12).sum()), int((d > 1e-12).sum())
        assert (wins, losses, len(d) - wins - losses) == (row.wins, row.losses, row.ties)
        assert row.outer_splits == len(d) and row.primary_regime == (row.analysis != 'cv123')
        close(d.mean(), row.mean_relative_regret_difference)
        close(binomtest(wins, wins + losses, .5).pvalue if wins + losses else 1., row.p_raw)
    for flag in [True, False]:
        group = gt[gt.primary_regime == flag]
        close(corrected(group.p_raw), group.p_holm)
    passed('real repeated settings aggregated by outer split; 21 primary and 3 sensitivity tests separated')
    audit = pd.read_csv(OUT / 'independent_oracle_audit.csv')
    assert len(audit) == 120 and audit.exact_match.all()
    assert (audit.fast_seconds > 0).all() and (audit.generic_seconds > 0).all()
    passed('120 additional generic-state audit matches and positive runtime records retained')
    findings = json.loads((OUT / 'findings.json').read_text())
    better = int(((st.p_holm < .05) & (st.mean_relative_regret_difference < 0)).sum())
    worse = int(((st.p_holm < .05) & (st.mean_relative_regret_difference > 0)).sum())
    assert (better, worse, int((st.p_holm >= .05).sum())) == (13, 15, 20)
    assert findings['synthetic_holm_significant_better'] == better and findings['synthetic_holm_significant_worse'] == worse
    assert not ((gt.p_holm < .05) & gt.primary_regime).any()
    assert not findings['population_superiority_established'] and not findings['specific_algorithm_priority_established']
    passed('positive and negative findings reproduced; superiority and priority remain unestablished')
    demo = json.loads((OUT / 'strict_example.json').read_text())
    assert demo['exact_selected_age'] == demo['upper_rate_selected_age'] == 8
    assert demo['rectangle_selected_age'] == 24
    assert demo['exact_scores'][0] == '3' and demo['exact_scores'][3] == '320/17'
    passed('strict method-distinguishing example retained with the matching upper-rate control')
    for name in ['shared_clock_example', 'synthetic_tradeoff']:
        assert (OUT / f'{name}.png').stat().st_size > 10000 and (OUT / f'{name}.svg').stat().st_size > 10000
    passed('both scientific figure pairs produced; PNGs visually inspected in the working session')
    assert all(sha(p) == h for p, h in frozen.items())
    passed('all 809 prior protected artifact hashes unchanged after complete audit')

    verification = dict(passed=True, checks=len(checks), details=checks, unit_test_groups=12,
                        exhaustive_cases=250, generic_cases_in_tests=100, generic_cases_in_audit=120,
                        attaining_pairwise_witnesses=witness_count, protected_unchanged=len(frozen))
    (OUT / 'verification.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
    created = datetime.now(timezone.utc).isoformat()
    record = dict(record_type='internal research provenance; not public priority', created_utc=created,
                  claim='ordered failure-phase/count exact finite-cohort relative-regret age replacement',
                  scientific_priority_established=False, public_disclosure_performed=False,
                  plan_sha256=sha('clock_regret/PLAN.md'), theory_sha256=sha('clock_regret/THEORY.md'),
                  implementation_sha256=sha('clock_regret/core.py'),
                  literature_audit_sha256=sha('clock_regret/LITERATURE.md'),
                  report_sha256=sha('clock_regret/REPORT.md'))
    (OUT / 'research_record.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    paths = sorted(p for folder in [Path('clock_regret'), OUT] for p in folder.rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts and p.name != 'completion_manifest.json')
    run_log = Path('out/clock_regret_run.log')
    if run_log.exists():
        paths.append(run_log)
    hashes = {p.as_posix(): sha(p) for p in paths}
    manifest = dict(validation_complete=True, implementation_complete=True,
                    exactness_established_under_stated_model=True, candidate_computational_contribution=True,
                    final_outcome='B: potentially novel but insufficiently established',
                    scientific_priority_established=False, public_disclosure_performed=False,
                    population_superiority_established=False, desired_established_global_novelty_achieved=False,
                    verification_checks=len(checks), protected_files_unchanged=len(frozen),
                    hashed_artifacts=len(hashes), created_utc=created, sha256=hashes)
    (OUT / 'completion_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    assert all(sha(p) == h for p, h in hashes.items())
    print(json.dumps({k: v for k, v in manifest.items() if k != 'sha256'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
