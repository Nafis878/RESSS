from fractions import Fraction as F
from itertools import combinations
import unittest
import numpy as np
import torch
from clock_regret_attention.core import focused_pair,optimal_premium_focus,minimum_certified_focus
from clock_regret_attention.models import AttentionRanker,features
from clock_regret_fleet.oracles import integer_pair,rate


class FocusTests(unittest.TestCase):
    def test_minimal_certificate_budget(self):
        h=[1,2,3,8]; f=[False,False,False,True]; q=[1,30,7,70]; a=5;b=10
        for eps in [F(1),F(1,4),F(1,100)]:
            selected=minimum_certified_focus(h,f,a,b,q,eps)
            self.assertLessEqual(focused_pair(h,f,a,b,q,selected).factor,1+eps)
            for size in range(len(selected)):
                for smaller in combinations(range(3),size):
                    self.assertGreater(focused_pair(h,f,a,b,q,smaller).factor,1+eps)
    def test_500_full_clock_random_focus_certificates(self):
        rng=np.random.default_rng(20261110)
        for _ in range(500):
            n=int(rng.integers(1,5)); h=tuple(map(int,rng.integers(1,7,n)))
            f=tuple(rng.random(n)<.4); a=int(rng.integers(2,7)); b=a+int(rng.integers(1,4))
            q=tuple(F(int(rng.integers(1,31)),int(rng.integers(1,6))) for _ in h)
            focus=[i for i,(hi,fi) in enumerate(zip(h,f)) if not fi and hi<a and rng.random()<.5]
            ans=focused_pair(h,f,a,b,q,focus); truth=integer_pair(h,f,a,b,q)
            self.assertLessEqual(ans.lower,truth); self.assertLessEqual(truth,ans.upper)
            self.assertEqual(ans.lower,rate(ans.witness,a,q)/rate(ans.witness,b,q))
            self.assertTrue(all(t==hi if fi else t>hi for t,hi,fi in zip(ans.witness,h,f)))

    def test_premium_ranking_minimizes_all_focus_factors(self):
        h=[1,2,3,8]; f=[False,False,False,True]; q=[1,30,7,70]; a=5;b=10
        for budget in range(4):
            focused=optimal_premium_focus(h,f,a,b,q,budget)
            chosen=focused_pair(h,f,a,b,q,focused)
            for other in combinations(range(3),budget):
                self.assertLessEqual(chosen.factor,focused_pair(h,f,a,b,q,other).factor)

    def test_sharpness_and_unsafe_omission(self):
        for a in [2,3,10,100,10000]:
            b=a+1; h=[a-1,b]; f=[False,True]; q=[1,3]
            focus=focused_pair(h,f,a,b,q,[]); full=focused_pair(h,f,a,b,q,[0])
            self.assertEqual(focus.factor,F(5,4))
            self.assertEqual(full.lower/focus.lower,F(5,4)*(1-F(1,2*b)))
        naive=focused_pair([1,3],[False,True],2,3,[100,1],[])
        truth=focused_pair([1,3],[False,True],2,3,[100,1],[0])
        self.assertEqual(naive.lower,1); self.assertEqual(truth.lower,F(255,206))
        self.assertEqual(naive.factor,F(153,103))

    def test_no_known_between_requires_no_attention(self):
        ans=focused_pair([1,2,10],[False,False,True],4,8,[2,100,500],[])
        self.assertEqual(ans.factor,1)
        self.assertEqual(ans.lower,focused_pair([1,2,10],[False,False,True],4,8,[2,100,500],[0,1]).lower)

    def test_attention_permutation_equivariance(self):
        torch.manual_seed(19); model=AttentionRanker().eval()
        r=dict(h=[1,2,7,8],f=[False,False,True,True],q=[F(1),F(30),F(5),F(70)],a=5,b=10)
        order=[2,0,3,1]; x=features(r)
        with torch.no_grad():
            first=model(torch.tensor(x)[None])[0].numpy()
            other=model(torch.tensor(x[order])[None])[0].numpy()
        self.assertTrue(np.allclose(first[order],other,atol=1e-6))

    def test_invalid_focus_and_all_focus_exact(self):
        for focus in [[1],[0,0],[-1],[True],[.1],None]:
            with self.assertRaises(ValueError): focused_pair([1,3],[False,True],2,3,[1,3],focus)
        for a,b in [(2,2),(3,2)]:
            with self.assertRaises(ValueError): focused_pair([1],[False],a,b,[1],[])
        all_assets=focused_pair([1,2,8],[False,False,True],5,10,[2,30,70],[0,1])
        self.assertEqual(all_assets.lower,all_assets.upper)


if __name__=='__main__': unittest.main()
