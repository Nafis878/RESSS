# ================================================================================================
# Google Colab script: extract per-cycle summary features of the Severson et al. (2019) battery
# dataset (124 commercial LFP/graphite cells, cycled to end of life) into ONE small CSV.
#
# Steps in Colab:
#   1. The cell below downloads the three batch files itself; if that fails, get them from the official project page
#        https://data.matr.io/1/projects/5c48dd2bc625d700019f3204
#      (files: 2017-05-12_batchdata_updated_struct_errorcorrect.mat,
#              2017-06-30_batchdata_updated_struct_errorcorrect.mat,
#              2018-04-12_batchdata_updated_struct_errorcorrect.mat)
#      and put them in /content (or mount Google Drive and change DATA_DIR).
#   2. Run this cell. It writes /content/severson_cycle_summary.csv.gz (about 5-10 MB).
#   3. Download that file and upload it to the chat.
# ================================================================================================
import os, glob, subprocess, h5py, numpy as np, pandas as pd

# ---- 0. download the three batch files (about 3 GB each; takes a few minutes in Colab) --------------------------
URLS = {'2017-05-12_batchdata_updated_struct_errorcorrect.mat': 'https://data.matr.io/1/api/v1/file/5c86c0b5fa2ede00015ddf66/download',
        '2017-06-30_batchdata_updated_struct_errorcorrect.mat': 'https://data.matr.io/1/api/v1/file/5c86bf13fa2ede00015ddd82/download',
        '2018-04-12_batchdata_updated_struct_errorcorrect.mat': 'https://data.matr.io/1/api/v1/file/5c86bd64fa2ede00015ddbb2/download'}
for fn, url in URLS.items():
    p = os.path.join('/content', fn)
    if not os.path.exists(p) or os.path.getsize(p) < 10**8:
        print('downloading', fn); subprocess.run(['wget', '-q', '-O', p, url], check=False)
    print(fn, round(os.path.getsize(p) / 1e9, 2) if os.path.exists(p) else 'MISSING', 'GB')
# If a file is MISSING or only a few KB, download it by hand from https://data.matr.io/1/projects/5c48dd2bc625d700019f3204
# (look for the three files named above), upload it to /content, and run this cell again.

DATA_DIR = '/content'
FILES = {1: '2017-05-12_batchdata_updated_struct_errorcorrect.mat',
         2: '2017-06-30_batchdata_updated_struct_errorcorrect.mat',
         3: '2018-04-12_batchdata_updated_struct_errorcorrect.mat'}
FIELDS = ['cycle', 'QDischarge', 'QCharge', 'IR', 'Tavg', 'Tmin', 'Tmax', 'chargetime']

rows, meta = [], []
for b, fname in FILES.items():
    path = os.path.join(DATA_DIR, fname)
    assert os.path.exists(path), f'missing {path}'
    f = h5py.File(path, 'r'); batch = f['batch']; n = batch['summary'].shape[0]
    print(f'batch {b}: {n} cells')
    for i in range(n):
        cid = f'b{b}c{i}'
        cl = np.array(f[batch['cycle_life'][i, 0]]).ravel()
        policy = f[batch['policy_readable'][i, 0]][()].tobytes()[::2].decode(errors='ignore')
        summ = f[batch['summary'][i, 0]]
        d = {k: np.hstack(summ[k][0, :].tolist()) for k in FIELDS}
        L = len(d['cycle'])
        df = pd.DataFrame({k: v[:L] for k, v in d.items()}); df.insert(0, 'cell', cid)
        rows.append(df)
        meta.append(dict(cell=cid, batch=b, channel=i, policy=policy, cycle_life_official=float(cl[0]) if cl.size else np.nan,
                         n_summary_rows=L, first_cycle=float(d['cycle'][0]) if L else np.nan, last_cycle=float(d['cycle'][-1]) if L else np.nan))
    f.close()

S = pd.concat(rows, ignore_index=True); M = pd.DataFrame(meta)
S.to_csv('/content/severson_cycle_summary.csv.gz', index=False, compression='gzip')
M.to_csv('/content/severson_cells.csv', index=False)
print(S.shape, M.shape); print(M.head()); print('files written: severson_cycle_summary.csv.gz, severson_cells.csv')
