# Two attaining worlds replace quadratic failure-count search

This extends the frozen `clock_regret/THEORY.md` formulation. The mathematical model and earlier-versus-later theorem are retained. The result below improves the later-versus-earlier search; the original quadratic formula remains correct but is unnecessarily general.

## Model

There are n positive integer logging endpoints H_i and failure indicators delta_i. Observed failures have L_i=H_i, and censored records have L_i>=H_i+1. A fixed positive integer replacement age d has failure indicator1{L_i<=d}, use min(L_i,d), and cost1+q*failure, where q=rho-1>0 is common. Define the finite-cohort rate R_d=sum(cost)/sum(use). Every policy shares each L_i. The Cartesian set of compatible lifetime completions is the uncertainty model.

These are deterministic finite-cohort certificates, not distributional predictions. No physical lifespan cap is imposed: any unknown L beyond both ages has the same outcomes and can be represented by max(H+1,max(a,b)+1). Fixed ages, common costs and integer clocks remain essential restrictions.

## Theorem 1: exact two-world comparison for a>b

Let M be censored records, E={i in M:H_i<b}, e=|E|, and J={i in M:b<=H_i<a}. Let m=e+|J|. Starting from the completion where every unknown lifetime survives both ages, write C_a^0,C_b^0,T_a^0,T_b^0 for its total costs and uses. Set

```
U = T_a^0 - m*a + e*(b+1) + sum_(i in J)(H_i+1).
D_0 = C_b^0 * U.
D_e = (C_b^0 + q*e) * (U-e).
G(a,b) = (C_a^0+q*m)*T_b^0 / min(D_0,D_e).
```

An attaining world for D_0 makes every asset in E fail at b+1, every asset in J fail at H_i+1, and every other unknown asset survive both ages. An attaining world for D_e makes E fail at b, J fail at H_i+1, and all other unknown assets survive both ages. Observed failures retain their measured times. Ties may use either witness. For e=0 the worlds coincide.

**Proof.** As in the original derivation, a shared failure L<=b can be moved to b without decreasing R_a/R_b: with fixed failure phases the exposure quotient T_b/T_a is nondecreasing in its shared time because T_a>=T_b. A later-only failure b<L<=a can be moved to max(H+1,b+1) because earlier-policy use is fixed while candidate use decreases. These changes leave costs unchanged.

Any unresolved asset eligible to fail by a which still survives both policies can now be moved into the later-only phase. This is compatible precisely when H<a. It increases candidate cost by q, cannot increase candidate use, and leaves earlier-policy cost and use unchanged. Therefore it strictly increases the candidate rate (q>0), so every eligible asset fails by a in an optimum. Assets with H>=a cannot fail by a.

Only the assignment of E remains: each asset either fails at b or b+1. For x shared failures, candidate total cost is the constant C_a^0+q*m, earlier use is the constant T_b^0, earlier cost is C_b^0+q*x, and candidate use is U-x. Identical early-phase contributions make the identities of the x assets irrelevant. Every integer x from0 to e is feasible.

Thus maximizing the quotient is equivalent to minimizing

```
D(x) = (C_b^0+q*x)*(U-x).
D''(x) = -2*q < 0.
```

This positive denominator is concave on [0,e]. For any x in that interval, concavity gives D(x)>=min(D(0),D(e)); integer restriction cannot create a smaller interior value. Both endpoints are feasible, so one of the two stated worlds attains the supremum. Every term is a positive total cost or use, hence no denominator singularity occurs. QED.

The concavity principle is established mathematics. The claimed candidate contribution is its exact reduction of this shared-censored-lifetime quotient to two specific worlds, not discovering concavity or minimax regret.

## Corollary 1: branch condition

For e>0,

```
D_e-D_0 = e * [q*(U-e)-C_b^0].
```

The all-shared-failure world is optimal when q*(U-e)<C_b^0; the no-shared-failure world is optimal when the inequality reverses; at equality both attain. This is an exact criterion from public records, not a fitted parameter or a statistical test. Both branches can occur, especially with high-cost early observed failures. Assuming one universal world is incorrect.

## Theorem 2: full exact selection in O(n log n+K^2 n)

For a<b, retain the earlier theorem. Sort the censored horizons once, let S_x be the sum of H+1 over their first x elements, and e_a their count with H<a. Then

```
G(a,b) = max_(0<=x<=e_a)
[(C_a^0+q*x)*(T_b^0-b*x+S_x)] /
[(C_b^0+q*x)*(T_a^0-a*x+S_x)].
```

This needs at most n+1 rational evaluations per pair and no new sorting. Sort observed failure times once too; prefix sums and binary searches compute their truncated-use and failure-cost totals for each age. A later-versus-earlier pair uses Theorem1 and at most two rational evaluations; G(a,a)=1. Finally W(a)=max_b G(a,b) and the age minimizing W exactly minimizes sup_L R_a(L)/min_b R_b(L), by the finite maximum/supremum identity already established.

Preparation uses O(n log n) arithmetic operations. Summarizing each candidate age costs O(log n); K^2 pairs require at most O(K^2 n) objective operations. Producing an explicit n-element witness for every pair adds O(K^2 n), so the same total bound holds. Without witnesses, prepared storage is O(n+K^2); retaining all witnesses uses O(n+K^2 n). Standalone later-pair computation can aggregate records in O(n), with no sorting.

This is an arithmetic-operation bound. Exact rational comparisons use Python arbitrary-precision cross-products; input bit size affects runtime. Array and prefix-sum arithmetic is guarded against int64 overflow. The computational input range is not a lifespan assumption.

## Scientific meaning and limits

The new algorithm returns the **same exact optima and choices** as the frozen quadratic solver; it improves computation and the structural characterization, not realized maintenance outcomes. Previous synthetic losses and failed transfer cannot be removed by this reduction. A generic endpoint-state optimizer can also reproduce the result, but does not use the two-world theorem. An originality claim must distinguish this specialized structure from established robust and fractional optimization.

This theorem is internally derived and independently numerically checked. Its historical first-in-literature status is a separate empirical literature question, and externally attributable priority requires a public dated record. Neither is established merely by the proof.

## Theorem 3: exact continuous-clock counterpart

Now retain exact integer-valued H and ages but allow compatible real lifetimes L>H. Observed failures remain exactly L=H. For a>b use the same e,m,C_a^0,C_b^0,T_a^0,T_b^0, and define

```
U_c = T_a^0 - m*a + e*b + sum_(i in J)H_i.
G_c(a,b) = (C_a^0+q*m)*T_b^0 / (C_b^0*U_c).
```

For a<b, the earlier sorted-count formula applies with S_x=sum of the x smallest eligible H_i, replacing H_i+1. Equal-age pairs remain1. The same prepared algorithm therefore computes all continuous suprema and the exact finite-policy minimax continuous score in O(n log n+K^2 n) arithmetic operations.

**Proof.** Failure phases and monotonicity arguments still apply. For a>b every eligible asset fails by a. A later-only failure approaches max(H,b) from above. Shared failures can be moved to b. In the closure, moving a shared failure at b to the later-only limiting phase leaves both exposure totals unchanged and reduces comparator cost by q, so cannot decrease the quotient. Hence no shared failure is needed in a continuous maximizer of the closure. This gives the displayed one-world limiting supremum. For a<b, later-only failures are dominated by survival; a shared failure approaches H from above, and the same fixed-count sorting argument applies. Positive exposures keep the quotient continuous within each fixed phase.

To attain the supremum arbitrarily closely, add epsilon in(0,1) to the indicated unknown limiting failure times, retaining their designated failure phases. Integer-valued H and distinct ages have gaps at least one, so this is feasible. Nonselected unknowns can survive both ages. These completions converge to the formulas. If a later pair has m>0, the limiting all-later-only completion itself is not compatible and must not be described as an attained witness. The API distinguishes limiting lifetimes, compatible epsilon approximations and attained cases. QED.

## Theorem 4: uniform clock-refinement and decision bound

Let G_r be the exact integer result after multiplying every H and age by a positive integer r, without changing costs, so the physical clock step is1/r. Let G_c be Theorem3's continuous supremum. Then, for every pair,

```
G_r(a,b) <= G_c(a,b) <= (1+1/r)*G_r(a,b).
```

The same sandwich holds for each W(a)=max_b G(a,b) and its minimum over policies. If a_r minimizes W_r, its continuous robust factor satisfies

```
W_c(a_r) <= (1+1/r)*min_a W_c(a).
```

**Proof.** Grid completions are a subset of continuous completions, giving the first inequality. For a>b the no-shared grid world has candidate use U_c+m/r. It gives G_r >= G_c/(1+m/(r*U_c)). All uses in this limiting world are at least one, so U_c>=n and m<=n, yielding the factor1+1/r. For a<b fix any shared-failure count x. Its continuous exposure totals are A<=B, each at least n. The corresponding grid completion adds x/r to both. The ratio of continuous to grid objectives is

```
[B/A] / [(B+x/r)/(A+x/r)]
 = (1+x/(r*A))/(1+x/(r*B)) <= 1+1/r.
```

Costs and eligible prefix counts are unchanged. Maximizing over counts gives the pairwise upper inequality; maximizing over comparators and minimizing over candidate policies preserve the sandwich. Finally W_c(a_r)<=factor*W_r(a_r)=factor*min W_r<=factor*min W_c. QED.

This is a deterministic resolution error bound for the robust finite-cohort objective. It does not bound future cost or safety. For other physical minimum times tau>0 and step Delta, the corresponding bound is1+Delta/tau; the dimensionless1/r expression uses the stated positive-unit normalization.

Example: four measured failures at time1 and one censored H1, a3,b2,rho2. The integer two-world maximum is1; the continuous supremum is10/9 and is not attained. Refined-grid values approach10/9. This demonstrates that a correct integer certificate does not automatically certify a continuous ambiguity set.
