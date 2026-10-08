# FD004 under the conventions of Kamariotis et al. (exploratory; plan hashed before the run)

## c_p/c_c = 0.1  (primary)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 8.44 | 4.20 to 12.68 | 7.57 to 9.57 | 0 | 1.1049 |
| STW_cost | 13.12 | 1.63 to 24.62 | 5.12 to 24.81 | 2 | 1.1526 |
| STW_cost_1se | 11.63 | 2.95 to 20.31 | 7.04 to 20.19 | 1 | 1.1374 |
| P1_cls_q | 32.74 | 11.29 to 54.19 | 14.19 to 54.63 | 8 | 1.3525 |
| P1_cls_opt_mid | 12.83 | 1.39 to 24.27 | 4.85 to 24.34 | 2 | 1.1496 |
| P1_cls_opt_max | 12.83 | 1.39 to 24.27 | 4.85 to 24.34 | 2 | 1.1496 |
| P1_res_q | 64.22 | 34.52 to 93.92 | 35.93 to 93.07 | 17 | 1.6732 |
| P1_res_opt_mid | 11.25 | 2.58 to 19.92 | 6.76 to 19.67 | 1 | 1.1335 |
| P1_res_opt_max | 11.25 | 2.58 to 19.92 | 6.76 to 19.67 | 1 | 1.1335 |
| P3_res60 | 15.93 | 6.85 to 25.01 | 11.13 to 24.70 | 1 | 1.1812 |
| age_grid | 91.65 | 78.53 to 104.78 | 80.26 to 108.61 | 1 | 1.9527 |
| P3_res125 | 12.20 | 3.47 to 20.93 | 7.58 to 20.64 | 1 | 1.1432 |
| HI_cost | 13.64 | 4.67 to 22.60 | 8.94 to 22.28 | 1 | 1.1578 |
| STW_window_unmapped (unmapped) | 8.79 | 0.52 to 17.05 | 4.32 to 16.78 | 1 | 1.1084 |
| STW_cost_unmapped (unmapped) | 11.07 | 0.12 to 22.01 | 3.19 to 22.49 | 2 | 1.1316 |
| STW_cost_1se_unmapped (unmapped) | 5.79 | 1.72 to 9.85 | 4.96 to 6.84 | 0 | 1.0778 |
| run_to_failure | 877.49 | 841.40 to 913.57 | 875.75 to 879.08 | 249 | 9.9593 |
| perfect_grid | 0.00 | -3.78 to 3.78 | 0.00 to 0.00 | 0 | 1.0189 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -24.30 | -46.40 to -5.71 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | -4.39 | -15.78 to +3.41 | unclear |
| STW_window | P1_cls_opt_max | -4.39 | -15.78 to +3.41 | unclear |
| STW_window | P1_res_q | -55.78 | -84.91 to -27.41 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -2.81 | -10.83 to +1.39 | unclear |
| STW_window | P1_res_opt_max | -2.81 | -10.83 to +1.39 | unclear |
| STW_window | P3_res60 | -7.49 | -15.97 to -3.02 | STW_window beats P3_res60 |
| STW_window | age_grid | -83.21 | -100.03 to -71.67 | STW_window beats age_grid |
| STW_window | P3_res125 | -3.76 | -11.86 to +0.52 | unclear |
| STW_window | HI_cost | -5.20 | -13.53 to -0.73 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -19.62 | -38.27 to -4.51 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | +0.30 | -0.11 to +0.71 | unclear |
| STW_cost | P1_cls_opt_max | +0.30 | -0.11 to +0.71 | unclear |
| STW_cost | P1_res_q | -51.09 | -80.14 to -25.38 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | +1.87 | -2.21 to +9.72 | unclear |
| STW_cost | P1_res_opt_max | +1.87 | -2.21 to +9.72 | unclear |
| STW_cost | P3_res60 | -2.81 | -7.19 to +5.23 | unclear |
| STW_cost | age_grid | -78.53 | -98.31 to -61.87 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +0.93 | -3.25 to +8.80 | unclear |
| STW_cost | HI_cost | -0.51 | -12.31 to +14.21 | unclear |
| STW_cost_1se | P1_cls_q | -21.11 | -40.03 to -2.87 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | -1.19 | -9.01 to +2.90 | unclear |
| STW_cost_1se | P1_cls_opt_max | -1.19 | -9.01 to +2.90 | unclear |
| STW_cost_1se | P1_res_q | -52.58 | -81.95 to -26.85 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | +0.38 | +0.04 to +0.71 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +0.38 | +0.04 to +0.71 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | -4.30 | -4.90 to -3.77 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -80.02 | -98.54 to -65.68 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -0.57 | -1.06 to -0.06 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -2.00 | -13.26 to +9.22 | unclear |

## c_p/c_c = 0.01  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 9.71 | 5.38 to 14.04 | 8.81 to 10.82 | 0 | 1.1178 |
| STW_cost | 89.39 | -27.03 to 205.81 | 5.12 to 215.86 | 2 | 1.9296 |
| STW_cost_1se | 50.57 | -33.44 to 134.59 | 7.04 to 137.77 | 1 | 1.5342 |
| P1_cls_q | 47.29 | -34.91 to 129.49 | 4.77 to 132.20 | 1 | 1.5007 |
| P1_cls_opt_mid | 88.89 | -27.22 to 205.00 | 4.85 to 214.66 | 2 | 1.9245 |
| P1_cls_opt_max | 88.89 | -27.22 to 205.00 | 4.85 to 214.66 | 2 | 1.9245 |
| P1_res_q | 50.06 | -33.68 to 133.80 | 6.76 to 136.73 | 1 | 1.5289 |
| P1_res_opt_mid | 53.25 | -32.25 to 138.74 | 8.91 to 141.91 | 1 | 1.5614 |
| P1_res_opt_max | 53.25 | -32.25 to 138.74 | 8.91 to 141.91 | 1 | 1.5614 |
| P3_res60 | 13.13 | 8.53 to 17.74 | 12.09 to 14.40 | 0 | 1.1527 |
| age_grid | 175.44 | 21.97 to 328.92 | 92.12 to 343.43 | 1 | 2.8064 |
| P3_res125 | 64.19 | -27.31 to 155.70 | 16.64 to 159.01 | 1 | 1.6729 |
| HI_cost | 53.28 | -32.64 to 139.19 | 8.94 to 141.90 | 1 | 1.5617 |
| STW_window_unmapped (unmapped) | 46.73 | -34.88 to 128.35 | 4.32 to 131.03 | 1 | 1.4950 |
| STW_cost_unmapped (unmapped) | 85.94 | -27.78 to 199.66 | 3.19 to 209.98 | 2 | 1.8945 |
| STW_cost_1se_unmapped (unmapped) | 5.79 | 1.72 to 9.85 | 4.96 to 6.84 | 0 | 1.0778 |
| run_to_failure | 9674.85 | 9313.99 to 10035.71 | 9657.48 to 9690.78 | 249 | 99.5935 |
| perfect_grid | 0.00 | -3.78 to 3.78 | 0.00 to 0.00 | 0 | 1.0189 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -37.57 | -122.07 to +4.65 | unclear |
| STW_window | P1_cls_opt_mid | -79.18 | -204.81 to +4.69 | unclear |
| STW_window | P1_cls_opt_max | -79.18 | -204.81 to +4.69 | unclear |
| STW_window | P1_res_q | -40.35 | -126.46 to +2.62 | unclear |
| STW_window | P1_res_opt_mid | -43.54 | -131.55 to +0.39 | unclear |
| STW_window | P1_res_opt_max | -43.54 | -131.55 to +0.39 | unclear |
| STW_window | P3_res60 | -3.42 | -3.79 to -3.06 | STW_window beats P3_res60 |
| STW_window | age_grid | -165.73 | -333.22 to -82.26 | STW_window beats age_grid |
| STW_window | P3_res125 | -54.48 | -148.66 to -7.26 | STW_window beats P3_res125 |
| STW_window | HI_cost | -43.56 | -131.88 to +0.55 | unclear |
| STW_cost | P1_cls_q | +42.10 | -0.20 to +126.83 | unclear |
| STW_cost | P1_cls_opt_mid | +0.50 | -0.17 to +1.44 | unclear |
| STW_cost | P1_cls_opt_max | +0.50 | -0.17 to +1.44 | unclear |
| STW_cost | P1_res_q | +39.33 | -3.85 to +124.41 | unclear |
| STW_cost | P1_res_opt_mid | +36.14 | -8.51 to +121.95 | unclear |
| STW_cost | P1_res_opt_max | +36.14 | -8.51 to +121.95 | unclear |
| STW_cost | P3_res60 | +76.25 | -7.86 to +202.52 | unclear |
| STW_cost | age_grid | -86.05 | -309.64 to +80.27 | unclear |
| STW_cost | P3_res125 | +25.19 | -25.20 to +114.25 | unclear |
| STW_cost | HI_cost | +36.11 | -92.95 to +202.43 | unclear |
| STW_cost_1se | P1_cls_q | +3.29 | +2.10 to +5.53 | P1_cls_q beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_mid | -38.31 | -123.36 to +5.18 | unclear |
| STW_cost_1se | P1_cls_opt_max | -38.31 | -123.36 to +5.18 | unclear |
| STW_cost_1se | P1_res_q | +0.51 | +0.04 to +1.18 | P1_res_q beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_mid | -2.68 | -4.60 to -1.58 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -2.68 | -4.60 to -1.58 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | +37.44 | -5.74 to +123.97 | unclear |
| STW_cost_1se | age_grid | -124.87 | -327.73 to +35.20 | unclear |
| STW_cost_1se | P3_res125 | -13.62 | -21.89 to -9.20 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -2.70 | -131.64 to +125.28 | unclear |

## c_p/c_c = 0.02  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 9.71 | 5.38 to 14.04 | 8.81 to 10.82 | 0 | 1.1178 |
| STW_cost | 47.02 | -10.81 to 104.85 | 5.12 to 109.72 | 2 | 1.4979 |
| STW_cost_1se | 28.94 | -12.79 to 70.67 | 7.04 to 72.45 | 1 | 1.3137 |
| P1_cls_q | 25.88 | -14.87 to 66.63 | 4.54 to 68.18 | 1 | 1.2826 |
| P1_cls_opt_mid | 46.63 | -11.04 to 104.31 | 4.85 to 108.93 | 2 | 1.4940 |
| P1_cls_opt_max | 46.63 | -11.04 to 104.31 | 4.85 to 108.93 | 2 | 1.4940 |
| P1_res_q | 28.50 | -13.10 to 70.10 | 6.76 to 71.69 | 1 | 1.3093 |
| P1_res_opt_mid | 31.23 | -11.24 to 73.70 | 8.91 to 75.45 | 1 | 1.3371 |
| P1_res_opt_max | 31.23 | -11.24 to 73.70 | 8.91 to 75.45 | 1 | 1.3371 |
| P3_res60 | 13.13 | 8.53 to 17.74 | 12.09 to 14.40 | 0 | 1.1527 |
| age_grid | 135.87 | 59.94 to 211.80 | 92.12 to 221.61 | 1 | 2.4032 |
| P3_res125 | 40.60 | -4.83 to 86.03 | 16.64 to 87.86 | 1 | 1.4326 |
| HI_cost | 31.25 | -11.54 to 74.05 | 8.94 to 75.45 | 1 | 1.3373 |
| STW_window_unmapped (unmapped) | 25.65 | -14.79 to 66.09 | 4.32 to 67.56 | 1 | 1.2802 |
| STW_cost_unmapped (unmapped) | 44.35 | -11.98 to 100.67 | 3.19 to 105.82 | 2 | 1.4707 |
| STW_cost_1se_unmapped (unmapped) | 5.79 | 1.72 to 9.85 | 4.96 to 6.84 | 0 | 1.0778 |
| run_to_failure | 4787.43 | 4607.00 to 4967.86 | 4778.74 to 4795.39 | 249 | 49.7967 |
| perfect_grid | 0.00 | -3.78 to 3.78 | 0.00 to 0.00 | 0 | 1.0189 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -16.17 | -58.04 to +4.87 | unclear |
| STW_window | P1_cls_opt_mid | -36.92 | -99.10 to +4.69 | unclear |
| STW_window | P1_cls_opt_max | -36.92 | -99.10 to +4.69 | unclear |
| STW_window | P1_res_q | -18.79 | -61.50 to +2.62 | unclear |
| STW_window | P1_res_opt_mid | -21.52 | -65.17 to +0.39 | unclear |
| STW_window | P1_res_opt_max | -21.52 | -65.17 to +0.39 | unclear |
| STW_window | P3_res60 | -3.42 | -3.79 to -3.06 | STW_window beats P3_res60 |
| STW_window | age_grid | -126.15 | -211.39 to -82.26 | STW_window beats age_grid |
| STW_window | P3_res125 | -30.89 | -77.57 to -7.26 | STW_window beats P3_res125 |
| STW_window | HI_cost | -21.54 | -65.36 to +0.55 | unclear |
| STW_cost | P1_cls_q | +21.14 | +0.05 to +63.08 | P1_cls_q beats STW_cost |
| STW_cost | P1_cls_opt_mid | +0.39 | -0.13 to +1.01 | unclear |
| STW_cost | P1_cls_opt_max | +0.39 | -0.13 to +1.01 | unclear |
| STW_cost | P1_res_q | +18.52 | -2.86 to +60.64 | unclear |
| STW_cost | P1_res_opt_mid | +15.79 | -6.29 to +58.28 | unclear |
| STW_cost | P1_res_opt_max | +15.79 | -6.29 to +58.28 | unclear |
| STW_cost | P3_res60 | +33.89 | -7.86 to +96.41 | unclear |
| STW_cost | age_grid | -88.85 | -197.05 to -5.08 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +6.42 | -18.28 to +50.42 | unclear |
| STW_cost | HI_cost | +15.76 | -48.16 to +97.99 | unclear |
| STW_cost_1se | P1_cls_q | +3.06 | +2.30 to +4.29 | P1_cls_q beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_mid | -17.69 | -59.76 to +3.88 | unclear |
| STW_cost_1se | P1_cls_opt_max | -17.69 | -59.76 to +3.88 | unclear |
| STW_cost_1se | P1_res_q | +0.44 | +0.04 to +0.90 | P1_res_q beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_mid | -2.29 | -3.34 to -1.57 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -2.29 | -3.34 to -1.57 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | +15.81 | -5.74 to +58.71 | unclear |
| STW_cost_1se | age_grid | -106.93 | -207.86 to -30.18 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -11.66 | -15.87 to -9.20 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -2.31 | -65.90 to +60.81 | unclear |

## c_p/c_c = 0.05  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 9.71 | 5.38 to 14.04 | 8.81 to 10.82 | 0 | 1.1178 |
| STW_cost | 21.60 | -1.25 to 44.45 | 5.12 to 46.04 | 2 | 1.2389 |
| STW_cost_1se | 15.96 | -0.66 to 32.58 | 7.04 to 33.26 | 1 | 1.1815 |
| P1_cls_q | 27.91 | 0.38 to 55.44 | 4.11 to 59.18 | 3 | 1.3033 |
| P1_cls_opt_mid | 21.28 | -1.50 to 44.06 | 4.85 to 45.49 | 2 | 1.2357 |
| P1_cls_opt_max | 21.28 | -1.50 to 44.06 | 4.85 to 45.49 | 2 | 1.2357 |
| P1_res_q | 15.56 | -1.01 to 32.14 | 6.76 to 32.67 | 1 | 1.1775 |
| P1_res_opt_mid | 18.02 | 1.09 to 34.95 | 8.91 to 35.58 | 1 | 1.2025 |
| P1_res_opt_max | 18.02 | 1.09 to 34.95 | 8.91 to 35.58 | 1 | 1.2025 |
| P3_res60 | 13.13 | 8.53 to 17.74 | 12.09 to 14.40 | 0 | 1.1527 |
| age_grid | 112.12 | 82.72 to 141.53 | 92.12 to 147.82 | 1 | 2.1613 |
| P3_res125 | 23.09 | 5.45 to 40.73 | 13.59 to 41.24 | 1 | 1.2541 |
| HI_cost | 18.04 | 0.89 to 35.19 | 8.94 to 35.57 | 1 | 1.2027 |
| STW_window_unmapped (unmapped) | 13.00 | -2.99 to 28.99 | 4.32 to 29.48 | 1 | 1.1514 |
| STW_cost_unmapped (unmapped) | 19.39 | -2.68 to 41.45 | 3.19 to 43.32 | 2 | 1.2164 |
| STW_cost_1se_unmapped (unmapped) | 5.79 | 1.72 to 9.85 | 4.96 to 6.84 | 0 | 1.0778 |
| run_to_failure | 1854.97 | 1782.80 to 1927.14 | 1851.50 to 1858.16 | 249 | 19.9187 |
| perfect_grid | 0.00 | -3.78 to 3.78 | 0.00 to 0.00 | 0 | 1.0189 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -18.20 | -49.65 to +5.62 | unclear |
| STW_window | P1_cls_opt_mid | -11.57 | -35.68 to +4.69 | unclear |
| STW_window | P1_cls_opt_max | -11.57 | -35.68 to +4.69 | unclear |
| STW_window | P1_res_q | -5.85 | -22.50 to +2.62 | unclear |
| STW_window | P1_res_opt_mid | -8.31 | -25.36 to +0.39 | unclear |
| STW_window | P1_res_opt_max | -8.31 | -25.36 to +0.39 | unclear |
| STW_window | P3_res60 | -3.42 | -3.79 to -3.06 | STW_window beats P3_res60 |
| STW_window | age_grid | -102.41 | -137.80 to -82.26 | STW_window beats age_grid |
| STW_window | P3_res125 | -13.38 | -31.02 to -4.31 | STW_window beats P3_res125 |
| STW_window | HI_cost | -8.33 | -25.49 to +0.55 | unclear |
| STW_cost | P1_cls_q | -6.31 | -22.34 to +2.01 | unclear |
| STW_cost | P1_cls_opt_mid | +0.32 | -0.12 to +0.78 | unclear |
| STW_cost | P1_cls_opt_max | +0.32 | -0.12 to +0.78 | unclear |
| STW_cost | P1_res_q | +6.03 | -2.34 to +22.45 | unclear |
| STW_cost | P1_res_opt_mid | +3.58 | -5.09 to +20.05 | unclear |
| STW_cost | P1_res_opt_max | +3.58 | -5.09 to +20.05 | unclear |
| STW_cost | P3_res60 | +8.46 | -7.86 to +32.73 | unclear |
| STW_cost | age_grid | -90.52 | -132.37 to -56.75 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -1.49 | -10.70 to +15.51 | unclear |
| STW_cost | HI_cost | +3.56 | -21.24 to +35.27 | unclear |
| STW_cost_1se | P1_cls_q | -11.95 | -35.75 to +4.18 | unclear |
| STW_cost_1se | P1_cls_opt_mid | -5.32 | -21.67 to +3.11 | unclear |
| STW_cost_1se | P1_cls_opt_max | -5.32 | -21.67 to +3.11 | unclear |
| STW_cost_1se | P1_res_q | +0.40 | +0.04 to +0.75 | P1_res_q beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_mid | -2.06 | -2.67 to -1.54 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -2.06 | -2.67 to -1.54 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | +2.83 | -5.74 to +19.58 | unclear |
| STW_cost_1se | age_grid | -96.16 | -135.46 to -66.79 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -7.13 | -8.41 to -6.23 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -2.08 | -26.45 to +22.09 | unclear |

## c_p/c_c = 0.2  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 8.16 | 2.90 to 13.43 | 5.82 to 12.18 | 1 | 1.1021 |
| STW_cost | 8.41 | 2.10 to 14.72 | 4.65 to 13.70 | 2 | 1.1046 |
| STW_cost_1se | 9.55 | 4.17 to 14.92 | 7.12 to 13.58 | 1 | 1.1162 |
| P1_cls_q | 30.25 | 15.90 to 44.60 | 17.68 to 43.71 | 17 | 1.3271 |
| P1_cls_opt_mid | 8.60 | 2.31 to 14.89 | 4.85 to 13.77 | 2 | 1.1065 |
| P1_cls_opt_max | 8.60 | 2.31 to 14.89 | 4.85 to 13.77 | 2 | 1.1065 |
| P1_res_q | 29.49 | 15.60 to 43.39 | 17.39 to 42.20 | 17 | 1.3194 |
| P1_res_opt_mid | 9.10 | 3.72 to 14.47 | 6.76 to 13.13 | 1 | 1.1115 |
| P1_res_opt_max | 9.10 | 3.72 to 14.47 | 6.76 to 13.13 | 1 | 1.1115 |
| P3_res60 | 9.10 | 3.72 to 14.47 | 6.76 to 13.13 | 1 | 1.1115 |
| age_grid | 82.93 | 72.03 to 93.83 | 72.51 to 95.46 | 4 | 1.8638 |
| P3_res125 | 10.02 | 4.62 to 15.43 | 7.58 to 14.04 | 1 | 1.1210 |
| HI_cost | 10.38 | 5.01 to 15.75 | 7.88 to 14.44 | 1 | 1.1247 |
| STW_window_unmapped (unmapped) | 6.68 | 1.61 to 11.74 | 4.32 to 10.44 | 1 | 1.0869 |
| STW_cost_unmapped (unmapped) | 6.48 | 0.56 to 12.40 | 2.76 to 11.64 | 2 | 1.0849 |
| STW_cost_1se_unmapped (unmapped) | 5.93 | 1.86 to 10.01 | 5.09 to 6.98 | 0 | 1.0793 |
| run_to_failure | 388.74 | 370.70 to 406.79 | 387.87 to 389.54 | 249 | 4.9797 |
| perfect_grid | 0.00 | -3.78 to 3.78 | 0.00 to 0.00 | 0 | 1.0189 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -22.09 | -34.94 to -10.29 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | -0.44 | -4.03 to +1.54 | unclear |
| STW_window | P1_cls_opt_max | -0.44 | -4.03 to +1.54 | unclear |
| STW_window | P1_res_q | -21.33 | -34.33 to -9.72 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -0.93 | -1.31 to -0.55 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -0.93 | -1.31 to -0.55 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -0.93 | -1.31 to -0.55 | STW_window beats P3_res60 |
| STW_window | age_grid | -74.76 | -87.70 to -63.78 | STW_window beats age_grid |
| STW_window | P3_res125 | -1.86 | -2.38 to -1.33 | STW_window beats P3_res125 |
| STW_window | HI_cost | -2.22 | -6.92 to +2.54 | unclear |
| STW_cost | P1_cls_q | -21.84 | -34.73 to -10.39 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | -0.19 | -0.57 to +0.19 | unclear |
| STW_cost | P1_cls_opt_max | -0.19 | -0.57 to +0.19 | unclear |
| STW_cost | P1_res_q | -21.08 | -33.90 to -9.66 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | -0.69 | -2.62 to +2.87 | unclear |
| STW_cost | P1_res_opt_max | -0.69 | -2.62 to +2.87 | unclear |
| STW_cost | P3_res60 | -0.69 | -2.62 to +2.87 | unclear |
| STW_cost | age_grid | -74.52 | -87.89 to -62.78 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -1.61 | -3.61 to +1.94 | unclear |
| STW_cost | HI_cost | -1.97 | -7.24 to +4.28 | unclear |
| STW_cost_1se | P1_cls_q | -20.71 | -33.60 to -9.02 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | +0.95 | -2.65 to +2.90 | unclear |
| STW_cost_1se | P1_cls_opt_max | +0.95 | -2.65 to +2.90 | unclear |
| STW_cost_1se | P1_res_q | -19.95 | -33.01 to -8.48 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | +0.45 | +0.10 to +0.79 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +0.45 | +0.10 to +0.79 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | +0.45 | +0.10 to +0.79 | P3_res60 beats STW_cost_1se |
| STW_cost_1se | age_grid | -73.38 | -86.38 to -62.13 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -0.48 | -0.99 to +0.02 | unclear |
| STW_cost_1se | HI_cost | -0.83 | -5.64 to +3.92 | unclear |

## c_p/c_c = 0.5  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 5.92 | 1.83 to 10.02 | 4.86 to 7.28 | 1 | 1.0792 |
| STW_cost | 4.90 | 0.75 to 9.06 | 3.61 to 6.48 | 2 | 1.0688 |
| STW_cost_1se | 6.99 | 2.86 to 11.11 | 6.07 to 8.12 | 0 | 1.0901 |
| P1_cls_q | 20.28 | 13.34 to 27.22 | 15.60 to 24.81 | 48 | 1.2255 |
| P1_cls_opt_mid | 5.49 | 1.34 to 9.64 | 4.22 to 7.01 | 2 | 1.0748 |
| P1_cls_opt_max | 5.49 | 1.34 to 9.64 | 4.22 to 7.01 | 2 | 1.0748 |
| P1_res_q | 8.66 | 3.37 to 13.95 | 5.66 to 11.91 | 17 | 1.1071 |
| P1_res_opt_mid | 7.80 | 3.53 to 12.07 | 6.75 to 9.20 | 1 | 1.0984 |
| P1_res_opt_max | 7.80 | 3.53 to 12.07 | 6.75 to 9.20 | 1 | 1.0984 |
| P3_res60 | 7.80 | 3.53 to 12.07 | 6.75 to 9.20 | 1 | 1.0984 |
| age_grid | 63.91 | 57.28 to 70.54 | 57.52 to 70.69 | 33 | 1.6700 |
| P3_res125 | 7.67 | 3.44 to 11.89 | 6.55 to 9.02 | 1 | 1.0970 |
| HI_cost | 9.56 | 5.26 to 13.86 | 7.86 to 11.66 | 4 | 1.1163 |
| STW_window_unmapped (unmapped) | 4.48 | 0.33 to 8.63 | 3.00 to 6.30 | 3 | 1.0645 |
| STW_cost_unmapped (unmapped) | 3.59 | -0.54 to 7.73 | 2.13 to 5.30 | 3 | 1.0555 |
| STW_cost_1se_unmapped (unmapped) | 5.86 | 1.79 to 9.94 | 4.78 to 7.18 | 1 | 1.0786 |
| run_to_failure | 95.50 | 88.28 to 102.71 | 95.15 to 95.82 | 249 | 1.9919 |
| perfect_grid | 0.00 | -3.78 to 3.78 | 0.00 to 0.00 | 0 | 1.0189 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -14.36 | -18.92 to -9.58 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | +0.43 | -0.55 to +1.12 | unclear |
| STW_window | P1_cls_opt_max | +0.43 | -0.55 to +1.12 | unclear |
| STW_window | P1_res_q | -2.74 | -5.96 to +0.24 | unclear |
| STW_window | P1_res_opt_mid | -1.88 | -2.23 to -1.56 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -1.88 | -2.23 to -1.56 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -1.88 | -2.23 to -1.56 | STW_window beats P3_res60 |
| STW_window | age_grid | -57.99 | -64.85 to -51.36 | STW_window beats age_grid |
| STW_window | P3_res125 | -1.75 | -2.07 to -1.41 | STW_window beats P3_res125 |
| STW_window | HI_cost | -3.64 | -5.60 to -2.01 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -15.37 | -19.79 to -10.54 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | -0.59 | -0.93 to -0.25 | STW_cost beats P1_cls_opt_mid |
| STW_cost | P1_cls_opt_max | -0.59 | -0.93 to -0.25 | STW_cost beats P1_cls_opt_max |
| STW_cost | P1_res_q | -3.76 | -6.88 to -0.90 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | -2.90 | -3.57 to -1.85 | STW_cost beats P1_res_opt_mid |
| STW_cost | P1_res_opt_max | -2.90 | -3.57 to -1.85 | STW_cost beats P1_res_opt_max |
| STW_cost | P3_res60 | -2.90 | -3.57 to -1.85 | STW_cost beats P3_res60 |
| STW_cost | age_grid | -59.01 | -65.74 to -52.44 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -2.76 | -3.43 to -1.71 | STW_cost beats P3_res125 |
| STW_cost | HI_cost | -4.65 | -6.77 to -2.70 | STW_cost beats HI_cost |
| STW_cost_1se | P1_cls_q | -13.29 | -17.83 to -8.47 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | +1.50 | +0.20 to +2.53 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +1.50 | +0.20 to +2.53 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | -1.67 | -4.98 to +1.48 | unclear |
| STW_cost_1se | P1_res_opt_mid | -0.81 | -1.80 to -0.17 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -0.81 | -1.80 to -0.17 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | -0.81 | -1.80 to -0.17 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -56.92 | -63.73 to -50.39 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -0.68 | -1.70 to +0.00 | unclear |
| STW_cost_1se | HI_cost | -2.57 | -4.45 to -1.11 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.8  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 4.24 | 0.26 to 8.22 | 3.22 to 5.48 | 14 | 1.0620 |
| STW_cost | 3.91 | -0.04 to 7.87 | 2.94 to 5.14 | 11 | 1.0588 |
| STW_cost_1se | 5.66 | 1.63 to 9.69 | 4.80 to 6.77 | 1 | 1.0765 |
| P1_cls_q | 9.54 | 5.19 to 13.88 | 8.17 to 10.98 | 100 | 1.1160 |
| P1_cls_opt_mid | 4.13 | 0.08 to 8.18 | 3.10 to 5.35 | 17 | 1.0609 |
| P1_cls_opt_max | 4.13 | 0.08 to 8.18 | 3.10 to 5.35 | 17 | 1.0609 |
| P1_res_q | 22.19 | 17.67 to 26.70 | 21.97 to 22.38 | 249 | 1.2449 |
| P1_res_opt_mid | 3.45 | -0.53 to 7.43 | 2.55 to 4.54 | 17 | 1.0540 |
| P1_res_opt_max | 3.45 | -0.53 to 7.43 | 2.55 to 4.54 | 17 | 1.0540 |
| P3_res60 | 7.48 | 3.28 to 11.67 | 6.61 to 8.59 | 1 | 1.0951 |
| age_grid | 22.63 | 18.23 to 27.03 | 21.82 to 23.63 | 234 | 1.2494 |
| P3_res125 | 7.34 | 3.20 to 11.49 | 6.47 to 8.51 | 1 | 1.0937 |
| HI_cost | 7.81 | 3.70 to 11.92 | 6.67 to 9.00 | 22 | 1.0984 |
| STW_window_unmapped (unmapped) | 3.55 | -0.36 to 7.46 | 2.69 to 4.62 | 3 | 1.0550 |
| STW_cost_unmapped (unmapped) | 3.05 | -0.85 to 6.94 | 2.04 to 4.25 | 14 | 1.0499 |
| STW_cost_1se_unmapped (unmapped) | 4.41 | 0.44 to 8.37 | 3.61 to 5.45 | 0 | 1.0638 |
| run_to_failure | 22.19 | 17.67 to 26.70 | 21.97 to 22.38 | 249 | 1.2449 |
| perfect_grid | 0.00 | -3.78 to 3.78 | 0.00 to 0.00 | 0 | 1.0189 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -5.30 | -6.72 to -3.92 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | +0.11 | -0.66 to +0.87 | unclear |
| STW_window | P1_cls_opt_max | +0.11 | -0.66 to +0.87 | unclear |
| STW_window | P1_res_q | -17.95 | -18.95 to -16.73 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | +0.78 | -0.11 to +1.75 | unclear |
| STW_window | P1_res_opt_max | +0.78 | -0.11 to +1.75 | unclear |
| STW_window | P3_res60 | -3.24 | -3.97 to -2.51 | STW_window beats P3_res60 |
| STW_window | age_grid | -18.39 | -19.75 to -17.03 | STW_window beats age_grid |
| STW_window | P3_res125 | -3.11 | -3.87 to -2.34 | STW_window beats P3_res125 |
| STW_window | HI_cost | -3.57 | -4.50 to -2.68 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -5.62 | -7.03 to -4.18 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | -0.22 | -0.91 to +0.45 | unclear |
| STW_cost | P1_cls_opt_max | -0.22 | -0.91 to +0.45 | unclear |
| STW_cost | P1_res_q | -18.27 | -19.25 to -17.07 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | +0.46 | -0.32 to +1.27 | unclear |
| STW_cost | P1_res_opt_max | +0.46 | -0.32 to +1.27 | unclear |
| STW_cost | P3_res60 | -3.56 | -4.26 to -2.79 | STW_cost beats P3_res60 |
| STW_cost | age_grid | -18.72 | -20.03 to -17.38 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -3.43 | -4.13 to -2.67 | STW_cost beats P3_res125 |
| STW_cost | HI_cost | -3.89 | -4.86 to -2.92 | STW_cost beats HI_cost |
| STW_cost_1se | P1_cls_q | -3.88 | -5.25 to -2.41 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | +1.53 | +0.71 to +2.34 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +1.53 | +0.71 to +2.34 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | -16.53 | -17.40 to -15.45 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | +2.21 | +1.25 to +3.20 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +2.21 | +1.25 to +3.20 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | -1.82 | -2.18 to -1.48 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -16.97 | -18.26 to -15.66 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -1.68 | -2.06 to -1.32 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -2.15 | -3.00 to -1.32 | STW_cost_1se beats HI_cost |

Grid-mapped policies with M < 0: 0. Recorded violations (all, incl. unmapped): 0.
