# A complete-family approximation certificate for heterogeneous failure costs

## Model and exact earlier-pair reduction (F1)

Use the preserved finite-cohort integer model, with preventive cost one and
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
preserved exact premium-prefix theorem; identical ages have value one.

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
