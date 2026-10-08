# Retained corrections

The first replay run completed small oracle studies and reached more than 200
engineering cohorts, then failed converting battery unit `b1c24` to an integer.
The original plan assumed numeric unit IDs. This is a public metadata type error,
not a theorem or optimizer failure. No battery decision or sealed battery outcome
was computed under the failed conversion.

The original numeric scenario mapping is retained unchanged. Before any string-ID
scenario decisions, extend it deterministically: for a nonnumeric unit string,
use its UTF-8 SHA-256 digest interpreted as an integer, modulo three. This rule is
fixed before inspecting those scenario outcomes and does not depend on lifetimes.
The original PLAN.md and its hash are preserved. All cohorts, including battery
cohorts and any negative outcomes, remain in the replay.

The initial implementation charged one beta approximation factor at every DP
stage, even when trimming removed no nondominated point. Its completed replay
and stress evidence, together with the original core, are retained under
`out/clock_regret_fleet/initial_conservative_certificate/`. A proved a posteriori
refinement counts only stages that remove a nondominated (Q,s) point. This
changes certificate tightness and possibly the upper-bound-selected decision;
it changes no tolerance, seed, cost scenario or guarantee. The complete fixed
studies are rerun for the final algorithm. Both versions' outcomes remain visible.
