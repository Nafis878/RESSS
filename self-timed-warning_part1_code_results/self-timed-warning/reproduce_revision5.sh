#!/bin/sh
# Third revision (paper5), level 1 (minutes): unit tests of the re-implemented metric M, then rebuild the numbers, the three
# new figures and the manuscript of the third revision from the frozen outputs in results/kam/ and results/audit/, and check
# that they are identical to paper5/reference/. Needs paper4/numbers.json (committed; regenerate with reproduce_revision2.sh).
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1
python kam/test_kam_metric.py | tail -1
python kam/make_rev5_numbers.py --frozen > /dev/null
python fig_rev5.py --frozen
sh paper5/build.sh
cmp paper5/numbers.json paper5/reference/numbers.json && cmp paper5/tex/manuscript.tex paper5/reference/manuscript.tex && cmp paper5/tex/supplementary.tex paper5/reference/supplementary.tex && echo "THIRD-REVISION REPRODUCTION CHECK PASSED"
# Reframed manuscript (paper6): same numbers.json, rewritten text; must equal paper6/reference/
cp paper5/numbers.json paper6/numbers.json
sh paper6/build.sh
cmp paper6/tex/manuscript.tex paper6/reference/manuscript.tex && cmp paper6/tex/supplementary.tex paper6/reference/supplementary.tex && echo "REFRAMED-MANUSCRIPT REPRODUCTION CHECK PASSED"
