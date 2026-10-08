"""Compare freshly produced outputs (out/) with the frozen outputs of the paper (results/), and the rebuilt paper numbers and
manuscript (paper2/) with the reference copies (paper2/reference/).

Every comparison is exact: CSV/CSV.GZ tables must be identical value by value (pandas, check_exact), JSON files identical
after parsing, Markdown/LaTeX files identical byte by byte.

Files fall into three groups:
  EXACT    gradient-boosted and scikit-learn experiments; bit-for-bit reproducible with the pinned versions (requirements.txt)
  NETWORK  outputs of neural networks (Keras/JAX, TCN-GAN) and analyses built on them; fixed seeds, but floating-point
           reductions may differ slightly across CPUs, so small differences are reported but do not fail the check
  SKIPPED  run logs, timings, Excel workbooks (embedded time stamps) and PDFs
Usage: python verify_reproduction.py            # all groups that were rerun
       python verify_reproduction.py --paper-only
Exit code 1 if an EXACT file or the paper numbers/manuscript differ.
"""
import sys, os, json, glob
import pandas as pd

NETWORK = ('safe/', 'window/base_preds', 'window/ext_preds', 'window/tcn_', 'window/dl_warning', 'window/h2h',
           'window/hybrid_external', 'window/ablation_results_PHM08.json')
SKIP_EXT = ('.log', '.txt', '.xlsx', '.pdf', '.png')
SKIP_NAMES = ('stw_timing.json',)


def group(rel):
    if rel.endswith(SKIP_EXT) or os.path.basename(rel) in SKIP_NAMES:
        return 'SKIPPED'
    if rel.startswith('window/first_warning_v2_'):          # main results: gradient boosting only
        return 'EXACT'
    if rel.startswith(NETWORK):
        return 'NETWORK'
    return 'EXACT'


def same(a, b):
    if a.endswith(('.csv', '.csv.gz')):
        A, B = pd.read_csv(a), pd.read_csv(b)
        try:
            pd.testing.assert_frame_equal(A, B, check_exact=True, check_dtype=False)
            return True, ''
        except AssertionError as e:
            return False, str(e).splitlines()[0][:120]
    if a.endswith('.json'):
        return json.load(open(a)) == json.load(open(b)), ''
    return open(a, 'rb').read() == open(b, 'rb').read(), ''


def main():
    paper_only = '--paper-only' in sys.argv
    failed, rows = False, []
    if not paper_only:
        for f in sorted(glob.glob('results/**/*', recursive=True)):
            if os.path.isdir(f):
                continue
            rel = os.path.relpath(f, 'results'); g = group(rel); o = os.path.join('out', rel)
            if g == 'SKIPPED':
                continue
            if not os.path.exists(o):
                rows.append((g, 'not rerun', rel, '')); continue
            ok, msg = same(f, o)
            rows.append((g, 'IDENTICAL' if ok else 'DIFFERENT', rel, msg))
            if not ok and g == 'EXACT':
                failed = True
    for ref, new in [('paper2/reference/numbers.json', 'paper2/numbers.json'),
                     ('paper2/reference/manuscript.tex', 'paper2/tex/manuscript.tex'),
                     ('paper2/reference/supplementary.tex', 'paper2/tex/supplementary.tex')]:
        if os.path.exists(new):
            ok, msg = same(ref, new); rows.append(('PAPER', 'IDENTICAL' if ok else 'DIFFERENT', new, msg)); failed |= not ok
        else:
            rows.append(('PAPER', 'not built', new, ''))
    w = max(len(r[2]) for r in rows)
    for g, s, rel, msg in rows:
        print(f'{g:8s} {s:10s} {rel:{w}s} {msg}')
    n = lambda g, s: sum(1 for r in rows if r[0] == g and r[1] == s)
    print(f"\nEXACT: {n('EXACT', 'IDENTICAL')} identical, {n('EXACT', 'DIFFERENT')} different, {n('EXACT', 'not rerun')} not rerun; "
          f"NETWORK: {n('NETWORK', 'IDENTICAL')} identical, {n('NETWORK', 'DIFFERENT')} different, {n('NETWORK', 'not rerun')} not rerun; "
          f"PAPER: {n('PAPER', 'IDENTICAL')} identical, {n('PAPER', 'DIFFERENT')} different")
    print('REPRODUCTION CHECK ' + ('FAILED' if failed else 'PASSED'))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
