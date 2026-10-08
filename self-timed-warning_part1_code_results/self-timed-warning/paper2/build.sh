#!/bin/sh
# Builds the RESS manuscript and supplementary material (LaTeX, Elsevier CAS double-column class) from numbers.json.
# Every number in the text comes from numbers.json; the build runs the consistency checks and stops if any fails.
# Needs Node.js (no npm packages). Compiling the PDFs additionally needs pdfLaTeX with latexmk (TeX Live 2023 or later).
set -e
cd "$(dirname "$0")"
cat _texhelpers.js _body.js _ablation_text.js _rev_text.js _supp.js _refs_appx.js _textail.js > paper_tex.js
node paper_tex.js
cp cas-dc.cls cas-common.sty tex/ && rm -rf tex/img && cp -r img tex/img
if command -v latexmk >/dev/null 2>&1; then
  (cd tex && latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex >/dev/null && latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary.tex >/dev/null && latexmk -c >/dev/null)
  echo "PDFs: paper2/tex/manuscript.pdf, paper2/tex/supplementary.pdf"
else
  echo "latexmk not found: LaTeX sources written to paper2/tex/ (compile with pdfLaTeX)"
fi
