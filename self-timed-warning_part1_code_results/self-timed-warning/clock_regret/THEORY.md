# Exact finite-cohort relative regret under shared censored lifetimes

The derivations below were developed in this project. Correctness is supported by proofs and independent numerical checks. **Priority for the specific reduction remains a literature question.** Age replacement, partial identification, minimax relative regret, and generic fractional optimization are established ideas.

## Model and scope

There are n>0 assets and K positive integer replacement ages d_k. A public logging record is (H_i,delta_i), where H_i>=1 is an integer and delta_i=1 denotes an observed failure. If delta_i=1, lifetime L_i=H_i; otherwise L_i>=H_i+1. Every policy on asset i uses **the same** L_i. Unknown lifetimes need not have a common probability distribution, independent censoring, bounded support, or finite population mean. The Cartesian completion set is the model; additional dependence or degradation constraints may shrink it and change sharpness.

For age d and common cost ratio rho>1, failure F_i(d)=1{L_i<=d}, use T_i(d)=min(L_i,d), and cost C_i(d)=1+(rho-1)F_i(d). Failure at a scheduled deadline is charged as failure. The finite-cohort rate is R_d(L)=sum_i C_i(d)/sum_i T_i(d)>0. This is not E[C/T] or a future-population renewal theorem.

Fixed ages may be conventional policies chosen on other data or deadlines already committed before truncation. Future sensor-triggered alarms, asset-specific varying deadlines, heterogeneous failure costs and continuous clocks are not covered by the implemented theorem. Current code accepts positive integer rho for exact rational arithmetic; the mathematical formulas apply to a common real rho>1.

Define G(a,b)=sup_{L compatible} R_a(L)/R_b(L). The selector minimizes W(a)=max_b G(a,b). Relative regret above the oracle is W(a)-1; throughout the artifacts the stored factor includes the leading one. This is a finite-cohort robust recommendation, not a promise that the selected policy can recover lifetimes of equipment already removed.

## Lemma 1: no lifespan cap is needed

For any pair a,b, every unknown lifetime above max(a,b) gives the same pair of outcomes. Replace such a lifetime by max(H_i+1,max(a,b)+1); it remains compatible and leaves both outcomes unchanged. Thus the unbounded completion set has a finite outcome representation without assuming an upper bound on physical life. Known failures retain their exact recorded lifetimes even if above both ages. The same statement holds for a finite policy family using its largest age.

## Notation for the joint-survival completion

Let M be unknown assets. Set each unknown lifetime above both ages, leaving observed failures fixed. Call the resulting totals C_a^0,C_b^0,T_a^0,T_b^0. These are computable from public records: known assets contribute their exact age-policy outcomes, unknown assets contribute cost1 and uses a,b respectively. Write q=rho-1. Changing an unknown lifetime into a failure adds q to the corresponding cost total.

## Theorem 1: exact earlier-versus-later comparison

Suppose a<b. Let E={i in M:H_i<a}. Sort its logger horizons increasingly as h_(1),...,h_(e), and S_x=sum_{i=1}^x(h_(i)+1), S_0=0. Then

```
G(a,b) = max_{0<=x<=e}
 [(C_a^0+qx)*(T_b^0-bx+S_x)] /
 [(C_b^0+qx)*(T_a^0-ax+S_x)].
```

An attaining witness fails the x selected assets at h_(i)+1 and makes all other unknown assets survive both ages.

**Proof.** An unknown lifetime is in one of three phases: both policies fail (L<=a), only b fails (a<L<=b), or both survive (L>b). Replace any b-only failure by joint survival: policy a is unchanged; b's cost decreases and its use cannot decrease. Hence R_a/R_b cannot decrease. Such failures are unnecessary in a maximizer.

For a shared failure, holding all other lifetimes and failure indicators fixed, its time t is added to both exposure totals. Because a<b, total T_a<=T_b for every completion, so (T_b_other+t)/(T_a_other+t) is nonincreasing in t. Choose the smallest compatible t=H_i+1. Only assets in E can fail by a.

At a fixed shared-failure count x, both total costs depend only on x. The exposure difference is T_b^0-T_a^0-x(b-a)>=0, independent of which assets fail. Maximizing the exposure ratio is therefore achieved by minimizing T_a, equivalently minimizing the sum of the selected H_i+1. The x smallest eligible horizons accomplish that. Substitution gives the displayed formula. Each extremum has an admissible explicit completion, proving both the upper bound and sharpness. If the exposure difference is zero, any eligible subset attains the same ratio and the sorted witness is still valid. □

Sorting costs O(n log n); the e+1 exact ratio evaluations cost O(n).

## Theorem 2: exact later-versus-earlier comparison

Suppose a>b. Let E={i in M:H_i<b}, e=|E|; let J={i in M:b<=H_i<a}. Form a gain list: first e identical values a-b-1 corresponding to E, followed by gains a-H_i-1 for J in decreasing order. Every gain is nonnegative and the initial gains are at least as large as the later ones. Let m=e+|J| and P_s be the sum of the first s gains, P_0=0. Then

```
G(a,b) = max_{0<=x<=e, 0<=y<=m-x}
 [(C_a^0+q(x+y))*T_b^0] /
 [(C_b^0+qx)*(T_a^0-x(a-b)-(P_(x+y)-P_x))].
```

An attaining witness chooses x assets in E to fail at b; the y best remaining gain assets fail at max(H_i+1,b+1); other unknown assets survive both ages.

**Proof.** The phases are shared failure L<=b, a-only failure b<L<=a, and joint survival L>a. In the shared-failure phase, the exposure quotient is (T_b_other+t)/(T_a_other+t). Now T_a>=T_b for every compatible world, so it is nondecreasing in t. Choose its largest phase time b. That is feasible precisely for E.

In the a-only phase, T_b is fixed at b and T_a includes t. Choose the smallest phase time max(H_i+1,b+1), feasible precisely in E or J. Relative to joint survival, a shared failure reduces T_a by a-b, while an a-only failure reduces it by its listed gain. **Neither changes T_b**, because each now has use b under the earlier policy. The known assets are untouched. For fixed phase counts x,y the cost totals are C_a^0+q(x+y), C_b^0+qx and T_b=T_b^0. Maximizing the ratio means minimizing T_a.

Every eligible shared-failure asset has the same a-only gain a-b-1. Reserve any x of those assets. The largest y gains remaining maximize total exposure reduction. With the stated stable ordering this sum is P_(x+y)-P_x. Every combination in the displayed count range is attainable and every denominator remains strictly positive. The proposed witnesses attain the resulting maxima, proving sharpness. □

The search has at most (e+1)(m+1) count cases. Sorting and prefix sums plus the count enumeration take O(n log n+n^2). No approximation grid, numerical tolerance, LP relaxation or simulation-based search enters the implemented rational result.

## Theorem 3: exact minimax policy choice

For a finite set of fixed ages,

```
sup_L [R_a(L)/min_b R_b(L)]
 = sup_L max_b [R_a(L)/R_b(L)]
 = max_b sup_L [R_a(L)/R_b(L)] = W(a).
```

The second equality exchanges a supremum with a finite maximum. Set G(a,a)=1, compute every pair using Theorems1–2, and choose the smallest W(a), breaking exact ties by the earliest age. The selected policy therefore minimizes the **exact** worst-case multiplicative finite-cohort regret over the specified candidate set. Witnesses certify every pairwise optimum; a witness for a maximizing comparator certifies W(a).

The overall running-time bound is O(K^2(n^2+n log n)). Per-pair working arrays are O(n); retaining all K^2 witnesses uses O(K^2 n). This arithmetic-operation bound does not make integer bit complexity constant: Python integers and exact fractions grow with input magnitude. The implementation rejects inputs if n*(max(H,ages,rho)+1) exceeds int64 capacity, preventing overflow in clock arrays and prefix sums; this is a computational range restriction, not an upper bound on physical lifetime. Fraction cross-products use arbitrary-precision integers. The theorem is deterministic and does not require independence among assets. Statistical comparisons of experiments separately require a valid sampling design.

## Established comparator and strict difference

For one age d, let O be known outcomes (logger failure or H_i>=d), C_O,T_O their totals, and U the unresolved assets. The individually sharp endpoints are

```
lower_d = (C_O+|U|)/(T_O+|U|*d)
upper_d = (C_O+rho*|U|)/(T_O+sum_(i in U)(H_i+1)).
```

The first is attained by joint survival at d; the second by failures at the earliest compatible times. An independent marginal rectangle uses upper_a/lower_b for a!=b and1 for identical policies. This can combine incompatible clock worlds. The new paired maxima respect those clocks, so G(a,b)<=upper_a/lower_b. The comparison uses **the same public input and individually sharp marginals**, not additional labels or weaker cap bounds.

Example: twelve censored assets with H=6, rho20, candidate ages8,12,16,24. All marginal upper rates equal20/7. The rectangle selector chooses age24 with its tied-world score20*16/7. The exact selector chooses age8 with exact worst factor3. The exact worst factor of age24 is20*16/17, about18.824. Compatible clocks cannot make age24 fail at7 while age16 survives to16 on those same assets. This is a method-distinguishing case, not evidence that age8 has lower average cost under every lifetime law.

## Scope attacks and unsupported extensions

This is an exact optimization algorithm for a particular finite-cohort ambiguity set. It does not identify a population survival curve, certify future failure probability, guarantee mean-cost superiority, solve arbitrary sensor-triggered policy arbitration, control physical interventions, or prove transfer across battery batches. Common rho and constant ordered ages are essential to the count reduction. Asset-specific deadlines can destroy the ordering arguments; heterogeneous failure costs destroy count-only cost totals. Continuous clocks change the strict-boundary cases and may yield only suprema. Those extensions need new proofs and cannot be advertised as completed.

Exactness is not priority. General robust optimization, minimax regret, shared potential outcomes and fractional programming are prior art. The defensible candidate contribution is the particular ordered failure-phase/count reduction with sharp witnesses and its quadratic search for these coupled censored renewal-rate ratios. Its first-in-literature status requires the accompanying audit and independent scrutiny.
