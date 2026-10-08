# Pre-specified confirmation protocol: self-timed warning model on real battery run-to-failure data (Severson et al., 2019)

Written before the data are available in this project (the per-cycle summary will be produced by the user with
severson_colab_extract.py and uploaded afterwards). Nothing below will be changed after the data arrive; any deviation will be
listed in a "Deviations" section with reasons. Failing outcomes will be reported as failures.

## Data and units
- Source: the three official batch files of Severson et al. (2019), reduced to one row per cell and cycle (fields cycle,
  QDischarge, QCharge, IR, Tavg, Tmin, Tmax, chargetime) plus one row per cell with the official cycle life.
- A cell is included if its official cycle life L is finite and its summary contains every cycle from its first cycle up to L.
  Cells whose data end before L, or whose summary starts after cycle 2, are excluded (this removes the censored cells and the
  cells whose test was split across batches).
- Remaining life at cycle t: r_t = L - t; rows after cycle L are discarded.
- Cleaning (fixed now): values that are non-finite or outside physical ranges are replaced by the last valid value of the same
  cell (forward fill; backward fill for leading gaps). Ranges: QDischarge and QCharge in [0.5, 1.2] Ah; IR in (0, 0.05] Ohm;
  Tavg, Tmin, Tmax in [15, 60] degC; chargetime in (0, 200] min.

## Time scale (fixed rule, computed from the included cells before any model is run)
- kappa = max(1, round(median(L) / 209.5)), where 209.5 is the median life of the PHM08 training engines.
- Each cell's cycles are grouped into consecutive blocks of kappa cycles (block j = cycles (j-1)*kappa+1 ... j*kappa); every
  feature is averaged within a block; the block's remaining life is r at the block's last cycle divided by kappa. Life in
  blocks = floor(L / kappa). All model and evaluation quantities (window, warning level, caps, features) are in blocks, so the
  model code, grids and the window [-13, +2] are used UNCHANGED; in cycles the window is [-13*kappa, +2*kappa].

## Model (identical to eol_window2.py / ncm_warning.py)
- Inputs: the seven per-cycle features above (block means), z-scored with statistics of the training cells of the split
  (one regime: all cells share the same test conditions apart from the charging protocol, which is not given to the model).
- Causal features (feats.causal_feats), HistGradientBoosting (absolute error, 500 iterations, lr 0.05, 31 leaves, min 40 per
  leaf, seed 0), caps {40, 60, 90} (with c >= H + 20), spans {1, 3, 6}, debounce {1, 2, 3, 5}, shifts -12..+8 step 0.5,
  selection by the number of correct first warnings on out-of-fold predictions of an inner 5-fold split (seed 100 + fold).
- Correct: -13 <= prediction - true remaining life <= +2 (in blocks) at the first warning; no warning before failure = missed.

## Competitors (same tuning and rule; as in ncm_warning.py)
- Age-only: the same regressor and caps with the block index as the only input.
- MLP + Kalman filter: MLP (64, 32) on the causal features, target min(r, 125)/100, scalar Kalman filter with a fixed decrease of
  one block per block, noise ratio in {1/25, 1/100, 1/400}.

## Splits
- Primary: 5-fold cross-validation by cell over all included cells (seed 2026 folds).
- Secondary: leave-one-batch-out (three folds: batches 1, 2, 3).

## Warning levels
- Primary H = 20 blocks; secondary H = 10 and 15 blocks.

## Pre-specified hypotheses (primary split, H = 20) -- the same criteria as the N-CMAPSS confirmation
- B1: in-window rate of the warning model >= 85 %.
- B2: late + missed rate <= 10 %.
- B3: higher in-window rate than age-only (exact McNemar, two-sided p < 0.05).
- B4: higher in-window rate than MLP + Kalman (exact McNemar, two-sided p < 0.05).
- Everything else (H = 10, 15, leave-one-batch-out, lead times, error distributions, cost analysis) is secondary.

## Deviations (added 2026-09-30 after structural data checks and BEFORE any model was run; the hash in BATTERY_PROTOCOL.sha256 covers the text above this section)
Only cell counts, cycle numbers, official lives and discharge capacities were inspected; no feature, model or result.
- D1 (completeness rule). In batches 1 and 3 the summary of every cell ends at cycle L - 1: the official life L is the first
  cycle whose discharge capacity is below 0.88 Ah (80 % of 1.1 Ah), and that cycle is not in the summary (the last recorded
  capacities are 0.880-0.881 Ah). Read literally, "contains every cycle up to L" would exclude these cells. A cell is therefore
  counted as complete if it contains cycles 1 ... L - 1 without gaps. Nothing else changes: the model only uses cycles with
  remaining life r >= 1, i.e. cycles 1 ... L - 1, and rows after cycle L are discarded as specified.
- D2 (cells split across batches). The protocol intended to exclude cells whose test was split across batches, detected by a
  summary that starts after cycle 2. The continuation files restart their cycle count at 1, so that detection fails. The split
  cells are identified from the data providers' published loading code (Severson et al., 2019): b1c0, b1c1, b1c2, b1c3, b1c4
  continue as b2c7, b2c8, b2c9, b2c15, b2c16 (the continuation lengths 662, 981, 1060, 208, 482 cycles match exactly). These ten
  records are excluded, as the protocol intended. Their batch-1 parts never reach 0.88 Ah (last capacities 0.97-1.04 Ah) and
  their batch-2 parts start degraded (0.97-1.03 Ah), so neither part is a complete run to failure.
- D3 (official life not supported by the data). b1c8, b1c10, b1c12, b1c13 and b1c22 have a finite official life but their
  capacity never falls below 0.91 Ah (last values 0.92-0.97 Ah); they are censored in substance and are excluded, as the data
  providers also do ("batteries that do not reach 80 % capacity").
- Primary analysis set: all remaining cells with finite official life (123 cells: 36 + 43 + 44 by batch). The providers also
  drop four batch-3 channels as "noisy" (b3c2, b3c37, b3c42, b3c43); the protocol has no such rule, so they stay in the primary
  set. A secondary analysis without them (119 cells) is added now, before any run. Cells b3c23 and b3c32 (no official life)
  are excluded by the protocol.

## Erratum to the Deviations notes (added after the run, 2026-09-30; no change to the analysis)
An independent review of the code and data after the run found three imprecise details in the notes above. (1) D1: the last
recorded capacities of batch-1 and batch-3 cells are 0.880-0.883 Ah (not 0.880-0.881); in batch 2 the summaries run past L and
are truncated at L. The evaluation uses blocks with remaining life >= 1 block; the training rows include the final block of each
cell (remaining life < 1 block), as in the engine code. (2) D3: the last capacities of the five excluded cells are 0.913-0.969 Ah
(not 0.92-0.97), and "never falls below 0.91 Ah" holds after the pre-specified cleaning (the raw records contain 0 Ah glitches).
(3) The "Model" section states that all cells share the same test conditions apart from the charging protocol; the three batches
also used different rest periods. The inner-split seed for leave-one-batch-out was 100 + batch (not specified by the protocol).
