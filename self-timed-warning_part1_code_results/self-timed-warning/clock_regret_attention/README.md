# Certified focus search with attention ablations

The best supported combination retains shared lifetime clocks, heterogeneous
premiums, exact compatible witnesses, omitted-premium focus bounds and the
complete-family FPTAS fallback. Validation chooses sequential greedy as the
proposal. Premium focus supplies the minimum certificate factor at each budget;
attention is optional and did not establish superiority against greedy.

Read THEORY.md, FAILURES_AND_LIMITATIONS.md, LITERATURE.md and REPORT.md.
The working paper is under `out/clock_regret_attention/manuscript.pdf`.
This is a new draft; earlier PDFs/results and all 1,025 protected artifacts are
preserved. Verdict B, potentially novel but insufficiently established.

From the project directory:

```powershell
$env:PYTHONUTF8='1'
$env:OMP_NUM_THREADS='1'
.venv/Scripts/python.exe -m unittest clock_regret_attention.test_core clock_regret_attention.test_integration -v
.venv/Scripts/python.exe -m clock_regret_attention.verify
.venv/Scripts/python.exe -m clock_regret_attention.verify_followup
```

The environment snapshot is in `out/clock_regret_attention/environment.txt`;
CPU torch was installed from the official PyTorch index. Reproduction needs
PyTorch, NumPy, the bundled older solver helpers, and ReportLab/Matplotlib/PyMuPDF
only for authoring/figures. Do not run old writeful experiment modules.
`run`, `challenger` and `ablations` recreate this stage's experiments and replace
its current result files; use a separate copy after final freezing.

```python
from fractions import Fraction
from clock_regret_attention.integration import select
r = select([1,2,7], [False,False,True], [2,5,10], [1,30,70],
           epsilon=Fraction(1,10), budget=2)
print(r['selected_age'], r['certified_exact_decision'])
print(r['lower_scores'], r['upper_scores'])
```

Default proposal is sequential greedy. A premium focus is also checked; both
are intersected with the existing FPTAS interval. To substitute a trained
attention proposal, load a checkpoint and pass `learned_selector(model)` as
the `selector` callback. A malformed focus is rejected. A wrong valid focus
cannot invalidate the mathematical interval. The final full-family wrapper is
discrete only; continuous/refinement results remain in the protected solver.

Plans were hashed before their respective computations, not publicly
preregistered. The follow-up ablations were motivated by original held-out
results; the validation choice was saved before generating fresh confirmation.
No real sealed lifetimes entered this training or validation stage.
