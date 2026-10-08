#!/bin/sh
# Level 1 (minutes): rebuild every number, table and the manuscript from the frozen experiment outputs in results/,
# and check that they are identical to the reference copies in paper2/reference/.
set -e
cd "$(dirname "$0")"
python tools/check_data.py
rm -rf out && mkdir -p out && cp -r results/* out/
python make_paper2_numbers.py > out/make_paper2_numbers.log
python rev_analyze.py > out/rev_analyze.log
python make_rev_numbers.py > out/make_rev_numbers.log
sh paper2/build.sh
python verify_reproduction.py --paper-only
