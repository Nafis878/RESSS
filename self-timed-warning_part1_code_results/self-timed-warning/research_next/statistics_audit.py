"""All-dataset descriptive comparisons and conditional LOBO paired validation.

These post hoc tests cannot establish algorithmic novelty or CV generalization.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import calibration_tools as T
OUT=Path('out/research_next')
ENG=['PHM08','FD001','FD002','FD003','FD004','NCMAPSS6']


def main():
    battery=pd.read_csv('results/contrib/Battery_cost.csv',low_memory=False)
    rows=[]
    for (split,lead,rho),g in battery[battery.analysis=='lobo'].groupby(['split','lead_cycles','rho']):
        a=g[g.policy=='CATc_a0.05'].set_index('unit').sort_index()
        for bname in ['STW_cost','STW_cost_1se']:
            b=g[g.policy==bname].set_index('unit').sort_index();assert a.index.equals(b.index)
            z=T.paired_binary(a.fail,b.fail);point,lo,hi=T.bootstrap_ratio(a.cost,a.use,b.cost,b.use)
            rows.append(dict(split=split,lead=lead,rho=rho,comparator=bname,n=len(a),**z,
                             cost_ratio=point,cost_lo=lo,cost_hi=hi,
                             renewal_contrast=T.renewal_contrast(a.cost,a.use,b.cost,b.use)))
    x=pd.DataFrame(rows);assert len(x)==96
    x['p_holm']=T.holm(x.p.to_numpy());x['reject_holm_05']=x.p_holm<.05
    x.to_csv(OUT/'lobo_paired_validation.csv',index=False)
    effects=pd.read_csv(OUT/'paired_effects.csv');cells=pd.read_csv(OUT/'policy_cells.csv')
    summary=[]
    for (ds,an,comp),g in effects.groupby(['dataset','analysis','comparator']):
        summary.append(dict(dataset=ds,analysis=an,comparator=comp,cells=len(g),
            mean_ratio=g.cost_ratio.mean(),sd_ratio=g.cost_ratio.std(),median_ratio=g.cost_ratio.median(),
            mean_delta_risk=g.delta_risk.mean(),sd_delta_risk=g.delta_risk.std(),median_delta_risk=g.delta_risk.median(),
            rescued_total=int(g.rescued.sum()),harmed_total=int(g.harmed.sum()),
            note='Cost cells reuse units; totals are policy-cell incidences, not independent units'))
    pd.DataFrame(summary).to_csv(OUT/'all_dataset_effects.csv',index=False)
    fold=[]
    for ds in ENG:
        x=pd.read_csv(f'results/contrib/{ds}_cost.csv',low_memory=False)
        for (f,lead,rho),g in x.groupby(['fold','lead_cycles','rho']):
            a=g[g.policy=='CATc_a0.05'];b=g[g.policy=='STW_cost_1se']
            fold.append(dict(dataset=ds,fold=f,lead=lead,rho=rho,
                ratio=T.ratio(a.cost,a.use)/T.ratio(b.cost,b.use),delta_risk=a.fail.mean()-b.fail.mean()))
    z=pd.DataFrame(fold);z.to_csv(OUT/'fold_effects.csv',index=False)
    z.groupby(['dataset','lead','rho']).agg(mean_ratio=('ratio','mean'),sd_ratio=('ratio','std'),median_ratio=('ratio','median'),
        mean_delta_risk=('delta_risk','mean'),sd_delta_risk=('delta_risk','std'),median_delta_risk=('delta_risk','median')).reset_index().to_csv(OUT/'fold_effects_summary.csv',index=False)
    # Keep the original interval-based cell decisions, clearly conditional on fitted predictions.
    import json
    n=json.loads(Path('results/contrib/contrib_numbers.json').read_text());w=[]
    for ds in ENG:
        for comp in ['STW_cost','STW_cost_1se','STW_window']:
            v=n['ds'][ds]['all']['cost']['verdict'][comp]
            w.append(dict(dataset=ds,comparator=comp,wins=v['wins'],ties=v['cells']-v['wins']-v['losses'],losses=v['losses'],dataset_verdict=v['verdict'],
                          note='Legacy paired-bootstrap intervals; no across-cell correction; fixed fitted predictions'))
    pd.DataFrame(w).to_csv(OUT/'win_tie_loss.csv',index=False)
    print('PASS all datasets summarized; 96 LOBO paired risk comparisons corrected together by Holm.')


if __name__=='__main__':main()
