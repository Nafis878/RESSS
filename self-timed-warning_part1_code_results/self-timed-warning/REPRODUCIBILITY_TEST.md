# Reproducibility test (5 October 2026)

The repository was unzipped into an empty folder and run with a new virtual environment created from
`requirements.txt` (Python 3.13, CPU only, 2 cores). No file from the original working folders was used.

## Level 1: `sh reproduce_numbers.sh` (25 s)

All three paper files were rebuilt from `results/` and are byte-identical to `paper2/reference/`:

| File | Result |
|---|---|
| `paper2/numbers.json` (every number in the manuscript and supplement) | IDENTICAL |
| `paper2/tex/manuscript.tex` | IDENTICAL |
| `paper2/tex/supplementary.tex` | IDENTICAL |

All 131 consistency checks of the manuscript build passed.

## Level 2, subset: experiments rerun from the data

Every rerun output was compared with its frozen copy in `results/` by `verify_reproduction.py`, value by value:

| Experiment | Output | Result |
|---|---|---|
| Main results, FD001 and FD003 (Table 2) | `window/first_warning_v2_FD001.csv`, `..._FD003.csv` | IDENTICAL |
| N-CMAPSS confirmation, incl. MLP + Kalman and age-only competitors (Table 7) | `ncm/warning_results.csv`, `ncm/warning_summary.json` | IDENTICAL |
| Bearing confirmation (Table 7) | `bearing/warning_results.csv`, `bearing/warning_summary.json` | IDENTICAL |
| Battery confirmation, all three analyses, and battery cost (Table 7, Supp. S5, S9) | `battery/warning_results.csv`, `battery/warning_summary.json`, `battery/cost.csv` | IDENTICAL |
| Other windows and cost, FD001 (Supp. S8–S9) | `multi/FD001_*.csv` (3 files) | IDENTICAL |
| Timing controls, health-indicator alarm, cost-tuned policies, N-CMAPSS and FD001 (Tables 3 and 6) | `rev/NCMAPSS6_*.csv`, `rev/FD001_*.csv` (6 files) | IDENTICAL |

Result: 18 of 18 rerun files identical, 0 different.

## Earlier check, all seven datasets

`rev_experiments.py` refits the self-timed warning model in every fold. During the revision of the manuscript it was run on
all seven datasets (PHM08, FD001–FD004, N-CMAPSS and battery). `rev_analyze.py` confirmed that its model outputs reproduce
the frozen results in `window/first_warning_v2_*.csv`, `ncm/` and `battery/` engine by engine on every dataset.

## Not covered by this test

- **Neural networks (level 3):** the 12 outputs of the neural-network analyses use fixed seeds, but JAX floating-point
  reductions can differ slightly between CPUs. `run_all.sh` reruns them, and `verify_reproduction.py` reports any
  differences.
- **Run logs, timings, Excel workbooks and figure files:** these are not compared byte by byte, because they contain time
  stamps or wall-clock times.
