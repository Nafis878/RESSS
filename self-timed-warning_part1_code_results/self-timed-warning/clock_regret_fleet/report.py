"""Author a focused, self-contained mathematical working draft and render it."""
import html
import json
import re
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,Preformatted,KeepTogether
from clock_regret_fleet.run import OUT,protect


def charts():
    records=json.loads((OUT/'tolerance_stress.json').read_text())
    labels=['1/10','1/4','1/2']; x=[.1,.25,.5]
    errors=[100*(max(float(r['approximation_factor']) if isinstance(r['approximation_factor'],(int,float))
              else float(__import__('fractions').Fraction(r['approximation_factor']))
              for r in records if r['epsilon']==label)-1) for label in labels]
    retained=[np.median([r['approximate_states_peak']/r['exact_states_peak'] for r in records if r['epsilon']==label]) for label in labels]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})
    fig,axes=plt.subplots(1,2,figsize=(7.0,2.5),layout='constrained')
    axes[0].plot(x,errors,'o-',color='#173E63'); axes[0].set_ylabel('Maximum observed pair gap (%)')
    axes[1].plot(x,retained,'s-',color='#94612D'); axes[1].set_ylabel('Median retained state fraction')
    for ax in axes:
        ax.set_xlabel('Requested tolerance'); ax.set_xticks(x,labels); ax.grid(alpha=.18)
    axes[1].set_ylim(0,1.05)
    fig.savefig(OUT/'tolerance.png',dpi=220); fig.savefig(OUT/'tolerance.svg'); plt.close(fig)


def manuscript():
    engineering=json.loads((OUT/'engineering_summary.json').read_text())
    stress=json.loads((OUT/'stress_summary.json').read_text())
    theory=Path('clock_regret_fleet/THEORY.md').read_text(encoding='utf-8').split('\n',1)[1]
    theory=theory.replace('Use the preserved finite-cohort integer model','Use the finite-cohort integer model')
    theory=theory.replace('the\npreserved exact premium-prefix theorem','the\nexact premium-prefix theorem in Appendix A')
    theory=theory.replace('Complete heterogeneous-cost selection\nmethod','Complete heterogeneous-cost selection\nmethod')
    later=Path('clock_regret_priority/THEORY.md').read_text(encoding='utf-8')
    later=later.split('## Model and theorem H1',1)[1].split('## Scientific interpretation',1)[0]
    text='''# Certified Relative-Regret Replacement for Censored Heterogeneous Fleets

Nafis Wadud Ansari

Daffodil International University

ansari2305341800@diu.edu.bd

Working research draft - 8 October 2026. This manuscript has not been deposited or externally peer reviewed. The specialized originality claim is proposed for assessment; historical priority is not established.

## Abstract

Preventive replacement hides later failure times, and assets can incur different failure consequences. We study oracle-relative total-cost/total-use regret over one shared compatible lifetime completion per record. For arbitrary positive rational failure premiums, we derive an exact subset reduction for earlier-versus-later replacement ages. At each subset cardinality, the objective increases with aggregate premium and decreases with earliest-failure exposure. Applying established approximate Pareto techniques to this reduction yields a fully polynomial-time approximation scheme for complete selection among fixed candidate ages, with feasible extremal completions and a user-controlled 1+epsilon guarantee. An a posteriori certificate charges approximation error only at stages that discard nondominated states; separated score intervals certify an exact minimax decision. We compose optimization and clock-refinement errors into a (1+epsilon)(1+1/r) decision bound. Independent full-clock and phase-endpoint oracles validate small instances. A constructed-cost replay of 304 frozen engineering cohorts certifies all 208 decisions involving multiple candidate ages, while realized performance is mixed and its mean slightly worsens. The proposed contribution is a specialized censored-cohort theorem and certified heterogeneous selector; neither approximate Pareto optimization nor robust replacement is claimed as a new general principle.

## 1. Engineering question and relation to prior work

The question is whether a fixed replacement age can be selected using compatible censored records while retaining distinct asset failure consequences and a verifiable numerical decision bound. A calculation for the recorded fleet can certify how an age compares with its finite oracle under the stated uncertainty model. It cannot establish a future fleet's safety or population-optimal renewal policy without additional assumptions.

Fox [1] establishes minimax absolute renewal cost under fixed-mean or fixed-Laplace-transform distributional ambiguity. His complete supplied letter does not state the present cohort-relative formulas. Nonparametric replacement bounds [2], Bayesian censored lifetime learning [3], shared uncertain dynamics [4] and oracle-relative distributional cost ratios [5] are established antecedents. The moment-robust age-replacement conference abstract [6] concerns absolute average cost and an extremal probability law; its full proof manuscript remains unavailable in this audit.

Approximate Pareto construction is also established. Mittal and Schulz [7] use approximate frontiers for objectives combined via norms. Herzel et al. [8], Section 3 and Theorem 3.1, explicitly develop approximation exact in one objective. The keep-smallest-exposure-in-premium-bucket strategy overlaps those tools. Our proposed distinction is the exact phase/subset reduction for this rate-ratio model, its scalar approximation guarantee and its composition with clock error. A broader new approximation-mechanism claim would be unjustified.

## 2. Cohort criterion and information boundary

There are n>0 records (H_i,delta_i), with H_i>=1 on a positive integer clock. If delta_i=1, L_i=H_i; otherwise L_i>=H_i+1. For a fixed age d, failure at L_i<=d costs 1+q_i, survival costs one, and use is min(L_i,d), with q_i>0 a known rational. All policies share each latent L_i.

```
R_d(L) = [n + sum_i q_i*1{L_i<=d}] / sum_i min(L_i,d).
G(a,b) = sup_(compatible L) R_a(L)/R_b(L).
W(a) = max_(b in candidate ages) G(a,b).
```

For a finite candidate family, the supremum of R_a(L)/min_b R_b(L) equals W(a), by finite maximum/supremum exchange. Select an age minimizing W. The uncertainty set is Cartesian per record; observations and costs are inputs, and sealed lifetimes are excluded from selection. This is a deterministic robust cohort criterion. Neither probability-law estimation, informative-censoring correction nor a fresh-population guarantee is implied.

Later-versus-earlier pairs have an exact sorted-premium formula, reproduced with proof in Appendix A. Common premiums specialize to the two-world theorem. The remaining obstacle to complete heterogeneous selection is the earlier-pair subset tradeoff, addressed next.

## 3. Complete heterogeneous selection: reductions and guarantees

'''+theory+'''

## 4. Validation design and reproducibility

The plan was locked and hashed before implementation outcomes. One thousand fixed-seed small integer cases are checked by complete Cartesian lifetime enumeration, independent of the subset formula. Two hundred full-family cases are checked against complete-world oracle scores, two hundred common-cost cases against the preserved exact implementation, and two hundred continuous pairs against independently labeled endpoint phases. Ten unit-test groups also cover exact rational input validation, positive denominators, feasible witnesses, clock/tolerance composition, permutations, actual nondominated-state removal and an exact-frontier example with 924 points. All checks pass.

In exact mode, the cardinality Pareto DP retains the full frontier and can be exponential. It supplies a larger-instance reference but is not itself an independent oracle. The constructive proof and the independent small oracles are therefore essential. A 30-case stress study uses 12 censored records with H uniform in 1..100, four observed failures at 180,190,200,210, ages 120 and 240, censored premiums 10H plus independent integer jitter 1..50, and observed premiums 300. These choices and all cases are reported; tolerances are 1/2,1/4,1/10.

| Tolerance | Maximum observed pair factor | Median exact/approximate state ratio |
|---|---:|---:|
'''
    for eps in ['1/2','1/4','1/10']:
        item=stress[eps]
        text+=f"| {eps} | {item['max_pair_gap']:.9f} | {item['median_state_ratio']:.3f} |\n"
    text+='''
Table 1. Observed gaps are below the proved worst-case guarantee; they are not universal constants. The finest tolerance is exact on these 30 cases, not necessarily on other inputs. State ratios measure representation size, not a statistically established runtime speedup.

![Tolerance and frontier tradeoff](tolerance.png)

Figure 1. Accuracy and retained-state tradeoffs across the 30 fixed heterogeneous stress cases. Both panels use the same cases and tolerances.

## 5. Engineering lifetime replay with constructed failure costs

All 304 frozen real cohorts are retained: PHM08, FD001-FD004, NCMAPSS6 and Battery. Candidate ages and logging records come from earlier frozen conventional fits and schedules, independently of the evaluation lifetimes. Repeated cost settings, loggers and splits overlap; the cohorts are not 304 independent deployment experiments. Ninety-six cohorts have one candidate age, 184 have two and 24 have three. Limited candidate diversity constrains arbitration headroom.

Measured asset-specific failure-consequence data are unavailable. This study therefore uses the explicitly constructed public scenario q_i=(rho-1)*(1+class_i), with numeric unit ID modulo three; nonnumeric IDs use the UTF-8 SHA-256 integer modulo three. These are scenario labels, not measured engineering costs. The metadata correction and original plan are retained. A tolerance of 1/4 is fixed for all cohorts. Both common-cost and heterogeneous decisions are selected before reading sealed evaluation lifetimes.

All 304 common-cost score reductions match the preserved solver. The final heterogeneous algorithm matches exact-mode decisions in all 304 scenarios and certifies each as a unique minimax decision; 208 involve multiple candidates and 96 are trivial one-age decisions. Heterogeneous premiums change 13 decisions compared with common-cost selection: two in FD002, four in FD004 and seven in Battery. Matching a minimax decision is a criterion-specific certificate, not evidence of lower realized maintenance cost.

Under the heterogeneous scenario costs, relative to common-cost selection, realized oracle-relative cohort regret improves in five cases, ties in 291 and worsens in eight. The mean difference is '''+f"{engineering['mean_realized_relative_regret_change']:.6f}"+''' regret-factor units, favoring common-cost selection. No independence-based significance test is performed on these overlapping cases. The new guarantee does not erase earlier negative maintenance and transfer results.

The initial implementation charged a beta factor even at stages losing no nondominated states. Its retained replay matched exact ages in 298 cases and certified 297. The proved actual-loss-stage refinement changes no tolerances, seeds or premiums. It tightens score intervals and yields the final certificates above. Both versions and their completed outcomes remain available.

## 6. Practical interpretation, limitations and originality

A maintenance analyst can supply a candidate age family and known positive failure premiums, obtain intervals for robust oracle-relative scores, and distinguish a certified exact decision from an approximate decision with explicit tolerance. The clock bound exposes how much numerical time resolution can change the cohort certificate. The interval-separation rule may be valuable when a precise decision is needed without retaining an exponential exact frontier. This is a computational assurance capability, whose engineering value still needs a substantive measured-cost case study.

The present model retains preventive cost one, exact recorded horizons, fixed candidate ages and Cartesian lifetime completions. It does not model downtime, interactions between components, arbitrary preventive costs, sequential interventions, noisy failures or population transfer. Stronger joint restrictions on lifetimes can change sharpness. No NP-hardness, universal runtime advantage, superior realized cost or deployed safety benefit is claimed.

The specialized reductions and guarantees are mathematically supported by constructive proofs and independent numerical checks. The general approximation mechanism overlaps established literature and must be attributed accordingly. The method is proposed as a model-specific contribution, with no claim to invent Pareto approximation or robust replacement. Historical-equivalence coverage remains incomplete for the separate moment-robust conference manuscript. Measured consequence data and prospective engineering validation are needed to assess practical utility beyond the present cost-scenario replay.

## Appendix A. Exact later-pair theorem and continuous sharpness

'''+later+'''

## References

[1] Fox, B. (1966). Letter to the Editor - Age Replacement with Discounting. Operations Research 14(3):533-537. DOI:10.1287/opre.14.3.533. Supplied publisher PDF inspected in full.

[2] Coolen-Schrijner, P.; Coolen, F.; Shaw, S. (2006). Nonparametric adaptive opportunity-based replacement strategies. Journal of the Operational Research Society 57:63-81.

[3] Drent, C.; Kapodistria, S.; Boxma, O. (2020). Censored lifetime learning: Optimal Bayesian age-replacement policies. Operations Research Letters 48(6):827-834. Inspected author preprint: EURANDOM 2020-005.

[4] Petrik, M.; Chow, Y.; Ghavamzadeh, M. (2016). Safe Policy Improvement by Minimizing Robust Baseline Regret. arXiv:1607.03842.

[5] Zhu, Z.; Zhang, J.; Ye, Y. (2006). Newsvendor Optimization with Limited Distribution Information. Author technical report, 18 November 2006.

[6] Shahri Majarshin, S. (2026). A robust age-based replacement problem. LNMB conference abstract. This is an abstract, not an inspected full manuscript.

[7] Mittal, S.; Schulz, A. S. (2008). A General Framework for Designing Approximation Schemes for Combinatorial Optimization Problems with Many Objectives Combined into One. APPROX/RANDOM, LNCS 5171:179-192. DOI:10.1007/978-3-540-85363-3_15.

[8] Herzel, A.; Bazgan, C.; Ruzika, S.; Thielen, C.; Vanderpooten, D. (2021). One-exact approximate Pareto sets. Journal of Global Optimization 80:87-115. DOI:10.1007/s10898-020-00951-7. Section 3 and Theorem 3.1 inspected in primary preprint arXiv:1908.10561.

Data and code availability: a local review archive contains the implementation, plan, protected-input hashes, fixed-case evidence and engineering replay inputs. It has not been publicly deposited. Source links and theorem-level comparisons are recorded in the companion literature audit. No third-party full-text papers are redistributed.
'''
    Path('clock_regret_fleet/MANUSCRIPT.md').write_text(text,encoding='utf-8')
    report=f'''# Completed heterogeneous-fleet investigation

The requested 9/10 novelty claim is not established. The work now contains a
complete heterogeneous selector with a proved FPTAS, exact feasible pair witnesses,
score intervals, actual-loss-stage certificates and a composed clock/tolerance
bound. General Pareto/FPTAS mechanics remain prior art; verdict B is retained.

Ten unit-test groups pass. Stored evidence includes 1,000 independent full-clock
pairs, 200 full families, 200 continuous phase oracles, 304 engineering scenario
replays and 90 tolerance stress evaluations. Common-cost reduction also passes
200 unit-test cases and every engineering replay.

All 208 multi-age engineering decisions are certified exact for the constructed
premium scenarios. There are also 96 trivial one-age cases. Costs are not measured
failure consequences. Decisions change in 13 of 304 cohorts, with realized wins,
ties and losses {engineering['realized_win_tie_loss']}; mean regret change
{engineering['mean_realized_relative_regret_change']:.9f} favors common-cost
selection. No significance test treats overlapping cohorts as independent.

Original evidence and 974 protected artifacts remain unchanged. The initial
conservative-certificate implementation/results are retained. The string-ID
scenario correction is documented. No deployment, public disclosure, reviewer
endorsement, historical firstness or 9/10 originality was created or assumed.

Exact contribution proposed for review: a complete heterogeneous-cost method for
shared censored-cohort oracle-relative replacement, with an exact subset
characterization, one-sided approximation bound, measurable loss-stage certificate
and a joint clock/optimization decision guarantee. This is specialized use of
established approximation tools. A materially stronger RESS claim still needs
measured consequence data and a convincing engineering demonstration; higher
scores cannot be obtained by suppressing these negative results.
'''
    Path('clock_regret_fleet/REPORT.md').write_text(report,encoding='utf-8')
    return text


def escaped(text):
    text=html.escape(text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    return text.replace('`','')


def pdf(text):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyPaper',fontName='Times-Roman',fontSize=10.5,leading=13.8,spaceAfter=7,allowWidows=False,allowOrphans=False))
    styles.add(ParagraphStyle(name='BodyLead',parent=styles['BodyPaper'],keepWithNext=True))
    styles.add(ParagraphStyle(name='TitlePaper',fontName='Times-Bold',fontSize=18,leading=22,alignment=TA_CENTER,spaceAfter=12))
    styles.add(ParagraphStyle(name='HeadPaper',fontName='Times-Bold',fontSize=12,leading=15,spaceBefore=11,spaceAfter=7,keepWithNext=True))
    styles.add(ParagraphStyle(name='SmallPaper',fontName='Times-Roman',fontSize=9,leading=11.5,spaceAfter=5))
    styles.add(ParagraphStyle(name='AuthorPaper',fontName='Times-Roman',fontSize=11,leading=14,alignment=TA_CENTER,spaceAfter=5))
    width=A4[0]-108; lines=text.splitlines(); story=[]; i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if line.startswith('```'):
            i+=1; block=[]
            while i<len(lines) and not lines[i].startswith('```'):
                block.extend(textwrap.wrap(lines[i],width=85,subsequent_indent='  ',replace_whitespace=False,drop_whitespace=False) or [''])
                i+=1
            story.append(KeepTogether([Preformatted('\n'.join(block),ParagraphStyle(name='MathPaper',fontName='Courier',fontSize=8,leading=10,spaceBefore=5,spaceAfter=8))]))
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                fields=[s.strip() for s in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch('[-:]+',s) for s in fields):
                    rows.append([Paragraph(escaped(s),styles['SmallPaper']) for s in fields])
                i+=1
            table=Table(rows,colWidths=[width*.20,width*.40,width*.40],repeatRows=1)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEF2F5')),
                ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#173E63')),
                ('LINEBELOW',(0,-1),(-1,-1),.6,colors.HexColor('#173E63')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            block=[table,Spacer(1,6)]
            while i<len(lines) and not lines[i].strip(): i+=1
            if i<len(lines) and lines[i].startswith('Table '):
                block.append(Paragraph(escaped(lines[i]),styles['BodyPaper'])); i+=1
            story.append(KeepTogether(block)); continue
        elif line.startswith('!['):
            name=re.search(r'\]\(([^)]+)\)',line).group(1)
            figure=Image(str(OUT/name)); ratio=figure.imageHeight/figure.imageWidth
            figure.drawWidth=width; figure.drawHeight=width*ratio
            block=[figure,Spacer(1,5)]; i+=1
            while i<len(lines) and not lines[i].strip(): i+=1
            if i<len(lines) and lines[i].startswith('Figure '):
                block.append(Paragraph(escaped(lines[i]),styles['BodyPaper'])); i+=1
            story.append(KeepTogether(block)); continue
        elif line.startswith('# '): story.append(Paragraph(escaped(line[2:]),styles['TitlePaper']))
        elif line.startswith('## '): story.append(Paragraph(escaped(line[3:]),styles['HeadPaper']))
        elif line in ['Nafis Wadud Ansari','Daffodil International University','ansari2305341800@diu.edu.bd']:
            story.append(Paragraph(escaped(line),styles['AuthorPaper']))
        else:
            block=[line]; i+=1
            while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','```','|','![')):
                block.append(lines[i].strip()); i+=1
            next_nonempty=i
            while next_nonempty<len(lines) and not lines[next_nonempty].strip(): next_nonempty+=1
            style=styles['BodyLead'] if next_nonempty<len(lines) and lines[next_nonempty].startswith('```') else styles['BodyPaper']
            story.append(Paragraph(escaped(' '.join(block)),style)); continue
        i+=1
    def footer(canvas,doc):
        canvas.saveState(); canvas.setFont('Times-Roman',8); canvas.setFillColor(colors.HexColor('#5B6470'))
        canvas.drawString(54,27,'Ansari | Certified heterogeneous replacement | Unpublished draft')
        canvas.drawRightString(A4[0]-54,27,str(doc.page)); canvas.restoreState()
    target=OUT/'manuscript.pdf'
    doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=54,rightMargin=54,topMargin=48,bottomMargin=45,
        title='Certified Relative-Regret Replacement for Censored Heterogeneous Fleets',author='Nafis Wadud Ansari')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=pymupdf.open(target); qa=OUT/'qa'; qa.mkdir(exist_ok=True)
    for j,page in enumerate(reader): page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(qa/f'page-{j+1}.png')
    (OUT/'pdf_qa.json').write_text(json.dumps({'pages':len(reader),'rendered_pages':len(reader),'visual_inspection_complete':False},indent=2))
    print(f'Manuscript authored and rendered: {len(reader)} pages.',flush=True)


def main():
    protect(); charts(); pdf(manuscript()); protect()


if __name__=='__main__': main()
