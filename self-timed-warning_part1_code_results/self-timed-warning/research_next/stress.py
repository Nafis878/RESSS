"""Post hoc calibration/score stress and labelled-target reference experiments.

Models remain fixed. This does not create or validate a new optimizer. New
outputs are isolated and never replace the frozen primary experiment.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import calibration_tools as T

OUT=Path('out/research_next')
ENG=['PHM08','FD001','FD002','FD003','FD004','NCMAPSS6']


def groups():
    for ds in ENG:
        x=pd.read_csv(f'results/contrib/{ds}_scores.csv.gz')
        x=x[x.selected]
        for (fold,lead,dt),g in x.groupby(['fold','lead_cycles','dT']):
            o=g[g.role=='oof'];t=g[g.role=='test']
            yield ds,'engine',str(fold),lead,dt,1.,o.score.to_numpy(),t.score.to_numpy(),np.arange(1.,61.)
    for p in sorted((OUT/'battery').glob('*_scores.csv')):
        x=pd.read_csv(p)
        for lead,g in x.groupby('lead'):
            yield 'Battery',g.analysis.iloc[0],g.split.iloc[0],lead,1,3.,g[g.role=='oof'].score.to_numpy(),g[g.role=='test_refit'].score.to_numpy(),np.arange(3.,181.,3.)


def calibration_stress():
    rows=[]
    for ds,an,split,lead,dt,scale,o,t,grid in groups():
        for fraction in [.25,.5,1.]:
            m=max(1,int(np.floor(len(o)*fraction)))
            for seed in range(2026,2036):
                rng=np.random.default_rng(seed);idx=rng.permutation(len(o))[:m];noise=rng.normal(size=m)
                for sd in [0.,3.,6.]:
                    cal=np.where(np.isfinite(o[idx]),o[idx]+sd*scale*noise,np.inf)
                    for alpha in [.01,.02,.05,.1]:
                        th,finite=T.grid_threshold(cal,alpha,grid)
                        for shift in [0.,3.,6.,12.]:
                            changed=t+shift*scale
                            rows.append(dict(dataset=ds,analysis=an,split=split,lead=lead,dT=dt,seed=seed,
                                calibration_fraction=fraction,n_cal=m,noise_cycles=sd*scale,target_score_shift=shift*scale,
                                alpha=alpha,threshold=th,finite_threshold=finite,n_test=len(t),
                                failures=int((changed>th).sum()),risk=float((changed>th).mean())))
        print(f'Stress {ds}/{an}/{split}/lead={lead}/grid={dt}',flush=True)
    x=pd.DataFrame(rows);x.to_csv(OUT/'calibration_stress.csv.gz',index=False)
    cols=['dataset','analysis','lead','dT','calibration_fraction','noise_cycles','target_score_shift','alpha']
    y=x.groupby(cols).agg(mean_risk=('risk','mean'),sd_risk=('risk','std'),median_risk=('risk','median'),
        min_risk=('risk','min'),max_risk=('risk','max'),finite_share=('finite_threshold','mean'),cases=('risk','size')).reset_index()
    y.to_csv(OUT/'calibration_stress_summary.csv',index=False)


def battery_shift():
    rows=[]
    for p in sorted((OUT/'battery').glob('*_scores.csv')):
        x=pd.read_csv(p)
        for lead,g in x.groupby('lead'):
            o=g[g.role=='oof'].score.to_numpy();th,finite=T.grid_threshold(o,.05,np.arange(3.,181.,3.))
            for (role,model),h in g.groupby(['role','model']):
                s=h.score.to_numpy()
                rows.append(dict(analysis=g.analysis.iloc[0],split=g.split.iloc[0],lead=lead,role=role,model=model,
                    n=len(s),source_threshold=th,source_finite=finite,median_score=np.median(s),
                    q95_score=float(np.sort(s)[int(np.ceil(.95*len(s)))-1]),tail_at_source_threshold=(s>th).mean(),
                    infinite_scores=int(np.isinf(s).sum())))
    pd.DataFrame(rows).to_csv(OUT/'battery_score_shift.csv',index=False)


def target_reference():
    rows=[]
    for name in ['lobo1','lobo2','lobo3']:
        z=np.load(OUT/'battery'/f'{name}_tables.npz');units=z['test_units'];n=len(units);grid=np.arange(3.,181.,3.)
        for lead in [0,15,30,45]:
            src=pd.read_csv(OUT/'battery'/f'{name}_scores.csv')
            src=src[src.lead==lead];old,oldfinite=T.grid_threshold(src[src.role=='oof'].score.to_numpy(),.05,grid)
            allscores=src[src.role=='test_refit'].set_index('unit').loc[units].score.to_numpy()
            for budget in [5,10,19,25]:
                assert budget<n
                for seed in range(2026,2036):
                    perm=np.random.default_rng(seed).permutation(n);cal=perm[:budget];test=perm[budget:]
                    th,finite=T.grid_threshold(allscores[cal],.05,grid);j=int(np.searchsorted(grid,th))
                    oldj=int(np.searchsorted(grid,old));ya=z['test_ya'][test,j];ok=z['test_ok'][test,j]
                    planned=ok&(ya>lead);use=np.where(planned,z['test_ta'][test,j]+lead,z['test_L'][test])
                    oldplanned=z['test_ok'][test,oldj]&(z['test_ya'][test,oldj]>lead)
                    olduse=np.where(oldplanned,z['test_ta'][test,oldj]+lead,z['test_L'][test])
                    assert np.array_equal(~planned,allscores[test]>th)
                    for rho in [5,10,20,50]:
                        rows.append(dict(split=name,lead=lead,rho=rho,budget=budget,seed=seed,n_test=len(test),
                            threshold=th,finite_threshold=finite,source_threshold=old,source_finite=oldfinite,
                            source_risk=float((~oldplanned).mean()),target_risk=float((~planned).mean()),
                            source_cost_rate=np.where(oldplanned,1.,rho).sum()/olduse.sum(),
                            target_cost_rate=np.where(planned,1.,rho).sum()/use.sum()))
    x=pd.DataFrame(rows);x.to_csv(OUT/'target_label_reference.csv',index=False)
    x.groupby(['split','lead','rho','budget']).agg(source_risk=('source_risk','mean'),target_risk=('target_risk','mean'),
        target_sd=('target_risk','std'),target_median=('target_risk','median'),finite_share=('finite_threshold','mean'),
        source_cost=('source_cost_rate','mean'),target_cost=('target_cost_rate','mean')).reset_index().to_csv(OUT/'target_label_reference_summary.csv',index=False)


def cost_change():
    rows=[]
    for ds in ENG+['Battery']:
        x=pd.read_csv(f'results/contrib/{ds}_cost.csv',low_memory=False)
        if ds!='Battery':x=x.assign(analysis='engine')
        x=x[(x.rho==10)&x.policy.isin(['CAT_a0.05','CATc_a0.05','STW_cost','STW_cost_1se'])]
        for (an,lead,pol),g in x.groupby(['analysis','lead_cycles','policy']):
            for rho in [5,10,20,50,100]:
                rows.append(dict(dataset=ds,analysis=an,lead=lead,policy=pol,selection_rho=10,evaluation_rho=rho,
                                 n=len(g),risk=g.fail.mean(),cost_rate=(1+(rho-1)*g.fail.astype(int)).sum()/g.use.sum()))
    pd.DataFrame(rows).to_csv(OUT/'cost_matrix_stress.csv',index=False)


def main():
    assert len(list((OUT/'battery').glob('*_scores.csv')))==8
    battery_shift();target_reference();cost_change();calibration_stress()
    print('PASS isolated score/calibration stress and target-label reference completed.')


if __name__=='__main__':main()
