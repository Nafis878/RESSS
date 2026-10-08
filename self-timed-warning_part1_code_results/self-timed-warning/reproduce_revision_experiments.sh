#!/bin/sh
# Revision (paper3), level 2 (several hours on 2 CPU cores): rerun every analysis added in the revision from the data, compare
# the outputs value by value with results/audit/, then rebuild the revised manuscript. Interrupted runs resume from out/audit/ckpt/.
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1
mkdir -p out/audit
python audit_confirmations.py battery_corrected
python audit_confirmations.py battery_baselines
python audit_confirmations.py battery_sens 3 2 4 6 5 1
python audit_confirmations.py bearing_corrected
python audit_confirmations.py bearing_sens 7 3 5 10 14
python audit_battery_controls.py
python audit_fixed_time.py
python audit_cost.py PHM08 FD001 FD002 FD003 FD004 NCMAPSS6 Battery
python verify_audit.py
python audit_summarize.py > /dev/null
python fig_audit.py
cp out/paper3_figs/Fig2_decomposition.png out/paper3_figs/Fig7_battery_v3.png out/paper3_figs/Fig8_shift_A1.png out/paper3_figs/FigR3_cost_audit.png paper3/img/
sh paper3/build.sh
cmp paper3/numbers.json paper3/reference/numbers.json && cmp paper3/tex/manuscript.tex paper3/reference/manuscript.tex && echo "REVISION REPRODUCTION CHECK PASSED"
