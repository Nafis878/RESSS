# Internal research record and proposed priority claim

This dossier records a concrete mathematical method, rather than asserting that numerical significance establishes novelty. It is an **internal provenance record**, not a public scientific priority claim. No preprint, DOI registration, repository release or external announcement was made in this work.

## Exact proposed contribution

> An exact quadratic-in-cohort-size ordered failure-phase algorithm for minimax multiplicative finite-cohort replacement cost-rate regret under right-censored integer lifetimes, preserving the shared latent failure time across fixed age policies and returning attaining worst-case lifetime witnesses.

The two pairwise count reductions in [THEORY.md](THEORY.md) are the claim's core. The earlier-versus-later problem reduces to one sorted shared-failure count. The later-versus-earlier problem reduces to two failure counts and a sorted exposure-gain prefix. Enumerating all policy pairs gives O(K^2(n^2+n log n)) arithmetic operations. Common costs, fixed ages and discrete clocks are essential stated restrictions.

## Attribution boundaries

Established ideas used here: age replacement, right-censoring, common potential outcomes, partial identification, minimax relative regret, fractional optimization, endpoint reductions and sorting. Their attribution belongs to the literature in [LITERATURE.md](LITERATURE.md), not this project. The three mathematical results were developed in this project and implemented in `core.py`; their historical originality remains subject to independent review.

No author identities, institutional affiliations, contributions of absent collaborators or prior public dates have been invented. Any future submission needs the actual researchers to review the claims, verify authorship and ensure compliance with the intended venue's disclosure rules.

## Evidence held locally

- Plan recorded before the new experiment run, with its SHA-256 in `out/clock_regret/plan_sha256.txt`. This is not independent preregistration; earlier negative findings motivated the plan.
- Constructive derivations and exact rational implementation; 250 exhaustive full-clock comparisons, 100 generic endpoint-state test comparisons and 120 additional endpoint-state audit comparisons.
- 2,400 independent synthetic cohorts and 304 frozen real replay tasks, including all specified negative comparisons and separated sealed lifetimes.
- Individually sharp same-input rectangle, upper-rate and complete-case baselines; 39,448 stored attaining pairwise witnesses.
- Completed primary-source comparison and explicit novelty attacks, with inspection gaps disclosed.
- Machine-readable hashes and UTC creation time in `out/clock_regret/research_record.json`; verification and full artifact manifest in the same directory.

Hashes support reproducibility and detection of later changes. A timestamp generated on this computer does not independently authenticate an invention date and does not establish public priority.

## Priority assessment

| Question | Established status |
|---|---|
| Is there a concrete implemented mathematical method? | Yes. |
| Does it exactly solve the stated finite-cohort optimization? | Supported by constructive proofs and independent numerical comparisons. |
| Does it differ from the evaluated conventional computations? | Yes; the strict example and experiments demonstrate different scores and choices. |
| Is its general minimax/maintenance principle new? | No; those ideas are established. |
| Has the particular reduction been found in inspected prior work? | No matching result located, with coverage limits disclosed. |
| Is it established as first in the literature? | No. |
| Is there an externally verifiable dated public disclosure? | No. |
| Does it establish better population cost, safety or battery transfer? | No. |

To establish a defensible external priority claim, the next decisive work is specialist review of the exact formulas and a broader equivalence/citation audit, followed by a reviewed, dated public disclosure with correct authorship. Public disclosure would establish a disclosure date, not by itself prove originality. These remaining steps cannot be replaced by local tests, generated names or a private hash manifest.
