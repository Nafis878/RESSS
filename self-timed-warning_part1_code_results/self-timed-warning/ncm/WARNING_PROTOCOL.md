# Pre-specified confirmation protocol: end-of-life warning model on N-CMAPSS

Written before the warning model (or any of its competitors below) has been run on N-CMAPSS. N-CMAPSS was used earlier in
this project for a different study (safety-calibrated lower bounds at fixed life fractions); no warning rule, warning level,
target cap, debounce or shift has ever been fitted, tuned or evaluated on it. The warning model was developed on PHM08 and
then run unchanged on C-MAPSS FD001-FD004. Every choice below is fixed now; failing outcomes will be reported as failures.
Any later deviation will be listed in a "Deviations" section with reasons.

## Data (unchanged from ncm/PREREGISTRATION.md)
- 99 run-to-failure engines (9 subsets), one row per engine per flight cycle (means of the 1 Hz signals).
- Sensors: T24, T30, T48, T50, Nf, Nc. Operating regime = flight class Fc (1, 2, 3); z-scores per Fc from training engines only.

## Warning model (identical to eol_window2.py; nothing re-designed for N-CMAPSS)
- Causal features per cycle (feats.causal_feats): 10- and 30-cycle exponential means of the baseline-removed signals,
  early-life baseline (first 20 cycles), 15- and 40-cycle slopes, age.
- Regressor: HistGradientBoosting, absolute-error loss, 500 iterations, learning rate 0.05, 31 leaves, min 40 samples per
  leaf, seed 0; target = min(RUL, cap), cap in {40, 60, 90}.
- Warning rule: smoothing span in {1, 3, 6} (causal exponential mean of the prediction), shift s in {-12, -11.5, ..., +8},
  debounce k in {1, 2, 3, 5}; warning at the first cycle where the smoothed, shifted prediction has been <= H for k
  consecutive cycles; the prediction issued at that cycle is scored. No warning before failure = MISSED (counted as late).
- Settings (cap, span, k, s) chosen by the number of in-window first warnings on out-of-fold predictions of an inner
  5-fold split of the training engines (seed 100 + fold), exactly as in eol_window2.py; the model is then refit on all
  training engines and applied once to the test engines.
- Correct: -13 <= prediction - true RUL <= +2 at the warning cycle.

## Competitors (same features, same inner-CV tuning of span, k, s, same warning rule)
- Age-only: the same regressor and caps with the cycle count as the only input (tests whether the sensors add value).
- MLP + Kalman filter (Peel-style re-implementation, strongest competitor on PHM08): MLP (64, 32), target min(RUL, 125)/100,
  constant-velocity Kalman filter over time with process/measurement noise ratio in {1/25, 1/100, 1/400} chosen with the
  other settings.

## Splits
- Primary: 5-fold cross-validation by engine over all 99 engines (seed 2026 folds, as in the earlier N-CMAPSS study).
- Secondary: official split (train on the 60 dev engines, test on the 39 test engines).

## Warning levels
- Primary H = 20 cycles. Secondary H = 10 and H = 15.

## Pre-specified hypotheses (primary split, H = 20)
- W1: in-window rate of the warning model >= 85 %.
- W2: late + missed rate of the warning model <= 10 %.
- W3: the warning model has a higher in-window rate than the age-only competitor (exact McNemar test on paired engine
  outcomes, two-sided p < 0.05).
- W4: the warning model has a higher in-window rate than MLP + Kalman (exact McNemar, two-sided p < 0.05).
- Everything else (H = 10, 15, official split, lead times, error distributions) is secondary and descriptive.

## Deviations (added after the runs; the hash in WARNING_PROTOCOL.sha256 covers the text above this section)
- The protocol gives the inner-split seed as 100 + fold for the cross-validation folds; the official split has no fold number,
  and seed 106 was used for its inner split. No other deviation. Outcomes: W1 not supported (68.7 %), W2 not supported
  (23.2 % late + missed), W3 supported, W4 not supported (p = 0.154).
