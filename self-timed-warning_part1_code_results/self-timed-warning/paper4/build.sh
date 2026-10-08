#!/bin/sh
# Builds the second revision of the manuscript and its supplementary material (LaTeX, Elsevier CAS double-column class) from
# numbers.json (paper4/numbers.json = paper3/numbers.json + key 'rev4' from audit_summarize2.py). Every quantitative statement
# is computed from numbers.json and checked; the build stops if any check fails. Needs Node.js; PDFs need pdfLaTeX + latexmk.
set -e
cd "$(dirname "$0")"
# figures shared with earlier versions are taken from paper2/img and paper3/img
for f in Fig1_STW_architecture Fig3_example_engines Fig4_level_tradeoff Fig5_error_leadtime Fig6_comparison_ablation Fig_rep30; do
  [ -f img/$f.png ] || cp ../paper2/img/$f.png img/
done
for f in Fig8_shift_A1 FigR3_cost_audit; do [ -f img/$f.png ] || cp ../paper3/img/$f.png img/; done
cat _texhelpers.js _b4_front.js _b4_cost.js _b4_final.js _b4_intro.js _b4_design.js _b4_res1.js _b4_res2.js _b4_disc.js _b4_frontmatter.js _s4.js _refs3.js _textail.js > paper_tex.js
node paper_tex.js
cp cas-dc.cls cas-common.sty tex/ && rm -rf tex/img && cp -r img tex/img
if command -v latexmk >/dev/null 2>&1; then
  (cd tex && latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex >/dev/null && latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary.tex >/dev/null && latexmk -c >/dev/null)
  echo "PDFs: paper4/tex/manuscript.pdf, paper4/tex/supplementary.pdf"
else
  echo "latexmk not found: LaTeX sources written to paper4/tex/ (compile with pdfLaTeX)"
fi
