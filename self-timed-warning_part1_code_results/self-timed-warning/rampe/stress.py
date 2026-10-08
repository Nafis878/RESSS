"""Validation, fixed-rule lead/cost and support stress; legacy compatibility bridge."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import core as R
from real import load_groups,decisions
OUT=Path('out/rampe')


def main():
    rows=[];shiftrows=[];files={}
    keep=['RAMPE','RAMPE_no_abstention','RAMPE_no_calibration','conventional','normalized','1SE']
    for info,units,ctx,strata,c,t,f in load_groups():
        for seed in range(2026,2036):
            perm=np.random.default_rng(seed).permutation(len(units));val0=perm[:len(units)//2];te=np.sort(perm[len(units)//2:])
            u=np.random.default_rng(seed+10000).random(len(te))
            for fraction in [.25,.5,1.]:
                val=val0[:max(1,int(len(val0)*fraction))]
                eps=np.random.default_rng(seed+20000).normal(size=c[val].shape)
                for noise in [0.,.1,1.]:
                    obs=np.maximum(.01,c[val]+noise*eps)
                    glob=R.evidence(obs,t[val],f[val],ctx[val],0,seed=seed,strata=strata,pooled=True)
                    ev={str(x):R.evidence(obs,t[val],f[val],ctx[val],x,seed=seed,strata=strata) for x in np.unique(ctx[te])}
                    a,b=decisions(ev,glob,ctx[te],u,seed)
                    for method in keep:
                        rows.append(dict(seed=seed,fraction=fraction,accounting_noise_sd=noise,n_validation=len(val),method=method,**info,**R.metrics(c[te],t[te],f[te],a[method],b[method])))
            if info['lead']==0 and info['rho']==10:
                if info['dataset'] not in files:
                    z=pd.read_csv(f"results/contrib/{info['dataset']}_cost.csv",low_memory=False)
                    if info['dataset']!='Battery':z=z.assign(analysis='engine',split=z.fold.astype(str))
                    z['unit']=z.unit.astype(str);z['split']=z.split.astype(str);files[info['dataset']]=z
                z=files[info['dataset']]
                lives=z[(z.analysis==info['analysis'])&(z.split==str(info['split']))&(z.policy=='run_to_failure')&(z.lead_cycles==0)&(z.rho==10)].set_index('unit').loc[units].use.to_numpy()
                assert np.allclose(t[f],np.broadcast_to(lives[:,None],t.shape)[f])
                glob=R.evidence(c[val0],t[val0],f[val0],ctx[val0],0,seed=seed,strata=strata,pooled=True)
                ev={str(x):R.evidence(c[val0],t[val0],f[val0],ctx[val0],x,seed=seed,strata=strata) for x in np.unique(ctx[te])}
                actions,ab=decisions(ev,glob,ctx[te],u,seed)
                leads=[0,15,30,45] if info['dataset']=='Battery' else [0,5,10,15]
                for lead in leads:
                    ff=f|((t+lead)>=lives[:,None]);tt=np.where(ff,lives[:,None],t+lead)
                    for rho in [5,10,20,50,100]:
                        cc=1+(rho-1)*ff.astype(float)
                        for method in keep:
                            shiftrows.append(dict(seed=seed,evaluation_lead=lead,evaluation_rho=rho,selection_lead=0,selection_rho=10,method=method,**info,**R.metrics(cc[te],tt[te],ff[te],actions[method],ab[method])))
                # Artificially remove the context-support signal. Outcomes stay fixed.
                unseen={str(x):R.evidence(c[val0],t[val0],f[val0],ctx[val0],'never_observed',seed=seed,strata=strata) for x in np.unique(ctx[te])}
                for kind in ['RAMPE','RAMPE_no_transfer']:
                    aa=[];bb=[]
                    for x in ctx[te]:j,b=R.choose(unseen[str(x)],kind);aa.append(j);bb.append(b)
                    rows.append(dict(seed=seed,fraction=1.,accounting_noise_sd=0.,n_validation=len(val0),method=kind+'_support_attack',**info,**R.metrics(c[te],t[te],f[te],aa,bb)))
        if info['rho']==10 and info['lead']==0:print(f"Stress {info['dataset']}/{info['analysis']}/{info['split']}",flush=True)
    pd.DataFrame(rows).to_csv(OUT/'validation_stress.csv.gz',index=False)
    pd.DataFrame(shiftrows).to_csv(OUT/'fixed_rule_shift.csv.gz',index=False)
    oldpath=Path('out/research_next/calibration_stress.csv.gz');old=pd.read_csv(oldpath,low_memory=False)
    bridge=dict(rows=len(old),sha256=hashlib.sha256(oldpath.read_bytes()).hexdigest(),all_rows_read=True,
        reused_calibration_fractions=sorted(old.calibration_fraction.unique().tolist()),reused_seeds=sorted(old.seed.unique().tolist()),
        compatible='sampling fractions and calibration-resampling seed framework',
        incompatible='score perturbations do not supply all four candidate alarm/life/cost trajectories; not recast as RAMPE cost results',
        prior_results_unchanged=True)
    (OUT/'legacy_stress_bridge.json').write_text(json.dumps(bridge,indent=2),encoding='utf-8')
    print(f'PASS {len(rows)} validation/support method cases and {len(shiftrows)} fixed-rule shift method cases; all {len(old)} legacy rows preserved/read.',flush=True)


if __name__=='__main__':main()
