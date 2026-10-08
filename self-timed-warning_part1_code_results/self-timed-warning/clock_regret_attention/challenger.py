"""Post-training sequential-greedy challenger; no model or plan changes."""
from fractions import Fraction as F
import json
import numpy as np
from clock_regret_attention.core import focused_pair, summary
from clock_regret_attention.run import OUT, protect, save


def greedy_focus(r, budget=4):
    chosen=[]; evaluations=0
    eligible=summary(r['h'],r['f'],r['a'],r['b'],r['q'])[4]
    for _ in range(min(budget,len(eligible))):
        candidates=[]
        for i in eligible:
            if i not in chosen:
                ans=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],chosen+[i])
                evaluations+=ans.evaluated_subsets
                candidates.append((ans.lower,r['q'][i],-r['h'][i],-i,i))
        chosen.append(max(candidates)[-1])
    return chosen,evaluations


def main():
    protect(); summaries=[]; rows=[]
    for split in ['id','shift']:
        records=json.loads((OUT/f'{split}-inputs.json').read_text())
        fitted=json.loads((OUT/f'{split}-evaluation.json').read_text())
        gaps=[]; factors=[]; covered=[]; diffs=[]
        for r in records:
            focus,evaluations=greedy_focus(r)
            ans=focused_pair(r['h'],r['f'],r['a'],r['b'],r['q'],focus)
            exact=F(r['exact']); assert ans.lower<=exact<=ans.upper
            gap=float(np.log(float(exact/ans.lower)))
            attention=np.mean([v['log_gap'] for v in fitted if v['method']=='attention' and v['case']==r['case']])
            gaps.append(gap); factors.append(float(ans.factor)); covered.append(ans.lower==exact)
            diffs.append(float(attention-gap))
            rows.append(dict(split=split,case=r['case'],focus=focus,lower=str(ans.lower),upper=str(ans.upper),
                             exact=str(exact),factor=str(ans.factor),witness=ans.witness,log_gap=gap,
                             full_optimum_covered=ans.lower==exact,proposal_subset_evaluations=evaluations,
                             attention_minus_greedy=float(attention-gap)))
        diffs=np.asarray(diffs)
        summaries.append(dict(split=split,method='sequential_greedy',mean_log_gap=float(np.mean(gaps)),
            median_log_gap=float(np.median(gaps)),mean_certificate_factor=float(np.mean(factors)),
            mean_optimum_coverage=float(np.mean(covered)),mean_attention_minus_greedy=float(diffs.mean()),
            attention_win_tie_loss=[int(np.sum(diffs<-1e-12)),int(np.sum(abs(diffs)<=1e-12)),int(np.sum(diffs>1e-12))],
            status='exploratory challenger added after planned outcomes; descriptive, not part of the four-test family'))
    save('greedy-evaluation.json',rows); save('greedy-summary.json',summaries); protect()
    print(json.dumps(summaries,indent=2))


if __name__=='__main__': main()
