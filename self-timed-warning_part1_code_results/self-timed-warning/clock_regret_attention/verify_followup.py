"""Follow-up evidence checks; leave all experiment outputs untouched."""
from dataclasses import asdict
from fractions import Fraction as F
import json
import numpy as np
import torch
from clock_regret_attention.run import OUT,sha,generate,protect
from clock_regret_attention.core import focused_pair
from clock_regret_attention.ablations import load_models,evaluate,describe,confirmation_tests
from clock_regret_attention.integration import select,learned_selector
from clock_regret_attention.models import AttentionRanker
from clock_regret_fleet.core import select as full_select
from clock_regret_fleet.oracles import rate


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def verify():
    torch.set_num_threads(1); checks={}; protect()
    assert sha('clock_regret_attention/ABLATION_PLAN.md')==(OUT/'ABLATION_PLAN.md.sha256').read_text().strip()
    models=load_models(); validation=read('validation_inputs.json')
    val=json.loads(json.dumps(evaluate(validation,models,'validation')))
    assert val==read('ablation-validation-evaluation.json')
    ranking=sorted([r for r in describe(val) if r['method']!='random'],key=lambda r:(r['mean_log_gap'],r['method']))
    selection=read('ablation-validation-selection.json'); assert ranking==selection['ranking']
    assert selection['selected']==ranking[0]['method']=='sequential_greedy'
    checks['validation_only_selector_choice_reproduced']=True
    datasets={name:read(f'{name}-inputs.json') for name in ['id','shift','confirmation_id','confirmation_shift']}
    for split,seed,shift in [('confirmation_id',20261403,False),('confirmation_shift',20261404,True)]:
        assert datasets[split]==generate(300,seed,shift)
    all_groups=[validation,read('training_inputs.json')]+list(datasets.values())
    canonical=lambda r:json.dumps({k:r[k] for k in ['h','f','a','b','q']},sort_keys=True)
    keys=[{canonical(r) for r in group} for group in all_groups]
    assert all(not keys[i]&keys[j] for i in range(len(keys)) for j in range(i+1,len(keys)))
    checks['fresh_confirmation_cohorts_disjoint']=600
    count=0
    for filename in ['ablation-original-evaluation.json','confirmation-evaluation.json','budget-evaluation.json']:
        for row in read(filename):
            split=row['split'].replace('original_',''); r=datasets[split][row['case']]
            p=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],row['focus']); exact=F(r['exact'])
            assert str(p.lower)==row['lower'] and str(p.upper)==row['upper'] and str(p.factor)==row['factor']
            assert p.lower<=exact<=p.upper
            assert np.isclose(row['log_gap'],np.log(float(exact/p.lower)),rtol=0,atol=1e-15)
            assert row['full_optimum_covered']==(p.lower==exact)
            assert rate(p.witness,r['a'],r['q'])/rate(p.witness,r['b'],r['q'])==p.lower
            if row.get('budget')==8: assert p.lower==exact==p.upper
            count+=1
    checks['ablation_confirmation_budget_exact_intervals']=count
    for split in ['confirmation_id','confirmation_shift']:
        rows=json.loads(json.dumps(evaluate(datasets[split],models,split)))
        assert rows==[r for r in read('confirmation-evaluation.json') if r['split']==split]
    checks['fresh_prediction_and_greedy_rows_reproduced']=6000
    assert confirmation_tests(read('confirmation-evaluation.json'),selection['selected'])==read('confirmation-tests.json')
    checks['confirmation_corrected_tests_reproduced']=4
    for kind in ['pooled','no_broadcast_attention']:
        for seed in [11,22,33]:
            log=read(f'{kind}-{seed}-training.json')
            assert len(log['history'])==25 and log['selected_epoch']==min(log['history'],key=lambda r:r['validation_bce'])['epoch']
    checks['additional_validation_checkpoint_selections']=6
    model=AttentionRanker().eval();model.load_state_dict(torch.load(OUT/'weights'/'attention-11.pt',weights_only=True))
    callback=learned_selector(model)
    for r in datasets['id'][:20]:
        ages=[r['a'],r['b'],r['b']+10]
        oracle=full_select(r['h'],r['f'],ages,r['q'],exact=True)['lower_scores']
        for selector in [None,callback]:
            result=select(r['h'],r['f'],ages,r['q'],F(1,2),budget=4,selector=selector)
            assert all(lo<=g<=hi for lo,g,hi in zip(result['lower_scores'],oracle,result['upper_scores']))
            assert oracle[result['chosen']]<=F(3,2)*min(oracle)
            for i,a in enumerate(ages):
                for j,b in enumerate(ages):
                    p=result['pairs'][i][j]
                    assert p.lower==rate(p.witness,a,r['q'])/rate(p.witness,b,r['q'])
            if result['certified_exact_decision']:assert oracle[result['chosen']]==min(oracle)
    checks['final_default_and_trained_full_family_checks']=40
    checks['protected_artifacts_unchanged']=protect()
    return checks


if __name__=='__main__':print(json.dumps(verify(),indent=2))
