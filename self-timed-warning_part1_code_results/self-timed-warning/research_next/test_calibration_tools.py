"""Tests for the isolated audit/reference code; no new-method claim."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np
import calibration_tools as T


class Tests(unittest.TestCase):
    def test_rank_at_feasibility_boundary(self):
        self.assertEqual(T.grid_threshold(np.arange(1,20),.05,np.arange(1,61)),(19.,True))
        self.assertEqual(T.grid_threshold(np.arange(1,19),.05,np.arange(1,61)),(60.,False))
    def test_empty_and_infinite_fallback(self):
        self.assertEqual(T.grid_threshold([],.05,[1,2]),(2.,False))
        self.assertEqual(T.grid_threshold([np.inf]*19,.05,[1,2]),(2.,False))
    def test_grid_rounding_and_unavailable_action(self):
        self.assertEqual(T.grid_threshold([3.1]*19,.05,[3,6,9]),(6.,True))
        self.assertEqual(T.grid_threshold([10]*19,.05,[3,6,9]),(9.,False))
    def test_selection_independent_of_order(self):
        s=np.arange(1,81)
        self.assertEqual(T.grid_threshold(s,.05,np.arange(1,100)),T.grid_threshold(np.random.default_rng(2026).permutation(s),.05,np.arange(1,100)))
    def test_invalid_inputs(self):
        for s,a,g in [([np.nan],.05,[1,2]),([1],0,[1,2]),([1],1,[1,2]),([1],.05,[2,1]),([1],.05,[])]:
            with self.assertRaises(ValueError):T.grid_threshold(s,a,g)
    def test_paired_binary(self):
        z=T.paired_binary([0]*10,[1]*10)
        self.assertEqual((z['rescued'],z['harmed'],z['difference']),(10,0,-1.))
        self.assertAlmostEqual(z['p'],2/1024)
        self.assertEqual(T.paired_binary([0,1],[0,1])['p'],1.)
    def test_holm(self):
        np.testing.assert_allclose(T.holm([.01,.04,.03]),[.03,.06,.06])
        self.assertEqual(len(T.holm([])),0)
    def test_renewal_contrast_hand_calculation(self):
        # The only unordered pair: h=.5*(1*4+2*4-3*2-4*1)=1.
        self.assertEqual(T.renewal_contrast([1,2],[1,2],[3,4],[4,4]),1.)
        self.assertEqual(T.renewal_contrast([1,1],[2,2],[1,1],[2,2]),0.)
        with self.assertRaises(ValueError):T.renewal_contrast([1],[1],[1],[1])
    def test_zero_failure_upper_stability(self):
        self.assertAlmostEqual(T.zero_failure_upper(1),.95)
        self.assertAlmostEqual(T.zero_failure_upper(59),1-.05**(1/59))
        self.assertGreater(T.zero_failure_upper(58),.05)
        self.assertLess(T.zero_failure_upper(59),.05)
        self.assertGreater(T.zero_failure_upper(80,.05/2160),T.zero_failure_upper(80))
    def test_bootstrap_reproducibility(self):
        args=([1,5,1],[10,20,30],[1,1,5],[15,25,35])
        self.assertEqual(T.bootstrap_ratio(*args),T.bootstrap_ratio(*args))
        self.assertEqual(T.bootstrap_ratio([1,1],[2,2],[1,1],[2,2]),(1.,1.,1.))
    def test_numerical_and_pair_guard(self):
        self.assertAlmostEqual(T.ratio([1e100,1e100],[1e101,1e101]),.1)
        with self.assertRaises(ValueError):T.ratio([1],[0])
        with self.assertRaises(ValueError):T.bootstrap_ratio([1,1],[2,2],[1],[2])


if __name__=='__main__':unittest.main(verbosity=2)
