"""Build tables and scientific figures from completed outputs only."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path('out/rampe');HERE=Path('rampe')

def table(x,digits=6):
    def fmt(v):
        if isinstance(v,(float,np.floating)):return f'{v:.{digits}g}' if np.isfinite(v) else 'NA'
        return str(v)
    return '| '+' | '.join(map(str,x.columns))+' |\n| '+' | '.join(['---']*len(x.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in x.itertuples(index=False,name=None))+'\n'

def main():
    r=pd.read_csv(OUT/'real_summary.csv');s=pd.read_csv(OUT/'synthetic_summary.csv');counts=json.loads((OUT/'statistical_scope.json').read_text())
    picked=['plain','CAT','CATc','1SE','conventional','RAMPE','normalized','learned']
    rp=r[r.method.isin(picked)].pivot(index=['dataset','analysis'],columns='method',values='cost_rate_mean').reset_index()
    risk=r[r.method.isin(['RAMPE','conventional','normalized','learned'])][['dataset','analysis','method','risk_mean','abstention_mean']]
    ab=r.groupby('method')[['cost_rate_mean','risk_mean','abstention_mean']].mean().reset_index()
    # These means weight each of eight evaluation regimes equally. Full CSVs
    # retain each regime and settings; they are not pooled renewal estimates.
    ss=s[(s.attack=='none')&(s.method.isin(['RAMPE','B','conventional']))][['n_validation','shift','method','population_rate_mean','population_risk_mean','population_context_feasible_mean','abstention_mean']]
    sa=s[s.attack!='none'][['attack','method','population_rate_mean','population_risk_mean','abstention_mean']]
    sa=sa[sa.method.isin(['RAMPE','B','conventional','RAMPE_no_transfer'])]
    temporal=pd.read_csv(OUT/'temporal_reference_summary.csv');tm=temporal[temporal.method=='RAMPE'][['feedback','block','shift','rho','population_rate_mean','population_risk_mean','abstention_mean']]
    vs=pd.read_csv(OUT/'validation_stress_summary.csv');v=vs[vs.method=='RAMPE'];vtable=v.groupby(['fraction','accounting_noise_sd'])[['cost_rate_mean','risk_mean','abstention_mean']].mean().reset_index()
    fixed=pd.read_csv(OUT/'fixed_rule_shift_summary.csv');ff=fixed[(fixed.method=='RAMPE')&(fixed.evaluation_rho.isin([10,100]))][['dataset','analysis','evaluation_lead','evaluation_rho','cost_rate_mean','risk_mean']]
    tests=pd.read_csv(OUT/'synthetic_paired_tests.csv');qt=tests[tests.attack=='none'].groupby(['shift','baseline']).agg(conditions=('seeds','size'),significant_Holm=('sign_p_holm',lambda x:int((x<.05).sum())),wins=('wins','sum'),ties=('ties','sum'),losses=('losses','sum')).reset_index()
    ci=pd.read_csv(OUT/'real_conditional_intervals.csv');ci_main=ci[ci.method=='RAMPE'];citable=ci_main.groupby(['dataset','analysis','baseline']).agg(mean_rate_difference=('cost_difference','mean'),minimum_interval_low=('conditional_bootstrap_low','min'),maximum_interval_high=('conditional_bootstrap_high','max')).reset_index()
    cal=pd.read_csv(OUT/'learned_calibration.csv');frag=pd.read_csv(OUT/'selection_fragility.csv').groupby('method').partition_authority_fragility.mean().reset_index()
    # Export small view tables with documented aggregation, retaining all source rows.
    for name,x in [('report_real_cost.csv',rp),('report_real_risk.csv',risk),('report_ablation.csv',ab),('report_synthetic.csv',ss),('report_temporal.csv',tm),('report_tests.csv',qt)]:x.to_csv(OUT/name,index=False)
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
    domains=[f'{a}/{b}' for a,b in zip(rp.dataset,rp.analysis)];yy=np.arange(len(rp))
    for method,offset in [('RAMPE',-.2),('normalized',0),('learned',.2)]:axes[0].scatter(rp[method]/rp['1SE'],yy+offset,label=method,s=28)
    axes[0].axvline(1,color='black',lw=1,ls='--');axes[0].set_yticks(yy,domains);axes[0].set_xlabel('Mean episode cost rate / 1SE');axes[0].set_title('Real data: RAMPE equals fallback');axes[0].legend(fontsize=8)
    for shift in [0.,.5,1.]:
        z=ss[(ss.method=='RAMPE')&(ss['shift']==shift)];axes[1].plot(z.n_validation,z.population_rate_mean/(1/6),marker='o',label=f'shift={shift:g}')
    axes[1].axhline(1,color='black',ls='--',lw=1);axes[1].set_xscale('log',base=2);axes[1].set_xticks([32,128,512,2048],[32,128,512,2048]);axes[1].set_xlabel('Source validation units');axes[1].set_ylabel('Population cost rate / stable B');axes[1].set_title('Synthetic: source certainty can hurt under shift');axes[1].legend(fontsize=8)
    fig.savefig(OUT/'main_results.png',dpi=180);fig.savefig(OUT/'main_results.svg');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    for feedback in tm.feedback.unique():
        z=tm[tm.feedback==feedback];axes[0].plot(z.block,z.population_rate_mean,marker='o',label=feedback);axes[1].plot(z.block,z.population_risk_mean,marker='o',label=feedback)
    axes[0].set_ylabel('Population cost rate');axes[1].set_ylabel('Population failure probability');axes[1].axhline(.05,color='black',ls='--',lw=1)
    for ax in axes:ax.set_xlabel('Completed feedback block');ax.axvline(2.5,color='gray',ls=':');ax.axvline(5.5,color='gray',ls=':')
    axes[0].legend(fontsize=7);fig.suptitle('Controlled reference: all-policy counterfactual feedback, not RL');fig.savefig(OUT/'temporal_reference.png',dpi=180);fig.savefig(OUT/'temporal_reference.svg');plt.close(fig)
    report=f'''# RAMPE final scientific report

**Decision: D. NOT A CONTRIBUTION.**

**Did this project produce a genuinely new scientific contribution that can defensibly be attributed to this research? NO.**

This conclusion concerns the proposed new RAMPE/RL-RAMPE method. The work produced a reproducible negative investigation, not a defensible new methodological contribution. All previous CAT/CAT-c evidence remains frozen. No deployment safety guarantee is claimed.

## SECTION 1 — Scientific problem discovered

Estimated policy performance, selection sensitivity and future deployment reliability differ. A low observed renewal cost may arise from missing rare failures, favorable validation regimes, or unstable authority selection. The intended problem is to allocate a whole maintenance policy using evidence about both economics and reliability. Real preventive maintenance also changes which future outcomes can be observed; this prototype has retrospective completed-unit outcomes and does not model that feedback.

The experiment uses six engine datasets (PHM08, FD001–FD004, NCMAPSS6; 1026 original held-out units) and Battery (123 cells evaluated in CV and three batch holdouts). These repeated regimes do not create new independent cells. The bearing dataset lacks a comparable frozen four-policy cost pool and was excluded explicitly. No predictors or original policies were retrained. All new results live in `out/rampe`; all source is in `rampe`.

For each of 38 original outer groups, split held-out units into disjoint labelled meta-validation and meta-test halves using ten seeds 2026–2035. Validation size is 9–26. Four leads and four cost asymmetries yield **6080 retrospective episodes, 121600 outcomes for 20 methods**. This consumes additional labelled lives; it is not zero-label deployment transfer, the original benchmark, or ten new model-training runs. Each new selector receives the same validation labels. Query context is first observed operating regime/flight class or known battery batch; future life and test failure labels are not gate inputs.

## SECTION 2 — Why existing CAT/CAT-c cannot solve it

Frozen evidence already found established conformal mathematics, fragility improvement over plain tuning on 5/6 engine datasets, no demonstrated fragility advantage over 1-SE, and failed battery transfer. A single calibrated threshold does not identify conditional target shift or validate a new expert authority mechanism. The new gate does not fix calibration/refit dependence in the old method. Independently selecting among fixed candidates on new labelled validation units is a different, narrower protocol.

## SECTION 3 — RAMPE mathematical formulation

Pool Π={{plain cost, CAT(.05), CAT-c(.05), 1-SE}}; fallback=1-SE. For policy k and supported context g, estimate C=sum(cost)/sum(useful life), S=bootstrap co-optimal-set membership fraction, Q=one-sided binomial failure upper bound, T=observed context-support indicator, U=bootstrap cost-rate SD and D=leave-one-validation-unit co-optimal membership fraction. Use 100 paired unit bootstrap draws. T is a support flag, not an estimator of genuine transfer reliability. S and D measure perturbation sensitivity; they need not sum to one across policies.

Risk tolerance α=.05 and family error δ=.05 are fixed. Allocate δ/[K(G+1)] per local/pooled policy bound. Analytic R=min(α/Q,2S,2D) when supported, else zero. Eligibility requires Q≤α, S≥.5, D≥.5, T=1. Choose min(C+U) among eligible policies; if none, abstain and execute 1-SE. R is not a probability. The .5 majority threshold and one-SD penalty are conventions, not learned scientific constants.

Five formulations were tested: analytic conjunction; normalized min(1,α/Q)SD divided by C+U; standardized logistic empirical acceptability learned from other datasets; minimum C+U uncertainty-only routing; and mean rank of C,Q,−S,U,−D. Equal ranks and multiplied components are explicitly heuristics rather than unexplained probability models. Logistic C=1 and threshold .5 were fixed, with no test tuning. Both battery regimes are excluded when Battery is the held-out learned-gate domain.

Uniform, reliability, random Dirichlet and inverse-cost weighting sample **one complete policy per unit**. Incompatible alarm times are never averaged. Weights depending on context can exploit specialization; a fixed lottery cannot beat the best member's population renewal rate.

## SECTION 4 — Algorithm and pseudocode

```text
Freeze fitted policies, finite causal contexts, fallback and alpha/delta.
Separate completed meta-validation lives from untouched meta-test units.
For each query context:
    estimate paired cost/life ratios and bootstrap/jackknife sensitivity
    compute multiplicity-corrected binomial failure upper bounds
    exclude unsupported or risk/stability-ineligible policies
    if any eligible: assign whole-policy authority minimizing cost + SD
    otherwise: record ABSTAIN and assign fallback authority
Evaluate outcomes only after authorities have been assigned.
```

Executable definitions: [core.py](core.py), [real.py](real.py). Protocol: [PLAN.md](PLAN.md). Independent baseline outcomes are preserved, not recomputed under new policy settings.

## SECTION 5 — RL-RAMPE assessment

RL was not justified for independent retrospective unit arbitration: no demonstrated action-dependent transition state or sequential real feedback exists. One decision with later selected-action feedback would first be a contextual bandit; variable renewal durations call for renewal/semi-Markov accounting. A real maintenance MDP/POMDP needs verified degradation transitions and action effects.

A controlled sequential reference was implemented with static source evidence versus rolling last-512-unit evidence, eight blocks of 256 units, 30 seeds, 18 methods, **8640 outcomes**. All policies' completed counterfactual outcomes become available only after each block. This is full-information updating, not a contextual-bandit or RL experiment. PPO, bandits and RL-RAMPE were not run or claimed validated. Temporal blocks shift failure distributions after block 2 and block 5; costs change from 50 to 100 at block 5. Block order is synthetic, not an invented chronology for the real datasets.

## SECTION 6 — Theoretical analysis

[THEORY.md](THEORY.md) proves three standard propositions and one index lemma, with explicit assumptions: simultaneous accepted-policy conditional failure control; uniform-estimation excess rate ≤2ε+oracle penalty inside the selected subset; fixed-lottery convexity of renewal rates; and the equivalence of the analytic index to its constraints. Ratio concentration requires known cost/life bounds and independent units. Bootstrap SD is not claimed as a finite-sample guarantee.

The accepted-policy property excludes an uncertified fallback. With zero failures, minimum local sample size is ceil(log(d)/log(.95)); even the least fragmented K=4 case needs 99 validation units. Actual total sizes are at most 26. Consequently every real gate abstains; this was retained rather than relaxing risk thresholds after observing results.

A counterexample shows that minimizing each context's cost/life ratio can be globally wrong: two equally likely contexts give greedy global rate .55 versus alternative 21/110≈.190909. The synthetic population oracle therefore optimizes the global fractional objective. This is an established fractional-control phenomenon, not a new theorem. Arbitrary hidden conditional shift is unidentifiable from unchanged source data and query contexts. No universal transfer bound or fallback safety theorem was obtained.

## SECTION 7 — Experimental results

Mean episode renewal cost rates across all leads/costs/partition seeds:

{table(rp)}

RAMPE and 1-SE have identical selected policy, unit costs, useful lives and failure labels in all 6080 episodes. Thus any gain against conventional pooled minimum cost is entirely inherited from 1-SE; it is not evidence that the reliability gate adds value. Learned and normalized gates are worse than RAMPE/1-SE on these aggregate rates. All 20 methods and setting-level results are retained in [real_summary.csv](../out/rampe/real_summary.csv) and [real_setting_summary.csv](../out/rampe/real_setting_summary.csv).

Failure probability and abstention:

{table(risk)}

The failure metric is the existing unplanned-failure label, not documented catastrophic severity. Median, observed maximum and variance concern per-unit accounting costs, which equal 1 or rho. Maxima are observed maxima, not population worst-case bounds. Renewal cost rate is the primary economic estimand, distinct from mean accounting cost or mean unit rate.

![Real cost ratios and synthetic hidden-shift failure](../out/rampe/main_results.png)

## SECTION 8 — Ablation results

Equal-weight mean over eight real evaluation regimes (not a pooled renewal rate):

{table(ab)}

Calibration eligibility is the binding bottleneck. Removing bootstrap stability, transfer veto or context does not make the small samples certifiable; unchanged outcomes do not prove those components are irrelevant in general. Removing calibration or abstention exposes the more aggressive authority choices. Removing all reliability uses local minimum cost; conventional uses pooled minimum cost. The no-stability variant removes S while retaining jackknife D, so it is a specific component removal, not removal of every perturbation signal. Random/inverse-cost lotteries and every synthetic ablation remain in the output tables.

Partition authority fragility (one minus largest majority-policy frequency over ten seeds):

{table(frag)}

This is a selection-sensitivity diagnostic with fixed fitted policies. It is not algorithmic-stability theory or predictor retraining fragility. Authority changes within sorted unit order are reported, but they are neither chronological nor within-life policy switching. Abstention avoided/introduced failures, false abstentions and accounting/life differences are ex-post paired diagnostics against conventional selection, not causal estimates of prevented catastrophes. No randomized real intervention occurred.

## SECTION 9 — Stress-test results

Validation stress completed **329080 method cases**: 328320 fraction/noise outcomes plus 760 support-removal outcomes. Fractions=.25,.5,1; additive cost-accounting noise SD=0,.1,1, with failure labels fixed. Noise is clipped to positive cost, introducing an acknowledged upward bias near zero; this is not sensor corruption. Mean RAMPE summaries across regimes/settings:

{table(vtable)}

Fixed-rule lead/cost shift completed **45600 method cases**. Freeze selection at lead 0/rho10. Actual frozen alarm-use outcomes are re-evaluated at four required lead times and rho=5,10,20,50,100. Failure occurs if originally failed or alarm-use+required-lead reaches/exceeds observed lifetime; failures consume full lifetime. No rule is retuned. Full results: [fixed_rule_shift_summary.csv](../out/rampe/fixed_rule_shift_summary.csv). Large lead may cause the fallback itself to fail; abstention does not protect against a universally inadequate pool.

All **247680** previous fixed-score stress rows were read and their original hash retained. They lack all candidate alarm/life trajectories and therefore cannot be relabelled as RAMPE cost experiments. Compatible fractions and seeds were reused; [legacy_stress_bridge.json](../out/rampe/legacy_stress_bridge.json) records the precise limit. Original results were not overwritten.

## SECTION 10 — Transfer and controlled mechanism results

The synthetic generator creates rare-event/variable-life A, stable preventive B, and regime-specialist C. A and C are not artificial additions to the real candidate pool: they are explicit toy outcome distributions requested to isolate the mechanism. Life SD parameters are 0/.6, n=32/128/512/2048, rho=10/50, accounting noise=0/1, source specialist prevalence=.1/.5/.9 and shift=0/.5/1, with 30 independent validation/test seeds per condition. **288 grid conditions =8640 episodes**, plus 60 attack episodes, giving **8700 episodes and 156600 method outcomes**. Each target episode contains 1000 units. Life and failure are independent in this toy generator; it is not a physically validated degradation simulator.

Source failure probabilities are A=.01, B=0, C=.15 outside specialist regime and 0 inside. Expected lives are 10,6 and 10/9. Shift increases target A and C failure probabilities and changes target regime prevalence without changing the available regime identifiers. Policy B's rate is 1/6. At large source n, matched-distribution arbitration improves over B and conventional selection, but hidden target shifts reverse that benefit:

{table(ss)}

Context-feasible fraction requires every assigned positive-probability policy to have true conditional failure probability ≤.05. A low marginal rate or negative cost excess against the constrained oracle does not imply an admissible policy; report feasibility alongside “regret”. Oracle disagreement is true population-context authority error against the fractional safe oracle, not model-classification accuracy. [uncertain_best_policy.csv](../out/rampe/uncertain_best_policy.csv) stratifies cases by resampling uncertainty in the identity of the best source policy. Uncertain winner identity alone does not establish better target arbitration.

Failure attacks:

{table(sa)}

An unseen-regime veto works only by assuming the stable B fallback remains valid. When all policies fail, RAMPE abstains but still fails with probability one. Removing the transfer veto can select source-qualified policies in the unseen context and fail badly. Real support removal is a signal intervention with unchanged outcomes, not newly generated real sensor regimes.

Cross-dataset transfer applies only to the learned gate: its training excludes every row of the held-out dataset, including both battery CV and LOBO together. It does not transfer or refit base health predictors. Learned acceptability calibration (empirical target-rate≤1-SE and failure≤.05 label, **not** failure probability calibration):

{table(cal)}

Other gates report holdout failure rate minus mean selected validation empirical risk; this is a calibration-gap diagnostic, not probability ECE. Quantities derived from repeated cells are descriptive. Genuine target conditional-risk calibration remained unestablished.

Controlled temporal reference:

{table(tm)}

Rolling completed counterfactual evidence can adapt after a shift; the first shifted block cannot benefit from unobserved future feedback. This shows the value of new information, not a new RL method. New full outcomes cannot be assumed available after real preventive interventions.

![Controlled full-information temporal reference](../out/rampe/temporal_reference.png)

## SECTION 11 — Statistical analysis

All method summaries include mean, SD, median, observed min/max. [real_paired_descriptive.csv](../out/rampe/real_paired_descriptive.csv) records paired rate effects, relative effects and win/tie/loss across all episodes. These 6080 episodes reuse units and fitted models; they are **not 6080 independent studies**. No significance test treats partition seeds or leads as independent samples.

Conditional real inference uses one partition seed (2026) and 2000 paired unit-bootstrap draws (seed2027), giving **{counts['conditional_real_comparisons']}** cost intervals. It conditions on frozen fitted rules and selected authorities and omits re-selection/retraining uncertainty. CV/shared-source dependence restricts interpretation; intervals do not establish deployment generalization. Selected interval envelopes across all 16 settings are shown below; they are not simultaneous confidence intervals:

{table(citable)}

RAMPE versus 1-SE has point difference 0 and interval [0,0] because actions are identical; this proves equality in recorded outcomes, not universal population equivalence. Battery LOBO uses disjoint test batches, one seed only, exact paired binary sign/McNemar tests and Holm correction across **{counts['lobo_holm_family']}** comparisons. Their exchangeability assumptions remain conditional on source fits. All raw and adjusted p-values are retained, including nonsignificant results.

Synthetic paired inference concerns independent **simulator validation cohorts**, not real-engine deployments. For each 30-seed condition, paired population-rate differences have mean/SD/median, relative effects, Student-t mean intervals (approximate), and exact nonzero-sign tests. Holm is applied across **{counts['synthetic_comparisons']}** comparisons including attacks; it controls this sign-testing family, not every descriptive metric or interval. Aggregated counts for nonattack conditions:

{table(qt)}

The sign test tests directional consistency (under iid simulator draws), not a null of equal mean. Ties are removed from its denominator. Monte Carlo confidence does not validate the simulator's physical assumptions. Full condition-level results, including loses and ties, are in [synthetic_paired_tests.csv](../out/rampe/synthetic_paired_tests.csv).

## SECTION 12 — Literature overlap table

The complete table with title, year, venue, problem, method/mathematics, similarity, difference and claim-invalidating assessment is [LITERATURE_AUDIT.md](LITERATURE_AUDIT.md). It includes 27 close/relevant papers across local experts, DES/meta-learning, streaming arbitration/abstention, cost-sensitive deferral, conformal testing, stability, robust optimization/domain generalization, safe contextual bandits, renewal control and maintenance/meta-RL. Reading depth and version differences are explicit.

Closest overlaps: [META-DES](https://arxiv.org/pdf/1810.01270) for multi-evidence learned competence; [streaming ADE](https://project.inria.fr/aaltd19/files/2019/08/AALTD_19_Boutegane.pdf) for uncertainty about competence plus adaptive abstention; [multi-expert deferral](https://proceedings.mlr.press/v206/verma23a/verma23a.pdf) for calibrated expert authority; [LTT](https://arxiv.org/html/2110.01052v5) for risk-screened utility selection; and [renewal bandits](https://www.atillaeryilmaz.com/RenewalBanditsSigmetrics2020.pdf) for rates, interrupted/truncated feedback and confidence-aware sequential control. No paper is claimed to contain the exact numerical six-feature recipe; that recipe is an unvalidated combination, not demonstrated conceptual novelty.

## SECTION 13 — Novelty attack

All six strict gates fail for the implemented claim. A: contextual competence allocation is established. B: CP screening, bootstrap/jackknife sensitivity and uncertainty penalties are established ingredients. C: gating, weighting and fallback are established mechanisms. D: a constrained cost-sensitive dynamic expert selector can reproduce the architecture. E: real authority always stays at the existing baseline; toy gains do not isolate a new contribution. F: close methods already address reliability-sensitive expert/policy authority, including confidence in meta-reliability itself.

Failure conditions were observed or identified: insufficient rare-failure evidence; unseen contexts; hidden conditional shift despite supported context; all-policy failure; correlated near-identical candidate outcomes; unreliable learned competence; nonexistent transfer signal; excessive abstention; local/global renewal objective mismatch; and unavailable counterfactual feedback. Removing context when no meaningful specialization exists cannot create information. Larger source samples can amplify confident wrong deployment under unidentified shift. CAT+ensemble, CAT+PPO, revised weights and a new name are rejected as novelty rescues.

## SECTION 14 — Final novelty verdict

**D. NOT A CONTRIBUTION. NO genuinely new scientific contribution is established.** Novelty fails and meaningful incremental real-data advantage over 1-SE is absent. This is not C: the synthetic matched-regime gains do not make RAMPE broadly empirically strong against its strongest real baseline and shift tests. It is not B: the implemented mechanism is not a sufficiently distinct promising new idea awaiting only more evidence.

Useful negative evidence and software were produced, but their first-in-literature originality, publication suitability and deployment validity were not established. This verdict applies to RAMPE and the requested novelty claim, not to the value of carefully preserving the earlier study.

## SECTION 15 — Exact contribution statement

Defensible statement: “We implemented and audited reliability-sensitive arbitration among four frozen maintenance policies. Under a labelled retrospective meta-validation protocol, corrected risk eligibility forced fallback in every real evaluation; alternative heuristic/learned gates did not establish an advantage over 1-SE. Controlled tests showed matched-regime selection gains and hidden-shift failures, and prior art prevented attributing the architecture as a new method.” This is an empirical audit statement, not a claim of new conformal, ensemble or RL methodology.

The minimum **meaningful** conceptual change is an operational, identifiable problem with policy-induced censored/delayed feedback, paid inspections, random renewal durations and a coupled conditional-safety/rate objective. A new estimator, impossibility result or nontrivial safety–regret–inspection tradeoff must address a precise limitation of existing renewal-bandit, safe-deferral and maintenance-POMDP methods. Adding those terms alone does not guarantee novelty. Current data do not establish that new problem or solution.

## SECTION 16 — Recommended paper title

**When Reliability Gates Only Reproduce the Baseline: An Audit of Maintenance Policy Arbitration**

This is a title for a transparent empirical/negative study, subject to further publication-quality validation. A title asserting novel RAMPE or RL-RAMPE is not supported.

## SECTION 17 — Abstract

Maintenance policy tuning often conflates estimated performance with reliable decision authority. We investigate retrospective reliability-sensitive arbitration among plain cost tuning, conformal risk-controlled tuning, a stability-oriented variant and the one-standard-error baseline. Evidence combines renewal cost, resampling sensitivity, multiplicity-corrected failure bounds, context support and uncertainty. Five reliability formulations and policy-level lotteries are evaluated without averaging incompatible maintenance decisions. Across six engine benchmarks and two battery evaluation regimes, 6080 labelled meta-validation episodes produce universal abstention for the analytical gate and exact reproduction of the one-standard-error fallback. Learned and normalized alternatives do not establish an aggregate economic advantage. Controlled synthetic experiments show that contextual selection can help under matched distributions but becomes confidently inferior under hidden conditional shifts as source sample size grows. A temporal reference adapts using completed counterfactual outcomes, whose availability exceeds real preventive-maintenance feedback. Standard conditional-risk properties exclude uncertified fallback and unidentified transfer. A two-round literature audit identifies substantial overlap with dynamic ensemble selection, confidence-aware abstention, calibrated multi-expert deferral and renewal-policy bandits. We therefore reject a new-method contribution and provide reproducible negative evidence separating fallback performance, source confidence and operational transfer reliability.

## SECTION 18 — Three to five defensible outputs

1. A preserved-data, executable comparison of five reliability formulations, four whole-policy lotteries and component removals across every compatible frozen evaluation setting.
2. An explicit attribution check showing every analytical real-data result is inherited from the 1-SE fallback, with no incremental authority change.
3. Controlled sample-size, uncertainty, context, conditional-shift and all-policy-failure tests, plus an honestly scoped full-information temporal reference.
4. Standard proofs and counterexamples separating accepted-policy risk, fallback behavior and local versus global renewal optimization.
5. A primary-source prior-art and strict novelty audit rejecting an unsupported new-method claim.

These are project outputs; none is asserted here to be a first-in-literature methodological contribution.

## SECTION 19 — Anticipated reviewer objections

“The gate cannot certify with these sample sizes.” Correct; this is a decisive negative result, not evidence that abstention magically protects deployment. “Additional validation labels change the benchmark.” Correct; baseline rules are frozen and the retrospective information budget is explicit. “Repeated seeds are pseudo-replication.” Correct; descriptive repetitions and conditional inference are distinguished. “The learner sees the target labels.” It sees other-dataset empirical labels for training; the held-out dataset is excluded, and target outcomes are evaluated after choice. Correlated training rows and domain mismatch still limit interpretation.

“Context support is not transfer reliability.” Correct and demonstrated by hidden conditional shift. “A/B/C are unrealistic.” They isolate a requested mechanism; life/failure independence and outcome-only generation preclude deployment claims. “The oracle objective differs from local selection.” Correct; a counterexample and fractional oracle expose that limitation. “Your ensemble/RL architecture already exists.” Correct; novelty is rejected. “Catastrophic failures were not measured.” Only frozen unplanned-failure proxies exist. “No bandit/RL comparisons were run.” They were not justified by available real feedback; the temporal reference is clearly full-information and no RL performance is claimed.

## SECTION 20 — Recommended next experiments

Before further algorithmic branding, collect or simulate a physically justified operational feedback process with logged authority propensities, preventive intervention/censoring, delayed failures, replacement durations and inspection actions. Define identifiability assumptions and target conditional safety. Compare simple context cost routing, globally coupled fractional routing, established cost-sensitive deferral, safe contextual/renewal bandits and a maintenance POMDP where actions change state. Use fresh independent chronological source/calibration/test cohorts, enough effective units to estimate rare failures, and multiple genuinely retrained predictors when that is the estimand. Evaluate policy disagreement, inspection information value, censoring bias, safety violations and total renewal economics with a prespecified inferential family. Audit the exact resulting math against renewal-bandit and censored-control prior work before making a novelty claim. Do not promise that more seeds or weights will rescue current RAMPE.

Reproduction instructions: [README.md](README.md). Integrity and scope: [verification.json](../out/rampe/verification.json) and [run_manifest.json](../out/rampe/run_manifest.json). The original 31488 battery decisions, 247680 score-stress cases and previous verification artifacts remain unchanged.
'''
    (HERE/'FINAL_REPORT.md').write_text(report,encoding='utf-8');print('PASS: 20-section report and four figure artifacts built from complete tables.')

if __name__=='__main__':main()
