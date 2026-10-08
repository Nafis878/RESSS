# Internal adversarial review

This is an internal assessment, not an external peer review.

1. **The DP is an existing approximate Pareto method.** Correct. One-exact Pareto
   approximation and DP trimming are attributed. The contribution proposed here
   is the specific shared-cohort phase/subset reduction and the guarantees it
   enables. General algorithmic originality is not established.
2. **Heterogeneity was already handled.** The preserved earlier extension only
   solved later-versus-earlier pairs. F1-F3 complete the earlier pairs and finite
   policy selection, with arbitrary positive rational premiums. Exact Pareto mode
   has no polynomial bound; the FPTAS is the polynomial approximation result.
3. **The guarantee concerns another mathematical criterion.** Correct. A bound
   on robust oracle-relative cohort regret does not prove improved realized cost,
   population reliability or deployment safety. The replay shows mean realized
   regret slightly worse than common-cost selection.
4. **The engineering cost labels are invented measurements.** They are explicitly
   constructed public scenarios. No measured failure consequences are claimed.
   Lifetimes come from all 304 frozen cohorts; sealed outcomes are accessed only
   after both decisions are selected. The string-ID correction is retained.
5. **304 cases imply a huge independent sample.** They overlap across settings,
   loggers and splits. No independent-case significance test is reported. The
   win/tie/loss counts are descriptive and cannot establish novelty.
6. **The method certifies every practical case.** It certified all cases in this
   replay only. Synthetic stress cases actually lose nondominated states and
   show nonzero approximation gaps. No universal exactness claim follows.
7. **Exactness is asserted by checking the approximate solver against itself.**
   Small integer cases use full Cartesian lifetime enumeration and continuous
   cases use separately labeled phase endpoints. Larger exact mode is an internal
   Pareto reference, supported by those independent checks but not independent
   proof of global correctness. The constructive argument provides that proof.
8. **Clock refinement bounds noisy failure measurements.** It does not. Observed
   horizons/flags remain exact. No measurement-error or population guarantee is
   claimed. Continuous limits are labeled and compatible approximations supplied.
9. **An exponential frontier proves NP-hardness.** It does not. F5 concerns one
   exact DP representation. Another polynomial scalar optimizer is not excluded.
10. **Removing a manuscript access gap is necessary for journal acceptance.**
    Access gaps affect our originality confidence, but are not a journal rule.
    Peer review can assess a precise, attributed claim. Public deposition is also
    not a prerequisite for journal acceptance or evidence of historical firstness.

Assessment: substantial technical progress, narrower general-mechanism novelty
than a 9/10 claim would imply, and insufficient engineering advantage for a
confident RESS submission. Outcome B is retained.
