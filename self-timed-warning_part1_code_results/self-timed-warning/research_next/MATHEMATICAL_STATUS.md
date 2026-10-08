# Mathematical status and rejected reference design

These are deterministic facts, standard statistical constructions and directly derived reference calculations. None is claimed as an original theorem. They do not confer a guarantee on the frozen CAT implementations.

## 1. Operational score and deterministic monotonicity

Fix a fitted predictor, causal preprocessing, smoothing span and debounce count k; call this complete rule g. Let x_t be its smoothed prediction and a_g(tau) its first time with k consecutive predictions at most tau. Increasing tau can only move a_g earlier. Let L be failure time and d(t) the next permitted decision time. With lead ell, a replacement succeeds iff d(a_g(tau))+ell < L. Define S_g as the smallest threshold on the action grid giving success, or +infinity if none does. For every finite grid threshold,

    F_g(tau) = 1{S_g > tau}.

Consequently, for the same g, tau_c >= tau_CAT implies F_g(tau_c) <= F_g(tau_CAT) for every trajectory, including a shifted trajectory. This is relative monotonicity, not an absolute risk guarantee. CAT-c also minimizes the training ratio over the permitted larger thresholds, so its training ratio cannot exceed bare CAT's training ratio. Deployment cost need not improve: both replacement costs and useful lives change.

## 2. Standard rank validity and its limits

For exchangeable calibration/new scores produced by one independently fixed g, let r=ceil((n+1)(1-alpha)) and augment the calibration order statistics with +infinity. The standard upper rank threshold gives P(S_new > tau_hat) <= alpha. Ties are conservative. Rounding upward and further increasing the threshold preserve the inequality when the required action exists.

That abstract construction is not automatically deployable. A +infinity critical score means no admissible action exists even at the largest finite threshold. An ideal infinite threshold must not be identified with a physically safe action in that case. For a finite-grid implementation, rank feasibility, action feasibility, and handling every infeasible outcome must all be specified before claiming an unconditional guarantee. Conditioning on the reported finite-threshold flag does not establish conditional coverage. If n=18 and alpha=.05, r=19 is unavailable; n=19 is the first finite-rank possibility, not sufficient evidence of a conditional 5% population-risk bound.

The frozen CF implementation pools predictions from several inner models and deploys a refitted predictor. Its setting was selected using the calibration outcomes. The frozen SPLIT and KMIN variants also select the setting using these outcomes. These do not satisfy the independently fixed-rule argument. Bonferroni over settings does not repair a change of score-generating model. Pooled overlapping CV observations do not justify independent-binomial tests. The exact deployment guarantee remains unestablished. [CRC](https://arxiv.org/html/2208.02814v4) is the established foundation; its marginal expectation guarantee differs from [LTT](https://arxiv.org/html/2110.01052v5)'s high-probability population-risk guarantee.

## 3. Why empirical bootstrap stability cannot certify rare-event safety

For a fixed policy with true iid binary failure probability p>0, an observed n-unit sample can have zero failures with probability (1-p)^n. Every empirical bootstrap resample of that sample then also has zero failures. Bootstrap failure variance is exactly zero on this event, even though p is positive. This counterexample invalidates a generic claim that estimated risk instability alone certifies safety. Cost-rate variance can still be positive because useful lives vary; that is what the implemented 1-SE rule estimates.

For a fixed policy and iid Bernoulli outcomes with zero observed failures, the exact one-sided (1-delta) binomial upper confidence bound is

    p_upper = 1 - delta^(1/n).

At delta=.05, n>=59 is needed for p_upper<=.05. For K=2160 fixed policies and a Bonferroni level delta/K, n>=209 zero-failure calibration units are needed to make that particular simultaneous bound <=.05. This is an example for that simple bound, not a universal minimum for all testing procedures. It is not the rank-calibration sample-size requirement. It also requires candidates fixed independently or an appropriate uniform construction; overlapping OOF scores do not automatically qualify.

## 4. Renewal contrast: a rigorous but standard reference calculation

For policy a, define R_a=E[C_a]/E[T_a], with positive finite expected useful cycle length. For a fixed comparison baseline b,

    H_ab = E[C_a]E[T_b] - E[C_b]E[T_a]
         = E[T_a]E[T_b](R_a - R_b).

Thus H_ab and the population cost-rate difference have the same sign. For iid paired units Z_i=(C_ai,T_ai,C_bi,T_bi), independent cross-unit products give the unbiased order-two statistic

    U_ab = [sum_i C_ai sum_i T_bi - sum_i C_ai T_bi
            - sum_i C_bi sum_i T_ai + sum_i C_bi T_ai] / [n(n-1)].

Every cross-unit term has expectation E[C_a]E[T_b] or E[C_b]E[T_a]; summing n(n-1) terms proves unbiasedness. Within-unit dependence is allowed. Reusing dependent CV fits does not meet the iid-pair assumption. The implementation verifies this algebra; it does not test a new optimizer.

A simpler concentration construction uses disjoint pairs. Let m=floor(n/2), and

    h_a(Z_i,Z_j) = (C_ai T_bj + C_aj T_bi
                   - C_bi T_aj - C_bj T_ai)/2.

If 0<=C<=rho and 0<T<=L_max, with L_max a known population bound, then h_a lies in [-rho L_max, rho L_max]. Independent disjoint pairs give a mean Htilde_ab with expectation H_ab. Hoeffding and a union bound over K predetermined candidates give simultaneous one-sided upper bounds

    H_ab <= Htilde_ab + 2 rho L_max sqrt(log(K/delta_C)/(2m))

with probability at least 1-delta_C. Selecting only candidates with a strictly negative upper bound establishes improvement over a baseline fixed independently of this calibration sample. If none qualifies, return that baseline. Separately testing binary failure constraints with FWER level delta_F can establish joint selected-policy feasibility and relative improvement with probability at least 1-delta_C-delta_F, if all assumptions hold. Absolute feasibility of the fallback requires its own certification; fallback to 1-SE alone supplies none.

The concentration estimator above uses disjoint pairs; the numerical audit reports the full U statistic only for the unbiasedness calculation. No concentration interval for the full U statistic is claimed in the outputs. If the baseline is selected on the same calibration sample, the argument requires a uniform family over all possible comparisons or a separate selection sample. An observed maximum lifetime cannot substitute for L_max. Heavy tails, changing deployment distributions, censoring and refitting invalidate the stated recipe unless handled separately.

This construction is an application of standard Hoeffding concentration and [LTT-style selection](https://arxiv.org/html/2110.01052v5). An independent feasible frontier also overlaps [Pareto Testing](https://arxiv.org/pdf/2210.07913). No scientifically distinct new algorithm has been established by changing the estimand to maintenance renewal cost. The bound may be too loose to select anything at these sample sizes.

## 5. Bounded score perturbations and unidentifiable transfer

If a justified coupling establishes S_target <= S_reference + epsilon almost surely, then

    {S_target > tau_hat + epsilon} is a subset of {S_reference > tau_hat}.

Therefore the latter valid risk bound transfers to an available upward-rounded threshold tau_hat+epsilon. This is a direct set inclusion. Source bootstrap variation does not establish the required target coupling or a valid epsilon. Synthetic additive-score stress specifies epsilon by construction and cannot validate it for an unseen battery batch.

Conversely, consider two target environments with identical source data and observed sensor prefixes. Suppose the policy plans replacement at time t. In one environment the subsequent failure is after t+ell; in the other it is before t+ell. The label-free selector receives identical information and chooses the same action, while its failure outcome differs. Unobserved conditional shifts cannot be certified away by a feature drift test. Earlier action can reduce relative risk, but universal absolute safety needs a physically guaranteed action, outcome information or restrictive shift assumptions. This is a standard identifiability counterexample, not a new impossibility theorem.

## 6. Theoretical conclusion

Guaranteed here: fixed-rule monotonicity, algebraic equivalence/unbiasedness under stated iid assumptions, and standard rank/concentration constructions under their specified assumptions. Observed here: frozen empirical comparisons and isolated post hoc diagnostics. Potential future work: an operational decision-stability functional with a new useful bound; an identifiable delayed/censored feedback model. Unsupported: an exact frozen-CAT deployment certificate, arbitrary-shift safety, bootstrap stability as safety, or superiority of a nonexistent new method.
