"""Build an outcome-summary benchmark with sealed full-lifetime truth."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path('rampe').resolve()))
from real import load_groups
sys.path.insert(0,str(Path.cwd()))
from observability.core import identify,visible_view,complete_case,healthy_imputation
OUT=Path('out/observability');POOL=['plain','CAT','CATc','1SE']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def protect():
    OUT.mkdir(parents=True,exist_ok=True);p=OUT/'protected_before.json'
    if p.exists():
        hashes=json.loads(p.read_text())
        assert all(sha(path)==h for path,h in hashes.items());return
    hashes=json.loads(Path('out/rampe/frozen_before.json').read_text())
    for folder in [Path('rampe'),Path('out/rampe')]:
        for f in folder.rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts:hashes[f.as_posix()]=sha(f)
    assert all(sha(path)==h for path,h in hashes.items())
    p.write_text(json.dumps(hashes,indent=1),encoding='utf-8');(OUT/'plan_sha256.txt').write_text(sha('observability/PLAN.md'),encoding='utf-8')

def main():
    protect();public=[];truth=[];tasks=[];budgets=[];task=0
    for info,units,context,strata,c,t,f in load_groups():
        assert t.max()<2000,('cap too small',info,t.max())
        for logger in range(4):
            h=t[:,logger];lograte=float(c[:,logger].sum()/h.sum())
            for target in range(4):
                task+=1;observable=f[:,logger]|(t[:,target]<=h+1e-10)
                view=visible_view(h,observable,c[:,target],t[:,target],f[:,target]);tr=float(c[:,target].sum()/t[:,target].sum());fr=float(f[:,target].mean())
                meta=dict(task=task,logger=POOL[logger],target=POOL[target],**info)
                for i,u in enumerate(units):
                    public.append(dict(unit=u,logger_endpoint=h[i],logger_cost=c[i,logger],logger_fail=int(f[i,logger]),outcome_observed=int(observable[i]),target_cost=view['cost'][i],target_use=view['use'][i],target_fail=view['fail'][i],**meta))
                    truth.append(dict(unit=u,true_target_cost=c[i,target],true_target_use=t[i,target],true_target_fail=int(f[i,target]),**meta))
                cc,cr=complete_case(view);hc,hr=healthy_imputation(view)
                for cap in [2000.,5000.,10000.]:
                    iv=identify(**view,rho=info['rho'],cap=cap)
                    tasks.append(dict(logger_rate=lograte,true_target_rate=tr,true_target_risk=fr,n=len(units),cap=cap,observed_fraction=observable.mean(),complete_case_rate=cc,complete_case_risk=cr,healthy_rate=hc,healthy_risk=hr,complete_case_false_improvement=bool(np.isfinite(cc) and cc<lograte-1e-12 and tr>=lograte-1e-12),healthy_false_improvement=bool(hc<lograte-1e-12 and tr>=lograte-1e-12),complete_case_false_safe=bool(np.isfinite(cr) and cr<=.05 and fr>.05),healthy_false_safe=bool(hr<=.05 and fr>.05),rate_low=iv.rate_low,rate_high=iv.rate_high,risk_low=iv.risk_low,risk_high=iv.risk_high,certified_improvement=iv.rate_high<lograte-1e-12,certified_safe=iv.risk_high<=.05,**meta))
                # Limited sealed-label reveals, not an operational audit claim.
                missing=np.flatnonzero(~observable)
                for seed in range(2026,2036):
                    order=np.random.default_rng(seed).permutation(missing)
                    for fraction in [0.,.1,.25,.5,1.]:
                        reveal=observable.copy();reveal[order[:int(np.ceil(fraction*len(missing)))]]=True
                        vv=visible_view(h,reveal,c[:,target],t[:,target],f[:,target]);iv=identify(**vv,rho=info['rho'],cap=5000.)
                        budgets.append(dict(seed=seed,release_fraction=fraction,released=int(reveal.sum()-observable.sum()),unknown=int((~reveal).sum()),n=len(units),logger_rate=lograte,true_target_rate=tr,true_target_risk=fr,rate_low=iv.rate_low,rate_high=iv.rate_high,risk_low=iv.risk_low,risk_high=iv.risk_high,certified_improvement=iv.rate_high<lograte-1e-12,certified_safe=iv.risk_high<=.05,**meta))
    pd.DataFrame(public).to_csv(OUT/'public_outcomes.csv.gz',index=False);pd.DataFrame(truth).to_csv(OUT/'sealed_truth.csv.gz',index=False)
    x=pd.DataFrame(tasks);x.to_csv(OUT/'task_results.csv.gz',index=False);pd.DataFrame(budgets).to_csv(OUT/'information_budget.csv.gz',index=False)
    metrics=['observed_fraction','true_target_rate','true_target_risk','rate_low','rate_high','risk_low','risk_high','certified_improvement','certified_safe','complete_case_false_improvement','healthy_false_improvement','complete_case_false_safe','healthy_false_safe']
    x.groupby(['dataset','analysis','logger','target','cap'])[metrics].mean().reset_index().to_csv(OUT/'pair_summary.csv',index=False)
    x[x.cap==5000].groupby(['dataset','analysis'])[metrics].mean().reset_index().to_csv(OUT/'domain_summary.csv',index=False)
    b=pd.DataFrame(budgets);b['rate_width']=b.rate_high-b.rate_low;b['risk_width']=b.risk_high-b.risk_low
    b.groupby(['release_fraction'])[['rate_width','risk_width','certified_improvement','certified_safe','released']].mean().reset_index().to_csv(OUT/'budget_summary.csv',index=False)
    print(json.dumps(dict(tasks=task,public_unit_rows=len(public),sealed_truth_rows=len(truth),cap_sensitivity_rows=len(tasks),budget_rows=len(budgets)),indent=2))

if __name__=='__main__':main()
