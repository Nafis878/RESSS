"""Frozen real replay, independent synthetic cohorts, exact witness artifacts."""
import itertools
import json
import hashlib
import platform
import time
from pathlib import Path
import numpy as np
import pandas as pd
from clock_regret.core import select, outcomes, compatible
from clock_regret.oracles import exhaustive_pair, endpoint_dp_pair

OUT = Path('out/clock_regret')
DOMAINS = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6', 'Battery']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protect():
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / 'protected_before.json'
    if path.exists():
        hashes = json.loads(path.read_text())
    else:
        hashes = json.loads(Path('out/method_validation/protected_before.json').read_text())
        for folder in [Path('method_validation'), Path('out/method_validation')]:
            for p in folder.rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:
                    hashes[p.as_posix()] = sha(p)
        path.write_text(json.dumps(hashes, indent=1), encoding='utf-8')
        (OUT / 'plan_sha256.txt').write_text(sha('clock_regret/PLAN.md'))
    assert all(sha(p) == h for p, h in hashes.items()), 'frozen artifact changed'
    return len(hashes)


def evaluate(case, meta, units, life, h, failed, ages, rho, rows, pair_rows, public, sealed):
    start = time.perf_counter()
    decision = select(h, failed, ages, rho)
    elapsed = time.perf_counter() - start
    assert compatible(life, h, failed)
    c, t, f = outcomes(life, ages, rho)
    rate = c.sum(0) / t.sum(0)
    oracle = rate.min()
    for i, unit in enumerate(units):
        public.append(dict(case=case, unit=str(unit), horizon=int(h[i]), logger_failed=bool(failed[i]),
                           ages='|'.join(map(str, ages)), rho=rho, **meta))
        sealed.append(dict(case=case, unit=str(unit), lifetime=int(life[i]), **meta))
    for method, key in [('exact_shared_clock', 'chosen'), ('sharp_rectangle', 'rectangle'),
                        ('upper_rate', 'upper_rate'), ('complete_case', 'complete_case')]:
        j = decision[key]
        truth_regret = float(rate[j] / oracle)
        worst = float(decision['scores'][j])
        assert truth_regret <= worst + 1e-10
        rows.append(dict(case=case, method=method, n=len(life), ages='|'.join(map(str, ages)),
                         selected_age=int(ages[j]), selected_index=j, cost_rate=float(rate[j]),
                         risk=float(f[:, j].mean()), realized_relative_regret=truth_regret,
                         exact_worst_relative_regret=worst,
                         rectangle_worst_upper=float(decision['rectangle_scores'][j]),
                         risk_upper=float(decision['risk_upper'][j]),
                         compute_seconds=elapsed, **meta))
    for i, a in enumerate(ages):
        for j, b in enumerate(ages):
            p = decision['pairs'][i][j]
            assert compatible(p.witness, h, failed)
            pair_rows.append(dict(case=case, age_a=int(a), age_b=int(b),
                                  numerator=p.ratio.numerator, denominator=p.ratio.denominator,
                                  exact_worst_ratio=float(p.ratio), count_cases=p.count_cases,
                                  rectangle_upper=(1. if i == j else float(decision['marginal_intervals'][i][1] / decision['marginal_intervals'][j][0])),
                                  lifetime_witness='|'.join(map(str, p.witness)), **meta))


def synthetic():
    rows, pairs, public, sealed = [], [], [], []
    case = 0
    settings = list(itertools.product([12, 24], [6, 10], [5, 20], ['short', 'long', 'mixture']))
    for setting_id, (n, horizon, rho, law) in enumerate(settings):
        for replicate in range(100):
            case += 1
            seed = 910000 + 1000 * setting_id + replicate
            rng = np.random.default_rng(seed)
            short = rng.integers(4, 15, n)
            long = rng.integers(18, 41, n)
            life = short if law == 'short' else long if law == 'long' else np.where(rng.random(n) < .5, short, long)
            h = np.minimum(life, horizon)
            failed = life <= horizon
            meta = dict(source='synthetic', dataset=law, analysis='independent_cohorts',
                        split=str(setting_id), logger=f'age{horizon}', rho=rho,
                        setting_id=setting_id, replicate=replicate, seed=seed, logging_age=horizon)
            # rho is supplied once in the public schema by evaluate.
            meta.pop('rho')
            evaluate(case, {**meta, 'evaluation_rho': rho}, np.arange(n), life, h, failed,
                     np.array([8, 12, 16, 24]), rho, rows, pairs, public, sealed)
        print(f'Synthetic setting {setting_id + 1}/24 complete ({law}, n={n}, H={horizon}, rho={rho})', flush=True)
    return pd.DataFrame(rows), pd.DataFrame(pairs), pd.DataFrame(public), pd.DataFrame(sealed)


def real():
    rows, pairs, public, sealed, provenance = [], [], [], [], []
    case = 0
    for ds in DOMAINS:
        source = Path(f'results/contrib/{ds}_cost.csv')
        x = pd.read_csv(source, dtype={'unit': str}, low_memory=False)
        if ds != 'Battery':
            x = x.assign(analysis='engine', split=x.fold.astype(str))
        x['split'] = x.split.astype(str)
        lead = 30 if ds == 'Battery' else 10
        for (analysis, split), g in x.groupby(['analysis', 'split']):
            age_rows = g[(g.policy == 'age') & (g.lead_cycles == 0)]
            ages = []
            source_ages = {}
            for source_rho, z in age_rows.groupby('rho'):
                d = pd.to_numeric(z.setting).unique()
                assert len(d) == 1 and d[0] == int(d[0])
                source_ages[str(int(source_rho))] = int(d[0])
                ages.append(int(d[0]))
            ages = np.array(sorted(set(ages)), dtype=np.int64)
            assert set(source_ages) == {'5', '10', '20', '50'}
            provenance.append(dict(dataset=ds, analysis=analysis, split=split,
                                   source_path=source.as_posix(), source_sha256=sha(source),
                                   source_age_by_rho=json.dumps(source_ages, sort_keys=True),
                                   deduplicated_ages='|'.join(map(str, ages))))
            life_rows = g[(g.policy == 'run_to_failure') & (g.lead_cycles == lead) & (g.rho == 5)]
            life_series = life_rows.set_index('unit').use.sort_index()
            assert not life_series.index.duplicated().any()
            units = life_series.index.to_numpy()
            life = life_series.to_numpy()
            assert np.equal(life, np.floor(life)).all()
            life = life.astype(np.int64)
            for rho in [5, 10, 20, 50]:
                for logger, policy in [('plain', 'STW_cost'), ('1SE', 'STW_cost_1se')]:
                    log = g[(g.policy == policy) & (g.lead_cycles == lead) & (g.rho == rho)].set_index('unit').loc[units]
                    h = log.use.to_numpy()
                    assert np.equal(h, np.floor(h)).all()
                    failed = log.fail.to_numpy(bool)
                    case += 1
                    meta = dict(source='real', dataset=ds, analysis=analysis, split=split,
                                logger=logger, evaluation_rho=rho, lead=lead)
                    evaluate(case, meta, units, life, h.astype(np.int64), failed, ages, rho,
                             rows, pairs, public, sealed)
        print(f'Real replay completed: {ds}', flush=True)
    pd.DataFrame(provenance).to_csv(OUT / 'real_policy_provenance.csv', index=False)
    return pd.DataFrame(rows), pd.DataFrame(pairs), pd.DataFrame(public), pd.DataFrame(sealed)


def oracle_audit():
    rng = np.random.default_rng(20261009)
    rows = []
    for rep in range(120):
        n = int(rng.choice([4, 8, 12]))
        h = rng.integers(1, 20, n)
        failed = rng.random(n) < .25
        a, b = map(int, rng.integers(2, 25, 2))
        rho = int(rng.choice([5, 20, 50]))
        start = time.perf_counter()
        from clock_regret.core import worst_pair
        result = worst_pair(h, failed, a, b, rho)
        fast_time = time.perf_counter() - start
        start = time.perf_counter()
        generic, transitions, vertices = endpoint_dp_pair(h, failed, a, b, rho)
        generic_time = time.perf_counter() - start
        assert result.ratio == generic
        rows.append(dict(rep=rep, n=n, age_a=a, age_b=b, rho=rho,
                         numerator=result.ratio.numerator, denominator=result.ratio.denominator,
                         exact_match=True, fast_seconds=fast_time, generic_seconds=generic_time,
                         count_cases=result.count_cases, generic_transitions=transitions, generic_vertices=vertices))
    pd.DataFrame(rows).to_csv(OUT / 'independent_oracle_audit.csv', index=False)


def main():
    start = time.monotonic()
    protected = protect()
    for name, fn in [('synthetic', synthetic), ('real', real)]:
        results, pairs, public, sealed = fn()
        for label, frame in [('results', results), ('pairwise', pairs), ('public', public), ('sealed', sealed)]:
            frame.to_csv(OUT / f'{name}_{label}.csv.gz', index=False)
        print(f'{name}: {results.case.nunique()} cases, {len(results)} method rows, {len(pairs)} exact witnesses', flush=True)
    oracle_audit()
    manifest = dict(protected_files_unchanged=protect(), synthetic_cases=2400, real_cases=304,
                    oracle_audit_cases=120, initial_protected_count=protected,
                    algorithm='ordered shared-lifetime failure-phase exact relative regret',
                    scientific_priority_established=False,
                    environment=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__),
                    elapsed_seconds=time.monotonic() - start)
    (OUT / 'run_summary.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == '__main__':
    main()
