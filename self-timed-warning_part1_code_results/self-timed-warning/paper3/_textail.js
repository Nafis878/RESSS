
// ================================================================ LaTeX writer (RESS, Elsevier CAS double column)
const path = require('path');
const OUT = __dirname + '/tex';
fs.mkdirSync(OUT, { recursive: true });

// ---------------- references: keys, citation conversion
const keyOf = (a, y) => (a.replace(/[^A-Za-z]/g, '') + y).toLowerCase();
const REFKEY = {}; REFS.forEach(([a, y]) => { REFKEY[`${a}|${y}`] = keyOf(a, y); });
const NAMES = [...new Set(REFS.map(r => r[0]))].sort((a, b) => b.length - a.length).map(n => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
const ITEM = new RegExp(`^(?:e\\.g\\.,?\\s+|see\\s+)?(${NAMES})(?:\\s+et al\\.|\\s+(?:&|and)\\s+[A-Z][A-Za-z'’-]+)?,\\s+(\\d{4})$`);
const NARR = new RegExp(`\\b(${NAMES})((?:\\s+et al\\.)|(?:\\s+(?:and|&)\\s+[A-Z][A-Za-z'’-]+))?\\s+\\((\\d{4})\\)`, 'g');
const citedOrder = []; const citedSet = new Set();
const useKey = (a, y) => { const k = REFKEY[`${a}|${y}`]; if (!k) throw new Error(`unknown citation ${a} ${y}`); if (!citedSet.has(k)) { citedSet.add(k); citedOrder.push(k); } return k; };
const CITE_S = '\u0001', CITE_E = '\u0002';
function citations(t) {
  t = t.replace(/\(([^()]*)\)/g, (whole, inner) => {
    const items = inner.split(/;\s+/); const hits = items.map(it => it.trim().match(ITEM));
    if (!hits.some(Boolean)) return whole;
    const parts = []; let run = [];
    items.forEach((it, i) => { if (hits[i]) run.push(useKey(hits[i][1], hits[i][2])); else { if (run.length) parts.push(CITE_S + run.join(',') + CITE_E), run = []; parts.push(it); } });
    if (run.length) parts.push(CITE_S + run.join(',') + CITE_E);
    return hits.every(Boolean) ? parts.join('') : '(' + parts.join('; ') + ')';
  });
  return t.replace(NARR, (m, a, mid, y) => `${a}${mid || ''} ${CITE_S}${useKey(a, y)}${CITE_E}`);
}

// ---------------- text rendering: *italic* **bold** _{sub} ^{sup}, escaping, symbols
const UNI = { '−': '\\textminus{}', '–': '--', '—': '---', '…': '\\ldots{}', '≤': '$\\le$', '≥': '$\\ge$', '×': '$\\times$', '±': '$\\pm$',
  '→': '$\\rightarrow$', '∈': '$\\in$', '≈': '$\\approx$', 'ε': '$\\varepsilon$', 'ρ': '$\\rho$', 'ℓ': '$\\ell$', 'κ': '$\\kappa$', 'θ': '$\\theta$',
  'τ': '$\\tau$', 'σ': '$\\sigma$', 'μ': '$\\mu$', 'α': '$\\alpha$', 'λ': '$\\lambda$', 'ŷ': '$\\hat{y}$', 'ỹ': '$\\tilde{y}$', '‘': '`', '’': "'",
  '“': '``', '”': "''", '²': '\\textsuperscript{2}', '°': '\\textdegree{}', '≠': '$\\neq$', '∞': '$\\infty$', 'ξ': '$\\xi$', 'β': '$\\beta$', 'γ': '$\\gamma$', 'δ': '$\\delta$', 'η': '$\\eta$', 'φ': '$\\phi$', 'ψ': '$\\psi$', 'ω': '$\\omega$', 'π': '$\\pi$', 'ν': '$\\nu$', 'ζ': '$\\zeta$', 'χ': '$\\chi$', 'Ω': '$\\Omega$', '≪': '$\\ll$', '≫': '$\\gg$', '∑': '$\\sum$', '∼': '$\\sim$', '⁻': '\\textsuperscript{\\textminus}', '¹': '\\textsuperscript{1}', '³': '\\textsuperscript{3}', '½': '\\textonehalf{}', '•': '\\textbullet{}', '∎': '\\hfill$\\blacksquare$', '′': "'", 'Σ': '$\\Sigma$', 'Δ': '$\\Delta$',
  '√': '$\\surd$', '·': '$\\cdot$', '\u00a0': '~', '\u2009': '\\,', '\u202f': '\\,', 'ä': '\\"a', 'ö': '\\"o', 'ü': '\\"u', 'é': "\\'e", 'è': '\\`e', 'á': "\\'a", 'ó': "\\'o", 'í': "\\'\\i{}", 'ñ': '\\~n', 'ç': '\\c{c}', 'ë': '\\"e' };
const URLS = [];
function esc(s) {
  s = s.replace(/https?:\/\/\S+/g, u0 => { let u = u0, tailp = ''; const bal = x => (x.match(/\(/g) || []).length - (x.match(/\)/g) || []).length;
    while (/[.,;]$/.test(u) || (u.endsWith(')') && bal(u) < 0)) { tailp = u.slice(-1) + tailp; u = u.slice(0, -1); }
    URLS.push(u); return `\u0003${URLS.length - 1}\u0004` + tailp; });
  s = s.replace(/\\/g, '\\textbackslash{}').replace(/([&%$#_{}])/g, '\\$1').replace(/~/g, '\\textasciitilde{}').replace(/\^/g, '\\textasciicircum{}');
  s = s.replace(/"([^"]*)"/g, "``$1''");
  s = [...s].map(c => UNI[c] !== undefined ? UNI[c] : c).join('');
  const bad = [...s].filter(c => c.charCodeAt(0) > 126 && !'\u0001\u0002\u0003\u0004'.includes(c));
  if (bad.length) throw new Error('unmapped characters: ' + [...new Set(bad)].join(' ') + ' in: ' + s.slice(0, 120));
  return s;
}
function finish(s) {
  return s.replace(/\u0001([^\u0002]*)\u0002/g, (m, k) => `\\cite{${k}}`).replace(/\u0003(\d+)\u0004/g, (m, i) => `\\url{${URLS[+i]}}`);
}
function tx(t, cite = true) {
  if (cite) t = citations(String(t)); else t = String(t);
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|_\{[^}]+\}|\^\{[^}]+\})/g; let out = '', last = 0, m;
  while ((m = re.exec(t))) {
    out += esc(t.slice(last, m.index)); const k = m[0];
    if (k.startsWith('**')) out += `\\textbf{${esc(k.slice(2, -2))}}`;
    else if (k.startsWith('*')) out += `\\textit{${esc(k.slice(1, -1))}}`;
    else if (k.startsWith('_{')) out += `\\textsubscript{${esc(k.slice(2, -1))}}`;
    else out += `\\textsuperscript{${esc(k.slice(2, -1))}}`;
    last = m.index + k.length;
  }
  return finish(out + esc(t.slice(last)));
}
const plain = t => String(t).replace(/\*\*|\*|_\{|\^\{|\}/g, ' ');
let WORDS = 0; const count = t => { WORDS += (plain(t).match(/\S+/g) || []).length; };

// ---------------- equations (the seven displayed equations, typeset as mathematics)
const EQMAP = {
  '*t*^{*} = min { *t* < *L*_{i} : the policy warns at *t* },': 't^{*} = \\min\\{\\, t < L_i : \\text{the policy warns at } t \\,\\},',
  '*z*_{t,j} = ( *x*_{t,j} − μ_{j}(*a*_{t}) ) / σ_{j}(*a*_{t}).': 'z_{t,j} = \\bigl( x_{t,j} - \\mu_j(a_t) \\bigr) / \\sigma_j(a_t).',
  '*y*_{t} = min( *r*_{t}, *c* ),   *c* ∈ {40, 60, 90}.': 'y_t = \\min( r_t, c ), \\qquad c \\in \\{40, 60, 90\\}.',
  'ỹ_{t} = EWM_{m}(ŷ)_{t} + *s*,': '\\tilde{y}_t = \\mathrm{EWM}_m(\\hat{y})_t + s,',
  '*t*^{*} = min { *t* : ỹ_{τ} ≤ *H* for all τ = *t* − *k* + 1, …, *t* },': 't^{*} = \\min\\{\\, t : \\tilde{y}_{\\tau} \\le H \\ \\text{for all}\\ \\tau = t-k+1, \\ldots, t \\,\\},',
  '*P*(*s*) = *F*(*b* − *s*) − *F*(*a* − *s*).': 'P(s) = F(b - s) - F(a - s).',
  '*s*^{*} = (*a* + *b*)/2 − *m* = −5.5 − *m*,': 's^{*} = (a + b)/2 - m = -5.5 - m,',
  'ŷ_{t*} − 2 ≤ *r*_{t*} ≤ ŷ_{t*} + 13.': '\\hat{y}_{t^*} - 2 \\le r_{t^*} \\le \\hat{y}_{t^*} + 13.' };

// ---------------- items -> LaTeX
let sec = 0, sub = 0, inAppendix = false;
function colspec(widths) { const tot = widths.reduce((a, b) => a + b, 0); return widths.map(w => `>{\\raggedright\\arraybackslash}p{\\dimexpr${(w / tot).toFixed(4)}\\linewidth-2\\tabcolsep\\relax}`).join(''); }
function render(items, mode) {
  const out = [];
  items.forEach(it => {
    if (!it || it.k === 'skip') return;
    if (it.k === 'p') { count(it.t); out.push((it.noIndent ? '\\noindent ' : '') + tx(it.t) + '\n'); return; }
    if (it.k === 'h1') {
      count(it.t); const m = it.t.match(/^(\d+)\.\s+(.*)$/);
      if (mode === 'supp') { out.push(`\\section*{${tx(it.t)}}\n`); return; }
      if (m) { sec += 1; sub = 0; must(+m[1] === sec, `section number ${m[1]} matches LaTeX counter ${sec}`); out.push(`\\section{${tx(m[2])}}\\label{sec:${sec}}\n`); return; }
      const am = it.t.match(/^Appendix ([A-Z])\.\s+(.*)$/);
      if (am) { if (!inAppendix) { out.push('\\appendix\n'); inAppendix = true; } out.push(`\\section*{Appendix ${am[1]}. ${tx(am[2])}}\n`); return; }
      out.push(`\\section*{${tx(it.t)}}\n`); return;
    }
    if (it.k === 'h2') {
      count(it.t); const m = it.t.match(/^(\d+)\.(\d+)\.\s+(.*)$/);
      if (m) { sub += 1; must(+m[1] === sec && +m[2] === sub, `subsection ${m[1]}.${m[2]} matches LaTeX counter ${sec}.${sub}`); out.push(`\\subsection{${tx(m[3])}}\n`); }
      else out.push(`\\subsection*{${tx(it.t)}}\n`);
      return;
    }
    if (it.k === 'eq') { must(EQMAP[it.t] !== undefined, `equation mapped: ${it.t}`); out.push(`\\begin{equation}\n${EQMAP[it.t]}\n\\end{equation}\n`); return; }
    if (it.k === 'li') {
      it.items.forEach(count);
      const bullets = it.items.every(t => t.startsWith('•'));
      out.push('\\begin{itemize}[leftmargin=1.2em,itemsep=2pt]\n' + it.items.map(t => {
        if (bullets) return `\\item ${tx(t.replace(/^•\s*/, ''))}`;
        const m = t.match(/^(\([ivx]+\))\s+(.*)$/s); return m ? `\\item[${m[1]}] ${tx(m[2])}` : `\\item ${tx(t)}`;
      }).join('\n') + '\n\\end{itemize}\n'); return;
    }
    if (it.k === 'table') {
      [it.caption, it.note || '', ...it.headers, ...it.rows.flat()].forEach(c => count(String(c)));
      const env = mode === 'supp' ? null : 'table*';
      const hdr = it.headers.map(h => tx(h)).join(' & ') + ' \\\\';
      const rows = it.rows.map(r => r.map(c => tx(c)).join(' & ') + ' \\\\').join('\n');
      const note = it.note ? `\\par\\vspace{3pt}{\\raggedright\\scriptsize ${tx(it.note)}\\par}` : '';
      if (mode === 'supp') {
        out.push(`{\\footnotesize\\setlength{\\tabcolsep}{4pt}\n\\begin{longtable}{@{}${colspec(it.widths)}@{}}\n\\caption{${tx(it.caption)}}\\\\\n\\toprule\n${hdr}\n\\midrule\\endfirsthead\n\\toprule\n${hdr}\n\\midrule\\endhead\n\\bottomrule\\endfoot\n${rows}\n\\end{longtable}}\n${it.note ? `{\\scriptsize ${tx(it.note)}\\par}\\medskip\n` : ''}`);
        return;
      }
      const lab = it.label ? `\\renewcommand{\\thetable}{${it.label}}` : '';
      out.push(`\\begin{${env}}[!tbp]\n${lab}\\footnotesize\\setlength{\\tabcolsep}{4pt}\n\\caption{${tx(it.caption)}}\n\\begin{tabular}{@{}${colspec(it.widths)}@{}}\n\\toprule\n${hdr}\n\\midrule\n${rows}\n\\bottomrule\n\\end{tabular}${note}\n\\end{${env}}\n${it.label ? '\\addtocounter{table}{-1}\n' : ''}`);
      return;
    }
    if (it.k === 'fig') {
      count(it.caption); const f = 'img/' + path.basename(it.path);
      if (mode === 'supp') { out.push(`\\begin{figure}[!htbp]\\centering\n\\includegraphics[width=${Math.min(1, it.widthIn / 6.5).toFixed(2)}\\linewidth]{${f}}\n\\caption{${tx(it.caption)}}\n\\end{figure}\n`); return; }
      const wide = it.widthIn > 4.5;
      out.push(`\\begin{${wide ? 'figure*' : 'figure'}}[!tbp]\\centering\n\\includegraphics[width=${wide ? '\\textwidth' : '\\linewidth'}]{${f}}\n\\caption{${tx(it.caption)}}\n\\end{${wide ? 'figure*' : 'figure'}}\n`);
      return;
    }
    throw new Error('unknown item ' + JSON.stringify(it).slice(0, 100));
  });
  return out.join('\n');
}

// ---------------- reference list in the numbered style of the journal
function vancouver(apa) {
  const m = apa.match(/^(.*?)\s\((\d{4})\)\.\s(.*)$/); if (!m) throw new Error('ref parse ' + apa);
  const [, auth, year, rest] = m;
  const toks = auth.replace(/,?\s&\s/g, ', ').split(/,\s/); const names = [];
  for (let i = 0; i < toks.length; i += 2) names.push(`${toks[i]} ${(toks[i + 1] || '').replace(/[.\s]/g, '')}`);
  const A = names.join(', ');
  let j = rest.match(/^(.*?[.?])\s\*([^*]+)\*,\s\*([^*]+)\*(?:\(([^)]+)\))?(?:,\s(?:Article\s)?([^.]+?))?\.(?:\s(https?:\S+))?$/);
  if (j) { const [, ti, jo, vol, iss, pg, url] = j; return `${A}. ${ti} ${jo} ${year};${vol}${iss ? `(${iss})` : ''}${pg ? `:${pg}` : ''}.${url ? ' ' + url : ''}`; }
  let c = rest.match(/^(.*?[.?])\sIn\s\*([^*]+)\*\s\(pp\.\s([^)]+)\)\.\s([^.]+)\.(?:\s(https?:\S+))?$/);
  if (c) { const [, ti, bk, pp, pub, url] = c; return `${A}. ${ti} In: ${bk}. ${pub}; ${year}, p. ${pp}.${url ? ' ' + url : ''}`; }
  throw new Error('ref format not recognised: ' + apa);
}

// ---------------- assemble the manuscript
const bodyTex = render(B, 'main');
REFS.forEach(([a, y]) => must(citedSet.has(keyOf(a, y)), `reference cited in the main text: ${a} ${y}`));
const leftover = [...bodyTex.matchAll(/[A-Z][a-z]+(?: et al\.)?,? \(?(?:19|20)\d\d\)?/g)].map(m => m[0]).filter(s => !/^(?:Table|Fig|Section|Supplementary|Appendix)/.test(s));
const byKey = Object.fromEntries(REFS.map(r => [keyOf(r[0], r[1]), r[2]]));
const bib = citedOrder.map(k => { const v = vancouver(byKey[k]); count(v); return `\\bibitem{${k}} ${tx(v, false)}`; }).join('\n');
let absWords = (plain(ABSTRACT).match(/\S+/g) || []).length; WORDS += absWords;
must(absWords <= 200, `abstract ${absWords} words <= 200 (RESS limit)`);
const kws = KEYWORDS.split(/;\s*/); must(kws.length >= 1 && kws.length <= 7, `${kws.length} keywords within the RESS limit of 1-7`);
HIGHLIGHTS.forEach(h => must(h.length <= 85, `highlight <= 85 characters (${h.length})`));
must(HIGHLIGHTS.length >= 3 && HIGHLIGHTS.length <= 5, '3-5 highlights');

const preamble = String.raw`\documentclass[a4paper,fleqn,doubleblind]{cas-dc}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{charter}
\renewcommand{\sfdefault}{bch}
\usepackage{textcomp}
\usepackage{amsmath,amssymb}
\usepackage[numbers,sort&compress]{natbib}
\usepackage{graphicx,booktabs,array,enumitem}
\usepackage{xurl}
\urlstyle{same}
\usepackage[switch]{lineno}
\usepackage[expansion=false]{microtype}
\def\tsc#1{\csdef{#1}{\textsc{\lowercase{#1}}\xspace}}
\renewcommand{\linenumberfont}{\normalfont\tiny\color{gray}}
\setlength{\bibsep}{1pt}
\renewcommand{\figurename}{Fig.}
`;
const front = String.raw`\begin{document}
\let\WriteBookmarks\relax
\let\printorcid\relax
\def\floatpagepagefraction{1}
\def\textpagefraction{.001}
\shorttitle{Self-timed end-of-life alarms: timing, cost and limits}
\shortauthors{Anonymized manuscript}
\title [mode = title]{${tx(TITLE, false)}}
\begin{abstract}
${tx(ABSTRACT, false)}
\end{abstract}
\begin{keywords}
${kws.map(k => tx(k, false)).join(' \\sep\n')}
\end{keywords}
\maketitle
\linenumbers
`;
const tail = String.raw`
\begin{thebibliography}{${citedOrder.length}}
${bib}
\end{thebibliography}
\end{document}
`;
fs.writeFileSync(OUT + '/manuscript.tex', preamble + front + bodyTex + tail);

// ---------------- supplementary material (single column)
const MAINWORDS = WORDS; sec = 0; sub = 0;
const suppTex = render(S, 'supp');
fs.writeFileSync(OUT + '/supplementary.tex', String.raw`\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{charter}
\usepackage{textcomp,amsmath,amssymb,graphicx,booktabs,array,longtable,enumitem,xurl}
\usepackage[expansion=false]{microtype}
\urlstyle{same}
\usepackage[margin=2.4cm]{geometry}
\usepackage[labelfont=bf,labelsep=period,font=small,justification=raggedright,singlelinecheck=false]{caption}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\begin{document}
\begin{center}{\Large\bfseries Supplementary material}\\[6pt]{\large ${tx(TITLE, false)}}\\[6pt]{\small Anonymized for review. Reference numbers in brackets refer to the reference list of the main article.}\end{center}
` + suppTex.replace(/\\cite\{([^}]+)\}/g, (m, ks) => '[' + ks.split(',').map(k => { const i = citedOrder.indexOf(k); if (i < 0) throw new Error('supplement cites a reference not in the main list: ' + k); return i + 1; }).join(', ') + ']') + '\n\\end{document}\n');

fs.writeFileSync(OUT + '/build_checks.txt', CHECK.join('\n') + `\n\nWords (abstract, text, tables, captions, appendices, references): ${MAINWORDS}\nAbstract: ${absWords} words; keywords: ${kws.length}; highlights: ${HIGHLIGHTS.map(h => h.length).join(', ')} characters\nUnconverted author-year patterns: ${leftover.length ? leftover.join(' | ') : 'none'}\n`);
console.log(`${CHECK.length} checks passed; words ${MAINWORDS}; abstract ${absWords}; references ${citedOrder.length}; leftover citations: ${leftover.length ? leftover.join(' | ') : 'none'}`);
