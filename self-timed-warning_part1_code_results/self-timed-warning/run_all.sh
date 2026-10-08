#!/bin/sh
# Level 3 (about 12-14 hours on 2 CPU cores): reproduces every result, figure and number of the manuscript from the data,
# including the neural-network analyses. Run from this folder (README). Ends with verify_reproduction.py.
set -e
export KERAS_BACKEND=jax
python tools/check_data.py
mkdir -p out/bearing out/stwt out/rep30 out/safe out/ncm out/window out/rep50 out/battery out/multi out/theory out/rev out/paper2_figs paper2/img
# 1. fixed-time reference pipeline: age-only, GBM, IOHMM, CNN, LSTM (5-fold engine CV) -> out/safe/preds_*.csv
for m in age iohmm gbm cnn lstm; do python safe_run.py $m; done
python safe_analyze.py stage                       # -> out/safe/v2_cut_predictions.csv (fixed-fraction predictions)
# 2. warning model: main results (Table 2, Fig. 4)
python eol_window2.py PHM08 10,15,20,30,40
for d in FD001 FD002 FD003 FD004; do python eol_window2.py $d 10,15,20; done
python eol_leakage.py                              # E1-E4, must report 4 PASS
# 3. identical-protocol comparison, ablation, oracle control, repeated splits
python h2h.py PHM08
python warn_ablation.py && python oracle_check.py
python rep50.py 20 && python rep50_excel.py
# 4. fixed-time reference models at half of life (Section 6.1)
python collect_base.py PHM08 && python ablate_hybrid.py
python tcn_gan.py PHM08 && python tcn_eval.py
python ext_data.py && python ext_stack.py
# 5. pre-specified N-CMAPSS confirmation: verify the protocol hash first
python -c "import hashlib;t=open('ncm/WARNING_PROTOCOL.md').read().split('\n## Deviations')[0];assert hashlib.sha256(t.encode()).hexdigest()==open('ncm/WARNING_PROTOCOL.sha256').read().split()[0];print('protocol hash OK')"
python ncm_warning.py
# 5b. pre-specified battery confirmation: verify the protocol hash first
python -c "import hashlib;t=open('battery/BATTERY_PROTOCOL.md').read().split('\n## Deviations')[0];assert hashlib.sha256(t.encode()).hexdigest()==open('battery/BATTERY_PROTOCOL.sha256').read().split()[0];print('battery protocol hash OK')"
python battery_warning.py && python battery_cost.py
# 5c. deep networks with the same inputs; other windows and cost; check of Proposition 1
python dl_warning.py
python multi_eval.py NCMAPSS6 NCMAPSS14 PHM08 FD001 FD002 FD003 FD004
python stw_timing.py
# 5d. pre-specified bearing confirmation (download Learning_set and Full_Test_Set of the PHM 2012 data to bearing/femto_repo first; see README)
python -c "import hashlib;assert hashlib.sha256(open('bearing/BEARING_PROTOCOL.md','rb').read()).hexdigest()==open('bearing/BEARING_PROTOCOL.sha256').read().split()[0];print('bearing protocol hash OK')"
# bearing_extract.py rebuilds bearing/femto_snapshot_features.csv.gz from the raw files (optional; the features are included)
[ -d bearing/femto_repo ] && python bearing_extract.py || echo 'raw bearing files not present: using the included features'
python bearing_warning.py
python stwt_all.py PHM08 FD001 FD002 FD003 FD004 NCMAPSS6 Battery
python rep30.py 1 15 && python rep30.py 16 30 && python rep30_excel.py
# 5e. revision experiments: timing controls, health-indicator alarm, cost-tuned policies
for d in PHM08 FD001 FD002 FD003 FD004 NCMAPSS6 Battery; do python rev_experiments.py $d; done
# 6. numbers, figures, manuscript (Node.js; pdfLaTeX for the PDFs)
python theory_check.py
python make_paper2_numbers.py && python rev_analyze.py && python make_rev_numbers.py && python fig_rev.py && python fig_future_work.py
python fig_stw_architecture.py && python paper2_figures.py && python paper2_figures_rev.py && python fig_rep30.py
python -c "from PIL import Image;import glob,os;[Image.open(f).convert('RGB').resize((2400,int(2400*Image.open(f).size[1]/Image.open(f).size[0]))).save('paper2/img/'+os.path.basename(f)) for f in glob.glob('out/paper2_figs/*.png')]"
sh paper2/build.sh
python verify_reproduction.py
