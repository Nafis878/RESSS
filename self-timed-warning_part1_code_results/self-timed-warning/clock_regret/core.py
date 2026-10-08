"""Exact shared-lifetime relative regret for fixed integer replacement ages.

Known tools: age replacement and minimax relative regret. Candidate contribution:
the ordered failure-phase reduction for censored finite-cohort renewal ratios.
"""
from dataclasses import dataclass
from fractions import Fraction
import numpy as np


def validate(horizon, logger_failed, ages, rho):
    h = np.asarray(horizon)
    failed = np.asarray(logger_failed)
    d = np.asarray(ages)
    if h.ndim != 1 or not len(h) or failed.shape != h.shape or d.ndim != 1 or not len(d):
        raise ValueError('nonempty aligned records and age vector required')
    if not np.isfinite(h).all() or not np.isfinite(d).all() or (h < 1).any() or (d < 1).any():
        raise ValueError('positive finite times required')
    if not np.equal(h, np.floor(h)).all() or not np.equal(d, np.floor(d)).all():
        raise ValueError('integer-clock model required')
    if not np.isin(failed, [0, 1]).all() or not np.isfinite(rho) or rho <= 1 or int(rho) != rho:
        raise ValueError('binary logger indicators and common integer cost ratio required')
    # Fractions use arbitrary-precision integers, but clock arrays and prefix
    # sums use int64. Reserve room for every cohort total and H+1 witness.
    if len(h) * (max(int(h.max()), int(d.max()), int(rho)) + 1) > np.iinfo(np.int64).max:
        raise ValueError('clock/cost magnitudes exceed safe int64 cohort totals')
    return h.astype(np.int64), failed.astype(bool), d.astype(np.int64), int(rho)


def outcomes(life, ages, rho):
    life = np.asarray(life, dtype=np.int64)
    d = np.asarray(ages, dtype=np.int64)
    f = life[:, None] <= d[None, :]
    use = np.minimum(life[:, None], d[None, :])
    cost = 1 + (rho - 1) * f.astype(np.int64)
    return cost, use, f


def compatible(life, h, failed):
    life = np.asarray(life)
    return bool(np.all(life[failed] == h[failed]) and np.all(life[~failed] > h[~failed]))


@dataclass
class PairResult:
    ratio: Fraction
    witness: np.ndarray
    count_cases: int


def worst_pair(horizon, logger_failed, age_a, age_b, rho):
    h, failed, d, rho = validate(horizon, logger_failed, [age_a, age_b], rho)
    a, b = map(int, d)
    n = len(h)
    # This completion represents the joint-survival phase; it is not a life cap.
    witness = np.where(failed, h, np.maximum(h + 1, max(a, b) + 1))
    known_c, known_t, _ = outcomes(h[failed], [a, b], rho)
    unknown = np.flatnonzero(~failed)
    ca = int(known_c[:, 0].sum()) + len(unknown)
    cb = int(known_c[:, 1].sum()) + len(unknown)
    ta = int(known_t[:, 0].sum()) + len(unknown) * a
    tb = int(known_t[:, 1].sum()) + len(unknown) * b
    if a == b:
        return PairResult(Fraction(1), witness, 1)
    best = Fraction(ca * tb, cb * ta)
    best_counts = (0, 0)
    cases = 0
    if a < b:
        eligible = unknown[h[unknown] < a]
        eligible = eligible[np.argsort(h[eligible], kind='stable')]
        prefix = np.r_[0, np.cumsum(h[eligible] + 1)].tolist()
        for x in range(len(eligible) + 1):
            xa = ta - x * a + int(prefix[x])
            xb = tb - x * b + int(prefix[x])
            value = Fraction((ca + (rho - 1) * x) * xb,
                             (cb + (rho - 1) * x) * xa)
            cases += 1
            if value > best:
                best = value
                best_counts = (x, 0)
        x, _ = best_counts
        witness[eligible[:x]] = h[eligible[:x]] + 1
    else:
        early = unknown[h[unknown] < b]
        middle = unknown[(h[unknown] >= b) & (h[unknown] < a)]
        middle = middle[np.argsort(h[middle], kind='stable')]
        choices = np.r_[early, middle].astype(np.int64)
        gains = a - np.maximum(h[choices] + 1, b + 1)
        # Early-phase choices all have the largest (equal) later-only gain.
        assert not len(gains) or np.all(gains[:-1] >= gains[1:])
        prefix = np.r_[0, np.cumsum(gains)].tolist()
        for x in range(len(early) + 1):
            for y in range(len(choices) - x + 1):
                xa = ta - x * (a - b) - (int(prefix[x + y]) - int(prefix[x]))
                value = Fraction((ca + (rho - 1) * (x + y)) * tb,
                                 (cb + (rho - 1) * x) * xa)
                cases += 1
                if value > best:
                    best = value
                    best_counts = (x, y)
        x, y = best_counts
        witness[early[:x]] = b
        chosen = choices[x:x + y]
        witness[chosen] = np.maximum(h[chosen] + 1, b + 1)
    assert compatible(witness, h, failed)
    c, t, _ = outcomes(witness, [a, b], rho)
    actual = Fraction(int(c[:, 0].sum()) * int(t[:, 1].sum()),
                      int(c[:, 1].sum()) * int(t[:, 0].sum()))
    assert actual == best, (a, b, actual, best, best_counts, n)
    return PairResult(best, witness, cases)


def marginal_intervals(horizon, logger_failed, ages, rho):
    h, failed, d, rho = validate(horizon, logger_failed, ages, rho)
    result = []
    for age in d:
        o = failed | (h >= age)
        f = failed & (h <= age)
        kc = int(np.where(o, 1 + (rho - 1) * f, 0).sum())
        kt = int(np.where(o, np.minimum(h, age), 0).sum())
        m = int((~o).sum())
        lower = Fraction(kc + m, kt + m * int(age))
        upper = Fraction(kc + rho * m, kt + int((h[~o] + 1).sum()))
        result.append((lower, upper))
    return result


def select(horizon, logger_failed, ages, rho):
    h, failed, d, rho = validate(horizon, logger_failed, ages, rho)
    k = len(d)
    pairs = [[worst_pair(h, failed, a, b, rho) for b in d] for a in d]
    scores = [max(row.ratio for row in rows) for rows in pairs]
    # Lower age is the explicit deterministic tie break for every selector.
    chosen = min(range(k), key=lambda j: (scores[j], int(d[j]), j))
    intervals = marginal_intervals(h, failed, d, rho)
    rect = [max(Fraction(1) if i == j else intervals[i][1] / intervals[j][0]
                for j in range(k)) for i in range(k)]
    rectangle = min(range(k), key=lambda j: (rect[j], int(d[j]), j))
    upper = min(range(k), key=lambda j: (intervals[j][1], int(d[j]), j))
    cc = []
    for age in d:
        o = failed | (h >= age)
        f = failed & (h <= age)
        if o.any():
            cc.append(Fraction(int((1 + (rho - 1) * f[o]).sum()), int(np.minimum(h[o], age).sum())))
        else:
            cc.append(None)
    cc_chosen = min(range(k), key=lambda j: (cc[j] is None, cc[j] or Fraction(0), int(d[j]), j))
    return dict(chosen=chosen, rectangle=rectangle, upper_rate=upper, complete_case=cc_chosen,
                pairs=pairs, scores=scores, rectangle_scores=rect, marginal_intervals=intervals,
                risk_upper=[Fraction(int((failed & (h <= age)).sum()) + int((~failed & (h < age)).sum()), len(h)) for age in d])
