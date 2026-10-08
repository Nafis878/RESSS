"""Freeze a review bundle after observed visual review and completed checks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from clock_regret_attention.run import OUT,protect,sha


def main():
    assert protect()==1025
    qa=json.loads((OUT/'pdf-qa.json').read_text())
    assert qa['pages']==8 and qa['text_bounds_pass']
    qa['visual_review']='All eight final rendered pages visually inspected: clear margins, tables, formulas, plots and footers; no clipping or overlap.'
    (OUT/'pdf-qa.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
    checks=json.loads((OUT/'final-checks.json').read_text())
    assert all(v['exit_code']==0 for k,v in checks.items() if isinstance(v,dict))
    sources=sorted(p for p in Path('clock_regret_attention').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    helpers=[Path(p) for p in ['clock_regret/core.py','clock_regret/oracles.py',
        'clock_regret_priority/heterogeneous.py','clock_regret_fleet/core.py','clock_regret_fleet/oracles.py']]
    evidence=sorted(p for p in OUT.rglob('*') if p.is_file() and 'qa' not in p.parts
        and p.name not in ['review_bundle.zip','completion_manifest.json','archive-tests.log'])
    members=sources+helpers+evidence
    bundle=OUT/'review_bundle.zip'
    member_hashes={p.as_posix():sha(p) for p in members}
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
        for p in members:z.write(p,p.as_posix())
        z.writestr('BUNDLE_HASHES.json',json.dumps(member_hashes,indent=2))
    # The extraction and implicit cleanup both stay inside this named workspace.
    workspace=Path.cwd().resolve();base=workspace/'tmp'/'attention-review';base.mkdir(parents=True,exist_ok=True)
    assert base.resolve().is_relative_to(workspace)
    with tempfile.TemporaryDirectory(prefix='bundle-',dir=base) as folder:
        target=Path(folder).resolve();assert target.is_relative_to(base.resolve())
        with zipfile.ZipFile(bundle) as z:
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
            z.extractall(target)
        for name,digest in member_hashes.items():assert sha(target/name)==digest
        env=dict(os.environ);env['PYTHONPATH']='';env['OMP_NUM_THREADS']='1';env['PYTHONUTF8']='1'
        result=subprocess.run([sys.executable,'-m','unittest','clock_regret_attention.test_core',
            'clock_regret_attention.test_integration','-v'],cwd=target,env=env,capture_output=True,text=True,encoding='utf-8')
        (OUT/'archive-tests.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        assert result.returncode==0,(result.stdout,result.stderr)
    assert protect()==1025
    outputs=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='completion_manifest.json')
    new_files=sources+outputs
    manifest=dict(stage='attention and complete failure ablations',date='2026-10-08',
        author=dict(name='Nafis Wadud Ansari',affiliation='Daffodil International University',email='ansari2305341800@diu.edu.bd'),
        verdict='B: potentially novel but insufficiently established',historical_originality_established=False,
        scientific_priority_established=False,attention_superiority_over_greedy_established=False,
        validation_selected_proposal='sequential_greedy',
        final_method='shared-clock heterogeneous regret + greedy and premium focused certificates + complete-family FPTAS intersection',
        unit_test_groups=9,archive_unit_test_exit_code=0,archive_members_verified=len(member_hashes),
        original_artifacts_unchanged=1025,generated_learning_and_holdout_cohorts=3000,
        final_pdf_pages=8,visual_review_passed=True,
        evidence_verifiers=json.loads((OUT/'verification.json').read_text())|json.loads((OUT/'followup-verification.json').read_text()),
        frozen_hashes={p.as_posix():sha(p) for p in new_files})
    (OUT/'completion_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(dict(new_artifacts_frozen=len(manifest['frozen_hashes']),archive_members_verified=len(member_hashes),
        archive_tests_exit_code=result.returncode,old_artifacts_unchanged=1025,pdf_pages=8,novelty_verdict=manifest['verdict']),indent=2))


if __name__=='__main__':main()
