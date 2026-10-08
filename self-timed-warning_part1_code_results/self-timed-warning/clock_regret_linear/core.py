"""Exact censored-age relative regret with a two-world later-pair theorem.

Prepared full-family complexity: O(n log n + K^2 n) arithmetic operations.
Standalone later-pair complexity: O(n), at most two objective evaluations.
"""
from dataclasses import dataclass
from fractions import Fraction
import numpy as np
from clock_regret.core import validate


@dataclass
class PairResult:
    ratio: Fraction
    witness: np.ndarray | None
    objective_evaluations: int
    branch: str


def _later(ca, cb, ta, tb, e, m, early_sum, eligible_sum, a, b, q):
    use = ta - m * a + e * (b + 1) + eligible_sum - early_sum
    no_shared = cb * use
    all_shared = (cb + q * e) * (use - e)
    choose_shared = all_shared < no_shared
    value = Fraction((ca + q * m) * tb, min(no_shared, all_shared))
    return value, choose_shared


def _witness(h, failed, a, b, choose_shared=False):
    life = np.where(failed, h, np.maximum(h + 1, max(a, b) + 1))
    if a > b:
        early = ~failed & (h < b)
        middle = ~failed & (h >= b) & (h < a)
        life[early] = b if choose_shared else b + 1
        life[middle] = h[middle] + 1
    return life


class Prepared:
    """Prepare sorted public records once; no hidden lifetimes are accepted."""
    def __init__(self, horizon, logger_failed, ages, rho):
        self.h, self.failed, self.ages, self.rho = validate(horizon, logger_failed, ages, rho)
        self.n = len(self.h)
        self.q = self.rho - 1
        unknown = np.flatnonzero(~self.failed)
        self.unknown_indices = unknown[np.argsort(self.h[unknown], kind='stable')]
        self.unknown = self.h[self.unknown_indices]
        self.uprefix = np.r_[0, np.cumsum(self.unknown + 1)]
        self.known = np.sort(self.h[self.failed])
        self.kprefix = np.r_[0, np.cumsum(self.known)]
        self.base = {}
        self.eligible = {}
        for d in self.ages:
            age = int(d)
            count = int(np.searchsorted(self.known, age, side='right'))
            self.base[age] = (self.n + self.q * count,
                              int(self.kprefix[count]) + (self.n - count) * age)
            self.eligible[age] = int(np.searchsorted(self.unknown, age, side='left'))

    def pair(self, age_a, age_b, include_witness=True):
        a, b = int(age_a), int(age_b)
        if a not in self.base or b not in self.base:
            raise ValueError('pair ages must belong to the prepared candidate pool')
        ca, ta = self.base[a]
        cb, tb = self.base[b]
        if a == b:
            witness = _witness(self.h, self.failed, a, b) if include_witness else None
            return PairResult(Fraction(1), witness, 1, 'identical')
        if a > b:
            e, m = self.eligible[b], self.eligible[a]
            value, shared = _later(ca, cb, ta, tb, e, m, int(self.uprefix[e]),
                                   int(self.uprefix[m]), a, b, self.q)
            witness = _witness(self.h, self.failed, a, b, shared) if include_witness else None
            return PairResult(value, witness, 2 if e else 1,
                              'all_shared' if shared else 'no_shared')
        best = Fraction(ca * tb, cb * ta)
        count = self.eligible[a]
        best_x = 0
        for x in range(count + 1):
            sx = int(self.uprefix[x])
            value = Fraction((ca + self.q * x) * (tb - b * x + sx),
                             (cb + self.q * x) * (ta - a * x + sx))
            if value > best:
                best, best_x = value, x
        witness = None
        if include_witness:
            witness = _witness(self.h, self.failed, a, b)
            selected = self.unknown_indices[:best_x]
            witness[selected] = self.h[selected] + 1
        return PairResult(best, witness, count + 1, f'prefix_{best_x}')


def worst_pair(horizon, logger_failed, age_a, age_b, rho, include_witness=True):
    h, failed, ages, rho = validate(horizon, logger_failed, [age_a, age_b], rho)
    a, b = map(int, ages)
    if a <= b:
        return Prepared(h, failed, [a, b], rho).pair(a, b, include_witness)
    n, q = len(h), rho - 1
    unknown = ~failed
    early = unknown & (h < b)
    eligible = unknown & (h < a)
    e, m = int(early.sum()), int(eligible.sum())
    ca = n + q * int((failed & (h <= a)).sum())
    cb = n + q * int((failed & (h <= b)).sum())
    ta = int(np.minimum(h[failed], a).sum()) + int(unknown.sum()) * a
    tb = int(np.minimum(h[failed], b).sum()) + int(unknown.sum()) * b
    value, shared = _later(ca, cb, ta, tb, e, m, int((h[early] + 1).sum()),
                           int((h[eligible] + 1).sum()), a, b, q)
    witness = _witness(h, failed, a, b, shared) if include_witness else None
    return PairResult(value, witness, 2 if e else 1, 'all_shared' if shared else 'no_shared')


def select(horizon, logger_failed, ages, rho, include_witness=True):
    prepared = Prepared(horizon, logger_failed, ages, rho)
    d = prepared.ages
    pairs = [[prepared.pair(int(a), int(b), include_witness) for b in d] for a in d]
    scores = [max(p.ratio for p in row) for row in pairs]
    chosen = min(range(len(d)), key=lambda j: (scores[j], int(d[j]), j))
    return dict(chosen=chosen, scores=scores, pairs=pairs,
                objective_evaluations=sum(p.objective_evaluations for row in pairs for p in row))
