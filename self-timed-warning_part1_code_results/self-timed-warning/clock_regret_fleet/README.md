# Certified heterogeneous-fleet replacement

The new implementation completes heterogeneous-cost policy selection with an
FPTAS, a score interval for every age, and an exact-decision certificate when
intervals separate. It preserves all 974 earlier artifacts. It does not establish
9/10 originality, public priority or superior realized maintenance performance.

Read THEORY.md, LITERATURE.md, REVIEW.md and REPORT.md. The PDF and reproducible
evidence are under `out/clock_regret_fleet/`; the PDF is a new draft, rather than
an edit to the earlier open manuscript. Authorship uses the researcher's supplied
name, affiliation and email.

From the project root with the existing environment:

```powershell
.venv/Scripts/python.exe -m unittest clock_regret_fleet.test_core -v
.venv/Scripts/python.exe -m clock_regret_fleet.run
.venv/Scripts/python.exe -m clock_regret_fleet.report
.venv/Scripts/python.exe -m clock_regret_fleet.verify
```

These are research reproduction commands. PDF authoring requires the PDF skill's
artifact marker immediately before the first authoring command, and visual QA
after rebuilding. Do not run old writeful experiment/report modules: prior
outputs are protected. Standalone review-archive tests need Python, NumPy and
the bundled pure helper modules; full workspace integrity checks require the
preserved workspace. The archive contains the three frozen engineering CSV
inputs needed for scenario replay, not third-party full-text papers.

```python
from fractions import Fraction
from clock_regret_fleet.core import select
answer = select([1,2,7], [False,False,True], [2,5,10],
                [1,30,70], epsilon=Fraction(1,10))
print(answer['selected_age'], answer['lower_scores'], answer['upper_scores'])
print(answer['certified_exact_decision'])
```

Exact rational premiums and tolerances are required; floating point values are
rejected. Clock times and candidate ages use the existing guarded positive
integer input range. `exact=True` keeps full Pareto frontiers and can be
exponential. `continuous=True` computes closure bounds and labels approach
indices; `pair.completion()` supplies a compatible epsilon-time completion.
Approximate decisions have factor 1+epsilon for the deterministic cohort
objective; real continuous-time refinement adds factor 1+1/r. Neither predicts
future safety. Preventive cost remains one; this is not arbitrary preventive
cost, downtime or a dynamic intervention model.

The initial conservative certificate and all its completed results remain in
`initial_conservative_certificate/`. The final actual-loss-stage certificate
is proved before interpreting its replay. Planned seeds, tolerances and cost
scenarios are unchanged; both versions' negative engineering findings remain.
