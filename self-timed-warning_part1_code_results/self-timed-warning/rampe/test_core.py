import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import core as R


class Tests(unittest.TestCase):
    def test_binomial_boundary(self):
        self.assertAlmostEqual(R.upper(0,59,.05),1-.05**(1/59))
        self.assertEqual(R.upper(5,5,.05),1)
        self.assertEqual(R.upper(0,0,.05),1)
        self.assertTrue(np.isfinite(R.upper(0,100,1e-30)))
    def test_invalid_counts(self):
        for args in [(-1,2,.05),(3,2,.05),(-1,-1,.05),(0,2,0)]:
            with self.assertRaises(ValueError):R.upper(*args)
    def test_ratio_of_sums(self):
        c=np.array([[1,2],[2,2]]);t=np.array([[1,2],[3,2]])
        e=R.evidence(c,t,c>1,['a','a'],'a')
        np.testing.assert_allclose(e.cost,[.75,1])
    def test_bootstrap_reproducibility(self):
        args=(np.array([[1,2],[2,1],[1,1]]),np.full((3,2),10),np.array([[0,1],[1,0],[0,0]]),['a']*3,'a')
        a=R.evidence(*args,seed=9);b=R.evidence(*args,seed=9)
        np.testing.assert_array_equal(a.uncertainty,b.uncertainty)
        np.testing.assert_array_equal(a.stability,b.stability)
    def test_stability_ties(self):
        np.testing.assert_array_equal(R.winning_share(np.array([[1,1],[1,1]])),[1,1])
        np.testing.assert_array_equal(R.winning_share(np.array([[1,2],[2,1]])),[.5,.5])
    def test_small_sample_abstention(self):
        c=np.ones((10,4));t=np.ones((10,4))*10;f=np.zeros((10,4),bool)
        e=R.evidence(c,t,f,['a']*10,'a')
        self.assertEqual(R.choose(e),(3,True))
    def test_large_sample_eligible(self):
        c=np.ones((1000,3));t=np.tile([10,6,9],(1000,1));f=np.zeros_like(c,bool)
        e=R.evidence(c,t,f,['a']*1000,'a')
        self.assertEqual(R.choose(e,fallback=1),(0,False))
    def test_unknown_context_and_transfer_removal(self):
        c=np.ones((1000,3));t=np.tile([10,6,9],(1000,1));f=np.zeros_like(c,bool)
        e=R.evidence(c,t,f,['a']*1000,'b')
        self.assertEqual(R.choose(e,fallback=1),(1,True))
        self.assertEqual(R.choose(e,'RAMPE_no_transfer',fallback=1),(0,False))
    def test_no_abstention(self):
        e=R.evidence(np.ones((2,3)),np.tile([10,6,9],(2,1)),np.zeros((2,3)),['a']*2,'a')
        self.assertEqual(R.choose(e,'RAMPE_no_abstention',fallback=1),(0,False))
    def test_one_unit_numerics(self):
        e=R.evidence([[1e100,2e100]],[[1e101,2e101]],[[0,0]],['a'],'a')
        self.assertTrue(np.isfinite(e.features()).all())
        self.assertEqual(R.choose(e,fallback=1),(1,True))
    def test_validated_inputs(self):
        for args in [([[np.nan]],[[1]],[[0]]),([[1]],[[0]],[[0]]),([[1]],[[1]],[[2]]),([],[],[])]:
            with self.assertRaises(ValueError):R.validate(*args)
    def test_lottery_selects_policies(self):
        self.assertEqual(R.draw_policy([.25,.75],.1),0)
        self.assertEqual(R.draw_policy([.25,.75],.7),1)
        with self.assertRaises(ValueError):R.draw_policy([.2,.3],.5)
    def test_weight_normalization_and_repro(self):
        e=R.evidence([[1,2],[1,2]],[[5,5],[5,5]],[[0,0],[0,0]],['a','a'],'a')
        for kind in ['uniform','random','inverse_cost','reliability']:
            w=R.weights(e,kind);self.assertAlmostEqual(w.sum(),1)
            np.testing.assert_array_equal(w,R.weights(e,kind))
    def test_metrics_hand_calculation(self):
        z=R.metrics([[1,5],[1,5]],[[10,20],[10,20]],[[0,1],[0,1]],[0,1],[0,1])
        self.assertAlmostEqual(z['cost_rate'],6/30)
        self.assertEqual(z['failures'],1);self.assertEqual(z['abstention'],.5)
    def test_component_removal(self):
        e=R.evidence(np.ones((10,3)),np.tile([10,6,9],(10,1)),np.zeros((10,3)),['a']*10,'a')
        self.assertEqual(R.choose(e,'RAMPE_no_calibration',fallback=1),(0,False))
        self.assertEqual(R.choose(e,'RAMPE_no_reliability',fallback=1),R.choose(e,'conventional',fallback=1))
    def test_unsupported_selector(self):
        e=R.evidence([[1]],[[1]],[[0]],['a'],'a')
        with self.assertRaises(ValueError):R.choose(e,'fake',fallback=0)
    def test_fractional_context_oracle(self):
        from synthetic import oracle
        c=np.array([[1.,11.],[10.,10.]]);t=np.array([[10.,100.],[10.,10.]])
        a,r=oracle(c,t,np.zeros((2,2)),np.array([.5,.5]))
        self.assertEqual(a[0],1);self.assertAlmostEqual(r,21/110)
        self.assertGreater(11/20,r)  # greedy local ratios are globally inferior
    def test_no_reliable_oracle(self):
        from synthetic import oracle
        a,r=oracle(np.ones((2,2)),np.ones((2,2)),np.ones((2,2)),np.array([.5,.5]))
        self.assertTrue(np.isnan(r));np.testing.assert_array_equal(a,[-1,-1])
    def test_mixture_renewal_rate(self):
        c=np.array([1.,10.]);t=np.array([10.,20.]);w=np.array([.3,.7])
        r=(w*c).sum()/(w*t).sum();weights=w*t/(w*t).sum()
        self.assertAlmostEqual(r,(weights*(c/t)).sum());self.assertGreaterEqual(r,min(c/t))


if __name__=='__main__':unittest.main(verbosity=2)
