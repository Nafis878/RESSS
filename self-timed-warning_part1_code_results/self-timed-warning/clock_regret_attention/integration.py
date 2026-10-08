"""Optional learned proposals with the existing solver as certified fallback."""
from dataclasses import dataclass
from fractions import Fraction as F
from numbers import Integral
import math
from clock_regret_attention.core import focused_pair, optimal_premium_focus, summary
from clock_regret_fleet.core import inputs, pair


@dataclass
class HybridPair:
    lower: F
    upper: F
    witness: tuple
    proposal_focus: tuple
    proposal_lower: F | None
    proposal_upper: F | None
    fallback_lower: F
    fallback_upper: F
    premium_focus: tuple = ()
    premium_lower: F | None = None
    premium_upper: F | None = None


def greedy_selector(h,f,a,b,q,budget):
    from clock_regret_attention.challenger import greedy_focus
    return greedy_focus(dict(h=h,f=f,a=a,b=b,q=q),budget)[0]


def learned_selector(model):
    """Return a public-input-only callback; exact certificate ignores logits."""
    import torch
    from clock_regret_attention.models import features
    model.eval()
    def propose(h,f,a,b,q,budget):
        r=dict(h=h,f=f,a=a,b=b,q=q)
        with torch.no_grad():
            scores=model(torch.tensor(features(r))[None])[0].tolist()
        if any(not math.isfinite(v) for v in scores):
            raise ValueError('proposal scores must be finite')
        eligible=summary(h,f,a,b,q)[4]
        return sorted(eligible,key=lambda i:(-scores[i],i))[:budget]
    return propose


def hybrid_pair(horizon,failed,a,b,premiums,epsilon=F(1,4),*,budget=4,selector=None):
    h,f,ages,q,eps=inputs(horizon,failed,[a,b],premiums,epsilon); a,b=ages
    if not isinstance(budget,Integral) or isinstance(budget,bool) or budget<0:
        raise ValueError('nonnegative integer budget required')
    fallback=pair(h,f,a,b,q,eps)
    if a>=b:
        return HybridPair(fallback.lower,fallback.upper,fallback.lifetimes,(),None,None,
                          fallback.lower,fallback.upper)
    focus=(selector or greedy_selector)(h,f,a,b,q,int(budget))
    focus=list(focus)
    if len(focus)>budget: raise ValueError('proposal exceeds focus budget')
    proposal=focused_pair(h,f,a,b,q,focus)
    premium_focus=optimal_premium_focus(h,f,a,b,q,budget)
    premium=(proposal if set(premium_focus)==set(proposal.focus)
             else focused_pair(h,f,a,b,q,premium_focus))
    lower=max(proposal.lower,premium.lower,fallback.lower)
    upper=min(proposal.upper,premium.upper,fallback.upper)
    assert lower<=upper and upper<=(1+eps)*lower
    witness=max([(fallback.lower,fallback.lifetimes),(proposal.lower,proposal.witness),
                 (premium.lower,premium.witness)],key=lambda p:p[0])[1]
    return HybridPair(lower,upper,witness,proposal.focus,proposal.lower,proposal.upper,
                      fallback.lower,fallback.upper,tuple(premium_focus),premium.lower,premium.upper)


def select(horizon,failed,ages,premiums,epsilon=F(1,4),*,budget=4,selector=None):
    """Discrete finite-family selection; no continuous/future-population claim."""
    h,f,d,q,eps=inputs(horizon,failed,ages,premiums,epsilon)
    results=[[hybrid_pair(h,f,a,b,q,eps,budget=budget,selector=selector) for b in d] for a in d]
    lower=tuple(max(p.lower for p in row) for row in results)
    upper=tuple(max(p.upper for p in row) for row in results)
    chosen=min(range(len(d)),key=lambda i:(upper[i],lower[i],i))
    competitors=[lower[i] for i in range(len(d)) if i!=chosen]
    return dict(chosen=chosen,selected_age=d[chosen],lower_scores=lower,upper_scores=upper,pairs=results,
        certified_exact_decision=not competitors or upper[chosen]<=min(competitors),
        certified_unique=not competitors or upper[chosen]<min(competitors),
        worst_case_decision_factor=1+eps,continuous=False)
