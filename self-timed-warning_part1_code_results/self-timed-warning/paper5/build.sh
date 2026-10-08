#!/bin/sh
# Builds the third revision of the manuscript and its supplementary material (LaTeX, Elsevier CAS double-column class) from
# numbers.json (paper5/numbers.json = paper4/numbers.json + key 'rev5' from kam/make_rev5_numbers.py). Every quantitative
# statement is computed from numbers.json and checked; the build stops if any check fails. Needs Node.js; PDFs need
# pdfLaTeX + latexmk. Figures of this revision: python fig_rev5.py (out/paper5_figs/ -> paper5/img/).
set -e
cd "$(dirname "$0")"
for f in Fig1_STW_architecture Fig3_example_engines Fig4_level_tradeoff Fig5_error_leadtime Fig6_comparison_ablation Fig_rep30; do
  [ -f img/$f.png ] || cp ../paper2/img/$f.png img/
done
for f in Fig8_shift_A1 FigR3_cost_audit; do [ -f img/$f.png ] || cp ../paper3/img/$f.png img/; done
for f in Fig2_matched Fig8_battery_physical Fig9_battery_cost; do [ -f img/$f.png ] || cp ../paper4/img/$f.png img/; done
for f in FigR3_cost_audit5 Fig9_battery_cost5 Fig10_metric_M; do
  [ -f ../out/paper5_figs/$f.png ] && cp ../out/paper5_figs/$f.png img/
done
cat _texhelpers.js _b5_front.js _b5_cost.js _b5_final.js _b5_intro.js _b5_design.js _b5_res1.js _b5_res2.js _b5_kam.js _b5_disc.js _b5_frontmatter.js _s5.js _refs3.js _textail.js > paper_tex.js
node paper_tex.js
cp cas-dc.cls cas-common.sty tex/ && rm -rf tex/img && cp -r img tex/img
if command -v latexmk >/dev/null 2>&1; then
  (cd tex && latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex >/dev/null && latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary.tex >/dev/null && latexmk -c >/dev/null)
  echo "PDFs: paper5/tex/manuscript.pdf, paper5/tex/supplementary.pdf"
else
  echo "latexmk not found: LaTeX sources written to paper5/tex/ (compile with pdfLaTeX)"
fi
