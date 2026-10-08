"""Independent general-state checks; never use the ordered count reduction."""
import itertools
from fractions import Fraction
import numpy as np
from clock_regret.core import outcomes


def exhaustive_pair(h, failed, a, b, rho):
    choices = [[int(x)] if f else range(int(x) + 1, max(int(x) + 1, a + 1, b + 1) + 1)
               for x, f in zip(h, failed)]
    best = Fraction(0)
    count = 0
    for life in itertools.product(*choices):
        c, t, _ = outcomes(life, [a, b], rho)
        value = Fraction(int(c[:, 0].sum()) * int(t[:, 1].sum()),
                         int(c[:, 1].sum()) * int(t[:, 0].sum()))
        best = max(best, value)
        count += 1
    return best, count


def hull(points):
    points = sorted(set(points))
    if len(points) < 3:
        return points

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def endpoint_dp_pair(h, failed, a, b, rho):
    # Generic failure-count DP with two-dimensional exposure hulls. No sorting
    # theorem, phase domination rule or project-specific closed form is used.
    states = {(0, 0): [(0, 0)]}
    transitions = 0
    for horizon, known in zip(h, failed):
        horizon = int(horizon)
        if known:
            clocks = [horizon]
        else:
            low = horizon + 1
            clocks = sorted({low, max(low, a), max(low, a + 1),
                             max(low, b), max(low, b + 1)})
        opts = []
        for life in clocks:
            opts.append((int(life <= a), int(life <= b), min(life, a), min(life, b)))
        opts = sorted(set(opts))
        new = {}
        for (fa, fb), exposures in states.items():
            for ia, ib, ta, tb in opts:
                key = (fa + ia, fb + ib)
                new.setdefault(key, []).extend((x + ta, y + tb) for x, y in exposures)
                transitions += len(exposures)
        states = {key: hull(points) for key, points in new.items()}
    best = Fraction(0)
    n = len(h)
    for (fa, fb), exposures in states.items():
        ca, cb = n + (rho - 1) * fa, n + (rho - 1) * fb
        for ta, tb in exposures:
            best = max(best, Fraction(ca * tb, cb * ta))
    return best, transitions, sum(map(len, states.values()))
