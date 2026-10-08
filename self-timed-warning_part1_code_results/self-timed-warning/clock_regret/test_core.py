import unittest
from fractions import Fraction
import numpy as np
from clock_regret.core import select, worst_pair, marginal_intervals, outcomes, compatible
from clock_regret.oracles import exhaustive_pair, endpoint_dp_pair


class ClockTests(unittest.TestCase):
    def test_full_clock_exhaustion_250_cases(self):
        rng = np.random.default_rng(82)
        for _ in range(250):
            h = rng.integers(1, 7, int(rng.integers(1, 5)))
            f = rng.integers(0, 2, len(h)).astype(bool)
            a, b = map(int, rng.integers(1, 9, 2))
            rho = int(rng.choice([2, 5, 20]))
            expected, _ = exhaustive_pair(h, f, a, b, rho)
            self.assertEqual(worst_pair(h, f, a, b, rho).ratio, expected)

    def test_generic_endpoint_dp_100_cases(self):
        rng = np.random.default_rng(83)
        for _ in range(100):
            h = rng.integers(1, 20, int(rng.integers(1, 13)))
            f = rng.integers(0, 2, len(h)).astype(bool)
            a, b = map(int, rng.integers(1, 25, 2))
            rho = int(rng.choice([2, 5, 20, 50]))
            expected, _, _ = endpoint_dp_pair(h, f, a, b, rho)
            self.assertEqual(worst_pair(h, f, a, b, rho).ratio, expected)

    def test_equal_ages_cancel_exactly(self):
        ans = worst_pair([1, 10, 2], [False, False, True], 7, 7, 20)
        self.assertEqual(ans.ratio, 1)

    def test_all_lifetimes_observed_collapse(self):
        h = [3, 8, 12, 19]
        ans = select(h, [True] * 4, [5, 10, 15], 5)
        c, t, _ = outcomes(h, [5, 10, 15], 5)
        rates = [Fraction(int(c[:, j].sum()), int(t[:, j].sum())) for j in range(3)]
        self.assertEqual(ans['chosen'], min(range(3), key=lambda j: rates[j]))
        for i in range(3):
            for j in range(3):
                self.assertEqual(ans['pairs'][i][j].ratio, rates[i] / rates[j])

    def test_failure_at_deadline_is_failure(self):
        c, t, f = outcomes([8], [8, 7], 20)
        self.assertEqual(c.tolist(), [[20, 1]])
        self.assertEqual(t.tolist(), [[8, 7]])
        self.assertEqual(f.tolist(), [[True, False]])

    def test_no_lifetime_cap_needed(self):
        h = [1000000, 1]
        ans = worst_pair(h, [False, False], 4, 8, 5)
        self.assertTrue(compatible(ans.witness, np.array(h), np.array([False, False])))
        self.assertGreater(ans.witness[0], 1000000)

    def test_rectangle_is_strictly_looser_same_information(self):
        ans = select([6] * 12, [False] * 12, [8, 12, 16, 24], 20)
        self.assertEqual(ans['chosen'], 0)
        self.assertEqual(ans['rectangle'], 3)
        self.assertLess(ans['scores'][ans['chosen']], ans['scores'][ans['rectangle']])
        for j in range(4):
            self.assertLessEqual(ans['scores'][j], ans['rectangle_scores'][j])

    def test_marginal_bounds_are_individually_sharp(self):
        h = np.array([2, 9, 4])
        f = np.array([False, False, True])
        for age, (low, high) in zip([3, 6, 10], marginal_intervals(h, f, [3, 6, 10], 5)):
            values = []
            import itertools
            for life in itertools.product(range(3, 12), range(10, 12), [4]):
                c, t, _ = outcomes(life, [age], 5)
                values.append(Fraction(int(c.sum()), int(t.sum())))
            self.assertEqual(low, min(values))
            self.assertEqual(high, max(values))

    def test_hidden_lifetime_mutation_leaves_selection_unchanged(self):
        h = [6, 6, 3, 6]
        f = [False, False, True, False]
        one = select(h, f, [8, 12, 16, 24], 20)
        # Neither sealed completion is passed to the selector.
        self.assertTrue(compatible([7, 7, 3, 7], np.array(h), np.array(f)))
        self.assertTrue(compatible([100, 200, 3, 400], np.array(h), np.array(f)))
        two = select(h, f, [8, 12, 16, 24], 20)
        self.assertEqual(one['scores'], two['scores'])
        self.assertEqual(one['chosen'], two['chosen'])

    def test_permutation_of_assets_and_policies(self):
        h = np.array([2, 8, 4, 10])
        f = np.array([False, True, False, False])
        d = np.array([3, 6, 12])
        original = select(h, f, d, 5)
        permuted = select(h[::-1], f[::-1], d[::-1], 5)
        self.assertEqual(d[original['chosen']], d[::-1][permuted['chosen']])
        self.assertEqual(original['scores'], list(reversed(permuted['scores'])))

    def test_duplicate_policy_does_not_change_optimum(self):
        one = select([2, 4, 6], [False, True, False], [3, 8, 12], 5)
        two = select([2, 4, 6], [False, True, False], [3, 8, 12, 8], 5)
        self.assertEqual(one['scores'], two['scores'][:3])
        self.assertEqual(one['chosen'], two['chosen'])

    def test_invalid_inputs_rejected(self):
        for args in [([], [], [1], 5), ([1.5], [False], [2], 5), ([1], [2], [2], 5),
                     ([1], [False], [0], 5), ([1], [False], [2], 1), ([1], [False], [2], 2.5),
                     ([np.iinfo(np.int64).max], [False], [2], 5),
                     ([1, 1], [False, False], [np.iinfo(np.int64).max // 2], 5),
                     ([1, 1], [False, False], [2], np.iinfo(np.int64).max // 2)]:
            with self.assertRaises(ValueError):
                select(*args)


if __name__ == '__main__':
    unittest.main()
