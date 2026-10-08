# Exact Relative-Regret Age Replacement under Censoring

## Two Extremal Worlds and a Clock-Resolution Guarantee

Working research draft - 8 October 2026. Authorship and public-release metadata are pending. This document has not been deposited or externally peer reviewed. Historical priority is proposed for assessment, not established.

## Abstract

Preventive replacement censors asset lifetimes, complicating comparison of candidate replacement ages. We study minimax multiplicative cost-rate regret on a finite cohort, with one shared compatible lifetime per asset and a common failure-cost ratio. For a later age compared with an earlier age, we show that all unresolved assets eligible to fail under the later policy can be made to fail there. The remaining denominator is concave in a shared-failure count, so one of two explicit lifetime worlds attains the exact maximum. Combined with a sorted-prefix converse comparison, this yields an exact O(n log n+K^2 n) arithmetic-operation solver. We derive a continuous-clock supremum and a uniform 1+1/r approximation guarantee for clock refinement. Exhaustive, independent state-optimizer and frozen-result checks agree. A paired computational study shows substantial later-pair acceleration, while all earlier mixed maintenance-performance and transfer findings remain unchanged. The proposed contribution is the specialized extremal characterization and solver; broad robust replacement and minimax principles are established prior art.

## 1. Problem and relation to existing work

Age replacement replaces an asset at failure or a fixed deadline. Removing it preventively hides its later lifetime. Separately attained upper and lower policy-rate bounds may describe incompatible worlds for the same asset. We retain the same latent lifetime across every policy and optimize a relative cost-rate comparison.

This coupling principle is established: Petrik, Chow and Ghavamzadeh [1] compare policy and baseline returns under shared uncertain dynamics and explain the conservatism of separate policy estimates. Minimax replacement dates at least to Fox [2]; nonparametric replacement bounds appear in Coolen-Schrijner et al. [3]. Recent block-replacement learning already exploits censored lifetimes and nested policy information [4]. A 2026 robust age-replacement conference abstract describes a two-point worst-case lifetime distribution under moment constraints [5]; this is different from two compatible completions of a recorded cohort. The proposed distinction is the exact specialized theorem below, its full-family computation and its clock-resolution guarantee. No inspected source gave these same statements, but remaining access gaps preclude a definitive first-in-literature claim.

## 2. Finite-cohort model

There are n>0 public records (H_i,delta_i), with integer H_i>=1. Observed failures satisfy L_i=H_i; censored records imply L_i>=H_i+1 in the integer model. Candidate ages d_k>=1 are fixed independently of the evaluation outcomes. Costs share a common rho>1, and q=rho-1. Failure at a deadline is charged as failure.

```
F_i(d) = 1{L_i <= d};  T_i(d) = min(L_i,d).
C_i(d) = 1 + q*F_i(d).
R_d(L) = sum_i C_i(d) / sum_i T_i(d).
G(a,b) = sup_(compatible L) R_a(L)/R_b(L).
W(a) = max_b G(a,b);  select argmin_a W(a).
```

Factors include one; excess relative regret is W-1. This is a deterministic robust objective for the recorded cohort, not a population renewal rate, average unit cost/use or future safety probability. Cartesian lifetime completions are assumed; no survival law, independent censoring or physical life cap is needed. Lifetimes above the largest age share identical policy outcomes and have a finite representative. Known failures remain exact even above all ages.

## 3. Two-world integer theorem

Consider a>b. Let E be censored assets with H<b, e its size; let J be censored assets with b<=H<a, and m=e+|J|. Under the completion where all unknowns survive both ages, let C_a0,C_b0,T_a0,T_b0 be the costs and uses. Define

```
U = T_a0 - m*a + e*(b+1) + sum_(i in J)(H_i+1).
D0 = C_b0*U.
De = (C_b0+q*e)*(U-e).
G(a,b) = (C_a0+q*m)*T_b0 / min(D0,De).
```

THEOREM 1. The displayed value is exact and attained. The D0 world makes E fail at b+1 and J at H+1. The De world makes E fail at b and J at H+1. Other unknowns survive both ages and known failures are unchanged.

PROOF. Shared failures can move to b without decreasing the quotient, because total candidate use is at least comparator use. Later-only failures can move to max(H+1,b+1). Any eligible remaining survivor can then move into the later-only phase, raising candidate cost and not increasing its use while leaving comparator outcomes unchanged. Hence every one of the m eligible assets fails by a. If x of E are shared failures, the numerator and comparator use are fixed; the denominator is (C_b0+qx)(U-x). Its second derivative is -2q<0. A positive concave denominator takes its minimum on [0,e] at an endpoint. Both endpoints are feasible, giving the two attaining worlds. QED.

The shared world wins exactly when q*(U-e)<C_b0; both branches occur. Four known failures at time 1 plus one censored H=1, a=3, b=2, rho=2, require the shared world. Assuming the no-shared world universally is incorrect.

## 4. Converse comparison and complete algorithm

For a<b, later-only failures are dominated by survival. Shared failures occur at their earliest compatible H+1. At a fixed shared-failure count x, both costs depend only on x and the exposure difference is fixed. Choose the x smallest eligible horizons. With prefix S_x=sum(H_i+1),

```
G(a,b) = max_(0<=x<=e_a)
 ((C_a0+qx)*(T_b0-bx+S_x)) /
 ((C_b0+qx)*(T_a0-ax+S_x)).
```

An interior count can be necessary: three censored H=1 records and one observed failure at 5, a=4, b=20, rho=20, have a unique maximizing prefix count 1 and ratio 1081/588. The converse cannot generally be replaced by just the two endpoint counts.

Sort censored horizons and observed failure times once. Prefix sums and binary searches provide costs, truncated uses and eligibility for each age. Earlier-versus-later pairs scan at most n+1 counts; later-versus-earlier pairs evaluate at most two worlds; identical ages give 1. The finite maximum/supremum identity makes max_b G(a,b) the exact robust oracle factor. Thus complete selection uses O(n log n+K^2 n) arithmetic operations, with the same bound when all witnesses are emitted. Without witnesses storage is O(n+K^2); retaining them uses O(n+K^2 n). Standalone later-pair aggregation is O(n), without sorting. Exact rational bit complexity depends on input magnitude. Array totals are checked for int64 safety before arithmetic.

## 5. Continuous clocks and clock-refinement guarantee

Now retain exact integer-valued H and ages but allow real compatible lifetimes L>H for censored records. Let

```
U_c = T_a0 - m*a + e*b + sum_(i in J)H_i.
G_c(a,b) = (C_a0+q*m)*T_b0 / (C_b0*U_c), for a>b.
```

THEOREM 2. This is the exact continuous supremum. Later-only failure times approach max(H,b) from above. In the closure, moving a shared failure at b into that limiting phase leaves exposures unchanged and reduces comparator cost. Hence one no-shared limiting world suffices. For a<b, the sorted-count formula uses S_x=sum(H_i) instead. The same operation bound holds.

When m>0 in a later comparison the supremum is not attained. The implementation labels limiting lifetimes separately and generates compatible epsilon completions for 0<epsilon<1. It never treats limits equal to H as observed or compatible failures. The full constructive proofs are in THEORY.md.

THEOREM 3. Let G_r be the integer model after scaling H and all ages by positive integer r, so the physical step is 1/r. Then

```
G_r <= G_c <= (1+1/r)*G_r.
W_c(a_r) <= (1+1/r)*min_a W_c(a),
where a_r minimizes W_r.
```

PROOF. Grid completions are continuous completions. In a later comparison, the no-shared grid world has candidate use U_c+m/r, so G_r>=G_c/(1+m/(r*U_c)). Since U_c>=n and m<=n, this implies the upper factor. For an earlier comparison with x shared failures, grid exposure adds x/r to both continuous totals A<=B. The quotient of continuous to grid objectives is (1+x/(rA))/(1+x/(rB))<=1+1/r since A>=n. Taking maxima and then minima preserves the bounds, giving the selected-policy inequality. QED.

This deterministic error bound concerns the robust cohort objective. With minimum physical time tau and step Delta, the bound is 1+Delta/tau. It does not handle noisy or rounded observed failure labels automatically. In the branch example of Section 3, the integer factor is 1 while the continuous supremum is 10/9; refinement converges to the latter.

![Clock refinement example](resolution.png)

Figure 1. Exact factors for the same physical records and age pair under refined integer clocks. The r=1 shared-failure branch changes to no-shared at r=2. Continuous limiting clocks are not attaining witnesses.

## 6. Exactness and computational experiments

Fifteen unit-test groups pass, including 1,000 full-clock exhaustive cases, 500 independent endpoint-state cases and 300 larger comparisons to the frozen quadratic solver. All 39,448 earlier stored pairwise optima and all 2,704 cohort selections reproduce exactly. Three hundred continuous comparisons to a phase-labeled endpoint/exposure-hull optimizer match; 1,500 full-family resolution tasks across 300 independent cohorts satisfy all pairwise and selected-policy bounds. The development log retains the correction of an impossible equal-age phase in the continuous checker.

For timing, n ranges from 16 to 1024. Each size has 12 independently generated inputs, three repeated timings per input, and alternating method order. Parameters are a=40, b=20, H uniform integers 1..24, observed-failure probability .15, and rho randomly 5, 20, 50; seed 20261011. Both methods receive the same public input and return explicit witnesses. The frozen implementation also performs internal witness checks. Table 1 reports medians across inputs; speed ratios are medians of each input's paired timing ratio.

| n | New time (ms) | Frozen time (ms) | Median speed ratio | Holm p |
|---|---:|---:|---:|---:|
| 16 | 0.0933 | 0.2785 | 2.88 | 0.003418 |
| 32 | 0.1040 | 0.6028 | 5.81 | 0.003418 |
| 64 | 0.1127 | 1.9636 | 16.59 | 0.003418 |
| 128 | 0.1229 | 6.5019 | 53.62 | 0.003418 |
| 256 | 0.1655 | 26.1076 | 159.30 | 0.003418 |
| 512 | 0.1808 | 102.5091 | 577.16 | 0.003418 |
| 1024 | 0.2027 | 406.9144 | 2007.09 | 0.003418 |

Table 1. Later-pair computation against the frozen quadratic implementation. Two-sided paired sign tests use one median per independent input and a Holm family of seven sizes. The sample count was amended from 8 to 12 before any timing observations because the eight-input test had insufficient p-value resolution; original plan and amendment are retained.

![Later-pair runtime](runtime.png)

Figure 2. Elapsed-time medians and interquartile bands across independent inputs. Results are conditional on this model, implementation and Windows/Python environment; they are not a comparison against every optimized robust solver.

All seven timing contrasts favor the new implementation at Holm p=.003418. Earlier-pair small-input diagnostics are slower than the frozen implementation; there is no universal speedup. A separately structured general-state optimizer matches another 120 small comparisons. The theorem establishes computational complexity; timing tests do not establish historical novelty.

## 7. Maintenance outcomes, limitations and novelty status

This computational improvement leaves every earlier integer maintenance choice unchanged. The previous 2,400 independent synthetic cohorts had 13 corrected performance contrasts favoring the exact method and 15 favoring baselines. Short-life cost and failure risk could worsen against upper-rate selection. Frozen real tasks did not establish statistically significant primary-domain superiority, and Battery LOBO offered no improvement. None of those negative findings is overwritten or claimed solved here.

The result covers fixed ages, common costs and a stated censoring/clock model. Heterogeneous failure costs, future sensor-triggered policies, dynamic interventions, survival-distribution identification and future safety remain outside scope. More plausible joint restrictions can shrink the Cartesian ambiguity set and change sharpness. Large practical speed ratios against a deliberately frozen predecessor do not establish superiority to all exact optimizers.

The proposed mathematical contribution is the specialized two-world/one-world characterization, complete exact solver and resolution guarantee. Coupling uncertainty and minimax decision theory themselves are prior art [1,6]. We found no equivalent specialized statement in inspected work, but full-text gaps and unpublished research remain. The originality claim is therefore proposed for independent review; first-in-literature and public priority are not established. No authorship, DOI, accepted publication or public disclosure date is invented.

## References

[1] Petrik, M.; Chow, Y.; Ghavamzadeh, M. (2016). Safe Policy Improvement by Minimizing Robust Baseline Regret. arXiv:1607.03842. https://arxiv.org/abs/1607.03842

[2] Fox, B. (1966). Letter to the Editor - Age Replacement with Discounting. Operations Research 14(3):533-537. https://doi.org/10.1287/opre.14.3.533

[3] Coolen-Schrijner, P.; Coolen, F.; Shaw, S. (2006). Nonparametric adaptive opportunity-based replacement strategies. Journal of the Operational Research Society 57:63-81. Author manuscript: https://maths.dur.ac.uk/stats/people/ps/opport3.pdf

[4] Ganesaraman, A.; Kulkarni, V. (2026). Data Driven Block Replacement Scheduling. arXiv:2607.15229. https://arxiv.org/abs/2607.15229

[5] Shahri Majarshin, S. (2026). A robust age-based replacement problem. LNMB conference abstract. https://www.lnmb.nl/conferences/2026/abstracts.html

[6] Crema, A. (2018). Min max(relative) set-regret combinatorial optimization. Optimization Online working paper. https://optimization-online.org/2018/10/6897/

Additional close work, inspected equations, search queries and access limitations are recorded in LITERATURE.md. Reproduction instructions, protected input hashes and the complete new artifact manifest accompany the source archive. Manuscript authors must verify and supply attribution and public-release metadata before deposit.
