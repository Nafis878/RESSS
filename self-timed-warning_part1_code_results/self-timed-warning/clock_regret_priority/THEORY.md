# Exact later-age regret with heterogeneous failure premiums

This extends the previously proved common-cost result. It establishes an exact
comparison theorem, rather than a general full-family heterogeneous-cost solver.

## Model and theorem H1

For asset i, preventive cost is one and failure cost is 1+q_i, with known
positive rational q_i. Retain integer H_i>=1, observed L_i=H_i, and censored
L_i>=H_i+1. All policies use the same compatible L_i. Define R_d(L) by total
cost divided by total use, and G(a,b)=sup_L R_a(L)/R_b(L).

For a>b, let E={unknown i:H_i<b}, J={unknown i:b<=H_i<a}, e=|E|, m=e+|J|.
Write baseline costs C_a0,C_b0 and uses T_a0,T_b0 when every unknown survives
both ages. Sort E by nondecreasing q_i and let Q_x be the sum of its x smallest
premiums, Q_0=0. Then

```
U = T_a0 - m*a + e*(b+1) + sum_(i in J)(H_i+1)
A = C_a0 + sum_(i in E union J)q_i
D_x = (C_b0+Q_x)*(U-x), for 0<=x<=e
G(a,b) = A*T_b0 / min_x D_x
```

An attaining completion makes the x selected cheapest assets in E fail at b,
the remaining E fail at b+1, J fail at H_i+1, and all other unknowns survive
both ages. Observed failures remain measured. Ties in premium or denominator
are resolved deterministically. The standalone algorithm uses O(n log n)
arithmetic operations, O(n) storage, and e+1 exact objective evaluations.

**Proof.** With failure phases fixed, a shared failure may be moved to b without
decreasing the exposure quotient T_b/T_a, because T_a>=T_b. A later-only failure
may be moved to max(H_i+1,b+1). Any eligible survivor may enter the later-only
phase: candidate cost increases by its strictly positive q_i, candidate use
cannot increase, and comparator cost and use remain unchanged. Thus all m
eligible assets fail by a at an optimum, so candidate cost A and comparator use
T_b0 are fixed. If a subset S of E fails at b, candidate use is U-|S| and
comparator cost is C_b0+sum_(i in S)q_i. At a fixed |S|=x, minimizing the
positive denominator requires the x smallest q_i. Every count is feasible.
Scanning its sorted premiums proves the formula and constructs an attaining
completion. QED.

## Common costs are an essential two-world assumption

When all q_i=q, Q_x=q*x and D_x is a positive concave quadratic. Its minimum
is at x=0 or x=e, recovering the existing two-world theorem.

With varying q_i, an interior minimum is possible. Take H=(1,1,1), observed
flags=(true,false,false), premiums=(98,1,100), a=3, b=2. Here C_a0=C_b0=101,
T_a0=7, T_b0=5, U=7, A=202, e=2. The three denominators are

```
D_0=707, D_1=612, D_2=1010.
G=1010/612=505/306.
```

The unique optimal shared count is one, with completion (1,2,3). Using only
zero or all shared failures gives max(1010/707,1010/1010)=1010/707, which is
strictly smaller. Thus extending the common-cost two-world rule unchanged to
heterogeneous costs is incorrect. The sorted-premium scan repairs it exactly.
This is an assumption-boundary result with a concrete failure mode; no
real-dataset performance advantage is inferred from this constructed example.

## Theorem H2: continuous limit and sharp clock-factor bound

Retain integer-valued H and ages but allow compatible real unknown lifetimes
L_i>H_i. Set

```
U_c = T_a0 - m*a + e*b + sum_(i in J)H_i
G_c(a,b) = A*T_b0/(C_b0*U_c).
```

This is the exact continuous supremum, with one no-shared limiting completion:
each eligible unknown approaches max(H_i,b) from above. If m>0 it is unattained;
otherwise the generated completion attains it. Adding epsilon in (0,1) to
the eligible limiting times gives compatible completions converging to G_c.

**Proof.** The H1 phase arguments still apply. In the closure, replacing a shared
failure at b with a later-only limiting failure at b leaves both uses unchanged
and reduces comparator cost by q_i>0. Hence all eligible failures may be later
only. Their limiting times give U_c and the formula. Integer-valued H and ages
leave a gap of at least one, so the stated epsilon sequence preserves phases.
Any compatible selected lifetime has strictly larger candidate use than its
limit, proving nonattainment when m>0. QED.

For an integer refinement factor r>=1, multiply every H and age by r, retaining
the premiums. The exact grid factor G_r satisfies

```
G_r <= G_c <= (1+1/r)*G_r, for a>b.
```

**Proof.** Compatible physical grid lifetimes are continuous completions, proving
the first inequality. The no-shared grid world uses U_c+m/r and has ratio
G_c/(1+m/(r*U_c)). Since U_c>=n and m<=n, this gives the upper factor. QED.

The constant is sharp for this pairwise bound. With every asset censored at
H_i=1, ages a=2,b=1 and arbitrary positive premiums, e=0,m=n,U_c=n.
Writing Q=sum_i q_i gives G_c=(n+Q)/n and G_r=(n+Q)/(n*(1+1/r)). Therefore
G_c/G_r=1+1/r exactly. Even the common-cost subclass attains the bound.
This proves sharpness of the uniform pairwise factor, not sharpness of a
full-family selected-policy bound or a future-population guarantee.

## Scientific interpretation

The extension removes a common failure-cost restriction for later-versus-earlier
comparisons, characterizes where the two-world formula fails, retains an exact
continuous limit, and proves that the uniform resolution constant cannot be
improved for all pairs. Sorting, exchange arguments, fractional objectives and
concavity are standard mathematical ingredients. Historical originality of
these specialized statements still requires a theorem-level prior-art assessment.
