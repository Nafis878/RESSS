"""Retrospective labelled-validation arbitration among frozen policy outcomes."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
sys.path.insert(0,str(Path(__file__).resolve().parent))
import core as R

OUT=Path('out/rampe')
DOMAINS=['PHM08','FD001','FD002','FD003','FD004','NCMAPSS6','Battery']
POOL=['STW_cost','CAT_a0.05','CATc_a0.05','STW_cost_1se']
BASE=['plain','CAT','CATc','1SE']
SELECTORS=['conventional','RAMPE','RAMPE_no_reliability','RAMPE_no_stability','RAMPE_no_calibration','RAMPE_no_transfer','RAMPE_no_abstention','RAMPE_no_context','normalized','uncertainty','rank']
ENSEMBLES={'uniform_ensemble':'uniform','reliability_ensemble':'reliability','random_weights':'random','cost_weights':'inverse_cost'}


def load_groups():
    ctx=pd.read_csv(OUT/'causal_context.csv',dtype={'unit':str,'context':str})
    for ds in DOMAINS:
        f=pd.read_csv(f'results/contrib/{ds}_cost.csv',low_memory=False)
        if ds!='Battery':f=f.assign(analysis='engine',split=f.fold.astype(str))
        f['unit']=f.unit.astype(str);f['split']=f.split.astype(str)
        q=ctx[ctx.dataset==ds].set_index('unit').context
        strata=q.nunique()
        for (analysis,split,lead,rho),g in f[f.policy.isin(POOL)].groupby(['analysis','split','lead_cycles','rho']):
            units=np.sort(g.unit.unique())
            matrices=[]
            for field in ['cost','use','fail']:
                z=g.pivot(index='unit',columns='policy',values=field).loc[units,POOL]
                assert not z.isna().any().any()
                matrices.append(z.to_numpy(dtype=bool if field=='fail' else float))
            context=q.loc[units].to_numpy()
            yield dict(dataset=ds,analysis=analysis,split=split,lead=lead,rho=rho),units,context,strata,*matrices


def decisions(ev,glob,context,u,seed):
    n=len(context);actions={};abstains={}
    for j,name in enumerate(BASE):actions[name]=np.full(n,j);abstains[name]=np.zeros(n,bool)
    for kind in SELECTORS:
        a=[];b=[]
        for x in context:
            e=glob if kind in ['conventional','RAMPE_no_context'] else ev[str(x)]
            j,ab=R.choose(e,kind);a.append(j);b.append(ab)
        actions[kind]=np.array(a);abstains[kind]=np.array(b)
    for name,kind in ENSEMBLES.items():
        actions[name]=np.array([R.draw_policy(R.weights(ev[str(x)],kind,seed=seed),r) for x,r in zip(context,u)])
        abstains[name]=np.zeros(n,bool)
    return actions,abstains


def fallback_details(c,t,f,action,ab,conventional):
    i=np.arange(len(c));a=action;b=conventional
    return dict(avoided_failures=int((ab&f[i,b]&~f[i,a]).sum()),introduced_failures=int((ab&~f[i,b]&f[i,a]).sum()),
        false_abstentions=int((ab&~f[i,b]&(c[i,b]/t[i,b]<c[i,a]/t[i,a]-1e-12)).sum()),
        abstention_cost_difference=float((c[i,a]-c[i,b])[ab].sum()),abstention_use_difference=float((t[i,a]-t[i,b])[ab].sum()))


def run():
    results=[];meta=[];paired=[];partition=[];case=0
    for info,units,context,strata,c,t,f in load_groups():
        for seed in range(2026,2036):
            case+=1;perm=np.random.default_rng(seed).permutation(len(units));m=len(units)//2
            val,te=perm[:m],np.sort(perm[m:]);assert not set(val)&set(te)
            rng=np.random.default_rng(seed+10000);u=rng.random(len(te))
            glob=R.evidence(c[val],t[val],f[val],context[val],'pooled',seed=seed,strata=strata,pooled=True)
            ev={str(x):R.evidence(c[val],t[val],f[val],context[val],x,seed=seed,strata=strata) for x in np.unique(context[te])}
            actions,abs_=decisions(ev,glob,context[te],u,seed)
            for name,a in actions.items():
                mm=R.metrics(c[te],t[te],f[te],a,abs_[name])
                selected_risk=np.array([ev[str(x)].risk[j] for x,j in zip(context[te],a)])
                mm['calibration_gap']=mm['risk']-float(selected_risk.mean())
                mm['selected_entropy']=float(-sum(v*np.log(v) for v in np.bincount(a,minlength=4)/len(a) if v))
                for j in range(4):mm[f'authority_{BASE[j]}']=float((a==j).mean())
                mm.update(fallback_details(c[te],t[te],f[te],a,abs_[name],actions['conventional']))
                results.append(dict(case=case,seed=seed,n_validation=m,method=name,**info,**mm))
            for x,e in ev.items():
                target=te[context[te].astype(str)==x];rr=c[target].sum(0)/t[target].sum(0);risk=f[target].mean(0)
                acceptable=(rr<=rr[3]+1e-12)&(risk<=.05)
                feat=e.features()
                for k in range(4):meta.append(dict(case=case,seed=seed,context=x,policy=k,acceptable=int(acceptable[k]),target_rate=rr[k],target_risk=risk[k],**info,**{f'x{j}':feat[k,j] for j in range(feat.shape[1])}))
            for i,idx in enumerate(te):
                row=dict(case=case,seed=seed,unit=units[idx],context=str(context[idx]),**info)
                for name in ['RAMPE','1SE','conventional','CATc']:
                    j=actions[name][i]
                    row.update({f'{name}_cost':c[idx,j],f'{name}_use':t[idx,j],f'{name}_fail':f[idx,j],f'{name}_policy':j})
                paired.append(row)
            partition += [dict(case=case,role='validation' if i in set(val) else 'test',seed=seed,unit=unit,**info) for i,unit in enumerate(units)]
        if info['lead']==0 and info['rho']==10:print(f"Completed {info['dataset']}/{info['analysis']}/{info['split']}",flush=True)
    x=pd.DataFrame(results);x.to_csv(OUT/'real_results.csv.gz',index=False)
    z=pd.DataFrame(meta);z.to_csv(OUT/'meta_features.csv.gz',index=False)
    p=pd.DataFrame(paired);p.to_csv(OUT/'paired_units.csv.gz',index=False)
    pd.DataFrame(partition).to_csv(OUT/'partitions.csv.gz',index=False)
    print(f'PASS {case} real arbitration episodes, {len(results)} method outcomes; learned gate next.',flush=True)
    learned(z,p,x)


def learned(z,paired,results):
    feat=[f'x{i}' for i in range(8)];pred=[];modelrows=[]
    for ds in DOMAINS:
        tr=z[z.dataset!=ds];te=z[z.dataset==ds].copy()
        assert not set(tr.dataset)&{ds}
        if tr.acceptable.nunique()<2:te['p_accept']=float(tr.acceptable.iloc[0])
        else:
            model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,max_iter=1000,random_state=2026))
            model.fit(tr[feat],tr.acceptable);te['p_accept']=model.predict_proba(te[feat])[:,1]
            modelrows.append(dict(heldout_dataset=ds,training_domains='|'.join(sorted(tr.dataset.unique())),training_rows=len(tr),coefs=model[-1].coef_.tolist(),intercept=model[-1].intercept_.tolist()))
        pred.append(te)
    z=pd.concat(pred);z.to_csv(OUT/'learned_predictions.csv.gz',index=False)
    (OUT/'learned_models.json').write_text(__import__('json').dumps(modelrows,indent=1),encoding='utf-8')
    lookup=z.set_index(['case','context','policy']);lr=[];lp=[]
    # Reuse same partitions and fixed candidates; no test target outcome enters selection.
    for info,units,context,strata,c,t,f in load_groups():
        for seed in range(2026,2036):
            case=int(results[(results.dataset==info['dataset'])&(results.analysis==info['analysis'])&(results.split.astype(str)==str(info['split']))&(results.lead==info['lead'])&(results.rho==info['rho'])&(results.seed==seed)].case.iloc[0])
            perm=np.random.default_rng(seed).permutation(len(units));te=np.sort(perm[len(units)//2:])
            choices={};abs_={}
            for ctx in np.unique(context[te]):
                rows=lookup.loc[(case,str(ctx))].sort_index()
                eligible=rows.p_accept.to_numpy()>=.5
                j=int(np.argmin(np.where(eligible,rows.x0.to_numpy()+rows.x4.to_numpy(),np.inf))) if eligible.any() else 3
                choices[str(ctx)]=j;abs_[str(ctx)]=not eligible.any()
            a=np.array([choices[str(ctx)] for ctx in context[te]]);ab=np.array([abs_[str(ctx)] for ctx in context[te]])
            mm=R.metrics(c[te],t[te],f[te],a,ab)
            lr.append(dict(case=case,seed=seed,n_validation=len(units)//2,method='learned',**info,**mm))
            for i,idx in enumerate(te):lp.append(dict(case=case,unit=units[idx],learned_cost=c[idx,a[i]],learned_use=t[idx,a[i]],learned_fail=f[idx,a[i]],learned_policy=a[i]))
    pd.concat([results,pd.DataFrame(lr)],ignore_index=True).to_csv(OUT/'real_results.csv.gz',index=False)
    pd.DataFrame(lp).to_csv(OUT/'learned_units.csv.gz',index=False)
    print(f'PASS learned empirical-acceptability gates evaluated on {len(lr)} episodes with dataset held out.',flush=True)


if __name__=='__main__':run()
