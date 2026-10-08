"""Explicit controlled policy-outcome experiment, not a maintenance simulator."""
import itertools,sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import core as R
OUT=Path('out/rampe')
SELECTORS=['conventional','RAMPE','RAMPE_no_reliability','RAMPE_no_stability','RAMPE_no_calibration','RAMPE_no_transfer','RAMPE_no_abstention','RAMPE_no_context','normalized','uncertainty','rank']
ENSEMBLES={'uniform_ensemble':'uniform','reliability_ensemble':'reliability','random_weights':'random','cost_weights':'inverse_cost'}


def rates(context,shift):
    context=np.asarray(context,int)
    return np.column_stack([np.full(len(context),.01+.08*shift),np.zeros(len(context)),
                            np.where(context==1,.06*shift,np.where(context==2,.7,.15+.1*shift))])


def cohort(n,prev,sigma,seed,stream,shift=0,unknown=False,allfail=False):
    rng=np.random.default_rng(np.random.SeedSequence([seed,stream]))
    uctx=rng.random(n);ctx=(uctx<min(.99,prev+.3*shift)).astype(int)
    if unknown:ctx[:]=2
    p=rates(ctx,shift)
    if unknown:p[:,0]=.7
    if allfail:p[:]=1.
    f=rng.random((n,3))<p
    t=np.column_stack([10*rng.lognormal(-.5*sigma*sigma,sigma,n),np.full(n,6.),np.where(ctx==1,9.,10.)])
    return ctx,t,f


def oracle(mu_c,mu_t,p,prob,alpha=.05):
    """Known-population fractional routing oracle; never used for selection."""
    feasible=p<=alpha+1e-12
    if not feasible.any(axis=1).all():return np.full(len(prob),-1),np.nan
    r=0.
    for _ in range(30):
        a=np.argmin(np.where(feasible,mu_c-r*mu_t,np.inf),axis=1)
        rr=float((prob*mu_c[np.arange(len(prob)),a]).sum()/(prob*mu_t[np.arange(len(prob)),a]).sum())
        if abs(rr-r)<1e-12:return a,rr
        r=rr
    return a,r


def evaluate(ev,glob,ctx,c,t,f,u,info,mu_c,mu_t,p,prob):
    contexts=[int(x) for x in np.unique(ctx)];out=[]
    oa,orr=oracle(mu_c,mu_t,p,prob)
    for kind in ['A','B','C']+SELECTORS+list(ENSEMBLES):
        a=np.empty(len(ctx),int);ab=np.zeros(len(ctx),bool);ww=[]
        for x in contexts:
            mask=ctx==x;e=glob if kind in ['conventional','RAMPE_no_context'] else ev[x]
            if kind in ['A','B','C']:
                j=['A','B','C'].index(kind);w=np.eye(3)[j];a[mask]=j
            elif kind in ENSEMBLES:
                w=R.weights(e,ENSEMBLES[kind],seed=info['seed'])
                a[mask]=np.minimum(np.searchsorted(np.cumsum(w),u[mask],side='right'),2)
            else:
                j,b=R.choose(e,kind,fallback=1);w=np.eye(3)[j];a[mask]=j;ab[mask]=b
            ww.append(w)
        w=np.vstack(ww);pop=float((prob[:,None]*w*mu_c).sum()/(prob[:,None]*w*mu_t).sum())
        prisk=float((prob[:,None]*w*p).sum())
        safe=bool(not ((w>1e-12)&(p>.05+1e-12)).any())
        disagreement=float(sum(prob[i]*(1-w[i,oa[i]]) for i in range(len(prob)))) if np.isfinite(orr) else np.nan
        mm=R.metrics(c,t,f,a,ab)
        mm.update(population_rate=pop,population_risk=prisk,population_context_feasible=safe,
                  reliable_oracle_rate=orr,excess_cost_vs_reliable_oracle=pop-orr,
                  oracle_disagreement=disagreement,validation_best_uncertainty=float(np.mean([1-max(ev[x].stability) for x in contexts])))
        out.append(dict(method=kind,**info,**mm))
    return out


def main():
    rows=[];case=0
    for n,rho,noise,sigma,prev in itertools.product([32,128,512,2048],[10,50],[0.,1.],[0.,.6],[.1,.5,.9]):
        for seed in range(2026,2056):
            vc,vt,vf=cohort(n,prev,sigma,seed,1)
            costs=1+(rho-1)*vf.astype(float)
            eps=np.random.default_rng(np.random.SeedSequence([seed,3])).normal(size=costs.shape)
            observed=np.maximum(.01,costs+noise*eps)
            glob=R.evidence(observed,vt,vf,vc,0,seed=seed,strata=3,pooled=True)
            ev={x:R.evidence(observed,vt,vf,vc,x,seed=seed,strata=3) for x in [0,1]}
            for shift in [0.,.5,1.]:
                case+=1;ctx,t,f=cohort(1000,prev,sigma,seed,2,shift)
                c=1+(rho-1)*f.astype(float);u=np.random.default_rng(np.random.SeedSequence([seed,4])).random(len(ctx))
                p=rates(np.array([0,1]),shift);mu_c=1+(rho-1)*p;mu_t=np.array([[10,6,10],[10,6,9]])
                prob=np.array([1-min(.99,prev+.3*shift),min(.99,prev+.3*shift)])
                info=dict(case=case,n_validation=n,rho=rho,noise=noise,life_variance=sigma,source_regime_prevalence=prev,shift=shift,seed=seed,attack='none')
                rows.extend(evaluate(ev,glob,ctx,c,t,f,u,info,mu_c,mu_t,p,prob))
        print(f'Synthetic n={n},rho={rho},noise={noise},life_sigma={sigma},regime_prevalence={prev}: {case} cases',flush=True)
    for attack in ['unseen_regime','known_all_fail']:
        for seed in range(2026,2056):
            case+=1;n=512;rho=50
            vc,vt,vf=cohort(n,.5,.6,seed,1,allfail=attack=='known_all_fail')
            obs=1+(rho-1)*vf.astype(float)
            glob=R.evidence(obs,vt,vf,vc,0,seed=seed,strata=3,pooled=True)
            targetcontexts=[2] if attack=='unseen_regime' else [0,1]
            ev={x:R.evidence(obs,vt,vf,vc,x,seed=seed,strata=3) for x in targetcontexts}
            ctx,t,f=cohort(1000,.5,.6,seed,2,unknown=attack=='unseen_regime',allfail=attack=='known_all_fail')
            p=rates(np.array(targetcontexts),0)
            if attack=='unseen_regime':p[:,0]=.7
            else:p[:]=1
            mu_c=1+(rho-1)*p;mu_t=np.array([[10,6,10]]) if attack=='unseen_regime' else np.array([[10,6,10],[10,6,9]])
            prob=np.array([1.]) if attack=='unseen_regime' else np.array([.5,.5])
            u=np.random.default_rng(np.random.SeedSequence([seed,4])).random(1000)
            info=dict(case=case,n_validation=n,rho=rho,noise=0.,life_variance=.6,source_regime_prevalence=.5,shift=0.,seed=seed,attack=attack)
            rows.extend(evaluate(ev,glob,ctx,1+(rho-1)*f.astype(float),t,f,u,info,mu_c,mu_t,p,prob))
    x=pd.DataFrame(rows);x.to_csv(OUT/'synthetic_results.csv.gz',index=False)
    print(f'PASS {case} synthetic episodes; {len(x)} method outcomes.',flush=True)


if __name__=='__main__':main()
