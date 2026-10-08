# Leakage checks, end-of-life first-warning model (PHM08)

- PASS  E1 engine sets disjoint (5 folds; inner folds only use outer-training engines)
- PASS  E2 causality: max |prediction(prefix) - prediction(full)| = 0.00e+00 over 90 checks
- PASS  E3 permuted-life labels: fold-1 in-window 15.9% vs real labels 97.7%
- PASS  E4 fold-1 rerun reproduces stored H=10 outcomes engine by engine
