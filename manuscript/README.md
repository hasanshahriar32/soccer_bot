# IEEE paper project

**Freshness and Interface Contracts for Distributed ROS 2 Ball Pursuit: An Executable Case Study**

The paper is grounded in this repository, uses IEEE conference two-column A4
format, and defaults to anonymous review. The GOAD example informed the modular
project layout; none of its ADCS research, authorship, results, or prose is reused.
The requirements in `guideline/guide.md` take precedence over the example's
single-column manuscript style.

Start with [the PDF](submission/SoccerBot_IEEE_Anonymous.pdf),
[main.tex](main.tex), and [submission readiness](submission/READINESS.md).
The [figure gallery](figures/README.md) includes technical component diagrams,
replay analysis plots, vector exports and editable draw.io files.
This is a complete research draft with reproducible **constructed offline**
evidence. It is not an assertion of conference eligibility or a field-validated
soccer system.

## Structure

```text
manuscript/
├── main.tex                    # IEEEtran, A4, anonymous author block
├── references.bib              # Primary literature and official software docs
├── sections/                   # Abstract through conclusion
├── figures/                    # PDF/SVG/PNG diagrams, plots and draw.io sources
├── generated/                  # Tables regenerated from the replay
├── data/                       # Per-tick CSV, summaries, JSON, source hashes
├── experiments/                # Standard-library source-execution harness
├── research/                   # Source audit, claim ledger, related work, plan
├── guideline/                  # Original supplied instructions, preserved
├── scripts/                    # Figure, PDF-check, and source-package tools
├── compile.sh                  # Tectonic / latexmk / pdfLaTeX + BibTeX
├── Makefile
├── build/                      # Local compiler intermediates, ignored
└── submission/                 # PDF, Overleaf ZIP, format report, readiness
```

## What is actually claimed

The original source contains metric/pixel ball-coordinate inconsistencies and
an alternative metric pursuit controller with no scan timeout. The study
executes that controller's actual methods with in-memory substitutes, then
compares receipt-age and payload-validity gates on 12 deterministic scenarios.
The full proposed gate runs only in the research harness. Robot runtime files
and launchers were not changed, and no hardware scripts were operated.

The experiment measures requested commands, not perception accuracy, networking
latency, actual velocity, collision avoidance, scoring, SLAM accuracy, or power.
Existing Nav2 and `twist_mux` mechanisms are acknowledged as close prior art;
the contribution is a bounded executable integration study, not a new general
control architecture. See `research/novelty_and_validation_plan.md` for stronger
follow-up research and the evidence it would need.

## Reproduce

Run from the repository root:

```bash
# Standard library only; does not import ROS, connect sockets, or move motors.
python3 manuscript/experiments/replay_supervisor.py
python3 manuscript/experiments/replay_supervisor.py --check-only

# Optional: regenerate figures; needs the pinned Python and system dependencies.
python3 -m pip install -r manuscript/requirements-figures.txt
python3 manuscript/scripts/build_figures.py

# Compile existing figures/tables; requires Tectonic or TeX Live + IEEEtran.
bash manuscript/compile.sh

# Poppler tools pdfinfo, pdffonts, pdftotext are needed for format checks.
python3 manuscript/scripts/check_submission.py
python3 manuscript/scripts/package_sources.py
```

Tectonic downloads missing TeX resources on its first build. In a restricted
environment, point `XDG_CACHE_HOME` to a writable cache directory and seed it
with an existing Tectonic cache if available. The local verified build used
`/tmp/soccer-paper-tex-cache`. That host-specific path is not needed on Overleaf.
Tables and pre-rendered PDF figures are included, so compiling the paper does
not require Python, ROS, or robot hardware. The Overleaf ZIP contains only
the manuscript and figure assets, including optional vector illustrations and
editable SVG/draw.io sources; choose `main.tex` and pdfLaTeX.

## Technical figures

The paper uses an illustrated component topology, paired command traces for
scan silence versus fresh invalid payloads, and the saved timeout sweep.
The contract illustration and complete 12-scenario matrix remain optional
figures outside the paper. All five sets have PDF/SVG/PNG exports; both diagrams
also have editable draw.io files. See the [gallery and source map](figures/README.md).

The architecture uses original Python-authored SVG robotics symbols and
librsvg's `rsvg-convert`, with Noto Sans. Statistical figures use the versions in
[requirements-figures.txt](requirements-figures.txt). The renderer reads frozen
replay outputs and never imports ROS or operates the robot. Source inputs,
runtime evidence, generator modules and exports are hash-bound in
[figure_manifest.json](data/figure_manifest.json); selected exact plotted values
are retained in [figure_data.json](data/figure_data.json). Draw.io structure is
checked programmatically; editor font placement has not been visually verified.

## Editing and responsible submission

Keep the author block anonymous for the initial double-blind submission.
Replace it with verified author information only when the venue requests it;
do not copy authors from the GOAD example. Keep evidence provenance in the
local research folder, outside an anonymous source upload. Rerun the format
checks after every paper change, especially changes affecting page count.

The supplied guideline states that LLM use must be solely non-intellectual.
This task included AI-assisted research design, literature synthesis, coding,
and drafting, so the draft discloses that use accurately. It cannot truthfully
certify the guideline's narrower condition or human approval. See
`submission/READINESS.md`; this question must be resolved before submission.
No plagiarism/similarity percentage, author approval, original-contribution
certification, or IEEE PDF eXpress approval is claimed.
