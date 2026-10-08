# Identification, not prediction uncertainty

These results are elementary partial-identification deductions. They are not claimed as original general mathematics. The proposed contribution is a paired evaluation resource and empirical diagnosis on the existing maintenance-policy pool.

## Outcome-summary observation contract

For a finite cohort of n independent run-to-end replays, record a logger endpoint H_i>0 and whether that logger failed or preventively removed the unit. Fixed target policies incur accounting cost c_i=1+(rho−1)F_i and useful life t_i. A target completion at/before a preventive logger endpoint is observable; a logger failure reveals the entire pre-failure record, so all target outcomes are observable. Otherwise its outcome is unresolved. Let O be observable outcomes and M the unresolved set, m=|M|. A_i is NOT a released complete future alarm time. Pending alarm information and raw sensor prefixes are outside this coarsened contract. Unit identity/source groups and cost/lead settings are public, but future RUL is not.

For each unresolved outcome assume H_i<t_i≤B, F_i∈{0,1}. B is a declared cap on a capped evaluation policy, not a sample-estimated lifespan bound. The observed sample is unchanged by capping because all original completions occur earlier than the caps. This is a finite-cohort outcome model; fixed sensor trajectories or a specified degradation process could impose additional constraints and make these intervals narrower.

## PROPOSITION 1 — sharp finite-cohort rate interval in the coarsened model

Let C_O=Σ_{i∈O}c_i and T_O=Σ_{i∈O}t_i. For the cohort ratio r=Σc_i/Σt_i:

    r_low  = (C_O+m)/(T_O+mB)
    r_high = (C_O+rho*m)/(T_O+Σ_{i∈M}H_i).

If m=0 both endpoints equal C_O/T_O. The upper endpoint is a supremum because unresolved times strictly exceed H_i.

Proof: each unresolved cost lies between 1 and rho. Each unresolved duration lies between H_i (strictly) and B. Positivity makes the ratio increase with each cost and decrease with each duration. Set every missing cost=1 and duration=B to attain the lower endpoint. Set every missing cost=rho and duration=H_i+epsilon to approach the upper endpoint as epsilon tends to zero. Both configurations satisfy the stated coarsened constraints. Hence no uniformly narrower interval is possible in this model. □

If durations are integer cycles, H_i+1 can replace H_i for a tighter upper endpoint. This implementation intentionally uses the conservative continuous-time relaxation, so “sharp” never means sharp for the full integer/sensor-policy class. If no justified cap exists, any unresolved duration can grow without bound and the infimum rate is zero. Introducing a finite cap is thus material for the lower endpoint; it does not change the upper endpoint.

## PROPOSITION 2 — failure interval and information requirement

Let f_O be observed failures. The sharp finite-cohort failure fraction interval is [f_O/n,(f_O+m)/n]. Proof: fill all unresolved binary outcomes with zero or one. Therefore a model-free cohort risk≤alpha certificate requires f_O+m≤alpha*n. With no observed failures, at most an alpha fraction can remain unresolved. This is an information requirement, not a calibration sample-size bound or future risk guarantee. □

## COROLLARY — economic improvement certificate

The logged cohort rate r_L is observable. If r_high<r_L then every compatible completion gives target improvement. If r_low<r_L<r_high, compatible worlds disagree on the sign. A point estimator choosing one such world cannot establish the sign without additional assumptions. Deleting missing outcomes or assigning them healthy labels does not create information.

## PROPOSITION 3 — monotonicity under additional observations

If an unresolved outcome is revealed and satisfies the contract, the compatible completion set becomes a subset of the old set. Hence the sharp lower rate/risk endpoints cannot decrease and the upper endpoints cannot increase. With all outcomes revealed, the intervals collapse to the actual finite-cohort metrics. Proof: set inclusion and extrema; or direct substitution of H_i<t_i≤B and 1≤c_i≤rho in the formulas. □

## Constructive nonidentification witness

One observed target has cost1,use8,failure0; one unresolved target has logger endpoint10. Declare rho50 and cap100; logging rate=.1. World L fills the unresolved target with cost1,use100,failure0, giving rate2/108<.1 and risk0. World H fills it with cost50,use10.01,failure1, giving rate51/18.01>.1 and risk.5. Their public outcome-summary records are identical. The intervals contain both worlds and return the same certification in both. These are valid outcome-model witnesses; no claim is made that both are realizable by an independently verified engine degradation/sensor model.

## What is not proved

No future-population coverage, conformal calibration, transfer robustness, treatment-effect identification, or safe exploration theorem is established. The original data have full trajectories from run-to-end tests, not actual preventive interventions. Pre-removal trajectory invariance is a replay assumption, not a physical causal validation. Random releases of sealed outcomes quantify retrospective information sensitivity; inspections of a removed component cannot automatically recover its true counterfactual remaining lifetime. A sensor-level benchmark would also have to expose pending alarms and validate each visibility decision by causal prefix execution.
