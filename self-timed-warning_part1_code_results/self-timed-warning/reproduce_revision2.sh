#!/bin/sh
# Second revision (paper4), level 1 (minutes): rebuild the numbers, the three new figures and the manuscript of the second
# revision from the frozen outputs in results/audit/ and check that they are identical to paper4/reference/.
# Needs paper3/numbers.json (committed; regenerate with reproduce_revision.sh).
set -e
cd "$(dirname "$0")"
python audit_summarize2.py --frozen > /dev/null
python fig_audit2.py --frozen
cp out/paper4_figs/Fig2_matched.png out/paper4_figs/Fig8_battery_physical.png out/paper4_figs/Fig9_battery_cost.png paper4/img/
sh paper4/build.sh
cmp paper4/numbers.json paper4/reference/numbers.json && cmp paper4/tex/manuscript.tex paper4/reference/manuscript.tex && cmp paper4/tex/supplementary.tex paper4/reference/supplementary.tex && echo "SECOND-REVISION REPRODUCTION CHECK PASSED"
