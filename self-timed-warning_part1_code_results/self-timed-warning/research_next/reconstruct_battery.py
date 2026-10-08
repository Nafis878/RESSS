"""Replay the frozen selected battery signal; record diagnostic scores without retuning.

Two queues cover disjoint original splits. Outputs are isolated; frozen evidence
is read-only. Every final CAT/CAT-c decision must match the frozen counterpart.
"""
import ast
import hashlib
import json
import os
import sys
import time
from pathlib import Path
ARGS=sys.argv[1:];sys.argv=sys.argv[:1]
sys.path.insert(0,os.getcwd());sys.path.insert(0,str(Path('contrib').resolve()))
import numpy as np
import pandas as pd
import audit_confirmations as AC
import audit_battery_cost_nested as BN
import battery_warning as BW
import eol_window2 as W
import cat as C
import cat_battery as CB

OUT=Path('out/research_next/battery');OUT.mkdir(parents=True,exist_ok=True)


def fit(S,L,kap,tr,tg,cap):
    B=AC.battery_blocks(S,kap,L,tr)
    F,Y=BW.features(B[B.cell.isin(np.concatenate([tr,tg]))],tr)
    X=np.vstack([F[u] for u in tr]);y=np.concatenate([Y[u] for u in tr])
    m=W.gbm(X,y,cap/kap)
    return {u:(m.predict(F[u])[:-1],Y[u][:-1]) for u in tg}


def run_split(S,L,an,name,tr,te,seed,settings,frozen):
    started=time.time();sel=settings[(settings.split==name)&(settings.alpha==.05)&(settings.lead_cycles==0)].iloc[0]
    cap,sp,k=ast.literal_eval(sel.setting)
    kap=AC.kap_rule(L[tr].values);assert kap==sel.kappa
    inner=np.array_split(np.random.default_rng(seed).permutation(tr),5)
    assert not set(tr)&set(te)
    records=[];cal_tabs=[];model_tabs=[]
    for i,iu in enumerate(inner):
        itr=np.setdiff1d(tr,iu);ki=AC.kap_rule(L[itr].values)
        p=fit(S,L,ki,itr,np.concatenate([iu,te]),cap)
        ca=CB.tab_c({u:p[u] for u in iu},ki,sp,k,BN.TAUS_C)
        tt=CB.tab_c({u:p[u] for u in te},ki,sp,k,BN.TAUS_C)
        cal_tabs.append(ca);model_tabs.append(tt)
        for lead in BN.LEADS_C:
            for role,tab in [('oof',ca),('test_inner',tt)]:
                for u,s in zip(tab[0],C.scores_from_table(tab,BN.TAUS_C,lead)):
                    records.append(dict(analysis=an,split=name,model=i,role=role,lead=lead,unit=u,score=s))
    p=fit(S,L,kap,tr,te,cap);final=CB.tab_c(p,kap,sp,k,BN.TAUS_C)
    cal=BN.cat(cal_tabs)
    checks=0
    for lead in BN.LEADS_C:
        so=C.scores_from_table(cal,BN.TAUS_C,lead);st=C.scores_from_table(final,BN.TAUS_C,lead)
        for u,s in zip(final[0],st):records.append(dict(analysis=an,split=name,model=-1,role='test_refit',lead=lead,unit=u,score=s))
        for alpha in C.ALPHAS:
            th,cert=C.tau_hat(so,alpha);j0=C.certified_column(BN.TAUS_C,th,cert)
            for rho in [5,10,20,50]:
                j1=C.cost_aware_column(cal,BN.TAUS_C,j0,lead,rho,C.cost_1cycle)
                for pol,j in [(f'CAT_a{alpha}',j0),(f'CATc_a{alpha}',j1)]:
                    c,t,planned=CB.R.cost_of(final[1][:,j],final[2][:,j],final[3][:,j],final[4],lead,rho)
                    ref=frozen[(frozen.split==name)&(frozen.lead_cycles==lead)&(frozen.rho==rho)&(frozen.policy==pol)].set_index('unit').loc[final[0]]
                    assert np.array_equal(c,ref.cost.to_numpy()) and np.allclose(t,ref.use.to_numpy(),rtol=0,atol=1e-10),f'{name}/{pol}/{lead}/{rho}: replay differs'
                    assert np.array_equal(~planned,ref.fail.to_numpy()),f'{name}/{pol}: failure differs'
                    checks+=len(ref)
    pd.DataFrame(records).to_csv(OUT/f'{name}_scores.csv',index=False)
    np.savez_compressed(OUT/f'{name}_tables.npz',cal_units=np.asarray(cal[0],str),test_units=np.asarray(final[0],str),
        cal_ok=cal[1],cal_ya=cal[2],cal_ta=cal[3],cal_L=cal[4],test_ok=final[1],test_ya=final[2],test_ta=final[3],test_L=final[4])
    line=f'PASS {name}: {checks} frozen CAT/CAT-c unit decisions match; setting {(cap,sp,k)}, {time.time()-started:.0f}s'
    (OUT/f'{name}_check.txt').write_text(line+'\n');print(line,flush=True)


def main():
    queue=int(ARGS[0]);S,L=AC.battery_cycles();units=np.sort(L.index.to_numpy())
    settings=pd.read_csv('results/contrib/Battery_settings.csv');frozen=pd.read_csv('results/contrib/Battery_cost.csv',low_memory=False)
    splits=[s for s in AC.battery_splits(units) if s[0] in ['cv123','lobo']]
    for i,args in enumerate(splits):
        if i%2!=queue:continue
        run_split(S,L,*args,settings,frozen)


if __name__=='__main__':main()
