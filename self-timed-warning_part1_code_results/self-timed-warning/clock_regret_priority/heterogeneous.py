"""Exact later-age relative rates with asset-specific rational failure premiums.

Preventive cost is one; asset i's failure cost is 1+q_i, with q_i>0.
This API solves a>b comparisons. No general heterogeneous full-family
polynomial-time selection result is asserted.
"""
from dataclasses import dataclass
from fractions import Fraction
from numbers import Integral
import numpy as np
from clock_regret.core import validate
from clock_regret.oracles import hull


@dataclass
class LaterPair:
    ratio: Fraction
    witness: tuple[int, ...]
    shared_count: int
    denominators: tuple[Fraction, ...]
    objective_evaluations: int


@dataclass
class ContinuousLater:
    ratio: Fraction
    limiting_lifetimes: tuple[int, ...]
    approach_indices: tuple[int, ...]
    attained: bool

    def completion(self, epsilon=Fraction(1,1000)):
        eps=Fraction(epsilon)
        if not 0<eps<1:
            raise ValueError('epsilon must lie strictly between zero and one')
        selected=set(self.approach_indices)
        return tuple(Fraction(t)+eps if i in selected else Fraction(t)
                     for i,t in enumerate(self.limiting_lifetimes))


def public(horizon, logger_failed, age_a, age_b, premiums):
    h,f,ages,_=validate(horizon,logger_failed,[age_a,age_b],2)
    a,b=map(int,ages)
    if a<=b:
        raise ValueError('heterogeneous prefix theorem requires candidate age a>b')
    try:
        values=list(premiums)
        if len(values)!=len(h):
            raise ValueError('one positive rational failure premium per asset required')
        if any(isinstance(x,(bool,float,np.floating)) for x in values):
            raise ValueError('premiums must be exact rationals, not floats or booleans')
        q=tuple(Fraction(int(x)) if isinstance(x,Integral) else Fraction(x) for x in values)
        if any(x<=0 for x in q):
            raise ValueError('strictly positive failure premiums required')
    except (TypeError,ZeroDivisionError,OverflowError) as error:
        raise ValueError('exact positive rational premiums required') from error
    return tuple(map(int,h)),tuple(map(bool,f)),a,b,q


def baseline(h,f,a,b,q):
    n=len(h)
    ca=Fraction(n)+sum((qi for hi,fi,qi in zip(h,f,q) if fi and hi<=a),Fraction(0))
    cb=Fraction(n)+sum((qi for hi,fi,qi in zip(h,f,q) if fi and hi<=b),Fraction(0))
    ta=sum(min(hi,a) if fi else a for hi,fi in zip(h,f))
    tb=sum(min(hi,b) if fi else b for hi,fi in zip(h,f))
    early=[i for i,(hi,fi) in enumerate(zip(h,f)) if not fi and hi<b]
    middle=[i for i,(hi,fi) in enumerate(zip(h,f)) if not fi and b<=hi<a]
    return ca,cb,ta,tb,early,middle


def later_pair(horizon,logger_failed,age_a,age_b,premiums):
    h,f,a,b,q=public(horizon,logger_failed,age_a,age_b,premiums)
    ca,cb,ta,tb,early,middle=baseline(h,f,a,b,q)
    order=sorted(early,key=lambda i:(q[i],i))
    m=len(early)+len(middle)
    use=ta-m*a+len(early)*(b+1)+sum(h[i]+1 for i in middle)
    cost=ca+sum((q[i] for i in early+middle),Fraction(0))
    premium=Fraction(0)
    denominators=[]
    for x in range(len(order)+1):
        if x:
            premium+=q[order[x-1]]
        denominators.append((cb+premium)*(use-x))
    selected=min(range(len(denominators)),key=lambda x:(denominators[x],x))
    shared=set(order[:selected])
    life=[hi if fi else max(hi+1,a+1) for hi,fi in zip(h,f)]
    for i in early:
        life[i]=b if i in shared else b+1
    for i in middle:
        life[i]=h[i]+1
    return LaterPair(cost*tb/denominators[selected],tuple(life),selected,
                     tuple(denominators),len(denominators))


def continuous_later_pair(horizon,logger_failed,age_a,age_b,premiums):
    h,f,a,b,q=public(horizon,logger_failed,age_a,age_b,premiums)
    ca,cb,ta,tb,early,middle=baseline(h,f,a,b,q)
    m=len(early)+len(middle)
    use=ta-m*a+len(early)*b+sum(h[i] for i in middle)
    cost=ca+sum((q[i] for i in early+middle),Fraction(0))
    life=[hi if fi else max(hi+1,a+1) for hi,fi in zip(h,f)]
    for i in early+middle:
        life[i]=max(h[i],b)
    return ContinuousLater(cost*tb/(cb*use),tuple(life),tuple(early+middle),m==0)


def phase_oracle(horizon,logger_failed,age_a,age_b,premiums,continuous=False):
    """Separate cost-state / exposure-hull DP; no premium sorting or prefix formula.

    Within a fixed failure phase the objective is linear-fractional in exposure;
    a maximum is attained on an exposure-hull vertex. The continuous oracle
    keeps boundary phase flags distinct from limiting lifetime values.
    """
    h,f,a,b,q=public(horizon,logger_failed,age_a,age_b,premiums)
    states={(Fraction(0),Fraction(0)):[(0,0)]}
    for hi,fi,qi in zip(h,f,q):
        if fi:
            choices=[(int(hi<=a),int(hi<=b),min(hi,a),min(hi,b))]
        elif continuous:
            choices=[(0,0,a,b)]
            if hi<b:
                choices.extend((1,1,t,t) for t in [hi,b])
            if hi<a:
                choices.extend((1,0,t,b) for t in [max(hi,b),a])
        else:
            times={hi+1,max(hi+1,a+1)}
            times.update(t for t in [b,b+1,a,a+1] if t>hi)
            choices=[(int(t<=a),int(t<=b),min(t,a),min(t,b)) for t in times]
        new={}
        for (pa,pb),points in states.items():
            for ia,ib,ta,tb in choices:
                new.setdefault((pa+ia*qi,pb+ib*qi),[]).extend((x+ta,y+tb) for x,y in points)
        states={key:hull(points) for key,points in new.items()}
    n=len(h)
    return max((n+pa)*tb/((n+pb)*ta) for (pa,pb),points in states.items() for ta,tb in points)


def rate_ratio(life,a,b,premiums):
    q=[Fraction(x) for x in premiums]
    n=len(q)
    ca=Fraction(n)+sum((qi for t,qi in zip(life,q) if t<=a),Fraction(0))
    cb=Fraction(n)+sum((qi for t,qi in zip(life,q) if t<=b),Fraction(0))
    ta=sum(min(t,a) for t in life)
    tb=sum(min(t,b) for t in life)
    return ca*tb/(cb*ta)
