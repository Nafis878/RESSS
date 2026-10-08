"""Read saved evidence and independently recompute certificates and contrasts."""
from fractions import Fraction as F
import json
import numpy as np
import torch
from clock_regret_attention.run import OUT,protect,generate
from clock_regret_attention.models import AttentionRanker,MLPRanker,features
from clock_regret_attention.core import focused_pair
from clock_regret_fleet.oracles import rate


def read(name): return json.loads((OUT/name).read_text())


def verify():
    torch.set_num_threads(1); checks={}; checks['old_artifacts_unchanged']=protect()
    splits={name:read(f'{name}-inputs.json') for name in ['id','shift']}
    training=read('training_inputs.json'); validation=read('validation_inputs.json')
    for records,count,seed,shift in [(training,1600,20261101,False),(validation,200,20261102,False),
                                    (splits['id'],300,20261103,False),(splits['shift'],300,20261104,True)]:
        assert records==generate(count,seed,shift)
    checks['regenerated_exactly_labeled_datasets']=2400
    canonical=lambda r:json.dumps({k:r[k] for k in ['h','f','a','b','q']},sort_keys=True)
    groups=[{canonical(r) for r in rows} for rows in [training,validation,splits['id'],splits['shift']]]
    assert all(len(g)==n for g,n in zip(groups,[1600,200,300,300]))
    assert all(not groups[i]&groups[j] for i in range(4) for j in range(i+1,4))
    r=splits['id'][0]; altered=dict(r,exact='999999',label=[999]*10,sealed_lifetime=[999]*10)
    assert np.array_equal(features(r),features(altered))
    checks['public_only_features_and_disjoint_input_sets']=True
    verified=0
    for split,records in splits.items():
        rows=read(f'{split}-evaluation.json')
        assert len(rows)==3300
        for row in rows:
            r=records[row['case']]; p=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],row['focus'])
            assert str(p.lower)==row['lower'] and str(p.upper)==row['upper'] and str(p.factor)==row['factor']
            assert p.lower<=F(r['exact'])<=p.upper and tuple(row['witness'])==p.witness
            assert rate(p.witness,r['a'],r['q'])/rate(p.witness,r['b'],r['q'])==p.lower
            assert np.isclose(row['log_gap'],np.log(float(F(r['exact'])/p.lower)),rtol=0,atol=1e-15)
            verified+=1
        for kind,cls in [('attention',AttentionRanker),('mlp',MLPRanker)]:
            x=torch.tensor(np.stack([features(r) for r in records]))
            for seed in [11,22,33]:
                model=cls().eval(); model.load_state_dict(torch.load(OUT/'weights'/f'{kind}-{seed}.pt',weights_only=True))
                with torch.no_grad(): predictions=model(x).numpy()
                bycase={v['case']:v for v in rows if v['method']==kind and v['seed']==seed}
                for i,scores in enumerate(predictions):
                    assert sorted(range(8),key=lambda j:(-float(scores[j]),j))[:4]==bycase[i]['focus']
    checks['exact_focus_results_and_feasible_witnesses']=verified
    checks['checkpoint_focus_predictions_reproduced']=3600
    for kind in ['attention','mlp']:
        for seed in [11,22,33]:
            log=read(f'{kind}-{seed}-training.json')
            assert len(log['history'])==25
            assert log['selected_epoch']==min(log['history'],key=lambda x:x['validation_bce'])['epoch']
    checks['fixed_epoch_validation_checkpoint_selection']=6
    rng=np.random.default_rng(20261300); recomputed=[]
    for split in ['id','shift']:
        rows=read(f'{split}-evaluation.json')
        values={method:np.asarray([np.mean([r['log_gap'] for r in rows if r['method']==method and r['case']==i])
                   for i in range(300)]) for method in ['attention','premium','mlp']}
        for baseline in ['premium','mlp']:
            d=values['attention']-values[baseline]; obs=abs(d.mean())
            perm=np.abs((rng.choice([-1,1],size=(9999,300))*d).mean(axis=1))
            p=(1+np.sum(perm>=obs-1e-15))/10000
            ci=np.quantile(d[rng.integers(0,300,size=(2000,300))].mean(axis=1),[.025,.975])
            recomputed.append(dict(split=split,baseline=baseline,mean=float(d.mean()),p=float(p),ci=ci))
    previous=0
    for rank,i in enumerate(sorted(range(4),key=lambda j:recomputed[j]['p'])):
        previous=max(previous,min(1.,(4-rank)*recomputed[i]['p'])); recomputed[i]['holm']=previous
    for saved,new in zip(read('statistical_tests.json'),recomputed):
        assert saved['raw_p']==new['p'] and saved['holm_p']==new['holm']
        assert abs(saved['mean_attention_minus_baseline']-new['mean'])<1e-15
        assert np.allclose(saved['bootstrap_95_ci'],new['ci'],rtol=0,atol=1e-15)
    checks['paired_tests_holm_and_bootstrap_reproduced']=4
    for r in read('math_focus_checks.json'):
        ans=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],r['focus'])
        truth=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],range(8))
        assert str(ans.lower)==r['lower'] and str(ans.upper)==r['upper'] and str(truth.lower)==r['exact']
        assert ans.lower<=truth.lower<=ans.upper
    checks['stored_arbitrary_focus_cases']=500
    from clock_regret_attention.challenger import greedy_focus
    for row in read('greedy-evaluation.json'):
        r=splits[row['split']][row['case']]; focus,count=greedy_focus(r)
        assert focus==row['focus'] and count==row['proposal_subset_evaluations']
        p=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],focus)
        assert str(p.lower)==row['lower'] and str(p.upper)==row['upper']
    checks['exploratory_greedy_cases_reproduced']=600
    assert protect()==1025
    return checks


if __name__=='__main__': print(json.dumps(verify(),indent=2))
