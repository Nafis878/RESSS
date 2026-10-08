"""Truth-free finite-cohort evaluation of coarsened censored outcome records."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Interval:
    rate_low:float
    rate_high:float
    risk_low:float
    risk_high:float
    observed:int
    unknown:int

def identify(horizon,observed,cost,use,fail,rho,cap):
    h=np.asarray(horizon,float);o=np.asarray(observed,bool)
    c,t,f=np.asarray(cost,float),np.asarray(use,float),np.asarray(fail,float)
    if h.ndim!=1 or not len(h) or any(x.shape!=h.shape for x in [o,c,t,f]):raise ValueError('aligned nonempty vectors required')
    if not np.isfinite(h).all() or (h<=0).any() or not np.isfinite(cap) or cap<=h.max() or rho<=1:raise ValueError('invalid horizons/cap/cost asymmetry')
    if not np.isfinite(c[o]).all() or not np.isfinite(t[o]).all() or (t[o]<=0).any() or (t[o]>cap).any() or not np.isin(f[o],[0,1]).all():raise ValueError('invalid observed outcomes')
    if not np.allclose(c[o],1+(rho-1)*f[o]):raise ValueError('cost/failure accounting mismatch')
    # Unknown values must be absent. This prevents accidental evaluation leakage.
    if any(np.isfinite(x[~o]).any() for x in [c,t,f]):raise ValueError('unresolved outcomes must be NaN')
    m=int((~o).sum());n=len(h);sc=float(c[o].sum());st=float(t[o].sum());sf=float(f[o].sum())
    if not m:return Interval(sc/st,sc/st,sf/n,sf/n,int(o.sum()),0)
    return Interval((sc+m)/(st+m*cap),(sc+m*rho)/(st+h[~o].sum()),sf/n,(sf+m)/n,int(o.sum()),m)

def visible_view(horizon,observed,cost,use,fail):
    o=np.asarray(observed,bool)
    return dict(horizon=np.asarray(horizon,float).copy(),observed=o.copy(),cost=np.where(o,cost,np.nan),use=np.where(o,use,np.nan),fail=np.where(o,fail,np.nan))

def complete_case(view):
    o=view['observed']
    return (float(view['cost'][o].sum()/view['use'][o].sum()),float(view['fail'][o].mean())) if o.any() else (np.nan,np.nan)

def healthy_imputation(view):
    o=view['observed'];c=np.where(o,view['cost'],1.);t=np.where(o,view['use'],view['horizon']);f=np.where(o,view['fail'],0.)
    return float(c.sum()/t.sum()),float(f.mean())
