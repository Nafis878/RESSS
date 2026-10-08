"""Continuous supremum and compatible epsilon sequences; never label limits truth."""
from dataclasses import dataclass
from fractions import Fraction
import numpy as np
from clock_regret.oracles import hull
from clock_regret_linear.core import Prepared


@dataclass
class ContinuousPair:
    ratio: Fraction
    limiting_lifetimes: np.ndarray
    approach_indices: np.ndarray
    objective_evaluations: int
    attained: bool

    def completion(self, epsilon=Fraction(1, 1000)):
        epsilon = Fraction(epsilon)
        if not 0 < epsilon < 1:
            raise ValueError('epsilon must be strictly between zero and one')
        result = [Fraction(int(t)) for t in self.limiting_lifetimes]
        for i in self.approach_indices:
            result[int(i)] += epsilon
        return result


class ContinuousPrepared(Prepared):
    def __init__(self, horizon, logger_failed, ages, rho):
        super().__init__(horizon, logger_failed, ages, rho)
        self.uprefix = np.r_[0, np.cumsum(self.unknown)]

    def pair(self, age_a, age_b):
        a, b = int(age_a), int(age_b)
        if a not in self.base or b not in self.base:
            raise ValueError('pair ages must belong to the prepared candidate pool')
        ca, ta = self.base[a]
        cb, tb = self.base[b]
        limit = np.where(self.failed, self.h, np.maximum(self.h+1, max(a,b)+1))
        if a == b:
            return ContinuousPair(Fraction(1), limit, np.array([], dtype=int), 1, True)
        if a > b:
            e, m = self.eligible[b], self.eligible[a]
            use = ta-m*a+e*b+int(self.uprefix[m])-int(self.uprefix[e])
            value = Fraction((ca+self.q*m)*tb, cb*use)
            indices = self.unknown_indices[:m]
            limit[indices] = np.maximum(self.h[indices], b)
            return ContinuousPair(value, limit, indices, 1, not m)
        best, best_x = Fraction(ca*tb,cb*ta), 0
        count = self.eligible[a]
        for x in range(count+1):
            sx = int(self.uprefix[x])
            value = Fraction((ca+self.q*x)*(tb-b*x+sx), (cb+self.q*x)*(ta-a*x+sx))
            if value > best:
                best, best_x = value, x
        indices = self.unknown_indices[:best_x]
        limit[indices] = self.h[indices]
        return ContinuousPair(best, limit, indices, count+1, not best_x)


def select(horizon, logger_failed, ages, rho):
    prepared = ContinuousPrepared(horizon, logger_failed, ages, rho)
    d = prepared.ages
    pairs = [[prepared.pair(a,b) for b in d] for a in d]
    scores = [max(p.ratio for p in row) for row in pairs]
    chosen = min(range(len(d)), key=lambda j:(scores[j],int(d[j]),j))
    return dict(chosen=chosen,scores=scores,pairs=pairs)


def closure_state_pair(h, failed, a, b, rho):
    """Independent phase-labeled endpoint/exposure-hull DP on the closure.

    Limiting times at a phase boundary retain the specified failure flags.
    Computing flags solely from limiting times would incorrectly include
    censoring/deadline atoms in the wrong phase.
    """
    states = {(0,0):[(0,0)]}
    lo, hi = min(a,b), max(a,b)
    for time, known in zip(h,failed):
        time = int(time)
        if known:
            options = [(int(time<=a),int(time<=b),min(time,a),min(time,b))]
        else:
            options = [(0,0,a,b)]
            if time < lo:
                options += [(1,1,t,t) for t in [time,lo]]
            if lo < hi and time < hi:
                for t in [max(time,lo),hi]:
                    options.append((0,1,a,t) if a<b else (1,0,t,b))
        updated = {}
        for (fa,fb), points in states.items():
            for ia,ib,ta,tb in options:
                updated.setdefault((fa+ia,fb+ib),[]).extend((x+ta,y+tb) for x,y in points)
        states = {key:hull(points) for key,points in updated.items()}
    n = len(h)
    return max(Fraction((n+(rho-1)*fa)*tb,(n+(rho-1)*fb)*ta)
               for (fa,fb),points in states.items() for ta,tb in points)
