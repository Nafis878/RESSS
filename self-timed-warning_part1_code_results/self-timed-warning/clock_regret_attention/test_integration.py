from fractions import Fraction as F
import unittest
import numpy as np
from clock_regret_attention.integration import select,hybrid_pair,learned_selector
from clock_regret_attention.models import AttentionRanker
from clock_regret_fleet.oracles import integer_pair,rate


class IntegrationTests(unittest.TestCase):
    def test_100_full_clock_families_and_adversarial_proposals(self):
        rng=np.random.default_rng(20261120)
        for _ in range(100):
            n=int(rng.integers(1,5)); h=list(map(int,rng.integers(1,6,n)))
            f=list(rng.random(n)<.4); q=list(map(int,rng.integers(1,100,n)))
            ages=sorted(set(map(int,rng.integers(2,8,3))))
            # A deliberately unhelpful focus must not invalidate the fallback.
            r=select(h,f,ages,q,F(1,2),budget=0,selector=lambda *args: [])
            exact=[]
            for i,a in enumerate(ages):
                truth=[]
                for j,b in enumerate(ages):
                    g=integer_pair(h,f,a,b,q); p=r['pairs'][i][j]; truth.append(g)
                    self.assertLessEqual(p.lower,g); self.assertLessEqual(g,p.upper)
                    self.assertGreaterEqual(p.lower,p.fallback_lower)
                    self.assertLessEqual(p.upper,p.fallback_upper)
                    self.assertEqual(p.lower,rate(p.witness,a,q)/rate(p.witness,b,q))
                exact.append(max(truth))
            chosen=r['chosen']
            self.assertLessEqual(exact[chosen],F(3,2)*min(exact))
            if r['certified_exact_decision']: self.assertEqual(exact[chosen],min(exact))

    def test_learned_selector_and_finite_validation(self):
        model=AttentionRanker().eval(); callback=learned_selector(model)
        h=[1,2,10]; f=[False,False,True]; q=[2,20,50]
        ans=hybrid_pair(h,f,5,10,q,budget=1,selector=callback)
        self.assertEqual(len(ans.proposal_focus),1)
        with self.assertRaises(ValueError):
            hybrid_pair(h,f,5,10,q,budget=1,selector=lambda *args:[0,1])


if __name__=='__main__': unittest.main()
