"""Frozen-integrity, protocol, outcome and statistical-family audit."""
import hashlib,json,platform,re,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import core as R
from real import load_groups
from synthetic import cohort,rates,evaluate
OUT=Path('out/rampe');checks=[]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def check(name,condition,detail=None):
    checks.append(dict(name=name,passed=bool(condition),detail=detail))
    if not condition:raise AssertionError(name)
def read(name):return pd.read_csv(OUT/name,low_memory=False)
def adjusted_holm(p):
    order=np.argsort(p);out=np.empty(len(p));last=0.
    for rank,idx in enumerate(order):last=max(last,min(1.,p[idx]*(len(p)-rank)));out[idx]=last
    return out

def main():
    frozen=json.loads((OUT/'frozen_before.json').read_text())
    changed=[p for p,h in frozen.items() if not Path(p).is_file() or sha(p)!=h]
    check('All 681 frozen sources/results/inputs unchanged',len(frozen)==681 and not changed,changed)
    check('Saved pre-experiment plan hash unchanged',sha('rampe/PLAN.md')==(OUT/'plan_sha256.txt').read_text().strip())
    old=json.loads(Path('out/research_next/completion_manifest.json').read_text())
    check('Previous investigation completion manifest preserved',old['investigation_complete'] and old['historical_completion']['checks']==262)
    check('All39 prior investigation checks retained',len(old['checks'])==39 and all(c['pass'] for c in old['checks']))
    bridge=json.loads((OUT/'legacy_stress_bridge.json').read_text());legacy=Path('out/research_next/calibration_stress.csv.gz')
    check('247680 old stress rows independently counted and hashed',len(pd.read_csv(legacy,low_memory=False))==247680==bridge['rows'] and sha(legacy)==bridge['sha256'])
    tests=subprocess.run([sys.executable,'rampe/test_core.py'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
    (OUT/'unit_tests.log').write_text(tests.stdout,encoding='utf-8')
    check('19 unit-test groups pass',tests.returncode==0 and 'Ran 19 tests' in tests.stdout)
    real=read('real_results.csv.gz');p=read('paired_units.csv.gz');parts=read('partitions.csv.gz');s=read('synthetic_results.csv.gz');v=read('validation_stress.csv.gz');fixed=read('fixed_rule_shift.csv.gz');tm=read('temporal_reference.csv.gz')
    check('Real grid is 6080 episodes x20 methods',len(real)==121600 and real.case.nunique()==6080 and (real.groupby('case').method.nunique()==20).all())
    check('Real episodes unique method/case',not real.duplicated(['case','method']).any())
    check('Six engines and both battery regimes represented',len(real[['dataset','analysis']].drop_duplicates())==8 and real.dataset.nunique()==7)
    check('Every real episode has exactly one seed/lead/cost/split identity',all((real.groupby('case')[c].nunique()==1).all() for c in ['seed','lead','rho','dataset','analysis','split']))
    check('Ten selection seeds, four leads and four cost asymmetries per regime',all(g.seed.nunique()==10 and g.lead.nunique()==4 and g.rho.nunique()==4 for _,g in real.groupby(['dataset','analysis'])))
    check('Every validation/test partition contains each unit once',not parts.duplicated(['case','unit']).any() and set(parts.role)=={'validation','test'})
    check('Meta-validation counts agree with saved partitions',np.array_equal(parts[parts.role=='validation'].groupby('case').size().sort_index(),real[real.method=='RAMPE'].set_index('case').n_validation.sort_index()))
    pt=parts[parts.role=='test'];joined=pt[['case','unit']].merge(p[['case','unit']],on=['case','unit'],how='outer',indicator=True,validate='one_to_one')
    check('Paired outcomes contain exactly the disjoint test units',(joined['_merge']=='both').all())
    check('Validation total sample size is 9 to26',real.n_validation.min()==9 and real.n_validation.max()==26)
    ram=real[real.method=='RAMPE'].set_index('case').sort_index();one=real[real.method=='1SE'].set_index('case').sort_index()
    check('All real RAMPE episodes abstain',(ram.abstention==1).all())
    check('RAMPE baseline outcome metrics identical',all(np.array_equal(ram[c],one[c]) for c in ['cost_rate','mean_cost','median_cost','max_cost','cost_variance','failures','risk','authority_changes']))
    check('RAMPE always gives authority to1SE',(ram.authority_1SE==1).all())
    check('Paired unit actions,costs,lives,failures identical to1SE',all(np.array_equal(p['RAMPE_'+c],p['1SE_'+c]) for c in ['policy','cost','use','fail']))
    # Aggregate recorded unit outcomes independently of summary generation.
    for method in ['RAMPE','1SE','conventional','CATc']:
        sums=p.groupby('case')[[method+'_cost',method+'_use',method+'_fail']].sum().sort_index();sizes=p.groupby('case').size().sort_index()
        r=real[real.method==method].set_index('case').sort_index()
        check(f'{method} recorded rates/failures equal paired-unit sums',np.allclose(sums[method+'_cost']/sums[method+'_use'],r.cost_rate,rtol=1e-12) and np.array_equal(sums[method+'_fail'],r.failures) and np.array_equal(sizes,r.n))
    ctx=read('causal_context.csv');check('Causal context inventory unique,1166 rows',len(ctx)==1166 and not ctx.duplicated(['dataset','unit']).any())
    context=ctx.assign(unit=ctx.unit.astype(str),context=ctx.context.astype(str));z=p.assign(unit=p.unit.astype(str),context=p.context.astype(str)).merge(context[['dataset','unit','context']],on=['dataset','unit'],suffixes=('_paired','_causal'),validate='many_to_one')
    check('Every paired query uses its pre-extracted causal context',len(z)==len(p) and (z.context_paired==z.context_causal).all())
    # Check frozen accounting and candidate baseline alignment on all settings.
    grouped=p.groupby(['dataset','analysis','split','lead','rho'],dropna=False);reference=real[real.method.isin(['plain','CAT','CATc','1SE'])].set_index(['case','method'])
    baseline_ok=True;unit_count={};outer=set()
    for info,units,context,strata,c,t,f in load_groups():
        outer.add((info['dataset'],info['analysis'],info['split']));unit_count.setdefault((info['dataset'],info['analysis']),set()).update(units)
        key=(info['dataset'],info['analysis'],info['split'],info['lead'],info['rho'])
        # Pandas may represent engine split as a string in mixed-domain table.
        g=p[(p.dataset==info['dataset'])&(p.analysis==info['analysis'])&(p.split.astype(str)==str(info['split']))&(p.lead==info['lead'])&(p.rho==info['rho'])]
        for seed in range(2026,2036):
            gg=g[g.seed==seed];perm=np.random.default_rng(seed).permutation(len(units));te=np.sort(perm[len(units)//2:]);case=int(gg.case.iloc[0])
            baseline_ok &= set(gg.unit.astype(str))==set(units[te])
            for j,method in enumerate(['plain','CAT','CATc','1SE']):
                rr=reference.loc[(case,method)];cc=c[te,j];tt=t[te,j];ff=f[te,j]
                baseline_ok &= np.isclose(rr.cost_rate,cc.sum()/tt.sum(),rtol=1e-12) and rr.failures==ff.sum()
    check('All four frozen baselines align across all6080 partitions',baseline_ok)
    check('38 outer groups;1026 engines;123 battery cells per regime',len(outer)==38 and sum(len(q) for (ds,an),q in unit_count.items() if ds!='Battery')==1026 and len(unit_count[('Battery','cv123')])==123 and len(unit_count[('Battery','lobo')])==123)
    models=json.loads((OUT/'learned_models.json').read_text());check('Learned model leaves entire dataset out',len(models)==7 and all(m['heldout_dataset'] not in m['training_domains'].split('|') and len(m['training_domains'].split('|'))==6 for m in models))
    lpred=read('learned_predictions.csv.gz');meta=read('meta_features.csv.gz');check('Learned probabilities aligned with fixed meta-features',len(lpred)==len(meta) and not lpred.duplicated(['case','context','policy']).any() and lpred.p_accept.between(0,1).all())
    lp=read('learned_units.csv.gz');check('Learned unit outcomes align one-to-one without dropped numeric engine ids',len(lp)==len(p) and len(lp.merge(p[['case','unit']],on=['case','unit'],validate='one_to_one'))==len(p))
    check('Synthetic8700 episodes x18 methods',len(s)==156600 and s.case.nunique()==8700 and (s.groupby('case').method.nunique()==18).all())
    grid=s[(s.attack=='none')&(s.method=='RAMPE')];keys=['n_validation','rho','noise','life_variance','source_regime_prevalence','shift']
    check('Synthetic288 conditions each30 independent seed cohorts',grid.groupby(keys).ngroups==288 and (grid.groupby(keys).seed.nunique()==30).all() and set(grid.n_validation)=={32,128,512,2048})
    check('Synthetic n=1000 target units per episode',(s.n==1000).all())
    check('No duplicate synthetic method/case',not s.duplicated(['case','method']).any())
    attacks=s[(s.method=='RAMPE')&(s.attack!='none')]
    check('Unseen regime always abstains to safe B',(attacks[attacks.attack=='unseen_regime'].abstention==1).all() and (attacks[attacks.attack=='unseen_regime'].population_risk==0).all())
    check('All-fail attack exposes fallback failure and infeasible oracle',(attacks[attacks.attack=='known_all_fail'].population_risk==1).all() and attacks[attacks.attack=='known_all_fail'].reliable_oracle_rate.isna().all())
    large=grid[(grid.n_validation==2048)&(grid['shift']==1)]
    check('Large-source hidden shift exceeds .05 mean failure risk',large.population_risk.mean()>.05)
    check('Matched large-source rate improves vs B only in simulator',grid[(grid.n_validation==2048)&(grid['shift']==0)].population_rate.mean()<1/6)
    # Value reproduction for one matched and one hidden-shift case; regenerate
    # source/test from stored parameters, not output summary means.
    for shift in [0.,1.]:
        target=grid[(grid.n_validation==512)&(grid.rho==50)&(grid.noise==1)&(grid.life_variance==.6)&(grid.source_regime_prevalence==.5)&(grid['shift']==shift)&(grid.seed==2026)].iloc[0]
        vc,vt,vf=cohort(512,.5,.6,2026,1);cost=1+49*vf.astype(float);eps=np.random.default_rng(np.random.SeedSequence([2026,3])).normal(size=cost.shape);obs=np.maximum(.01,cost+eps)
        glob=R.evidence(obs,vt,vf,vc,0,seed=2026,strata=3,pooled=True);ev={g:R.evidence(obs,vt,vf,vc,g,seed=2026,strata=3) for g in [0,1]}
        tc,tt,tf=cohort(1000,.5,.6,2026,2,shift);u=np.random.default_rng(np.random.SeedSequence([2026,4])).random(1000);pp=rates(np.array([0,1]),shift);prob=np.array([1-(.5+.3*shift),.5+.3*shift])
        result=pd.DataFrame(evaluate(ev,glob,tc,1+49*tf.astype(float),tt,tf,u,dict(seed=2026),1+49*pp,np.array([[10,6,10],[10,6,9]]),pp,prob)).set_index('method').sort_index();stored=s[s.case==target.case].set_index('method').sort_index()
        check(f'Synthetic all-method value replay shift{shift}',all(np.allclose(result[m],stored[m],rtol=1e-12,atol=1e-12,equal_nan=True) for m in ['cost_rate','risk','abstention','population_rate','population_risk','reliable_oracle_rate']))
    check('Validation/support stress complete329080 rows',len(v)==329080 and len(v[~v.method.str.endswith('_support_attack')])==328320 and len(v[v.method.str.endswith('_support_attack')])==760)
    check('Stress validation noise/fractions retain full settings',set(v.fraction)=={.25,.5,1.} and set(v.accounting_noise_sd)=={0.,.1,1.})
    check('RAMPE remains fallback under validation stress',(v[v.method=='RAMPE'].abstention==1).all())
    check('Fixed-rule shift45600 rows with frozen selection economics',len(fixed)==45600 and (fixed.selection_lead==0).all() and (fixed.selection_rho==10).all() and set(fixed.evaluation_rho)=={5,10,20,50,100})
    fbase=fixed[fixed.method=='1SE'].set_index(['dataset','analysis','split','seed','evaluation_lead','evaluation_rho']).sort_index();fram=fixed[fixed.method=='RAMPE'].set_index(['dataset','analysis','split','seed','evaluation_lead','evaluation_rho']).sort_index()
    check('RAMPE and fallback remain identical under lead/cost shifts',np.allclose(fbase.cost_rate,fram.cost_rate) and np.array_equal(fbase.failures,fram.failures))
    monotone=fixed[fixed.method=='RAMPE'].sort_values('evaluation_lead').groupby(['dataset','analysis','split','seed','evaluation_rho']).failures.apply(lambda x:(np.diff(x)>=0).all()).all()
    check('Fixed-rule failures monotone in required lead',monotone)
    # Failure labels do not change with cost asymmetry; mean cost is 1+(rho-1)risk.
    check('Shifted economic accounting exact',np.allclose(fixed.mean_cost,1+(fixed.evaluation_rho-1)*fixed.risk,rtol=1e-12))
    check('Temporal30 seeds x8 blocks x2 feedback regimes x18 methods',len(tm)==8640 and tm.seed.nunique()==30 and tm.block.nunique()==8 and not tm.duplicated(['seed','block','feedback','method']).any())
    t0=tm[tm.block==0].pivot(index=['seed','method'],columns='feedback',values='cost_rate')
    check('Temporal block0 equal before any new feedback',np.array_equal(t0.iloc[:,0],t0.iloc[:,1]))
    rolled=tm[(tm.method=='RAMPE')&(tm.feedback=='rolling_full_information')&(tm.block>=5)];static=tm[(tm.method=='RAMPE')&(tm.feedback=='static_source')&(tm.block>=6)]
    check('Temporal reference adapts with complete outcomes only',(rolled.population_risk==0).all() and static.population_risk.mean()>.05)
    source=Path('rampe/temporal.py').read_text(encoding='utf-8');check('Feedback append occurs after evaluation in temporal source',source.index('rows.extend(evaluate')<source.index('history_ctx=np.concatenate'))
    ci=read('real_conditional_intervals.csv');lobo=ci[(ci.dataset=='Battery')&(ci.analysis=='lobo')];q=read('synthetic_paired_tests.csv');scope=json.loads((OUT/'statistical_scope.json').read_text())
    check('Inference families768 real,96 LOBO,580 synthetic',len(ci)==768 and len(lobo)==96 and len(q)==580 and scope['conditional_real_comparisons']==768 and scope['lobo_holm_family']==96 and scope['synthetic_comparisons']==580)
    check('Holm values independently recomputed',np.allclose(q.sign_p_holm,adjusted_holm(q.sign_p.to_numpy())) and np.allclose(lobo.paired_binary_p_holm,adjusted_holm(lobo.paired_binary_p.to_numpy())))
    identical=ci[(ci.method=='RAMPE')&(ci.baseline=='1SE')]
    check('All128 RAMPE-vs1SE conditional differences and intervals zero',len(identical)==128 and np.allclose(identical[['cost_difference','conditional_bootstrap_low','conditional_bootstrap_high']],0))
    report=Path('rampe/FINAL_REPORT.md').read_text(encoding='utf-8');lit=Path('rampe/LITERATURE_AUDIT.md').read_text(encoding='utf-8')
    check('All20 requested report sections present once',len(re.findall(r'^## SECTION \d+',report,re.M))==20 and all(f'## SECTION {i} —' in report for i in range(1,21)))
    check('Final report explicit D and NO', '**D. NOT A CONTRIBUTION.' in report and 'research? NO.' in report)
    check('Primary literature includes closest reproducing mechanisms',all(x in lit for x in ['META-DES','Arbitrated Dynamic Ensemble with Abstaining','Learning to Defer to Multiple Experts','Learning to Control Renewal Processes','Meta-Scheduling','Strict novelty gate']))
    links=re.findall(r'\]\(([^)]+)\)',report);missing=[x for x in links if not x.startswith('https:') and not (Path('rampe')/x).exists() and x not in ['../out/rampe/verification.json','../out/rampe/run_manifest.json']]
    check('Report local links resolve',not missing,missing)
    check('Both scientific figures exported PNG/SVG',all((OUT/f).is_file() and (OUT/f).stat().st_size>1000 for f in ['main_results.png','main_results.svg','temporal_reference.png','temporal_reference.svg']))
    result=dict(passed=True,checks=len(checks),unit_test_groups=19,protected_files=len(frozen),changed_files=changed,verdict='D. NOT A CONTRIBUTION',genuinely_new_scientific_contribution=False,items=checks)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    import scipy,sklearn,matplotlib
    # The redirect log can still be open while this process prints its final
    # message, so it is intentionally outside the artifact hash snapshot.
    artifacts=[p for root in [Path('rampe'),OUT] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['run_manifest.json','verification_failure.json','verification_run.log']]
    manifest=dict(complete=True,verdict='D. NOT A CONTRIBUTION',genuinely_new_contribution=False,checks=len(checks),unit_test_groups=19,protected_unchanged_files=len(frozen),counts={**scope,'validation_stress_method_rows':len(v),'fixed_rule_shift_method_rows':len(fixed),'temporal_reference_method_rows':len(tm),'old_stress_rows_preserved':247680,'original_battery_decisions_preserved':31488},scope=dict(new_predictors_fitted=False,rl_implemented=False,temporal_feedback='synthetic full-information completed counterfactual outcomes',real_protocol='retrospective additional labelled meta-validation among frozen policies',zero_label_transfer=False,complete_RAMPE_safety_guarantee=False),runtime=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,matplotlib=matplotlib.__version__),sha256={p.as_posix():sha(p) for p in sorted(artifacts)})
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(f'PASS {len(checks)}/{len(checks)} checks;19 unit tests;{len(frozen)} frozen files unchanged;verdict D/NO.')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        (OUT/'verification_failure.json').write_text(json.dumps(dict(error=repr(exc),checks=checks),indent=2),encoding='utf-8');raise
