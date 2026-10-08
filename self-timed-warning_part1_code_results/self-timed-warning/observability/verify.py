import hashlib,json,re,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path.cwd()))
from observability.core import identify
OUT=Path('out/observability');checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,ok):
    checks.append(dict(name=name,passed=bool(ok)))
    if not ok:raise AssertionError(name)
def read(name):return pd.read_csv(OUT/name,low_memory=False)

def main():
    protected=json.loads((OUT/'protected_before.json').read_text());changed=[p for p,h in protected.items() if not Path(p).is_file() or sha(p)!=h]
    check('Every original and RAMPE artifact remains byte-identical',not changed)
    check('Pre-run pivot plan hash retained',sha('observability/PLAN.md')==(OUT/'plan_sha256.txt').read_text().strip())
    old=json.loads(Path('out/rampe/run_manifest.json').read_text());check('Completed59-check RAMPE verdict D unchanged',old['checks']==59 and old['verdict']=='D. NOT A CONTRIBUTION')
    test=subprocess.run([sys.executable,'observability/test_core.py'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8');(OUT/'unit_tests.log').write_text(test.stdout,encoding='utf-8')
    check('13 mathematical/leakage/witness unit tests pass',test.returncode==0 and 'Ran 13 tests' in test.stdout)
    p=read('public_outcomes.csv.gz');truth=read('sealed_truth.csv.gz');x=read('task_results.csv.gz');b=read('information_budget.csv.gz')
    check('9728 tasks325632 unit pairs and29184 cap evaluations',p.task.nunique()==9728 and len(p)==325632 and len(truth)==325632 and len(x)==29184)
    check('486400 information-release evaluations',len(b)==486400 and b.seed.nunique()==10 and set(b.release_fraction)=={0.,.1,.25,.5,1.})
    check('Public and truth task/unit keys unique',not p.duplicated(['task','unit']).any() and not truth.duplicated(['task','unit']).any())
    z=p.merge(truth,on=['task','unit','dataset','analysis','split','lead','rho','logger','target'],validate='one_to_one')
    check('Public and sealed truth align one-to-one',len(z)==len(p))
    obs=z.outcome_observed.astype(bool)
    check('Visibility contract matches logger endpoint/completion',np.array_equal(obs,z.logger_fail.astype(bool)|(z.true_target_use<=z.logger_endpoint+1e-10)))
    check('Every unresolved target field is absent',z.loc[~obs,['target_cost','target_use','target_fail']].isna().all().all())
    check('Observable values exactly reproduce original outcomes',all(np.array_equal(z.loc[obs,a],z.loc[obs,c]) for a,c in [('target_cost','true_target_cost'),('target_use','true_target_use'),('target_fail','true_target_fail')]))
    check('Public schema contains no future RUL/lifetime/true target fields',not any('rul' in c.lower() or c.startswith('true_') or c in ['life','lifetime'] for c in p.columns))
    check('Declared caps exceed every sampled completion',z.true_target_use.max()<2000 and z.logger_endpoint.max()<2000)
    check('All truth rates contained by all rate intervals',((x.true_target_rate>=x.rate_low-1e-12)&(x.true_target_rate<=x.rate_high+1e-12)).all())
    check('All truth risks contained by all risk intervals',((x.true_target_risk>=x.risk_low-1e-12)&(x.true_target_risk<=x.risk_high+1e-12)).all())
    check('No false interval economic or risk declarations',not (x.certified_improvement&(x.true_target_rate>=x.logger_rate-1e-12)).any() and not (x.certified_safe&(x.true_target_risk>.05)).any())
    check('Self-policy pairs fully observable and point-identified',(x[x.logger==x.target].observed_fraction==1).all() and np.allclose(x[x.logger==x.target].rate_low,x[x.logger==x.target].rate_high))
    check('All eight original evaluation regimes included',x[['dataset','analysis']].drop_duplicates().shape[0]==8)
    check('All sixteen logger-target pairs included',x[['logger','target']].drop_duplicates().shape[0]==16)
    check('All settings have four leads/four cost asymmetries per regime',all(g.lead.nunique()==4 and g.rho.nunique()==4 for _,g in x.groupby(['dataset','analysis'])))
    check('No duplicate cap/task or release/task/seed results',not x.duplicated(['task','cap']).any() and not b.duplicated(['task','seed','release_fraction']).any())
    # Recompute intervals solely from public views; no hidden evaluator label is
    # passed to identify. All tasks are checked, not just illustrative positives.
    saved=x[x.cap==5000].set_index('task');ok=True
    for task,g in p.groupby('task'):
        iv=identify(g.logger_endpoint,g.outcome_observed.astype(bool),g.target_cost,g.target_use,g.target_fail,float(g.rho.iloc[0]),5000.)
        row=saved.loc[task];ok &= np.allclose([iv.rate_low,iv.rate_high,iv.risk_low,iv.risk_high],row[['rate_low','rate_high','risk_low','risk_high']].to_numpy(dtype=float),rtol=1e-12,atol=1e-12)
    check('All9728 intervals independently reproduced using only public data',ok)
    pivot=x.pivot(index='task',columns='cap',values='rate_high');check('Cap sensitivity leaves all upper rate endpoints unchanged',np.allclose(pivot[2000],pivot[5000]) and np.allclose(pivot[5000],pivot[10000]))
    p_low=x.pivot(index='task',columns='cap',values='rate_low');check('Lower rates monotonically decrease when caps relax',((p_low[2000]>=p_low[5000]-1e-12)&(p_low[5000]>=p_low[10000]-1e-12)).all())
    ordered=b.sort_values(['task','seed','release_fraction']);nested=True
    for col,direction in [('rate_low',1),('rate_high',-1),('risk_low',1),('risk_high',-1)]:
        delta=ordered.groupby(['task','seed'])[col].diff().dropna();nested &= (direction*delta>=-1e-12).all()
    check('All97280 release paths have nested intervals',nested and ordered.groupby(['task','seed']).ngroups==97280)
    full=b[b.release_fraction==1];check('Full reveal collapses to exact cohort truths',np.allclose(full.rate_low,full.true_target_rate) and np.allclose(full.rate_high,full.true_target_rate) and np.allclose(full.risk_low,full.true_target_risk) and np.allclose(full.risk_high,full.true_target_risk))
    zero=b[b.release_fraction==0].merge(saved[['rate_low','rate_high']],on='task',suffixes=('_release','_initial'))
    check('Zero-budget release repeats initial identification',np.allclose(zero.rate_low_release,zero.rate_low_initial) and np.allclose(zero.rate_high_release,zero.rate_high_initial))
    report=Path('observability/REPORT.md').read_text(encoding='utf-8');check('Report discloses candidate B and no established novel method','B — POTENTIALLY NOVEL BUT INSUFFICIENTLY ESTABLISHED' in report and 'not an established novel learning algorithm' in report)
    check('Report retains physical/causal/sensor scope limitations',all(term in report for term in ['not a safe physical inspection','pending alarms','not evidence of future deployment safety','continuous-time']))
    findings=json.loads((OUT/'findings.json').read_text());diag=x[(x.cap==5000)&(x.logger!=x.target)];check('Reported7296 distinct-policy tasks and false claims match output',findings['offdiagonal_tasks']==len(diag)==7296 and findings['healthy_false_safe']==int(diag.healthy_false_safe.sum())==418 and findings['certified_improvements']==int(diag.certified_improvement.sum())==1028)
    check('Report source/output links resolve',all((Path('observability')/link).exists() or link=='../out/observability/verification.json' for link in re.findall(r'\]\(([^)]+)\)',report) if not link.startswith('https:')))
    result=dict(passed=True,checks=len(checks),unit_tests=13,protected_files=len(protected),changed_files=changed,novelty='B: candidate benchmark/empirical contribution; methodological novelty not established',items=checks)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    files=[p for root in [Path('observability'),OUT] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='completion_manifest.json']
    manifest=dict(artifact_complete=True,novelty_established=False,contribution_kind='candidate paired benchmark and empirical study',checks=len(checks),unit_tests=13,protected_files_unchanged=len(protected),scope='finite-cohort, coarsened outcome-summary replay; no population or physical intervention guarantee',counts=dict(policy_pair_tasks=9728,public_unit_pairs=325632,cap_evaluations=29184,information_budget_evaluations=486400),sha256={p.as_posix():sha(p) for p in sorted(files)})
    (OUT/'completion_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(f'PASS {len(checks)} checks;13 tests;{len(protected)} protected files unchanged;candidate B.')

if __name__=='__main__':main()
