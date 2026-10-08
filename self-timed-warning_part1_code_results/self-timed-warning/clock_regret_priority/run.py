"""Store all independently checkable heterogeneous-cost correctness evidence."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from clock_regret_priority.heterogeneous import later_pair,continuous_later_pair,phase_oracle,rate_ratio
from clock_regret_priority.test_heterogeneous import exhaustive
from clock_regret_linear.core import worst_pair as common_pair
from clock_regret_linear.continuous import ContinuousPrepared

OUT=Path('out/clock_regret_priority')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protect():
    hashes=json.loads((OUT/'protected_before.json').read_text())
    assert len(hashes)==908 and all(sha(p)==h for p,h in hashes.items())
    return len(hashes)


def row(case,h,f,a,b,q,method,actual,oracle):
    assert actual==oracle
    return dict(case=case,n=len(h),horizon='|'.join(map(str,h)),logger_failed='|'.join(map(str,map(int,f))),
                age_a=a,age_b=b,premiums='|'.join(map(str,q)),method=method,
                exact_ratio=str(actual),oracle_ratio=str(oracle),exact_match=True)


def main():
    start=time.monotonic(); protect()
    assert sha('clock_regret_priority/PLAN.md')==(OUT/'PLAN.md.sha256').read_text().strip()
    rng=np.random.default_rng(20261021); records=[]
    for case in range(1000):
        n=int(rng.integers(1,5)); h=rng.integers(1,7,n); f=rng.random(n)<.35
        b=int(rng.integers(1,6)); a=int(rng.integers(b+1,8))
        q=[Fraction(int(rng.integers(1,31)),int(rng.integers(1,8))) for _ in range(n)]
        ans=later_pair(h,f,a,b,q)
        assert rate_ratio(ans.witness,a,b,q)==ans.ratio
        entry=row(case,h,f,a,b,q,'full_clock',ans.ratio,exhaustive(h,f,a,b,q))
        entry.update(witness='|'.join(map(str,ans.witness)),shared_count=ans.shared_count,
                     denominators='|'.join(map(str,ans.denominators)))
        records.append(entry)
    pd.DataFrame(records).to_csv(OUT/'full_clock.csv.gz',index=False)
    print('1,000 exhaustive full-clock comparisons complete.',flush=True)
    rng=np.random.default_rng(20261022); records=[]
    for case in range(500):
        n=int(rng.integers(1,9)); h=rng.integers(1,15,n); f=rng.random(n)<.35
        b=int(rng.integers(1,18)); a=b+int(rng.integers(1,8))
        q=[Fraction(int(rng.integers(1,51)),int(rng.integers(1,8))) for _ in range(n)]
        for is_continuous,fn in [(False,later_pair),(True,continuous_later_pair)]:
            ans=fn(h,f,a,b,q)
            records.append(row(case,h,f,a,b,q,'continuous_state' if is_continuous else 'integer_state',
                               ans.ratio,phase_oracle(h,f,a,b,q,continuous=is_continuous)))
    pd.DataFrame(records).to_csv(OUT/'phase_oracles.csv.gz',index=False)
    print('500 integer and 500 continuous phase-state comparisons complete.',flush=True)
    rng=np.random.default_rng(20261023); records=[]
    for case in range(200):
        n=int(rng.integers(1,101)); h=rng.integers(1,40,n); f=rng.random(n)<.4
        b=int(rng.integers(1,40)); a=b+int(rng.integers(1,30)); rho=int(rng.choice([2,5,20,50]));q=[rho-1]*n
        records.append(row(case,h,f,a,b,q,'integer_common_reduction',later_pair(h,f,a,b,q).ratio,
                           common_pair(h,f,a,b,rho).ratio))
        records.append(row(case,h,f,a,b,q,'continuous_common_reduction',continuous_later_pair(h,f,a,b,q).ratio,
                           ContinuousPrepared(h,f,[a,b],rho).pair(a,b).ratio))
    pd.DataFrame(records).to_csv(OUT/'common_reduction.csv.gz',index=False)
    rng=np.random.default_rng(20261024); epsilon_rows=[]; resolution_rows=[]
    for case in range(200):
        n=int(rng.integers(1,16)); h=rng.integers(1,15,n); f=rng.random(n)<.4
        b=int(rng.integers(1,15)); a=b+int(rng.integers(1,7))
        q=[Fraction(int(rng.integers(1,41)),3) for _ in range(n)]
        c=continuous_later_pair(h,f,a,b,q); previous=Fraction(0)
        for eps in [Fraction(1,2),Fraction(1,16),Fraction(1,1024)]:
            life=c.completion(eps); actual=rate_ratio(life,a,b,q)
            assert all(t==int(hi) if fi else t>int(hi) for t,hi,fi in zip(life,h,f))
            assert previous<=actual<=c.ratio and (actual==c.ratio)==c.attained
            entry=row(case,h,f,a,b,q,'epsilon',c.ratio,c.ratio)
            entry.update(epsilon=str(eps),completion='|'.join(map(str,life)),completion_ratio=str(actual),attained=c.attained)
            epsilon_rows.append(entry); previous=actual
        for r in [1,2,4,16,64]:
            g=later_pair(h*r,f,a*r,b*r,q); bound=Fraction(r+1,r)
            assert g.ratio<=c.ratio<=bound*g.ratio
            entry=row(case,h,f,a,b,q,'resolution',c.ratio,c.ratio)
            entry.update(r=r,grid_ratio=str(g.ratio),uniform_bound=str(bound),bounds_hold=True)
            resolution_rows.append(entry)
    pd.DataFrame(epsilon_rows).to_csv(OUT/'epsilon_sequences.csv.gz',index=False)
    pd.DataFrame(resolution_rows).to_csv(OUT/'resolution.csv.gz',index=False)
    sharp=[]
    for n in [1,2,8]:
        q=[Fraction(i+1,i+2) for i in range(n)]
        c=continuous_later_pair([1]*n,[False]*n,2,1,q)
        for r in [1,2,4,16,64,1024]:
            g=later_pair([r]*n,[False]*n,2*r,r,q)
            assert c.ratio/g.ratio==Fraction(r+1,r)
            sharp.append(dict(n=n,r=r,premiums='|'.join(map(str,q)),grid_ratio=str(g.ratio),
                              continuous_ratio=str(c.ratio),exact_factor=str(c.ratio/g.ratio),sharp=True))
    pd.DataFrame(sharp).to_csv(OUT/'sharpness.csv',index=False)
    example=later_pair([1,1,1],[True,False,False],3,2,[98,1,100])
    (OUT/'interior_counterexample.json').write_text(json.dumps(dict(horizon=[1,1,1],logger_failed=[True,False,False],
        premiums=[98,1,100],age_a=3,age_b=2,denominators=list(map(str,example.denominators)),
        optimal_shared_count=example.shared_count,witness=example.witness,exact_ratio=str(example.ratio),
        two_endpoint_ratio=str(Fraction(1010,min(example.denominators[0],example.denominators[-1])))),indent=2),encoding='utf-8')
    summary=dict(exhaustive_full_clock_cases=1000,integer_state_cases=500,continuous_state_cases=500,
                 common_cost_integer_cases=200,common_cost_continuous_cases=200,
                 compatible_epsilon_completions=600,heterogeneous_resolution_comparisons=1000,
                 sharpness_equalities=18,all_checks_passed=True,protected_artifacts_unchanged=protect(),
                 historical_priority_established=False,elapsed_seconds=time.monotonic()-start)
    (OUT/'run_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__': main()
