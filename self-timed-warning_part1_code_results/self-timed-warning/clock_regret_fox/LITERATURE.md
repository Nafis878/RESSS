# Full-text comparison: Fox (1966)

Audit date: 8 October 2026. This addendum supersedes only the Fox access-gap
assessment in the preserved earlier audits. **Verdict B remains: potentially
novel, but historical originality and public priority are not established.**

## Source and inspection

Bennett Fox, *Letter to the Editor - Age Replacement with Discounting*,
Operations Research 14(3):533-537 (1966), DOI 10.1287/opre.14.3.533.
The researcher supplied the publisher PDF. Its SHA-256 is
`999868a8805d5ddf55002dbc6c637196cb3763b261cc7766161e8b6457d6b2b7`.
The PDF contains seven pages: a publisher cover, five journal pages, and a
copyright notice. All five relevant journal pages were rendered and visually
inspected, including all five theorems, Lemma 1, equations (1)-(16), the complete
unknown-distribution proof and the references. The scan lacks an article text
layer; automated extraction yielded only the cover and download notices.
The visual inspection, rather than that extraction, supports this comparison.
Page 533 begins with another author's preceding letter; page 537 ends with a
different replacement letter. Neither is attributed to Fox.

## What Fox actually establishes

Fox uses planned cost c1 and failure cost c2, with 0<c1<c2. Stages repeat after
replacement, the planning horizon is infinite, and a fixed stationary age is
used. A positive continuous discount rate alpha discounts each replacement cost.
For a known continuous lifetime distribution F, his equations (3)-(5) give

```
phi(a) = c1*exp(-alpha*a)*(1-F(a))
         + c2*integral_[0,a] exp(-alpha*x) dF(x)
delta(a) = exp(-alpha*a)*(1-F(a))
           + integral_[0,a] exp(-alpha*x) dF(x)
R(a,F) = phi(a)/(1-delta(a)).
```

This quotient is the expected discounted renewal cost from a geometric renewal
equation. It is not a ratio of one policy's rate to a comparator policy's rate.
The known-distribution section assumes a continuous failure rate increasing
strictly to infinity for Theorems 1, 2 and 4.

| Result | Inspected statement and scope | Relation to our proposed result |
|---|---|---|
| Theorem 1, pp.534-535 | Finite unique optimal discounted age and its hazard first-order condition | Known-distribution scalar optimization; no censored-cohort extremal worlds |
| Theorem 2, p.535 | Finite-stage value recursion; computed ages approach the infinite-stage optimum, with a stopping criterion | Convergence across numbers of renewal stages, not an exact pairwise regret scan |
| Theorem 3, pp.535-536 | As alpha decreases to zero, alpha times discounted risk converges to long-run average cost; also a statement for optimized risk | Discount approximation is established; it is not a clock-mesh bound |
| Theorem 4 and Lemma 1, p.536 | Optimal discounted ages converge to the unique average-cost optimum under the hazard condition | Optimizer convergence under discount removal, not a sharp 1+1/r resolution factor |
| Theorem 5, p.537 | Replacing only on failure is minimax for absolute discounted risk over a fixed-Laplace-transform class, and absolute average cost over a fixed-mean class; also for the corresponding nondecreasing-hazard subclasses | Minimax age replacement is established prior art; no oracle-relative finite-cohort theorem is stated |

Theorem 5's ambiguity sets are important. The discounted class fixes alpha>0
and nu in (0,1), and requires integral exp(-alpha*x) dF(x)=nu. The average-cost
class fixes the lifetime mean mu. They are not simply all lifetime laws with no
information. The discounted proof uses the exponential law with mean
(1-nu)/(alpha*nu). Failure-only risk is c2*nu/(1-nu) for every law in the first
class, and failure-only also minimizes risk under the exponential witness. The
minimax inequality chain therefore closes at that value. The average-cost
proof is credited to Barlow and Proschan (1965), p.91, and adapted to discounting.
This argument does not use right-censored record bounds, a finite shared cohort,
cardinality concavity or a premium-prefix denominator.

Equation (15) gives the familiar average renewal rate

```
S(a,F) = [c1*(1-F(a)) + c2*F(a)] / integral_[0,a] (1-F(x)) dx.
```

Our total-cost/total-use structure must therefore not be portrayed as a new
renewal-cost principle. Fox also mentions sequential adaptation and cites his
1965 technical report *An Adaptive Age Replacement Policy*. That report is a
bibliographic pointer, not a full text inspected in this addendum.

## Direct comparison of the optimization problems

| Feature | Fox's minimax theorem | Our exact cohort comparison |
|---|---|---|
| Uncertain object | A common probability law F constrained by a mean or Laplace transform | One compatible lifetime L_i for each observed or censored record |
| Criterion | Absolute expected discounted risk or long-run average cost | Supremum of R_a(L)/R_b(L), then minimization against a finite oracle family |
| Information | Distributional summary constraint; no given record vector | Observed failures fixed at H_i; censored L_i>H_i, or L_i>=H_i+1 on an integer clock |
| Extremal construction | Exponential law closes an absolute-cost minimax inequality chain | Explicit lifetime worlds; a cardinality minimum, or a sorted-premium scan |
| Time parameter | Discount rate alpha; continuous replacement age | Recorded time and clock refinement r; optional continuous latent completions |
| Cost heterogeneity | Common c1,c2 in this letter | Common costs or positive asset-specific failure premiums |

Sharing uncertainty is not itself a novelty claim. Neither a quotient nor the
appearance of an extremal witness suffices to make two methods equivalent.
The inspected Fox statements do not state our common-cost two-world theorem,
heterogeneous premium-prefix theorem, or sharp pairwise clock factor. This
closes the specific Fox full-text gap and supports separation of these precise
formulations; it does not prove that those results cannot be derived from other
existing mathematics.

## Checked separating example

Use planned cost one and failure cost two. A fully observed single cohort record
with lifetime 10 and candidate ages {8,20} has rates 1/8 and 2/10. Its oracle-
relative scores are exactly 1 and 8/5, so age 8 is selected. There is no lifetime
uncertainty in this cohort example.

In Fox's fixed-mean class with mu=10, failure-only is minimax with average rate
2/10. The exponential law of mean 10 gives any finite age a the rate
`(2-exp(-a/10))/(10*(1-exp(-a/10)))`, which is strictly above 2/10.
This demonstrates differing decisions under the respective uncertainty sets and
criteria. It is not an empirical comparison on a common problem, a superiority
claim, or an independent proof of historical originality.

`comparison_examples.json` records exact cohort ratios, an exact discounted
exponential specialization of Fox's equation (5), and the already proved strict
interior heterogeneous example. The latter is checked again by full enumeration,
not only by the prefix formula. No new statistical significance claim is needed:
these are deterministic identities and formulation comparisons.

## Current novelty and priority assessment

**The Fox gap is closed.** One previously identified material full-manuscript
gap remains: Sina Shahri Majarshin's 2026 LNMB abstract, *A robust age-based
replacement problem*. Its moment-constrained, absolute-cost formulation was
compared from the primary abstract, but the full proof manuscript has not been
located. The separate robust MDP journal article is not that manuscript.

The present specialized theorems remain mathematically supported candidates.
The assessment is not an automatic promotion to established novelty because
one old paper differs. Literature coverage, independent specialist assessment
and first-in-literature priority remain distinct issues. No public deposit or
external review has occurred. Authorship is attributed to Nafis Wadud Ansari,
Daffodil International University; the intended public destination is pending.
A future deposit can create a verifiable public disclosure record, but cannot
by itself prove historical firstness.

The new Markdown manuscript incorporates this comparison and corrects the proof
file pointers. The earlier PDFs and all prior results remain preserved; they do
not contain this later addendum. The source PDF and its rendered pages are
private research material and are not placed in a public review archive.
