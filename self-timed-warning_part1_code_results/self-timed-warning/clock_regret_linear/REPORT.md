# Completed result and novelty decision

The project now has a concrete mathematical and computational contribution:
an exact two-world characterization of later-versus-earlier replacement regret,
an exact complete-family solver, a continuous-clock supremum, and a uniform
clock-refinement guarantee. The derivations and constructive witnesses are in
`THEORY.md`; the working paper is `MANUSCRIPT.md` and the companion PDF.

**Decision: B - potentially novel, supported by correctness evidence, but not
yet established as globally original or historically first.** This is stronger
than the previous unsuccessful broad novelty claims. The specialized statements
were not located in the inspected literature. Coupled uncertainty, robust
replacement, minimax regret and concavity are established techniques. The
literature matrix records close work and remaining access gaps. Statistical
significance cannot settle historical priority.

## What was established

For a later age, every eligible censored asset may be made to fail by that age.
The remaining denominator is a positive concave quadratic in the number of
shared failures. Only the two endpoint worlds need evaluation. The converse
age ordering needs a sorted-prefix count scan, with a demonstrated interior
optimum. Together these give **O(n log n + K^2 n)** arithmetic operations,
including generation of all pairwise witnesses, compared with the quadratic
per-pair predecessor. Standalone later-pair computation is O(n).

Under continuous latent clocks, one no-shared limiting world suffices for a
later comparison. An explicit epsilon completion approaches the supremum without
mislabeling a boundary limit as a compatible observed lifetime. Refining the
integer clock by r gives **G_r <= G_c <= (1+1/r)G_r** for every pair and the
same approximation factor for the continuous objective of the grid-selected
policy. This concerns exact recorded horizons and fixed ages, rather than
measurement error or a future-population guarantee.

## Completed validation and statistical results

- 15 unit-test groups, including 1,000 full-clock exhaustive cases, 500 independent
  endpoint-state cases and 300 larger predecessor comparisons.
- All 39,448 frozen pairwise optima and all 2,704 original cohort selections
  reproduced exactly, with explicit attaining integer witnesses.
- 300 continuous phase-labeled optimizer comparisons and compatible epsilon
  completion checks; 1,500 full-family refinement tasks on 300 independent cohorts.
- 84 independent timing inputs, with three repeated timings per input. All seven
  size contrasts favor the new later-pair implementation: two-sided sign-test
  raw p=0.00048828125, Holm p=0.00341796875. Median paired speed ratios range
  from 2.88 at n=16 to 2,007.09 at n=1,024. These are comparisons with the frozen
  implementation, which also checks witnesses internally.
- 120 separate general-state diagnostic comparisons agree exactly. Earlier-pair
  small-input diagnostics are slower than the predecessor, so no universal
  timing superiority is asserted.
- The final verifier checks stored witnesses, exact objectives, test calculations,
  refinement inequalities, plan hashes, archive contents and all 858 protected
  earlier artifacts. The accompanying JSON records the actual final result.

The timing sample count was amended from 8 to 12 before observations because
the minimum attainable eight-input two-sided p-value could not pass the first
Holm threshold. The continuous extension was planned after the integer work;
its plan is a development record, rather than a preregistration. An impossible
equal-age phase in the independent continuous checker was corrected, retained
in the development log and covered by a regression test.

## Empirical scope and scientific priority

All original integer policy choices are unchanged. Earlier mixed synthetic
performance, increased short-life risk in some comparisons, absence of primary
real-domain significant superiority and no Battery LOBO improvement remain in
the research record. The new result is a computational and model-resolution
contribution, rather than evidence that those limitations disappeared.

The method assumes a finite policy pool, common costs and Cartesian compatible
lifetimes. Future interventions, sensor policies, heterogeneous costs, joint
physical constraints and noisy failure labels require additional theory.

A five-page manuscript, proof, source, statistics, figures, literature audit and
hashed internal review archive have been prepared. **Public priority is still
pending actual author names, affiliations, an intended repository/preprint
account, and release rights.** No public deposit, DOI, accepted-paper status or
invented authorship is claimed. A dated public disclosure can establish a
verifiable disclosure record; independent prior-art assessment is still needed
to establish originality. See `PRIORITY.md` for the precise prepared claim.
