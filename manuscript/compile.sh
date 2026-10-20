#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mkdir -p build submission
if command -v tectonic >/dev/null 2>&1; then
    tectonic --keep-logs --keep-intermediates --outdir build main.tex
elif command -v latexmk >/dev/null 2>&1; then
    latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
elif command -v pdflatex >/dev/null 2>&1 && command -v bibtex >/dev/null 2>&1; then
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
    bibtex build/main
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
else
    printf '%s\n' 'Install Tectonic or TeX Live (IEEEtran + BibTeX), or upload the source ZIP to Overleaf.' >&2
    exit 1
fi
cp build/main.pdf submission/HazBot_IEEE_Anonymous.pdf
# Retain existing local links to the paper; the previous draft is archived.
cp build/main.pdf submission/SoccerBot_IEEE_Anonymous.pdf
printf '%s\n' 'Built submission/HazBot_IEEE_Anonymous.pdf (SoccerBot filename is a compatibility copy)'
