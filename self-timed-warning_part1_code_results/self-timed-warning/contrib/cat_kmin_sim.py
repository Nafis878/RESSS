"""Supplement the saved Phase 1 with explicit earliest-of-five rank calibration.

Fixed synthetic rules from the original plan; five disjoint calibration samples,
one common test trajectory. KMIN has an upper bound, not the single-rule lower
bound incorrectly proposed in the plan. No refitted/calibration-selected model.
"""
import os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np
import pandas as pd
import cat as C
import cat_sim as S


def main():
    pools = {}
    for sigma, seed in [(0.4, 2026), (0.15, 2027)]:
        tf, x, valid, _ = S.sim_pool(sigma, 200000, seed)
        for lead in [0,5,10,15]: pools[(f'simulator sigma={sigma}',lead)] = S.sim_scores(tf,x,valid,lead)
    rng = np.random.default_rng(9000); pieces = {lead: [] for lead in [0,5,10,15]}
    for _ in range(100):
        life, d = S.deg_units(2000,rng)
        x = S.ewm_rows(S.deg_estimate(life,d,20,0.04*rng.standard_normal(d.shape)),3)
        mm = S.runmin_rows(x,2)
        for lead in pieces: pieces[lead].append(mm[np.arange(len(life)), life-lead-2])
    for lead, chunks in pieces.items(): pools[('degradation (20, 3, 2)',lead)] = np.concatenate(chunks)
    rows=[]; checks=[]; cell=0
    for (model,lead), scores in pools.items():
        assert np.isfinite(scores).all(), f'Infeasible synthetic trajectories: {model}, lead {lead}; fixed finite-score theorem not applicable'
        sorted_scores=np.sort(scores); size=len(scores)
        for count in [20,50,100,200]:
            for alpha in C.ALPHAS:
                cell+=1; rank=C.order_index(count,alpha)
                if rank>count:
                    rows.append(dict(model=model,lead=lead,n_per_member=count,alpha=alpha,certifiable=False))
                    continue
                rng=np.random.default_rng(9400+cell); pf=[]
                for _ in range(20):
                    draw=scores[rng.integers(0,size,(1000,count,5))]
                    thresholds=np.partition(draw,rank-1,axis=1)[:,rank-1,:]
                    # Same fixed alarm rule: earliest member uses the largest threshold.
                    effective=thresholds.max(axis=1)
                    pf.extend(1-np.searchsorted(sorted_scores,effective,side='right')/size)
                pf=np.array(pf); value=pf.mean(); se=pf.std()/np.sqrt(len(pf)); ok=value<=alpha+3*se
                rows.append(dict(model=model,lead=lead,n_per_member=count,alpha=alpha,certifiable=True,replicates=len(pf),
                                 p_fail=value,mcse=se,upper=alpha,within=ok))
                checks.append(ok)
        print(f'{model}, lead {lead}: earliest-of-five checked',flush=True)
    pd.DataFrame(rows).to_csv('out/contrib/sim_kmin.csv',index=False)
    line=f'{"PASS" if all(checks) else "FAIL"}  fixed-rule KMIN upper bound in {sum(checks)}/{len(checks)} certifiable cells, 20000 replicates each; no single-rule lower bound claimed'
    open('out/contrib/sim_kmin_checks.txt','w').write(line+'\n');print(line)
    if not all(checks): raise SystemExit(1)


if __name__=='__main__': main()
