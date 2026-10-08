from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path('out/observability')

def table(x):
    def fmt(v):return f'{v:.5g}' if isinstance(v,(float,np.floating)) else str(v)
    return '| '+' | '.join(x.columns)+' |\n| '+' | '.join(['---']*len(x.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in x.itertuples(index=False,name=None))+'\n'

def main():
    x=pd.read_csv(OUT/'task_results.csv.gz',low_memory=False);z=x[(x.cap==5000)&(x.logger!=x.target)].copy()
    z['true_improvement']=z.true_target_rate<z.logger_rate-1e-12
    z['ambiguous_improvement']=(z.rate_low<z.logger_rate-1e-12)&(z.rate_high>=z.logger_rate-1e-12)
    z['hidden_rate_width']=z.rate_high-z.rate_low
    cols=['observed_fraction','true_improvement','certified_improvement','ambiguous_improvement','complete_case_false_improvement','healthy_false_improvement','complete_case_false_safe','healthy_false_safe','hidden_rate_width']
    d=z.groupby(['dataset','analysis'])[cols].mean().reset_index();d.to_csv(OUT/'offdiagonal_domain_summary.csv',index=False)
    p=z.groupby(['logger','target'])[cols].mean().reset_index();p.to_csv(OUT/'offdiagonal_pair_summary.csv',index=False)
    detailed=z.groupby(['dataset','analysis','logger','target','lead','rho'])[cols].mean().reset_index();detailed.to_csv(OUT/'offdiagonal_setting_summary.csv',index=False)
    b=pd.read_csv(OUT/'information_budget.csv.gz',low_memory=False);bb=b[b.logger!=b.target].copy();bb['rate_width']=bb.rate_high-bb.rate_low;bb['risk_width']=bb.risk_high-bb.risk_low
    bs=bb.groupby('release_fraction')[['rate_width','risk_width','certified_improvement','certified_safe','released']].mean().reset_index();bs.to_csv(OUT/'offdiagonal_budget_summary.csv',index=False)
    # Finite-cohort precision, not significance testing across duplicated settings.
    summary=dict(offdiagonal_tasks=len(z),observed_fraction_unweighted_tasks=float(z.observed_fraction.mean()),full_life_improvements=int(z.true_improvement.sum()),certified_improvements=int(z.certified_improvement.sum()),improvements_not_certified=int((z.true_improvement&~z.certified_improvement).sum()),ambiguous_improvement_tasks=int(z.ambiguous_improvement.sum()),complete_case_false_improvements=int(z.complete_case_false_improvement.sum()),healthy_false_improvements=int(z.healthy_false_improvement.sum()),complete_case_false_safe=int(z.complete_case_false_safe.sum()),healthy_false_safe=int(z.healthy_false_safe.sum()),interval_false_improvements=int((z.certified_improvement&~z.true_improvement).sum()),interval_false_safe=int((z.certified_safe&(z.true_target_risk>.05)).sum()))
    (OUT/'findings.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    allpairs=x[x.cap==5000].groupby(['logger','target']).observed_fraction.mean().unstack().reindex(index=['plain','CAT','CATc','1SE'],columns=['plain','CAT','CATc','1SE'])
    fig,axes=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
    im=axes[0].imshow(allpairs,vmin=0,vmax=1,cmap='viridis');axes[0].set_xticks(range(4),allpairs.columns);axes[0].set_yticks(range(4),allpairs.index);axes[0].set_xlabel('Target policy');axes[0].set_ylabel('Logging policy');axes[0].set_title('Fraction of outcome-summary records observable')
    for i in range(4):
        for j in range(4):axes[0].text(j,i,f'{allpairs.iloc[i,j]:.1%}',ha='center',va='center',color='white' if allpairs.iloc[i,j]<.6 else 'black')
    fig.colorbar(im,ax=axes[0],shrink=.8)
    axes[1].plot(bs.release_fraction,bs.certified_improvement,marker='o',label='certified economic improvement');axes[1].plot(bs.release_fraction,bs.certified_safe,marker='o',label='finite-cohort risk <= .05');axes[1].set_xlabel('Fraction of unresolved outcomes released');axes[1].set_ylabel('Fraction of off-diagonal tasks');axes[1].set_ylim(0,1);axes[1].set_title('Retrospective information requirement');axes[1].legend(fontsize=8)
    fig.savefig(OUT/'observability.png',dpi=180);fig.savefig(OUT/'observability.svg');plt.close(fig)
    report=f'''# A new research pivot: maintenance observability

## Status and exact proposed contribution

**Candidate contribution: a paired maintenance-policy observability benchmark and an empirical characterization of which full-lifetime policy comparisons remain supportable from intervention-censored outcome summaries.**

This is a concrete new artifact in this project. It is a **potentially novel benchmark/empirical contribution**, not an established novel learning algorithm. Classification: **B — POTENTIALLY NOVEL BUT INSUFFICIENTLY ESTABLISHED**. The artifact and finite-cohort calculations are verified; first-in-literature priority, physically valid intervention feedback and publication-level generalization remain unestablished. The prior RAMPE verdict remains D; its outputs were not edited or relabelled.

The conceptual pivot is from “choose the most reliable policy” to “determine whether the data permit a policy comparison at all”. Changing ensemble weights cannot recover observations that replacement has prevented. Existing research already establishes censoring, Bayesian maintenance learning, partial identification and partially observable control. The contribution candidate is the exact paired resource and empirical question, with transparent information contracts, not those broad ideas.

## What was added

The resource pairs four frozen policies as both logger and target across six engine datasets and Battery CV/LOBO, all original leads and cost settings. There are **9728 policy-pair tasks**, **325632 unit-pair records** in each of the public and sealed files, **29184 cap-sensitivity evaluations**, and **486400 information-budget evaluations**. These are repeated evaluation tasks over 1026 engines and 123 battery cells (battery protocols reuse cells), not that many independent physical assets.

`public_outcomes.csv.gz` exposes logger endpoints, observable logger outcomes and only target outcomes measurable within the outcome-summary observation contract. All unresolved target cost/use/failure entries are NaN. `sealed_truth.csv.gz` preserves evaluator answers separately; it is locally accessible for reproducibility and therefore is not a secure hidden leaderboard. The core evaluator accepts no truth file and rejects nonmissing unresolved outcome fields. A mutation test changes sealed unobserved outcomes without changing the public view or evaluator output.

The mask represents original-policy completion before logger removal, or a complete run-to-failure logger record. It is generated by a retrospective outcome replay. It does **not** pretend to be validated sensor-prefix execution: pending alarms and their known future deadlines could reveal additional information. Raw post-removal trajectories are not used by the public evaluator. This coarsening makes the contract conservative but materially narrower than a deployment-ready benchmark.

## Main empirical result

To avoid trivial self-policy pairs, headline counts use only the **{summary['offdiagonal_tasks']} off-diagonal tasks** and cap5000. The mean observable fraction across tasks is **{summary['observed_fraction_unweighted_tasks']:.2%}**. The full-lifetime evaluator finds **{summary['full_life_improvements']}** target-versus-logger economic improvements; **{summary['certified_improvements']}** can be certified from the censored outcome summaries. **{summary['improvements_not_certified']}** actual improvements remain uncertified. This is a measurement/identification gap, not proof that those policies fail economically.

Deleting unresolved units gives **{summary['complete_case_false_improvements']}** false economic-improvement declarations and **{summary['complete_case_false_safe']}** false finite-cohort risk≤.05 declarations. Treating unresolved units as healthy gives **{summary['healthy_false_improvements']}** false improvement and **{summary['healthy_false_safe']}** false risk declarations. The interval evaluator gives **{summary['interval_false_improvements']}** false improvement and **{summary['interval_false_safe']}** false risk declarations within the tested cohort/model. That zero is an algebraic containment consequence plus a data check, not evidence of future deployment safety.

All eight regimes, including negative results:

{table(d)}

Logger-target summaries:

{table(p[['logger','target','observed_fraction','true_improvement','certified_improvement','complete_case_false_safe','healthy_false_safe']])}

![Observability and retrospective information sensitivity](../out/observability/observability.png)

## Theory and information budget

For observed target cost sum C, useful-life sum T, m unknown outcomes, logging endpoints H_i, rho>1 and a declared cap B:

    rate ∈ [(C+m)/(T+mB), (C+rho*m)/(T+Σunknown H_i)]
    risk ∈ [observed_failures/n, (observed_failures+m)/n].

The upper rate endpoint is a supremum in the continuous-time relaxed outcome model. These formulas are sharp in that coarsened model, not in a fully specified fixed-policy sensor process. Three standard propositions, an economic-sign corollary and constructive opposite-ranking worlds are proved in [THEORY.md](THEORY.md). They do not establish methodological priority.

Caps2000/5000/10000 are declared capped-policy assumptions. All observed original completions are below each cap, verified by construction; they are not physical maximum-life estimates. The cap affects the lower rate endpoint; without a cap and with any unknown outcome the infimum can be zero. The economic upper endpoint is cap-independent. The identification set can only shrink when valid missing outcomes are revealed.

Release uniformly sampled unresolved evaluator outcomes at fractions0/.1/.25/.5/1 and ten seeds. This is retrospective label-budget sensitivity, not a safe physical inspection intervention or an ability to recover a removed asset's true remaining lifetime. No test treats these repeated releases as independent physical studies:

{table(bs)}

For an assumption-free cohort risk≤.05 claim with no observed failures, at least95% of target outcomes must be resolved. This follows from binary missing-outcome bounds and is not a new universal sample-complexity theorem. A large validation set cannot remove this identification obstacle simply by reducing standard errors around a biased point estimator.

## Prior-art distinction and novelty attack

Read [LITERATURE.md](LITERATURE.md) for primary sources, reading scope, and comparisons. Censored lifetime learning already treats the maintenance-learning feedback tradeoff. Nonparametric adaptive replacement already supplies survival/cost bounds. Off-policy evaluation without overlap already uses partial identification. InfraLib already benchmarks infrastructure decisions under partial observation. Censoring sensitivity analysis already benchmarks survival predictors. Those papers prevent a generic “censoring-aware maintenance” novelty claim.

The potentially distinct resource is the **same assets, fixed policy pool and lead/cost settings evaluated under paired full-lifetime and logger-induced outcome-summary views**, with a truth-free decision-certificate API, ambiguity witnesses and controlled additional-information curves. The targeted search did not locate this exact artifact. That is sufficient to motivate a candidate; it is insufficient to assert first-in-literature priority. Unlike a prognosis benchmark, the target is the supportability of a policy economic/risk claim. Unlike an RL simulator, no new transition or intervention model is invented.

The strict RAMPE new-method gate is not silently relaxed to declare a method novel. The new artifact has no novel estimator/theorem claim. Its benchmark originality and scientific utility need resource-oriented review and a stronger sensor/operational validation before an A-level verdict.

## Paper-ready contribution wording

Proposed title: **From Full-Life Scores to Censored Logs: A Paired Maintenance Observability Benchmark**.

Defensible statement: “We provide a paired outcome-summary evaluation resource for maintenance-policy comparison, preserving full-lifetime evaluator truth while withholding outcomes hidden by alternative preventive logging policies. Across all compatible engine and battery settings, we quantify the gap between retrospective economic superiority and comparisons supportable from censored logs. We include model-free finite-cohort identification intervals, leakage checks, ambiguity witnesses and retrospective information-budget curves.”

Potential contributions:

1. A project-original paired logger/target dataset and evaluator that separates observability from prediction uncertainty.
2. A newly measured, fully retained cross-policy observability and false-certification pattern across the existing assets/settings.
3. A reproducible information-release stress test and explicit certificate contract that expose when a point comparison relies on hidden outcomes.

These support a concrete candidate resource/empirical contribution. They do not justify claiming a new survival method, conformal theorem, causal effect or RL mechanism.

## Limitations and remaining novelty gate

The benchmark uses pre-existing public/retrospective run-to-end data and already fitted policies. No raw new physical measurements, causal treatment effects, or independent predictor retraining are added. Caps and continuous-time relaxation are material assumptions. Pairwise completions are not a jointly realizable full-world sensor model. Repeated costs/leads/batch protocols create dependence, so counts and means are descriptive. Complete-case and healthy-label methods are diagnostics, not claimed state-of-the-art survival competitors. Kaplan–Meier/IPCW need censoring/positivity assumptions and are not ruled out when those are justified. General benchmark novelty cannot be proved from unsuccessful exact-keyword searches.

The next required step for a stronger contribution is sensor-prefix replay: run each target causally on the released prefix, expose pending alarms/deadlines, compare contract intervals against a justified survival/censoring model, and replicate on independently logged intervention data. The local files have been added now; their novelty is reported as potential, not guaranteed by the user's request.

Reproduction and schemas: [README.md](README.md). Integrity/test evidence: [verification.json](../out/observability/verification.json). All frozen CAT and RAMPE reports/results remain unchanged.
'''
    Path('observability/REPORT.md').write_text(report,encoding='utf-8');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
