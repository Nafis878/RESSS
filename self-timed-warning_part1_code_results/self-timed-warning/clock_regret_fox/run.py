"""Verify the supplied-source addendum without changing any prior artifact."""
from pathlib import Path
from fractions import Fraction
from itertools import product
import hashlib
import json
from clock_regret_linear.core import select
from clock_regret_priority.heterogeneous import later_pair, rate_ratio

OUT = Path('out/clock_regret_fox')
SRC = Path(r'C:\Users\UseR\Downloads\fox-1966-letter-to-the-editor-age-replacement-with-discounting.pdf')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protected = json.loads((OUT/'protected_before.json').read_text())
    checks = {}
    checks['958_prior_artifacts_unchanged'] = len(protected)==958 and all(
        sha(path)==value for path,value in protected.items())
    source = json.loads((OUT/'source_record.json').read_text())
    checks['supplied_source_unchanged'] = sha(SRC)==source['sha256']
    checks['all_five_journal_pages_rendered'] = all(
        (OUT/'source_qa'/f'page-{i}.png').is_file() for i in range(2,7))

    # No censoring: exactly one compatible world, independently evaluated.
    answer = select([10],[True],[8,20],2)
    rates = [Fraction(1,8),Fraction(2,10)]
    scores = [max(value/other for other in rates) for value in rates]
    checks['known_cohort_exact_scores'] = list(answer['scores'])==scores==[Fraction(1),Fraction(8,5)]
    checks['known_cohort_selects_preventive_age_8'] = int(answer['chosen'])==0

    # Fox: alpha=lambda=log(2), nu=1/2, c1=1, c2=2.
    # At integer age a, z=exp(-2*alpha*a)=4**(-a), phi=1,
    # delta=(1+z)/2. Thus risk=2/(1-z)>failure-only risk 2.
    discounted = []
    for a in [1,2,8,20]:
        z = Fraction(1,4**a)
        phi = z + (1-z)
        delta = z + (1-z)/2
        risk = phi/(1-delta)
        assert risk==2/(1-z) and risk>2
        discounted.append({'age':a,'phi':str(phi),'delta':str(delta),'risk':str(risk)})
    checks['fox_exponential_discount_identity'] = True

    h=(1,1,1); flags=(True,False,False); premiums=(98,1,100)
    result=later_pair(h,flags,3,2,premiums)
    brute=max(rate_ratio((1,x,y),3,2,premiums) for x,y in product(range(2,5),repeat=2))
    checks['heterogeneous_interior_full_enumeration'] = result.ratio==brute==Fraction(505,306)
    checks['heterogeneous_endpoints_are_strictly_insufficient'] = (
        result.shared_count==1 and result.denominators==(Fraction(707),Fraction(612),Fraction(1010))
        and max(Fraction(1010,707),Fraction(1))<brute)

    # Produce a new working Markdown version, preserving the frozen old draft.
    paper=Path('clock_regret_priority/MANUSCRIPT.md').read_text(encoding='utf-8')
    old='Minimax replacement dates at least to Fox [2];'
    new=('Fox [2], Theorem 5, proves failure-only minimax replacement for absolute '
         'discounted cost under fixed-Laplace-transform ambiguity and average cost '
         'under fixed-mean ambiguity. Its full supplied text has now been inspected; '
         'it does not state the present finite-cohort oracle-relative theorem;')
    assert paper.count(old)==1
    paper=paper.replace(old,new)
    old='The full constructive proofs are in THEORY.md.'
    assert paper.count(old)==1
    paper=paper.replace(old,'The full common-cost constructive proofs are in clock_regret_linear/THEORY.md; heterogeneous proofs are in clock_regret_priority/THEORY.md.')
    old=("Fox's full old derivation and the separate moment-robust conference manuscript remain unresolved access gaps; "
         'unpublished work and alternative terminology are additional coverage limitations.')
    assert paper.count(old)==1
    paper=paper.replace(old,('The supplied full Fox paper has now been inspected, closing that access gap. '
        'Its five theorems concern discounted or average absolute renewal cost, '
        'hazard-based optimization and discount removal; its minimax proof uses '
        'an exponential distribution witness. They do not state the present '
        'two-world, premium-prefix or clock-factor results. The separate '
        'moment-robust conference manuscript remains a full-text access gap; '
        'unpublished work and alternative terminology are additional coverage limitations.'))
    paper += ('\n\nSupplied-source addendum (8 October 2026): see clock_regret_fox/LITERATURE.md '
              'for the complete Fox theorem map, uncertainty-class distinctions, '
              'checked separating example and source-integrity record. '
              'Earlier frozen PDFs predate this addendum.\n')
    Path('clock_regret_fox/MANUSCRIPT.md').write_text(paper,encoding='utf-8')
    checks['updated_manuscript_closes_only_fox_gap'] = (
        old not in paper and 'remains a full-text access gap' in paper
        and 'novelty verdict remains B' in paper)
    checks['prior_artifacts_unchanged_after_addendum'] = all(
        sha(path)==value for path,value in protected.items())
    assert all(checks.values()),checks
    evidence={'cohort':{'known_lifetime':10,'ages':[8,20],
                       'rates':list(map(str,rates)),'oracle_relative_scores':list(map(str,scores)),
                       'selected_age':8},
              'fox_discounted_exponential_specialization':{
                  'alpha':'log(2)','lambda':'log(2)','nu':'1/2',
                  'planned_cost':1,'failure_cost':2,'failure_only_risk':'2','finite_ages':discounted},
              'heterogeneous':{'horizon':h,'observed_failure':flags,'premiums':premiums,
                  'candidate_age':3,'comparator_age':2,'full_clock_enumeration_value':str(brute),
                  'prefix_value':str(result.ratio),'witness':result.witness,'shared_count':result.shared_count,
                  'denominators':list(map(str,result.denominators))}}
    (OUT/'comparison_examples.json').write_text(json.dumps(evidence,indent=2))
    verification={'date':'2026-10-08','checks':checks,'passed':sum(checks.values()),
                  'source_visual_inspection':'All relevant journal pages 533-537 inspected; article is scanned.',
                  'fox_full_text_gap_closed':True,'remaining_identified_full_manuscript_gaps':1,
                  'novelty_verdict':'B','historical_priority_established':False,
                  'public_disclosure_created':False}
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2))
    files=[p for directory in [Path('clock_regret_fox'),OUT] for p in directory.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and p.name!='completion_manifest.json']
    manifest={'date':'2026-10-08','protected_artifacts_unchanged':len(protected),
              'fox_gap_closed':True,'novelty_verdict':'B','checks_passed':sum(checks.values()),
              'sha256':{p.as_posix():sha(p) for p in sorted(files)}}
    (OUT/'completion_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(verification,indent=2))


if __name__=='__main__':
    main()
