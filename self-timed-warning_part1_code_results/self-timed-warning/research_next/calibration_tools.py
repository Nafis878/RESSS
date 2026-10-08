"""Reference calculations for the mechanism audit, not a novel optimizer."""
import os
import sys
from pathlib import Path
sys.path.insert(0,os.getcwd());sys.path.insert(0,str(Path('contrib').resolve()))
import numpy as np
from scipy.stats import binomtest
import cat as C


def grid_threshold(scores,alpha,grid):
    scores=np.asarray(scores,float);grid=np.asarray(grid,float)
    if not 0<alpha<1:raise ValueError('alpha must lie in (0,1)')
    if scores.ndim!=1 or np.isnan(scores).any() or np.isneginf(scores).any():raise ValueError('invalid scores')
    if grid.ndim!=1 or not len(grid) or not np.isfinite(grid).all() or (np.diff(grid)<=0).any():raise ValueError('invalid action grid')
    th,finite=C.tau_hat(scores,alpha)
    if not finite or th>grid[-1]:return float(grid[-1]),False
    return float(grid[np.searchsorted(grid,th,side='left')]),True


def holm(p):
    p=np.asarray(p,float)
    if p.ndim!=1 or not np.isfinite(p).all() or ((p<0)|(p>1)).any():raise ValueError('invalid p-values')
    order=np.argsort(p,kind='stable');out=np.empty(len(p));m=len(p)
    out[order]=np.minimum(1,np.maximum.accumulate((m-np.arange(m))*p[order]))
    return out


def paired_binary(a,b):
    a=np.asarray(a,bool);b=np.asarray(b,bool)
    if a.shape!=b.shape or a.ndim!=1 or not len(a):raise ValueError('invalid pairs')
    rescued=int((~a&b).sum());harmed=int((a&~b).sum());n=rescued+harmed
    p=float(binomtest(harmed,n,.5).pvalue) if n else 1.
    return dict(rescued=rescued,harmed=harmed,difference=float(a.mean()-b.mean()),p=p)


def ratio(c,t):
    c=np.asarray(c,float);t=np.asarray(t,float)
    if c.shape!=t.shape or c.ndim!=1 or not len(c) or not np.isfinite(c).all() or not np.isfinite(t).all() or (t<=0).any():raise ValueError('invalid renewal observations')
    return float(c.sum()/t.sum())


def renewal_contrast(ca,ta,cb,tb):
    """Unbiased order-two U-statistic for EC_a ET_b - EC_b ET_a, under i.i.d. pairs.

    The sign of its population expectation equals the sign of R_a-R_b when
    expected cycle lengths are positive. This is algebra, not new methodology.
    """
    ca,ta,cb,tb=[np.asarray(x,float) for x in [ca,ta,cb,tb]]
    ratio(ca,ta);ratio(cb,tb)
    if ca.shape!=cb.shape or len(ca)<2:raise ValueError('need at least two paired units')
    n=len(ca)
    return float((ca.sum()*tb.sum()-np.dot(ca,tb)-cb.sum()*ta.sum()+np.dot(cb,ta))/(n*(n-1)))


def zero_failure_upper(n,delta=.05):
    if n<1 or not 0<delta<1:raise ValueError('invalid n/delta')
    return float(-np.expm1(np.log(delta)/n))


def bootstrap_ratio(ca,ta,cb,tb,seed=2027,B=2000):
    point=ratio(ca,ta)/ratio(cb,tb)
    ca,ta,cb,tb=[np.asarray(x,float) for x in [ca,ta,cb,tb]]
    if ca.shape!=cb.shape:raise ValueError('unpaired units')
    idx=np.random.default_rng(seed).integers(0,len(ca),size=(B,len(ca)))
    r=(ca[idx].sum(1)/ta[idx].sum(1))/(cb[idx].sum(1)/tb[idx].sum(1))
    lo,hi=np.quantile(r,[.025,.975])
    return point,float(lo),float(hi)
