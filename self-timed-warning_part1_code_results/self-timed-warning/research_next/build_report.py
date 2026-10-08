"""Build isolated descriptive tables and scientific figures from actual outputs."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path('out/research_next')


def md(df):
    def fmt(x):
        if isinstance(x,(float,np.floating)):return f'{x:.4f}'
        return str(x)
    return '\n'.join(['| '+' | '.join(map(str,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']+
                     ['| '+' | '.join(fmt(x) for x in row)+' |' for row in df.itertuples(index=False,name=None)])


def main():
    cells=pd.read_csv(OUT/'policy_cells.csv')
    effects=pd.read_csv(OUT/'all_dataset_effects.csv')
    x=cells[cells.analysis=='engine'].groupby(['dataset','policy']).fragile.sum().unstack()
    x=x[['CAT_a0.05','CATc_a0.05','STW_cost','STW_cost_1se']].reset_index()
    (OUT/'fragility_table.md').write_text(md(x)+'\n',encoding='utf-8')
    z=effects[effects.comparator=='STW_cost_1se'][['dataset','analysis','mean_ratio','sd_ratio','median_ratio','mean_delta_risk','sd_delta_risk','median_delta_risk']]
    (OUT/'effects_table.md').write_text(md(z)+'\n',encoding='utf-8')
    stress=pd.read_csv(OUT/'calibration_stress.csv.gz',low_memory=False)
    z=stress[(stress.analysis=='engine')&(stress.dT==1)&(stress.alpha==.05)&(stress.noise_cycles==0)&(stress.calibration_fraction==1)]
    z=z.groupby(['dataset','target_score_shift']).risk.mean().unstack().reset_index()
    (OUT/'score_stress_table.md').write_text(md(z)+'\n',encoding='utf-8')
    z=stress[(stress.alpha==.05)&(stress.target_score_shift==0)&(stress.calibration_fraction==1)]
    z=z.groupby(['dataset','analysis','dT','noise_cycles']).agg(mean_risk=('risk','mean'),sd_risk=('risk','std'),median_risk=('risk','median')).reset_index()
    z.to_csv(OUT/'noise_stress_summary.csv',index=False)
    shifted=pd.read_csv(OUT/'battery_score_shift.csv')
    target=pd.read_csv(OUT/'target_label_reference_summary.csv')
    fig,ax=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
    # Same pooled source threshold for every model; not separate model certificates.
    for i,name in enumerate(['lobo1','lobo2','lobo3']):
        g=shifted[(shifted.split==name)&(shifted.lead==0)]
        o=g[g.role=='oof'];inner=g[g.role=='test_inner'];refit=g[g.role=='test_refit']
        means=[np.average(o.tail_at_source_threshold,weights=o.n),inner.tail_at_source_threshold.mean(),refit.tail_at_source_threshold.iloc[0]]
        ax[0].bar(np.arange(3)+(i-1)*.24,means,width=.23,label=f'Batch {i+1}')
    ax[0].axhline(.05,color='black',ls='--',lw=1,label='5% reference')
    ax[0].set_xticks(np.arange(3),['Source OOF','Target inner\nmodels (mean)','Target refit'])
    ax[0].set_ylabel('Tail fraction at pooled source threshold')
    ax[0].set_title('Transfer shift persists across inner models')
    ax[0].set_ylim(0,.65);ax[0].legend(fontsize=8)
    for name in ['lobo1','lobo2','lobo3']:
        g=target[(target.split==name)&(target.lead==0)&(target.rho==10)]
        ax[1].plot(g.budget,g.target_risk,marker='o',label=f'Batch {name[-1]}')
    ax[1].axhline(.05,color='black',ls='--',lw=1)
    ax[1].axvspan(4,10.5,color='grey',alpha=.15)
    ax[1].text(7.2,.12,'Rank infeasible;\nmaximum-grid fallback',ha='center',fontsize=8)
    ax[1].set_ylim(-.01,.15);ax[1].set_xticks([5,10,19,25])
    ax[1].set_xlabel('Completed target lives used for calibration')
    ax[1].set_ylabel('Held-out failure fraction, mean of 10 resamples')
    ax[1].set_title('Existing target-calibration reference')
    ax[1].legend(fontsize=8)
    fig.suptitle('Battery diagnostics: zero lead; source alpha = 0.05',fontsize=12)
    fig.savefig(OUT/'battery_diagnostics.png',dpi=180)
    fig.savefig(OUT/'battery_diagnostics.svg')
    plt.close(fig)
    print('PASS tables and standalone PNG/SVG scientific figure generated.')


if __name__=='__main__':main()
