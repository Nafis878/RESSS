"""Phase 3: certified alarm thresholds (CAT) on the 17 PRONOSTIA bearings (validity of the guarantee only; exploratory,
plan hashed before the run, contrib/PLAN.md). Five-fold cross-validation by bearing (seed 2026), kappa from the outer
training bearings (audit_confirmations.bearing_corrected), task in blocks (H = 20 blocks as in the protocol), the recipe's
regressor and features (bearing_warning.features), inner folds seed 100 + fold. Lead time 0: a failure is a bearing that
fails without an alarm. With 13-14 calibration bearings, alpha >= 1/(n+1) ~ 0.07 is needed for a certificate.
Reproduction check: the window-tuned first warnings at H = 20 equal the original warning script rerun on this platform (cv).
Usage: python contrib/cat_bearing.py       Outputs: out/contrib/Bearing_units.csv, Bearing_settings.csv, Bearing_check.txt
"""
import os, sys, time, json, hashlib, platform
from pathlib import Path
ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'contrib'))
import numpy as np, pandas as pd
import eol_window2 as W
import rev_experiments as R
import audit_confirmations as AC
import bearing_warning as GW
from safe_common import outer_folds
import cat as C

OUT = 'out/contrib'; os.makedirs(OUT, exist_ok=True)


def fit_predict(B, train_u, target_u):
    F, Y = GW.features(B, train_u); X = np.vstack([F[u] for u in train_u]); y = np.concatenate([Y[u] for u in train_u]); out = {}
    for cap in W.CAPS:
        m = W.gbm(X, y, cap); out[cap] = {u: (m.predict(F[u])[:-1], Y[u][:-1]) for u in target_u}
    return out


def main():
    marker = Path(OUT) / 'Bearing_verified.json'
    output_names = ['Bearing_units.csv', 'Bearing_settings.csv', 'Bearing_platform.csv', 'Bearing_check.txt']
    sig = signature()
    if marker.exists():
        cached = json.loads(marker.read_text())
        valid = cached.get('signature') == sig and all((Path(OUT) / name).exists() and
            hashlib.sha256((Path(OUT) / name).read_bytes()).hexdigest() == cached.get('outputs', {}).get(name)
            for name in output_names)
        if valid:
            print('PASS  Bearing outputs reused: code, input, numerical environment and verified output hashes unchanged', flush=True)
            return
    t0 = time.time(); S, L = AC.bearing_snapshots(); units = np.sort(L.index.values); rows, sets, w20, platform = [], [], [], []
    for fold, te in enumerate(outer_folds(units), 1):
        te = np.sort(te); tr = np.setdiff1d(units, te); kap = AC.kap_rule(L[tr].values); B = AC.bearing_blocks(S, kap, L)
        inner = np.array_split(np.random.default_rng(100 + fold).permutation(tr), 5); oof = {c: {} for c in W.CAPS}
        for iu in inner:
            if len(iu) == 0: continue
            p = fit_predict(B, np.setdiff1d(tr, iu), iu)
            for c in W.CAPS: oof[c].update(p[c])
        fin = fit_predict(B, tr, te)
        best = None
        for cap in W.CAPS:
            for sp in W.SPANS:
                Po = {u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}
                for k in W.KS:
                    tot = W.in_counts(Po, 20, k) - 0.001 * np.abs(W.SHIFTS); j = int(np.argmax(tot))
                    if best is None or tot[j] > best[0]: best = (tot[j], cap, sp, k, W.SHIFTS[j])
        _, cap, sp, k, s = best
        w20.append(W.evaluate({u: (W.smooth(p, sp), y) for u, (p, y) in fin[cap].items()}, 20, k, s).assign(split=f'cv{fold}'))
        platform.append(GW.run_split(B, f'cv{fold}', tr, te, 100 + fold))
        tab_o = R.alarm_table({u: (W.smooth(p, sp), y) for u, (p, y) in oof[cap].items()}, k, R.TAUS)
        tab_t = R.alarm_table({u: (W.smooth(p, sp), y) for u, (p, y) in fin[cap].items()}, k, R.TAUS)
        S_cf = C.scores_from_table(tab_o, R.TAUS, 0.0); S_te = C.scores_from_table(tab_t, R.TAUS, 0.0)
        for alpha in C.ALPHAS:
            th, cert = C.tau_hat(S_cf, alpha); j0 = C.certified_column(R.TAUS, th, cert)
            sets.append(dict(split=f'cv{fold}', kappa=kap, alpha=alpha, setting=str((cap, sp, k)), n_cf=len(S_cf), tau_cf=th, cert_cf=cert,
                             n_inf_cf=int(np.isinf(S_cf).sum()), oof_scores='/'.join(f'{v:g}' for v in np.sort(S_cf))))
            U, ok, ya, ta, Lb = tab_t
            for i, u in enumerate(U):
                rows.append(dict(split=f'cv{fold}', kappa=kap, alpha=alpha, policy=f'CAT_a{alpha}', unit=u, certifiable=cert, tau=R.TAUS[j0],
                                 fail=not (ok[i, j0] and ya[i, j0] > 0), rul_at_alarm_snapshots=ya[i, j0] * kap if ok[i, j0] else np.nan,
                                 life_snapshots=int(L[u]), test_score=S_te[i]))
        print(f'bearing cv{fold}: kappa {kap}, setting {(cap, sp, k)}, OOF scores {np.sort(S_cf)}', flush=True)
    D = pd.DataFrame(rows); D.to_csv(f'{OUT}/Bearing_units.csv', index=False); pd.DataFrame(sets).to_csv(f'{OUT}/Bearing_settings.csv', index=False)
    ref = pd.concat(platform); ref.to_csv(f'{OUT}/Bearing_platform.csv', index=False)
    ref = ref[(ref.method == 'warning') & (ref.H == 20)].set_index(['split', 'unit']).cls
    mine = pd.concat(w20).set_index(['split', 'unit']).cls.reindex(ref.index); same = bool((mine == ref).all())
    line = f'{"PASS" if same else "FAIL"}  R0 bearing window-tuned first warnings at H = 20 identical to the original script on this platform ({int((mine == "IN").sum())}/{len(mine)} in window)'
    open(f'{OUT}/Bearing_check.txt', 'w', newline='\n').write(line + '\n'); print(line); print(f'bearings finished in {time.time() - t0:.0f}s')
    if not same: raise SystemExit('STOP: bearing results not reproduced on the CAT code path')
    marker.write_text(json.dumps({'signature': sig, 'outputs': {name: hashlib.sha256((Path(OUT) / name).read_bytes()).hexdigest()
                                    for name in output_names}}, indent=2))


def signature():
    """Guard complete-run reuse against changes of code, inputs or numerical environment."""
    import sklearn, scipy
    h = hashlib.sha256()
    for folder in ['.', 'contrib', 'kam']:
        for path in sorted(Path(folder).glob('*.py')):
            h.update(str(path).encode()); h.update(b'\0'); h.update(path.read_bytes())
    h.update(Path('bearing/femto_snapshot_features.csv.gz').read_bytes())
    h.update(json.dumps([sys.version, platform.platform(), platform.processor(), np.__version__, pd.__version__, sklearn.__version__, scipy.__version__,
        [os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']]]).encode())
    return h.hexdigest()


def guarded_main():
    """Allow another queue to reuse a verified run without concurrent output writes."""
    with open(Path(OUT) / 'Bearing_run.lock', 'a+b') as lock:
        lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
        if os.name == 'nt':
            import msvcrt
            while True:
                try: msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1); break
                except OSError: time.sleep(1)
            try: main()
            finally:
                lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
            try: main()
            finally: fcntl.flock(lock, fcntl.LOCK_UN)


if __name__ == '__main__':
    guarded_main()
