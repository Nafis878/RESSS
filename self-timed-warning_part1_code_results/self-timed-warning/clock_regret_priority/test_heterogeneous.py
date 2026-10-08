import itertools
from fractions import Fraction
import unittest
import numpy as np
from clock_regret_linear.core import worst_pair as common_pair
from clock_regret_linear.continuous import ContinuousPrepared
from clock_regret_priority.heterogeneous import later_pair,continuous_later_pair,phase_oracle,rate_ratio


def exhaustive(h,f,a,b,q):
    options=[[int(t)] if known else range(int(t)+1,max(int(t)+1,a+1)+1)
             for t,known in zip(h,f)]
    return max(rate_ratio(life,a,b,q) for life in itertools.product(*options))


class HeterogeneousTests(unittest.TestCase):
    def test_full_clock_exhaustion_1000(self):
        rng=np.random.default_rng(20261021)
        for _ in range(1000):
            n=int(rng.integers(1,5))
            h=rng.integers(1,7,n)
            f=rng.random(n)<.35
            b=int(rng.integers(1,6)); a=int(rng.integers(b+1,8))
            q=[Fraction(int(rng.integers(1,31)),int(rng.integers(1,8))) for _ in range(n)]
            answer=later_pair(h,f,a,b,q)
            self.assertEqual(answer.ratio,exhaustive(h,f,a,b,q))
            self.assertEqual(answer.ratio,rate_ratio(answer.witness,a,b,q))
            self.assertTrue(all(t==hi if known else t>hi for t,hi,known in zip(answer.witness,h,f)))

    def test_separate_phase_oracles_500(self):
        rng=np.random.default_rng(20261022)
        for _ in range(500):
            n=int(rng.integers(1,9))
            h=rng.integers(1,15,n); f=rng.random(n)<.35
            b=int(rng.integers(1,18)); a=b+int(rng.integers(1,8))
            q=[Fraction(int(rng.integers(1,51)),int(rng.integers(1,8))) for _ in range(n)]
            self.assertEqual(later_pair(h,f,a,b,q).ratio,phase_oracle(h,f,a,b,q))
            self.assertEqual(continuous_later_pair(h,f,a,b,q).ratio,
                             phase_oracle(h,f,a,b,q,continuous=True))

    def test_common_cost_reduction(self):
        rng=np.random.default_rng(20261023)
        for _ in range(200):
            n=int(rng.integers(1,101)); h=rng.integers(1,40,n)
            f=rng.random(n)<.4; b=int(rng.integers(1,40)); a=b+int(rng.integers(1,30))
            rho=int(rng.choice([2,5,20,50])); q=[rho-1]*n
            self.assertEqual(later_pair(h,f,a,b,q).ratio,common_pair(h,f,a,b,rho).ratio)
            self.assertEqual(continuous_later_pair(h,f,a,b,q).ratio,
                             ContinuousPrepared(h,f,[a,b],rho).pair(a,b).ratio)

    def test_strict_interior_counterexample(self):
        answer=later_pair([1,1,1],[True,False,False],3,2,[98,1,100])
        self.assertEqual(answer.denominators,(707,612,1010))
        self.assertEqual(answer.shared_count,1)
        self.assertEqual(answer.witness,(1,2,3))
        self.assertEqual(answer.ratio,Fraction(505,306))
        endpoint=Fraction(1010,min(answer.denominators[0],answer.denominators[-1]))
        self.assertGreater(answer.ratio,endpoint)

    def test_uniform_pairwise_constant_is_sharp(self):
        for n in [1,2,8]:
            h=[1]*n; f=[False]*n
            q=[Fraction(i+1,i+2) for i in range(n)]
            c=continuous_later_pair(h,f,2,1,q)
            for r in [1,2,4,16,64,1024]:
                g=later_pair([r]*n,f,2*r,r,q)
                self.assertEqual(c.ratio/g.ratio,Fraction(r+1,r))

    def test_exact_epsilon_sequences_and_attainment(self):
        rng=np.random.default_rng(20261024)
        for _ in range(200):
            n=int(rng.integers(1,16)); h=rng.integers(1,15,n); f=rng.random(n)<.4
            b=int(rng.integers(1,15)); a=b+int(rng.integers(1,7))
            q=[Fraction(int(rng.integers(1,41)),3) for _ in range(n)]
            c=continuous_later_pair(h,f,a,b,q); previous=Fraction(0)
            for eps in [Fraction(1,2),Fraction(1,16),Fraction(1,1024)]:
                life=c.completion(eps)
                self.assertTrue(all(t==hi if known else t>hi for t,hi,known in zip(life,h,f)))
                value=rate_ratio(life,a,b,q)
                self.assertLessEqual(previous,value); self.assertLessEqual(value,c.ratio)
                self.assertEqual(value==c.ratio,c.attained)
                previous=value
            for r in [1,2,4,16,64]:
                g=later_pair(h*r,f,a*r,b*r,q)
                self.assertLessEqual(g.ratio,c.ratio)
                self.assertLessEqual(c.ratio,Fraction(r+1,r)*g.ratio)

    def test_permutation_tied_premiums_and_observed_failures(self):
        h=[1,1,8,2,40]; f=[False,False,True,False,False]; q=[2,2,7,3,4]
        first=later_pair(h,f,12,4,q)
        other=later_pair(h[::-1],f[::-1],12,4,q[::-1])
        self.assertEqual(first.ratio,other.ratio)
        self.assertEqual(first.witness[2],8)
        self.assertGreater(first.witness[4],40)
        fully=later_pair([1,8],[True,True],12,4,[1,100])
        self.assertEqual(fully.ratio,rate_ratio((1,8),12,4,[1,100]))

    def test_rational_premiums_and_validation(self):
        self.assertEqual(later_pair([1],[False],3,2,['1/3']).ratio,
                         later_pair([1],[False],3,2,[Fraction(1,3)]).ratio)
        for premiums in [[],[0],[-1],[True],[.2],[float('nan')],['nan'],[[1]],None]:
            with self.assertRaises(ValueError):
                later_pair([1],[False],3,2,premiums)
        for a,b in [(2,2),(1,2),(2.5,1),(2,0)]:
            with self.assertRaises(ValueError): later_pair([1],[False],a,b,[1])
        c=continuous_later_pair([1],[False],3,2,[1])
        for eps in [0,1,-1]:
            with self.assertRaises(ValueError): c.completion(eps)


if __name__=='__main__': unittest.main()
