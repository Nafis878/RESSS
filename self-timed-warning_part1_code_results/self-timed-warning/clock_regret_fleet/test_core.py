from fractions import Fraction as F
import unittest
import numpy as np
from clock_regret_fleet.core import pair,select,bucket
from clock_regret_fleet.oracles import integer_pair,integer_family,continuous_pair,rate
from clock_regret_linear.core import select as common_select


class FleetTests(unittest.TestCase):
    def test_full_clock_pairs_1000(self):
        rng=np.random.default_rng(20261031)
        for _ in range(1000):
            n=int(rng.integers(1,5)); h=tuple(map(int,rng.integers(1,7,n)))
            f=tuple(rng.random(n)<.35); a,b=map(int,rng.integers(1,8,2))
            q=tuple(F(int(rng.integers(1,51)),int(rng.integers(1,8))) for _ in h)
            truth=integer_pair(h,f,a,b,q)
            exact=pair(h,f,a,b,q,exact=True); approx=pair(h,f,a,b,q,F(1,4))
            self.assertEqual(exact.lower,truth)
            self.assertLessEqual(approx.lower,truth); self.assertLessEqual(truth,approx.upper)
            self.assertLessEqual(approx.upper,F(5,4)*approx.lower)
            self.assertEqual(approx.lower,rate(approx.lifetimes,a,q)/rate(approx.lifetimes,b,q))
            self.assertTrue(all(t==hi if fi else t>hi for t,hi,fi in zip(approx.lifetimes,h,f)))

    def test_full_family_200(self):
        rng=np.random.default_rng(20261032)
        for _ in range(200):
            n=int(rng.integers(1,5)); h=tuple(map(int,rng.integers(1,6,n)))
            f=tuple(rng.random(n)<.4); ages=tuple(sorted(set(map(int,rng.integers(1,7,3)))))
            q=tuple(F(int(rng.integers(1,31)),3) for _ in h)
            truth=integer_family(h,f,ages,q); ans=select(h,f,ages,q,F(1,4))
            for lo,t,up in zip(ans['lower_scores'],truth,ans['upper_scores']):
                self.assertLessEqual(lo,t); self.assertLessEqual(t,up)
            self.assertLessEqual(truth[ans['chosen']],F(5,4)*min(truth))
            if ans['certified_exact_decision']: self.assertEqual(truth[ans['chosen']],min(truth))

    def test_common_cost_reduction_200(self):
        rng=np.random.default_rng(20261033)
        for _ in range(200):
            n=int(rng.integers(1,31)); h=rng.integers(1,30,n); f=rng.random(n)<.3
            ages=sorted(set(map(int,rng.integers(1,40,4)))); rho=int(rng.integers(2,21))
            truth=common_select(h,f,ages,rho); ans=select(h,f,ages,[rho-1]*n,exact=True)
            self.assertEqual(tuple(truth['scores']),ans['lower_scores'])
            self.assertEqual(truth['chosen'],ans['chosen'])

    def test_continuous_closure_200(self):
        rng=np.random.default_rng(20261034)
        for _ in range(200):
            n=int(rng.integers(1,5)); h=tuple(map(int,rng.integers(1,7,n)))
            f=tuple(rng.random(n)<.35); a,b=map(int,rng.integers(1,8,2))
            q=tuple(F(int(rng.integers(1,31)),5) for _ in h)
            truth=continuous_pair(h,f,a,b,q)
            self.assertEqual(pair(h,f,a,b,q,exact=True,continuous=True).lower,truth)
            ans=pair(h,f,a,b,q,continuous=True)
            self.assertLessEqual(ans.lower,truth); self.assertLessEqual(truth,ans.upper)
            life=ans.completion(F(1,1000))
            self.assertTrue(all(t==hi if fi else t>hi for t,hi,fi in zip(life,h,f)))
            self.assertLessEqual(rate(life,a,q)/rate(life,b,q),truth)

    def test_joint_clock_and_optimization_bound(self):
        h=[1,2,3,8]; f=[False,False,False,True]; q=[1,30,7,70]; ages=[2,5,10]
        c=select(h,f,ages,q,exact=True,continuous=True)
        for r in [1,2,8,32]:
            grid=select([x*r for x in h],f,[x*r for x in ages],q)
            self.assertLessEqual(c['lower_scores'][grid['chosen']],F(5,4)*F(r+1,r)*min(c['lower_scores']))
            for i,a in enumerate(ages):
                for j,b in enumerate(ages):
                    g=pair([x*r for x in h],f,a*r,b*r,q,exact=True).lower
                    v=c['pairs'][i][j].lower
                    self.assertLessEqual(g,v); self.assertLessEqual(v,F(r+1,r)*g)

    def test_permutations_and_certificate(self):
        h=[1,2,1,7]; f=[False,False,True,True]; q=[1,30,5,70]; ages=[2,5,10]
        ans=select(h,f,ages,q)
        rev=select(h[::-1],f[::-1],ages,q[::-1])
        self.assertEqual(ans['lower_scores'],rev['lower_scores'])
        fully=select([10],[True],[8,20],[1])
        self.assertTrue(fully['certified_exact_decision']); self.assertTrue(fully['certified_unique'])
        self.assertEqual(fully['selected_age'],8)
        self.assertEqual(select([1],[False],[2,2],[3])['lower_scores'],(F(1),F(1)))

    def test_bucket_boundaries_and_huge_rationals(self):
        for m in [1,2,31]:
            for k in [0,1,32,1024]:
                for j in [0,m-1]:
                    value=F(2**k)*F(m+j,m)
                    self.assertEqual(bucket(value,F(1),m),(k,j))
        ans=pair([1,2,4],[False,False,True],3,5,[F(1,10**50),10**50,7])
        truth=integer_pair((1,2,4),(False,False,True),3,5,(F(1,10**50),F(10**50),F(7)))
        self.assertLessEqual(ans.lower,truth); self.assertLessEqual(truth,ans.upper)

    def test_validation(self):
        for eps in [0,-1,2,True,.1,None,'nan']:
            with self.assertRaises(ValueError): pair([1],[False],2,3,[1],eps)
        for q in [[],[0],[-1],[True],[.5],None,['nan']]:
            with self.assertRaises(ValueError): select([1],[False],[2,3],q)
        for ages in [[],[0],[2.5]]:
            with self.assertRaises(ValueError): select([1],[False],ages,[1])

    def test_actual_trimming_and_exponential_exact_frontier(self):
        h=[3,8,15,21,26,31,38,47,52,60,75,99,180,190,200,210]
        f=[False]*12+[True]*4; q=[10*x+13 for x in h[:12]]+[300]*4
        ans=pair(h,f,120,240,q,F(1,2)); truth=pair(h,f,120,240,q,exact=True)
        self.assertGreater(ans.trim_steps,0)
        self.assertLessEqual(ans.lower,truth.lower); self.assertLessEqual(truth.lower,ans.upper)
        self.assertEqual(ans.upper/ans.lower,F(49,48)**ans.trim_steps)
        from itertools import combinations
        from clock_regret_fleet.core import pareto
        points=[(sum(2**(i+1) for i in subset),sum(2**(i+1) for i in subset),0)
                for subset in combinations(range(12),6)]
        self.assertEqual(len(pareto(points)),924)

    def test_approximate_permutation_invariance_100(self):
        rng=np.random.default_rng(20261036)
        for _ in range(100):
            h=list(map(int,rng.integers(1,100,12)))+[180,190]
            f=[False]*12+[True]*2; q=list(map(int,rng.integers(1,1000,14)))
            indices=list(map(int,rng.permutation(14)))
            first=pair(h,f,120,240,q,F(1,2))
            other=pair([h[i] for i in indices],[f[i] for i in indices],120,240,[q[i] for i in indices],F(1,2))
            self.assertEqual(first.lower,other.lower); self.assertEqual(first.upper,other.upper)


if __name__=='__main__': unittest.main()
