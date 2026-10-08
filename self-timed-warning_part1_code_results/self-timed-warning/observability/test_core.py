import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import numpy as np
from observability.core import identify,visible_view,complete_case,healthy_imputation

class Tests(unittest.TestCase):
    def fixture(self):return visible_view([10,10],[True,False],[1,50],[8,11],[0,1])
    def test_all_observed_exact(self):
        x=identify(**visible_view([10,12],[True,True],[1,10],[8,12],[0,1]),rho=10,cap=100)
        self.assertAlmostEqual(x.rate_low,11/20);self.assertEqual(x.rate_low,x.rate_high);self.assertEqual(x.risk_low,.5);self.assertEqual(x.risk_low,x.risk_high)
    def test_none_observed(self):
        x=identify(**visible_view([10,20],[False,False],[10,1],[11,21],[1,0]),rho=10,cap=100)
        self.assertAlmostEqual(x.rate_low,.01);self.assertAlmostEqual(x.rate_high,20/30);self.assertEqual((x.risk_low,x.risk_high),(0,1))
    def test_ratio_manual(self):
        x=identify(**self.fixture(),rho=50,cap=100)
        self.assertAlmostEqual(x.rate_low,2/108);self.assertAlmostEqual(x.rate_high,51/18);self.assertEqual(x.risk_high,.5)
    def test_hidden_truth_mutation(self):
        v=self.fixture();w=visible_view([10,10],[True,False],[1,1],[8,100],[0,0])
        for key in v:np.testing.assert_array_equal(v[key],w[key])
        self.assertEqual(identify(**v,rho=50,cap=100),identify(**w,rho=50,cap=100))
    def test_refuses_leakage(self):
        v=self.fixture();v['fail'][1]=1
        with self.assertRaises(ValueError):identify(**v,rho=50,cap=100)
    def test_accounting_consistency(self):
        v=self.fixture();v['cost'][0]=50
        with self.assertRaises(ValueError):identify(**v,rho=50,cap=100)
    def test_invalid_cap(self):
        with self.assertRaises(ValueError):identify(**self.fixture(),rho=50,cap=10)
    def test_cap_sensitivity_upper_invariant(self):
        a=identify(**self.fixture(),rho=50,cap=100);b=identify(**self.fixture(),rho=50,cap=1000)
        self.assertEqual(a.rate_high,b.rate_high);self.assertGreater(a.rate_low,b.rate_low)
    def test_constructive_extremes(self):
        v=self.fixture();x=identify(**v,rho=50,cap=100)
        self.assertAlmostEqual((1+1)/(8+100),x.rate_low)
        eps=1e-7;self.assertAlmostEqual((1+50)/(8+10+eps),x.rate_high,places=6)
    def test_reveal_nests_intervals(self):
        a=identify(**self.fixture(),rho=50,cap=100);b=identify(**visible_view([10,10],[True,True],[1,50],[8,11],[0,1]),rho=50,cap=100)
        self.assertLessEqual(a.rate_low,b.rate_low);self.assertGreaterEqual(a.rate_high,b.rate_high);self.assertLessEqual(a.risk_low,b.risk_low);self.assertGreaterEqual(a.risk_high,b.risk_high)
    def test_false_safe_healthy_label(self):
        v=self.fixture();r,p=healthy_imputation(v);self.assertEqual(p,0);self.assertEqual(identify(**v,rho=50,cap=100).risk_high,.5)
    def test_complete_case_all_missing(self):
        v=visible_view([10],[False],[50],[11],[1]);self.assertTrue(np.isnan(complete_case(v)[0]))
    def test_adversarial_witness_same_logs(self):
        v=self.fixture();low=visible_view([10,10],[True,False],[1,1],[8,100],[0,0]);high=visible_view([10,10],[True,False],[1,50],[8,10.01],[0,1])
        for key in v:np.testing.assert_array_equal(low[key],high[key])
        self.assertLess(2/108,.1);self.assertGreater(51/18.01,.1)

if __name__=='__main__':unittest.main(verbosity=2)
