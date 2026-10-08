"""Evidence-linked working paper, tables and scientific figures."""
from pathlib import Path
import json
from html import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Preformatted,KeepTogether,Image
from clock_regret_attention.run import OUT,protect

TITLE='Certified Focus Search for Relative-Regret Replacement from Censored Fleets'
SUBTITLE='Attention ablations, sharp omission bounds and a complete-family fallback'


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def figure():
    rows=read('budget-summary.json'); fig,axes=plt.subplots(2,2,figsize=(8.4,5.2),constrained_layout=True)
    for col,split in enumerate(['id','shift']):
        for method,color,mark in [('premium','#4477aa','o'),('attention','#aa3377','s'),('sequential_greedy','#228833','^')]:
            group=[r for r in rows if r['split']==split and r['method']==method]
            for row,metric in [(0,'mean_log_gap'),(1,'mean_certificate_factor')]:
                axes[row,col].plot([r['budget'] for r in group],[r[metric] for r in group],marker=mark,color=color,label=method.replace('_',' '))
        axes[0,col].set_title('ID' if split=='id' else 'Shift')
        axes[0,col].set_yscale('symlog',linthresh=.005)
        axes[0,col].set_ylabel('Mean log(exact / focused)')
        axes[1,col].set_ylabel('Mean certificate factor')
        for row in range(2):
            axes[row,col].set_xticks([0,1,2,4,8]); axes[row,col].set_xlabel('Focused eligible assets k')
            axes[row,col].grid(alpha=.2)
    axes[0,0].legend(fontsize=8)
    fig.savefig(OUT/'budget_ablations.png',dpi=180); plt.close(fig)


def build():
    protect();figure(); width=A4[0]-108; story=[]; md=[]
    body=ParagraphStyle('Body',fontName='Times-Roman',fontSize=10.5,leading=13.4,spaceAfter=7)
    heading=ParagraphStyle('Heading',fontName='Times-Bold',fontSize=13,leading=16,spaceAfter=9)
    small=ParagraphStyle('Small',fontName='Times-Roman',fontSize=8.7,leading=11,spaceAfter=5)
    cell=ParagraphStyle('Cell',fontName='Times-Roman',fontSize=8.6,leading=10.6)
    code=ParagraphStyle('Code',fontName='Courier',fontSize=8.1,leading=11,spaceAfter=7)
    def p(text,style=body):story.append(Paragraph(escape(text),style));md.append(text+'\n')
    def h(text):story.append(Paragraph(escape(text),heading));md.append('## '+text+'\n')
    def eq(text):story.append(KeepTogether([Preformatted(text,code)]));md.append('```\n'+text+'\n```\n')
    def table(headers,rows,widths=None):
        data=[[Paragraph(escape(str(v)),cell) for v in row] for row in [headers]+rows]
        t=Table(data,colWidths=widths or [width/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6edf2')),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#576b7d')),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('TOPPADDING',(0,0),(-1,-1),5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7f8')])]))
        story.extend([t,Spacer(1,9)]);md.append('| '+' | '.join(map(str,headers))+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+
             '\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n')
    def page():story.append(PageBreak());md.append('\n---\n')
    p(TITLE,ParagraphStyle('Title',fontName='Times-Bold',fontSize=19,leading=23,spaceAfter=9))
    p(SUBTITLE,ParagraphStyle('Subtitle',fontName='Times-Italic',fontSize=12,leading=15,spaceAfter=12))
    p('Nafis Wadud Ansari | Daffodil International University\nansari2305341800@diu.edu.bd',small)
    p('Working paper and research audit | 8 October 2026 | Historical novelty provisional',small)
    h('Abstract')
    p('Right censoring creates shared uncertainty across replacement ages. We study focused adversarial search for the ratio of two cohort cost rates, while retaining every unresolved asset in the true ambiguity set. We derive an omitted-premium factor valid for any learned or deterministic focus, an asymptotically sharp family, and a premium-optimal focus and minimum certified budget characterization. Intersecting this bound with the previous complete-family FPTAS preserves exact feasible witnesses and its decision tolerance. A fixed attention experiment improves proposal quality over premium ranking and a capacity-matched pointwise MLP, but a sequential greedy challenger has lower mean gaps. Retrained pooling/context ablations and validation selection favor greedy; 600 fresh synthetic cohorts confirm its small proposal advantage over premium ranking. Attention is optional guidance, not the source of the guarantee. These are model-specific candidate mathematical results; established architectural novelty, engineering benefit and historical priority are not claimed.')
    h('1. Scope and contribution boundary')
    p('Record i has positive integer horizon H_i and observed-failure flag delta_i. Compatible latent lives obey L_i=H_i when observed, and L_i>=H_i+1 otherwise. Every age uses the same life vector. Preventive cost is one and failure premium q_i is a positive exact rational. The ambiguity set is Cartesian; no iid survival law is fitted.')
    eq('R_d(L) = [n + sum_i q_i 1{L_i <= d}] / sum_i min(L_i,d)\nG(a,b) = sup_compatible_L R_a(L)/R_b(L)\nW(a) = max_b G(a,b); choose an age minimizing W(a).')
    p('The contribution proposed for review is the specialized focus certificate and its limits, not Transformers, minimax regret, scenario reduction or generic interval composition. The existing heterogeneous solver, continuous-clock results and earlier negative engineering outcomes are retained. This follow-up does not extend the certificate to sensor policies, intervention dynamics or future populations.')
    page();h('2. Exact subset reduction and focused search')
    p('Fix a<b. Let C_a,C_b be total costs when all censored assets survive both ages; let T_a,T_b be corresponding total uses, including every known failure. Thus C_a<=C_b. Eligible shared failures are E={i: delta_i=0, H_i<a}. A subset S of E fails at H_i+1; other censored assets survive b. Write Q(S)=sum_(i in S)q_i and s(S)=sum_(i in S)(H_i+1).')
    eq('f(S) = (C_a+Q(S))*(T_b-b*|S|+s(S)) /\n       ((C_b+Q(S))*(T_a-a*|S|+s(S)))\nG(a,b) = max_(S subset E) f(S).')
    p('Reduction justification. A censored failure in (a,b] leaves the earlier rate unchanged while increasing later cost and decreasing later use, so survival is at least as adversarial. Within a shared-failure subset, costs are fixed and the exposure quotient is B/A with B>=A. Its derivative with respect to the sum of shared uses is (A-B)/A^2<=0; earliest compatible failures maximize it. Lifetimes beyond b are equivalent for this pair. These observations give the finite subset representation without a physical life cap.')
    p('For an arbitrary focus F subset E, enumerate only S subset F and define g_F=max f(S). All unfocused assets remain in the baseline costs and uses. Focus affects computation, not what is considered compatible. A maximizing subset gives a life vector attaining g_F exactly. Floating-point attention logits are used only to rank indices; certificate arithmetic uses exact fractions.')
    h('Theorem A1. Selector-independent omitted-premium bound')
    eq('Q_tail = sum_(i in E minus F) q_i\nkappa_F = ((C_a+Q_tail)*C_b)/(C_a*(C_b+Q_tail))\ng_F <= G(a,b) <= kappa_F*g_F.')
    p('Proof. Split a maximizing S into S_F=S intersect F and its tail. Add tail shared failures one at a time at times t<=a. Each replaces uses (a,b) with (t,t). Before addition B/A<=b/a because every asset has min(L,b)<=b*min(L,a)/a. For t<a, (b-t)/(a-t)>=b/a, so removing this pair cannot increase B/A. For t=a only B decreases. The cost quotient multiplier, with x=Q(S_F), y=Q(S minus F), is')
    eq('K(x,y) = ((C_a+x+y)*(C_b+x))/((C_b+x+y)*(C_a+x))\n       = 1 + y*(C_b-C_a)/((C_a+x)*(C_b+x+y)).')
    p('K increases in y and decreases in x. Hence f(S)<=K(0,Q_tail)f(S_F)<=kappa_F*g_F. Every focused subset is compatible, proving the lower bound and attaining witness. This proof holds even for an adversarial, untrained or shifted selector. It is deterministic containment, not a statistical confidence interval.')
    page();h('3. Sharpness, optimal focus and complete-family integration')
    h('A2. A sharp uniform factor')
    p('Take two records: censored H=a-1 with premium 1, and known failure at b=a+1 with premium 3, a>=2. With empty focus, C_a=2,C_b=5,Q_tail=1 and kappa=5/4. Direct evaluation of the two subsets gives')
    eq('g_F = 2*b/(5*a)\nG/g_F = (5/4)*(1-1/(2*b)) -> 5/4.')
    p('The shared-failure subset is strictly optimal for every a>=2. A smaller factor based only on these same cost summaries fails along this family. This does not preclude horizon-dependent tighter bounds or establish selected-policy-bound sharpness.')
    h('A3-A4. Premium-optimal focus and a minimum certified budget')
    p('At a fixed cardinality k, choosing the k largest eligible premiums minimizes Q_tail and therefore kappa. No attention rule can uniformly improve this factor at that k under A1. A smaller factor alone need not give a smaller absolute upper bound kappa*g_F. For 0<epsilon<=1, every focus qualifies if C_b<=(1+epsilon)C_a; otherwise the factor requirement is exactly')
    eq('kappa_F <= 1+epsilon  iff\nQ_tail <= epsilon*C_a*C_b / (C_b-(1+epsilon)*C_a).')
    p('The shortest descending-premium prefix meeting that tail threshold has minimum cardinality among focuses certified by A1. This is an algebraic corollary, not a new polynomial solver: enumerating k focused assets requires 2^k subsets. If C_a=C_b, even empty focus is exact, so this pair does not require attention.')
    h('Retaining the strongest existing certificate')
    p('The final implementation uses validation-selected greedy proposals by default, also checks premium focus, and intersects their intervals with the existing FPTAS interval. An optional learned selector replaces the greedy proposal. Let l be the maximum lower endpoint and u the minimum upper endpoint; retain the compatible witness attaining l. Since each interval contains G, l<=G<=u. The FPTAS fallback ensures u<=(1+epsilon)l.')
    eq('L_a=max_b l(a,b); U_a=max_b u(a,b)\na_hat in argmin_a U_a\nW(a_hat) <= U(a_hat) <= U(a_star)\n         <= (1+epsilon)*L(a_star) <= (1+epsilon)*W(a_star).')
    p('Later-versus-earlier pairs retain the exact premium-prefix solver. If U(a_hat)<=min_(a!=a_hat)L_a, selection is an exact minimizer; a strict inequality certifies uniqueness. The composition logic is standard. Running the full fallback adds work, so this wrapper is not claimed to accelerate the pipeline.')
    page();h('4. Fixed attention experiment and statistical limits')
    p('The first plan was hashed before outcomes. Training uses 1,600 synthetic cohorts, validation 200, and held-out ID/shift tests 300 each. Every pair has eight censored eligible assets and two known failures between a and b. ID uses ages 16-48 and broadly varying premiums; shift uses ages 40-80, larger age gaps, horizon-correlated unknown premiums and larger known premiums. Gold subset membership is solved from public inputs, never hidden future lifetimes. Seeds and all records are saved.')
    p('Attention has one width-32 two-head Transformer block, no positional embedding and 8,993 parameters. The pointwise MLP has 9,065 parameters and the same 12 public features. Three model seeds use Adam .002, batches 64 and 25 epochs; validation BCE chooses a checkpoint. Exact focused search uses k=4 (16 subsets); full eight-asset search is the evaluation oracle (256 subsets).')
    p('Primary outcome is log(G_exact/g_F), lower better. Original results average three seed metrics within each cohort. Four planned attention-minus-baseline mean contrasts use two-sided Monte Carlo sign flips, 9,999 draws, Holm adjustment and 2,000 cohort-bootstrap draws. Independent units are 300 cohorts per split, not 900 seed results.')
    methods=read('method_summary.json'); table(['Original protocol','ID mean gap','Shift mean gap','ID kappa','Shift kappa'],
        [[method,*[f"{next(r for r in methods if r['method']==method and r['split']==split)['mean_log_gap']:.6f}" for split in ['id','shift']],
          *[f"{next(r for r in methods if r['method']==method and r['split']==split)['mean_certificate_factor']:.3f}" for split in ['id','shift']]]
         for method in ['attention','mlp','premium','singleton','premium_per_use','horizon','random']], [120,95,95,88,89])
    table(['Contrast','Mean difference','Nominal 95% bootstrap CI','Holm p'],
        [[r['split']+' vs '+r['baseline'],f"{r['mean_attention_minus_baseline']:.7f}",
          f"[{r['bootstrap_95_ci'][0]:.7f}, {r['bootstrap_95_ci'][1]:.7f}]",f"{r['holm_p']:.4f}"] for r in read('statistical_tests.json')],
        [93,98,231,65])
    p('All four mean contrasts reject under the test assumptions, but effect size and novelty differ. ID attention versus premium has 26 wins, 267 ties, 7 losses. Greedy, added after this plan, has means .004608 ID and .015272 shift, below attention in both. The primary table is preserved rather than retrospectively replacing its controls.',small)
    p('Sign flips require exchangeability/symmetry under the null. Bootstrap intervals condition on fitted models and are neither simultaneous nor training-uncertainty intervals. These tests measure a synthetic adversarial proposal, not realized maintenance improvement or historical originality.',small)
    page();h('5. Retrained ablations and fresh confirmation')
    p('After the first outcomes, a separately hashed follow-up plan fixed two retrained ablations: pooled set context (9,053 parameters), and attention with six broadcast pair-context features zeroed (8,993 parameters). Token horizon/age normalization and eligibility still encode the pair; the latter is not removal of all conditioning. Both use the same three seeds and schedule. The follow-up deployment protocol averages checkpoint logits before top-k, unlike averaging the original seed metrics.')
    ab=read('ablation-original-summary.json'); confirm=read('confirmation-summary.json')
    def val(source,method,split):return next(r for r in source if r['method']==method and r['split']==split)['mean_log_gap']
    table(['Selector','Original ID','Original shift','Fresh ID','Fresh shift'],
        [[method,*[f"{val(ab,method,'original_'+s):.6f}" for s in ['id','shift']],
          *[f"{val(confirm,method,'confirmation_'+s):.6f}" for s in ['id','shift']]]
         for method in ['attention','no_broadcast_attention','pooled','mlp','sequential_greedy','premium','singleton','premium_per_use','horizon','random']],
         [137,87,89,87,87])
    p('On 200 validation cohorts, greedy minimizes mean gap (.003026), followed by attention (.003065), no-broadcast attention (.003156), pooled (.003219) and MLP (.003269). The choice was saved before generating 300 fresh ID and 300 fresh shift cohorts with new seeds. All candidate results remain visible; the selected method is not changed after confirmation.')
    tests=[r for r in read('confirmation-tests.json') if not r['structural_self_comparison']]
    table(['Selected greedy vs premium','Mean difference','Nominal 95% CI','Holm p'],
        [[r['split'].replace('confirmation_',''),f"{r['mean_selected_minus_baseline']:.7f}",
          f"[{r['bootstrap_95_ci'][0]:.7f}, {r['bootstrap_95_ci'][1]:.7f}]",f"{r['holm_p']:.4f}"] for r in tests],[93,98,231,65])
    p('Fresh wins/ties/losses are 29/271/0 ID and 42/258/0 shift. Greedy-versus-itself gives structural ties and p=1 in the fixed four-test family; this is not independent superiority evidence. Fresh confirmation supports a small proposal benefit against premium for the chosen rule, not a new greedy algorithm. Broadcast context has only a small descriptive effect here. Attention helps compared with the pointwise ablation, but has not established necessity or superiority over greedy.')
    p('Original-set ablations are exploratory because earlier outcomes motivated them. Fresh cohorts supply a cleaner validation-selected confirmation for the stated synthetic laws, not for prospective equipment failure or a new physical domain.')
    page();h('6. Budget, certificate-removal and precision ablations')
    img=Image(str(OUT/'budget_ablations.png')); ratio=img.imageHeight/img.imageWidth;img.drawWidth=width;img.drawHeight=width*ratio;story.append(img)
    md.append('![Budget ablations](../out/clock_regret_attention/budget_ablations.png)\n')
    p('Figure 1. Original held-out cohorts; follow-up ensemble protocol. The upper panels use a symmetric-log axis with a linear region near zero. Focus grows along a fixed model ranking; greedy recomputes each marginal. Full focus is exact for every rule. Kappa is a deterministic worst-case factor, not a confidence interval.',small)
    table(['At k=4','Final subsets','Proposal subsets','ID optimum coverage','Shift coverage'],
        [['Premium',16,0,'72.67%','31.00%'],['Attention ensemble',16,'neural inference','75.33%','37.00%'],
         ['Sequential greedy',16,172,'76.33%','38.33%']],[111,75,99,120,82])
    p('At k=1,2 attention has higher mean gaps than premium on both distributions; its ranking was trained on optimum membership, not all budget objectives. At k=4 proposal gaps are small but certificate factors remain around 3 ID and 11 shift. Premium sorting minimizes kappa at fixed k by A3. At k=8 all gaps are zero, kappa=1, and the final search enumerates 256 subsets; greedy additionally performs 1,004 proposal subset evaluations. Counts exclude neural inference, sorting and the full fallback, so they are not runtime measurements.')
    h('Removing the omission certificate fails mathematically')
    eq('H=(1,3), delta=(0,1), q=(100,1), a=2, b=3, F=empty\ng_F=1, but compatible L=(2,3) gives G=255/206 > 1.\nkappa_F=153/103 retains the omitted uncertainty.')
    p('Treating unfocused assets as known survivors and declaring g_F exact is false. Conversely, no known failures between the pair gives C_a=C_b and empty focus exact: attention is unnecessary. The fallback intersection retains its previous tolerance for any focus. Functional complete-family checks do not demonstrate cost or time improvements.')
    page();h('7. Failure synthesis and assumptions that remain')
    table(['Earlier direction','Evidence and failure','Retained component'],[
        ['CAT / transfer','CAT-c improves failure-containing cells over 1-SE on 0/6 engine datasets; battery LOBO failures 25.2-34.15%.','Explicit information/feasibility contract; no transferred safety theorem.'],
        ['RAMPE','All 6,080 episodes equal fallback 1-SE; gates abstain everywhere. Verdict D.','Declared fallback; reject renamed reliability scores and unsupported RL.'],
        ['Observability / generic LP','All 29,184 cap evaluations reproduced; no novel optimizer; grouped sensitivity 0/21 Holm rejections.','Public/sealed separation, matched information; no fabricated sensor-prefix replay.'],
        ['Shared-clock / linear solver','Exact structure and witnesses; mixed performance, 13 favorable and 15 unfavorable corrected synthetic comparisons.','Same-world quotient and exact computational reductions.'],
        ['Heterogeneous fleet','304 constructed-cost replays: 5 wins, 291 ties, 8 losses; mean regret change +.004718477.','Complete-family FPTAS and actual-loss-stage certificate.'],
        ['Attention / follow-up','Small gains over MLP/premium; greedy wins validation and has lower average gaps. Focus factors remain loose.','Optional proposal plus independently valid omission certificate.']], [94,238,155])
    p('Detailed source paths, all retained negative findings and limits are in FAILURES_AND_LIMITATIONS.md. These are different experiments and metrics; they are not pooled into a single success score. The 1966 Fox access issue is closed by the supplied full-text audit; older reports retain their original chronology.')
    p('The final method assumes exact observed horizons/flags, fixed integer ages, positive rational premiums, common preventive cost and independent compatible completions. It does not model joint physical constraints, downtime, imperfect repair, adaptive sensors, intervention effects or limited maintenance resources. The trained cohort has eight eligible assets; large-fleet and variable-size generalization is untested. Cost scenarios are constructed, not measured consequences.')
    p('Running all proposed intervals plus the full fallback preserves precision and can tighten endpoints, but adds overhead. No end-to-end speedup, prospective cost benefit, population risk control, causal effect or accepted-paper status has been established. The finite-cohort guarantee concerns W, which can prefer a policy with worse mean realized cost. Statistical significance and exactness cannot establish historical originality.')
    page();h('8. Literature boundary, reproducibility and review claim')
    p('Transformers [1], pooled set learning [2], set attention [3] and attention-based combinatorial proposals [4] are established. Censored RUL Transformers [5] prevent a broad first-attention-maintenance claim. NeurPRISE [6] is especially close: it uses Transformer interactions for robust scenario selection, and its greedy PRISE comparator motivates our stronger challenger. Robust scenario reduction already has multiplicative guarantees [7,8]. Those general ideas are attributed, not claimed as new.')
    p('The precise candidate is the omitted-premium formula for this shared rate quotient, its sharpness family and minimum certified focus budget. The inspected primary statements do not show that formula, but the audit cannot exclude equivalent reformulations or earlier derivations. A specialized corollary may be insufficiently substantial for a stand-alone method paper. Verdict B: potentially novel but insufficiently established. No positive historical-priority verdict or 9/10 originality rating is supported.')
    p('The release includes two hashed plans, all 3,000 generated cohorts, twelve checkpoints/training histories, primary and follow-up outputs, exact math checks, unit tests, two verification scripts and a review archive. There are 1,600 training, 200 validation and 1,200 held-out synthetic cohorts. The 1,025 earlier protected files remain unchanged. Exact witness/interval checks cover the saved results; independent full-clock unit checks cover small cases. No real sealed lifetimes enter learned features or training labels.')
    p('For reproduction use the saved environment snapshot and README commands. Scores and certification are exact rational calculations; ranking uses floating point. Attention logits are not failure probabilities or causal explanations. No public preprint, DOI, external review or priority date has been generated for this project. The prepared claim needs independent specialist comparison and a measured engineering demonstration before an established original-method claim.')
    h('Primary references')
    refs=[
        '[1] Vaswani et al. (2017). Attention Is All You Need. arXiv:1706.03762.',
        '[2] Zaheer et al. (2017). Deep Sets. NeurIPS 30.',
        '[3] Lee et al. (2019). Set Transformer: A Framework for Attention-based Permutation-Invariant Neural Networks. PMLR 97, 3744-3753.',
        '[4] Kool, van Hoof and Welling (2019). Attention, Learn to Solve Routing Problems! ICLR. arXiv:1803.08475.',
        '[5] Noot, Martin and Birmele (2025). LSTM and Transformers based methods for Remaining Useful Life Prediction considering Censored Data. IJPHM 16(2). DOI:10.36001/IJPHM.2025.v16i2.4260.',
        '[6] Lin, Zhou, Bi, Wu, Song, Cao and Zhang (2026). Learning Scenario Reduction for Two-Stage Robust Optimization with Discrete Uncertainty. arXiv:2605.14494v1.',
        '[7] Goerigk and Khosravi (2023). Optimal scenario reduction for one- and two-stage robust optimization with discrete uncertainty in the objective. EJOR 310(2), 529-551. Author preprint arXiv:2209.00499.',
        '[8] Aigner, Denzler, Liers, Pokutta and Sharma (2025/2026). Scenario Reduction for Distributionally Robust Optimization. arXiv:2503.11484v3.'
    ]
    for ref in refs:p(ref,small)
    p('Primary links, inspection depth and historical-equivalence gaps are in LITERATURE.md. Earlier exact/FPTAS results are project predecessors documented in the protected stage manuscripts, not independently published prior art.',small)
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Times-Roman',8);canvas.setFillColor(colors.HexColor('#53616a'))
        canvas.drawString(54,27,'Ansari | Certified focus search | Working paper, 8 October 2026')
        canvas.drawRightString(A4[0]-54,27,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(OUT/'manuscript.pdf'),pagesize=A4,leftMargin=54,rightMargin=54,topMargin=45,bottomMargin=45,
        title=TITLE,author='Nafis Wadud Ansari',subject=SUBTITLE)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (Path('clock_regret_attention')/'MANUSCRIPT.md').write_text('# '+TITLE+'\n\n'+'\n'.join(md),encoding='utf-8')
    protect();print('Working paper written')


if __name__=='__main__':build()
