"""Saved learned-proposal/fallback integration checks on complete age families."""
from dataclasses import asdict
from fractions import Fraction as F
import json
import torch
from clock_regret_attention.run import OUT,save,protect
from clock_regret_attention.models import AttentionRanker
from clock_regret_attention.integration import select,learned_selector
from clock_regret_fleet.core import select as exact_select


def main():
    protect(); torch.set_num_threads(1)
    model=AttentionRanker().eval()
    model.load_state_dict(torch.load(OUT/'weights'/'attention-11.pt',weights_only=True))
    callback=learned_selector(model); rows=[]
    for r in json.loads((OUT/'id-inputs.json').read_text())[:20]:
        ages=[r['a'],r['b'],r['b']+10]
        result=select(r['h'],r['f'],ages,r['q'],F(1,2),budget=4,selector=callback)
        truth=exact_select(r['h'],r['f'],ages,r['q'],exact=True)
        exact=truth['lower_scores']
        assert all(lo<=g<=hi for lo,g,hi in zip(result['lower_scores'],exact,result['upper_scores']))
        assert exact[result['chosen']]<=F(3,2)*min(exact)
        if result['certified_exact_decision']: assert exact[result['chosen']]==min(exact)
        rows.append(dict(case=r['case'],ages=ages,selected_age=result['selected_age'],
            lower_scores=result['lower_scores'],upper_scores=result['upper_scores'],exact_scores=exact,
            certified_exact_decision=result['certified_exact_decision'],
            pairs=[[asdict(p) for p in row] for row in result['pairs']]))
    save('hybrid-family-demo.json',rows); protect(); print('20 trained-proposal complete-family checks passed')


if __name__=='__main__': main()
