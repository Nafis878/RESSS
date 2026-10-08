# Attention and focus-certificate priority audit

Audit: 8 October 2026. Primary sources, targeted search and citation chaining.
This is a bounded audit, not a systematic review or proof of historical firstness.

| Primary work | Inspected material | Overlap and claim boundary |
|---|---|---|
| [Vaswani et al., Attention Is All You Need (2017)](https://arxiv.org/abs/1706.03762) | Primary abstract/metadata | Transformers and attention are established; no architecture novelty claimed. |
| [Zaheer et al., Deep Sets (2017)](https://papers.neurips.cc/paper/6931-deep-sets) | Proceedings abstract | Pooled set representations are established. Our pooled ablation follows this general approach. |
| [Lee et al., Set Transformer (2019)](https://proceedings.mlr.press/v97/lee19d.html) | Proceedings page and author PDF | Set attention and permutation-invariant processing are established. Our token scores are equivariant; top-k index ties need a declared tie rule. |
| [Kool, van Hoof and Welling, Attention, Learn to Solve Routing Problems! (2019)](https://arxiv.org/abs/1803.08475) | Primary abstract and conference PDF | Attention-guided combinatorial heuristics are established. A maintenance application does not create a new attention mechanism. |
| [Noot, Martin and Birmele, LSTM and Transformers based methods for Remaining Useful Life Prediction considering Censored Data (2025)](https://papers.phmsociety.org/index.php/ijphm/article/download/4260/2619) | Full primary PDF, front matter and architecture/censoring discussion | Uses censored RUL information with a Transformer and conformal intervals. Our task is public-cohort adversarial optimization, not RUL prediction. A broad censored-maintenance Transformer claim is rejected. |
| [Lin et al., Learning Scenario Reduction for Two-Stage Robust Optimization with Discrete Uncertainty (2026)](https://arxiv.org/html/2605.14494v1) | Full primary HTML; Sections 3, 4.1, 4.2 and related-work references inspected | PRISE greedily chooses scenarios by reduced-objective contribution; NeurPRISE uses GNN/Transformer interactions and learned rankings. This is close prior art against learned attention-based robust search reduction. Our assets induce subsets in a rate quotient, rather than discrete two-stage recourse scenarios. That distinction alone does not establish originality. |
| [Goerigk and Khosravi, Optimal Scenario Reduction for One- and Two-Stage Robust Optimization (2022 preprint; 2023 journal version)](https://arxiv.org/pdf/2209.00499) | Full primary PDF available; Theorems 1, 2 and 8 examined | Multiplicative guarantees for reduced robust uncertainty sets already exist. The inspected statements use cost-vector domination/convex-hull conditions. They do not display our omitted-premium formula; generic certification novelty is rejected. |
| [Aigner et al., Scenario Reduction for Distributionally Robust Optimization (2025; v3 March 2026)](https://arxiv.org/html/2503.11484v3) | Full primary HTML available; Assumptions 2.1, 2.2 and Theorem 2.4 examined | Projection/aggregation of ambiguity sets with multiplicative guarantees is established. The proof uses monotonicity, homogeneity and representative-scenario bounds. We require a model-specific shared-use/cost calculation; no claim is made that generic scenario-reduction bounds are new. |

Additional publisher abstracts checked: a 2024 Bayesian adversarial probsparse
Transformer in RESS, and a 2026 uncertainty-aware hybrid Transformer with dropout
and conformal prediction. These corroborate broad application overlap; their
full methods were not used to assert equivalence with our theorem.

The precise candidate is A1's factor
`((C_a+Q_tail)*C_b)/(C_a*(C_b+Q_tail))`, its sharpness family, and the
premium-optimal focus/budget characterization for this finite-cohort ratio.
No inspected primary statement was identified with exactly these results.
That negative search outcome is weak evidence: reparameterizations, older
reliability/robust fractional optimization work, inaccessible and unpublished
equivalents remain possible. A1 may be a useful specialized corollary rather
than a substantial stand-alone methodological advance. A specialist equivalence
review remains necessary to judge this.

The 1966 Fox text was resolved in the preceding local Fox audit. Do not retain
older reports' now-stale claim that that PDF is unavailable. The separate 2026
LNMB moment-robust replacement full derivation remains an earlier-stage access
gap; the abstract alone does not establish its exact equivalence or difference.
Earlier shared-world relative-regret, censored maintenance, partial-identification
and FPTAS prior art remains attributed in the protected stage audits.

## Search record

Queries included Transformer/censored RUL, attention/minimax regret maintenance,
attention/robust scenario selection, learned combinatorial optimization,
set attention, certified neural guidance, omitted scenario/relative-regret
bounds, robust coresets, and exact titles above. Citation chaining from Lin et
al. located the two robust scenario-reduction guarantee papers. Narrow searches
for omitted premium/censored relative regret returned no matching formula;
irrelevant search results are not evidence of novelty.

## Verdict

Attention architecture, learned robust scenario ranking, greedy search and
generic interval intersection are **established prior art**. A1-A4 are
**proved model-specific candidate results**, not established original results.
Strict project verdict remains **B: potentially novel but insufficiently
established**. No publication, public priority date, independent review or
9/10 originality has been created by this audit.
