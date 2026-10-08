"""Wall time of the STW regressor (three caps) for one PHM08 fit/calibration split, same 2-core machine as dl_warning.py."""
import sys, time, json, numpy as np
sys.argv = sys.argv[:1]
import eol_window2 as W
from safe_common import load_dataset, outer_folds, fit_cal_split
tr, _, _ = load_dataset('PHM08'); units = np.sort(tr.unit.unique()); ts = []
for test in outer_folds(units)[:3]:
    fit, cal = fit_cal_split(np.setdiff1d(units, test)); t = time.time(); W.predict_all(tr, fit, np.concatenate([cal, test]), fit); ts.append(round(time.time() - t, 1))
json.dump(dict(stw_seconds_per_fold=ts), open('out/window/stw_timing.json', 'w')); print(ts)
