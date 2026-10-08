#!/bin/sh
# Revision (paper3), level 1 (minutes): rebuild the numbers, the four new figures and the revised manuscript from the frozen
# audit outputs in results/audit/ and check that they are identical to paper3/reference/.
set -e
cd "$(dirname "$0")"
python audit_summarize.py --frozen > /dev/null
python fig_audit.py --frozen
cp out/paper3_figs/Fig2_decomposition.png out/paper3_figs/Fig7_battery_v3.png out/paper3_figs/Fig8_shift_A1.png out/paper3_figs/FigR3_cost_audit.png paper3/img/
sh paper3/build.sh
cmp paper3/numbers.json paper3/reference/numbers.json && cmp paper3/tex/manuscript.tex paper3/reference/manuscript.tex && cmp paper3/tex/supplementary.tex paper3/reference/supplementary.tex && echo "REVISION REPRODUCTION CHECK PASSED"
