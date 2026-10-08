"""Read-only scientific audit of existing sources and frozen numerical outputs.

Writes only out/research_next. No model fitting or policy selection occurs here.
"""
import ast
import hashlib
import json
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path('out/research_next')
OUT.mkdir(parents=True, exist_ok=True)
ENG = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6']
POL = ['STW_cost', 'STW_cost_1se', 'STW_window', 'CAT_a0.05', 'CATc_a0.05',
       'CATc_plainset_a0.05', 'CATc_bonf_a0.05', 'CATc_a0.01', 'CATc_a0.02', 'CATc_a0.1']


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inventory():
    protected = {}
    # Protect frozen outputs, existing contribution outputs, manuscripts and implementation.
    for folder in ['results', 'out/contrib', 'paper5', 'paper6', 'paper7', 'docs_contrib', 'contrib', 'kam', 'tools']:
        for p in sorted(Path(folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.lock':
                protected[p.as_posix()] = digest(p)
    for p in Path('.').glob('*'):
        if p.is_file() and p.suffix in ['.py', '.js', '.sh', '.md', '.txt']:
            protected[p.as_posix()] = digest(p)
    (OUT/'protected_before.json').write_text(json.dumps(protected, indent=1), encoding='utf-8')
    src, symbols = [], {}
    for p in sorted(Path('.').rglob('*')):
        if not p.is_file() or p.suffix not in ['.py','.js','.sh']: continue
        if any(part in ['.venv','out','results','.git','research_next','__pycache__'] for part in p.parts): continue
        code=p.read_text(encoding='utf-8-sig'); entry=dict(path=p.as_posix(),lines=len(code.splitlines()),sha256=digest(p))
        if p.suffix == '.py':
            tree=ast.parse(code,filename=str(p))
            symbols[p.as_posix()] = {'doc': ast.get_docstring(tree),
                'functions': [{'name':n.name,'line':n.lineno,'end':n.end_lineno,'doc':ast.get_docstring(n)}
                              for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))],
                'imports': [ast.unparse(n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]}
            entry['functions']=len(symbols[p.as_posix()]['functions'])
        src.append(entry)
    pd.DataFrame(src).to_csv(OUT/'source_inventory.csv', index=False)
    (OUT/'source_symbols.json').write_text(json.dumps(symbols,indent=1),encoding='utf-8')
    outputs=[]
    for p in sorted(Path('results').rglob('*')):
        if not p.is_file(): continue
        row=dict(path=p.as_posix(),bytes=p.stat().st_size,sha256=digest(p),read='bytes')
        if p.name.endswith(('.csv','.csv.gz')):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', pd.errors.DtypeWarning)
                x=pd.read_csv(p,low_memory=False)
            row.update(read='all CSV rows',rows=len(x),columns='|'.join(map(str,x.columns)),missing=int(x.isna().sum().sum()))
        elif p.suffix=='.json':
            x=json.loads(p.read_text(encoding='utf-8-sig'));row.update(read='JSON parsed',keys='|'.join(map(str,x)) if isinstance(x,dict) else f'list:{len(x)}')
        outputs.append(row)
    pd.DataFrame(outputs).to_csv(OUT/'frozen_output_inventory.csv',index=False)
    print(f'Inventoried {len(src)} source files and read {len(outputs)} frozen artifacts; protected {len(protected)} files.',flush=True)


def decisions():
    details, pairs, setting_changes = [], [], []
    for ds in ENG+['Battery']:
        x=pd.read_csv(f'results/contrib/{ds}_cost.csv',low_memory=False)
        if ds!='Battery': x=x.assign(analysis='engine',split=x.fold)
        x=x[x.policy.isin(POL)].copy()
        for (an,lead,rho,pol),g in x.groupby(['analysis','lead_cycles','rho','policy']):
            details.append(dict(dataset=ds,analysis=an,lead=lead,rho=rho,policy=pol,n=len(g),failures=int(g.fail.sum()),
                risk=float(g.fail.mean()),cost_rate=g.cost.sum()/g.use.sum(),mean_use=g.use.mean(),
                median_notice=g.rul_at_alarm.median(),mean_notice=g.rul_at_alarm.mean(),
                fragile=int(g.groupby('split').fail.any().sum()),splits=g.split.nunique()))
        for (an,lead,rho),g in x.groupby(['analysis','lead_cycles','rho']):
            piv={p:h.set_index(['split','unit']).sort_index() for p,h in g.groupby('policy')}
            a=piv['CATc_a0.05']
            for bname in ['CAT_a0.05','STW_cost','STW_cost_1se','STW_window','CATc_plainset_a0.05','CATc_bonf_a0.05']:
                b=piv[bname]; assert a.index.equals(b.index)
                pairs.append(dict(dataset=ds,analysis=an,lead=lead,rho=rho,comparator=bname,n=len(a),
                    delta_risk=float(a.fail.mean()-b.fail.mean()),
                    rescued=int((~a.fail & b.fail).sum()),harmed=int((a.fail & ~b.fail).sum()),
                    cost_ratio=(a.cost.sum()/a.use.sum())/(b.cost.sum()/b.use.sum()),
                    mean_use_difference=float((a.use-b.use).mean()),
                    notice_difference=float((a.rul_at_alarm-b.rul_at_alarm).mean())))
            # Tau comparison is meaningful only within the same setting for CAT and CAT-c.
            b=piv['CAT_a0.05']; assert (a.tau>=b.tau).all() and (~a.fail | b.fail).all()
            setting_changes.append(dict(dataset=ds,analysis=an,lead=lead,rho=rho,
                catc_threshold_increased=int((a.tau>b.tau).sum()),units=len(a),
                same_as_1se=int(((a.cost==piv['STW_cost_1se'].cost)&np.isclose(a.use,piv['STW_cost_1se'].use)).sum())))
    pd.DataFrame(details).to_csv(OUT/'policy_cells.csv',index=False)
    pd.DataFrame(pairs).to_csv(OUT/'paired_effects.csv',index=False)
    pd.DataFrame(setting_changes).to_csv(OUT/'catc_changes.csv',index=False)
    # Batch analysis isolates which held-out batch generates the pooled transfer failure.
    b=pd.read_csv('results/contrib/Battery_cost.csv',low_memory=False)
    b=b[b.policy.isin(POL)]
    b['batch']=b.unit.str.extract(r'^b(\d)').astype(int)
    rows=[]
    for (an,batch,lead,rho,pol),g in b.groupby(['analysis','batch','lead_cycles','rho','policy']):
        rows.append(dict(analysis=an,batch=batch,lead=lead,rho=rho,policy=pol,n=len(g),failures=int(g.fail.sum()),
                         risk=g.fail.mean(),cost_rate=g.cost.sum()/g.use.sum(),median_notice=g.rul_at_alarm.median()))
    pd.DataFrame(rows).to_csv(OUT/'battery_by_batch.csv',index=False)


def score_diagnostics():
    rows, setting = [], []
    for ds in ENG:
        x=pd.read_csv(f'results/contrib/{ds}_scores.csv.gz')
        for (fold,lead,dt),z in x.groupby(['fold','lead_cycles','dT']):
            for key,g in z.groupby('setting'):
                o=g[g.role=='oof'].score.to_numpy(); t=g[g.role=='test'].score.to_numpy()
                n=len(o); rank=int(np.ceil((n+1)*.95-1e-9)); th=np.sort(o)[rank-1] if rank<=n else np.inf
                rows.append(dict(dataset=ds,fold=fold,lead=lead,dT=dt,setting=key,selected=bool(g.selected.iloc[0]),
                    n_cal=n,n_test=len(t),threshold=th,cal_tail=(o>th).mean(),test_tail=(t>th).mean(),
                    oof_q95=np.quantile(o,.95),test_q95=np.quantile(t,.95),cal_infinite=int(np.isinf(o).sum()),
                    test_infinite=int(np.isinf(t).sum())))
        c=pd.read_csv(f'results/contrib/{ds}_cost.csv',low_memory=False)
        s=pd.read_csv(f'results/contrib/{ds}_selected.csv').set_index('fold')
        for (fold,lead,rho),g in c[c.policy=='STW_cost'].groupby(['fold','lead_cycles','rho']):
            key=g.setting.iloc[0].rsplit('|',1)[0]
            wkey=str(tuple(int(s.loc[fold,k]) for k in ['cap','span','k']))
            setting.append(dict(dataset=ds,fold=fold,lead=lead,rho=rho,plain_setting=key,cat_setting=wkey,
                                same_setting=ast.literal_eval(key)==ast.literal_eval(wkey)))
    pd.DataFrame(rows).to_csv(OUT/'score_shift.csv',index=False)
    pd.DataFrame(setting).to_csv(OUT/'setting_confound.csv',index=False)


def main():
    inventory(); decisions(); score_diagnostics()
    p=json.loads((OUT/'protected_before.json').read_text())
    assert all(digest(Path(name))==h for name,h in p.items())
    print('PASS: all protected implementation and frozen evidence unchanged.')


if __name__=='__main__': main()
