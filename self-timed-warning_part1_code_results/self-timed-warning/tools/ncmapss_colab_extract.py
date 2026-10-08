"""
N-CMAPSS -> small per-flight-cycle summary (run in Google Colab or Kaggle, NOT on your laptop).

How to use (Google Colab, free):
  1. Go to https://colab.research.google.com  ->  New notebook.
  2. Upload this file (folder icon on the left -> upload), then run in a cell:
         !python ncmapss_colab_extract.py
     It downloads the official NASA archive (~14 GB) to Colab's temporary disk, reads one subset at a time,
     keeps only the average of every signal per engine per flight cycle, and deletes the big files.
     Runtime: roughly 20-60 minutes depending on Colab's speed.
  3. Download the output file  ncmapss_cycle_summary.csv.gz  (a few MB) from the file panel
     and attach it in the chat.

Nothing is stored on your computer except the small output file.
"""
import os, sys, glob, zipfile, subprocess, shutil
import numpy as np, pandas as pd

URL = "https://phm-datasets.s3.amazonaws.com/NASA/17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip"
WORK = "/content/ncmapss_tmp" if os.path.isdir("/content") else "./ncmapss_tmp"
OUT = "ncmapss_cycle_summary.csv.gz"
os.makedirs(WORK, exist_ok=True)

try:
    import h5py
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "h5py"]); import h5py

outer = os.path.join(WORK, "ncmapss.zip")
if not os.path.exists(outer):
    print("Downloading official NASA archive (about 14 GB) ...", flush=True)
    subprocess.check_call(["wget", "-q", "--show-progress", "-O", outer, URL])

def h5_members(zpath):
    with zipfile.ZipFile(zpath) as z:
        return z, [n for n in z.namelist() if n.lower().endswith(".h5")]

z = zipfile.ZipFile(outer)
names = z.namelist(); print("archive contains:", names[:20], flush=True)
h5s = [n for n in names if n.lower().endswith(".h5")]
if not h5s:                                                  # nested archive: extract inner zip(s) first
    for inner in [n for n in names if n.lower().endswith(".zip")]:
        print("extracting inner archive", inner, flush=True)
        z.extract(inner, WORK)
    z.close(); os.remove(outer)                              # free space
    inner_paths = glob.glob(os.path.join(WORK, "**", "*.zip"), recursive=True)
    sources = [(p, n) for p in inner_paths for n in zipfile.ZipFile(p).namelist() if n.lower().endswith(".h5")]
else:
    sources = [(outer, n) for n in h5s]
print("subsets found:", [os.path.basename(n) for _, n in sources], flush=True)

def dec(a):
    return [x.decode() if isinstance(x, bytes) else str(x) for x in np.array(a).ravel()]

parts_out = []
for zpath, member in sources:
    name = os.path.basename(member).replace(".h5", "")
    try:
        with zipfile.ZipFile(zpath) as zz:
            zz.extract(member, WORK)
        path = os.path.join(WORK, member)
        with h5py.File(path, "r") as f:
            wv, xv, av = dec(f["W_var"]), dec(f["X_s_var"]), dec(f["A_var"])
            for part in ("dev", "test"):
                W = np.asarray(f[f"W_{part}"], dtype=np.float32); X = np.asarray(f[f"X_s_{part}"], dtype=np.float32)
                Y = np.asarray(f[f"Y_{part}"], dtype=np.float32).ravel(); A = np.asarray(f[f"A_{part}"], dtype=np.float32)
                df = pd.DataFrame(np.hstack([A, W, X, Y[:, None]]), columns=av + wv + xv + ["RUL"])
                g = df.groupby(["unit", "cycle"], sort=True)
                s = g.mean(); s["n_seconds"] = g.size(); s = s.reset_index()
                s.insert(0, "part", part); s.insert(0, "subset", name)
                parts_out.append(s)
                print(f"{name} {part}: {len(df):,} rows -> {len(s):,} cycle rows, units {sorted(s.unit.unique().astype(int).tolist())}", flush=True)
                del W, X, Y, A, df
        os.remove(path)
    except Exception as e:                                   # e.g. a truncated subset in the official archive
        print(f"SKIPPED {name}: {e}", flush=True)

R = pd.concat(parts_out, ignore_index=True)
R.to_csv(OUT, index=False, compression="gzip")
print("\nWROTE", OUT, f"{os.path.getsize(OUT)/1e6:.1f} MB,", len(R), "rows,", R.subset.nunique(), "subsets")
shutil.rmtree(WORK, ignore_errors=True)
