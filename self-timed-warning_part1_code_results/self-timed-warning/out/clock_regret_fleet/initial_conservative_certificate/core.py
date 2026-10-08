"""Certified complete-family heterogeneous-cost cohort selection."""
from dataclasses import dataclass
from fractions import Fraction
from numbers import Integral
import numpy as np
from clock_regret.core import validate
from clock_regret_priority.heterogeneous import later_pair, continuous_later_pair


def inputs(horizon, failed, ages, premiums, epsilon):
    h,f,d,_=validate(horizon,failed,ages,2)
    try:
        raw=list(premiums)
        if len(raw)!=len(h) or any(isinstance(x,(bool,float,np.floating)) for x in raw):
            raise ValueError('one exact positive rational premium per asset required')
        q=tuple(Fraction(int(x)) if isinstance(x,Integral) else Fraction(x) for x in raw)
        if any(x<=0 for x in q): raise ValueError('positive premiums required')
        if isinstance(epsilon,(bool,float,np.floating)): raise ValueError('exact rational tolerance required')
        eps=Fraction(epsilon)
        if not 0<eps<=1: raise ValueError('tolerance must lie in (0,1]')
    except (TypeError,ZeroDivisionError,OverflowError) as exc:
        raise ValueError('exact rational premiums and tolerance required') from exc
    return tuple(map(int,h)),tuple(map(bool,f)),tuple(map(int,d)),q,eps


@dataclass
class Pair:
    lower: Fraction
    upper: Fraction
    lifetimes: tuple
    approach_indices: tuple
    states_peak: int
    states_final: int
    exact: bool

    def completion(self,epsilon_time=Fraction(1,1000)):
        t=Fraction(epsilon_time)
        if not 0<t<1: raise ValueError('epsilon_time must lie in (0,1)')
        approach=set(self.approach_indices)
        return tuple(Fraction(v)+t if i in approach else Fraction(v) for i,v in enumerate(self.lifetimes))


def bucket(value,minimum,subdivisions):
    ratio=value/minimum
    k=ratio.numerator.bit_length()-ratio.denominator.bit_length()
    power=Fraction(2**k) if k>=0 else Fraction(1,2**(-k))
    if ratio<power: k-=1; power/=2
    scaled=ratio/power
    j=int((scaled-1)*subdivisions)
    assert k>=0 and 0<=j<subdivisions
    return k,j


def pareto(states):
    kept=[]; smallest=None
    for point in sorted(states,key=lambda p:(-p[0],p[1],p[2])):
        if smallest is None or point[1]<smallest:
            kept.append(point); smallest=point[1]
    return kept


def pair(horizon,failed,a,b,premiums,epsilon=Fraction(1,4),*,exact=False,continuous=False):
    h,f,ages,q,eps=inputs(horizon,failed,[a,b],premiums,epsilon)
    a,b=ages
    if a>b:
        r=(continuous_later_pair if continuous else later_pair)(h,f,a,b,q)
        if continuous: life=r.limiting_lifetimes; approach=r.approach_indices
        else: life=r.witness; approach=()
        return Pair(r.ratio,r.ratio,life,approach,0,0,True)
    life=tuple(hi if fi else max(hi+1,b+1) for hi,fi in zip(h,f))
    if a==b: return Pair(Fraction(1),Fraction(1),life,(),0,0,True)
    n=len(h)
    ca=Fraction(n)+sum((qi for hi,fi,qi in zip(h,f,q) if fi and hi<=a),Fraction(0))
    cb=Fraction(n)+sum((qi for hi,fi,qi in zip(h,f,q) if fi and hi<=b),Fraction(0))
    ta=sum(min(hi,a) if fi else a for hi,fi in zip(h,f))
    tb=sum(min(hi,b) if fi else b for hi,fi in zip(h,f))
    eligible=sorted((i for i,(hi,fi) in enumerate(zip(h,f)) if not fi and hi<a),
                    key=lambda i:(h[i],q[i],i))
    e=len(eligible)
    if e==0: return Pair(ca*tb/(cb*ta),ca*tb/(cb*ta),life,(),1,1,True)
    subdivisions=(2*e*eps.denominator+eps.numerator-1)//eps.numerator
    minimum=min(q[i] for i in eligible)
    states={0:[(Fraction(0),0,0)]}; peak=1
    for i in eligible:
        new={x:list(points) for x,points in states.items()}
        t=h[i] if continuous else h[i]+1
        for x,points in states.items():
            new.setdefault(x+1,[]).extend((Q+q[i],s+t,mask|(1<<i)) for Q,s,mask in points)
        for x,points in new.items():
            if not exact and x:
                bins={}
                for p in points:
                    key=bucket(p[0],minimum,subdivisions)
                    if key not in bins or (p[1],-p[0],p[2])<(bins[key][1],-bins[key][0],bins[key][2]):
                        bins[key]=p
                points=list(bins.values())
            new[x]=pareto(points)
        states=new; peak=max(peak,sum(map(len,states.values())))
    best=None; selected=0
    for x,points in states.items():
        for Q,s,mask in points:
            value=(ca+Q)*(tb-b*x+s)/((cb+Q)*(ta-a*x+s))
            if best is None or value>best or (value==best and mask<selected):
                best=value; selected=mask
    result=list(life); approach=[]
    for i in eligible:
        if selected&(1<<i):
            result[i]=h[i] if continuous else h[i]+1
            if continuous: approach.append(i)
    factor=Fraction(1) if exact else Fraction(subdivisions+1,subdivisions)**e
    assert factor<=1+eps
    return Pair(best,factor*best,tuple(result),tuple(approach),peak,sum(map(len,states.values())),exact)


def select(horizon,failed,ages,premiums,epsilon=Fraction(1,4),*,exact=False,continuous=False):
    h,f,d,q,eps=inputs(horizon,failed,ages,premiums,epsilon)
    results=[[pair(h,f,a,b,q,eps,exact=exact,continuous=continuous) for b in d] for a in d]
    lower=tuple(max(p.lower for p in row) for row in results)
    upper=tuple(max(p.upper for p in row) for row in results)
    chosen=min(range(len(d)),key=lambda i:(upper[i],lower[i],i))
    competitors=[lower[i] for i in range(len(d)) if i!=chosen]
    certified=not competitors or upper[chosen]<=min(competitors)
    unique=not competitors or upper[chosen]<min(competitors)
    return {'chosen':chosen,'selected_age':d[chosen],'lower_scores':lower,'upper_scores':upper,
            'certified_exact_decision':certified,'certified_unique':unique,'pairs':results,
            'worst_case_decision_factor':1+eps,'continuous':continuous,'exact_mode':exact}
