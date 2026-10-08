"""Theory-guided shift rule STW-T (bearing/BEARING_PROTOCOL.md, Part B).
Given the out-of-fold predictions (already smoothed with the selected span) and the selected debounce k, choose the shift s on the
grid that minimises |median OOF first-warning error - (-5.5)|; missed units ignored; ties -> larger OOF in-window count, then
smaller |s|. Same first-warning rule as eol_window2 (first cycle where the shifted prediction has been <= H for k cycles)."""
import numpy as np, pandas as pd
CENTRE = -5.5

def shift_T(Po, H, k, shifts, lo=-13, hi=2):
    thr = -(H - shifts); errs = []
    for p, y in Po.values():
        mk = pd.Series(p).rolling(k, min_periods=k).max().values; mk = np.where(np.isnan(mk), np.inf, mk); nrm = -np.minimum.accumulate(mk)
        i = np.searchsorted(nrm, thr, side='left'); ok = i < len(p); ii = np.minimum(i, len(p) - 1)
        errs.append(np.where(ok, p[ii] + shifts - y[ii], np.nan))
    E = np.vstack(errs)                                           # units x shifts
    with np.errstate(all='ignore'):
        med = np.nanmedian(E, axis=0)
    cnt = ((E >= lo) & (E <= hi)).sum(0)
    dev = np.where(np.isnan(med), np.inf, np.abs(med - CENTRE))
    order = np.lexsort((np.abs(shifts), -cnt, np.round(dev, 9)))    # primary: dev, then larger count, then smaller |s|
    return float(shifts[order[0]])
