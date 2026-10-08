import itertools
import unittest
import numpy as np
from method_validation.run import generic_lp, holm, summarize


class ValidationTests(unittest.TestCase):
    def test_holm_known_example(self):
        np.testing.assert_allclose(holm([.01, .04, .03, .002]), [.03, .06, .06, .008])

    def test_holm_order_ties_and_limits(self):
        np.testing.assert_allclose(holm([1., 0., .02, .02]), [1., 0., .06, .06])
        self.assertEqual(holm([.1])[0], .1)

    def test_lp_matches_exhaustive_binary_endpoint_completions(self):
        # Independent enumeration, without importing the implemented bound function.
        for m in [1, 2, 3]:
            h = np.arange(1, m + 1, dtype=float)
            rates = []
            for failure in itertools.product([0, 1], repeat=m):
                for use in itertools.product(*[(x, 10.) for x in h]):
                    rates.append((5. + sum(1 + 4 * f for f in failure)) / (7. + sum(use)))
            actual = generic_lp(5., 7., 1., m, h.sum(), 5., 10., m + 1)
            np.testing.assert_allclose(actual, [min(rates), max(rates), 1 / (m + 1), 1.])

    def test_lp_complete_observation_collapse(self):
        np.testing.assert_allclose(generic_lp(7., 21., 1., 0, 0., 5., 100., 3),
                                   [1 / 3] * 4)

    def test_lp_all_unknown_and_continuous_supremum(self):
        np.testing.assert_allclose(generic_lp(0., 0., 0., 2, 9., 10., 100., 2),
                                   [.01, 20 / 9, 0., 1.])

    def test_lp_scale_and_cap_sensitivity(self):
        base = generic_lp(5., 7., 1., 2, 3., 5., 10., 3)
        doubled = generic_lp(10., 14., 2., 4, 6., 5., 10., 6)
        np.testing.assert_allclose(base, doubled)
        larger = generic_lp(5., 7., 1., 2, 3., 5., 100., 3)
        self.assertLess(larger[0], base[0])
        np.testing.assert_allclose(larger[1:], base[1:])

    def test_summary_zero_observed_does_not_call_complete_case_safe(self):
        sums = [np.array([x], float) for x in [0, 0, 0, 2, 4, 2, 4, 10, 8, 2]]
        out = summarize(sums, np.array([5.]), 2)
        self.assertEqual(out['complete_case_false_safe_fraction'], 0.)
        self.assertEqual(out['healthy_false_safe_fraction'], 1.)
        self.assertEqual(out['hidden_failure_fraction'], 1.)

    def test_summary_complete_information_has_no_false_or_missed_claims(self):
        sums = [np.array([x], float) for x in [2, 20, 0, 0, 0, 2, 10, 2, 20, 0]]
        out = summarize(sums, np.array([5.]), 2)
        self.assertEqual(out['true_gain_fraction'], 1.)
        self.assertEqual(out['certified_gain_fraction'], 1.)
        for name in ['missed_gain_fraction', 'healthy_false_safe_fraction',
                     'complete_case_false_safe_fraction', 'healthy_false_gain_fraction',
                     'complete_case_false_gain_fraction', 'hidden_failure_fraction']:
            self.assertEqual(out[name], 0.)


if __name__ == '__main__':
    unittest.main()
