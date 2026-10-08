"""Controlled full-information temporal reference; no bandit or RL claim.

Past blocks supply all policies' completed-unit counterfactual outcomes. Real
preventive intervention does not supply this feedback; this is an information
reference, not a deployable censoring model or a chronological real dataset.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import core as R
from synthetic import cohort,rates,evaluate
OUT=Path('out/rampe')


def main():
    rows=[]
    for seed in range(2026,2056):
        ctx0,t0,f0=cohort(512,.5,.6,seed,1)
        history_ctx,history_t,history_f=ctx0.copy(),t0.copy(),f0.copy()
        for block in range(8):
            shift=0 if block<3 else (.5 if block<6 else 1.)
            rho=50 if block<5 else 100
            tc,tt,tf=cohort(256,.5,.6,seed,100+block,shift)
            p=rates(np.array([0,1]),shift);mc=1+(rho-1)*p;mt=np.array([[10,6,10],[10,6,9]])
            prevalence=min(.99,.5+.3*shift);prob=np.array([1-prevalence,prevalence])
            u=np.random.default_rng(np.random.SeedSequence([seed,200+block])).random(256)
            for updating in [False,True]:
                cc,tt0,ff=(history_ctx[-512:],history_t[-512:],history_f[-512:]) if updating else (ctx0,t0,f0)
                costs=1+(rho-1)*ff.astype(float)
                glob=R.evidence(costs,tt0,ff,cc,0,seed=seed,strata=3,pooled=True)
                ev={x:R.evidence(costs,tt0,ff,cc,x,seed=seed,strata=3) for x in [0,1]}
                info=dict(case=seed*10+block,seed=seed,block=block,shift=shift,rho=rho,n_validation=512,noise=0.,life_variance=.6,source_regime_prevalence=.5,attack='none',feedback='rolling_full_information' if updating else 'static_source')
                rows.extend(evaluate(ev,glob,tc,1+(rho-1)*tf.astype(float),tt,tf,u,info,mc,mt,p,prob))
            # Feedback is added only after both selectors finish the block.
            history_ctx=np.concatenate([history_ctx,tc]);history_t=np.vstack([history_t,tt]);history_f=np.vstack([history_f,tf])
        print(f'Temporal full-information reference seed {seed}',flush=True)
    pd.DataFrame(rows).to_csv(OUT/'temporal_reference.csv.gz',index=False)
    print(f'PASS {len(rows)} temporal reference outcomes; no future block used in selection.',flush=True)


if __name__=='__main__':main()
