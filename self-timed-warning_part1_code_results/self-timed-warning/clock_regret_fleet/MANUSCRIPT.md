# Certified Relative-Regret Replacement for Censored Heterogeneous Fleets

Nafis Wadud Ansari

Daffodil International University

ansari2305341800@diu.edu.bd

Working research draft - 8 October 2026. This manuscript has not been deposited or externally peer reviewed. The specialized originality claim is proposed for assessment; historical priority is not established.

## Abstract

Preventive replacement hides later failure times, and assets can incur different failure consequences. We study oracle-relative total-cost/total-use regret over one shared compatible lifetime completion per record. For arbitrary positive rational failure premiums, we derive an exact subset reduction for earlier-versus-later replacement ages. At each subset cardinality, the objective increases with aggregate premium and decreases with earliest-failure exposure. Applying established approximate Pareto techniques to this reduction yields a fully polynomial-time approximation scheme for complete selection among fixed candidate ages, with feasible extremal completions and a user-controlled 1+epsilon guarantee. An a posteriori certificate charges approximation error only at stages that discard nondominated states; separated score intervals certify an exact minimax decision. We compose optimization and clock-refinement errors into a (1+epsilon)(1+1/r) decision bound. Independent full-clock and phase-endpoint oracles validate small instances. A constructed-cost replay of 304 frozen engineering cohorts certifies all 208 decisions involving multiple candidate ages, while realized performance is mixed and its mean slightly worsens. The proposed contribution is a specialized censored-cohort theorem and certified heterogeneous selector; neither approximate Pareto optimization nor robust replacement is claimed as a new general principle.

## 1. Engineering question and relation to prior work

The question is whether a fixed replacement age can be selected using compatible censored records while retaining distinct asset failure consequences and a verifiable numerical decision bound. A calculation for the recorded fleet can certify how an age compares with its finite oracle under the stated uncertainty model. It cannot establish a future fleet's safety or population-optimal renewal policy without additional assumptions.

Fox [1] establishes minimax absolute renewal cost under fixed-mean or fixed-Laplace-transform distributional ambiguity. His complete supplied letter does not state the present cohort-relative formulas. Nonparametric replacement bounds [2], Bayesian censored lifetime learning [3], shared uncertain dynamics [4] and oracle-relative distributional cost ratios [5] are established antecedents. The moment-robust age-replacement conference abstract [6] concerns absolute average cost and an extremal probability law; its full proof manuscript remains unavailable in this audit.

Approximate Pareto construction is also established. Mittal and Schulz [7] use approximate frontiers for objectives combined via norms. Herzel et al. [8], Section 3 and Theorem 3.1, explicitly develop approximation exact in one objective. The keep-smallest-exposure-in-premium-bucket strategy overlaps those tools. Our proposed distinction is the exact phase/subset reduction for this rate-ratio model, its scalar approximation guarantee and its composition with clock error. A broader new approximation-mechanism claim would be unjustified.

## 2. Cohort criterion and information boundary

There are n>0 records (H_i,delta_i), with H_i>=1 on a positive integer clock. If delta_i=1, L_i=H_i; otherwise L_i>=H_i+1. For a fixed age d, failure at L_i<=d costs 1+q_i, survival costs one, and use is min(L_i,d), with q_i>0 a known rational. All policies share each latent L_i.

```
R_d(L) = [n + sum_i q_i*1{L_i<=d}] / sum_i min(L_i,d).
G(a,b) = sup_(compatible L) R_a(L)/R_b(L).
W(a) = max_(b in candidate ages) G(a,b).
```

For a finite candidate family, the supremum of R_a(L)/min_b R_b(L) equals W(a), by finite maximum/supremum exchange. Select an age minimizing W. The uncertainty set is Cartesian per record; observations and costs are inputs, and sealed lifetimes are excluded from selection. This is a deterministic robust cohort criterion. Neither probability-law estimation, informative-censoring correction nor a fresh-population guarantee is implied.

Later-versus-earlier pairs have an exact sorted-premium formula, reproduced with proof in Appendix A. Common premiums specialize to the two-world theorem. The remaining obstacle to complete heterogeneous selection is the earlier-pair subset tradeoff, addressed next.

## 3. Complete heterogeneous selection: reductions and guarantees


## Model and exact earlier-pair reduction (F1)

Use the finite-cohort integer model, with preventive cost one and
strictly positive rational failure premiums q_i. Observed L_i=H_i and censored
L_i>=H_i+1. Every policy shares the same completion. Candidate ages are fixed
positive integers. No population distribution, independence or future-safety
guarantee is asserted.

For a<b let E contain censored i with H_i<a. Under the completion in which all
censored assets survive both ages, write baseline totals C_a,C_b,T_a,T_b.
For S subset E define x=|S|, Q(S)=sum_(i in S) q_i and
s(S)=sum_(i in S)(H_i+1). Then exactly

```
G(a,b) = max_(S subset E) f_x(Q(S),s(S)),
f_x(Q,s) = (C_a+Q)*(T_b-b*x+s) /
           ((C_b+Q)*(T_a-a*x+s)).
```

An attaining completion makes S fail at H_i+1 and all other unresolved assets
survive both ages. The baseline includes known failures without altering them.
At fixed x, f_x is nondecreasing in Q and nonincreasing in s.

**Proof.** With a<b, shared-failure exposure T_b/T_a decreases as its time
increases, since T_b>=T_a. Thus each shared failure may be placed at its earliest
compatible time. A failure only under b may be replaced with survival: candidate
outcomes are unchanged, comparator cost decreases, and comparator use increases,
so R_a/R_b cannot decrease. Only shared-failure subsets remain. Both use totals
are positive and their difference is T_b-T_a-(b-a)x>=0, because each feasible
world has min(L,b)>=min(L,a). Also C_b>=C_a. Hence (C_a+Q)/(C_b+Q) increases with
Q, and (T_b-bx+s)/(T_a-ax+s) decreases with s. QED.

This reduction, not a horizon sort, permits arbitrary premiums. It does not say
the exact Pareto frontier is polynomial-sized or that the problem is NP-hard.

## One-sided trimming and complete-family FPTAS (F2)

Let e=|E|>0, 0<epsilon<=1, M=ceil(2e/epsilon), beta=1+1/M, and
q_min=min_(i in E) q_i. Maintain states (x,Q,s,S) for subsets of processed E.
The empty subset has its own bucket. A positive Q lies in a dyadic subdivision

```
q_min*2^k*(1+j/M) <= Q < q_min*2^k*(1+(j+1)/M),
k>=0, 0<=j<M.
```

Each bucket has maximum/minimum ratio at most beta. At each processed asset,
generate skip/take states. Separately for each cardinality x and bucket retain
the state with smallest s (breaking ties in favor of largest Q, then a fixed
subset order). Exact Pareto pruning can also discard states dominated by another
with the same x, larger Q and smaller s. States retain actual subsets, rather
than rounded synthetic failure costs.

Let g be the largest actual objective over surviving states and U=beta^e*g.
Then g<=G(a,b)<=U<=(1+epsilon)*g. g has a compatible attaining completion.
For e=0 the exact baseline ratio and witness suffice. Later pairs use the
exact premium-prefix theorem in Appendix A; identical ages have value one.

**Proof.** By induction after t assets, for every true subset there is a retained
state of the same cardinality with Q_ret>=Q_true/beta^t and s_ret<=s_true.
Taking the next asset preserves the inequality before trimming because its
positive premium is added to both states; skipping preserves it too. Keeping
the smallest s in a bucket worsens Q by at most beta and never increases s.
Pareto pruning preserves the induction. For alpha=beta^e,

```
[(C_a+Q)/(C_b+Q)] /
[(C_a+Q/alpha)/(C_b+Q/alpha)] <= alpha.
```

The first numerator ratio is at most alpha; the second denominator ratio is at
most one. Monotonicity in Q,s therefore bounds every true subset's objective by
alpha times a retained objective. Retained states themselves are feasible,
giving the lower bound. Finally log(beta^e)<=e/M<=epsilon/2<=log(1+epsilon)
for epsilon in (0,1], proving the desired factor. QED.

There are B=O((e/epsilon)*(1+log(e*q_max/q_min))) premium buckets, each with
at most e+1 cardinalities. The DP takes O(e^2*B) state-generation and bucket
operations, plus optional Pareto sorting O(e^2*B log B); memory is O(e*B)
states, with subset bitsets of O(e) bits. Total complete-family work is at most
K^2 times this pair bound plus exact later-pair work. Input rationals and dyadic
bucket comparisons are exact. Arithmetic and subset bit lengths are polynomial
in the rational input encoding, n and 1/epsilon. Thus the stated algorithm is a
fully polynomial-time approximation scheme for the complete-family objective.
It is not an exact polynomial-time heterogeneous selector.

Dyadic subdivision is used to avoid enormous rational powers in bucket lookup.
Fractional powers beta^e appear only in the certificate, with polynomial bit
length. Optional exact mode keeps full cardinality Pareto frontiers and has no
polynomial worst-case claim.

**A posteriori refinement.** Pareto-prune the generated states before bucketing.
Count only stages t_loss at which bucketing actually removes a nondominated
(Q,s) point. At a stage with no such removal, the induction incurs no beta loss.
Consequently `U=beta^t_loss*g` is valid and sharper than beta^e*g. If no stage
loses a nondominated point, the DP is exact and U=g. This is detectable from
public intermediate states; it does not require the unknown true optimum or
sealed lifetimes. The fixed M and advertised 1+epsilon worst-case bound remain
unchanged. With common premiums, Q is fixed by x, and Pareto pruning retains the
smallest s, so no nondominated point is lost and this automatically recovers the
exact common-cost reduction.

## Selection and decision certificates (F3)

For each pair retain a feasible lower value g_ab and upper value U_ab; exact
pairs have identical values. Define l_a=max_b g_ab and u_a=max_b U_ab.
Then l_a<=W(a)<=u_a<=(1+epsilon)l_a. Select a_hat minimizing u_a. Therefore

```
W(a_hat) <= u_a_hat <= (1+epsilon)*min_a W(a).
```

Proof: apply the upper inequality to an exact minimax age and use minimization
of u. Scores also certify a unique exact minimax age if
`u_a_hat < min_(a != a_hat) l_a`. The non-strict version certifies that the
selected age is an exact minimizer, possibly tied. If score intervals overlap,
the algorithm reports an approximate decision rather than asserting exactness.
This criterion does not identify a future-population optimal age.

## Continuous closure and joint numerical-error bound (F4)

Retain the exact recorded integer H and ages, allow censored real L_i>H_i,
and replace each earliest time H_i+1 in F1 by the limiting H_i. The subset
formula is now a supremum; shared phases must be labeled separately from the
numeric limit when H_i is approached from above. The F2 DP and factor carry
over because its proof uses positivity and monotonicity, not integer exposure.
Selected shared lifetimes can be made compatible with epsilon_time in (0,1).
Even if a returned limiting subset contains failures, another subset can tie
and attain the supremum; the API flags whether its returned completion itself
is attained and does not assert global nonattainment for every earlier pair.

For refined integer step 1/r, arbitrary heterogeneous premiums retain

```
G_r <= G_c <= (1+1/r)*G_r,
W_c(a_hat_r) <= (1+epsilon)*(1+1/r)*min_a W_c(a).
```

**Proof.** For earlier pairs fix any subset. Continuous-to-grid costs are
identical, and grid use adds x/r to both exposure totals A<=B. The quotient
change is (1+x/(rA))/(1+x/(rB))<=1+1/r since A>=n and x<=n. Maximize over
subsets. Later pairs already have the heterogeneous refinement bound; equal
ages are exact. Combining the pair sandwiches with F3 proves the joint bound.
This composes approximation and time-resolution errors without conflating
either with model uncertainty. The pairwise clock constant is sharp by the
already proved family; sharpness of the product or selected-policy bound is
not claimed. No noisy measurement guarantee follows from clock refinement.

## What is and is not proposed as new

The proposed extension is a complete, certified heterogeneous-cost selection
method for this shared censored-cohort rate-ratio model, including its exact
subset reduction, tolerance control and joint clock/optimization bound. Approximate
Pareto sets, dynamic-program trimming, cardinality bookkeeping and interval
certification are established tools. This is a specialized theorem/application
of those tools, not a new general approximation principle. A stronger scientific
claim still depends on engineering significance and theorem-level prior art.

## Exact-frontier size boundary (F5)

The exact Pareto DP can have exponentially many states at a single cardinality.
For n censored assets let q_i=2^(i+1), H_i=q_i-1, and choose a>max H_i, b>a.
At fixed x=floor(n/2), every subset has s=Q, with a distinct binary subset sum.
Larger Q improves the premium criterion but worsens exposure s, so none of the
binomial(n,x) points dominates another. Additional known failures between a and
b can make C_b>C_a, so both criteria are relevant. This proves the exponential
frontier boundary of this exact DP, not NP-hardness of the scalar optimization
problem and not impossibility of another exact polynomial algorithm.


## 4. Validation design and reproducibility

The plan was locked and hashed before implementation outcomes. One thousand fixed-seed small integer cases are checked by complete Cartesian lifetime enumeration, independent of the subset formula. Two hundred full-family cases are checked against complete-world oracle scores, two hundred common-cost cases against the preserved exact implementation, and two hundred continuous pairs against independently labeled endpoint phases. Ten unit-test groups also cover exact rational input validation, positive denominators, feasible witnesses, clock/tolerance composition, permutations, actual nondominated-state removal and an exact-frontier example with 924 points. All checks pass.

In exact mode, the cardinality Pareto DP retains the full frontier and can be exponential. It supplies a larger-instance reference but is not itself an independent oracle. The constructive proof and the independent small oracles are therefore essential. A 30-case stress study uses 12 censored records with H uniform in 1..100, four observed failures at 180,190,200,210, ages 120 and 240, censored premiums 10H plus independent integer jitter 1..50, and observed premiums 300. These choices and all cases are reported; tolerances are 1/2,1/4,1/10.

| Tolerance | Maximum observed pair factor | Median exact/approximate state ratio |
|---|---:|---:|
| 1/2 | 1.001138238 | 2.058 |
| 1/4 | 1.000254540 | 1.459 |
| 1/10 | 1.000000000 | 1.149 |

Table 1. Observed gaps are below the proved worst-case guarantee; they are not universal constants. The finest tolerance is exact on these 30 cases, not necessarily on other inputs. State ratios measure representation size, not a statistically established runtime speedup.

![Tolerance and frontier tradeoff](tolerance.png)

Figure 1. Accuracy and retained-state tradeoffs across the 30 fixed heterogeneous stress cases. Both panels use the same cases and tolerances.

## 5. Engineering lifetime replay with constructed failure costs

All 304 frozen real cohorts are retained: PHM08, FD001-FD004, NCMAPSS6 and Battery. Candidate ages and logging records come from earlier frozen conventional fits and schedules, independently of the evaluation lifetimes. Repeated cost settings, loggers and splits overlap; the cohorts are not 304 independent deployment experiments. Ninety-six cohorts have one candidate age, 184 have two and 24 have three. Limited candidate diversity constrains arbitration headroom.

Measured asset-specific failure-consequence data are unavailable. This study therefore uses the explicitly constructed public scenario q_i=(rho-1)*(1+class_i), with numeric unit ID modulo three; nonnumeric IDs use the UTF-8 SHA-256 integer modulo three. These are scenario labels, not measured engineering costs. The metadata correction and original plan are retained. A tolerance of 1/4 is fixed for all cohorts. Both common-cost and heterogeneous decisions are selected before reading sealed evaluation lifetimes.

All 304 common-cost score reductions match the preserved solver. The final heterogeneous algorithm matches exact-mode decisions in all 304 scenarios and certifies each as a unique minimax decision; 208 involve multiple candidates and 96 are trivial one-age decisions. Heterogeneous premiums change 13 decisions compared with common-cost selection: two in FD002, four in FD004 and seven in Battery. Matching a minimax decision is a criterion-specific certificate, not evidence of lower realized maintenance cost.

Under the heterogeneous scenario costs, relative to common-cost selection, realized oracle-relative cohort regret improves in five cases, ties in 291 and worsens in eight. The mean difference is 0.004718 regret-factor units, favoring common-cost selection. No independence-based significance test is performed on these overlapping cases. The new guarantee does not erase earlier negative maintenance and transfer results.

The initial implementation charged a beta factor even at stages losing no nondominated states. Its retained replay matched exact ages in 298 cases and certified 297. The proved actual-loss-stage refinement changes no tolerances, seeds or premiums. It tightens score intervals and yields the final certificates above. Both versions and their completed outcomes remain available.

## 6. Practical interpretation, limitations and originality

A maintenance analyst can supply a candidate age family and known positive failure premiums, obtain intervals for robust oracle-relative scores, and distinguish a certified exact decision from an approximate decision with explicit tolerance. The clock bound exposes how much numerical time resolution can change the cohort certificate. The interval-separation rule may be valuable when a precise decision is needed without retaining an exponential exact frontier. This is a computational assurance capability, whose engineering value still needs a substantive measured-cost case study.

The present model retains preventive cost one, exact recorded horizons, fixed candidate ages and Cartesian lifetime completions. It does not model downtime, interactions between components, arbitrary preventive costs, sequential interventions, noisy failures or population transfer. Stronger joint restrictions on lifetimes can change sharpness. No NP-hardness, universal runtime advantage, superior realized cost or deployed safety benefit is claimed.

The specialized reductions and guarantees are mathematically supported by constructive proofs and independent numerical checks. The general approximation mechanism overlaps established literature and must be attributed accordingly. The method is proposed as a model-specific contribution, with no claim to invent Pareto approximation or robust replacement. Historical-equivalence coverage remains incomplete for the separate moment-robust conference manuscript. Measured consequence data and prospective engineering validation are needed to assess practical utility beyond the present cost-scenario replay.

## Appendix A. Exact later-pair theorem and continuous sharpness



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



## References

[1] Fox, B. (1966). Letter to the Editor - Age Replacement with Discounting. Operations Research 14(3):533-537. DOI:10.1287/opre.14.3.533. Supplied publisher PDF inspected in full.

[2] Coolen-Schrijner, P.; Coolen, F.; Shaw, S. (2006). Nonparametric adaptive opportunity-based replacement strategies. Journal of the Operational Research Society 57:63-81.

[3] Drent, C.; Kapodistria, S.; Boxma, O. (2020). Censored lifetime learning: Optimal Bayesian age-replacement policies. Operations Research Letters 48(6):827-834. Inspected author preprint: EURANDOM 2020-005.

[4] Petrik, M.; Chow, Y.; Ghavamzadeh, M. (2016). Safe Policy Improvement by Minimizing Robust Baseline Regret. arXiv:1607.03842.

[5] Zhu, Z.; Zhang, J.; Ye, Y. (2006). Newsvendor Optimization with Limited Distribution Information. Author technical report, 18 November 2006.

[6] Shahri Majarshin, S. (2026). A robust age-based replacement problem. LNMB conference abstract. This is an abstract, not an inspected full manuscript.

[7] Mittal, S.; Schulz, A. S. (2008). A General Framework for Designing Approximation Schemes for Combinatorial Optimization Problems with Many Objectives Combined into One. APPROX/RANDOM, LNCS 5171:179-192. DOI:10.1007/978-3-540-85363-3_15.

[8] Herzel, A.; Bazgan, C.; Ruzika, S.; Thielen, C.; Vanderpooten, D. (2021). One-exact approximate Pareto sets. Journal of Global Optimization 80:87-115. DOI:10.1007/s10898-020-00951-7. Section 3 and Theorem 3.1 inspected in primary preprint arXiv:1908.10561.

Data and code availability: a local review archive contains the implementation, plan, protected-input hashes, fixed-case evidence and engineering replay inputs. It has not been publicly deposited. Source links and theorem-level comparisons are recorded in the companion literature audit. No third-party full-text papers are redistributed.
