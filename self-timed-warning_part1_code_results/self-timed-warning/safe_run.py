"""python safe_run.py <method> <dataset>  ->  out/safe/preds_<dataset>_<method>.csv (point predictions only)"""
import sys, os, time, numpy as np, pandas as pd
from safe_common import load_dataset, outer_folds, fit_cal_split, regime_norm, engines
from safe_methods import make

def run(method, ds):
    tr, te, true = load_dataset(ds); units = np.sort(tr.unit.unique()); rows = []; info = []
    splits = [(k, np.setdiff1d(units, test), test) for k, test in enumerate(outer_folds(units), 1)]
    if te is not None: splits.append(('official', units, None))
    for k, outer_tr, test in splits:
        t0 = time.time(); fit_u, cal_u = fit_cal_split(outer_tr)
        Zf = regime_norm(tr[tr.unit.isin(fit_u)]); E = engines(tr, Zf)
        m = make(method, ds).fit({u: E[u] for u in fit_u})
        def add(us, role):
            for u in us:
                Z, reg, rul = E[u]; p = m.predict(Z, reg); L = len(Z)
                rows.append(pd.DataFrame({'fold': str(k), 'role': role, 'unit': u, 't': np.arange(1, L + 1), 'life': L, 'true_rul': rul, 'point': p}))
        add(cal_u, 'cal')
        if test is not None: add(test, 'test')
        else:
            ET = engines(te, Zf)
            for u in sorted(ET):
                Z, reg, _ = ET[u]; p = m.predict(Z, reg)
                rows.append(pd.DataFrame({'fold': 'official', 'role': 'official', 'unit': [u], 't': [len(Z)], 'life': [np.nan], 'true_rul': [true[u]], 'point': [p[-1]]}))
        extra = {a: getattr(m, a) for a in ('epochs', 'iters') if hasattr(m, a)}
        info.append(dict(dataset=ds, method=method, fold=str(k), n_fit=len(fit_u), n_cal=len(cal_u), seconds=round(time.time() - t0), **extra))
        print(ds, method, 'fold', k, info[-1], flush=True)
    os.makedirs('out/safe', exist_ok=True)
    pd.concat(rows, ignore_index=True).to_csv(f'out/safe/preds_{ds}_{method}.csv', index=False)
    pd.DataFrame(info).to_csv(f'out/safe/info_{ds}_{method}.csv', index=False)

if __name__ == '__main__':
    method = sys.argv[1]; dss = sys.argv[2].split(',') if len(sys.argv) > 2 else ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004']
    for ds in dss: run(method, ds)
