#!/bin/sh
# Builds the revised manuscript and supplementary material (LaTeX, Elsevier CAS double-column class) from numbers.json
# (paper3/numbers.json = numbers of the submitted version + key 'rev3' from audit_summarize.py). Every quantitative statement
# is computed from numbers.json and checked; the build stops if any check fails. Needs Node.js; PDFs need pdfLaTeX + latexmk.
set -e
cd "$(dirname "$0")"
# figures shared with the submitted version are taken from paper2/img
for f in Fig1_STW_architecture Fig3_example_engines Fig4_level_tradeoff Fig5_error_leadtime Fig6_comparison_ablation Fig_rep30; do
  [ -f img/$f.png ] || cp ../paper2/img/$f.png img/
done
cat _texhelpers.js _b3_front.js _b3_cost.js _b3_final.js _b3_intro.js _b3_design.js _b3_res1.js _b3_res2.js _b3_disc.js _b3_frontmatter.js _s3.js _refs3.js _textail.js > paper_tex.js
node paper_tex.js
cp cas-dc.cls cas-common.sty tex/ && rm -rf tex/img && cp -r img tex/img
if command -v latexmk >/dev/null 2>&1; then
  (cd tex && latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex >/dev/null && latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary.tex >/dev/null && latexmk -c >/dev/null)
  echo "PDFs: paper3/tex/manuscript.pdf, paper3/tex/supplementary.pdf"
else
  echo "latexmk not found: LaTeX sources written to paper3/tex/ (compile with pdfLaTeX)"
fi
