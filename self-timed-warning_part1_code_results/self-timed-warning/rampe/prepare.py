"""One-time frozen protection and causal context extraction."""
import hashlib,json,sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path.cwd()))
from safe_common import load_dataset
OUT=Path('out/rampe');OUT.mkdir(parents=True,exist_ok=True)


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    target=OUT/'frozen_before.json'
    if target.exists():raise SystemExit('Refusing to reset the frozen protection baseline.')
    old=json.loads(Path('out/research_next/protected_before.json').read_text())
    previous=json.loads(Path('out/research_next/completion_manifest.json').read_text())
    old.update(previous['sha256'])
    old['out/research_next/completion_manifest.json']=digest('out/research_next/completion_manifest.json')
    inputs=json.loads(Path('results/contrib/completion_audit.json').read_text())['input_sha256'];old.update(inputs)
    assert all(digest(p)==h for p,h in old.items())
    target.write_text(json.dumps(old,indent=1),encoding='utf-8')
    rows=[]
    for ds in ['PHM08','FD001','FD002','FD003','FD004']:
        d,_,_=load_dataset(ds)
        first=d.sort_values(['unit','cycle']).groupby('unit').first()
        rows += [dict(dataset=ds,unit=str(u),context=str(int(r.regime)),observed_at_cycle=int(r.cycle),definition='first observed operating regime; fixed rounding in original protocol') for u,r in first.iterrows()]
    n=pd.read_csv('ncm/ncmapss_cycle_summary.csv.gz')
    key=n.subset+'|'+n.part+'|'+n.unit.astype(int).astype(str);ids={k:i+1 for i,k in enumerate(sorted(key.unique()))}
    n['uid']=key.map(ids)
    first=n.sort_values(['uid','cycle']).groupby('uid').first()
    rows += [dict(dataset='NCMAPSS6',unit=str(u),context=str(int(np.round(r.Fc))),observed_at_cycle=int(r.cycle),definition='first observed flight class') for u,r in first.iterrows()]
    b=pd.read_csv('battery/severson_cells.csv')
    rows += [dict(dataset='Battery',unit=r.cell,context=str(r.batch),observed_at_cycle=0,definition='known experiment batch metadata') for r in b.itertuples(index=False)]
    pd.DataFrame(rows).to_csv(OUT/'causal_context.csv',index=False)
    (OUT/'plan_sha256.txt').write_text(digest('rampe/PLAN.md')+'\n',encoding='utf-8')
    print(f'PASS {len(old)} frozen files protected; {len(rows)} causal unit contexts extracted.')


if __name__=='__main__':main()
