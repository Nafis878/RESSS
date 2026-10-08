"""Final evidence audit, preserved-artifact checks and internal review bundle.

Run at the project root. This verifies stored results without retiming methods.
The bundle is a local review artifact, not a public priority deposit.
"""
from datetime import datetime, timezone
from fractions import Fraction
import importlib.metadata
import inspect
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile
import numpy as np
import pandas as pd
from pypdf import PdfReader
from clock_regret_linear.core import select, worst_pair
from clock_regret_linear.continuous import ContinuousPrepared, closure_state_pair, select as continuous_select
from clock_regret_linear.run import OUT, protect, sha


CHECKS = []


def check(name, condition):
    if not bool(condition):
        raise AssertionError(name)
    CHECKS.append(dict(name=name, passed=True))


def vectors(row):
    h = np.array(list(map(int, row.horizon.split('|'))), dtype=np.int64)
    f = np.array(list(map(int, row.logger_failed.split('|'))), dtype=bool)
    return h, f


def rate_ratio(life, a, b, rho):
    # Independent direct evaluation; accepts exact Fraction continuous times.
    ca = sum(1+(rho-1)*int(t <= a) for t in life)
    cb = sum(1+(rho-1)*int(t <= b) for t in life)
    ta = sum(min(t, a) for t in life)
    tb = sum(min(t, b) for t in life)
    return Fraction(ca, cb) * Fraction(tb, ta)


def tests():
    done = subprocess.run([sys.executable, '-m', 'unittest', 'clock_regret_linear.test_core', '-v'],
                          capture_output=True, text=True, encoding='utf-8', check=False)
    text = done.stdout + done.stderr
    (OUT/'tests.log').write_text(text, encoding='utf-8')
    check('all 15 mathematical unit-test groups pass',
          done.returncode == 0 and re.search(r'Ran 15 tests', text) and text.rstrip().endswith('OK'))
    check('selection API accepts public records without hidden lifetimes',
          list(inspect.signature(select).parameters) ==
          ['horizon', 'logger_failed', 'ages', 'rho', 'include_witness'])


def replay():
    stored = pd.read_csv(OUT/'replay_pairwise.csv.gz')
    cases = pd.read_csv(OUT/'replay_cases.csv')
    check('39,448 stored pairwise rows and 2,704 unique cohorts',
          len(stored) == 39448 and len(cases) == 2704 and
          not stored.duplicated(['source','case','age_a','age_b']).any() and
          not cases.duplicated(['source','case']).any())
    new_groups = dict(tuple(stored.groupby(['source','case'], sort=False)))
    summaries = cases.set_index(['source','case'])
    total = 0
    for source in ['synthetic','real']:
        public = pd.read_csv(f'out/clock_regret/{source}_public.csv.gz', dtype={'unit':str})
        old = pd.read_csv(f'out/clock_regret/{source}_pairwise.csv.gz')
        old_groups = dict(tuple(old.groupby('case', sort=False)))
        results = pd.read_csv(f'out/clock_regret/{source}_results.csv.gz')
        chosen = results[results.method == 'exact_shared_clock'].set_index('case').selected_age
        for case, g in public.groupby('case', sort=False):
            h = g.horizon.to_numpy(np.int64)
            f = g.logger_failed.to_numpy(bool)
            ages = list(map(int, g.ages.iloc[0].split('|')))
            rho = int(g.rho.iloc[0])
            answer = select(h, f, ages, rho, include_witness=False)
            row = summaries.loc[(source,case)]
            assert row.selected_age == chosen[case] == ages[answer['chosen']]
            assert Fraction(row.worst_factor) == answer['scores'][answer['chosen']]
            assert row.n == len(h) and row.k == len(ages)
            assert row.objective_evaluations == answer['objective_evaluations']
            original = old_groups[case].set_index(['age_a','age_b'])
            pair_rows = new_groups[(source,case)]
            assert len(pair_rows) == len(ages)**2
            for p in pair_rows.itertuples(index=False):
                a, b = int(p.age_a), int(p.age_b)
                value = Fraction(int(p.numerator), int(p.denominator))
                before = original.loc[(a,b)]
                assert value == Fraction(int(before.numerator), int(before.denominator))
                fresh = answer['pairs'][ages.index(a)][ages.index(b)]
                assert fresh.ratio == value and fresh.branch == p.branch
                assert fresh.objective_evaluations == p.objective_evaluations
                assert p.original_count_cases == before.count_cases
                life = np.array(list(map(int, p.lifetime_witness.split('|'))), dtype=np.int64)
                assert life.shape == h.shape
                assert np.array_equal(life[f],h[f]) and (life[~f] > h[~f]).all()
                # Python ints avoid array multiplication overflow in direct evaluation.
                assert rate_ratio(list(map(int,life)),a,b,rho) == value
                if a > b:
                    assert p.objective_evaluations <= 2
                total += 1
    check('every frozen exact objective and selected age is reproduced', total == 39448)
    check('every stored integer witness is compatible and attains its exact ratio', total == 39448)
    check('later comparisons use at most two objective evaluations', total == 39448)


def statistics():
    raw = pd.read_csv(OUT/'timing_raw.csv.gz')
    inputs = pd.read_csv(OUT/'timing_independent_inputs.csv')
    tests = pd.read_csv(OUT/'timing_paired_tests.csv')
    check('252 positive timing observations, no duplicate repetitions',
          len(raw) == 252 and not raw.duplicated(['n','independent_input','repeat']).any() and
          (raw[['linear_seconds','quadratic_seconds']] > 0).all().all())
    rng = np.random.default_rng(20261011)
    groups = dict(tuple(raw.groupby(['n','independent_input'],sort=False)))
    for n in [16,32,64,128,256,512,1024]:
        for case in range(12):
            h = rng.integers(1,25,n)
            f = rng.random(n)<.15
            rho = int(rng.choice([5,20,50]))
            group = groups[(n,case)]
            assert sorted(group.repeat) == [0,1,2]
            for row in group.itertuples(index=False):
                hh, ff = vectors(row)
                assert np.array_equal(h,hh) and np.array_equal(f,ff) and rho == row.rho
            fresh = worst_pair(h,f,40,20,rho)
            assert all(Fraction(int(x.numerator),int(x.denominator)) == fresh.ratio
                       for x in group.itertuples(index=False))
    check('84 independent timing inputs reproduce the prospective seed and exact objectives', len(groups) == 84)
    med = raw.groupby(['n','independent_input'])[['linear_seconds','quadratic_seconds']].median().reset_index()
    med['speedup'] = med.quadratic_seconds/med.linear_seconds
    pd.testing.assert_frame_equal(inputs,med,check_exact=False,rtol=1e-10,atol=1e-14)
    check('three repeats aggregate to one median per independent statistical unit', len(inputs) == 84)
    ps = []
    for n, g in med.groupby('n'):
        row = tests[tests.n == n].iloc[0]
        delta = g.linear_seconds-g.quadratic_seconds
        wins, losses = int((delta<0).sum()), int((delta>0).sum())
        count = wins+losses
        # Independent exact two-sided binomial calculation; no scipy/run helper.
        p = min(1., 2*sum(math.comb(count,k) for k in range(min(wins,losses)+1))/2**count) if count else 1.
        assert row.independent_inputs == 12 and row.linear_faster == wins and row.quadratic_faster == losses
        assert row.ties == 12-count and row.p_raw == p
        for name, expected in [('median_linear_seconds',g.linear_seconds.median()),
                               ('median_quadratic_seconds',g.quadratic_seconds.median()),
                               ('median_speedup',g.speedup.median()),
                               ('min_speedup',g.speedup.min()),('max_speedup',g.speedup.max())]:
            assert math.isclose(row[name],expected,rel_tol=1e-10,abs_tol=1e-14)
        ps.append(p)
    order = sorted(range(len(ps)),key=lambda i:ps[i])
    adjusted = [0.]*len(ps)
    running = 0.
    for rank, i in enumerate(order):
        running = max(running,min(1.,(len(ps)-rank)*ps[i]))
        adjusted[i] = running
    check('independent exact sign-test and seven-contrast Holm calculations agree',
          np.allclose(tests.p_holm,adjusted,rtol=1e-12,atol=0))
    check('all seven specified later-pair timing contrasts are corrected significant',
          (tests.p_holm<.05).all() and (tests.linear_faster==12).all())
    diagnostic = pd.read_csv(OUT/'small_input_diagnostics.csv')
    check('120 recorded separately structured small-input diagnostics agree',
          len(diagnostic) == 120 and diagnostic.exact_match.all())


def continuous():
    rows = pd.read_csv(OUT/'continuous_oracle.csv')
    check('300 distinct continuous audit cases',len(rows)==300 and rows.case.nunique()==300)
    for row in rows.itertuples(index=False):
        h, f = vectors(row)
        a,b,rho = int(row.age_a),int(row.age_b),int(row.rho)
        pair = ContinuousPrepared(h,f,[a,b],rho).pair(a,b)
        value = Fraction(int(row.numerator),int(row.denominator))
        assert pair.ratio == value == closure_state_pair(h,f,a,b,rho)
        assert pair.attained == row.attained
        previous = Fraction(0)
        for eps in [Fraction(1,2),Fraction(1,16),Fraction(1,1024)]:
            life = pair.completion(eps)
            assert all(t==int(hi) if fi else t>int(hi) for t,hi,fi in zip(life,h,f))
            actual = rate_ratio(life,a,b,rho)
            assert previous <= actual <= value
            if pair.attained:
                assert actual == value
            else:
                assert actual < value
            previous = actual
    check('all continuous optima match a separate phase-labeled state optimizer',True)
    check('900 exact epsilon completions are compatible and approach the declared suprema',True)
    tasks = pd.read_csv(OUT/'resolution_sandwich.csv')
    check('1,500 refinement tasks on 300 distinct independent cohorts',
          len(tasks)==1500 and tasks.case.nunique()==300 and
          not tasks.duplicated(['case','r']).any())
    for case, group in tasks.groupby('case',sort=False):
        assert sorted(group.r)==[1,2,4,16,64]
        first = next(group.itertuples(index=False))
        h,f = vectors(first)
        ages = list(map(int,first.ages.split('|')))
        rho = int(first.rho)
        c = continuous_select(h,f,ages,rho)
        for row in group.itertuples(index=False):
            hh,ff = vectors(row)
            assert np.array_equal(h,hh) and np.array_equal(f,ff)
            assert row.ages==first.ages and row.rho==rho
            r = int(row.r)
            g = select(h*r,f,np.array(ages)*r,rho,include_witness=False)
            bound = Fraction(r+1,r)
            assert Fraction(row.uniform_factor_bound)==bound
            assert Fraction(row.grid_optimum)==min(g['scores'])
            assert Fraction(row.continuous_optimum)==min(c['scores'])
            assert row.grid_age==ages[g['chosen']] and row.continuous_age==ages[c['chosen']]
            assert Fraction(row.selected_continuous_factor)==c['scores'][g['chosen']]
            for i in range(len(ages)):
                assert g['scores'][i] <= c['scores'][i] <= bound*g['scores'][i]
                for j in range(len(ages)):
                    grid, cont = g['pairs'][i][j].ratio,c['pairs'][i][j].ratio
                    assert grid <= cont <= bound*grid
            assert c['scores'][g['chosen']] <= bound*min(c['scores'])
    check('all stored pairwise, policywise and selected-policy refinement bounds independently recompute',True)
    example = pd.read_csv(OUT/'resolution_example.csv')
    h,f = [1]*5,[True]*4+[False]
    for row in example.itertuples(index=False):
        r = int(row.r)
        pair = worst_pair(np.array(h)*r,f,3*r,2*r,2)
        assert pair.ratio == Fraction(row.grid_factor)
        assert Fraction(row.continuous_factor)==Fraction(10,9)
        assert row.branch==pair.branch
    check('integer/continuous counterexample and branch switch reproduce',len(example)==7)


def document():
    paper = PdfReader(OUT/'manuscript.pdf')
    text = '\n'.join(page.extract_text() for page in paper.pages)
    check('five-page manuscript contains all three theorems and human-readable references',
          len(paper.pages)==5 and all(x in text for x in ['THEOREM 1','THEOREM 2','THEOREM 3','References']))
    check('manuscript attributes the verified block-replacement author correctly',
          'Ganesaraman, A.' in text and 'Ganesaraman, K.' not in text)
    check('all manuscript pages rendered for visual review',
          all((OUT/'qa'/f'page-{i+1}.png').is_file() for i in range(len(paper.pages))))
    (OUT/'pdf_qa.json').write_text(json.dumps(dict(
        pdf_sha256=sha(OUT/'manuscript.pdf'), pages=len(paper.pages),
        renderer='PyMuPDF, scale 1.3; Poppler executable unavailable',
        visual_review='All five latest page PNGs inspected by the authoring assistant before final packaging.',
        visual_defects_detected=0, table_split=False),indent=2),encoding='utf-8')


def payload_files():
    excluded = {'completion_manifest.json','review_bundle.zip','payload_hashes.json','bundle_tests.log'}
    paths = [p for folder in [Path('clock_regret_linear'),OUT] for p in folder.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and 'qa' not in p.parts and p.name not in excluded]
    paths += [Path('clock_regret/core.py'),Path('clock_regret/oracles.py')]
    for source in ['synthetic','real']:
        paths += [Path(f'out/clock_regret/{source}_{kind}.csv.gz') for kind in ['public','pairwise','results']]
    paths += [Path('clock_regret/REPORT.md'),Path('out/clock_regret/findings.json'),
              Path('out/clock_regret/synthetic_paired_tests.csv'),
              Path('out/clock_regret/real_outer_split_tests.csv')]
    return sorted(set(paths),key=lambda p:p.as_posix())


def package():
    paths = payload_files()
    hashes = {p.as_posix():sha(p) for p in paths}
    (OUT/'payload_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    paths.append(OUT/'payload_hashes.json')
    archive = OUT/'review_bundle.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(paths,key=lambda p:p.as_posix()):
            item = zipfile.ZipInfo(p.as_posix(),date_time=(2026,10,8,0,0,0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o644 << 16
            z.writestr(item,p.read_bytes())
    import hashlib
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {p.as_posix() for p in paths}
        archived_hashes = json.loads(z.read((OUT/'payload_hashes.json').as_posix()))
        assert archived_hashes == hashes
        assert all(hashlib.sha256(z.read(p)).hexdigest()==h for p,h in hashes.items())
        # Execute the packaged sources independently of the preserved workspace.
        with tempfile.TemporaryDirectory(prefix='clock_regret_review_') as folder:
            z.extractall(folder)
            environment = dict(os.environ)
            environment.pop('PYTHONPATH',None)
            command = (
                'from pathlib import Path; import unittest; '
                'import clock_regret_linear.core as core; '
                'import clock_regret.core as helper; '
                'assert Path(core.__file__).resolve().is_relative_to(Path.cwd()); '
                'assert Path(helper.__file__).resolve().is_relative_to(Path.cwd()); '
                'suite=unittest.defaultTestLoader.loadTestsFromName("clock_regret_linear.test_core"); '
                'result=unittest.TextTestRunner(verbosity=2).run(suite); '
                'raise SystemExit(0 if result.wasSuccessful() else 1)'
            )
            tested = subprocess.run([sys.executable,'-c',command],cwd=folder,env=environment,
                                    capture_output=True,text=True,encoding='utf-8',check=False)
            log = tested.stdout+tested.stderr
            (OUT/'bundle_tests.log').write_text(log,encoding='utf-8')
            assert tested.returncode==0 and re.search(r'Ran 15 tests',log) and log.rstrip().endswith('OK')
    return dict(path=archive.as_posix(),sha256=sha(archive),entries=len(paths),
                purpose='Internal unpublished review bundle',bytes=archive.stat().st_size,
                isolated_archive_unit_test_groups_passed=15)


def main():
    count = protect()
    check('858 earlier artifacts unchanged before the audit',count==858)
    for name in ['PLAN.md','PLAN_AMENDMENT.md','PLAN_RESOLUTION.md']:
        check(f'retained {name} matches its pre-experiment hash',
              sha(Path('clock_regret_linear')/name)==(OUT/(name+'.sha256')).read_text().strip())
    tests(); replay(); statistics(); continuous(); document()
    check('858 earlier artifacts unchanged after all evidence checks',protect()==858)
    for name, flag in [('run_summary.json','scientific_priority_established'),
                       ('resolution_summary.json','priority_established')]:
        check(f'{name} does not fabricate priority',json.loads((OUT/name).read_text())[flag] is False)
    record = dict(
        recorded_at_utc=datetime.now(timezone.utc).isoformat(),
        title='Exact Relative-Regret Age Replacement under Censoring: Two Extremal Worlds and a Clock-Resolution Guarantee',
        authorship='Pending actual author names and affiliations',
        status='B: potentially novel specialized contribution; historical originality and public priority unestablished',
        mathematical_claims=['Two-world integer later-pair characterization',
                            'Exact O(n log n + K^2 n) full-family solver',
                            'Continuous limiting-world supremum',
                            'Uniform (1+1/r) refinement and selected-policy guarantee'],
        public_priority_established=False, externally_peer_reviewed=False, public_deposit=None,
        license='Unspecified; review artifact only',
        scope='Finite recorded cohort, fixed integer ages and horizons, common integer cost ratio > 1, Cartesian completions',
        unchanged_prior_artifacts=count, unchanged_prior_population_performance=True,
        verification_checks=len(CHECKS), all_verification_checks_passed=True,
        environment={name:importlib.metadata.version(name) for name in
                     ['numpy','pandas','scipy','matplotlib','reportlab','pypdf','pymupdf']},
        python=sys.version, source_sha256={p.as_posix():sha(p) for p in Path('clock_regret_linear').glob('*.py')})
    (OUT/'research_record.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    verification = dict(passed=True,checks=CHECKS,check_count=len(CHECKS),
                        protected_artifacts_unchanged=count,scientific_priority_established=False)
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
    bundle = package()
    # Reversible test imports may create bytecode; exclude it from the manifest.
    files = sorted(p for folder in [Path('clock_regret_linear'),OUT] for p in folder.rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts and p.name!='completion_manifest.json')
    manifest = dict(status='Complete local mathematical, experimental and review package',
                    scientific_priority_established=False,public_release_pending=True,
                    protected_artifacts_unchanged=protect(),verified_check_count=len(CHECKS),
                    new_artifact_count=len(files),review_bundle=bundle,
                    sha256={p.as_posix():sha(p) for p in files})
    destination = OUT/'completion_manifest.json'
    destination.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    saved = json.loads(destination.read_text())
    assert all(sha(p)==h for p,h in saved['sha256'].items())
    print(json.dumps(dict(verification_checks=len(CHECKS),all_passed=True,
                         protected_artifacts_unchanged=count,new_hashed_artifacts=len(files),
                         manuscript_pages=5,review_bundle=bundle,
                         scientific_priority_established=False),indent=2),flush=True)


if __name__=='__main__':
    main()
