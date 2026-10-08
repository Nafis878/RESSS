"""Small independent Cartesian oracles; no subset reduction or DP trimming."""
from itertools import product
from fractions import Fraction


def rate(life,age,q):
    return (Fraction(len(life))+sum((qi for t,qi in zip(life,q) if t<=age),Fraction(0)))/sum(min(t,age) for t in life)


def worlds(h,f,ages):
    return product(*[[hi] if fi else range(hi+1,max(hi+1,max(ages)+1)+1) for hi,fi in zip(h,f)])


def integer_pair(h,f,a,b,q):
    return max(rate(life,a,q)/rate(life,b,q) for life in worlds(h,f,[a,b]))


def integer_family(h,f,ages,q):
    scores=[Fraction(1)]*len(ages)
    for life in worlds(h,f,ages):
        rates=[rate(life,a,q) for a in ages]
        best=min(rates)
        scores=[max(score,r/best) for score,r in zip(scores,rates)]
    return scores


def continuous_pair(h,f,a,b,q):
    options=[]
    for hi,fi in zip(h,f):
        if fi:
            choices=[(int(hi<=a),int(hi<=b),min(hi,a),min(hi,b))]
        else:
            choices=[(0,0,a,b)]
            early=min(a,b); late=max(a,b)
            if hi<early:
                choices.extend((1,1,t,t) for t in [hi,early])
            if hi<late:
                for t in [max(hi,early),late]:
                    choices.append((1,0,t,b) if a>b else (0,1,a,t))
        options.append(choices)
    best=Fraction(0)
    for world in product(*options):
        ca=Fraction(len(h))+sum((qi*point[0] for qi,point in zip(q,world)),Fraction(0))
        cb=Fraction(len(h))+sum((qi*point[1] for qi,point in zip(q,world)),Fraction(0))
        ta=sum(point[2] for point in world); tb=sum(point[3] for point in world)
        best=max(best,ca*tb/(cb*ta))
    return best
