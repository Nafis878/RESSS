"""Reproduce planned evidence; sealed outcomes are used only after selection."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from clock_regret_fleet.core import pair,select
from clock_regret_fleet.oracles import integer_pair,integer_family,continuous_pair,rate
from clock_regret_linear.core import select as common_select

OUT=Path('out/clock_regret_fleet')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def public_unit_class(unit):
    try: return int(unit)%3
    except ValueError: return int(hashlib.sha256(str(unit).encode('utf-8')).hexdigest(),16)%3


def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,default=str),encoding='utf-8')


def protect():
    hashes=json.loads((OUT/'protected_before.json').read_text())
    assert all(sha(p)==v for p,v in hashes.items())
    assert sha('clock_regret_fleet/PLAN.md')==(OUT/'PLAN.md.sha256').read_text().strip()
    return len(hashes)


def basic_records():
    rows=[]; rng=np.random.default_rng(20261031)
    for case in range(1000):
        n=int(rng.integers(1,5)); h=tuple(map(int,rng.integers(1,7,n)))
        f=tuple(map(bool,rng.random(n)<.35)); a,b=map(int,rng.integers(1,8,2))
        q=tuple(F(int(rng.integers(1,51)),int(rng.integers(1,8))) for _ in h)
        truth=integer_pair(h,f,a,b,q); exact=pair(h,f,a,b,q,exact=True); approx=pair(h,f,a,b,q)
        assert exact.lower==truth and approx.lower<=truth<=approx.upper<=F(5,4)*approx.lower
        assert rate(approx.lifetimes,a,q)/rate(approx.lifetimes,b,q)==approx.lower
        rows.append(dict(case=case,h=h,f=f,a=a,b=b,q=q,truth=truth,lower=approx.lower,
                         upper=approx.upper,witness=approx.lifetimes))
    save('full_clock.json',rows)
    rows=[]; rng=np.random.default_rng(20261032)
    for case in range(200):
        n=int(rng.integers(1,5)); h=tuple(map(int,rng.integers(1,6,n)))
        f=tuple(map(bool,rng.random(n)<.4)); ages=tuple(sorted(set(map(int,rng.integers(1,7,3)))))
        q=tuple(F(int(rng.integers(1,31)),3) for _ in h)
        truth=integer_family(h,f,ages,q); ans=select(h,f,ages,q)
        assert all(lo<=v<=up for lo,v,up in zip(ans['lower_scores'],truth,ans['upper_scores']))
        assert truth[ans['chosen']]<=F(5,4)*min(truth)
        if ans['certified_exact_decision']: assert truth[ans['chosen']]==min(truth)
        rows.append(dict(case=case,h=h,f=f,ages=ages,q=q,truth=truth,lower=ans['lower_scores'],
                         upper=ans['upper_scores'],chosen=ans['chosen'],certified=ans['certified_exact_decision']))
    save('full_family.json',rows)
    rows=[]; rng=np.random.default_rng(20261034)
    for case in range(200):
        n=int(rng.integers(1,5)); h=tuple(map(int,rng.integers(1,7,n)))
        f=tuple(map(bool,rng.random(n)<.35)); a,b=map(int,rng.integers(1,8,2))
        q=tuple(F(int(rng.integers(1,31)),5) for _ in h)
        truth=continuous_pair(h,f,a,b,q); ans=pair(h,f,a,b,q,continuous=True)
        assert pair(h,f,a,b,q,exact=True,continuous=True).lower==truth
        assert ans.lower<=truth<=ans.upper
        rows.append(dict(case=case,h=h,f=f,a=a,b=b,q=q,truth=truth,lower=ans.lower,upper=ans.upper,
                         limiting_lifetimes=ans.lifetimes,approach_indices=ans.approach_indices))
    save('continuous.json',rows)
    print('Small full-clock, family and continuous oracle studies complete.',flush=True)


def replay():
    public=pd.read_csv('out/clock_regret/real_public.csv.gz')
    sealed=pd.read_csv('out/clock_regret/real_sealed.csv.gz')
    frozen=pd.read_csv('out/clock_regret/real_results.csv.gz')
    rows=[]
    for number,(case,frame) in enumerate(public.groupby('case',sort=True),1):
        h=tuple(map(int,frame.horizon)); f=tuple(map(bool,frame.logger_failed))
        ages=tuple(map(int,str(frame.ages.iloc[0]).split('|'))); rho=int(frame.rho.iloc[0])
        common=common_select(h,f,ages,rho)
        reduction=select(h,f,ages,[rho-1]*len(h),exact=True)
        assert tuple(common['scores'])==reduction['lower_scores']
        previous=frozen[(frozen['case']==case)&(frozen.method=='exact_shared_clock')].iloc[0]
        assert int(previous.selected_age)==ages[common['chosen']]
        q=tuple(F((rho-1)*(1+public_unit_class(unit))) for unit in frame.unit)
        # Both decisions are finalized before accessing hidden lifetime values.
        approx=select(h,f,ages,q,F(1,4)); truth=select(h,f,ages,q,exact=True)
        assert all(lo<=v<=up for lo,v,up in zip(approx['lower_scores'],truth['lower_scores'],approx['upper_scores']))
        assert truth['lower_scores'][approx['chosen']]<=F(5,4)*min(truth['lower_scores'])
        if approx['certified_exact_decision']:
            assert truth['lower_scores'][approx['chosen']]==min(truth['lower_scores'])
        hidden=sealed[sealed['case']==case].set_index('unit')
        life=tuple(int(hidden.loc[unit,'lifetime']) for unit in frame.unit)
        assert all(t==hi if fi else t>hi for t,hi,fi in zip(life,h,f))
        costs=[rate(life,a,q) for a in ages]; oracle=min(costs)
        rows.append(dict(case=int(case),dataset=str(frame.dataset.iloc[0]),analysis=str(frame.analysis.iloc[0]),
             split=str(frame.split.iloc[0]),logger=str(frame.logger.iloc[0]),n=len(h),h=h,f=f,ages=ages,q=q,
             common_age=ages[common['chosen']],heterogeneous_exact_age=truth['selected_age'],
             approximate_age=approx['selected_age'],certified=approx['certified_exact_decision'],
             certified_unique=approx['certified_unique'],lower=approx['lower_scores'],upper=approx['upper_scores'],
             exact_scores=truth['lower_scores'],approximation_gap=truth['lower_scores'][approx['chosen']]/min(truth['lower_scores']),
             realized_common=costs[common['chosen']]/oracle,
             realized_heterogeneous=costs[truth['chosen']]/oracle,
             realized_approximate=costs[approx['chosen']]/oracle,
             states_peak=max(p.states_peak for row in approx['pairs'] for p in row)))
        if number%50==0: print(f'Frozen scenario replay: {number} cohorts.',flush=True)
    assert len(rows)==304
    save('engineering_scenarios.json',rows)
    differences=[float(F(r['realized_approximate'])-F(r['realized_common'])) for r in rows]
    summary=dict(cohorts=len(rows),source='Frozen engineering lifetime cohorts; constructed public cost scenarios',
        scenario_rule='q_i=(rho-1)*(1+public_unit_class); numeric ID mod 3 or UTF-8 SHA-256 integer mod 3 for nonnumeric IDs',common_reductions_exact=len(rows),
        approximate_exact_age_matches=sum(r['approximate_age']==r['heterogeneous_exact_age'] for r in rows),
        heterogeneous_changes_common_age=sum(r['heterogeneous_exact_age']!=r['common_age'] for r in rows),
        certified_exact_decisions=sum(r['certified'] for r in rows),
        certified_unique_decisions=sum(r['certified_unique'] for r in rows),
        single_candidate_cohorts=sum(len(r['ages'])==1 for r in rows),
        multiple_candidate_cohorts=sum(len(r['ages'])>1 for r in rows),
        nontrivial_certified_decisions=sum(r['certified'] and len(r['ages'])>1 for r in rows),
        max_selection_factor=max(float(r['approximation_gap']) for r in rows),
        realized_win_tie_loss=[sum(d<0 for d in differences),sum(d==0 for d in differences),sum(d>0 for d in differences)],
        mean_realized_relative_regret_change=float(np.mean(differences)),
        independent_observations=False,
        inferential_test='None: overlapping frozen cohorts and constructed costs do not justify independent-case significance tests.')
    save('engineering_summary.json',summary)
    print(json.dumps(summary),flush=True)


def stress():
    rng=np.random.default_rng(20261035); rows=[]
    for case in range(30):
        h=tuple(map(int,rng.integers(1,101,12)))+(180,190,200,210)
        f=(False,)*12+(True,)*4
        q=tuple(F(10*hi+int(rng.integers(1,51))) for hi in h[:12])+(F(300),)*4
        exact=pair(h,f,120,240,q,exact=True)
        for eps in [F(1,2),F(1,4),F(1,10)]:
            ans=pair(h,f,120,240,q,eps)
            assert ans.lower<=exact.lower<=ans.upper<= (1+eps)*ans.lower
            rows.append(dict(case=case,h=h,f=f,q=q,a=120,b=240,epsilon=eps,
                exact=exact.lower,lower=ans.lower,upper=ans.upper,
                approximation_factor=exact.lower/ans.lower,
                exact_states_peak=exact.states_peak,approximate_states_peak=ans.states_peak,
                witness=ans.lifetimes))
    save('tolerance_stress.json',rows)
    summary={str(eps):dict(cases=30,max_pair_gap=max(float(r['approximation_factor']) for r in rows if r['epsilon']==eps),
                    mean_pair_gap=float(np.mean([float(r['approximation_factor']) for r in rows if r['epsilon']==eps])),
                    median_state_ratio=float(np.median([r['exact_states_peak']/r['approximate_states_peak'] for r in rows if r['epsilon']==eps])))
             for eps in [F(1,2),F(1,4),F(1,10)]}
    save('stress_summary.json',summary); print(json.dumps(summary),flush=True)


def main():
    start=time.monotonic(); count=protect()
    basic_records(); replay(); stress()
    assert protect()==count
    save('run_summary.json',dict(protected_artifacts_unchanged=count,seconds=time.monotonic()-start,
        planned_studies_complete=True,historical_novelty_established=False,public_priority_established=False))


if __name__=='__main__': main()
