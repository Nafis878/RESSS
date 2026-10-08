# Certified focus search and limits of attention-based omission

The finite-cohort model and positive rational premiums are unchanged. For a<b,
the earlier exact reduction has eligible censored assets E={i:H_i<a}, baseline
C_a<=C_b,T_a,T_b with every unresolved asset surviving both ages, and subset
objective

```
f(S) = (C_a+Q(S))*(T_b-b*|S|+s(S)) /
       ((C_b+Q(S))*(T_a-a*|S|+s(S))),
s(S)=sum_(i in S)(H_i+1).
```

All costs and uses retain every asset. A focus set F subset E permits exact
enumeration only of S subset F. It may be selected by attention, an MLP, a
deterministic rule or an adversary. Let g_F=max_(S subset F) f(S), and
Q_tail=sum_(i in E minus F) q_i. Define

```
kappa_F = ((C_a+Q_tail)*C_b)/(C_a*(C_b+Q_tail)).
g_F <= G(a,b) <= kappa_F*g_F.
```

## Theorem A1: a selector-independent certificate

The interval above is valid for every focus set. A compatible witness attains
g_F. The bound is deterministic and holds even if attention has no predictive
skill, is miscalibrated or changes under distribution shift. It is not a
probabilistic confidence interval or a statement about future failure risk.

**Proof.** Consider a true maximizing subset S, and let S_F=S intersect F and
S_tail=S minus F. Starting from the world for S_F, add tail shared failures
one at a time at times t=H_i+1<=a. This replaces uses (a,b) by (t,t). Before
each addition the total exposure ratio B/A is at most b/a, because every
asset has min(L,b)<=b*min(L,a)/a. For t<a, the removed-use ratio
(b-t)/(a-t)>=b/a; subtracting that pair cannot increase B/A. For t=a, only
B decreases, with the same conclusion. Thus adding tail shared failures can
only decrease the exposure factor.

Write x=Q(S_F) and y=Q(S_tail). The change in the cost quotient is

```
K(x,y) = ((C_a+x+y)*(C_b+x))/((C_b+x+y)*(C_a+x)).
```

It increases in y>=0 and decreases in x>=0 when C_b>=C_a. For example
`K=1+y*(C_b-C_a)/((C_a+x)*(C_b+x+y))` makes both statements immediate.
Hence f(S)<=K(x,y)*f(S_F)<=K(0,Q_tail)*g_F. Maximizing over S gives the
upper bound. Every focused subset is a true feasible subset, giving the
lower bound and an attaining completion. QED.

In particular kappa=1 if no eligible premium is omitted or C_a=C_b. If there
are no known failures between a and b, C_a=C_b; the empty shared-failure subset
already maximizes the exposure factor, and no attention is needed for this pair.
Later-versus-earlier pairs retain the exact premium-prefix theorem. Full-family
score intervals and exact-decision certificates therefore follow as before.
Intersecting this interval with the prior FPTAS interval is valid: take the
maximum lower value and the minimum upper value. Retain the witness belonging
to the maximum lower value. Attention may propose a witness or search focus;
it cannot override a valid upper bound.

## Proposition A2: sharpness of the uniform omitted-mass factor

Take two records: one censored H=a-1 with premium 1, and one observed failure
at b=a+1 with premium 3, a>=2. Let F be empty. Then C_a=2,C_b=5,Q_tail=1
and kappa=5/4. The focused factor is 2b/(5a). For every a>=2,
the shared-failure world is the full optimum and

```
G/g_F = (5/4)*(1-1/(2*b)) -> 5/4 as a -> infinity.
```

There are only two relevant subsets, and the shared world is strictly larger
for every a>=2. This follows by direct substitution,
so the constant cannot be uniformly reduced on this family while retaining
only the same cost summaries. This is sharpness of the pair certificate,
not sharpness of a selected-policy bound or a proof that no horizon-dependent
certificate could be tighter.

## Proposition A3: premium sorting already optimizes this worst-case factor

For a fixed number k of focused assets, kappa_F is minimized by including the
k largest eligible premiums. Indeed K(0,y) is nondecreasing in y, and that
choice minimizes omitted mass. Therefore no learned attention mechanism can
claim a uniformly better kappa certificate at the same k using this bound.
Attention can still improve the proposed lower witness g_F on some inputs,
and so empirical proposal quality must be tested separately. Smaller kappa
does not necessarily mean a smaller absolute upper bound kappa*g_F; no such
stronger ordering is asserted.

## Counterexample: attention omission is not identification

H=(1,3), observed flags=(false,true), premiums=(100,1), a=2,b=3. With F empty,
g_F=1. But compatible L=(2,3) gives R_a/R_b=255/206>1. Therefore silently
treating unfocused censored assets as known survivors produces a false exact
certificate. The valid bound kappa=153/103 retains this missed uncertainty.
No learned attention score can repair the logic of an unjustified omission.

## Corollary A4: a minimum certified focus budget

For an exact rational 0<epsilon<=1, if C_b<=(1+epsilon)C_a, every
focus (including empty) has kappa<=1+epsilon. Otherwise the same condition is
equivalent to

```
Q_tail <= epsilon*C_a*C_b / (C_b-(1+epsilon)*C_a).
```

This follows by multiplying the positive denominators in A1. Sorting premiums
descending and taking the shortest prefix whose remaining mass meets this
threshold minimizes cardinality among all focuses certified by A1 at this
tolerance, by A3. It need not minimize cardinality under a stronger certificate
or the actual unknown approximation error. Enumeration still costs 2^k
subset evaluations; this is not a new FPTAS or a general polynomial algorithm.
The implementation provides this inspectable budget choice separately from
the fixed-budget learned experiments.

## Complete-family integration and retained precision

Let [l_F,u_F] be A1's interval and [l_P,u_P] the existing FPTAS interval,
with compatible attaining witnesses for both lower bounds. Define
l=max(l_F,l_P), u=min(u_F,u_P), and retain the witness attaining l. Both
intervals contain G, hence l<=G<=u and u<=u_P<=(1+epsilon)l_P
<=(1+epsilon)l. For a>=b the exact previous solver is retained. Define
L_a=max_b l(a,b), U_a=max_b u(a,b), and choose a_hat minimizing U_a.
If a_star minimizes the true full-family W, then

```
W(a_hat) <= U(a_hat) <= U(a_star)
          <= (1+epsilon)*L(a_star) <= (1+epsilon)*W(a_star).
```

If U(a_hat)<=min_(a!=a_hat)L_a, the selected policy is an exact minimizer;
a strict inequality certifies uniqueness. This generic interval composition is
established optimization logic; the new candidate is the specialized A1
certificate. Running the full fallback for every pair adds computation, so the
current integration is precision-preserving and not a demonstrated speedup.

## Novelty boundary

Scaled dot-product attention, set attention, learned subset proposals, solver
guidance, coreset/scenario reduction and checked optimization certificates are
established. A1-A3 are the specialized mathematical results derived here for
this censored-cohort quotient. Their proof and validation do not establish
historical priority. Attention does not enter their validity conditions and is
not claimed as the source of the mathematical guarantee.
