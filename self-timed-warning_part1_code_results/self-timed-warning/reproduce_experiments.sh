#!/bin/sh
# Level 2 (several hours on 2 CPU cores): rerun every experiment that does not involve a neural network, from the data,
# into out/, and compare each output with the frozen copy in results/ (exact equality). Then rebuild the paper numbers
# and the manuscript; outputs of the neural-network analyses, which this level does not rerun, are taken from results/.
set -e
cd "$(dirname "$0")"
python tools/check_data.py
rm -rf out && mkdir -p out/window out/ncm out/battery out/bearing out/multi out/stwt out/theory out/rep30 out/rep50 out/rev
# main results (Table 2) and leakage checks
python eol_window2.py PHM08 10,15,20,30,40
for d in FD001 FD002 FD003 FD004; do python eol_window2.py $d 10,15,20; done
python eol_leakage.py
# component ablation and oracle-timed control (Table 5)
python warn_ablation.py && python oracle_check.py
# pre-specified confirmations (Table 7): protocol hashes are verified first
python -c "import hashlib;t=open('ncm/WARNING_PROTOCOL.md').read().split('\n## Deviations')[0];assert hashlib.sha256(t.encode()).hexdigest()==open('ncm/WARNING_PROTOCOL.sha256').read().split()[0];print('N-CMAPSS protocol hash OK')"
python ncm_warning.py
python -c "import hashlib;t=open('battery/BATTERY_PROTOCOL.md').read().split('\n## Deviations')[0];assert hashlib.sha256(t.encode()).hexdigest()==open('battery/BATTERY_PROTOCOL.sha256').read().split()[0];print('battery protocol hash OK')"
python battery_warning.py && python battery_cost.py
python -c "import hashlib;assert hashlib.sha256(open('bearing/BEARING_PROTOCOL.md','rb').read()).hexdigest()==open('bearing/BEARING_PROTOCOL.sha256').read().split()[0];print('bearing protocol hash OK')"
python bearing_warning.py
# other windows and cost (Supp. S8-S9), theory-guided shift (S10), repeated random test sets (S11), Proposition 1 (Fig. 8)
python multi_eval.py NCMAPSS6 NCMAPSS14 PHM08 FD001 FD002 FD003 FD004
python stwt_all.py PHM08 FD001 FD002 FD003 FD004 NCMAPSS6 Battery
python rep50.py 20
python rep30.py 1 15 && python rep30.py 16 30 && python rep30_excel.py
python theory_check.py
# timing controls, health-indicator alarm and cost-tuned policies (Tables 3 and 6, Fig. 6, Supp. S12)
for d in PHM08 FD001 FD002 FD003 FD004 NCMAPSS6 Battery; do python rev_experiments.py $d; done
python rev_analyze.py > out/rev_analyze.log
# compare the rerun outputs with results/ before anything else is copied into out/
python verify_reproduction.py || { echo "an exactly reproducible output differs from results/ (see above)"; exit 1; }
# rebuild numbers and manuscript; neural-network outputs (not rerun at this level) come from results/
cp -rn results/* out/ 2>/dev/null || true
python make_paper2_numbers.py > out/make_paper2_numbers.log
python make_rev_numbers.py > out/make_rev_numbers.log
sh paper2/build.sh
python verify_reproduction.py
