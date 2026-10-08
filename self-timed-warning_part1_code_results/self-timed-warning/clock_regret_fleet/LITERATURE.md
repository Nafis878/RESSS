# Mechanism-level audit of the complete heterogeneous selector

8 October 2026. Read with the preserved Fox addendum and earlier primary-source
audits. This audit explicitly attempts to disprove broad novelty claims.

## Closest computational prior art

**Mittal and Schulz (2008), A General Framework for Designing Approximation
Schemes for Combinatorial Optimization Problems with Many Objectives Combined
into One**, APPROX/RANDOM, LNCS 5171:179-192. The primary
[author PDF](https://web.mit.edu/schulz/www/epapers/ms-approx-2008.pdf) was inspected
for its formulation, approximate-Pareto construction and approximation theorem.
It combines objectives via norms and obtains FPTAS results for resource
allocation/scheduling. It establishes the general strategy of using approximate
Pareto frontiers to optimize aggregate objectives. It does not formulate the
present censored-cohort cost/use quotient, but invalidates a claim that this
project invented multiobjective approximation or DP-state compression.

**Herzel, Bazgan, Ruzika, Thielen and Vanderpooten, One-Exact Approximate Pareto
Sets**, 2019 preprint, Journal of Global Optimization 80:87-115 (2021).
The full primary [arXiv HTML](https://arxiv.org/html/1908.10561v1) was inspected
for Section 3, Theorem 3.1 and its hyperstripe proof, and the algorithmic
conditions and discussion of dynamic-programming methods. The
[published record](https://link.springer.com/article/10.1007/s10898-020-00951-7)
confirms the journal version. The theorem retains the minimum first objective
inside multiplicative stripes in the other objectives. This directly overlaps
our generic keep-smallest-exposure-in-premium-bucket idea. Counting favorable
one-sided approximation as a wholly new decision mechanism is rejected.
The specialized reduction and its scalar rate-ratio bound still need separate
assessment; a new maintenance application does not erase this overlap.

Papadimitriou and Yannakakis (2000) and Woeginger (2000) are foundational
bibliographic antecedents cited by the inspected author paper. Their originals
were not separately read in full here; this audit does not imply otherwise.

## Comparison with maintenance and regret prior art

Fox's supplied five-theorem letter has now been compared in full in
`clock_regret_fox/LITERATURE.md`: fixed-mean/Laplace-transform ambiguity,
absolute renewal cost, exponential minimax witness. Shared-world relative
objectives are already present in the inspected Zhu-Zhang-Ye newsvendor report
and robust baseline-regret work of Petrik et al. Bayesian censored replacement
learning is already present in the inspected Drent et al. preprint. They do not
state the present specialized F1-F4 formulas in the sections inspected.

The primary [LNMB abstract](https://www.lnmb.nl/conferences/2026/abstracts.html)
for Shahri Majarshin's *A robust age-based replacement problem* remains the
identified full-proof access gap. It concerns first/second-moment distributional
ambiguity and absolute long-run cost with a two-point extremal distribution.
The new search did not recover its full manuscript. The separate robust MDP
article must not be substituted for it. Unpublished work and terminology
coverage remain additional limits.

## Actual searches before and after implementation

- `"age replacement" "minimax regret" "heterogeneous" approximation`
- `"relative regret" "replacement" "censored" approximation`
- `approximate Pareto curves subset selection cardinality fully polynomial approximation Papadimitriou Yannakakis`
- `"age replacement" "approximation scheme" regret`
- `"maintenance" "multiplicative regret" censored`
- `"A robust age-based replacement problem" "Majarshin" manuscript`
- `"A General Framework for Designing" "FPTAS" nonlinear Mittal Schulz`
- `"regret" "FPTAS" "fractional" optimization`
- `"minimax regret" "replacement" "approximation" censored`
- `"cost-rate" "Pareto" replacement regret`
- `"censored" "replacement" "FPTAS"`
- `"age replacement" "Pareto" "regret"`
- `"minimax relative regret" "heterogeneous" maintenance`
- `"minimax" "censored" "cost rate" replacement`

Narrow search silence is not evidence of novelty. Only relevant primary papers
support the technical comparisons; irrelevant search matches are not evidence.

## Gate and claim boundary

| Candidate claim | Assessment |
|---|---|
| A new Pareto/FPTAS principle | Rejected: substantial general-mechanism prior art |
| A new minimax or oracle-relative objective | Rejected: broad objective is established |
| Complete heterogeneous selection for the specific shared censored-cohort quotient | Constructively derived F1-F3; independent oracles and complete replay support correctness; proposed specialized contribution |
| Joint clock/tolerance guarantee and actual-loss-stage certificate | Derived for this model; standard composition and trimming ingredients must be attributed |
| A broadly superior engineering maintenance policy | Rejected by available evidence: 5 wins, 8 losses, 291 ties; slightly worse mean realized scenario regret |
| Exact polynomial heterogeneous selection or NP-hardness | Neither is proved; do not claim either |
| Solid 9/10 originality or established first priority | Not supported by the completed audit |

The work is a meaningful extension of the existing project, with mathematically
proved approximation control, complete heterogeneous policy selection and exact
decision certification when intervals separate. The closest generic methods can
reproduce the approximation strategy once the subset reduction is supplied.
Consequently the strength of a claim rests on that specialized reduction,
guarantees and engineering relevance, not on renaming the DP.

**Verdict B: potentially novel but insufficiently established.** It is not
scientifically defensible to turn the desired score into a conclusion. The
extension strengthens the mathematical submission, but measured consequence
data, a convincing substantive engineering advantage and the remaining
equivalence check are still absent. A local timestamp or deposit would not
resolve those issues. No external review or public release occurred.
