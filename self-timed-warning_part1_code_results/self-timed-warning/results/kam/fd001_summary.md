# FD001 under the conventions of Kamariotis et al. (Phase 2, exploratory; plan hashed before the run)

## c_p/c_c = 0.1  (primary)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures / 100 | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 8.08 | 3.08 to 13.09 | 7.21 to 8.97 | 0 | 1.1062 |
| STW_cost | 13.66 | -4.63 to 31.95 | 3.90 to 32.66 | 1 | 1.1633 |
| STW_cost_1se | 7.04 | 2.04 to 12.04 | 6.32 to 7.79 | 0 | 1.0956 |
| P1_cls_q | 11.22 | -7.95 to 30.39 | 1.71 to 29.77 | 1 | 1.1383 |
| P1_cls_opt_mid | 12.02 | -7.26 to 31.29 | 2.41 to 30.69 | 1 | 1.1465 |
| P1_cls_opt_max | 12.02 | -7.26 to 31.29 | 2.41 to 30.69 | 1 | 1.1465 |
| P1_res_q | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_mid | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_max | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P3_res60 | 10.34 | 4.90 to 15.79 | 9.46 to 11.29 | 0 | 1.1293 |
| age_grid | 79.25 | 50.40 to 108.11 | 59.21 to 112.79 | 1 | 1.8346 |
| P3_res125 | 9.98 | 4.77 to 15.19 | 9.15 to 10.80 | 0 | 1.1256 |
| HI_cost | 18.32 | -1.81 to 38.45 | 7.73 to 38.48 | 1 | 1.2110 |
| STW_window_unmapped (unmapped) | 3.93 | -0.87 to 8.74 | 3.45 to 4.41 | 0 | 1.0637 |
| STW_cost_unmapped (unmapped) | 11.55 | -6.43 to 29.53 | 2.12 to 30.05 | 1 | 1.1417 |
| STW_cost_1se_unmapped (unmapped) | 5.25 | 0.31 to 10.18 | 4.73 to 5.74 | 0 | 1.0772 |
| run_to_failure | 872.32 | 829.52 to 915.13 | 869.21 to 875.34 | 100 | 9.9515 |
| perfect_grid | 0.00 | -4.58 to 4.58 | 0.00 to 0.00 | 0 | 1.0235 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -3.14 | -21.96 to +6.74 | unclear |
| STW_window | P1_cls_opt_mid | -3.93 | -22.91 to +6.01 | unclear |
| STW_window | P1_cls_opt_max | -3.93 | -22.91 to +6.01 | unclear |
| STW_window | P1_res_q | +2.39 | +1.51 to +3.31 | P1_res_q beats STW_window |
| STW_window | P1_res_opt_mid | +2.39 | +1.51 to +3.31 | P1_res_opt_mid beats STW_window |
| STW_window | P1_res_opt_max | +2.39 | +1.51 to +3.31 | P1_res_opt_max beats STW_window |
| STW_window | P3_res60 | -2.26 | -3.18 to -1.42 | STW_window beats P3_res60 |
| STW_window | age_grid | -71.17 | -104.79 to -51.08 | STW_window beats age_grid |
| STW_window | P3_res125 | -1.90 | -2.60 to -1.21 | STW_window beats P3_res125 |
| STW_window | HI_cost | -10.24 | -30.61 to +0.60 | unclear |
| STW_cost | P1_cls_q | +2.45 | -24.97 to +30.18 | unclear |
| STW_cost | P1_cls_opt_mid | +1.65 | -25.93 to +29.43 | unclear |
| STW_cost | P1_cls_opt_max | +1.65 | -25.93 to +29.43 | unclear |
| STW_cost | P1_res_q | +7.97 | -1.87 to +27.02 | unclear |
| STW_cost | P1_res_opt_mid | +7.97 | -1.87 to +27.02 | unclear |
| STW_cost | P1_res_opt_max | +7.97 | -1.87 to +27.02 | unclear |
| STW_cost | P3_res60 | +3.32 | -6.68 to +22.50 | unclear |
| STW_cost | age_grid | -65.59 | -101.40 to -36.00 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +3.69 | -6.30 to +22.79 | unclear |
| STW_cost | HI_cost | -4.66 | -33.34 to +23.72 | unclear |
| STW_cost_1se | P1_cls_q | -4.17 | -22.87 to +5.61 | unclear |
| STW_cost_1se | P1_cls_opt_mid | -4.97 | -23.91 to +4.91 | unclear |
| STW_cost_1se | P1_cls_opt_max | -4.97 | -23.91 to +4.91 | unclear |
| STW_cost_1se | P1_res_q | +1.35 | +0.74 to +2.01 | P1_res_q beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_mid | +1.35 | +0.74 to +2.01 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +1.35 | +0.74 to +2.01 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | -3.30 | -4.07 to -2.56 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -72.21 | -105.86 to -51.95 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -2.93 | -3.62 to -2.24 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -11.28 | -31.76 to -0.42 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.01  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures / 100 | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 8.08 | 3.08 to 13.09 | 7.21 to 8.97 | 0 | 1.1062 |
| STW_cost | 107.51 | -93.46 to 308.49 | 3.90 to 314.68 | 1 | 2.1239 |
| STW_cost_1se | 7.04 | 2.04 to 12.04 | 6.32 to 7.79 | 0 | 1.0956 |
| P1_cls_q | 4.10 | -0.47 to 8.67 | 3.43 to 4.80 | 0 | 1.0654 |
| P1_cls_opt_mid | 104.51 | -96.04 to 305.05 | 2.41 to 308.52 | 1 | 2.0931 |
| P1_cls_opt_max | 104.51 | -96.04 to 305.05 | 2.41 to 308.52 | 1 | 2.0931 |
| P1_res_q | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_mid | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_max | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P3_res60 | 11.57 | 6.18 to 16.96 | 10.81 to 12.38 | 0 | 1.1419 |
| age_grid | 227.26 | -91.52 to 546.05 | 59.21 to 566.13 | 1 | 3.3495 |
| P3_res125 | 9.98 | 4.77 to 15.19 | 9.15 to 10.80 | 0 | 1.1256 |
| HI_cost | 116.01 | -95.59 to 327.61 | 7.73 to 332.88 | 1 | 2.2109 |
| STW_window_unmapped (unmapped) | 3.93 | -0.87 to 8.74 | 3.45 to 4.41 | 0 | 1.0637 |
| STW_cost_unmapped (unmapped) | 103.66 | -93.68 to 301.00 | 2.12 to 306.54 | 1 | 2.0844 |
| STW_cost_1se_unmapped (unmapped) | 5.25 | 0.31 to 10.18 | 4.73 to 5.74 | 0 | 1.0772 |
| run_to_failure | 9623.23 | 9195.16 to 10051.31 | 9592.12 to 9653.44 | 100 | 99.5153 |
| perfect_grid | 0.00 | -4.58 to 4.58 | 0.00 to 0.00 | 0 | 1.0235 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | +3.98 | +3.10 to +4.91 | P1_cls_q beats STW_window |
| STW_window | P1_cls_opt_mid | -96.42 | -300.68 to +6.01 | unclear |
| STW_window | P1_cls_opt_max | -96.42 | -300.68 to +6.01 | unclear |
| STW_window | P1_res_q | +2.39 | +1.51 to +3.31 | P1_res_q beats STW_window |
| STW_window | P1_res_opt_mid | +2.39 | +1.51 to +3.31 | P1_res_opt_mid beats STW_window |
| STW_window | P1_res_opt_max | +2.39 | +1.51 to +3.31 | P1_res_opt_max beats STW_window |
| STW_window | P3_res60 | -3.49 | -4.40 to -2.59 | STW_window beats P3_res60 |
| STW_window | age_grid | -219.18 | -557.76 to -51.08 | STW_window beats age_grid |
| STW_window | P3_res125 | -1.90 | -2.60 to -1.21 | STW_window beats P3_res125 |
| STW_window | HI_cost | -107.93 | -324.95 to +0.60 | unclear |
| STW_cost | P1_cls_q | +103.41 | -0.33 to +310.60 | unclear |
| STW_cost | P1_cls_opt_mid | +3.01 | -302.62 to +310.53 | unclear |
| STW_cost | P1_cls_opt_max | +3.01 | -302.62 to +310.53 | unclear |
| STW_cost | P1_res_q | +101.82 | -1.87 to +309.05 | unclear |
| STW_cost | P1_res_opt_mid | +101.82 | -1.87 to +309.05 | unclear |
| STW_cost | P1_res_opt_max | +101.82 | -1.87 to +309.05 | unclear |
| STW_cost | P3_res60 | +95.95 | -7.97 to +303.19 | unclear |
| STW_cost | age_grid | -119.75 | -539.12 to +243.85 | unclear |
| STW_cost | P3_res125 | +97.54 | -6.30 to +304.61 | unclear |
| STW_cost | HI_cost | -8.50 | -326.62 to +304.33 | unclear |
| STW_cost_1se | P1_cls_q | +2.94 | +2.19 to +3.75 | P1_cls_q beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_mid | -97.46 | -301.72 to +4.91 | unclear |
| STW_cost_1se | P1_cls_opt_max | -97.46 | -301.72 to +4.91 | unclear |
| STW_cost_1se | P1_res_q | +1.35 | +0.74 to +2.01 | P1_res_q beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_mid | +1.35 | +0.74 to +2.01 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +1.35 | +0.74 to +2.01 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | -4.52 | -5.39 to -3.71 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -220.22 | -558.90 to -51.95 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -2.93 | -3.62 to -2.24 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -108.97 | -326.00 to -0.42 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.02  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures / 100 | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 8.08 | 3.08 to 13.09 | 7.21 to 8.97 | 0 | 1.1062 |
| STW_cost | 55.37 | -43.84 to 154.59 | 3.90 to 158.00 | 1 | 1.5902 |
| STW_cost_1se | 7.04 | 2.04 to 12.04 | 6.32 to 7.79 | 0 | 1.0956 |
| P1_cls_q | 53.67 | -46.31 to 153.65 | 2.74 to 155.19 | 1 | 1.5728 |
| P1_cls_opt_mid | 53.12 | -46.50 to 152.74 | 2.41 to 154.17 | 1 | 1.5672 |
| P1_cls_opt_max | 53.12 | -46.50 to 152.74 | 2.41 to 154.17 | 1 | 1.5672 |
| P1_res_q | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_mid | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_max | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P3_res60 | 11.57 | 6.18 to 16.96 | 10.81 to 12.38 | 0 | 1.1419 |
| age_grid | 145.04 | -12.67 to 302.74 | 59.21 to 314.44 | 1 | 2.5079 |
| P3_res125 | 9.98 | 4.77 to 15.19 | 9.15 to 10.80 | 0 | 1.1256 |
| HI_cost | 61.74 | -43.30 to 166.78 | 7.73 to 169.32 | 1 | 1.6554 |
| STW_window_unmapped (unmapped) | 3.93 | -0.87 to 8.74 | 3.45 to 4.41 | 0 | 1.0637 |
| STW_cost_unmapped (unmapped) | 52.49 | -44.95 to 149.93 | 2.12 to 152.94 | 1 | 1.5607 |
| STW_cost_1se_unmapped (unmapped) | 5.25 | 0.31 to 10.18 | 4.73 to 5.74 | 0 | 1.0772 |
| run_to_failure | 4761.62 | 4547.58 to 4975.65 | 4746.06 to 4776.72 | 100 | 49.7576 |
| perfect_grid | 0.00 | -4.58 to 4.58 | 0.00 to 0.00 | 0 | 1.0235 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -45.59 | -147.31 to +5.62 | unclear |
| STW_window | P1_cls_opt_mid | -45.04 | -146.33 to +6.01 | unclear |
| STW_window | P1_cls_opt_max | -45.04 | -146.33 to +6.01 | unclear |
| STW_window | P1_res_q | +2.39 | +1.51 to +3.31 | P1_res_q beats STW_window |
| STW_window | P1_res_opt_mid | +2.39 | +1.51 to +3.31 | P1_res_opt_mid beats STW_window |
| STW_window | P1_res_opt_max | +2.39 | +1.51 to +3.31 | P1_res_opt_max beats STW_window |
| STW_window | P3_res60 | -3.49 | -4.40 to -2.59 | STW_window beats P3_res60 |
| STW_window | age_grid | -136.95 | -306.10 to -51.08 | STW_window beats age_grid |
| STW_window | P3_res125 | -1.90 | -2.60 to -1.21 | STW_window beats P3_res125 |
| STW_window | HI_cost | -53.66 | -161.41 to +0.60 | unclear |
| STW_cost | P1_cls_q | +1.70 | -149.88 to +153.91 | unclear |
| STW_cost | P1_cls_opt_mid | +2.25 | -148.87 to +154.32 | unclear |
| STW_cost | P1_cls_opt_max | +2.25 | -148.87 to +154.32 | unclear |
| STW_cost | P1_res_q | +49.68 | -1.87 to +152.37 | unclear |
| STW_cost | P1_res_opt_mid | +49.68 | -1.87 to +152.37 | unclear |
| STW_cost | P1_res_opt_max | +49.68 | -1.87 to +152.37 | unclear |
| STW_cost | P3_res60 | +43.81 | -7.97 to +146.54 | unclear |
| STW_cost | age_grid | -89.66 | -296.08 to +87.57 | unclear |
| STW_cost | P3_res125 | +45.40 | -6.30 to +147.97 | unclear |
| STW_cost | HI_cost | -6.36 | -163.73 to +148.45 | unclear |
| STW_cost_1se | P1_cls_q | -46.63 | -148.21 to +4.46 | unclear |
| STW_cost_1se | P1_cls_opt_mid | -46.08 | -147.31 to +4.91 | unclear |
| STW_cost_1se | P1_cls_opt_max | -46.08 | -147.31 to +4.91 | unclear |
| STW_cost_1se | P1_res_q | +1.35 | +0.74 to +2.01 | P1_res_q beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_mid | +1.35 | +0.74 to +2.01 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +1.35 | +0.74 to +2.01 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | -4.52 | -5.39 to -3.71 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -137.99 | -307.22 to -51.95 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -2.93 | -3.62 to -2.24 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -54.70 | -162.61 to -0.42 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.05  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures / 100 | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 8.08 | 3.08 to 13.09 | 7.21 to 8.97 | 0 | 1.1062 |
| STW_cost | 24.09 | -14.22 to 62.40 | 3.90 to 63.99 | 1 | 1.2700 |
| STW_cost_1se | 7.04 | 2.04 to 12.04 | 6.32 to 7.79 | 0 | 1.0956 |
| P1_cls_q | 21.92 | -17.18 to 61.01 | 2.12 to 61.09 | 1 | 1.2478 |
| P1_cls_opt_mid | 22.29 | -16.91 to 61.49 | 2.41 to 61.56 | 1 | 1.2516 |
| P1_cls_opt_max | 22.29 | -16.91 to 61.49 | 2.41 to 61.56 | 1 | 1.2516 |
| P1_res_q | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_mid | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_max | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P3_res60 | 11.57 | 6.18 to 16.96 | 10.81 to 12.38 | 0 | 1.1419 |
| age_grid | 95.70 | 34.64 to 156.76 | 59.21 to 163.43 | 1 | 2.0029 |
| P3_res125 | 9.98 | 4.77 to 15.19 | 9.15 to 10.80 | 0 | 1.1256 |
| HI_cost | 29.17 | -12.04 to 70.39 | 7.73 to 71.19 | 1 | 1.3221 |
| STW_window_unmapped (unmapped) | 3.93 | -0.87 to 8.74 | 3.45 to 4.41 | 0 | 1.0637 |
| STW_cost_unmapped (unmapped) | 21.79 | -15.86 to 59.43 | 2.12 to 60.77 | 1 | 1.2465 |
| STW_cost_1se_unmapped (unmapped) | 5.25 | 0.31 to 10.18 | 4.73 to 5.74 | 0 | 1.0772 |
| run_to_failure | 1844.65 | 1759.03 to 1930.26 | 1838.42 to 1850.69 | 100 | 19.9031 |
| perfect_grid | 0.00 | -4.58 to 4.58 | 0.00 to 0.00 | 0 | 1.0235 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -13.84 | -53.19 to +6.29 | unclear |
| STW_window | P1_cls_opt_mid | -14.21 | -53.76 to +6.01 | unclear |
| STW_window | P1_cls_opt_max | -14.21 | -53.76 to +6.01 | unclear |
| STW_window | P1_res_q | +2.39 | +1.51 to +3.31 | P1_res_q beats STW_window |
| STW_window | P1_res_opt_mid | +2.39 | +1.51 to +3.31 | P1_res_opt_mid beats STW_window |
| STW_window | P1_res_opt_max | +2.39 | +1.51 to +3.31 | P1_res_opt_max beats STW_window |
| STW_window | P3_res60 | -3.49 | -4.40 to -2.59 | STW_window beats P3_res60 |
| STW_window | age_grid | -87.62 | -155.30 to -51.08 | STW_window beats age_grid |
| STW_window | P3_res125 | -1.90 | -2.60 to -1.21 | STW_window beats P3_res125 |
| STW_window | HI_cost | -21.09 | -63.28 to +0.60 | unclear |
| STW_cost | P1_cls_q | +2.17 | -56.14 to +60.96 | unclear |
| STW_cost | P1_cls_opt_mid | +1.80 | -56.70 to +60.67 | unclear |
| STW_cost | P1_cls_opt_max | +1.80 | -56.70 to +60.67 | unclear |
| STW_cost | P1_res_q | +18.40 | -1.87 to +58.35 | unclear |
| STW_cost | P1_res_opt_mid | +18.40 | -1.87 to +58.35 | unclear |
| STW_cost | P1_res_opt_max | +18.40 | -1.87 to +58.35 | unclear |
| STW_cost | P3_res60 | +12.52 | -7.97 to +52.62 | unclear |
| STW_cost | age_grid | -71.61 | -150.18 to -6.22 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +14.11 | -6.30 to +54.08 | unclear |
| STW_cost | HI_cost | -5.08 | -65.90 to +54.93 | unclear |
| STW_cost_1se | P1_cls_q | -14.87 | -54.21 to +5.21 | unclear |
| STW_cost_1se | P1_cls_opt_mid | -15.25 | -54.77 to +4.91 | unclear |
| STW_cost_1se | P1_cls_opt_max | -15.25 | -54.77 to +4.91 | unclear |
| STW_cost_1se | P1_res_q | +1.35 | +0.74 to +2.01 | P1_res_q beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_mid | +1.35 | +0.74 to +2.01 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +1.35 | +0.74 to +2.01 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | -4.52 | -5.39 to -3.71 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -88.66 | -156.26 to -51.95 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -2.93 | -3.62 to -2.24 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -22.13 | -64.44 to -0.42 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.2  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures / 100 | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 6.93 | 1.95 to 11.91 | 6.13 to 7.77 | 0 | 1.0944 |
| STW_cost | 8.45 | -0.44 to 17.33 | 3.90 to 16.99 | 1 | 1.1100 |
| STW_cost_1se | 7.04 | 2.04 to 12.04 | 6.32 to 7.79 | 0 | 1.0956 |
| P1_cls_q | 9.42 | -2.85 to 21.69 | 1.21 to 21.56 | 2 | 1.1199 |
| P1_cls_opt_mid | 6.88 | -2.87 to 16.62 | 2.41 to 15.25 | 1 | 1.0939 |
| P1_cls_opt_max | 6.88 | -2.87 to 16.62 | 2.41 to 15.25 | 1 | 1.0939 |
| P1_res_q | 28.30 | 7.47 to 49.13 | 12.15 to 48.50 | 7 | 1.3131 |
| P1_res_opt_mid | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_max | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P3_res60 | 6.70 | 1.66 to 11.74 | 6.07 to 7.37 | 0 | 1.0921 |
| age_grid | 70.34 | 49.93 to 90.74 | 52.66 to 91.73 | 3 | 1.7433 |
| P3_res125 | 8.02 | 2.91 to 13.14 | 7.16 to 8.91 | 0 | 1.1056 |
| HI_cost | 12.89 | 2.93 to 22.86 | 7.73 to 22.12 | 1 | 1.1554 |
| STW_window_unmapped (unmapped) | 3.93 | -0.87 to 8.74 | 3.45 to 4.41 | 0 | 1.0637 |
| STW_cost_unmapped (unmapped) | 6.44 | -2.29 to 15.16 | 2.12 to 14.69 | 1 | 1.0893 |
| STW_cost_1se_unmapped (unmapped) | 5.25 | 0.31 to 10.18 | 4.73 to 5.74 | 0 | 1.0772 |
| run_to_failure | 386.16 | 364.76 to 407.57 | 384.61 to 387.67 | 100 | 4.9758 |
| perfect_grid | 0.00 | -4.58 to 4.58 | 0.00 to 0.00 | 0 | 1.0235 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -2.49 | -14.91 to +6.00 | unclear |
| STW_window | P1_cls_opt_mid | +0.05 | -8.67 to +4.78 | unclear |
| STW_window | P1_cls_opt_max | +0.05 | -8.67 to +4.78 | unclear |
| STW_window | P1_res_q | -21.37 | -41.94 to -4.66 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | +1.24 | +0.45 to +2.09 | P1_res_opt_mid beats STW_window |
| STW_window | P1_res_opt_max | +1.24 | +0.45 to +2.09 | P1_res_opt_max beats STW_window |
| STW_window | P3_res60 | +0.23 | -0.48 to +1.01 | unclear |
| STW_window | age_grid | -63.41 | -84.82 to -45.84 | STW_window beats age_grid |
| STW_window | P3_res125 | -1.09 | -2.02 to -0.18 | STW_window beats P3_res125 |
| STW_window | HI_cost | -5.96 | -15.46 to -0.52 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -0.97 | -16.64 to +11.54 | unclear |
| STW_cost | P1_cls_opt_mid | +1.57 | -10.54 to +13.81 | unclear |
| STW_cost | P1_cls_opt_max | +1.57 | -10.54 to +13.81 | unclear |
| STW_cost | P1_res_q | -19.85 | -39.83 to -3.81 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | +2.76 | -1.87 to +11.35 | unclear |
| STW_cost | P1_res_opt_max | +2.76 | -1.87 to +11.35 | unclear |
| STW_cost | P3_res60 | +1.75 | -2.86 to +10.31 | unclear |
| STW_cost | age_grid | -61.89 | -82.82 to -42.52 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +0.43 | -4.36 to +9.21 | unclear |
| STW_cost | HI_cost | -4.44 | -17.06 to +8.10 | unclear |
| STW_cost_1se | P1_cls_q | -2.37 | -14.63 to +6.07 | unclear |
| STW_cost_1se | P1_cls_opt_mid | +0.17 | -8.52 to +4.91 | unclear |
| STW_cost_1se | P1_cls_opt_max | +0.17 | -8.52 to +4.91 | unclear |
| STW_cost_1se | P1_res_q | -21.26 | -41.75 to -4.72 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | +1.35 | +0.74 to +2.01 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +1.35 | +0.74 to +2.01 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | +0.34 | -0.33 to +1.02 | unclear |
| STW_cost_1se | age_grid | -63.29 | -84.79 to -45.64 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -0.98 | -1.67 to -0.34 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -5.85 | -15.39 to -0.42 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.5  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures / 100 | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 4.94 | 0.10 to 9.78 | 3.45 to 7.19 | 1 | 1.0740 |
| STW_cost | 3.89 | -1.44 to 9.22 | 1.72 to 6.92 | 2 | 1.0633 |
| STW_cost_1se | 6.08 | 1.21 to 10.95 | 5.42 to 6.75 | 0 | 1.0857 |
| P1_cls_q | 12.03 | 4.27 to 19.80 | 6.26 to 18.37 | 12 | 1.1466 |
| P1_cls_opt_mid | 3.79 | -1.39 to 8.97 | 2.41 to 5.98 | 1 | 1.0623 |
| P1_cls_opt_max | 3.79 | -1.39 to 8.97 | 2.41 to 5.98 | 1 | 1.0623 |
| P1_res_q | 7.25 | 0.33 to 14.17 | 3.14 to 12.38 | 7 | 1.0977 |
| P1_res_opt_mid | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P1_res_opt_max | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| P3_res60 | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| age_grid | 48.69 | 39.83 to 57.56 | 40.40 to 56.76 | 12 | 1.5218 |
| P3_res125 | 5.91 | 1.02 to 10.81 | 5.30 to 6.53 | 0 | 1.0840 |
| HI_cost | 10.37 | 4.93 to 15.82 | 7.90 to 13.53 | 2 | 1.1297 |
| STW_window_unmapped (unmapped) | 3.12 | -1.65 to 7.88 | 2.68 to 3.54 | 0 | 1.0554 |
| STW_cost_unmapped (unmapped) | 2.16 | -2.61 to 6.92 | 0.89 to 4.29 | 1 | 1.0455 |
| STW_cost_1se_unmapped (unmapped) | 4.91 | 0.01 to 9.80 | 4.43 to 5.37 | 0 | 1.0737 |
| run_to_failure | 94.46 | 85.90 to 103.03 | 93.84 to 95.07 | 100 | 1.9903 |
| perfect_grid | 0.00 | -4.58 to 4.58 | 0.00 to 0.00 | 0 | 1.0235 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -7.09 | -13.40 to -1.21 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | +1.15 | -1.77 to +4.01 | unclear |
| STW_window | P1_cls_opt_max | +1.15 | -1.77 to +4.01 | unclear |
| STW_window | P1_res_q | -2.31 | -7.35 to +1.76 | unclear |
| STW_window | P1_res_opt_mid | -0.75 | -2.26 to +1.60 | unclear |
| STW_window | P1_res_opt_max | -0.75 | -2.26 to +1.60 | unclear |
| STW_window | P3_res60 | -0.75 | -2.26 to +1.60 | unclear |
| STW_window | age_grid | -43.75 | -51.73 to -35.44 | STW_window beats age_grid |
| STW_window | P3_res125 | -0.97 | -2.49 to +1.36 | unclear |
| STW_window | HI_cost | -5.44 | -9.06 to -1.75 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -8.14 | -14.16 to -2.69 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | +0.10 | -3.11 to +3.77 | unclear |
| STW_cost | P1_cls_opt_max | +0.10 | -3.11 to +3.77 | unclear |
| STW_cost | P1_res_q | -3.36 | -8.14 to +0.33 | unclear |
| STW_cost | P1_res_opt_mid | -1.80 | -4.05 to +1.29 | unclear |
| STW_cost | P1_res_opt_max | -1.80 | -4.05 to +1.29 | unclear |
| STW_cost | P3_res60 | -1.80 | -4.05 to +1.29 | unclear |
| STW_cost | age_grid | -44.80 | -53.29 to -35.94 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -2.02 | -4.33 to +1.16 | unclear |
| STW_cost | HI_cost | -6.48 | -10.65 to -2.18 | STW_cost beats HI_cost |
| STW_cost_1se | P1_cls_q | -5.95 | -12.30 to -0.04 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | +2.29 | -0.09 to +3.90 | unclear |
| STW_cost_1se | P1_cls_opt_max | +2.29 | -0.09 to +3.90 | unclear |
| STW_cost_1se | P1_res_q | -1.17 | -6.50 to +3.27 | unclear |
| STW_cost_1se | P1_res_opt_mid | +0.39 | -0.17 to +0.98 | unclear |
| STW_cost_1se | P1_res_opt_max | +0.39 | -0.17 to +0.98 | unclear |
| STW_cost_1se | P3_res60 | +0.39 | -0.17 to +0.98 | unclear |
| STW_cost_1se | age_grid | -42.61 | -50.79 to -34.16 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | +0.17 | -0.43 to +0.78 | unclear |
| STW_cost_1se | HI_cost | -4.29 | -7.67 to -1.71 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.8  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures / 100 | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 2.26 | -2.51 to 7.02 | 1.45 to 3.18 | 4 | 1.0466 |
| STW_cost | 1.79 | -2.91 to 6.49 | 1.10 to 2.62 | 3 | 1.0418 |
| STW_cost_1se | 4.76 | 0.05 to 9.46 | 4.04 to 5.40 | 1 | 1.0722 |
| P1_cls_q | 5.93 | 0.98 to 10.87 | 4.12 to 7.71 | 27 | 1.0841 |
| P1_cls_opt_mid | 2.18 | -2.50 to 6.86 | 1.53 to 2.91 | 2 | 1.0458 |
| P1_cls_opt_max | 2.18 | -2.50 to 6.86 | 1.53 to 2.91 | 2 | 1.0458 |
| P1_res_q | 1.99 | -2.79 to 6.76 | 1.02 to 3.12 | 7 | 1.0438 |
| P1_res_opt_mid | 1.99 | -2.79 to 6.76 | 1.02 to 3.12 | 7 | 1.0438 |
| P1_res_opt_max | 1.99 | -2.79 to 6.76 | 1.02 to 3.12 | 7 | 1.0438 |
| P3_res60 | 5.69 | 0.72 to 10.66 | 5.17 to 6.24 | 0 | 1.0817 |
| age_grid | 22.51 | 17.69 to 27.34 | 19.87 to 25.15 | 72 | 1.2539 |
| P3_res125 | 5.91 | 1.02 to 10.81 | 5.30 to 6.53 | 0 | 1.0840 |
| HI_cost | 7.38 | 2.73 to 12.03 | 5.94 to 8.76 | 10 | 1.0990 |
| STW_window_unmapped (unmapped) | 2.88 | -1.86 to 7.63 | 2.51 to 3.26 | 0 | 1.0530 |
| STW_cost_unmapped (unmapped) | 1.00 | -3.55 to 5.54 | 0.36 to 1.74 | 2 | 1.0337 |
| STW_cost_1se_unmapped (unmapped) | 3.42 | -1.39 to 8.23 | 2.97 to 3.85 | 0 | 1.0585 |
| run_to_failure | 21.54 | 16.19 to 26.89 | 21.15 to 21.92 | 100 | 1.2439 |
| perfect_grid | 0.00 | -4.58 to 4.58 | 0.00 to 0.00 | 0 | 1.0235 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -3.67 | -5.54 to -1.86 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | +0.08 | -0.85 to +1.01 | unclear |
| STW_window | P1_cls_opt_max | +0.08 | -0.85 to +1.01 | unclear |
| STW_window | P1_res_q | +0.27 | -0.82 to +1.16 | unclear |
| STW_window | P1_res_opt_mid | +0.27 | -0.82 to +1.16 | unclear |
| STW_window | P1_res_opt_max | +0.27 | -0.82 to +1.16 | unclear |
| STW_window | P3_res60 | -3.43 | -4.40 to -2.38 | STW_window beats P3_res60 |
| STW_window | age_grid | -20.25 | -22.99 to -17.55 | STW_window beats age_grid |
| STW_window | P3_res125 | -3.65 | -4.66 to -2.56 | STW_window beats P3_res125 |
| STW_window | HI_cost | -5.12 | -6.50 to -3.68 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -4.14 | -6.08 to -2.26 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | -0.39 | -1.21 to +0.46 | unclear |
| STW_cost | P1_cls_opt_max | -0.39 | -1.21 to +0.46 | unclear |
| STW_cost | P1_res_q | -0.20 | -1.16 to +0.57 | unclear |
| STW_cost | P1_res_opt_mid | -0.20 | -1.16 to +0.57 | unclear |
| STW_cost | P1_res_opt_max | -0.20 | -1.16 to +0.57 | unclear |
| STW_cost | P3_res60 | -3.90 | -4.76 to -2.89 | STW_cost beats P3_res60 |
| STW_cost | age_grid | -20.72 | -23.42 to -17.98 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -4.12 | -5.07 to -3.07 | STW_cost beats P3_res125 |
| STW_cost | HI_cost | -5.59 | -6.96 to -4.15 | STW_cost beats HI_cost |
| STW_cost_1se | P1_cls_q | -1.17 | -3.29 to +0.92 | unclear |
| STW_cost_1se | P1_cls_opt_mid | +2.58 | +1.65 to +3.47 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +2.58 | +1.65 to +3.47 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | +2.77 | +1.39 to +3.89 | P1_res_q beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_mid | +2.77 | +1.39 to +3.89 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +2.77 | +1.39 to +3.89 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | -0.93 | -1.67 to -0.20 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -17.76 | -20.40 to -15.07 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -1.16 | -1.88 to -0.43 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -2.62 | -4.17 to -1.12 | STW_cost_1se beats HI_cost |

Grid-mapped policies with M < 0: 0. Recorded violations (all, incl. unmapped): 1.
