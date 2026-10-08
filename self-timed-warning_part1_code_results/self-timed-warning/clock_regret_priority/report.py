"""Attributed extended draft; read preserved manuscript without modifying it."""
import html
import re
import shutil
from pathlib import Path
import pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,Preformatted,KeepTogether
from clock_regret_priority.run import OUT,protect


def manuscript():
    text=Path('clock_regret_linear/MANUSCRIPT.md').read_text(encoding='utf-8')
    text=text.replace('## Two Extremal Worlds and a Clock-Resolution Guarantee',
                      '## Extremal Worlds, Heterogeneous Failure Costs and Sharp Clock Bounds\n\n'
                      'Nafis Wadud Ansari\n\nDaffodil International University\n\nansari2305341800@diu.edu.bd')
    before='Working research draft - 8 October 2026. Authorship and public-release metadata are pending. This document has not been deposited or externally peer reviewed. Historical priority is proposed for assessment, not established.'
    text=text.replace(before,
        'Attributed working research draft - 8 October 2026. Author details were supplied by the researcher. '
        'The publishing destination and release rights remain pending. This document has not been deposited '
        'or externally peer reviewed. Historical priority is proposed for assessment, not established.')
    text=text.replace('We derive a continuous-clock supremum and a uniform 1+1/r approximation guarantee for clock refinement.',
        'We derive a continuous-clock supremum and a uniform 1+1/r approximation guarantee for clock refinement. '
        'A heterogeneous-cost extension replaces the two endpoint worlds with a sorted-premium prefix scan; '
        'a strict interior counterexample shows why the original cost restriction matters. An explicit family '
        'proves the uniform pairwise clock factor sharp.')
    text=text.replace('The proposed distinction is the exact specialized theorem below,',
        'Oracle-relative expected-cost ratios under shared distributional ambiguity and fractional duality '
        'also appear in the newsvendor report of Zhu, Zhang and Ye [9]. '
        'The proposed distinction is the exact specialized theorem below,')
    text=text.replace('No authorship, DOI, accepted publication or public disclosure date is invented.',
        'The present draft uses the author identity supplied by the researcher. No DOI, accepted publication '
        'or public disclosure date is invented.')
    text=text.replace('Heterogeneous failure costs, future sensor-triggered policies,',
        'General full-family heterogeneous-cost selection, future sensor-triggered policies,')
    text=text.replace('The result covers fixed ages, common costs and a stated censoring/clock model.',
        'The complete-family polynomial result covers fixed ages, common costs and a stated censoring/clock model. '
        'Section 8 extends later-versus-earlier pairwise comparisons to asset-specific failure premiums.')
    body,references=text.split('## References',1)
    extra='''## 8. Exact comparisons with asset-specific failure costs

Retain preventive cost one, but allow known positive rational failure premiums q_i, so asset i costs 1+q_i upon failure. The lifetime uncertainty and shared-world objective are unchanged. For a>b use the same E, J, e and m as Section 3. Sort E by increasing q_i and let Q_x be the sum of its x smallest premiums. Define

```
U = T_a0 - m*a + e*(b+1) + sum_(i in J)(H_i+1).
A = C_a0 + sum_(i in E union J)q_i.
D_x = (C_b0+Q_x)*(U-x), 0<=x<=e.
G(a,b) = A*T_b0 / min_x D_x.
```

THEOREM H1. This value is exact and attained. At a minimizing count x, the x cheapest premiums in E fail at b, the remaining E at b+1, J at H_i+1, and other unknowns survive both ages. A standalone comparison uses O(n log n) arithmetic operations, O(n) storage and e+1 objective evaluations.

PROOF. Shared failures can move to b and later-only failures to max(H_i+1,b+1), as before. Every eligible survivor can enter the later-only phase, increasing candidate cost by q_i>0 and not increasing its use, while leaving comparator outcomes fixed. Thus all eligible assets fail by a. Candidate cost A and comparator use T_b0 are then constant. If x assets in E fail at b, candidate use is U-x, and comparator cost is C_b0 plus their premiums. At fixed x, the positive denominator is minimized by the x smallest premiums. All counts are feasible. Scanning them proves the result and constructs its completion. QED.

For common q_i=q, Q_x=qx recovers the concave denominator and two endpoint worlds. With heterogeneous premiums, an interior minimum can occur. For horizons (1,1,1), observed flags (true,false,false), premiums (98,1,100), a=3 and b=2, the denominator scan is:

| Shared count x | Denominator D_x | Candidate/comparator factor |
|---|---:|---:|
| 0 | 707 | 1010/707 |
| 1 | 612 | 505/306 |
| 2 | 1010 | 1 |

Table 2. The unique optimum is x=1 with compatible completion (1,2,3). Retaining only the two common-cost endpoint worlds misses the true maximum. This is a constructed assumption-boundary example, not a real-data performance study.

The earlier-versus-later common-cost prefix theorem is not automatically generalized by H1. The implementation exposes a later-comparison API and does not advertise a polynomial complete-family heterogeneous-cost solver.

## 9. Continuous heterogeneous clocks and sharpness

Let U_c=T_a0-m*a+e*b+sum_(i in J)H_i, and retain A from H1.

```
G_c(a,b) = A*T_b0/(C_b0*U_c), for a>b.
G_r <= G_c <= (1+1/r)*G_r.
```

THEOREM H2. The continuous value and refinement sandwich remain exact with positive heterogeneous premiums. One no-shared limiting world suffices; if m>0, the supremum is unattained. Compatible epsilon completions approach it.

PROOF. In the closure, a shared failure at b can enter the later-only limiting phase, leaving uses unchanged while reducing comparator cost by its q_i>0. All eligible assets can therefore fail later only, giving U_c and the formula. Grid lifetimes are continuous completions. The no-shared grid world has candidate use U_c+m/r and ratio G_c/(1+m/(r*U_c)). Since U_c>=n and m<=n, the stated upper factor follows. QED.

SHARPNESS. Let every asset be censored at H_i=1, a=2,b=1, with arbitrary positive premiums. Then e=0,m=n,U_c=n. If Q=sum_i q_i, G_c=(n+Q)/n and G_r=(n+Q)/(n*(1+1/r)). Hence G_c/G_r=1+1/r exactly. The uniform pairwise factor cannot be improved, even in the common-cost subclass. Sharpness of the common-cost selected-policy factor is not asserted.

Eight added unit-test groups pass. The stored extension evidence comprises 1,000 exhaustive full-clock comparisons, 500 integer and 500 continuous cost-state/exposure-hull comparisons, 200 integer and 200 continuous common-cost reductions, 600 compatible epsilon completions, 1,000 refinement comparisons, and 18 exact sharpness equalities. All match exact rational arithmetic. No heterogeneous real-data gain or new runtime-significance claim is made.

## 10. Updated prior-art assessment and disclosure

The recovered Drent et al. preprint [7], Sections 2-5, studies parametric Bayesian lifetime learning and expected discounted replacement cost. The full published Khan et al. paper [8], Sections 3-5 and Appendix A.2, obtains sharp expected-value bounds through Lipschitz-constrained linear programs. Their inspected theorems do not provide the present rate-ratio/premium-prefix result. Zhu et al. [9] already optimize an oracle-relative cost ratio using a shared uncertain demand distribution, invalidating any broad claim that this research invented that objective principle.

The specialized contribution now includes a heterogeneous-cost theorem, an explicit boundary of the two-world result, and sharpness of the clock factor. Those statements are internally proved and computationally validated. No equivalent was found in the inspected sources. Fox's full old derivation and the separate moment-robust conference manuscript remain unresolved access gaps; unpublished work and alternative terminology are additional coverage limitations. The novelty verdict remains B, potentially novel but insufficiently established, under the project's strict gate. The supplied author identity permits attribution of this draft, while a public deposit and historical-first assessment remain pending. The complete audit and internal reviewer attack are in LITERATURE.md and REVIEW.md.

'''
    references=references.replace('Additional close work, inspected equations, search queries and access limitations are recorded in LITERATURE.md.',
        'Additional close work, inspected equations, search queries and access limitations are recorded in the current and preserved literature audits.')
    references=references.replace('Manuscript authors must verify and supply attribution and public-release metadata before deposit.',
        'The author must supply the intended public destination and confirm release rights before deposit.')
    refs_more='''

[7] Drent, C.; Kapodistria, S.; Boxma, O. (2020). Censored lifetime learning: Optimal Bayesian age-replacement policies. Operations Research Letters 48(6):827-834. Inspected author preprint: EURANDOM 2020-005. https://www.eurandom.tue.nl/wp-content/uploads/2020/04/005-report.pdf

[8] Khan, S.; Saveski, M.; Ugander, J. (2024). Off-policy Evaluation Beyond Overlap: Sharp Partial Identification Under Smoothness. PMLR 235:23734-23757. https://proceedings.mlr.press/v235/khan24b.html

[9] Zhu, Z.; Zhang, J.; Ye, Y. (2006). Newsvendor Optimization with Limited Distribution Information. Author technical report, 18 November 2006. https://web.stanford.edu/~yyye/REVDreport.pdf
'''
    note='Additional close work, inspected equations, search queries and access limitations are recorded in the current and preserved literature audits. Reproduction instructions, protected input hashes and the complete new artifact manifest accompany the source archive. The author must supply the intended public destination and confirm release rights before deposit.'
    references=references.replace(note,'').rstrip()
    text=body+extra+'## References'+references+refs_more+'\n\n'+note+'\n'
    Path('clock_regret_priority/MANUSCRIPT.md').write_text(text,encoding='utf-8')
    return text


def pdf(text):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Body',fontName='Times-Roman',fontSize=10.5,leading=13.6,spaceAfter=7,allowWidows=False,allowOrphans=False))
    styles.add(ParagraphStyle(name='TitlePaper',fontName='Times-Bold',fontSize=19,leading=23,alignment=TA_CENTER,spaceAfter=12))
    styles.add(ParagraphStyle(name='HeadingPaper',fontName='Times-Bold',fontSize=12,leading=15,spaceBefore=10,spaceAfter=7,keepWithNext=True))
    styles.add(ParagraphStyle(name='SmallPaper',fontName='Times-Roman',fontSize=9,leading=11.5,spaceAfter=6))
    styles.add(ParagraphStyle(name='Author',fontName='Times-Roman',fontSize=11,leading=14,alignment=TA_CENTER,spaceAfter=5))
    width=A4[0]-108; lines=text.splitlines(); story=[]; i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1;continue
        if line.startswith('```'):
            i+=1;block=[]
            while i<len(lines) and not lines[i].startswith('```'):
                block.append(lines[i]);i+=1
            story.append(Preformatted('\n'.join(block),ParagraphStyle(name='MathCode',fontName='Courier',fontSize=8.5,leading=10.6,spaceBefore=6,spaceAfter=9)))
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                fields=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-:]+',x) for x in fields):
                    rows.append([Paragraph(html.escape(x),styles['SmallPaper']) for x in fields])
                i+=1
            widths=[width*.10,width*.22,width*.23,width*.26,width*.19] if len(rows[0])==5 else [width*.26,width*.32,width*.42]
            table=Table(rows,colWidths=widths,repeatRows=1)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEF2F5')),
                ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#6D7C8A')),
                ('LINEBELOW',(0,-1),(-1,-1),.6,colors.HexColor('#6D7C8A')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),
                ('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
            block=[table,Spacer(1,8)]
            while i<len(lines) and not lines[i].strip():i+=1
            if i<len(lines) and lines[i].startswith('Table '):
                block.append(Paragraph(html.escape(lines[i].strip()),styles['Body']));i+=1
            story.append(KeepTogether(block));continue
        elif line.startswith('!['):
            name=re.search(r'\]\(([^)]+)\)',line).group(1)
            figure=Image(str(OUT/name))
            ratio=figure.imageHeight/figure.imageWidth
            figure.drawWidth=width;figure.drawHeight=width*ratio
            story.append(figure);story.append(Spacer(1,5))
        elif line.startswith('# '):story.append(Paragraph(html.escape(line[2:]),styles['TitlePaper']))
        elif line.startswith('## '):story.append(Paragraph(html.escape(line[3:]),styles['HeadingPaper']))
        elif line in ['Nafis Wadud Ansari','Daffodil International University','ansari2305341800@diu.edu.bd']:
            story.append(Paragraph(html.escape(line),styles['Author']))
        else:
            block=[line];i+=1
            while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','```','|','![')):
                block.append(lines[i].strip());i+=1
            story.append(Paragraph(html.escape(' '.join(block)),styles['Body']));continue
        i+=1
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Times-Roman',8);canvas.setFillColor(colors.HexColor('#5B6470'))
        canvas.drawString(54,27,'Ansari | Censored replacement regret | Unpublished research draft')
        canvas.drawRightString(A4[0]-54,27,str(doc.page));canvas.restoreState()
    target=OUT/'manuscript.pdf'
    doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=54,rightMargin=54,topMargin=48,bottomMargin=45,
        title='Exact Relative-Regret Age Replacement under Censoring',author='Nafis Wadud Ansari',pageCompression=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=pymupdf.open(target);(OUT/'qa').mkdir(exist_ok=True)
    for j,page in enumerate(reader):page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(OUT/'qa'/f'page-{j+1}.png')
    print(f'Attributed manuscript: {len(reader)} pages; every page rendered.',flush=True)


def main():
    protect()
    for name in ['runtime.png','resolution.png']:
        shutil.copyfile(Path('out/clock_regret_linear')/name,OUT/name)
    pdf(manuscript());protect()


if __name__=='__main__':main()
