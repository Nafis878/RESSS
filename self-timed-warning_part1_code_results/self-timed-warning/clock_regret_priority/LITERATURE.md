# Follow-up theorem-level novelty audit

8 October 2026. Read together with the preserved
`clock_regret_linear/LITERATURE.md`. Primary documents recovered here are
cached privately with retrieval status and SHA-256. Full third-party papers are
excluded from the review archive. Differences below are comparisons of inspected
formulations, rather than proof that no alternative derivation exists anywhere.

## Previously unresolved primary texts

**Drent, Kapodistria and Boxma (2020), Censored lifetime learning: Optimal Bayesian
age-replacement policies.** [Primary EURANDOM preprint, 2020-005](https://www.eurandom.tue.nl/wp-content/uploads/2020/04/005-report.pdf)
was recovered in full (9 PDF pages). Sections 2-5 were inspected: newsboy lifetime
family, gamma updating, equations (4)-(6) for expected discounted dynamic cost,
Theorem 1 on value monotonicity, Theorem 2 on learning consistency, and Theorem 3
on myopic convergence. These do not state the deterministic compatible-cohort
ratio theorem or premium-prefix scan. Parametric Bayesian prediction and adaptive
sampling are established; neither is claimed new. This closes the earlier author
preprint access gap; it does not imply a line-by-line inspection of the final
publisher version. The [published record](https://www.sciencedirect.com/science/article/pii/S016763772030153X)
confirms ORL 48(6):827-834, DOI 10.1016/j.orl.2020.10.005.

**Khan, Saveski and Ugander (2024), Off-policy Evaluation Beyond Overlap: Sharp
Partial Identification Under Smoothness.** The [full published PMLR PDF](https://raw.githubusercontent.com/mlresearch/v235/main/assets/khan24b/khan24b.pdf)
was recovered (24 pages). Sections 3-5, Theorem 4.5, Appendix A.2 and A.1(c) were
inspected. Their linear objective averages conditional rewards; Lipschitz metric
constraints yield a noninteraction envelope and asymptotic population bounds.
Our joint failure phases produce a quotient involving four totals, with a
cardinality/premium denominator. Their closed form does not directly reproduce
that optimization. Sharp partial identification, latent potential outcomes,
efficient bound computation and limiting constructions are prior art. This closes
the final-PDF access gap; their preprint was also recovered for version checking.

**Zhu, Zhang and Ye (2006), Newsvendor Optimization with Limited Distribution
Information.** The [primary author report](https://web.stanford.edu/~yyye/REVDreport.pdf)
defines an oracle-relative expected-cost ratio under moment/support ambiguity.
Section 2 interchanges the comparator and uncertainty maxima and uses fractional
duality; Lemmas 1-2 give closed forms. These were inspected directly. This is
stronger prior art than simply citing generic minimax regret: shared-world
oracle ratios and finite extremal representations were already used in inventory
optimization. Its stochastic newsvendor cost is piecewise linear in demand,
with no replacement-use denominator or per-record right-censoring constraints.
No premium-prefix or clock-refinement statement was found in the inspected
results. The objective principle must be attributed; a broad new-ratio claim is
rejected. Retrieval metadata records the complete 35-page report.

## Remaining access gaps

**Fox (1966), Age Replacement with Discounting.** The [primary publisher abstract](https://pubsonline.informs.org/doi/abs/10.1287/opre.14.3.533)
establishes discounted minimax replacement. Publisher PDF retrieval returned
403; the JSTOR PDF endpoint returned a non-PDF response. Cached publisher text
provided the introduction, rather than the complete derivation; browser PDF
screenshots did not provide usable page content. The full old derivation remains
unresolved. No paywall or access control was bypassed. The NASA bibliographic
digest is secondary and was not treated as the original proof.

**Shahri Majarshin (2026), A robust age-based replacement problem.** The
[primary LNMB abstract](https://www.lnmb.nl/conferences/2026/abstracts.html)
describes first/second-moment ambiguity, long-run absolute cost and an extremal
two-point distribution. Searches and the [primary institutional publication page](https://research.tue.nl/en/persons/sina-shahri-majarshin/)
did not locate its full manuscript. The institution lists a separate robust
replacement MDP article already inspected in the earlier audit. A probability
distribution supported on two times and two entire cohort completions are
different objects, but the unavailable manuscript prevents a complete proof
comparison. No claim about unpublished results is justified.

## Actual queries in this follow-up

1. `"Censored life-time learning" pdf`
2. `"Fox" "Age Replacement with Discounting" pdf`
3. `"A robust age-based replacement problem" Shahri`
4. `"Off-policy Evaluation Beyond Overlap" pdf Khan Saveski Ugander`
5. `"Censored lifetime learning" Drent pdf`
6. `"Censored life-time learning" Drent Kapodistria Boxma`
7. `"Shahri Majarshin" "moments" replacement`
8. `"Age Replacement with Discounting" "minimax"`
9. `"Shahri Majarshin" "robust age" paper`
10. `"replacement" "relative regret" "censored"`
11. `"age replacement" "minimax regret" algorithm`
12. `"age replacement" "worst-case ratio"`
13. `"Age Replacement with Discounting" "RAND"`
14. `"Sina Shahri Majarshin" research publications`
15. `"censored" "replacement" "heterogeneous costs" regret`
16. `"replacement" "relative regret" lifetime robust optimization`
17. `"age replacement with discounting" "65-22"`
18. `"replacement" "censored" "heterogeneous" "regret"`
19. `"age replacement" "failure costs" "robust"`
20. `"censored" "cost-rate" "regret"`
21. `"age replacement" "regret" "robust" censored`
22. `"relative regret" "fractional" optimization`
23. `"censored" "replacement" "failure premiums"`
24. `"A robust age-based replacement problem" -site:lnmb.nl`

Results were filtered to relevant primary sources before relying on technical
claims. Irrelevant keyword hits and search-engine silence were not evidence of
originality. Citation chaining found the 2006 inventory ratio formulation.

## Claim assessment

| Claim | Mathematical status | Literature separation | Allowed wording |
|---|---|---|---|
| Minimax replacement / relative regret / shared uncertainty | Established prior art | Equivalent broad ideas located | Cite; never claim invention |
| Exact two-world integer later-pair theorem in this censored cohort model | Constructive proof and exhaustive/independent validation | No equivalent inspected statement; two material full-text gaps remain | Derived specialized result; proposed novelty |
| Sorted-premium heterogeneous later-pair theorem | New constructive derivation; exact witnesses; 1,000 exhaustive and 500 integer state comparisons | No equivalent found in inspected formulations or specific query results | Precise candidate extension, not universally established priority |
| Continuous heterogeneous limit and failure of the unchanged two-world rule | Proof, strict interior counterexample and 500 continuous state comparisons | No same inspected theorem found | State exact model and theorem scope |
| Sharp uniform 1+1/r pairwise clock factor | Proof of upper bound plus exact attaining family | No same inspected statement found | Mathematical sharpness; not a statistical novelty test |

The strict novelty gate is not satisfied conclusively because the final historical
equivalence check remains incomplete. **Verdict B remains appropriate.** The new
extension and sharpness theorem strengthen the submission's concrete content;
they do not justify changing the historical verdict merely to satisfy a desired
answer. Independent expert assessment has not occurred. It is evidence that
could strengthen a claim, rather than a substitute for a correct proof.

## Public priority

The user supplied Nafis Wadud Ansari, Daffodil International University, and
ansari2305341800@diu.edu.bd for authorship. The attributed draft now uses those
details. A repository/preprint destination is still pending. No public record,
DOI, reviewer endorsement or accepted-paper status was created. A verified
dated disclosure can establish a public disclosure record while leaving
first-in-literature originality a separate assessment.
