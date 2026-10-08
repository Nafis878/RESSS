# FD003 under the conventions of Kamariotis et al. (exploratory; plan hashed before the run)

## c_p/c_c = 0.1  (primary)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 5.12 | -2.56 to 12.80 | 4.53 to 5.75 | 0 | 1.0686 |
| STW_cost | 31.13 | -1.99 to 64.25 | 3.44 to 67.62 | 3 | 1.3330 |
| STW_cost_1se | 7.26 | -0.62 to 15.15 | 6.61 to 8.00 | 0 | 1.0903 |
| P1_cls_q | 29.75 | -2.33 to 61.82 | 2.28 to 66.10 | 3 | 1.3189 |
| P1_cls_opt_mid | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_cls_opt_max | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_res_q | 46.79 | 8.40 to 85.19 | 10.63 to 91.72 | 5 | 1.4922 |
| P1_res_opt_mid | 7.88 | -0.20 to 15.97 | 7.05 to 8.68 | 0 | 1.0967 |
| P1_res_opt_max | 7.88 | -0.20 to 15.97 | 7.05 to 8.68 | 0 | 1.0967 |
| P3_res60 | 10.39 | 2.06 to 18.72 | 9.52 to 11.35 | 0 | 1.1222 |
| age_grid | 73.00 | 73.00 to 73.00 | 61.43 to 85.50 | 0 | 1.7586 |
| P3_res125 | 11.87 | 3.33 to 20.41 | 10.81 to 13.07 | 0 | 1.1372 |
| HI_cost | 18.55 | -2.84 to 39.94 | 8.21 to 38.72 | 1 | 1.2051 |
| STW_window_unmapped (unmapped) | 6.52 | -1.37 to 14.41 | 5.87 to 7.15 | 0 | 1.0828 |
| STW_cost_unmapped (unmapped) | 12.17 | -7.39 to 31.74 | 2.65 to 30.77 | 1 | 1.1403 |
| STW_cost_1se_unmapped (unmapped) | 7.26 | -0.65 to 15.18 | 6.64 to 7.92 | 0 | 1.0903 |
| run_to_failure | 879.77 | 812.59 to 946.96 | 877.15 to 882.38 | 100 | 9.9595 |
| perfect_grid | 0.00 | -7.01 to 7.01 | 0.00 to 0.00 | 0 | 1.0165 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -24.63 | -61.18 to +2.90 | unclear |
| STW_window | P1_cls_opt_mid | +1.66 | +1.10 to +2.26 | P1_cls_opt_mid beats STW_window |
| STW_window | P1_cls_opt_max | +1.66 | +1.10 to +2.26 | P1_cls_opt_max beats STW_window |
| STW_window | P1_res_q | -41.67 | -86.81 to -5.44 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -2.76 | -3.45 to -2.08 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -2.76 | -3.45 to -2.08 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -5.27 | -6.13 to -4.47 | STW_window beats P3_res60 |
| STW_window | age_grid | -67.88 | -80.85 to -55.97 | STW_window beats age_grid |
| STW_window | P3_res125 | -6.75 | -7.64 to -5.96 | STW_window beats P3_res125 |
| STW_window | HI_cost | -13.43 | -33.74 to -2.91 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | +1.38 | -35.64 to +38.27 | unclear |
| STW_cost | P1_cls_opt_mid | +27.67 | -0.13 to +64.43 | unclear |
| STW_cost | P1_cls_opt_max | +27.67 | -0.13 to +64.43 | unclear |
| STW_cost | P1_res_q | -15.66 | -52.18 to +20.64 | unclear |
| STW_cost | P1_res_opt_mid | +23.25 | -4.52 to +59.79 | unclear |
| STW_cost | P1_res_opt_max | +23.25 | -4.52 to +59.79 | unclear |
| STW_cost | P3_res60 | +20.74 | -7.02 to +57.31 | unclear |
| STW_cost | age_grid | -41.87 | -71.98 to -4.95 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +19.26 | -8.48 to +55.69 | unclear |
| STW_cost | HI_cost | +12.58 | -25.30 to +50.58 | unclear |
| STW_cost_1se | P1_cls_q | -22.49 | -59.13 to +5.07 | unclear |
| STW_cost_1se | P1_cls_opt_mid | +3.80 | +3.19 to +4.49 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +3.80 | +3.19 to +4.49 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | -39.53 | -84.61 to -3.21 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | -0.62 | -1.30 to +0.09 | unclear |
| STW_cost_1se | P1_res_opt_max | -0.62 | -1.30 to +0.09 | unclear |
| STW_cost_1se | P3_res60 | -3.13 | -3.84 to -2.49 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -65.74 | -78.70 to -53.83 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -4.61 | -5.46 to -3.84 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -11.29 | -31.45 to -0.77 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.01  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 5.12 | -2.56 to 12.80 | 4.53 to 5.75 | 0 | 1.0686 |
| STW_cost | 309.91 | -36.55 to 656.37 | 3.44 to 715.48 | 3 | 4.1668 |
| STW_cost_1se | 7.26 | -0.62 to 15.15 | 6.61 to 8.00 | 0 | 1.0903 |
| P1_cls_q | 4.62 | -2.88 to 12.12 | 4.03 to 5.26 | 0 | 1.0635 |
| P1_cls_opt_mid | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_cls_opt_max | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_res_q | 7.07 | -0.88 to 15.03 | 6.38 to 7.75 | 0 | 1.0884 |
| P1_res_opt_mid | 7.88 | -0.20 to 15.97 | 7.05 to 8.68 | 0 | 1.0967 |
| P1_res_opt_max | 7.88 | -0.20 to 15.97 | 7.05 to 8.68 | 0 | 1.0967 |
| P3_res60 | 12.65 | 4.01 to 21.30 | 11.66 to 13.72 | 0 | 1.1451 |
| age_grid | 73.00 | 73.00 to 73.00 | 61.43 to 85.50 | 0 | 1.7586 |
| P3_res125 | 13.92 | 5.13 to 22.71 | 12.79 to 15.17 | 0 | 1.1580 |
| HI_cost | 116.44 | -96.34 to 329.23 | 8.21 to 333.63 | 1 | 2.2002 |
| STW_window_unmapped (unmapped) | 6.52 | -1.37 to 14.41 | 5.87 to 7.15 | 0 | 1.0828 |
| STW_cost_unmapped (unmapped) | 104.79 | -94.88 to 304.47 | 2.65 to 308.79 | 1 | 2.0817 |
| STW_cost_1se_unmapped (unmapped) | 7.26 | -0.65 to 15.18 | 6.64 to 7.92 | 0 | 1.0903 |
| run_to_failure | 9697.73 | 9025.90 to 10369.57 | 9671.46 to 9723.84 | 100 | 99.5955 |
| perfect_grid | 0.00 | -7.01 to 7.01 | 0.00 to 0.00 | 0 | 1.0165 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | +0.50 | -0.14 to +1.16 | unclear |
| STW_window | P1_cls_opt_mid | +1.66 | +1.10 to +2.26 | P1_cls_opt_mid beats STW_window |
| STW_window | P1_cls_opt_max | +1.66 | +1.10 to +2.26 | P1_cls_opt_max beats STW_window |
| STW_window | P1_res_q | -1.95 | -2.43 to -1.48 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -2.76 | -3.45 to -2.08 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -2.76 | -3.45 to -2.08 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -7.53 | -8.26 to -6.84 | STW_window beats P3_res60 |
| STW_window | age_grid | -67.88 | -80.85 to -55.97 | STW_window beats age_grid |
| STW_window | P3_res125 | -8.80 | -9.81 to -7.90 | STW_window beats P3_res125 |
| STW_window | HI_cost | -111.32 | -328.50 to -2.91 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | +305.29 | -1.32 to +711.12 | unclear |
| STW_cost | P1_cls_opt_mid | +306.45 | -0.13 to +712.41 | unclear |
| STW_cost | P1_cls_opt_max | +306.45 | -0.13 to +712.41 | unclear |
| STW_cost | P1_res_q | +302.84 | -3.63 to +708.24 | unclear |
| STW_cost | P1_res_opt_mid | +302.03 | -4.52 to +707.54 | unclear |
| STW_cost | P1_res_opt_max | +302.03 | -4.52 to +707.54 | unclear |
| STW_cost | P3_res60 | +297.26 | -9.16 to +702.77 | unclear |
| STW_cost | age_grid | +236.91 | -69.43 to +640.48 | unclear |
| STW_cost | P3_res125 | +295.99 | -10.63 to +701.63 | unclear |
| STW_cost | HI_cost | +193.47 | -224.03 to +607.47 | unclear |
| STW_cost_1se | P1_cls_q | +2.64 | +1.97 to +3.38 | P1_cls_q beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_mid | +3.80 | +3.19 to +4.49 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +3.80 | +3.19 to +4.49 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | +0.19 | -0.33 to +0.76 | unclear |
| STW_cost_1se | P1_res_opt_mid | -0.62 | -1.30 to +0.09 | unclear |
| STW_cost_1se | P1_res_opt_max | -0.62 | -1.30 to +0.09 | unclear |
| STW_cost_1se | P3_res60 | -5.39 | -6.13 to -4.67 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -65.74 | -78.70 to -53.83 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -6.66 | -7.56 to -5.81 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -109.18 | -326.13 to -0.77 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.02  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 5.12 | -2.56 to 12.80 | 4.53 to 5.75 | 0 | 1.0686 |
| STW_cost | 155.03 | -17.02 to 327.08 | 3.44 to 355.56 | 3 | 2.5925 |
| STW_cost_1se | 7.26 | -0.62 to 15.15 | 6.61 to 8.00 | 0 | 1.0903 |
| P1_cls_q | 4.26 | -3.22 to 11.74 | 3.70 to 4.89 | 0 | 1.0598 |
| P1_cls_opt_mid | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_cls_opt_max | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_res_q | 7.07 | -0.88 to 15.03 | 6.38 to 7.75 | 0 | 1.0884 |
| P1_res_opt_mid | 7.88 | -0.20 to 15.97 | 7.05 to 8.68 | 0 | 1.0967 |
| P1_res_opt_max | 7.88 | -0.20 to 15.97 | 7.05 to 8.68 | 0 | 1.0967 |
| P3_res60 | 12.65 | 4.01 to 21.30 | 11.66 to 13.72 | 0 | 1.1451 |
| age_grid | 73.00 | 73.00 to 73.00 | 61.43 to 85.50 | 0 | 1.7586 |
| P3_res125 | 13.92 | 5.13 to 22.71 | 12.79 to 15.17 | 0 | 1.1580 |
| HI_cost | 62.06 | -43.88 to 168.01 | 8.21 to 169.79 | 1 | 1.6474 |
| STW_window_unmapped (unmapped) | 6.52 | -1.37 to 14.41 | 5.87 to 7.15 | 0 | 1.0828 |
| STW_cost_unmapped (unmapped) | 53.34 | -45.69 to 152.37 | 2.65 to 154.34 | 1 | 1.5587 |
| STW_cost_1se_unmapped (unmapped) | 7.26 | -0.65 to 15.18 | 6.64 to 7.92 | 0 | 1.0903 |
| run_to_failure | 4798.87 | 4462.95 to 5134.78 | 4785.73 to 4811.92 | 100 | 49.7977 |
| perfect_grid | 0.00 | -7.01 to 7.01 | 0.00 to 0.00 | 0 | 1.0165 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | +0.86 | +0.26 to +1.52 | P1_cls_q beats STW_window |
| STW_window | P1_cls_opt_mid | +1.66 | +1.10 to +2.26 | P1_cls_opt_mid beats STW_window |
| STW_window | P1_cls_opt_max | +1.66 | +1.10 to +2.26 | P1_cls_opt_max beats STW_window |
| STW_window | P1_res_q | -1.95 | -2.43 to -1.48 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -2.76 | -3.45 to -2.08 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -2.76 | -3.45 to -2.08 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -7.53 | -8.26 to -6.84 | STW_window beats P3_res60 |
| STW_window | age_grid | -67.88 | -80.85 to -55.97 | STW_window beats age_grid |
| STW_window | P3_res125 | -8.80 | -9.81 to -7.90 | STW_window beats P3_res125 |
| STW_window | HI_cost | -56.94 | -164.67 to -2.91 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | +150.77 | -0.93 to +351.54 | unclear |
| STW_cost | P1_cls_opt_mid | +151.57 | -0.13 to +352.32 | unclear |
| STW_cost | P1_cls_opt_max | +151.57 | -0.13 to +352.32 | unclear |
| STW_cost | P1_res_q | +147.96 | -3.63 to +348.43 | unclear |
| STW_cost | P1_res_opt_mid | +147.15 | -4.52 to +347.74 | unclear |
| STW_cost | P1_res_opt_max | +147.15 | -4.52 to +347.74 | unclear |
| STW_cost | P3_res60 | +142.38 | -9.16 to +342.82 | unclear |
| STW_cost | age_grid | +82.03 | -69.43 to +279.76 | unclear |
| STW_cost | P3_res125 | +141.11 | -10.63 to +341.67 | unclear |
| STW_cost | HI_cost | +92.97 | -113.38 to +298.08 | unclear |
| STW_cost_1se | P1_cls_q | +3.00 | +2.34 to +3.72 | P1_cls_q beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_mid | +3.80 | +3.19 to +4.49 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +3.80 | +3.19 to +4.49 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | +0.19 | -0.33 to +0.76 | unclear |
| STW_cost_1se | P1_res_opt_mid | -0.62 | -1.30 to +0.09 | unclear |
| STW_cost_1se | P1_res_opt_max | -0.62 | -1.30 to +0.09 | unclear |
| STW_cost_1se | P3_res60 | -5.39 | -6.13 to -4.67 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -65.74 | -78.70 to -53.83 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -6.66 | -7.56 to -5.81 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -54.80 | -162.42 to -0.77 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.05  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 5.12 | -2.56 to 12.80 | 4.53 to 5.75 | 0 | 1.0686 |
| STW_cost | 62.11 | -5.49 to 129.70 | 3.44 to 139.61 | 3 | 1.6478 |
| STW_cost_1se | 7.26 | -0.62 to 15.15 | 6.61 to 8.00 | 0 | 1.0903 |
| P1_cls_q | 42.13 | -11.96 to 96.21 | 2.88 to 100.95 | 2 | 1.4447 |
| P1_cls_opt_mid | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_cls_opt_max | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_res_q | 44.21 | -11.65 to 100.07 | 4.35 to 103.80 | 2 | 1.4659 |
| P1_res_opt_mid | 7.88 | -0.20 to 15.97 | 7.05 to 8.68 | 0 | 1.0967 |
| P1_res_opt_max | 7.88 | -0.20 to 15.97 | 7.05 to 8.68 | 0 | 1.0967 |
| P3_res60 | 11.72 | 3.18 to 20.25 | 10.69 to 12.81 | 0 | 1.1356 |
| age_grid | 73.00 | 73.00 to 73.00 | 61.43 to 85.50 | 0 | 1.7586 |
| P3_res125 | 12.91 | 4.21 to 21.61 | 11.72 to 14.28 | 0 | 1.1478 |
| HI_cost | 29.43 | -12.71 to 71.58 | 8.21 to 71.49 | 1 | 1.3157 |
| STW_window_unmapped (unmapped) | 6.52 | -1.37 to 14.41 | 5.87 to 7.15 | 0 | 1.0828 |
| STW_cost_unmapped (unmapped) | 22.46 | -16.52 to 61.45 | 2.65 to 61.66 | 1 | 1.2449 |
| STW_cost_1se_unmapped (unmapped) | 7.26 | -0.65 to 15.18 | 6.64 to 7.92 | 0 | 1.0903 |
| run_to_failure | 1859.55 | 1725.18 to 1993.91 | 1854.29 to 1864.77 | 100 | 19.9191 |
| perfect_grid | 0.00 | -7.01 to 7.01 | 0.00 to 0.00 | 0 | 1.0165 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -37.00 | -95.98 to +2.39 | unclear |
| STW_window | P1_cls_opt_mid | +1.66 | +1.10 to +2.26 | P1_cls_opt_mid beats STW_window |
| STW_window | P1_cls_opt_max | +1.66 | +1.10 to +2.26 | P1_cls_opt_max beats STW_window |
| STW_window | P1_res_q | -39.09 | -98.56 to +0.78 | unclear |
| STW_window | P1_res_opt_mid | -2.76 | -3.45 to -2.08 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -2.76 | -3.45 to -2.08 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -6.59 | -7.41 to -5.81 | STW_window beats P3_res60 |
| STW_window | age_grid | -67.88 | -80.85 to -55.97 | STW_window beats age_grid |
| STW_window | P3_res125 | -7.79 | -8.86 to -6.85 | STW_window beats P3_res125 |
| STW_window | HI_cost | -24.31 | -66.47 to -2.91 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | +19.98 | -60.06 to +99.40 | unclear |
| STW_cost | P1_cls_opt_mid | +58.65 | -0.13 to +136.38 | unclear |
| STW_cost | P1_cls_opt_max | +58.65 | -0.13 to +136.38 | unclear |
| STW_cost | P1_res_q | +17.90 | -2.42 to +57.75 | unclear |
| STW_cost | P1_res_opt_mid | +54.22 | -4.52 to +131.77 | unclear |
| STW_cost | P1_res_opt_max | +54.22 | -4.52 to +131.77 | unclear |
| STW_cost | P3_res60 | +50.39 | -8.18 to +127.86 | unclear |
| STW_cost | age_grid | -10.89 | -69.48 to +64.11 | unclear |
| STW_cost | P3_res125 | +49.19 | -9.61 to +126.52 | unclear |
| STW_cost | HI_cost | +32.68 | -47.48 to +112.39 | unclear |
| STW_cost_1se | P1_cls_q | -34.86 | -93.74 to +4.51 | unclear |
| STW_cost_1se | P1_cls_opt_mid | +3.80 | +3.19 to +4.49 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +3.80 | +3.19 to +4.49 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | -36.95 | -96.49 to +2.98 | unclear |
| STW_cost_1se | P1_res_opt_mid | -0.62 | -1.30 to +0.09 | unclear |
| STW_cost_1se | P1_res_opt_max | -0.62 | -1.30 to +0.09 | unclear |
| STW_cost_1se | P3_res60 | -4.45 | -5.30 to -3.64 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -65.74 | -78.70 to -53.83 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -5.65 | -6.70 to -4.68 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -22.17 | -64.18 to -0.77 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.2  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 5.12 | -2.56 to 12.80 | 4.53 to 5.75 | 0 | 1.0686 |
| STW_cost | 15.64 | -0.90 to 32.19 | 3.44 to 31.63 | 3 | 1.1755 |
| STW_cost_1se | 7.26 | -0.62 to 15.15 | 6.61 to 8.00 | 0 | 1.0903 |
| P1_cls_q | 21.77 | 2.06 to 41.49 | 5.75 to 41.64 | 5 | 1.2379 |
| P1_cls_opt_mid | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_cls_opt_max | 3.46 | -3.92 to 10.84 | 2.95 to 4.02 | 0 | 1.0517 |
| P1_res_q | 21.48 | 3.72 to 39.25 | 5.56 to 41.27 | 5 | 1.2349 |
| P1_res_opt_mid | 7.07 | -0.88 to 15.03 | 6.38 to 7.75 | 0 | 1.0884 |
| P1_res_opt_max | 7.07 | -0.88 to 15.03 | 6.38 to 7.75 | 0 | 1.0884 |
| P3_res60 | 7.07 | -0.88 to 15.03 | 6.38 to 7.75 | 0 | 1.0884 |
| age_grid | 81.75 | 63.22 to 100.28 | 64.35 to 104.34 | 2 | 1.8475 |
| P3_res125 | 13.68 | 1.93 to 25.44 | 8.74 to 22.65 | 1 | 1.1556 |
| HI_cost | 13.12 | 1.23 to 25.01 | 8.21 to 22.33 | 1 | 1.1498 |
| STW_window_unmapped (unmapped) | 6.52 | -1.37 to 14.41 | 5.87 to 7.15 | 0 | 1.0828 |
| STW_cost_unmapped (unmapped) | 7.03 | -3.88 to 17.93 | 2.65 to 15.33 | 1 | 1.0879 |
| STW_cost_1se_unmapped (unmapped) | 7.26 | -0.65 to 15.18 | 6.64 to 7.92 | 0 | 1.0903 |
| run_to_failure | 389.89 | 356.30 to 423.48 | 388.57 to 391.19 | 100 | 4.9798 |
| perfect_grid | 0.00 | -7.01 to 7.01 | 0.00 to 0.00 | 0 | 1.0165 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -16.65 | -36.57 to -0.48 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | +1.66 | +1.10 to +2.26 | P1_cls_opt_mid beats STW_window |
| STW_window | P1_cls_opt_max | +1.66 | +1.10 to +2.26 | P1_cls_opt_max beats STW_window |
| STW_window | P1_res_q | -16.36 | -36.31 to -0.37 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | -1.95 | -2.43 to -1.48 | STW_window beats P1_res_opt_mid |
| STW_window | P1_res_opt_max | -1.95 | -2.43 to -1.48 | STW_window beats P1_res_opt_max |
| STW_window | P3_res60 | -1.95 | -2.43 to -1.48 | STW_window beats P3_res60 |
| STW_window | age_grid | -76.63 | -99.29 to -59.22 | STW_window beats age_grid |
| STW_window | P3_res125 | -8.56 | -17.47 to -3.73 | STW_window beats P3_res125 |
| STW_window | HI_cost | -8.00 | -17.36 to -2.91 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -6.13 | -26.46 to +14.06 | unclear |
| STW_cost | P1_cls_opt_mid | +12.18 | -0.13 to +28.42 | unclear |
| STW_cost | P1_cls_opt_max | +12.18 | -0.13 to +28.42 | unclear |
| STW_cost | P1_res_q | -5.84 | -22.00 to +10.05 | unclear |
| STW_cost | P1_res_opt_mid | +8.57 | -3.63 to +24.61 | unclear |
| STW_cost | P1_res_opt_max | +8.57 | -3.63 to +24.61 | unclear |
| STW_cost | P3_res60 | +8.57 | -3.63 to +24.61 | unclear |
| STW_cost | age_grid | -66.11 | -92.53 to -42.05 | STW_cost beats age_grid |
| STW_cost | P3_res125 | +1.96 | -6.69 to +14.37 | unclear |
| STW_cost | HI_cost | +2.53 | -14.31 to +19.69 | unclear |
| STW_cost_1se | P1_cls_q | -14.51 | -34.42 to +1.63 | unclear |
| STW_cost_1se | P1_cls_opt_mid | +3.80 | +3.19 to +4.49 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +3.80 | +3.19 to +4.49 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | -14.22 | -34.17 to +1.87 | unclear |
| STW_cost_1se | P1_res_opt_mid | +0.19 | -0.33 to +0.76 | unclear |
| STW_cost_1se | P1_res_opt_max | +0.19 | -0.33 to +0.76 | unclear |
| STW_cost_1se | P3_res60 | +0.19 | -0.33 to +0.76 | unclear |
| STW_cost_1se | age_grid | -74.49 | -97.02 to -56.80 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -6.42 | -15.35 to -1.62 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | -5.85 | -15.09 to -0.77 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.5  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 7.25 | -0.77 to 15.26 | 3.97 to 11.52 | 4 | 1.0902 |
| STW_cost | 7.10 | -1.08 to 15.28 | 3.32 to 11.76 | 5 | 1.0887 |
| STW_cost_1se | 7.17 | -0.70 to 15.03 | 6.56 to 7.87 | 0 | 1.0894 |
| P1_cls_q | 15.13 | 4.47 to 25.80 | 9.20 to 21.90 | 15 | 1.1703 |
| P1_cls_opt_mid | 4.23 | -3.60 to 12.06 | 2.87 to 6.55 | 1 | 1.0595 |
| P1_cls_opt_max | 4.23 | -3.60 to 12.06 | 2.87 to 6.55 | 1 | 1.0595 |
| P1_res_q | 6.30 | -1.59 to 14.19 | 2.51 to 11.00 | 5 | 1.0805 |
| P1_res_opt_mid | 7.48 | -0.63 to 15.60 | 4.12 to 11.84 | 4 | 1.0926 |
| P1_res_opt_max | 7.48 | -0.63 to 15.60 | 4.12 to 11.84 | 4 | 1.0926 |
| P3_res60 | 7.07 | -0.88 to 15.03 | 6.38 to 7.75 | 0 | 1.0884 |
| age_grid | 66.07 | 55.95 to 76.19 | 55.02 to 78.02 | 13 | 1.6881 |
| P3_res125 | 7.87 | -0.31 to 16.05 | 6.40 to 10.13 | 1 | 1.0965 |
| HI_cost | 9.85 | 2.01 to 17.70 | 8.21 to 12.43 | 1 | 1.1167 |
| STW_window_unmapped (unmapped) | 5.02 | -2.74 to 12.78 | 2.87 to 8.15 | 2 | 1.0676 |
| STW_cost_unmapped (unmapped) | 4.56 | -2.81 to 11.94 | 1.66 to 8.49 | 3 | 1.0629 |
| STW_cost_1se_unmapped (unmapped) | 6.88 | -0.96 to 14.72 | 6.29 to 7.49 | 0 | 1.0865 |
| run_to_failure | 95.95 | 82.52 to 109.39 | 95.43 to 96.48 | 100 | 1.9919 |
| perfect_grid | 0.00 | -7.01 to 7.01 | 0.00 to 0.00 | 0 | 1.0165 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -7.89 | -15.03 to -1.01 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | +3.02 | -0.99 to +7.67 | unclear |
| STW_window | P1_cls_opt_max | +3.02 | -0.99 to +7.67 | unclear |
| STW_window | P1_res_q | +0.95 | -2.40 to +4.24 | unclear |
| STW_window | P1_res_opt_mid | -0.24 | -3.15 to +2.83 | unclear |
| STW_window | P1_res_opt_max | -0.24 | -3.15 to +2.83 | unclear |
| STW_window | P3_res60 | +0.17 | -3.31 to +4.59 | unclear |
| STW_window | age_grid | -58.83 | -71.81 to -47.60 | STW_window beats age_grid |
| STW_window | P3_res125 | -0.63 | -3.55 to +3.33 | unclear |
| STW_window | HI_cost | -2.61 | -6.91 to +2.16 | unclear |
| STW_cost | P1_cls_q | -8.03 | -14.84 to -2.01 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | +2.87 | -0.48 to +7.18 | unclear |
| STW_cost | P1_cls_opt_max | +2.87 | -0.48 to +7.18 | unclear |
| STW_cost | P1_res_q | +0.80 | -2.13 to +3.62 | unclear |
| STW_cost | P1_res_opt_mid | -0.38 | -3.69 to +3.19 | unclear |
| STW_cost | P1_res_opt_max | -0.38 | -3.69 to +3.19 | unclear |
| STW_cost | P3_res60 | +0.03 | -3.92 to +4.92 | unclear |
| STW_cost | age_grid | -58.97 | -71.51 to -47.38 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -0.77 | -4.05 to +3.37 | unclear |
| STW_cost | HI_cost | -2.75 | -7.40 to +2.65 | unclear |
| STW_cost_1se | P1_cls_q | -7.96 | -14.93 to -1.72 | STW_cost_1se beats P1_cls_q |
| STW_cost_1se | P1_cls_opt_mid | +2.94 | +0.55 to +4.43 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +2.94 | +0.55 to +4.43 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | +0.87 | -4.06 to +4.83 | unclear |
| STW_cost_1se | P1_res_opt_mid | -0.32 | -4.79 to +3.16 | unclear |
| STW_cost_1se | P1_res_opt_max | -0.32 | -4.79 to +3.16 | unclear |
| STW_cost_1se | P3_res60 | +0.09 | -0.42 to +0.61 | unclear |
| STW_cost_1se | age_grid | -58.90 | -71.14 to -47.64 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -0.70 | -2.92 to +0.68 | unclear |
| STW_cost_1se | HI_cost | -2.69 | -5.30 to -0.89 | STW_cost_1se beats HI_cost |

## c_p/c_c = 0.8  (descriptive)
| Policy | M (%) | Eq. 7 95% CI | Bootstrap 95% CI | Failures | Ratio vs 1-cycle perfect |
|---|---|---|---|---|---|
| STW_window | 3.23 | -4.18 to 10.63 | 2.10 to 4.52 | 8 | 1.0493 |
| STW_cost | 3.44 | -3.73 to 10.61 | 2.31 to 4.73 | 9 | 1.0515 |
| STW_cost_1se | 6.00 | -1.72 to 13.71 | 5.36 to 6.68 | 0 | 1.0775 |
| P1_cls_q | 7.50 | -0.07 to 15.07 | 5.39 to 9.65 | 34 | 1.0927 |
| P1_cls_opt_mid | 2.58 | -4.74 to 9.91 | 1.82 to 3.47 | 3 | 1.0428 |
| P1_cls_opt_max | 2.54 | -4.77 to 9.85 | 1.78 to 3.42 | 3 | 1.0423 |
| P1_res_q | 22.47 | 14.07 to 30.87 | 22.14 to 22.80 | 100 | 1.2449 |
| P1_res_opt_mid | 2.50 | -4.61 to 9.61 | 1.63 to 3.50 | 5 | 1.0420 |
| P1_res_opt_max | 2.50 | -4.61 to 9.61 | 1.63 to 3.50 | 5 | 1.0420 |
| P3_res60 | 7.07 | -0.88 to 15.03 | 6.38 to 7.75 | 0 | 1.0884 |
| age_grid | 22.08 | 13.45 to 30.71 | 21.53 to 22.55 | 97 | 1.2410 |
| P3_res125 | 7.07 | -0.87 to 15.01 | 6.34 to 7.81 | 1 | 1.0884 |
| HI_cost | 5.76 | -1.78 to 13.30 | 4.40 to 7.12 | 10 | 1.0750 |
| STW_window_unmapped (unmapped) | 2.98 | -4.36 to 10.32 | 2.32 to 3.80 | 2 | 1.0468 |
| STW_cost_unmapped (unmapped) | 1.91 | -4.88 to 8.70 | 1.01 to 2.97 | 5 | 1.0359 |
| STW_cost_1se_unmapped (unmapped) | 5.78 | -1.92 to 13.48 | 5.20 to 6.39 | 1 | 1.0753 |
| run_to_failure | 22.47 | 14.07 to 30.87 | 22.14 to 22.80 | 100 | 1.2449 |
| perfect_grid | 0.00 | -7.01 to 7.01 | 0.00 to 0.00 | 0 | 1.0165 |

| My policy | vs | M difference (pp) | Paired bootstrap 95% CI | Verdict |
|---|---|---|---|---|
| STW_window | P1_cls_q | -4.27 | -6.44 to -2.28 | STW_window beats P1_cls_q |
| STW_window | P1_cls_opt_mid | +0.64 | -0.79 to +2.13 | unclear |
| STW_window | P1_cls_opt_max | +0.69 | -0.77 to +2.17 | unclear |
| STW_window | P1_res_q | -19.24 | -20.43 to -17.87 | STW_window beats P1_res_q |
| STW_window | P1_res_opt_mid | +0.72 | -0.40 to +1.95 | unclear |
| STW_window | P1_res_opt_max | +0.72 | -0.40 to +1.95 | unclear |
| STW_window | P3_res60 | -3.85 | -5.09 to -2.43 | STW_window beats P3_res60 |
| STW_window | age_grid | -18.86 | -20.12 to -17.48 | STW_window beats age_grid |
| STW_window | P3_res125 | -3.84 | -5.06 to -2.44 | STW_window beats P3_res125 |
| STW_window | HI_cost | -2.53 | -3.88 to -1.08 | STW_window beats HI_cost |
| STW_cost | P1_cls_q | -4.06 | -6.16 to -2.10 | STW_cost beats P1_cls_q |
| STW_cost | P1_cls_opt_mid | +0.86 | -0.37 to +2.30 | unclear |
| STW_cost | P1_cls_opt_max | +0.90 | -0.33 to +2.33 | unclear |
| STW_cost | P1_res_q | -19.03 | -20.23 to -17.68 | STW_cost beats P1_res_q |
| STW_cost | P1_res_opt_mid | +0.94 | +0.13 to +1.92 | P1_res_opt_mid beats STW_cost |
| STW_cost | P1_res_opt_max | +0.94 | +0.13 to +1.92 | P1_res_opt_max beats STW_cost |
| STW_cost | P3_res60 | -3.63 | -5.06 to -2.05 | STW_cost beats P3_res60 |
| STW_cost | age_grid | -18.64 | -19.91 to -17.24 | STW_cost beats age_grid |
| STW_cost | P3_res125 | -3.63 | -5.01 to -2.09 | STW_cost beats P3_res125 |
| STW_cost | HI_cost | -2.32 | -3.86 to -0.78 | STW_cost beats HI_cost |
| STW_cost_1se | P1_cls_q | -1.50 | -3.96 to +0.98 | unclear |
| STW_cost_1se | P1_cls_opt_mid | +3.41 | +2.33 to +4.36 | P1_cls_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_cls_opt_max | +3.45 | +2.37 to +4.41 | P1_cls_opt_max beats STW_cost_1se |
| STW_cost_1se | P1_res_q | -16.48 | -17.14 to -15.77 | STW_cost_1se beats P1_res_q |
| STW_cost_1se | P1_res_opt_mid | +3.49 | +2.25 to +4.56 | P1_res_opt_mid beats STW_cost_1se |
| STW_cost_1se | P1_res_opt_max | +3.49 | +2.25 to +4.56 | P1_res_opt_max beats STW_cost_1se |
| STW_cost_1se | P3_res60 | -1.08 | -1.58 to -0.60 | STW_cost_1se beats P3_res60 |
| STW_cost_1se | age_grid | -16.09 | -16.84 to -15.32 | STW_cost_1se beats age_grid |
| STW_cost_1se | P3_res125 | -1.08 | -1.70 to -0.52 | STW_cost_1se beats P3_res125 |
| STW_cost_1se | HI_cost | +0.24 | -1.32 to +1.83 | unclear |

Grid-mapped policies with M < 0: 0. Recorded violations (all, incl. unmapped): 0.
