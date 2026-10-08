"""Check that the input data are exactly those used for the paper.

Every data file is checked against tools/DATA_SHA256.json. For the NASA text files (PHM08 and C-MAPSS) a mismatch of the
file hash is not fatal when the parsed numerical content is identical (a hash of the values read as float64), so a fresh
download from the NASA repository with different whitespace is accepted. Run from the repository root:
    python tools/check_data.py            # check
    python tools/check_data.py --write    # (maintainers) record the hashes of the current files
"""
import sys, json, hashlib, os, glob
import numpy as np

REF = 'tools/DATA_SHA256.json'
FILES = sorted(['a/train.txt'] + glob.glob('cmapss/*.txt') + ['ncm/ncmapss_cycle_summary.csv.gz', 'battery/severson_cycle_summary.csv.gz',
               'battery/severson_cells.csv', 'bearing/femto_snapshot_features.csv.gz', 'ncm/WARNING_PROTOCOL.md',
               'battery/BATTERY_PROTOCOL.md', 'bearing/BEARING_PROTOCOL.md'])
NUMERIC = lambda f: f == 'a/train.txt' or (f.startswith('cmapss/') and not f.endswith('readme.txt'))


def file_hash(f):
    return hashlib.sha256(open(f, 'rb').read()).hexdigest()


def value_hash(f):
    a = np.loadtxt(f, ndmin=2).astype(np.float64)
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest() + f':{a.shape[0]}x{a.shape[1]}'


def main():
    if '--write' in sys.argv:
        ref = {f: {'sha256': file_hash(f), **({'values': value_hash(f)} if NUMERIC(f) else {})} for f in FILES}
        json.dump(ref, open(REF, 'w'), indent=1); print(f'wrote {REF} ({len(ref)} files)'); return
    ref = json.load(open(REF)); bad = []
    for f, r in ref.items():
        if not os.path.exists(f):
            bad.append(f'{f}: missing'); continue
        if file_hash(f) == r['sha256']:
            continue
        if 'values' in r and value_hash(f) == r['values']:
            print(f'{f}: file differs in formatting, numerical content identical'); continue
        bad.append(f'{f}: content differs from the data used for the paper')
    if bad:
        print('DATA CHECK FAILED\n  ' + '\n  '.join(bad)); sys.exit(1)
    print(f'data check passed ({len(ref)} files)')


if __name__ == '__main__':
    main()
