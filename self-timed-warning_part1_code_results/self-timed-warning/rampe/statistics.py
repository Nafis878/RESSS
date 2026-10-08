"""Descriptive repeated-partition statistics and explicitly conditional inference."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import binomtest,t as student
OUT=Path('out/rampe')
_read_csv=pd.read_csv
def read_csv(*args,**kwargs):
    kwargs.setdefault('low_memory',False)
    return _read_csv(*args,**kwargs)
pd.read_csv=read_csv

def holm(p):
    p=np.asarray(p,float);ix=np.argsort(p);z=np.minimum(1,np.maximum.accumulate(p[ix]*(len(p)-np.arange(len(p)))))
    ans=np.empty(len(p));ans[ix]=z;return ans

def summary(x,keys,metrics,name):
    available=[m for m in metrics if m in x]
    g=x.groupby(keys,dropna=False)[available].agg(['mean','std','median','min','max'])
    g.columns=['_'.join(c) for c in g.columns];g.reset_index().to_csv(OUT/name,index=False)

def main():
    real=pd.read_csv(OUT/'real_results.csv.gz');syn=pd.read_csv(OUT/'synthetic_results.csv.gz')
    metrics=['cost_rate','mean_cost','median_cost','max_cost','cost_variance','risk','abstention','authority_changes','calibration_gap','selected_entropy','avoided_failures','introduced_failures','false_abstentions','abstention_cost_difference','abstention_use_difference']
    summary(real,['dataset','analysis','method'],metrics,'real_summary.csv')
    summary(real,['dataset','analysis','lead','rho','method'],metrics,'real_setting_summary.csv')
    summary(syn,['attack','n_validation','shift','method'],metrics+['population_rate','population_risk','population_context_feasible','oracle_disagreement','excess_cost_vs_reliable_oracle','validation_best_uncertainty'],'synthetic_summary.csv')
    pairs=[]
    for baseline in ['1SE','conventional']:
        b=real[real.method==baseline].set_index('case')
        for (ds,an,method),g in real.groupby(['dataset','analysis','method']):
            d=g.cost_rate.to_numpy()-b.loc[g.case].cost_rate.to_numpy()
            risk=g.risk.to_numpy()-b.loc[g.case].risk.to_numpy()
            pairs.append(dict(dataset=ds,analysis=an,method=method,baseline=baseline,cases=len(d),mean_difference=d.mean(),sd_difference=d.std(ddof=1),median_difference=np.median(d),relative_mean_difference=d.mean()/b.loc[g.case].cost_rate.mean(),wins=int((d<-1e-12).sum()),ties=int((abs(d)<=1e-12).sum()),losses=int((d>1e-12).sum()),risk_difference=risk.mean()))
    pd.DataFrame(pairs).to_csv(OUT/'real_paired_descriptive.csv',index=False)
    # One partition seed only. Unit bootstrap conditions on frozen fitted rules and
    # selected authorities; it does not measure retraining/selection uncertainty.
    p=pd.read_csv(OUT/'paired_units.csv.gz');lp=pd.read_csv(OUT/'learned_units.csv.gz')
    assert len(p)==len(lp)
    n_paired=len(p);p=p.merge(lp,on=['case','unit'],validate='one_to_one');assert len(p)==n_paired
    p=p[p.seed==2026]
    rng=np.random.default_rng(2027);rows=[]
    for (ds,an,lead,rho),g in p.groupby(['dataset','analysis','lead','rho']):
        # Reuse the same resampled units for every paired comparison.
        idx=rng.integers(0,len(g),size=(2000,len(g)))
        for method in ['RAMPE','learned']:
            c=g[method+'_cost'].to_numpy();u=g[method+'_use'].to_numpy();f=g[method+'_fail'].to_numpy()
            for base in ['1SE','conventional','CATc']:
                cb=g[base+'_cost'].to_numpy();ub=g[base+'_use'].to_numpy();fb=g[base+'_fail'].to_numpy()
                diff=c.sum()/u.sum()-cb.sum()/ub.sum()
                boot=c[idx].sum(1)/u[idx].sum(1)-cb[idx].sum(1)/ub[idx].sum(1)
                win=int(((f==0)&(fb==1)).sum());loss=int(((f==1)&(fb==0)).sum())
                pv=binomtest(win,win+loss,.5).pvalue if win+loss else 1.
                lo,hi=np.quantile(boot,[.025,.975]);rows.append(dict(dataset=ds,analysis=an,lead=lead,rho=rho,method=method,baseline=base,n_units=len(g),cost_difference=diff,relative_difference=diff/(cb.sum()/ub.sum()),conditional_bootstrap_low=lo,conditional_bootstrap_high=hi,avoided_failures=win,introduced_failures=loss,paired_binary_p=pv))
    ci=pd.DataFrame(rows);ci['paired_binary_p_holm']=np.nan
    # LOBO cell outcomes have disjoint held-out batches conditional on source fits.
    # A single seed avoids duplicated cells. CV fitting dependence is descriptive.
    lobo_mask=(ci.dataset=='Battery')&(ci.analysis=='lobo')
    ci.loc[lobo_mask,'paired_binary_p_holm']=holm(ci.loc[lobo_mask,'paired_binary_p'])
    ci.to_csv(OUT/'real_conditional_intervals.csv',index=False)
    tests=[];keys=['attack','n_validation','rho','noise','life_variance','source_regime_prevalence','shift']
    for key,g in syn.groupby(keys):
        a=g[g.method=='RAMPE'].set_index('seed')
        for base in ['B','conventional']:
            b=g[g.method==base].set_index('seed').loc[a.index]
            d=a.population_rate.to_numpy()-b.population_rate.to_numpy();nz=d[abs(d)>1e-12]
            sd=d.std(ddof=1);se=sd/np.sqrt(len(d));half=student.ppf(.975,len(d)-1)*se
            tests.append(dict(zip(keys,key),baseline=base,seeds=len(d),mean_difference=d.mean(),sd_difference=sd,median_difference=np.median(d),mean_ci_low=d.mean()-half,mean_ci_high=d.mean()+half,relative_mean_difference=d.mean()/b.population_rate.mean(),wins=int((d<-1e-12).sum()),ties=int((abs(d)<=1e-12).sum()),losses=int((d>1e-12).sum()),sign_p=binomtest(int((nz<0).sum()),len(nz),.5).pvalue if len(nz) else 1.,context_feasible_fraction=a.population_context_feasible.mean(),risk_difference=(a.population_risk-b.population_risk).mean()))
    q=pd.DataFrame(tests);q['sign_p_holm']=holm(q.sign_p);q.to_csv(OUT/'synthetic_paired_tests.csv',index=False)
    for f,keys in [('validation_stress.csv.gz',['dataset','analysis','fraction','accounting_noise_sd','method']),('fixed_rule_shift.csv.gz',['dataset','analysis','evaluation_lead','evaluation_rho','method']),('temporal_reference.csv.gz',['feedback','block','shift','rho','method'])]:
        x=pd.read_csv(OUT/f);summary(x,keys,metrics+['population_rate','population_risk','population_context_feasible'],f.replace('.csv.gz','_summary.csv'))
    # Selection fragility: change in majority authority between repeated partition
    # seeds. These are selection seeds, not newly trained model seeds.
    z=real[real.method!='learned'].copy();authority=['authority_plain','authority_CAT','authority_CATc','authority_1SE']
    z['majority_policy']=z[authority].to_numpy().argmax(1)
    frag=z.groupby(['dataset','analysis','split','lead','rho','method']).majority_policy.agg(lambda v:1-v.value_counts().max()/len(v)).reset_index(name='partition_authority_fragility')
    frag.to_csv(OUT/'selection_fragility.csv',index=False)
    lmeta=lp.groupby('case').learned_policy.agg(lambda v:v.value_counts().index[0]).reset_index(name='majority_policy')
    lmeta=lmeta.merge(real[real.method=='learned'][['case','dataset','analysis','split','lead','rho']],on='case',validate='one_to_one')
    lf=lmeta.groupby(['dataset','analysis','split','lead','rho']).majority_policy.agg(lambda v:1-v.value_counts().max()/len(v)).reset_index(name='partition_authority_fragility');lf['method']='learned'
    pd.concat([frag,lf],ignore_index=True).to_csv(OUT/'selection_fragility.csv',index=False)
    learned=pd.read_csv(OUT/'learned_predictions.csv.gz');cal=[]
    for ds,g in learned.groupby('dataset'):
        prob=g.p_accept.to_numpy();label=g.acceptable.to_numpy();ece=0.
        for j in range(10):
            mask=(prob>=j/10)&(prob<((j+1)/10) if j<9 else prob<=1)
            if mask.any():ece+=mask.mean()*abs(prob[mask].mean()-label[mask].mean())
        cal.append(dict(dataset=ds,rows=len(g),acceptability_brier=float(((prob-label)**2).mean()),acceptability_ece=ece,mean_probability=prob.mean(),empirical_acceptability=label.mean()))
    pd.DataFrame(cal).to_csv(OUT/'learned_calibration.csv',index=False)
    unclear=syn[(syn.attack=='none')&(syn.method=='RAMPE')].copy();unclear['uncertainty_band']=pd.cut(unclear.validation_best_uncertainty,[-.001,.1,.3,1.],labels=['low','medium','high'])
    summary(unclear,['shift','uncertainty_band'],['population_rate','population_risk','abstention','oracle_disagreement'],'uncertain_best_policy.csv')
    counts=dict(real_method_rows=len(real),real_episodes=real.case.nunique(),synthetic_method_rows=len(syn),synthetic_episodes=syn.case.nunique(),synthetic_comparisons=len(q),synthetic_holm_significant=int((q.sign_p_holm<.05).sum()),conditional_real_comparisons=len(ci),lobo_holm_family=int(lobo_mask.sum()))
    (OUT/'statistical_scope.json').write_text(json.dumps(counts,indent=2),encoding='utf-8');print(counts)

if __name__=='__main__':main()
