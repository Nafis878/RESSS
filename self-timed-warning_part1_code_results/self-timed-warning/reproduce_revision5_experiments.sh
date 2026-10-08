#!/bin/sh
# Third revision (paper5), levels 2-3 (about 6 CPU-hours on 2 cores): reruns every analysis of the third revision from the data
# with the plans kam/PHASE2_PLAN.md and kam/PHASE3_4_PLAN.md, compares the regenerated summary tables with the frozen ones
# (kam/check_r0.py for FD001; verify_revision5.py for the rest) and rebuilds the manuscript. Single-threaded processes give the
# same trees as two threads (checked); run at most two processes at a time on two cores.
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1
python kam/test_kam_metric.py
python kam/kam_grid_effect.py
python kam/kam_simulator.py
python kam/kam_fd001.py cv && python kam/kam_fd001.py leak
python kam/kam_fd001.py splits 1 15 && python kam/kam_fd001.py splits 16 30
for ds in FD002 FD003 FD004; do python kam/kam_fd001.py cv --ds $ds && python kam/kam_fd001.py leak --ds $ds; done
python kam/kam_fd001_summarize.py && python kam/check_r0.py
for ds in FD002 FD003 FD004; do python kam/kam_fd001_summarize.py --ds $ds > /dev/null; done
python kam/kam_fragility.py > /dev/null
python audit_hi_calibrated.py PHM08 FD001 FD002 FD003 FD004 NCMAPSS6
python audit_battery_cost_nested.py
python audit_fixed_matched.py --ds FD004
python verify_revision5.py
python kam/make_rev5_numbers.py && python fig_rev5.py && sh paper5/build.sh
