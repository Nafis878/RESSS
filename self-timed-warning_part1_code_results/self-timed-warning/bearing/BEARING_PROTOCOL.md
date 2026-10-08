# Pre-specified confirmation protocol: self-timed warning model on rolling-bearing run-to-failure data (FEMTO / PRONOSTIA)

Written before any bearing measurement has been read in this project. Only the folder and file names of the public mirror
(github.com/wkzs111/phm-ieee-2012-data-challenge-dataset) were listed, to name the units below; no data value has been opened.
The protocol is hashed (SHA-256 in BEARING_PROTOCOL.sha256) and sent to the co-author before the data are downloaded.
Nothing below will be changed after the data are read; any deviation will be listed in a "Deviations" section with reasons.
Failing outcomes will be reported as failures. This protocol also pre-specifies a theory-guided variant of the shift rule (Part B).

## Part A. Confirmation of the unchanged model

### Data and units
- Source: the IEEE PHM 2012 data challenge data recorded on the PRONOSTIA platform (FEMTO-ST). 17 bearings run to failure under
  three operating conditions: condition 1 (1800 rpm, 4000 N): Bearing1_1 ... Bearing1_7; condition 2 (1650 rpm, 4200 N):
  Bearing2_1 ... Bearing2_7; condition 3 (1500 rpm, 5000 N): Bearing3_1, Bearing3_2, Bearing3_3.
- Complete runs: folders Learning_set (Bearing1_1, 1_2, 2_1, 2_2, 3_1, 3_2) and Full_Test_Set (the other 11). The truncated
  Test_set folder is not used.
- Each acc_*.csv file is one snapshot: 2560 samples of horizontal and vertical acceleration (25.6 kHz, 0.1 s), recorded every
  10 s; columns hour, minute, second, microsecond, horizontal, vertical. The field separator (comma or semicolon) is detected per
  file. Temperature files are not used (not available for all bearings).
- Snapshots are ordered by file index. Life of a bearing L = number of acceleration snapshots (the test was stopped at failure);
  remaining life at snapshot t: r_t = L - t. A bearing is included if its snapshot files are complete (indices 1..L, no gap).

### Per-snapshot features (fixed now)
For each of the two channels (mean removed): RMS; peak (max |x|); kurtosis (Fisher, i.e. 0 for a Gaussian); crest factor
(peak / RMS). Eight features per snapshot. Non-finite values are replaced by the last valid value of the same bearing (forward
fill; backward fill for leading gaps).

### Time scale (same rule as the battery protocol)
- kappa = max(1, round(median(L) / 209.5)); consecutive snapshots are averaged in blocks of kappa (block j = snapshots
  (j-1)*kappa+1 ... j*kappa); remaining life of a block = r at its last snapshot / kappa; blocks up to floor(L / kappa).
- The model, grids, warning levels and the window [-13, +2] are applied in blocks, unchanged.

### Model (identical to eol_window2.py / battery_warning.py)
- Normalisation: z-score per operating condition (three regimes) with statistics of the training bearings of the split; if a
  condition has no training bearing in a split, the pooled statistics of all training bearings are used for it.
- Causal features (feats.causal_feats), HistGradientBoosting (absolute error, 500 iterations, lr 0.05, 31 leaves, min 40 per
  leaf, seed 0), caps {40, 60, 90} (c >= H + 20), spans {1, 3, 6}, debounce {1, 2, 3, 5}, shifts -12..+8 step 0.5, selection by
  the number of correct first warnings on out-of-fold predictions of an inner 5-fold split (seed 100 + outer fold).
- Correct: -13 <= prediction - true remaining life <= +2 (blocks) at the first warning; no warning before failure = missed.

### Competitors (same tuning and rule)
- Age-only: the same regressor and caps with the block index as the only input.
- MLP + Kalman filter: MLP (64, 32) on the causal features, target min(r, 125)/100, scalar Kalman filter with a fixed decrease
  of one block per block, noise ratio in {1/25, 1/100, 1/400}.

### Splits
- Primary: 5-fold cross-validation by bearing over all included bearings (seed 2026 folds, safe_common.outer_folds).
- Secondary: the official challenge split (train on the 6 Learning_set bearings, test on the 11 Full_Test_Set bearings;
  inner seed 106).

### Warning levels
- Primary H = 20 blocks; secondary H = 10 and 15 blocks.

### Pre-specified hypotheses (primary split, H = 20), the same criteria as the N-CMAPSS and battery confirmations
- F1: in-window rate of the warning model >= 85 %.
- F2: late + missed rate <= 10 %.
- F3: higher in-window rate than age-only (exact McNemar, two-sided p < 0.05).
- F4: higher in-window rate than MLP + Kalman (exact McNemar, two-sided p < 0.05).
- With 17 bearings the McNemar tests have little power; a non-significant F3/F4 will be reported as not supported.
- Everything else (H = 10, 15, the official split, error distributions, Part B) is secondary.

## Part B. Theory-guided shift rule (STW-T), fixed before it is run on any dataset
Motivation: Proposition 1 of the manuscript says the best shift makes the median warning error equal to the window centre
(-5.5). On N-CMAPSS the count-selected shifts were about 3 cycles short of that value.
- Rule: cap, span and debounce are chosen exactly as in the standard model (count criterion on out-of-fold predictions, with
  the shift free). Then, with these three fixed, the shift is re-chosen as the grid value s that minimises
  |median over training bearings of (out-of-fold first-warning error with shift s) - (-5.5)|; missed units are ignored in the
  median; ties are broken by the larger out-of-fold in-window count, then by smaller |s|. Everything else is unchanged.
- T1 (bearings, fresh data, primary split, H = 20): the in-window rate of STW-T is not lower than that of the standard model by
  more than 5 percentage points. Reported with the exact McNemar test between the two.
- STW-T will also be run, with the same code, on PHM08, FD001-FD004, N-CMAPSS and the battery data (primary splits,
  H = 10, 15, 20). Those datasets were seen before this rule was written, so those results are descriptive, not confirmatory;
  in particular an improvement on N-CMAPSS, whose result motivated the rule, is not evidence for the rule.
