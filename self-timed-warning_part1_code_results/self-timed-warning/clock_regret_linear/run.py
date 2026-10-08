"""Frozen-result exact replay and independently sampled computational study."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from clock_regret.core import worst_pair as quadratic
from clock_regret.oracles import endpoint_dp_pair
from clock_regret_linear.core import select, worst_pair

OUT = Path('out/clock_regret_linear')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protect():
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / 'protected_before.json'
    if not destination.exists():
        hashes = json.loads(Path('out/clock_regret/protected_before.json').read_text())
        old_manifest_path = Path('out/clock_regret/completion_manifest.json')
        old = json.loads(old_manifest_path.read_text())
        assert all(sha(p) == h for p, h in old['sha256'].items())
        hashes.update(old['sha256'])
        hashes[old_manifest_path.as_posix()] = sha(old_manifest_path)
        destination.write_text(json.dumps(hashes, indent=2), encoding='utf-8')
        for name in ['PLAN.md', 'PLAN_AMENDMENT.md']:
            (OUT / (name + '.sha256')).write_text(sha(Path('clock_regret_linear') / name), encoding='utf-8')
    hashes = json.loads(destination.read_text())
    assert all(sha(p) == h for p, h in hashes.items()), 'protected research artifact changed'
    return len(hashes)


def attained(result, h, failed, a, b, rho):
    life = result.witness
    assert np.array_equal(life[failed], h[failed]) and (life[~failed] > h[~failed]).all()
    n = len(h)
    ratio = Fraction((n+(rho-1)*int((life <= a).sum())) * int(np.minimum(life, b).sum()),
                     (n+(rho-1)*int((life <= b).sum())) * int(np.minimum(life, a).sum()))
    assert ratio == result.ratio


def replay():
    rows, pair_rows = [], []
    for source in ['synthetic', 'real']:
        public = pd.read_csv(f'out/clock_regret/{source}_public.csv.gz', dtype={'unit': str})
        old_pairs = pd.read_csv(f'out/clock_regret/{source}_pairwise.csv.gz')
        old_results = pd.read_csv(f'out/clock_regret/{source}_results.csv.gz')
        old_groups = dict(tuple(old_pairs.groupby('case', sort=False)))
        chosen = old_results[old_results.method == 'exact_shared_clock'].set_index('case').selected_age
        for case, g in public.groupby('case', sort=False):
            h, failed = g.horizon.to_numpy(np.int64), g.logger_failed.to_numpy(bool)
            ages = list(map(int, g.ages.iloc[0].split('|')))
            rho = int(g.rho.iloc[0])
            start = time.perf_counter()
            answer = select(h, failed, ages, rho)
            seconds = time.perf_counter() - start
            old = old_groups[case].set_index(['age_a', 'age_b'])
            assert ages[answer['chosen']] == chosen[case]
            for i, a in enumerate(ages):
                for j, b in enumerate(ages):
                    result = answer['pairs'][i][j]
                    row = old.loc[(a, b)]
                    assert result.ratio == Fraction(int(row.numerator), int(row.denominator))
                    attained(result, h, failed, a, b, rho)
                    pair_rows.append(dict(source=source, case=case, age_a=a, age_b=b,
                        numerator=result.ratio.numerator, denominator=result.ratio.denominator,
                        objective_evaluations=result.objective_evaluations, branch=result.branch,
                        original_count_cases=int(row.count_cases),
                        lifetime_witness='|'.join(map(str, result.witness))))
            rows.append(dict(source=source, case=case, n=len(h), k=len(ages),
                selected_age=ages[answer['chosen']], worst_factor=str(answer['scores'][answer['chosen']]),
                objective_evaluations=answer['objective_evaluations'], original_count_cases=int(old.count_cases.sum()),
                seconds=seconds, exact_pairwise_match=True, exact_selection_match=True))
        print(f'{source}: exact replay of {len(old_groups)} cohorts complete', flush=True)
    pd.DataFrame(rows).to_csv(OUT / 'replay_cases.csv', index=False)
    pd.DataFrame(pair_rows).to_csv(OUT / 'replay_pairwise.csv.gz', index=False)


def corrected(p):
    p = np.asarray(p)
    order = np.argsort(p, kind='stable')
    result = np.empty(len(p))
    result[order] = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return result


def timing():
    rng = np.random.default_rng(20261011)
    records = []
    for n in [16, 32, 64, 128, 256, 512, 1024]:
        for case in range(12):
            h = rng.integers(1, 25, n)
            failed = rng.random(n) < .15
            rho = int(rng.choice([5, 20, 50]))
            for repeat in range(3):
                measurements, answers = {}, {}
                order = [('linear', worst_pair), ('quadratic', quadratic)]
                if (case + repeat) % 2:
                    order.reverse()
                for method, fn in order:
                    start = time.perf_counter_ns()
                    answer = fn(h, failed, 40, 20, rho)
                    measurements[method] = (time.perf_counter_ns() - start) / 1e9
                    answers[method] = answer
                assert answers['linear'].ratio == answers['quadratic'].ratio
                attained(answers['linear'], h, failed, 40, 20, rho)
                records.append(dict(n=n, independent_input=case, repeat=repeat, rho=rho,
                    linear_seconds=measurements['linear'], quadratic_seconds=measurements['quadratic'],
                    linear_objectives=answers['linear'].objective_evaluations,
                    quadratic_count_cases=answers['quadratic'].count_cases,
                    numerator=answer.ratio.numerator, denominator=answer.ratio.denominator,
                    horizon='|'.join(map(str,h)), logger_failed='|'.join(map(str,failed.astype(int))),
                    exact_match=True))
        print(f'Later-pair benchmark n={n}: 12 independent inputs, 3 repeats complete', flush=True)
    raw = pd.DataFrame(records)
    raw.to_csv(OUT / 'timing_raw.csv.gz', index=False)
    inputs = raw.groupby(['n', 'independent_input'])[['linear_seconds', 'quadratic_seconds']].median().reset_index()
    inputs['speedup'] = inputs.quadratic_seconds / inputs.linear_seconds
    inputs.to_csv(OUT / 'timing_independent_inputs.csv', index=False)
    tests = []
    for n, g in inputs.groupby('n'):
        delta = g.linear_seconds - g.quadratic_seconds
        wins, losses = int((delta < 0).sum()), int((delta > 0).sum())
        tests.append(dict(n=n, independent_inputs=len(g), linear_faster=wins, quadratic_faster=losses,
            ties=len(g)-wins-losses, median_linear_seconds=g.linear_seconds.median(),
            median_quadratic_seconds=g.quadratic_seconds.median(), median_speedup=g.speedup.median(),
            min_speedup=g.speedup.min(), max_speedup=g.speedup.max(),
            p_raw=binomtest(wins, wins+losses, .5).pvalue if wins+losses else 1.))
    tests = pd.DataFrame(tests)
    tests['p_holm'] = corrected(tests.p_raw)
    tests.to_csv(OUT / 'timing_paired_tests.csv', index=False)
    diagnostics = []
    rng2 = np.random.default_rng(20261012)
    for n in [4, 8, 12, 16, 24]:
        for case in range(12):
            h = rng2.integers(1, 25, n)
            failed = rng2.random(n) < .25
            rho = 20
            for a, b in [(40, 20), (20, 40)]:
                start = time.perf_counter_ns()
                answer = worst_pair(h, failed, a, b, rho)
                elapsed = (time.perf_counter_ns()-start)/1e9
                start = time.perf_counter_ns()
                old = quadratic(h, failed, a, b, rho)
                old_elapsed = (time.perf_counter_ns()-start)/1e9
                start = time.perf_counter_ns()
                oracle, transitions, _ = endpoint_dp_pair(h, failed, a, b, rho)
                oracle_elapsed = (time.perf_counter_ns()-start)/1e9
                assert answer.ratio == old.ratio == oracle
                diagnostics.append(dict(n=n, case=case, age_a=a, age_b=b, linear_seconds=elapsed,
                    quadratic_seconds=old_elapsed, generic_seconds=oracle_elapsed,
                    generic_transitions=transitions, exact_match=True))
    pd.DataFrame(diagnostics).to_csv(OUT / 'small_input_diagnostics.csv', index=False)


def main():
    start = time.monotonic()
    protected = protect()
    replay()
    timing()
    summary = dict(protected_artifacts_unchanged=protect(), initial_protected_count=protected,
        replay_cohorts=2704, pairwise_optima_reproduced=39448,
        independent_timing_inputs=84, repeated_timings_per_input=3,
        timing_family=7, diagnostic_generic_state_comparisons=120,
        scientific_priority_established=False, population_performance_changed=False,
        elapsed_seconds=time.monotonic()-start,
        environment=dict(python=platform.python_version(), platform=platform.platform(),
                         numpy=np.__version__, pandas=pd.__version__))
    (OUT / 'run_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
