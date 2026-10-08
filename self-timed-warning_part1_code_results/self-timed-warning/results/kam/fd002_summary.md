# FD002 under the conventions of Kamariotis et al. (exploratory; plan hashed before the run)

## c_p/c_c = 0.1  (primary)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 4.85 | 1.86 to 7.84 | 4.48 to 5.20 | 0 | 1.0723 |
| STW_cost | 17.21 | 3.08 to 31.34 | 6.32 to 31.40 | 4 | 1.1987 |
| STW_cost_1se | 4.91 | 1.95 to 7.88 | 4.55 to 5.27 | 0 | 1.0730 |
| P1_cls_q | 16.42 | 2.13 to 30.71 | 5.69 to 30.76 | 4 | 1.1907 |
| P1_cls_opt_mid | 7.11 | -0.35 to 14.56 | 3.29 to 14.31 | 1 | 1.0954 |
| P1_cls_opt_max | 7.11 | -0.35 to 14.56 | 3.29 to 14.31 | 1 | 1.0954 |
| P1_res_q | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_mid | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_max | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P3_res60 | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| age_grid | 73.50 | 58.01 to 88.99 | 60.45 to 90.81 | 2 | 1.7744 |
| P3_res125 | 8.08 | 4.95 to 11.21 | 7.55 to 8.63 | 0 | 1.1054 |
| HI_cost | 14.69 | 6.40 to 22.98 | 10.29 to 22.71 | 1 | 1.1730 |
| STW_window_unmapped (unmapped) | 3.78 | 0.79 to 6.78 | 3.49 to 4.08 | 0 | 1.0614 |
| STW_cost_unmapped (unmapped) | 5.31 | -1.81 to 12.43 | 1.61 to 12.61 | 1 | 1.0770 |
| STW_cost_1se_unmapped (unmapped) | 3.48 | 0.50 to 6.46 | 3.21 to 3.76 | 0 | 1.0583 |
| run_to_failure | 873.05 | 846.29 to 899.81 | 871.27 to 874.84 | 260 | 9.9516 |
| perfect_grid | 0.00 | -2.83 to 2.83 | 0.00 to 0.00 | 0 | 1.0227 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -11.57 | -25.96 to -0.72 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | -2.26 | -9.56 to +1.61 | unclear |
| STW_window | P1_cls_opt_max | -2.26 | -9.56 to +1.61 | unclear |
| STW_window | P1_res_q | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -0.80 | -1.13 to -0.50 | STW_window beats P3_res60 |
| STW_window | age_grid | -68.65 | -85.91 to -55.59 | STW_window beats age_grid |
| STW_window | P3_res125 | -3.23 | -3.72 to -2.76 | STW_window beats P3_res125 |
| STW_window | HI_cost | -9.84 | -17.93 to -5.44 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | +0.78 | -16.79 to +18.38 | unclear |
| STW_cost | P1_cls_opt_mid | +10.10 | -0.56 to +24.02 | unclear |
| STW_cost | P1_cls_opt_max | +10.10 | -0.56 to +24.02 | unclear |
| STW_cost | P1_res_q | +11.55 | +0.63 to +25.83 | P1_res_q beats STW_cost |
| STW_cost | P1_res_opt_mid | +11.55 | +0.63 to +25.83 | P1_res_opt_mid beats STW_cost |
| STW_cost | P1_res_opt_max | +11.55 | +0.63 to +25.83 | P1_res_opt_max beats STW_cost |
| STW_cost | P3_res60 | +11.55 | +0.63 to +25.83 | P3_res60 beats STW_cost |
| STW_cost | age_grid | -56.29 | -77.71 to -37.39 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +9.13 | -1.96 to +23.39 | unclear |
| STW_cost | HI_cost | +2.52 | -12.18 to +17.50 | unclear |
| STW_cost_1se | P1_cls_q | -11.51 | -25.90 to -0.66 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | -2.19 | -9.46 to +1.66 | unclear |
| STW_cost_1se | P1_cls_opt_max | -2.19 | -9.46 to +1.66 | unclear |
| STW_cost_1se | P1_res_q | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -68.59 | -85.91 to -55.45 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -3.16 | -3.63 to -2.72 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -9.78 | -17.95 to -5.37 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.01  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 4.85 | 1.86 to 7.84 | 4.48 to 5.20 | 0 | 1.0723 |
| STW_cost | 159.76 | 7.15 to 312.36 | 41.89 to 316.36 | 4 | 2.6566 |
| STW_cost_1se | 4.91 | 1.95 to 7.88 | 4.55 to 5.27 | 0 | 1.0730 |
| P1_cls_q | 3.85 | 0.95 to 6.75 | 3.47 to 4.22 | 0 | 1.0621 |
| P1_cls_opt_mid | 42.94 | -34.17 to 120.06 | 3.29 to 121.86 | 1 | 1.4619 |
| P1_cls_opt_max | 42.94 | -34.17 to 120.06 | 3.29 to 121.86 | 1 | 1.4619 |
| P1_res_q | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_mid | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_max | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P3_res60 | 9.07 | 5.85 to 12.29 | 8.50 to 9.64 | 0 | 1.1155 |
| age_grid | 67.66 | 67.66 to 67.66 | 63.17 to 72.28 | 0 | 1.7147 |
| P3_res125 | 10.52 | 7.25 to 13.80 | 9.99 to 11.08 | 0 | 1.1303 |
| HI_cost | 53.06 | -30.09 to 136.21 | 10.29 to 138.15 | 1 | 1.5654 |
| STW_window_unmapped (unmapped) | 3.78 | 0.79 to 6.78 | 3.49 to 4.08 | 0 | 1.0614 |
| STW_cost_unmapped (unmapped) | 40.54 | -34.94 to 116.03 | 1.61 to 118.55 | 1 | 1.4374 |
| STW_cost_1se_unmapped (unmapped) | 3.48 | 0.50 to 6.46 | 3.21 to 3.76 | 0 | 1.0583 |
| run_to_failure | 9630.46 | 9362.86 to 9898.07 | 9612.72 to 9648.35 | 260 | 99.5164 |
| perfect_grid | 0.00 | -2.83 to 2.83 | 0.00 to 0.00 | 0 | 1.0227 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | +1.00 | +0.62 to +1.36 | P1_cls_q beats STW_window |
| STW_window | P1_cls_opt_mid | -38.09 | -117.03 to +1.61 | unclear |
| STW_window | P1_cls_opt_max | -38.09 | -117.03 to +1.61 | unclear |
| STW_window | P1_res_q | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -4.22 | -4.73 to -3.69 | STW_window beats P3_res60 |
| STW_window | age_grid | -62.81 | -67.48 to -58.29 | STW_window beats age_grid |
| STW_window | P3_res125 | -5.67 | -6.22 to -5.17 | STW_window beats P3_res125 |
| STW_window | HI_cost | -48.21 | -133.48 to -5.44 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | +155.90 | +38.12 to +312.65 | P1_cls_q beats STW_cost |
| STW_cost | P1_cls_opt_mid | +116.81 | -0.66 to +272.48 | unclear |
| STW_cost | P1_cls_opt_max | +116.81 | -0.66 to +272.48 | unclear |
| STW_cost | P1_res_q | +154.10 | +36.24 to +310.71 | P1_res_q beats STW_cost |
| STW_cost | P1_res_opt_mid | +154.10 | +36.24 to +310.71 | P1_res_opt_mid beats STW_cost |
| STW_cost | P1_res_opt_max | +154.10 | +36.24 to +310.71 | P1_res_opt_max beats STW_cost |
| STW_cost | P3_res60 | +150.69 | +32.64 to +307.46 | P3_res60 beats STW_cost |
| STW_cost | age_grid | +92.10 | -28.29 to +248.98 | unclear |
| STW_cost | P3_res125 | +149.23 | +31.19 to +305.90 | P3_res125 beats STW_cost |
| STW_cost | HI_cost | +106.70 | -53.69 to +267.28 | unclear |
| STW_cost_1se | P1_cls_q | +1.06 | +0.71 to +1.40 | P1_cls_q beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_mid | -38.03 | -116.97 to +1.66 | unclear |
| STW_cost_1se | P1_cls_opt_max | -38.03 | -116.97 to +1.66 | unclear |
| STW_cost_1se | P1_res_q | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | -4.16 | -4.68 to -3.64 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -62.75 | -67.36 to -58.27 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -5.61 | -6.13 to -5.14 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -48.15 | -133.42 to -5.37 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.02  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 4.85 | 1.86 to 7.84 | 4.48 to 5.20 | 0 | 1.0723 |
| STW_cost | 80.56 | 5.01 to 156.11 | 22.13 to 158.05 | 4 | 1.8467 |
| STW_cost_1se | 4.91 | 1.95 to 7.88 | 4.55 to 5.27 | 0 | 1.0730 |
| P1_cls_q | 3.56 | 0.69 to 6.44 | 3.18 to 3.94 | 0 | 1.0592 |
| P1_cls_opt_mid | 23.04 | -15.14 to 61.21 | 3.29 to 62.11 | 1 | 1.2583 |
| P1_cls_opt_max | 23.04 | -15.14 to 61.21 | 3.29 to 62.11 | 1 | 1.2583 |
| P1_res_q | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_mid | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_max | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P3_res60 | 9.07 | 5.85 to 12.29 | 8.50 to 9.64 | 0 | 1.1155 |
| age_grid | 67.66 | 67.66 to 67.66 | 63.17 to 72.28 | 0 | 1.7147 |
| P3_res125 | 10.52 | 7.25 to 13.80 | 9.99 to 11.08 | 0 | 1.1303 |
| HI_cost | 31.74 | -9.62 to 73.11 | 10.29 to 74.01 | 1 | 1.3474 |
| STW_window_unmapped (unmapped) | 3.78 | 0.79 to 6.78 | 3.49 to 4.08 | 0 | 1.0614 |
| STW_cost_unmapped (unmapped) | 20.97 | -16.28 to 58.22 | 1.61 to 59.70 | 1 | 1.2372 |
| STW_cost_1se_unmapped (unmapped) | 3.48 | 0.50 to 6.46 | 3.21 to 3.76 | 0 | 1.0583 |
| run_to_failure | 4765.23 | 4631.43 to 4899.04 | 4756.36 to 4774.18 | 260 | 49.7582 |
| perfect_grid | 0.00 | -2.83 to 2.83 | 0.00 to 0.00 | 0 | 1.0227 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | +1.29 | +0.91 to +1.66 | P1_cls_q beats STW_window |
| STW_window | P1_cls_opt_mid | -18.18 | -57.33 to +1.61 | unclear |
| STW_window | P1_cls_opt_max | -18.18 | -57.33 to +1.61 | unclear |
| STW_window | P1_res_q | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -4.22 | -4.73 to -3.69 | STW_window beats P3_res60 |
| STW_window | age_grid | -62.81 | -67.48 to -58.29 | STW_window beats age_grid |
| STW_window | P3_res125 | -5.67 | -6.22 to -5.17 | STW_window beats P3_res125 |
| STW_window | HI_cost | -26.89 | -69.26 to -5.44 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | +77.00 | +18.61 to +154.60 | P1_cls_q beats STW_cost |
| STW_cost | P1_cls_opt_mid | +57.53 | -0.62 to +134.50 | unclear |
| STW_cost | P1_cls_opt_max | +57.53 | -0.62 to +134.50 | unclear |
| STW_cost | P1_res_q | +74.91 | +16.46 to +152.45 | P1_res_q beats STW_cost |
| STW_cost | P1_res_opt_mid | +74.91 | +16.46 to +152.45 | P1_res_opt_mid beats STW_cost |
| STW_cost | P1_res_opt_max | +74.91 | +16.46 to +152.45 | P1_res_opt_max beats STW_cost |
| STW_cost | P3_res60 | +71.49 | +12.88 to +149.09 | P3_res60 beats STW_cost |
| STW_cost | age_grid | +12.90 | -48.07 to +90.87 | unclear |
| STW_cost | P3_res125 | +70.04 | +11.42 to +147.69 | P3_res125 beats STW_cost |
| STW_cost | HI_cost | +48.82 | -30.51 to +128.49 | unclear |
| STW_cost_1se | P1_cls_q | +1.35 | +1.00 to +1.68 | P1_cls_q beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_mid | -18.12 | -57.23 to +1.66 | unclear |
| STW_cost_1se | P1_cls_opt_max | -18.12 | -57.23 to +1.66 | unclear |
| STW_cost_1se | P1_res_q | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | -4.16 | -4.68 to -3.64 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -62.75 | -67.36 to -58.27 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -5.61 | -6.13 to -5.14 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -26.83 | -69.28 to -5.37 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.05  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 4.85 | 1.86 to 7.84 | 4.48 to 5.20 | 0 | 1.0723 |
| STW_cost | 33.05 | 3.66 to 62.43 | 10.27 to 63.06 | 4 | 1.3607 |
| STW_cost_1se | 4.91 | 1.95 to 7.88 | 4.55 to 5.27 | 0 | 1.0730 |
| P1_cls_q | 10.07 | -4.76 to 24.89 | 2.34 to 25.09 | 1 | 1.1257 |
| P1_cls_opt_mid | 11.09 | -3.87 to 26.05 | 3.29 to 26.26 | 1 | 1.1362 |
| P1_cls_opt_max | 11.09 | -3.87 to 26.05 | 3.29 to 26.26 | 1 | 1.1362 |
| P1_res_q | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_mid | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_max | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P3_res60 | 9.07 | 5.85 to 12.29 | 8.50 to 9.64 | 0 | 1.1155 |
| age_grid | 67.66 | 67.66 to 67.66 | 63.17 to 72.28 | 0 | 1.7147 |
| P3_res125 | 10.52 | 7.25 to 13.80 | 9.99 to 11.08 | 0 | 1.1303 |
| HI_cost | 18.95 | 2.54 to 35.37 | 10.29 to 35.53 | 1 | 1.2166 |
| STW_window_unmapped (unmapped) | 3.78 | 0.79 to 6.78 | 3.49 to 4.08 | 0 | 1.0614 |
| STW_cost_unmapped (unmapped) | 9.22 | -5.23 to 23.68 | 1.61 to 24.38 | 1 | 1.1171 |
| STW_cost_1se_unmapped (unmapped) | 3.48 | 0.50 to 6.46 | 3.21 to 3.76 | 0 | 1.0583 |
| run_to_failure | 1846.09 | 1792.57 to 1899.61 | 1842.54 to 1849.67 | 260 | 19.9033 |
| perfect_grid | 0.00 | -2.83 to 2.83 | 0.00 to 0.00 | 0 | 1.0227 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -5.22 | -20.30 to +2.55 | unclear |
| STW_window | P1_cls_opt_mid | -6.24 | -21.51 to +1.61 | unclear |
| STW_window | P1_cls_opt_max | -6.24 | -21.51 to +1.61 | unclear |
| STW_window | P1_res_q | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -0.80 | -1.13 to -0.50 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -4.22 | -4.73 to -3.69 | STW_window beats P3_res60 |
| STW_window | age_grid | -62.81 | -67.48 to -58.29 | STW_window beats age_grid |
| STW_window | P3_res125 | -5.67 | -6.22 to -5.17 | STW_window beats P3_res125 |
| STW_window | HI_cost | -14.10 | -30.76 to -5.44 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | +22.98 | +0.43 to +52.65 | P1_cls_q beats STW_cost |
| STW_cost | P1_cls_opt_mid | +21.96 | -0.58 to +51.64 | unclear |
| STW_cost | P1_cls_opt_max | +21.96 | -0.58 to +51.64 | unclear |
| STW_cost | P1_res_q | +27.39 | +4.59 to +57.48 | P1_res_q beats STW_cost |
| STW_cost | P1_res_opt_mid | +27.39 | +4.59 to +57.48 | P1_res_opt_mid beats STW_cost |
| STW_cost | P1_res_opt_max | +27.39 | +4.59 to +57.48 | P1_res_opt_max beats STW_cost |
| STW_cost | P3_res60 | +23.98 | +1.01 to +54.10 | P3_res60 beats STW_cost |
| STW_cost | age_grid | -34.61 | -59.98 to -4.05 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +22.52 | -0.44 to +52.60 | unclear |
| STW_cost | HI_cost | +14.09 | -16.75 to +45.21 | unclear |
| STW_cost_1se | P1_cls_q | -5.15 | -20.25 to +2.62 | unclear |
| STW_cost_1se | P1_cls_opt_mid | -6.18 | -21.40 to +1.66 | unclear |
| STW_cost_1se | P1_cls_opt_max | -6.18 | -21.40 to +1.66 | unclear |
| STW_cost_1se | P1_res_q | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | -4.16 | -4.68 to -3.64 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -62.75 | -67.36 to -58.27 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -5.61 | -6.13 to -5.14 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -14.04 | -30.78 to -5.37 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.2  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 8.96 | 2.77 to 15.15 | 4.27 to 15.04 | 3 | 1.1143 |
| STW_cost | 9.29 | 2.51 to 16.07 | 4.34 to 15.57 | 4 | 1.1177 |
| STW_cost_1se | 4.91 | 1.95 to 7.88 | 4.55 to 5.27 | 0 | 1.0730 |
| P1_cls_q | 16.91 | 6.75 to 27.07 | 7.68 to 26.14 | 10 | 1.1957 |
| P1_cls_opt_mid | 4.64 | 0.52 to 8.76 | 2.83 to 7.85 | 1 | 1.0702 |
| P1_cls_opt_max | 4.64 | 0.52 to 8.76 | 2.83 to 7.85 | 1 | 1.0702 |
| P1_res_q | 46.40 | 30.28 to 62.52 | 31.23 to 61.53 | 30 | 1.4973 |
| P1_res_opt_mid | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_max | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P3_res60 | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| age_grid | 57.14 | 46.49 to 67.80 | 47.35 to 68.62 | 6 | 1.6071 |
| P3_res125 | 5.87 | 2.84 to 8.89 | 5.48 to 6.24 | 0 | 1.0828 |
| HI_cost | 13.76 | 8.00 to 19.52 | 10.12 to 19.00 | 2 | 1.1635 |
| STW_window_unmapped (unmapped) | 2.71 | -0.23 to 5.64 | 2.43 to 3.00 | 0 | 1.0504 |
| STW_cost_unmapped (unmapped) | 3.35 | -0.58 to 7.28 | 1.61 to 6.73 | 1 | 1.0570 |
| STW_cost_1se_unmapped (unmapped) | 3.48 | 0.50 to 6.46 | 3.21 to 3.76 | 0 | 1.0583 |
| run_to_failure | 386.52 | 373.14 to 399.90 | 385.64 to 387.42 | 260 | 4.9758 |
| perfect_grid | 0.00 | -2.83 to 2.83 | 0.00 to 0.00 | 0 | 1.0227 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -7.95 | -16.99 to +0.02 | unclear |
| STW_window | P1_cls_opt_mid | +4.32 | -1.78 to +10.65 | unclear |
| STW_window | P1_cls_opt_max | +4.32 | -1.78 to +10.65 | unclear |
| STW_window | P1_res_q | -37.44 | -52.49 to -22.42 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | +3.30 | -1.45 to +9.45 | unclear |
| STW_window | P1_res_opt_max | +3.30 | -1.45 to +9.45 | unclear |
| STW_window | P3_res60 | +3.30 | -1.45 to +9.45 | unclear |
| STW_window | age_grid | -48.19 | -61.25 to -36.23 | STW_window beats age_grid |
| STW_window | P3_res125 | +3.09 | -1.65 to +9.18 | unclear |
| STW_window | HI_cost | -4.81 | -10.06 to +1.19 | unclear |
| STW_cost | P1_cls_q | -7.62 | -16.97 to +1.80 | unclear |
| STW_cost | P1_cls_opt_mid | +4.65 | -0.10 to +10.74 | unclear |
| STW_cost | P1_cls_opt_max | +4.65 | -0.10 to +10.74 | unclear |
| STW_cost | P1_res_q | -37.11 | -52.19 to -21.91 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | +3.63 | -1.35 to +9.99 | unclear |
| STW_cost | P1_res_opt_max | +3.63 | -1.35 to +9.99 | unclear |
| STW_cost | P3_res60 | +3.63 | -1.35 to +9.99 | unclear |
| STW_cost | age_grid | -47.85 | -61.12 to -36.41 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +3.42 | -1.59 to +9.78 | unclear |
| STW_cost | HI_cost | -4.47 | -11.83 to +3.51 | unclear |
| STW_cost_1se | P1_cls_q | -12.00 | -21.28 to -2.72 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | +0.27 | -3.01 to +2.11 | unclear |
| STW_cost_1se | P1_cls_opt_max | +0.27 | -3.01 to +2.11 | unclear |
| STW_cost_1se | P1_res_q | -41.49 | -56.78 to -26.08 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_mid |
| STW_cost_1se | P1_res_opt_max | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P1_res_opt_max |
| STW_cost_1se | P3_res60 | -0.74 | -1.06 to -0.43 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -52.23 | -63.70 to -42.31 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -0.96 | -1.26 to -0.67 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -8.85 | -14.27 to -5.18 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.5  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 4.94 | 1.59 to 8.29 | 3.60 to 6.56 | 4 | 1.0733 |
| STW_cost | 3.81 | 0.63 to 6.99 | 2.52 to 5.42 | 4 | 1.0617 |
| STW_cost_1se | 5.01 | 1.91 to 8.12 | 4.34 to 5.94 | 1 | 1.0740 |
| P1_cls_q | 14.42 | 9.07 to 19.77 | 10.51 to 18.50 | 37 | 1.1702 |
| P1_cls_opt_mid | 3.25 | 0.31 to 6.18 | 2.63 to 4.07 | 1 | 1.0560 |
| P1_cls_opt_max | 3.25 | 0.31 to 6.18 | 2.63 to 4.07 | 1 | 1.0560 |
| P1_res_q | 11.73 | 6.73 to 16.72 | 8.07 to 15.38 | 30 | 1.1427 |
| P1_res_opt_mid | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P1_res_opt_max | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| P3_res60 | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| age_grid | 46.82 | 41.64 to 52.01 | 41.96 to 51.80 | 27 | 1.5016 |
| P3_res125 | 5.87 | 2.84 to 8.89 | 5.48 to 6.24 | 0 | 1.0828 |
| HI_cost | 10.55 | 7.00 to 14.09 | 8.66 to 12.64 | 7 | 1.1306 |
| STW_window_unmapped (unmapped) | 2.71 | -0.23 to 5.64 | 2.43 to 3.00 | 0 | 1.0504 |
| STW_cost_unmapped (unmapped) | 1.92 | -1.02 to 4.85 | 1.06 to 3.09 | 2 | 1.0423 |
| STW_cost_1se_unmapped (unmapped) | 3.21 | 0.26 to 6.17 | 2.95 to 3.49 | 0 | 1.0556 |
| run_to_failure | 94.61 | 89.26 to 99.96 | 94.25 to 94.97 | 260 | 1.9903 |
| perfect_grid | 0.00 | -2.83 to 2.83 | 0.00 to 0.00 | 0 | 1.0227 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -9.48 | -13.50 to -5.40 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | +1.69 | +0.09 to +3.46 | P1_cls_opt_mid beats STW_window |
| STW_window | P1_cls_opt_max | +1.69 | +0.09 to +3.46 | P1_cls_opt_max beats STW_window |
| STW_window | P1_res_q | -6.79 | -10.28 to -3.18 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -0.71 | -2.12 to +0.93 | unclear |
| STW_window | P1_res_opt_max | -0.71 | -2.12 to +0.93 | unclear |
| STW_window | P3_res60 | -0.71 | -2.12 to +0.93 | unclear |
| STW_window | age_grid | -41.88 | -47.10 to -36.84 | STW_window beats age_grid |
| STW_window | P3_res125 | -0.93 | -2.33 to +0.74 | unclear |
| STW_window | HI_cost | -5.60 | -7.78 to -3.49 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -10.61 | -14.55 to -6.69 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | +0.56 | -0.60 to +2.15 | unclear |
| STW_cost | P1_cls_opt_max | +0.56 | -0.60 to +2.15 | unclear |
| STW_cost | P1_res_q | -7.92 | -11.43 to -4.31 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | -1.84 | -3.25 to -0.12 | STW_cost beats P1_res_opt_mid |
| STW_cost | P1_res_opt_max | -1.84 | -3.25 to -0.12 | STW_cost beats P1_res_opt_max |
| STW_cost | P3_res60 | -1.84 | -3.25 to -0.12 | STW_cost beats P3_res60 |
| STW_cost | age_grid | -43.01 | -48.29 to -37.98 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -2.06 | -3.39 to -0.38 | STW_cost beats P3_res125 |
| STW_cost | HI_cost | -6.73 | -9.10 to -4.36 | STW_cost beats HI_cost |
| STW_cost_1se | P1_cls_q | -9.41 | -13.74 to -5.23 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | +1.77 | +0.69 to +2.92 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +1.77 | +0.69 to +2.92 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | -6.71 | -10.69 to -2.82 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | -0.64 | -1.26 to +0.27 | unclear |
| STW_cost_1se | P1_res_opt_max | -0.64 | -1.26 to +0.27 | unclear |
| STW_cost_1se | P3_res60 | -0.64 | -1.26 to +0.27 | unclear |
| STW_cost_1se | age_grid | -41.81 | -46.96 to -36.75 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -0.86 | -1.50 to +0.12 | unclear |
| STW_cost_1se | HI_cost | -5.53 | -7.88 to -3.41 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.8  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 2.31 | -0.62 to 5.24 | 1.89 to 2.80 | 5 | 1.0464 |
| STW_cost | 1.86 | -1.01 to 4.72 | 1.45 to 2.31 | 5 | 1.0417 |
| STW_cost_1se | 3.67 | 0.67 to 6.66 | 3.27 to 4.09 | 2 | 1.0602 |
| P1_cls_q | 6.48 | 3.35 to 9.62 | 5.36 to 7.61 | 78 | 1.0890 |
| P1_cls_opt_mid | 2.41 | -0.52 to 5.33 | 1.84 to 2.98 | 11 | 1.0473 |
| P1_cls_opt_max | 2.41 | -0.52 to 5.33 | 1.84 to 2.98 | 11 | 1.0473 |
| P1_res_q | 3.06 | 0.02 to 6.09 | 2.26 to 3.85 | 30 | 1.0540 |
| P1_res_opt_mid | 3.06 | 0.02 to 6.09 | 2.26 to 3.85 | 30 | 1.0540 |
| P1_res_opt_max | 3.06 | 0.02 to 6.09 | 2.26 to 3.85 | 30 | 1.0540 |
| P3_res60 | 5.66 | 2.57 to 8.74 | 5.29 to 6.03 | 0 | 1.0806 |
| age_grid | 21.54 | 18.17 to 24.91 | 20.90 to 22.22 | 239 | 1.2431 |
| P3_res125 | 5.87 | 2.84 to 8.89 | 5.48 to 6.24 | 0 | 1.0828 |
| HI_cost | 7.14 | 4.20 to 10.09 | 6.33 to 7.98 | 25 | 1.0958 |
| STW_window_unmapped (unmapped) | 2.71 | -0.23 to 5.64 | 2.43 to 3.00 | 0 | 1.0504 |
| STW_cost_unmapped (unmapped) | 1.05 | -1.74 to 3.85 | 0.63 to 1.50 | 6 | 1.0335 |
| STW_cost_1se_unmapped (unmapped) | 2.60 | -0.32 to 5.53 | 2.33 to 2.86 | 0 | 1.0493 |
| run_to_failure | 21.63 | 18.29 to 24.98 | 21.41 to 21.85 | 260 | 1.2440 |
| perfect_grid | 0.00 | -2.83 to 2.83 | 0.00 to 0.00 | 0 | 1.0227 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -4.17 | -5.43 to -2.91 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | -0.09 | -0.63 to +0.42 | unclear |
| STW_window | P1_cls_opt_max | -0.09 | -0.63 to +0.42 | unclear |
| STW_window | P1_res_q | -0.74 | -1.59 to +0.15 | unclear |
| STW_window | P1_res_opt_mid | -0.74 | -1.59 to +0.15 | unclear |
| STW_window | P1_res_opt_max | -0.74 | -1.59 to +0.15 | unclear |
| STW_window | P3_res60 | -3.34 | -3.87 to -2.78 | STW_window beats P3_res60 |
| STW_window | age_grid | -19.23 | -20.02 to -18.40 | STW_window beats age_grid |
| STW_window | P3_res125 | -3.56 | -4.06 to -3.00 | STW_window beats P3_res125 |
| STW_window | HI_cost | -4.83 | -5.72 to -3.92 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -4.63 | -5.85 to -3.40 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | -0.55 | -1.12 to +0.04 | unclear |
| STW_cost | P1_cls_opt_max | -0.55 | -1.12 to +0.04 | unclear |
| STW_cost | P1_res_q | -1.20 | -2.01 to -0.38 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | -1.20 | -2.01 to -0.38 | STW_cost beats P1_res_opt_mid |
| STW_cost | P1_res_opt_max | -1.20 | -2.01 to -0.38 | STW_cost beats P1_res_opt_max |
| STW_cost | P3_res60 | -3.80 | -4.34 to -3.24 | STW_cost beats P3_res60 |
| STW_cost | age_grid | -19.69 | -20.46 to -18.92 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -4.01 | -4.53 to -3.48 | STW_cost beats P3_res125 |
| STW_cost | HI_cost | -5.29 | -6.25 to -4.32 | STW_cost beats HI_cost |
| STW_cost_1se | P1_cls_q | -2.82 | -4.15 to -1.52 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | +1.26 | +0.61 to +1.90 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +1.26 | +0.61 to +1.90 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | +0.61 | -0.33 to +1.54 | unclear |
| STW_cost_1se | P1_res_opt_mid | +0.61 | -0.33 to +1.54 | unclear |
| STW_cost_1se | P1_res_opt_max | +0.61 | -0.33 to +1.54 | unclear |
| STW_cost_1se | P3_res60 | -1.99 | -2.40 to -1.55 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -17.88 | -18.64 to -17.10 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -2.20 | -2.62 to -1.76 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -3.48 | -4.46 to -2.53 | STW_cost_1se beats HI_cost |

Grid-mapped policies with M < 0: 0. Recorded violations (all, incl. unmapped): 0.
