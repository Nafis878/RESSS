# Theory audit: standard properties, explicit limitations

All statements below are deductions under stated assumptions, not original theorems. Symbols: fixed policies k=1,…,K; finite, prespecified contexts g=1,…,G; unit cost c>0, useful life t>0, failure F∈{0,1}; population renewal rate r=E[c]/E[t]. This rate differs from E[c/t]. Policies and contexts must be fixed before the new validation outcomes are observed.

## PROPOSITION 1 — simultaneous accepted-policy failure control

Assume independent validation units sampled from a common deployment population, with conditionally iid Bernoulli failure outcomes within each context for each fixed policy. Dependence between policies on the same unit is allowed. Each policy-context count is binomial conditional on its context sample size. Let d=δ/[K(G+1)]. Define Q(k,g) as the one-sided Clopper–Pearson upper bound: beta inverse survival at d with parameters (failures+1,n−failures), taking Q=1 for n=0 or all failures. Include the K pooled bounds in the same allocation.

With probability at least 1−δ over validation, every supported policy-context pair with Q≤α has true conditional failure probability ≤α. Any data-dependent selection among these pairs inherits that property, even if cost, bootstrap stability and jackknife filters use the same validation set.

Proof: binomial interval coverage gives P(p(k,g)>Q(k,g))≤d for each fixed pair, including random sample size by conditioning. Apply the union bound to at most K(G+1) pairs. On the simultaneous event, Q≤α implies p≤α. Further filters only remove eligible policies. Integrating conditional risks gives marginal risk ≤α only if every deployed context uses an accepted pair. □

**Fallback limitation:** an empty accepted set followed by an uncertified 1-SE policy does not inherit this guarantee. The actual RAMPE system always uses this uncertified fallback on real data. No deployment theorem for the complete algorithm was established. An unseen context, a context defined after observing failures, dependent units, adaptively fitted candidates, or conditional distribution shift can violate assumptions. This independent meta-validation statement does not repair the original CAT calibration/refit concern.

**Sample requirement:** even with zero failures, Q=1−d^(1/n). Certification requires n≥ceil(log(d)/log(1−α)). With K=4,G≥1,δ=α=.05, the minimum is 99 units in the least fragmented case. Actual total meta-validation sizes are 9–26, and local sizes are smaller. Thus no real-data eligibility is possible under this gate; universal abstention is a mathematical consequence, not an empirical safety discovery.

## LEMMA 2 — interpretation of the reliability index

Set R=min{α/Q,2S,2D} on supported contexts, else R=0. Then R≥1 is exactly the conjunction Q≤α, S≥.5 and D≥.5 (ignoring floating-point tolerance). Proof follows directly from the definition of a minimum. This is a constraint satisfaction index. It is not P(policy is reliable), a conformal p-value, a calibrated competence probability, or a transfer certificate. □

## PROPOSITION 3 — conditional selection excess rate

Suppose a nonempty candidate subset A satisfies a uniform estimation event |rhat_k−r_k|≤ε. For nonnegative penalties u_k, select a minimizing rhat_k+u_k over A. For k* minimizing true rate within A,

    r_a − r_k* ≤ 2ε + u_k* − u_a ≤ 2ε + u_k*.

Proof: r_a≤rhat_a+ε≤rhat_k*+u_k*−u_a+ε≤r_k*+2ε+u_k*−u_a. □

This does not bound regret against the best truly safe policy if the gate excluded that policy. Relative to a larger true-safe set, an additional eligibility-exclusion gap is necessary. It does not control an uncertified fallback. Nor does greedy contextwise application bound the global renewal objective below.

For a possible uniform event, suppose known bounds 0≤c≤c_max and 0<t≤t_max, E[t]≥t_min>0, and independent units. Hoeffding plus a union bound can bound both sample means. If |chat−E[c]|≤ε_c and |that−E[t]|≤ε_t<t_min, then

    |chat/that − r| ≤ (ε_c + r ε_t)/(t_min−ε_t).

Proof: subtract ratios, combine their numerator, and lower-bound that. Known population bounds are required; observed maxima cannot be substituted. Bootstrap SD in this implementation is not asserted to be such a uniform bound. These are standard concentration/selection arguments, with no novel regret theorem.

## PROPOSITION 4 — a fixed policy lottery cannot improve the best member's rate

For context-independent weights w_k≥0 summing to one, choose one whole policy at the start of an independent renewal. Then

    r_mix = Σ w_k E[c_k] / Σ w_k E[t_k]
          = Σ v_k r_k,  v_k=w_k E[t_k]/Σ w_j E[t_j].

The v_k form a probability vector. Therefore min r_k≤r_mix≤max r_k. Proof: direct substitution. □

Contextual routing can improve over a globally fixed member when genuine specialization exists. This is already the premise of local experts and dynamic expert selection. Averaging incompatible maintenance times has no justification here.

## COUNTEREXAMPLE — minimizing each context's rate is not global rate minimization

Two equally likely contexts have (cost,life) pairs:

| Context | Policy A | Policy B |
|---|---|---|
| 0 | (1,10) | (11,100) |
| 1 | (10,10) | (10,10) |

Greedy local rates select A in context 0 because .1<.11, yielding global rate (1+10)/(10+10)=.55. Selecting B there gives 21/110≈.190909. Both can satisfy failure risk ≤.05 if cost means are represented with preventive cost 1 and failure cost 201: probabilities 0,.05,.045 respectively. Thus even reliable local routing need not solve the global renewal objective. This is a standard fractional-objective phenomenon. The synthetic oracle iterates argmin_k E[c|g,k]−r E[t|g,k] and updates the global ratio; it uses known generator means, never selection data. An executable regression test checks the counterexample.

## IMPOSSIBILITY ARGUMENT — source evidence cannot identify arbitrary conditional shift

Two target worlds can have identical source validation data and identical query contexts but different target P(F|context,policy). A source-only selector has identical evidence and authorities in the two worlds. If its chosen policy becomes unsafe in one world, no universal safety conclusion follows from its source confidence or context-support flag. More source data narrows uncertainty about the source, not uncertainty about an unidentified target change. A meaningful transfer bound needs extra invariance, bounded-shift, target-label, or causal assumptions. RAMPE supplies none.

## HEURISTICS and EMPIRICAL RESULTS

Bootstrap co-optimal-set membership S and jackknife membership D measure sensitivity to resampling, not safety. Both share data and are correlated. The majority threshold and one-SD cost penalty are interpretable conventions. Multiplying normalized components and averaging ranks are sensitivity variants with no probability interpretation. Logistic acceptability predicts an empirical label using other datasets and is not calibrated to deployment failure risk.

EMPIRICAL RESULT: RAMPE equals 1-SE on every real episode; therefore its incremental observed effect is exactly zero there. Controlled matched distributions demonstrate contextual selection; hidden conditional shifts defeat it. The full-information temporal reference illustrates adaptation from new outcomes, with unrealistically available counterfactual labels.

## CONJECTURE — a future operational problem, not a novelty claim

Identifiable arbitration with policy-induced censored/delayed feedback, an explicit inspection budget, a renewal-rate objective and conditional safety might require a useful new mechanism. Renewal bandits already address reward/time ratios and truncated observations; maintenance POMDPs already address partial observation and learning. Any future claim must isolate a precise remaining mathematical distinction and compare those methods. No theorem, implementation or novelty is claimed for this conjecture.
