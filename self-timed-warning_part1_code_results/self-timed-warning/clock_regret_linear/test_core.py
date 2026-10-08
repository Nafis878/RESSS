import unittest
from fractions import Fraction
import numpy as np
from clock_regret.core import worst_pair as quadratic
from clock_regret.oracles import exhaustive_pair, endpoint_dp_pair
from clock_regret_linear.core import Prepared, select, worst_pair
from clock_regret_linear.continuous import ContinuousPrepared, closure_state_pair


def attained(result, h, failed, a, b, rho):
    life = result.witness
    assert life is not None
    assert np.array_equal(life[failed], h[failed]) and (life[~failed] > h[~failed]).all()
    n = len(h)
    return Fraction((n + (rho-1)*int((life <= a).sum())) * int(np.minimum(life, b).sum()),
                    (n + (rho-1)*int((life <= b).sum())) * int(np.minimum(life, a).sum()))


class LinearTests(unittest.TestCase):
    def test_full_integer_clock_exhaustion_1000(self):
        rng = np.random.default_rng(1201)
        for _ in range(1000):
            h = rng.integers(1, 7, int(rng.integers(1, 5)))
            failed = rng.random(len(h)) < .4
            a, b = map(int, rng.integers(1, 9, 2))
            rho = int(rng.choice([2, 5, 20]))
            result = worst_pair(h, failed, a, b, rho)
            self.assertEqual(result.ratio, exhaustive_pair(h, failed, a, b, rho)[0])
            self.assertEqual(result.ratio, attained(result, h, failed, a, b, rho))

    def test_separate_general_state_oracle_500(self):
        rng = np.random.default_rng(1202)
        for _ in range(500):
            h = rng.integers(1, 20, int(rng.integers(1, 13)))
            failed = rng.random(len(h)) < .3
            a, b = map(int, rng.integers(1, 25, 2))
            rho = int(rng.choice([2, 5, 20, 50]))
            result = worst_pair(h, failed, a, b, rho)
            self.assertEqual(result.ratio, endpoint_dp_pair(h, failed, a, b, rho)[0])

    def test_frozen_quadratic_algorithm_300_larger_cases(self):
        rng = np.random.default_rng(1203)
        for _ in range(300):
            h = rng.integers(1, 70, int(rng.integers(12, 121)))
            failed = rng.random(len(h)) < .35
            a, b = map(int, rng.integers(1, 90, 2))
            rho = int(rng.choice([2, 5, 20, 50]))
            result = worst_pair(h, failed, a, b, rho)
            self.assertEqual(result.ratio, quadratic(h, failed, a, b, rho).ratio)

    def test_both_endpoint_branches_and_equality(self):
        cases = [([1], [False], 3, 2, 2, 'no_shared'),
                 ([1]*5, [True]*4+[False], 3, 2, 2, 'all_shared'),
                 ([1]*2, [True, False], 3, 2, 2, 'no_shared')]
        for h, f, a, b, rho, branch in cases:
            h, f = np.array(h), np.array(f)
            ans = worst_pair(h, f, a, b, rho)
            self.assertEqual(ans.branch, branch)
            self.assertEqual(ans.ratio, quadratic(h, f, a, b, rho).ratio)
            self.assertEqual(ans.ratio, attained(ans, h, f, a, b, rho))

    def test_later_pair_at_most_two_objectives(self):
        for n in [1, 10, 100, 10000]:
            answer = worst_pair(np.ones(n, dtype=int), np.zeros(n, bool), 40, 20, 20)
            self.assertLessEqual(answer.objective_evaluations, 2)

    def test_earlier_pair_can_have_strict_interior_count(self):
        answer = worst_pair([1,1,1,5], [False,False,False,True], 4, 20, 20)
        self.assertEqual(answer.branch, 'prefix_1')
        self.assertEqual(answer.ratio, Fraction(1081,588))
        self.assertGreater(answer.ratio, 1)

    def test_continuous_identical_age_has_no_later_only_phase(self):
        h, f = [19,8], [True,False]
        self.assertEqual(closure_state_pair(h,f,23,23,2), 1)
        self.assertEqual(ContinuousPrepared(h,f,[23],2).pair(23,23).ratio, 1)

    def test_continuous_limit_is_not_an_attaining_witness(self):
        answer = ContinuousPrepared([1]*5,[True]*4+[False],[3,2],2).pair(3,2)
        self.assertEqual(answer.ratio, Fraction(10,9))
        self.assertFalse(answer.attained)
        self.assertEqual(answer.limiting_lifetimes[-1], 2)

    def test_compatible_epsilon_sequence_approaches_supremum(self):
        answer = ContinuousPrepared([1]*5,[True]*4+[False],[3,2],2).pair(3,2)
        values=[]
        for epsilon in [Fraction(1,2),Fraction(1,10),Fraction(1,1000)]:
            life=answer.completion(epsilon)
            self.assertGreater(life[-1], 1)
            ca=sum(1+int(t<=3) for t in life)
            cb=sum(1+int(t<=2) for t in life)
            ratio=Fraction(ca,cb)*sum(min(t,2) for t in life)/sum(min(t,3) for t in life)
            self.assertLess(ratio, answer.ratio)
            values.append(ratio)
        self.assertEqual(values, sorted(values))

    def test_resolution_error_example_and_bound(self):
        continuous = Fraction(10,9)
        previous=Fraction(0)
        for r in [1,2,4,16,64]:
            answer=worst_pair([r]*5,[True]*4+[False],3*r,2*r,2)
            self.assertLessEqual(previous,answer.ratio)
            self.assertLessEqual(answer.ratio,continuous)
            self.assertLessEqual(continuous,Fraction(r+1,r)*answer.ratio)
            previous=answer.ratio

    def test_prepared_and_standalone_agree(self):
        h = [2, 8, 1, 12, 5]
        f = [False, True, True, False, False]
        ages = [3, 6, 12, 20]
        prep = Prepared(h, f, ages, 5)
        for a in ages:
            for b in ages:
                self.assertEqual(prep.pair(a, b).ratio, worst_pair(h, f, a, b, 5).ratio)

    def test_fully_observed_and_duplicates(self):
        answer = select([1, 8, 12], [True]*3, [2, 10, 16, 10], 5)
        self.assertEqual(answer['scores'][1], answer['scores'][3])
        self.assertEqual(answer['pairs'][1][3].ratio, 1)
        self.assertEqual(min(answer['scores']), 1)

    def test_permutation_and_witness_omission(self):
        h, f, d = np.array([2, 5, 1, 9]), np.array([False, True, True, False]), np.array([3, 8, 12])
        a = select(h, f, d, 5)
        b = select(h[::-1], f[::-1], d[::-1], 5, include_witness=False)
        self.assertEqual(a['scores'], b['scores'][::-1])
        self.assertEqual(d[a['chosen']], d[::-1][b['chosen']])
        self.assertTrue(all(p.witness is None for row in b['pairs'] for p in row))

    def test_no_life_cap(self):
        ans = worst_pair([1000000, 1], [False, False], 8, 4, 5)
        self.assertGreater(ans.witness[0], 1000000)

    def test_bad_inputs_and_overflow(self):
        for args in [([], [], [2], 5), ([1.5], [False], [2], 5), ([1], [2], [2], 5),
                     ([1], [False], [0], 5), ([1], [False], [2], 1),
                     ([np.iinfo(np.int64).max], [False], [2], 5)]:
            with self.assertRaises(ValueError):
                select(*args)
        with self.assertRaises(ValueError):
            Prepared([1], [False], [2], 5).pair(2, 3)


if __name__ == '__main__':
    unittest.main()
