"""Interpretable arbitration research prototype. No novel-method claim.

Candidates are fixed before labelled meta-validation. Outputs are authority
indices, never arithmetic averages of incompatible alarm times. Confidence
claims require assumptions stated separately; bootstrap evidence is heuristic.
"""
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from scipy.stats import beta, rankdata


@lru_cache(maxsize=20000)
def upper(f,n,delta):
    if n<0 or f<0 or f>n or not 0<delta<1:raise ValueError('invalid binomial counts')
    if n==0 or f==n:return 1.
    return float(beta.isf(delta,f+1,n-f))


@dataclass
class Evidence:
    cost:np.ndarray
    stability:np.ndarray
    risk_upper:np.ndarray
    support:bool
    uncertainty:np.ndarray
    perturb_stability:np.ndarray
    risk:np.ndarray
    n:int
    global_risk_upper:np.ndarray

    def features(self):
        scale=max(float(np.median(self.cost)),1e-12)
        return np.column_stack([self.cost/scale,self.stability,self.risk_upper,
            np.full(len(self.cost),float(self.support)),self.uncertainty/scale,
            self.perturb_stability,self.risk,np.full(len(self.cost),np.log1p(self.n))])


def validate(c,t,f):
    c,t=np.asarray(c,float),np.asarray(t,float)
    if not np.isin(np.asarray(f),[0,1]).all():raise ValueError('failure labels must be binary')
    f=np.asarray(f,bool)
    if c.ndim!=2 or not c.shape[0] or c.shape!=t.shape or c.shape!=f.shape:raise ValueError('need nonempty paired unit x policy arrays')
    if not np.isfinite(c).all() or not np.isfinite(t).all() or (c<=0).any() or (t<=0).any():raise ValueError('cost/life must be finite and positive')
    return c,t,f


def winning_share(r):
    best=np.isclose(r,r.min(axis=1,keepdims=True),rtol=1e-10,atol=1e-12)
    return best.mean(0)  # probability of membership in the co-optimal set


def evidence(c,t,f,context,query,seed=2026,B=100,delta=.05,strata=1,pooled=False):
    c,t,f=validate(c,t,f);context=np.asarray(context)
    if context.shape!=(len(c),) or B<2 or strata<1:raise ValueError('invalid context/bootstrap settings')
    k=c.shape[1];d=delta/(k*(strata+1))
    gu=np.array([upper(int(v),len(c),d) for v in f.sum(0)])
    mask=np.ones(len(c),bool) if pooled else context==query
    support=bool(mask.any());n=int(mask.sum())
    if not support:mask=np.ones(len(c),bool)
    a,b,z=c[mask],t[mask],f[mask]
    point=a.sum(0)/b.sum(0)
    idx=np.random.default_rng(seed).integers(0,len(a),size=(B,len(a)))
    draws=a[idx].sum(1)/b[idx].sum(1)
    stab=winning_share(draws);sd=draws.std(0,ddof=1)
    if len(a)>1:
        jack=(a.sum(0)-a)/(b.sum(0)-b)
        perturb=winning_share(jack)
    else:perturb=np.full(k,1/k)
    q=np.array([upper(int(v),len(a),d) for v in z.sum(0)]) if support else np.ones(k)
    return Evidence(point,stab,q,support,sd,perturb,z.mean(0),n,gu)


def reliability(e,alpha=.05):
    """Minimum constraint satisfaction, not a calibrated probability."""
    if not 0<alpha<1:raise ValueError('invalid risk tolerance')
    if not e.support:return np.zeros(len(e.cost))
    return np.minimum.reduce([alpha/np.maximum(e.risk_upper,1e-12),2*e.stability,2*e.perturb_stability])


def choose(e,kind='RAMPE',fallback=3,alpha=.05):
    k=len(e.cost)
    if not 0<=fallback<k:raise ValueError('invalid fallback index')
    if kind not in ['RAMPE','conventional','RAMPE_no_reliability','uncertainty','rank','normalized','RAMPE_no_calibration','RAMPE_no_stability','RAMPE_no_transfer','RAMPE_no_abstention','RAMPE_no_context']:raise ValueError('unknown selector')
    if kind in ['conventional','RAMPE_no_reliability']:return int(np.argmin(e.cost)),False
    if kind=='uncertainty':return int(np.argmin(e.cost+e.uncertainty)),False
    if kind=='rank':
        r=np.mean([rankdata(e.cost),rankdata(e.risk_upper),rankdata(-e.stability),rankdata(e.uncertainty),rankdata(-e.perturb_stability)],axis=0)
        return int(np.argmin(r)),False
    if kind=='normalized':
        r=np.minimum(1,alpha/np.maximum(e.risk_upper,1e-12))*e.stability*e.perturb_stability
        if not e.support or not r.any():return fallback,True
        return int(np.argmax(r/(e.cost+e.uncertainty))),False
    eligible=np.ones(k,bool)
    if kind!='RAMPE_no_calibration':eligible &= e.risk_upper<=alpha+1e-12
    if kind!='RAMPE_no_stability':eligible &= e.stability>=.5-1e-12
    eligible &= e.perturb_stability>=.5-1e-12
    if kind=='RAMPE_no_transfer':
        # Remove support veto: global risk is substituted only for an unseen context.
        q=e.risk_upper if e.support else e.global_risk_upper
        eligible=np.ones(k,bool)&(q<=alpha+1e-12)&(e.stability>=.5-1e-12)&(e.perturb_stability>=.5-1e-12)
    elif not e.support:eligible[:]=False
    if eligible.any():return int(np.argmin(np.where(eligible,e.cost+e.uncertainty,np.inf))),False
    if kind=='RAMPE_no_abstention':return int(np.argmin(e.cost+e.uncertainty)),False
    return fallback,True


def weights(e,kind='uniform',alpha=.05,seed=2026):
    k=len(e.cost)
    if kind=='uniform':w=np.ones(k)
    elif kind=='inverse_cost':w=1/e.cost
    elif kind=='random':w=np.random.default_rng(seed).dirichlet(np.ones(k))
    elif kind=='reliability':w=np.minimum(1,alpha/np.maximum(e.risk_upper,1e-12))*e.stability*e.perturb_stability/(e.cost+e.uncertainty)
    else:raise ValueError('unknown weighting rule')
    return w/w.sum() if w.sum()>0 else np.ones(k)/k


def draw_policy(w,u):
    w=np.asarray(w,float)
    if not np.isfinite(w).all() or (w<0).any() or not np.isclose(w.sum(),1) or not 0<=u<1:raise ValueError('invalid probability distribution')
    return min(int(np.searchsorted(np.cumsum(w),u,side='right')),len(w)-1)


def metrics(c,t,f,action,abstain=None):
    c,t,f=validate(c,t,f);a=np.asarray(action,int)
    if a.shape!=(len(c),) or (a<0).any() or (a>=c.shape[1]).any():raise ValueError('invalid actions')
    i=np.arange(len(c));cc=c[i,a];tt=t[i,a];ff=f[i,a]
    return dict(cost_rate=float(cc.sum()/tt.sum()),mean_cost=float(cc.mean()),median_cost=float(np.median(cc)),
                max_cost=float(cc.max()),cost_variance=float(cc.var()),failures=int(ff.sum()),risk=float(ff.mean()),
                n=len(c),authority_changes=int((np.diff(a)!=0).sum()),abstention=float(np.mean(abstain)) if abstain is not None else 0.)
