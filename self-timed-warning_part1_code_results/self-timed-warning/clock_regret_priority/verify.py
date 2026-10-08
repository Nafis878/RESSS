"""Exact evidence and archive audit; never manufacture a positive novelty verdict."""
from datetime import datetime,timezone
from fractions import Fraction
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile
import pandas as pd
from pypdf import PdfReader
import pymupdf
from clock_regret_priority.heterogeneous import later_pair,continuous_later_pair,phase_oracle,rate_ratio
from clock_regret_priority.test_heterogeneous import exhaustive
from clock_regret_priority.run import OUT,protect,sha
from clock_regret_linear.core import worst_pair as common_pair
from clock_regret_linear.continuous import ContinuousPrepared

CHECKS=[]


def check(name,condition):
    if not bool(condition):raise AssertionError(name)
    CHECKS.append(dict(name=name,passed=True))


def inputs(row):
    return (list(map(int,row.horizon.split('|'))),list(map(bool,map(int,row.logger_failed.split('|')))),
            int(row.age_a),int(row.age_b),list(map(Fraction,row.premiums.split('|'))))


def evidence():
    full=pd.read_csv(OUT/'full_clock.csv.gz')
    check('1,000 unique full-clock cases recorded',len(full)==1000 and full.case.nunique()==1000)
    for row in full.itertuples(index=False):
        h,f,a,b,q=inputs(row);p=later_pair(h,f,a,b,q)
        assert p.ratio==Fraction(row.exact_ratio)==Fraction(row.oracle_ratio)==exhaustive(h,f,a,b,q)
        life=tuple(map(int,row.witness.split('|')))
        assert p.witness==life and p.shared_count==row.shared_count
        assert p.denominators==tuple(map(Fraction,row.denominators.split('|')))
        assert all(t==hi if fi else t>hi for t,hi,fi in zip(life,h,f))
        assert rate_ratio(life,a,b,q)==p.ratio
    check('all 1,000 exhaustive ratios and attaining witnesses independently recompute',True)
    phases=pd.read_csv(OUT/'phase_oracles.csv.gz')
    check('500 integer and 500 continuous state comparisons recorded',
          phases.groupby('method').size().to_dict()=={'integer_state':500,'continuous_state':500})
    for row in phases.itertuples(index=False):
        h,f,a,b,q=inputs(row);c=row.method=='continuous_state'
        p=continuous_later_pair(h,f,a,b,q) if c else later_pair(h,f,a,b,q)
        assert p.ratio==Fraction(row.exact_ratio)==Fraction(row.oracle_ratio)==phase_oracle(h,f,a,b,q,c)
    check('every separately structured integer and continuous state optimum recomputes',True)
    reduction=pd.read_csv(OUT/'common_reduction.csv.gz')
    check('200 integer and 200 continuous common-cost reductions recorded',
          reduction.groupby('method').size().to_dict()=={'continuous_common_reduction':200,'integer_common_reduction':200})
    for row in reduction.itertuples(index=False):
        h,f,a,b,q=inputs(row);rho=int(q[0])+1
        assert all(x==q[0] and x.denominator==1 for x in q)
        if row.method=='integer_common_reduction':
            value=later_pair(h,f,a,b,q).ratio;before=common_pair(h,f,a,b,rho).ratio
        else:
            value=continuous_later_pair(h,f,a,b,q).ratio;before=ContinuousPrepared(h,f,[a,b],rho).pair(a,b).ratio
        assert value==before==Fraction(row.exact_ratio)==Fraction(row.oracle_ratio)
    check('every common-cost reduction matches preserved solver exactly',True)
    eps=pd.read_csv(OUT/'epsilon_sequences.csv.gz')
    check('600 epsilon completions on 200 unique cohorts recorded',len(eps)==600 and eps.case.nunique()==200)
    for case,group in eps.groupby('case',sort=False):
        previous=Fraction(0)
        for row in group.itertuples(index=False):
            h,f,a,b,q=inputs(row);p=continuous_later_pair(h,f,a,b,q)
            life=p.completion(Fraction(row.epsilon));value=rate_ratio(life,a,b,q)
            assert life==tuple(map(Fraction,row.completion.split('|')))
            assert p.ratio==Fraction(row.exact_ratio) and p.attained==row.attained
            assert value==Fraction(row.completion_ratio) and previous<=value<=p.ratio
            assert all(t==hi if fi else t>hi for t,hi,fi in zip(life,h,f))
            assert (value==p.ratio)==p.attained;previous=value
    check('all compatible epsilon sequences and attainment labels recompute',True)
    resolution=pd.read_csv(OUT/'resolution.csv.gz')
    check('1,000 refinement tasks on 200 cohorts recorded',len(resolution)==1000 and resolution.case.nunique()==200)
    for case,group in resolution.groupby('case',sort=False):
        assert sorted(group.r)==[1,2,4,16,64]
        for row in group.itertuples(index=False):
            h,f,a,b,q=inputs(row);r=int(row.r)
            c=continuous_later_pair(h,f,a,b,q).ratio
            g=later_pair([x*r for x in h],f,a*r,b*r,q).ratio
            assert g==Fraction(row.grid_ratio) and c==Fraction(row.exact_ratio)
            assert Fraction(row.uniform_bound)==Fraction(r+1,r)
            assert g<=c<=Fraction(r+1,r)*g
    check('every heterogeneous clock-refinement inequality recomputes exactly',True)
    sharp=pd.read_csv(OUT/'sharpness.csv')
    check('18 sharpness equalities recorded',len(sharp)==18 and not sharp.duplicated(['n','r']).any())
    for row in sharp.itertuples(index=False):
        n,r=int(row.n),int(row.r);q=list(map(Fraction,row.premiums.split('|')))
        c=continuous_later_pair([1]*n,[False]*n,2,1,q).ratio
        g=later_pair([r]*n,[False]*n,2*r,r,q).ratio
        assert g==Fraction(row.grid_ratio) and c==Fraction(row.continuous_ratio)
        assert c/g==Fraction(r+1,r)==Fraction(row.exact_factor)
    check('uniform pairwise constant attains 1+1/r exactly in every sharpness example',True)
    example=json.loads((OUT/'interior_counterexample.json').read_text())
    p=later_pair(example['horizon'],example['logger_failed'],example['age_a'],example['age_b'],example['premiums'])
    check('strict interior optimum invalidates the unchanged two-world extension',
          p.ratio==Fraction(505,306)==Fraction(example['exact_ratio']) and p.shared_count==1 and
          p.ratio>Fraction(example['two_endpoint_ratio']) and p.denominators==(707,612,1010))


def paper():
    pdf=PdfReader(OUT/'manuscript.pdf');text='\n'.join(p.extract_text() for p in pdf.pages)
    check('seven-page attributed draft contains original and added theorems',
          len(pdf.pages)==7 and all(x in text for x in ['THEOREM 1','THEOREM 2','THEOREM 3','THEOREM H1','THEOREM H2','SHARPNESS']))
    check('PDF authorship matches the details supplied by the user',
          pdf.metadata.author=='Nafis Wadud Ansari' and all(x in text for x in
          ['Nafis Wadud Ansari','Daffodil International University','ansari2305341800@diu.edu.bd']))
    check('draft explicitly records unresolved historical status',
          'potentially novel but insufficiently established' in text and 'has not been deposited' in text)
    check('published-paper and earlier inventory-ratio citations appear',
          'Khan, S.' in text and 'Drent, C.' in text and 'Zhu, Z.' in text)
    rendered=pymupdf.open(OUT/'manuscript.pdf')
    check('scientific figures fit completely inside the page content area',
          all(54-.01<=rect.x0 and rect.x1<=A4_WIDTH_MINUS_MARGIN+.01
              for page in rendered for item in page.get_images(full=True)
              for rect in page.get_image_rects(item[0])))
    check('all seven latest QA page PNGs exist',all((OUT/'qa'/f'page-{i+1}.png').is_file() for i in range(7)))
    (OUT/'pdf_qa.json').write_text(json.dumps(dict(pdf_sha256=sha(OUT/'manuscript.pdf'),pages=7,
        renderer='PyMuPDF, scale 1.3',visual_review='All seven corrected page PNGs inspected by the authoring assistant.',
        detected_final_visual_defects=0,development_fix='Figure aspect ratio initialized before assigning draw dimensions.'),indent=2),encoding='utf-8')


A4_WIDTH_MINUS_MARGIN=595.2755905511812-54


def bundle():
    excluded={'completion_manifest.json','review_bundle.zip','payload_hashes.json','bundle_tests.log'}
    paths=[p for folder in [Path('clock_regret_priority'),OUT] for p in folder.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and 'primary_cache' not in p.parts
           and 'qa' not in p.parts and p.name not in excluded]
    paths += [Path('clock_regret/core.py'),Path('clock_regret/oracles.py')]
    paths += [p for p in Path('clock_regret_linear').glob('*') if p.is_file() and p.suffix in ['.py','.md']]
    paths += [Path('out/clock_regret_linear')/name for name in ['runtime.png','resolution.png']]
    paths=sorted(set(paths),key=lambda p:p.as_posix())
    hashes={p.as_posix():sha(p) for p in paths}
    (OUT/'payload_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    paths.append(OUT/'payload_hashes.json')
    archive=OUT/'review_bundle.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(paths,key=lambda p:p.as_posix()):
            item=zipfile.ZipInfo(p.as_posix(),date_time=(2026,10,8,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o644<<16
            z.writestr(item,p.read_bytes())
    import hashlib
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={p.as_posix() for p in paths}
        assert all(hashlib.sha256(z.read(p)).hexdigest()==h for p,h in hashes.items())
        assert not any('primary_cache' in p or '/qa/' in p or '__pycache__' in p for p in z.namelist())
        with tempfile.TemporaryDirectory(prefix='censored_regret_review_') as folder:
            z.extractall(folder);environment=dict(os.environ);environment.pop('PYTHONPATH',None)
            code=('from pathlib import Path; import unittest; '
                  'import clock_regret_priority.heterogeneous as core; '
                  'assert Path(core.__file__).resolve().is_relative_to(Path.cwd()); '
                  'suite=unittest.defaultTestLoader.loadTestsFromName("clock_regret_priority.test_heterogeneous"); '
                  'result=unittest.TextTestRunner(verbosity=2).run(suite); '
                  'raise SystemExit(0 if result.wasSuccessful() else 1)')
            done=subprocess.run([sys.executable,'-c',code],cwd=folder,env=environment,capture_output=True,
                                text=True,encoding='utf-8',check=False)
            log=done.stdout+done.stderr;(OUT/'bundle_tests.log').write_text(log,encoding='utf-8')
            assert done.returncode==0 and 'Ran 8 tests' in log and log.rstrip().endswith('OK')
    return dict(path=archive.as_posix(),sha256=sha(archive),entries=len(paths),bytes=archive.stat().st_size,
                isolated_archive_unit_test_groups_passed=8,public_release=False)


def main():
    check('908 prior artifacts unchanged before audit',protect()==908)
    check('prospective plan retains its pre-test hash',
          sha('clock_regret_priority/PLAN.md')==(OUT/'PLAN.md.sha256').read_text().strip())
    done=subprocess.run([sys.executable,'-m','unittest','clock_regret_priority.test_heterogeneous','-v'],
                        capture_output=True,text=True,encoding='utf-8',check=False)
    log=done.stdout+done.stderr;(OUT/'tests.log').write_text(log,encoding='utf-8')
    check('all eight new unit-test groups pass',done.returncode==0 and 'Ran 8 tests' in log and log.rstrip().endswith('OK'))
    check('new method takes public recording/cost inputs without hidden lifetimes',
          list(inspect.signature(later_pair).parameters)==['horizon','logger_failed','age_a','age_b','premiums'])
    evidence();paper()
    recovered=json.loads((OUT/'retrieval.json').read_text())
    for entry in recovered:
        if entry['pdf_recovered']:
            assert sha(entry['local_pdf'])==entry['sha256']
    check('all recovered primary PDF hashes match retrieval records',True)
    check('both Fox failures remain recorded as unresolved access',
          len([x for x in recovered if x['name'].startswith('fox') and not x['pdf_recovered']])==2)
    summary=json.loads((OUT/'run_summary.json').read_text())
    check('experiment summary does not invent historical priority',summary['historical_priority_established'] is False)
    check('908 prior artifacts unchanged after verification',protect()==908)
    record=dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),
        author={'name':'Nafis Wadud Ansari','affiliation':'Daffodil International University',
                'email':'ansari2305341800@diu.edu.bd','source':'Details supplied by user in this conversation'},
        verdict='B: potentially novel but insufficiently established',
        mathematical_result='Exact heterogeneous later-pair prefix theorem; continuous limit; sharp pairwise resolution factor',
        historical_originality_established=False,public_priority_established=False,
        public_destination=None,public_deposit=None,externally_peer_reviewed=False,
        release_rights='Unspecified; internal review draft',
        protected_artifacts_unchanged=908,previous_negative_results_preserved=True,
        claims_of_new_real_performance=False,statistical_test_used_to_prove_novelty=False,
        test_summary=summary,verification_check_count=len(CHECKS),
        environment={name:importlib.metadata.version(name) for name in ['numpy','pandas','reportlab','pypdf','pymupdf']},
        source_sha256={p.as_posix():sha(p) for p in Path('clock_regret_priority').glob('*.py')})
    (OUT/'research_record.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    verification=dict(passed=True,check_count=len(CHECKS),checks=CHECKS,protected_artifacts_unchanged=908,
                      historical_originality_established=False,public_priority_established=False)
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
    archive=bundle()
    paths=sorted(p for folder in [Path('clock_regret_priority'),OUT] for p in folder.rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts and p.name!='completion_manifest.json')
    manifest=dict(local_work_status='Complete theorem extension, attributed draft and review audit',
        novelty_verdict='B',historical_priority_established=False,public_destination_pending=True,
        protected_artifacts_unchanged=protect(),verified_check_count=len(CHECKS),review_bundle=archive,
        new_artifact_count=len(paths),sha256={p.as_posix():sha(p) for p in paths})
    (OUT/'completion_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    assert all(sha(p)==h for p,h in manifest['sha256'].items())
    print(json.dumps(dict(checks=len(CHECKS),all_passed=True,protected_artifacts_unchanged=908,
                         manuscript_pages=7,new_hashed_artifacts=len(paths),review_bundle=archive,
                         novelty_verdict='B',public_priority_established=False),indent=2),flush=True)


if __name__=='__main__':main()
