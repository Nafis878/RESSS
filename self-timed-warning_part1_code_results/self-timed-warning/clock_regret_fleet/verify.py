"""Freeze the completed evidence and construct an isolated mathematical review kit."""
from pathlib import Path
from fractions import Fraction as F
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import zipfile
import pymupdf
from clock_regret_fleet.run import OUT,protect,sha
from clock_regret_fleet.core import pair
from clock_regret_fleet.oracles import integer_pair,integer_family,continuous_pair,rate


def read(name): return json.loads((OUT/name).read_text())


def main():
    count=protect(); checks={}
    test=subprocess.run([sys.executable,'-m','unittest','clock_regret_fleet.test_core','-v'],capture_output=True,text=True)
    (OUT/'tests.log').write_text(test.stdout+test.stderr)
    checks['ten_test_groups_pass']=test.returncode==0 and 'Ran 10 tests' in test.stderr
    rows=read('full_clock.json')
    checks['1000_stored_full_clock_cases']=len(rows)==1000
    checks['independent_full_clock_values_recomputed']=all(
        integer_pair(r['h'],r['f'],r['a'],r['b'],list(map(F,r['q'])))==F(r['truth']) for r in rows)
    checks['all_integer_witness_values_feasible']=all(
        all(t==h if f else t>h for t,h,f in zip(r['witness'],r['h'],r['f']))
        and rate(r['witness'],r['a'],list(map(F,r['q'])))/rate(r['witness'],r['b'],list(map(F,r['q'])))==F(r['lower']) for r in rows)
    checks['all_pair_intervals_valid']=all(F(r['lower'])<=F(r['truth'])<=F(r['upper'])<=F(5,4)*F(r['lower']) for r in rows)
    families=read('full_family.json')
    checks['200_independent_families_recomputed']=len(families)==200 and all(
        integer_family(r['h'],r['f'],r['ages'],list(map(F,r['q'])))==list(map(F,r['truth'])) for r in families)
    checks['stored_family_selection_factors_valid']=all(
        F(r['truth'][r['chosen']])<=F(5,4)*min(map(F,r['truth'])) for r in families)
    continuous=read('continuous.json')
    checks['200_continuous_phase_oracles_recomputed']=len(continuous)==200 and all(
        continuous_pair(r['h'],r['f'],r['a'],r['b'],list(map(F,r['q'])))==F(r['truth']) for r in continuous)
    checks['continuous_intervals_and_limits_labeled']=all(
        F(r['lower'])<=F(r['truth'])<=F(r['upper']) and all(
            r['limiting_lifetimes'][i]==r['h'][i] or r['a']>r['b'] for i in r['approach_indices']) for r in continuous)
    real=read('engineering_scenarios.json'); summary=read('engineering_summary.json')
    checks['all_304_engineering_scenarios_present']=len(real)==304
    checks['208_nontrivial_and_96_single_age_cohorts']=sum(len(r['ages'])>1 for r in real)==208 and sum(len(r['ages'])==1 for r in real)==96
    checks['all_engineering_exact_decision_certificates_valid']=all(r['certified'] and
        F(r['exact_scores'][r['ages'].index(r['approximate_age'])])==min(map(F,r['exact_scores'])) for r in real)
    checks['engineering_negative_results_retained']=summary['realized_win_tie_loss']==[5,291,8] and summary['mean_realized_relative_regret_change']>0
    checks['engineering_scenarios_labeled_not_measured']=summary['scenario_rule'].startswith('q_i=') and not summary['independent_observations']
    stress=read('tolerance_stress.json')
    checks['90_tolerance_cases_with_valid_bounds']=len(stress)==90 and all(
        F(r['lower'])<=F(r['exact'])<=F(r['upper'])<=(1+F(r['epsilon']))*F(r['lower']) for r in stress)
    checks['nonzero_approximation_losses_exercised']=any(F(r['approximation_factor'])>1 for r in stress)
    snapshot=OUT/'initial_conservative_certificate'
    checks['initial_algorithm_and_evidence_preserved']=all(sha(snapshot/name)==value for name,value in json.loads((snapshot/'snapshot.json').read_text()).items())
    pdf=pymupdf.open(OUT/'manuscript.pdf'); text='\n'.join(p.get_text() for p in pdf)
    checks['seven_page_attributed_manuscript']=len(pdf)==7 and 'Nafis Wadud Ansari' in text and 'Daffodil International University' in text
    checks['complete_theorem_and_negative_results_in_pdf']=all(s in text for s in ['FPTAS','F1','F2','F3','F4','F5','Appendix A','0.004718'])
    checks['pdf_no_text_outside_page']=all(
        x0>=45 and y0>=30 and x1<=page.rect.width-45 and y1<=page.rect.height-20
        for page in pdf for x0,y0,x1,y1,*_ in page.get_text('blocks'))
    qa=read('pdf_qa.json')
    checks['all_final_pages_visually_reviewed']=qa['visual_inspection_complete'] and qa['rendered_pages']==len(pdf)
    checks['974_prior_artifacts_unchanged']=count==974 and protect()==974
    assert all(checks.values()),checks
    (OUT/'research_record.json').write_text(json.dumps(dict(date='2026-10-08',python=sys.version,platform=platform.platform(),
        plan_sha256=sha('clock_regret_fleet/PLAN.md'),source_inputs={p:sha(p) for p in [
            'out/clock_regret/real_public.csv.gz','out/clock_regret/real_sealed.csv.gz','out/clock_regret/real_results.csv.gz']},
        source_artifacts_preserved=count,novelty_verdict='B',historical_priority_established=False),indent=2))
    (OUT/'verification.json').write_text(json.dumps(dict(checks=checks,passed=sum(checks.values()),novelty_verdict='B'),indent=2))
    files=[p for p in Path('clock_regret_fleet').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [p for p in OUT.rglob('*') if p.is_file() and p.name not in ['review_bundle.zip','completion_manifest.json','bundle_tests.log']]
    helper_paths=['clock_regret/core.py','clock_regret/oracles.py','clock_regret_linear/core.py','clock_regret_priority/heterogeneous.py']
    helper_paths+=['out/clock_regret/real_public.csv.gz','out/clock_regret/real_sealed.csv.gz','out/clock_regret/real_results.csv.gz']
    bundle=OUT/'review_bundle.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(set(files+[Path(p) for p in helper_paths])): archive.write(p,p.as_posix())
    with tempfile.TemporaryDirectory(prefix='fleet_review_') as temp:
        with zipfile.ZipFile(bundle) as archive: archive.extractall(temp)
        independent=subprocess.run([sys.executable,'-m','unittest','clock_regret_fleet.test_core','-v'],cwd=temp,capture_output=True,text=True)
        (OUT/'bundle_tests.log').write_text(independent.stdout+independent.stderr)
        assert independent.returncode==0,independent.stderr
    new_files=[p for folder in [Path('clock_regret_fleet'),OUT] for p in folder.rglob('*') if p.is_file()
               and '__pycache__' not in p.parts and p.name!='completion_manifest.json']
    manifest=dict(date='2026-10-08',local_research_phases_complete=True,requested_novelty_score_9_established=False,
        novelty_verdict='B',historical_priority_established=False,public_priority_established=False,
        protected_artifacts_unchanged=count,verification_checks_passed=sum(checks.values()),
        isolated_bundle_tests_passed=True,bundle_sha256=sha(bundle),sha256={p.as_posix():sha(p) for p in sorted(new_files)})
    (OUT/'completion_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:v for k,v in manifest.items() if k!='sha256'},indent=2))


if __name__=='__main__': main()
