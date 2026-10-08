import json
from fractions import Fraction
from pathlib import Path
import numpy as np
import pandas as pd
from clock_regret_linear.core import select as grid_select
from clock_regret_linear.continuous import select as continuous_select, closure_state_pair, ContinuousPrepared
from clock_regret_linear.run import OUT, protect, sha


def main():
    protect()
    (OUT/'PLAN_RESOLUTION.md.sha256').write_text(sha('clock_regret_linear/PLAN_RESOLUTION.md'))
    rng = np.random.default_rng(20261013)
    oracle = []
    for case in range(300):
        n = int(rng.integers(1,13))
        h = rng.integers(1,20,n)
        f = rng.random(n)<.4
        a,b = map(int,rng.integers(1,25,2))
        rho = int(rng.choice([2,5,20,50]))
        ans = ContinuousPrepared(h,f,[a,b],rho).pair(a,b)
        assert ans.ratio == closure_state_pair(h,f,a,b,rho)
        oracle.append(dict(case=case,n=n,age_a=a,age_b=b,rho=rho,
            numerator=ans.ratio.numerator,denominator=ans.ratio.denominator,exact_match=True,
            attained=ans.attained,horizon='|'.join(map(str,h)),logger_failed='|'.join(map(str,f.astype(int)))))
    pd.DataFrame(oracle).to_csv(OUT/'continuous_oracle.csv',index=False)
    rows=[]
    for case in range(300):
        n=int(rng.integers(1,21))
        h=rng.integers(1,16,n)
        f=rng.random(n)<.4
        ages=sorted(set(map(int,rng.integers(1,21,4))))
        rho=int(rng.choice([2,5,20,50]))
        c=continuous_select(h,f,ages,rho)
        for r in [1,2,4,16,64]:
            grid=grid_select(h*r,f,np.array(ages)*r,rho,include_witness=False)
            bound=Fraction(r+1,r)
            for i,a in enumerate(ages):
                assert grid['scores'][i] <= c['scores'][i] <= bound*grid['scores'][i]
                for j,b in enumerate(ages):
                    gr=grid['pairs'][i][j].ratio
                    gc=c['pairs'][i][j].ratio
                    assert gr <= gc <= bound*gr
            j=grid['chosen']
            assert c['scores'][j] <= bound*min(c['scores'])
            rows.append(dict(case=case,n=n,r=r,rho=rho,ages='|'.join(map(str,ages)),
                grid_age=ages[j],continuous_age=ages[c['chosen']],
                grid_optimum=str(min(grid['scores'])),continuous_optimum=str(min(c['scores'])),
                selected_continuous_factor=str(c['scores'][j]),uniform_factor_bound=str(bound),
                all_pairwise_bounds_hold=True,selection_bound_holds=True,
                horizon='|'.join(map(str,h)),logger_failed='|'.join(map(str,f.astype(int)))))
    pd.DataFrame(rows).to_csv(OUT/'resolution_sandwich.csv',index=False)
    demo=[]
    h=np.array([1]*5); f=np.array([True]*4+[False])
    c=ContinuousPrepared(h,f,[3,2],2).pair(3,2)
    for r in [1,2,4,8,16,64,1024]:
        g=grid_select(h*r,f,np.array([3,2])*r,2)['pairs'][0][1]
        demo.append(dict(r=r,grid_factor=str(g.ratio),continuous_factor=str(c.ratio),
            grid_factor_float=float(g.ratio),continuous_factor_float=float(c.ratio),branch=g.branch))
    pd.DataFrame(demo).to_csv(OUT/'resolution_example.csv',index=False)
    summary=dict(continuous_independent_oracle_cases=300,all_exact_matches=True,
        independent_resolution_cohorts=300,resolution_factors=[1,2,4,16,64],
        full_family_resolution_tasks=1500,all_bounds_hold=True,
        priority_established=False,protected_artifacts_unchanged=protect())
    (OUT/'resolution_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    main()
