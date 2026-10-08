#!/bin/sh
# Second revision (paper4), level 2 (several hours on 2 CPU cores): rerun the analyses added in the second revision from the
# data, compare every output with results/audit/ (verify_audit.py), then rebuild the manuscript. Interrupted runs resume from
# out/audit/ckpt/.
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1
mkdir -p out/audit
python audit_fixed_matched.py          # matched, cross-fitted fixed-time vs self-timed comparison on PHM08 (Table 4)
python audit_battery_physical.py cv    # battery, common physical task, fully nested, cross-validation by cell (Table 8)
python audit_battery_physical.py lobo  # same, one batch held out
python audit_battery_cost2.py          # battery cost with the capacity trend, CV and held-out batch (Table 9)
python verify_audit.py
python audit_summarize2.py > /dev/null
python fig_audit2.py
cp out/paper4_figs/Fig2_matched.png out/paper4_figs/Fig8_battery_physical.png out/paper4_figs/Fig9_battery_cost.png paper4/img/
sh paper4/build.sh
cmp paper4/numbers.json paper4/reference/numbers.json && cmp paper4/tex/manuscript.tex paper4/reference/manuscript.tex && echo "SECOND-REVISION REPRODUCTION CHECK PASSED"
