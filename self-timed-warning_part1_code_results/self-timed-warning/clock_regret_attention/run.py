"""Fixed-data, fixed-seed attention proposal experiment and paired analysis."""
from fractions import Fraction as F
import copy
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
from torch import nn
from clock_regret_attention.core import focused_pair,optimal_premium_focus
from clock_regret_attention.models import AttentionRanker,MLPRanker,features

OUT=Path('out/clock_regret_attention')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protect():
    hashes=json.loads((OUT/'protected_before.json').read_text())
    assert len(hashes)==1025 and all(sha(p)==v for p,v in hashes.items())
    assert sha('clock_regret_attention/PLAN.md')==(OUT/'PLAN.md.sha256').read_text().strip()
    return len(hashes)


def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,default=str),encoding='utf-8')


def generate(count,seed,shift=False):
    rng=np.random.default_rng(seed); records=[]
    for i in range(count):
        if shift:
            a=int(rng.integers(40,81)); b=a+int(rng.integers(40,101))
            h=list(map(int,rng.integers(4,a,8)))
            q=[int(hi*rng.integers(1,4)) for hi in h]
            known_q=list(map(int,rng.integers(100,601,2)))
        else:
            a=int(rng.integers(16,49)); b=a+int(rng.integers(5,41))
            h=list(map(int,rng.integers(1,a,8)))
            q=list(map(int,np.maximum(1,np.rint(np.exp(rng.uniform(0,5,8))))))
            known_q=list(map(int,rng.integers(5,201,2)))
        h+=list(map(int,rng.integers(a+1,b+1,2))); q+=known_q; f=[False]*8+[True]*2
        r=dict(case=i,h=h,f=f,a=a,b=b,q=q,shift=shift)
        answer=focused_pair(h,f,a,b,q,range(8))
        r['exact']=str(answer.lower)
        r['label']=[int(j in answer.selected_failures) for j in range(10)]
        records.append(r)
    return records


def tensors(records):
    return (torch.tensor(np.stack([features(r) for r in records])),
            torch.tensor([r['label'] for r in records],dtype=torch.float32))


def train(kind,seed,training,validation):
    torch.manual_seed(seed)
    model=(AttentionRanker if kind=='attention' else MLPRanker)()
    optimizer=torch.optim.Adam(model.parameters(),lr=.002)
    lossfn=nn.BCEWithLogitsLoss()
    x,y=tensors(training); xv,yv=tensors(validation)
    best=float('inf'); state=None; history=[]; start=time.perf_counter()
    for epoch in range(25):
        model.train(); order=torch.randperm(len(x)); total=0.
        for batch in order.split(64):
            optimizer.zero_grad(); loss=lossfn(model(x[batch])[:,:8],y[batch,:8])
            loss.backward(); optimizer.step(); total+=float(loss.detach())*len(batch)
        model.eval()
        with torch.no_grad(): val=float(lossfn(model(xv)[:,:8],yv[:,:8]))
        if val<best: best=val; state=copy.deepcopy(model.state_dict())
        history.append(dict(epoch=epoch+1,training_bce=total/len(x),validation_bce=val))
    model.load_state_dict(state); model.eval(); folder=OUT/'weights'; folder.mkdir(exist_ok=True)
    torch.save(state,folder/f'{kind}-{seed}.pt')
    save(f'{kind}-{seed}-training.json',dict(seed=seed,kind=kind,parameters=sum(p.numel() for p in model.parameters()),
        elapsed_seconds=time.perf_counter()-start,selected_epoch=min(history,key=lambda r:r['validation_bce'])['epoch'],history=history))
    print(f'{kind} seed {seed}: validation BCE {best:.5f}',flush=True)
    return model


def baselines(r):
    h,f,a,b,q=r['h'],r['f'],r['a'],r['b'],r['q']
    single={i:focused_pair(h,f,a,b,q,[i]).lower for i in range(8)}
    rng=np.random.default_rng(20261200+1000*int(r['shift'])+r['case'])
    return dict(premium=sorted(range(8),key=lambda i:(-q[i],h[i],i))[:4],
        horizon=sorted(range(8),key=lambda i:(h[i],-q[i],i))[:4],
        premium_per_use=sorted(range(8),key=lambda i:(-F(q[i],h[i]+1),i))[:4],
        singleton=sorted(range(8),key=lambda i:(-single[i],i))[:4],
        random=list(map(int,rng.permutation(8)[:4])))


def evaluate(records,models,split):
    rows=[]; x,_=tensors(records)
    for method in ['attention','mlp']:
        for seed,model in models[method].items():
            start=time.perf_counter()
            with torch.no_grad(): logits=model(x).numpy()
            elapsed=time.perf_counter()-start
            for r,logit in zip(records,logits):
                focus=sorted(range(8),key=lambda i:(-float(logit[i]),i))[:4]
                ans=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],focus)
                exact=F(r['exact']); assert ans.lower<=exact<=ans.upper
                rows.append(dict(split=split,case=r['case'],method=method,seed=seed,focus=focus,
                    lower=str(ans.lower),upper=str(ans.upper),factor=str(ans.factor),
                    exact=str(exact),log_gap=float(np.log(float(exact/ans.lower))),
                    full_optimum_covered=ans.lower==exact,forward_batch_seconds=elapsed,
                    witness=ans.witness))
    for r in records:
        for method,focus in baselines(r).items():
            ans=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],focus); exact=F(r['exact'])
            assert ans.lower<=exact<=ans.upper
            rows.append(dict(split=split,case=r['case'],method=method,seed=None,focus=focus,
                lower=str(ans.lower),upper=str(ans.upper),factor=str(ans.factor),exact=str(exact),
                log_gap=float(np.log(float(exact/ans.lower))),full_optimum_covered=ans.lower==exact,
                witness=ans.witness))
    save(f'{split}-evaluation.json',rows)
    return rows


def statistical_analysis(rows):
    rng=np.random.default_rng(20261300); contrasts=[]; descriptions=[]
    for split in ['id','shift']:
        relevant=[r for r in rows if r['split']==split]
        methods=sorted({r['method'] for r in relevant}); per_method={}
        for method in methods:
            matrix=[[r for r in relevant if r['method']==method and r['case']==i] for i in range(300)]
            values=np.asarray([np.mean([r['log_gap'] for r in group]) for group in matrix])
            per_method[method]=values
            factors=[np.mean([float(F(r['factor'])) for r in group]) for group in matrix]
            coverage=[np.mean([r['full_optimum_covered'] for r in group]) for group in matrix]
            descriptions.append(dict(split=split,method=method,mean_log_gap=float(values.mean()),
                median_log_gap=float(np.median(values)),mean_certificate_factor=float(np.mean(factors)),
                mean_optimum_coverage=float(np.mean(coverage))))
        for baseline in ['premium','mlp']:
            difference=per_method['attention']-per_method[baseline]
            observed=abs(float(difference.mean()))
            draws=np.abs((rng.choice([-1,1],size=(9999,300))*difference).mean(axis=1))
            p=(1+int(np.sum(draws>=observed-1e-15)))/10000
            boots=difference[rng.integers(0,300,size=(2000,300))].mean(axis=1)
            ci=np.quantile(boots,[.025,.975])
            contrasts.append(dict(split=split,baseline=baseline,mean_attention_minus_baseline=float(difference.mean()),
                bootstrap_95_ci=list(map(float,ci)),raw_p=p,
                win_tie_loss=[int(np.sum(difference<-1e-12)),int(np.sum(abs(difference)<=1e-12)),int(np.sum(difference>1e-12))],
                unit='independent held-out cohort; average over three model seeds',
                test='Monte Carlo paired sign flips of mean difference, two-sided, 9999 draws'))
    ordered=sorted(range(len(contrasts)),key=lambda i:contrasts[i]['raw_p']); previous=0.
    for rank,i in enumerate(ordered):
        previous=max(previous,min(1.,(len(contrasts)-rank)*contrasts[i]['raw_p']))
        contrasts[i]['holm_p']=previous
    save('statistical_tests.json',contrasts); save('method_summary.json',descriptions)
    print(json.dumps(contrasts,indent=2),flush=True)


def math_checks():
    rng=np.random.default_rng(20261111); rows=[]
    for case in range(500):
        a=int(rng.integers(10,40));b=a+int(rng.integers(5,30))
        h=list(map(int,rng.integers(1,a,8)))+[b]; f=[False]*8+[True]
        q=list(map(int,rng.integers(1,100,9))); focus=list(map(int,rng.permutation(8)[:4]))
        ans=focused_pair(h,f,a,b,q,focus); full=focused_pair(h,f,a,b,q,range(8))
        premium=focused_pair(h,f,a,b,q,optimal_premium_focus(h,f,a,b,q,4))
        assert ans.lower<=full.lower<=ans.upper and premium.factor<=ans.factor
        rows.append(dict(case=case,h=h,f=f,a=a,b=b,q=q,focus=focus,lower=str(ans.lower),upper=str(ans.upper),
                         exact=str(full.lower),premium_factor=str(premium.factor),focus_factor=str(ans.factor)))
    save('math_focus_checks.json',rows)
    sharp=[]
    for a in [2,3,10,100,1000,10000]:
        b=a+1; focus=focused_pair([a-1,b],[False,True],a,b,[1,3],[])
        full=focused_pair([a-1,b],[False,True],a,b,[1,3],[0])
        assert full.lower/focus.lower==F(5,4)*(1-F(1,2*b))
        sharp.append(dict(a=a,b=b,factor=str(focus.factor),exact_to_focus=str(full.lower/focus.lower)))
    save('sharpness.json',sharp)


def main():
    protect(); torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    training=generate(1600,20261101); validation=generate(200,20261102)
    tests=dict(id=generate(300,20261103),shift=generate(300,20261104,True))
    save('training_inputs.json',training);save('validation_inputs.json',validation)
    for split,records in tests.items():save(f'{split}-inputs.json',records)
    models={kind:{seed:train(kind,seed,training,validation) for seed in [11,22,33]} for kind in ['attention','mlp']}
    rows=[]
    for split,records in tests.items(): rows.extend(evaluate(records,models,split))
    statistical_analysis(rows); math_checks(); protect()
    save('run_summary.json',dict(training_cohorts=1600,validation_cohorts=200,held_out_cohorts=600,
        model_seeds=[11,22,33],epochs=25,focus_budget=4,protected_artifacts_unchanged=1025,
        torch_version=torch.__version__,sealed_lifetimes_used=False))


if __name__=='__main__':main()
