"""Follow-up retrained ablations, validation selection, fresh confirmation."""
import copy
from fractions import Fraction as F
import json
import time
import numpy as np
import torch
from torch import nn
from clock_regret_attention.run import OUT,protect,save,sha,generate,tensors,baselines
from clock_regret_attention.models import AttentionRanker,MLPRanker
from clock_regret_attention.core import focused_pair
from clock_regret_attention.challenger import greedy_focus


class PooledRanker(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder=nn.Sequential(nn.Linear(12,48),nn.ReLU(),nn.Linear(48,48),nn.ReLU())
        self.score=nn.Sequential(nn.Linear(96,62),nn.ReLU(),nn.Linear(62,1))
    def forward(self,x):
        h=self.encoder(x); pooled=h.mean(dim=1,keepdim=True).expand_as(h)
        return self.score(torch.cat([h,pooled],dim=-1)).squeeze(-1)


class NoBroadcastRanker(AttentionRanker):
    def forward(self,x):
        masked=x.clone(); masked[:,:,6:]=0
        return super().forward(masked)


CLASSES=dict(attention=AttentionRanker,mlp=MLPRanker,pooled=PooledRanker,
             no_broadcast_attention=NoBroadcastRanker)


def train(kind,seed,training,validation):
    torch.manual_seed(seed); model=CLASSES[kind]()
    x,y=tensors(training); xv,yv=tensors(validation)
    opt=torch.optim.Adam(model.parameters(),lr=.002); lossfn=nn.BCEWithLogitsLoss()
    best=float('inf'); state=None; history=[]; start=time.perf_counter()
    for epoch in range(25):
        model.train(); total=0.
        for batch in torch.randperm(len(x)).split(64):
            opt.zero_grad(); loss=lossfn(model(x[batch])[:,:8],y[batch,:8]); loss.backward(); opt.step()
            total+=float(loss.detach())*len(batch)
        model.eval()
        with torch.no_grad(): val=float(lossfn(model(xv)[:,:8],yv[:,:8]))
        if val<best: best=val; state=copy.deepcopy(model.state_dict())
        history.append(dict(epoch=epoch+1,training_bce=total/len(x),validation_bce=val))
    model.load_state_dict(state); model.eval(); torch.save(state,OUT/'weights'/f'{kind}-{seed}.pt')
    save(f'{kind}-{seed}-training.json',dict(seed=seed,kind=kind,parameters=sum(p.numel() for p in model.parameters()),
        elapsed_seconds=time.perf_counter()-start,selected_epoch=min(history,key=lambda r:r['validation_bce'])['epoch'],history=history))
    print(f'{kind} seed {seed}: validation BCE {best:.5f}',flush=True)
    return model


def load_models():
    models={}
    for kind,cls in CLASSES.items():
        models[kind]=[]
        for seed in [11,22,33]:
            model=cls().eval(); model.load_state_dict(torch.load(OUT/'weights'/f'{kind}-{seed}.pt',weights_only=True))
            models[kind].append(model)
    return models


def focuses(records,models,budget=4):
    x,_=tensors(records); proposals={}
    for kind,ensemble in models.items():
        with torch.no_grad(): logits=torch.stack([model(x) for model in ensemble]).mean(0).numpy()
        proposals[kind]=[sorted(range(8),key=lambda j:(-float(scores[j]),j))[:budget] for scores in logits]
    for method in ['premium','singleton','premium_per_use','horizon','random']:
        proposals[method]=[baselines(r)[method] for r in records]
    proposals['sequential_greedy']=[greedy_focus(r,budget)[0] for r in records]
    return proposals


def evaluate(records,models,split):
    rows=[]
    for method,focuses_for_method in focuses(records,models).items():
        for r,focus in zip(records,focuses_for_method):
            p=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],focus); exact=F(r['exact'])
            assert p.lower<=exact<=p.upper
            rows.append(dict(split=split,case=r['case'],method=method,focus=focus,lower=str(p.lower),
                upper=str(p.upper),factor=str(p.factor),exact=str(exact),witness=p.witness,
                log_gap=float(np.log(float(exact/p.lower))),full_optimum_covered=p.lower==exact))
    return rows


def describe(rows):
    descriptions=[]
    for split in sorted({r['split'] for r in rows}):
        for method in sorted({r['method'] for r in rows}):
            group=[r for r in rows if r['split']==split and r['method']==method]
            descriptions.append(dict(split=split,method=method,cohorts=len(group),
                mean_log_gap=float(np.mean([r['log_gap'] for r in group])),
                mean_certificate_factor=float(np.mean([float(F(r['factor'])) for r in group])),
                optimum_coverage=float(np.mean([r['full_optimum_covered'] for r in group]))))
    return descriptions


def confirmation_tests(rows,selected):
    rng=np.random.default_rng(20261500); contrasts=[]
    for split in ['confirmation_id','confirmation_shift']:
        bymethod={method:np.asarray([r['log_gap'] for r in sorted(rows,key=lambda x:x['case'])
                     if r['method']==method and r['split']==split])
                  for method in [selected,'premium','sequential_greedy']}
        for baseline in ['premium','sequential_greedy']:
            d=bymethod[selected]-bymethod[baseline]; observed=abs(float(d.mean()))
            draws=np.abs((rng.choice([-1,1],size=(9999,300))*d).mean(1))
            p=(1+int(np.sum(draws>=observed-1e-15)))/10000
            boots=d[rng.integers(0,300,size=(2000,300))].mean(1)
            contrasts.append(dict(split=split,selected=selected,baseline=baseline,mean_selected_minus_baseline=float(d.mean()),
                raw_p=p,bootstrap_95_ci=list(map(float,np.quantile(boots,[.025,.975]))),
                win_tie_loss=[int(np.sum(d<-1e-12)),int(np.sum(abs(d)<=1e-12)),int(np.sum(d>1e-12))],
                structural_self_comparison=selected==baseline))
    previous=0.
    for rank,i in enumerate(sorted(range(4),key=lambda j:contrasts[j]['raw_p'])):
        previous=max(previous,min(1.,(4-rank)*contrasts[i]['raw_p'])); contrasts[i]['holm_p']=previous
    return contrasts


def budget_study(records,models,split):
    x,_=tensors(records)
    with torch.no_grad(): logits=torch.stack([m(x) for m in models['attention']]).mean(0).numpy()
    rows=[]
    for k in [0,1,2,4,8]:
        for r,scores in zip(records,logits):
            for method in ['premium','sequential_greedy','attention']:
                if method=='attention': focus=sorted(range(8),key=lambda i:(-float(scores[i]),i))[:k]; count=0
                elif method=='premium': focus=sorted(range(8),key=lambda i:(-r['q'][i],r['h'][i],i))[:k]; count=0
                else: focus,count=greedy_focus(r,k)
                p=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],focus)
                rows.append(dict(split=split,case=r['case'],method=method,budget=k,focus=focus,
                    lower=str(p.lower),upper=str(p.upper),factor=str(p.factor),exact=r['exact'],
                    log_gap=float(np.log(float(F(r['exact'])/p.lower))),full_optimum_covered=p.lower==F(r['exact']),
                    subset_evaluations_including_proposal=count+p.evaluated_subsets))
    return rows


def main():
    protect(); plan=sha('clock_regret_attention/ABLATION_PLAN.md')
    (OUT/'ABLATION_PLAN.md.sha256').write_text(plan)
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    training=json.loads((OUT/'training_inputs.json').read_text()); validation=json.loads((OUT/'validation_inputs.json').read_text())
    for kind in ['pooled','no_broadcast_attention']:
        for seed in [11,22,33]: train(kind,seed,training,validation)
    models=load_models(); valrows=evaluate(validation,models,'validation')
    val_summary=describe(valrows)
    eligible=[r for r in val_summary if r['method']!='random']
    winner=min(eligible,key=lambda r:(r['mean_log_gap'],r['method']))['method']
    save('ablation-validation-evaluation.json',valrows)
    save('ablation-validation-selection.json',dict(selected=winner,ranking=sorted(eligible,key=lambda r:(r['mean_log_gap'],r['method'])),
        tie_break='lexical method name',ensemble='mean of three checkpoint logits, then top four',
        plan_sha256=plan,confirmation_data_not_yet_generated=True))
    print('Validation selected: '+winner,flush=True)
    descriptive=[]; budget=[]; confirmation=[]
    for split in ['id','shift']:
        records=json.loads((OUT/f'{split}-inputs.json').read_text())
        descriptive.extend(evaluate(records,models,'original_'+split))
        budget.extend(budget_study(records,models,split))
    for split,seed,shift in [('confirmation_id',20261403,False),('confirmation_shift',20261404,True)]:
        records=generate(300,seed,shift); save(f'{split}-inputs.json',records)
        confirmation.extend(evaluate(records,models,split))
    save('ablation-original-evaluation.json',descriptive); save('ablation-original-summary.json',describe(descriptive))
    save('confirmation-evaluation.json',confirmation); save('confirmation-summary.json',describe(confirmation))
    save('confirmation-tests.json',confirmation_tests(confirmation,winner))
    save('budget-evaluation.json',budget)
    budget_summary=[]
    for split in ['id','shift']:
        for method in ['premium','sequential_greedy','attention']:
            for k in [0,1,2,4,8]:
                group=[r for r in budget if r['split']==split and r['method']==method and r['budget']==k]
                budget_summary.append(dict(split=split,method=method,budget=k,
                    mean_log_gap=float(np.mean([r['log_gap'] for r in group])),
                    mean_certificate_factor=float(np.mean([float(F(r['factor'])) for r in group])),
                    optimum_coverage=float(np.mean([r['full_optimum_covered'] for r in group])),
                    mean_subset_evaluations=float(np.mean([r['subset_evaluations_including_proposal'] for r in group]))))
    save('budget-summary.json',budget_summary); assert sha('clock_regret_attention/ABLATION_PLAN.md')==plan; protect()
    print(json.dumps(read_tests:=json.loads((OUT/'confirmation-tests.json').read_text()),indent=2),flush=True)


if __name__=='__main__': main()
