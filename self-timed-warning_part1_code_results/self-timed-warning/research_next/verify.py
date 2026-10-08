"""Verify new diagnostics and original preservation without resetting baselines."""
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import sklearn
sys.path.insert(0,str(Path(__file__).resolve().parent))
import calibration_tools as T
import cat as C

OUT=Path('out/research_next')
ENG=['PHM08','FD001','FD002','FD003','FD004','NCMAPSS6']


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def main():
    checks=[]
    def check(label,ok):
        checks.append(dict(check=label,pass_=bool(ok)))
        print(('PASS ' if ok else 'FAIL ')+label,flush=True)
    protected=json.loads((OUT/'protected_before.json').read_text())
    changed=[p for p,h in protected.items() if not Path(p).is_file() or digest(p)!=h]
    check('all 591 protected original files unchanged',len(protected)==591 and not changed)
    old=json.loads(Path('results/contrib/completion_audit.json').read_text())
    check('historical 262-check completion record retained',old['complete'] and len(old['checks'])==262 and all(x['pass'] for x in old['checks']))
    check('all 21 original inputs unchanged',len(old['input_sha256'])==21 and all(digest(p)==h for p,h in old['input_sha256'].items()))
    check('all 80 frozen completion artifacts unchanged',len(old['sha256'])==80 and all(digest(Path('results/contrib')/p)==h for p,h in old['sha256'].items()))
    src=pd.read_csv(OUT/'source_inventory.csv')
    check('168-file source inventory consistent',len(src)==168 and src.lines.sum()==16595 and all(digest(p)==h for p,h in zip(src.path,src.sha256)))
    check('90 Python AST inventories retained',len(json.loads((OUT/'source_symbols.json').read_text()))==90)
    outputs=pd.read_csv(OUT/'frozen_output_inventory.csv')
    check('284-artifact frozen inventory consistent',len(outputs)==284 and all(digest(p)==h for p,h in zip(outputs.path,outputs.sha256)))
    result=subprocess.run([sys.executable,'research_next/test_calibration_tools.py'],capture_output=True,text=True,timeout=30)
    log=result.stdout+result.stderr
    (OUT/'unit_tests.log').write_text(log,encoding='utf-8')
    check('all 11 reference unit-test groups pass',result.returncode==0 and 'Ran 11 tests' in log and 'OK' in log and 'FAILED' not in log)
    frozen=pd.read_csv('results/contrib/Battery_cost.csv',low_memory=False)
    total=0
    for name in ['cv1','cv2','cv3','cv4','cv5','lobo1','lobo2','lobo3']:
        z=np.load(OUT/'battery'/f'{name}_tables.npz')
        grid=np.arange(3.,181.,3.)
        cal=(z['cal_units'],z['cal_ok'],z['cal_ya'],z['cal_ta'],z['cal_L'])
        tab=(z['test_units'],z['test_ok'],z['test_ya'],z['test_ta'],z['test_L'])
        x=pd.read_csv(OUT/'battery'/f'{name}_scores.csv')
        ok=True;count=0
        for lead in [0,15,30,45]:
            scores=C.scores_from_table(cal,grid,lead)
            refscores=x[(x.lead==lead)&(x.role=='oof')].set_index('unit').loc[z['cal_units']].score.to_numpy()
            ok &= np.array_equal(scores,refscores)
            testscore=C.scores_from_table(tab,grid,lead)
            ok &= np.array_equal(testscore,x[(x.lead==lead)&(x.role=='test_refit')].set_index('unit').loc[z['test_units']].score.to_numpy())
            for alpha in [.01,.02,.05,.1]:
                th,finite=C.tau_hat(scores,alpha);j0=C.certified_column(grid,th,finite)
                for rho in [5,10,20,50]:
                    j1=C.cost_aware_column(cal,grid,j0,lead,rho,C.cost_1cycle)
                    costs,use=C.cost_1cycle(tab,lead,rho)
                    for pol,j in [(f'CAT_a{alpha}',j0),(f'CATc_a{alpha}',j1)]:
                        ref=frozen[(frozen.split==name)&(frozen.lead_cycles==lead)&(frozen.rho==rho)&(frozen.policy==pol)].set_index('unit').loc[z['test_units']]
                        ok &= np.array_equal(costs[:,j],ref.cost.to_numpy()) and np.allclose(use[:,j],ref.use.to_numpy(),rtol=0,atol=1e-10)
                        ok &= np.array_equal(testscore>grid[j],ref.fail.to_numpy())
                        count+=len(ref)
        msg=(OUT/'battery'/f'{name}_check.txt').read_text()
        recorded=int(re.search(r': (\d+) frozen',msg).group(1))
        check(f'{name}: frozen replay decisions and scores verified ({count})',ok and recorded==count)
        total+=count
    check('all 31488 battery decisions reproduced',total==31488)
    stress=pd.read_csv(OUT/'calibration_stress.csv.gz',low_memory=False)
    ids=['dataset','analysis','split','lead','dT']
    counts=stress.groupby(ids).size()
    check('complete 247680-row / 172-group stress grid',len(stress)==247680 and len(counts)==172 and (counts==1440).all())
    check('stress includes all seven cost domains and eight battery splits',set(stress.dataset)==set(ENG+['Battery']) and stress[stress.dataset=='Battery'].split.nunique()==8)
    check('stress seeds, calibration fractions and alpha grid complete',set(stress.seed)==set(range(2026,2036)) and set(stress.calibration_fraction)=={.25,.5,1.} and set(stress.alpha)=={.01,.02,.05,.1})
    check('stress risk equals saved unit failures',np.allclose(stress.risk,stress.failures/stress.n_test,rtol=0,atol=1e-14) and stress.risk.between(0,1).all())
    common=ids+['seed','calibration_fraction','noise_cycles','alpha']
    ordered=stress.sort_values(common+['target_score_shift'])
    check('larger synthetic critical-score shift never reduces failure',ordered.groupby(common).failures.diff().dropna().ge(0).all())
    base=stress[(stress.calibration_fraction==1)&(stress.noise_cycles==0)&(stress.target_score_shift==0)].copy()
    reproduced=True;nbaselines=0
    for ds in ENG+['Battery']:
        f=pd.read_csv(f'results/contrib/{ds}_cost.csv',low_memory=False)
        settings=pd.read_csv(f'results/contrib/{ds}_settings.csv')
        if ds!='Battery':
            f['split']=f.fold.astype(str)
            settings=settings[settings.dT==1].copy();settings['split']=settings.fold.astype(str)
        else:f['split']=f.split.astype(str)
        for _,r in base[(base.dataset==ds)&(base.dT==1)&(base.seed==2026)].iterrows():
            pol=f'CAT_a{r.alpha}'
            ref=f[(f.split==str(r.split))&(f.lead_cycles==r.lead)&(f.rho==10)&(f.policy==pol)]
            ss=settings[(settings.split.astype(str)==str(r.split))&(settings.lead_cycles==r.lead)&(settings.alpha==r.alpha)]
            if len(ss)!=1 or len(ref)!=r.n_test:reproduced=False;continue
            finite=bool(ss.cert_cf.iloc[0]);expected=float(ss.tau_cf.iloc[0]) if finite else (180. if ds=='Battery' else 60.)
            reproduced &= int(ref.fail.sum())==int(r.failures) and finite==bool(r.finite_threshold) and expected==r.threshold
            nbaselines+=1
    check(f'no-stress baselines match frozen CAT costs/settings ({nbaselines} cells)',reproduced and nbaselines==608)
    m_ok=True;m_count=0
    for ds in ['FD001','FD002','FD003','FD004']:
        f=pd.read_csv(f'results/contrib/{ds}_M.csv')
        for _,r in base[(base.dataset==ds)&(base.dT==10)&(base.seed==2026)].iterrows():
            ref=f[(f.split.astype(str)==str(r.split))&(f.q==.1)&(f.policy==f'CATg_a{r.alpha}')]
            m_ok &= len(ref)==r.n_test and int(ref.fail.sum())==int(r.failures)
            m_count+=1
    check(f'no-stress dT=10 baselines match frozen M failure decisions ({m_count} cells)',m_ok and m_count==80)
    target=pd.read_csv(OUT/'target_label_reference.csv')
    check('complete labelled-target reference grid',len(target)==1920 and set(target.split)=={'lobo1','lobo2','lobo3'} and set(target.budget)=={5,10,19,25} and set(target.seed)==set(range(2026,2036)))
    nmap={'lobo1':36,'lobo2':43,'lobo3':44}
    disjoint=True
    for r in target[['split','budget','seed']].drop_duplicates().itertuples(index=False):
        perm=np.random.default_rng(r.seed).permutation(nmap[r.split])
        disjoint &= not set(perm[:r.budget]) & set(perm[r.budget:])
    check('target reference uses disjoint calibration/remaining-unit partitions',disjoint and np.array_equal(target.n_test+target.budget,target.split.map(nmap)))
    check('small-label budgets explicitly marked nonfinite',(~target[target.budget<19].finite_threshold).all() and (target[target.budget<19].threshold==180).all())
    check('target cost/risk numerical results valid',target.target_risk.between(0,1).all() and target.source_risk.between(0,1).all() and (target[['source_cost_rate','target_cost_rate']]>0).all().all())
    cost=pd.read_csv(OUT/'cost_matrix_stress.csv')
    check('complete 640-cell fixed-policy cost grid',len(cost)==640 and set(cost.evaluation_rho)=={5,10,20,50,100} and (cost.selection_rho==10).all())
    paired=pd.read_csv(OUT/'lobo_paired_validation.csv')
    check('all 96 paired risk tests use full-family Holm',len(paired)==96 and np.allclose(T.holm(paired.p.to_numpy()),paired.p_holm,rtol=0,atol=1e-14) and not paired.reject_holm_05.any())
    check('paired conditional cost intervals contain estimates',((paired.cost_lo<=paired.cost_ratio)&(paired.cost_ratio<=paired.cost_hi)).all())
    effects=pd.read_csv(OUT/'all_dataset_effects.csv')
    check('all engine and both battery regimes reported',set(effects.dataset)==set(ENG+['Battery']) and set(effects[effects.dataset=='Battery'].analysis)=={'cv123','lobo'})
    report=Path('research_next/FINAL_SCIENTIFIC_REPORT.md').read_text(encoding='utf-8')
    statement=report.split('### 15. Contribution statement (exactly 150 words)')[1].split('### 16.')[0].strip()
    check('contribution statement exactly 150 whitespace-delimited words',len(statement.split())==150)
    check('all 16 pitch items present',len(re.findall(r'^### \d+\.',report,flags=re.M))==16)
    check('all ten phase statuses and negative novelty gate documented',all(f'| {i}:' in report for i in range(1,11)) and 'no defensible novel methodological contribution' in report.lower() and 'no eligible method' in report.lower())
    missing=[]
    link_text=re.sub(r'```.*?```','',report,flags=re.S)
    link_text=re.sub(r'^ {4}.*$','',link_text,flags=re.M)
    for label,url in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',link_text):
        if not url.startswith(('http://','https://')) and not (Path('research_next')/url).exists() and 'completion_manifest.json' not in url:missing.append(url)
    check('report local evidence links resolve',not missing)
    check('figure artifacts present',all((OUT/f'battery_diagnostics.{ext}').stat().st_size>10000 for ext in ['png','svg']))
    required=['PLAN.md','README.md','LITERATURE_AUDIT.md','MATHEMATICAL_STATUS.md','FINAL_SCIENTIFIC_REPORT.md','audit.py','reconstruct_battery.py','calibration_tools.py','stress.py','statistics_audit.py','build_report.py','verify.py','test_calibration_tools.py']
    check('all investigation deliverables exist',all((Path('research_next')/p).is_file() for p in required))
    # Recheck after tests and saved-score calculations, which import original modules.
    check('protected originals still unchanged after validation',all(digest(p)==h for p,h in protected.items()))
    hashed={p.as_posix():digest(p) for folder in ['research_next','out/research_next'] for p in sorted(Path(folder).rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.name!='completion_manifest.json'}
    manifest=dict(investigation_complete=all(c['pass_'] for c in checks),
        new_method_implemented=False,new_method_validated=False,novel_method_established=False,
        novelty_gate='not_passed; user-authorized negative-novelty fallback completed',
        historical_completion={'checks':262,'preserved_files':591,'input_files':21,'frozen_artifacts':80},
        diagnostic_counts={'battery_replay_decisions':total,'stress_rows':len(stress),'stress_groups':len(counts),'target_reference_rows':len(target),'cost_matrix_cells':len(cost),'paired_risk_tests':len(paired),'new_unit_test_groups':11},
        scope_limits=['no new optimizer','no new-method removal ablations','fixed-signal score stress only','no independent retraining seed study','no training-class prevalence intervention','no verified chronological stream','no operational delayed/censored-feedback experiment','no exact frozen deployment guarantee'],
        checks=[{'check':c['check'],'pass':c['pass_']} for c in checks],changed_protected_files=changed,
        environment={'python':platform.python_version(),'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'scikit_learn':sklearn.__version__,'threads':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}},
        checked_at_utc=datetime.now(timezone.utc).isoformat(),client_report_date='2026-10-08 Asia/Dhaka',
        investigation_plan_sha256=digest('research_next/PLAN.md'),original_completion_sha256=digest('results/contrib/completion_audit.json'),sha256=hashed)
    (OUT/'completion_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f"{'PASS' if manifest['investigation_complete'] else 'FAIL'} {sum(c['pass_'] for c in checks)}/{len(checks)} investigation checks; novelty gate not passed.")
    if not manifest['investigation_complete']:raise SystemExit(1)


if __name__=='__main__':main()
