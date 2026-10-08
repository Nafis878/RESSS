# Recorded correction during the continuous extension

The first continuous-closure oracle audit stopped at case8 (seed20261013): H=[19,8], failure indicators=[true,false], a=b=23, rho2. The formula returned1 but the general-state checker returned4/3. Investigation found that the checker admitted a later-only failure phase even when the two ages were identical, where that phase has zero width and is impossible.

The checker now requires min(a,b)<max(a,b) before admitting a later-only phase. A dedicated regression test retains the failing case. The theorem and continuous formula were unchanged. The complete300-case audit and resolution study were restarted after correcting the checker; no partial failed study is presented as a success. The correction does not affect the completed integer solver, its previous independent oracle or its timing study.
