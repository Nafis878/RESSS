"""Any-selector focused adversary with an exact omitted-premium certificate."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import combinations
from numbers import Integral
from clock_regret_fleet.core import inputs


@dataclass
class FocusResult:
    lower: F
    upper: F
    factor: F
    witness: tuple[int,...]
    focus: tuple[int,...]
    selected_failures: tuple[int,...]
    evaluated_subsets: int


def summary(h,f,a,b,q):
    n=len(h)
    ca=F(n)+sum((qi for hi,fi,qi in zip(h,f,q) if fi and hi<=a),F(0))
    cb=F(n)+sum((qi for hi,fi,qi in zip(h,f,q) if fi and hi<=b),F(0))
    ta=sum(min(hi,a) if fi else a for hi,fi in zip(h,f))
    tb=sum(min(hi,b) if fi else b for hi,fi in zip(h,f))
    eligible=tuple(i for i,(hi,fi) in enumerate(zip(h,f)) if not fi and hi<a)
    return ca,cb,ta,tb,eligible


def focused_pair(horizon,failed,a,b,premiums,focus):
    h,f,d,q,_=inputs(horizon,failed,[a,b],premiums,F(1,4)); a,b=d
    if a>=b: raise ValueError('focused subset theorem requires a<b')
    ca,cb,ta,tb,eligible=summary(h,f,a,b,q)
    try:
        values=list(focus)
        if any(not isinstance(i,Integral) or isinstance(i,bool) for i in values):
            raise ValueError('focus indices must be integers')
        chosen=tuple(sorted(map(int,values)))
        if len(set(chosen))!=len(chosen) or not set(chosen)<=set(eligible):
            raise ValueError('focus must be a subset of eligible censored records')
    except TypeError as exc: raise ValueError('focus must be an index sequence') from exc
    best=None; subset=()
    for x in range(len(chosen)+1):
        for selected in combinations(chosen,x):
            Q=sum((q[i] for i in selected),F(0)); s=sum(h[i]+1 for i in selected)
            value=(ca+Q)*(tb-b*x+s)/((cb+Q)*(ta-a*x+s))
            if best is None or value>best:
                best=value; subset=selected
    tail=sum((q[i] for i in eligible if i not in chosen),F(0))
    factor=(ca+tail)*cb/(ca*(cb+tail))
    life=[hi if fi else max(hi+1,b+1) for hi,fi in zip(h,f)]
    for i in subset: life[i]=h[i]+1
    return FocusResult(best,factor*best,factor,tuple(life),chosen,subset,2**len(chosen))


def optimal_premium_focus(horizon,failed,a,b,premiums,budget):
    h,f,d,q,_=inputs(horizon,failed,[a,b],premiums,F(1,4)); a,b=d
    if a>=b: raise ValueError('requires a<b')
    if not isinstance(budget,Integral) or isinstance(budget,bool) or budget<0:
        raise ValueError('nonnegative integer budget required')
    eligible=summary(h,f,a,b,q)[4]
    return tuple(sorted(eligible,key=lambda i:(-q[i],h[i],i))[:int(budget)])


def minimum_certified_focus(horizon,failed,a,b,premiums,tolerance=F(1,4)):
    """Smallest cardinality certifying factor <=1+tolerance using A1 only.

    This can require full enumeration; it is not a polynomial-time replacement
    for the fleet FPTAS. Ties in cost summaries may admit other minimal focuses.
    """
    h,f,d,q,eps=inputs(horizon,failed,[a,b],premiums,tolerance); a,b=d
    if a>=b: raise ValueError('requires a<b')
    ca,cb,_,_,eligible=summary(h,f,a,b,q)
    order=sorted(eligible,key=lambda i:(-q[i],h[i],i))
    tail=sum((q[i] for i in order),F(0)); chosen=[]
    def factor(y): return (ca+y)*cb/(ca*(cb+y))
    for i in order:
        if factor(tail)<=1+eps: break
        chosen.append(i); tail-=q[i]
    assert factor(tail)<=1+eps
    return tuple(chosen)
