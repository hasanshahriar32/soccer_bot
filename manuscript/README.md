# HazBot IEEE paper project

**HazBot: Architecture and Coordination Verification of A Raspberry Pi-Based Mobile Manipulator for Hazardous-Object Retrieval**

Start with the [paper PDF](submission/HazBot_IEEE_Anonymous.pdf), [Overleaf ZIP](submission/HazBot_IEEE_Overleaf.zip), [LaTeX entry point](main.tex), and [figure gallery](figures/README.md).

The paper has been rebuilt around a Raspberry Pi and four subsystems: navigation/LiDAR, wheel control, native camera inference, and a robotic arm/gripper. It connects these components to a seven-phase retrieval mission, with hazardous-object retrieval as the application objective and ball-based simulated control as the nonhazardous surrogate context.

## Evidence and results

The reported results come from three reproducible offline studies:

| Study | Scope | Computed results |
|---|---|---|
| Wrist geometry | URDF chain, analytical and independently implemented transforms | 68,921 sampled poses; 0.200 m shoulder–wrist link bound; 2,747 below-ground samples; 1,013 FK comparison poses |
| Gateway semantics | Actual isolated wheel branch and pure arm mapper | 261,121 wheel pairs; 1,020 mixed-zero pairs emit no command; 2,255 arm mapping cases; 29 characterization checks pass |
| Reference coordination | Seven phases, 12 Boolean observations, independent command-admissibility oracle | 28,672 cases per policy; 0 full-policy violations; ablation counts 480/128/288; 109 checks pass |

These are source geometry, software behavior, and bounded reference-model results. They are not physical mission success, hazardous-material identification, detector accuracy, payload, or endurance measurements. See the [evaluation protocol](research/evaluation_protocol.md), [claim ledger](research/claim_evidence.csv), and [resource assessment](research/hazbot_evidence_assessment.md).

## Layout

```text
manuscript/
├── main.tex, references.bib       # Anonymous IEEEtran A4 paper
├── sections/                     # Abstract through conclusion
├── figures/                      # HazBot vector figures, previews, editable diagrams
├── experiments/                  # Source characterization and reference verifier
├── data/                         # CSV datasets, results, provenance, validation
├── generated/                    # Computed LaTeX summary and table
├── research/                     # Literature, evidence ledger, methods, roadmap
├── guideline/                    # Original supplied requirements, preserved
├── scripts/                      # Render, compile-check, package tools
├── compile.sh, Makefile
├── archive/                      # Previous ball-pursuit paper snapshot
└── submission/                   # Current PDF, Overleaf ZIP, validation, readiness
```

## Reproduce

From the repository root:

```bash
# Python standard library; no ROS, sockets, serial connections, or motor operation.
python3 manuscript/experiments/characterize_hazbot.py
python3 manuscript/experiments/verify_hazbot_mission.py

# Regenerate technical figures and both compact annotated photographs.
python3 -m pip install -r manuscript/requirements-figures.txt
python3 manuscript/scripts/build_figures.py

# Existing PDF figures and computed table are sufficient for LaTeX compilation.
bash manuscript/compile.sh
python3 manuscript/scripts/check_submission.py
python3 manuscript/scripts/package_sources.py
```

Tectonic or TeX Live with IEEEtran and BibTeX is required. Figure regeneration additionally uses librsvg's rsvg-convert and Noto Sans fonts; plotting dependencies are pinned in requirements-figures.txt. Poppler's pdfinfo, pdffonts, and pdftotext support the format checks. On this machine the verified Tectonic cache is /tmp/soccer-paper-tex-cache; this path is not required by the source package.

The ZIP contains main.tex, sections, bibliography, IEEE template files, computed HazBot prose, vector figures, the original supplied study diagrams and compact derivatives, and editable architecture/mission/arm draw.io diagrams. It does not include runtime configuration, credentials, private research notes, or source provenance. Choose main.tex and pdfLaTeX on Overleaf. Full experimental reproducibility uses this local repository.

## Figures

The active paper has nine numbered figures: the original hardware architecture and seven-phase mission; three compact single-column workflow, methodology and verification diagrams; arm geometry; two annotated prototype photographs; and the operator dashboard. The compact diagrams match the original paper's design: shared blue/teal/gold/red palette, Noto Sans typography, numbered badges, pale panels, thin borders and arrow styling. The renderer imports the palette directly from the architecture/mission renderer so the design remains consistent. DejaVu Sans is embedded only where mathematical symbols require it.

The author-supplied wide PDFs in figures/worflow-methodology-arch remain unchanged. The paper uses the _column.pdf derivatives with labels at least 6.5 pt. Both originals and compact derivatives are packaged. Regenerate the compact figures with `python3 manuscript/scripts/build_compact_study_figures.py`; the main figure builder also calls this renderer.

The workflow is discussed in System Architecture, the methodology opens the analysis method, and verification accompanies the bounded-model procedure and results. The mission strip retains its phase-specific transition view. Duplicate numerical tables are excluded from print, with their findings retained in figures and text. See [placement rationale](research/figure_integration.md), [layout validation](data/figure_integration_validation.json) and the [gallery](figures/README.md).

The supplied photographs are retained as photo/bot.png and photo/laptop_front.png; compact publication derivatives photo/bot.jpeg and photo/laptop_front.jpeg feed the paper, and the supplied dashboard is photo/dashboard_edited.png. The annotation script adds compact numbered vector markers with caption keys identifying hardware and interface panels. The paper includes hazbot_prototype.pdf, hazbot_front.pdf, and hazbot_dashboard.pdf through sections/03_prototype_photo.tex. No image generation or synthetic hardware is used. Refresh the annotations and recheck the six-page/3 MB limits when replacing the images.

The acknowledgment briefly credits ChatGPT (OpenAI) for assistance with manuscript preparation. The broader assistance history and the supplied guideline's non-intellectual-only restriction remain recorded in the local submission-readiness notes.

The source arm has three positioning axes and a separately actuated gripper. Direct camera acquisition/native inference, LiDAR controller communication, and separate drive/arm Arduino paths are shown explicitly. Differing proposal revisions and unsubstantiated slide performance figures are reconciled in the private resource assessment rather than combined as measured results.

## Current and historical files

HazBot_IEEE_Anonymous.pdf and HazBot_IEEE_Overleaf.zip are the canonical outputs. The compile/package scripts also refresh the old SoccerBot filenames as compatibility copies for existing local links; they contain the same current paper, not a second manuscript.

The [previous case study ZIP](archive/SoccerBot_Previous_Case_Study_2026-10-21.zip) preserves the earlier ball-pursuit manuscript and its original diagrams. Unprefixed figures, replay data, replay_supervisor.py, and repository_audit.md remain historical supporting material. They are excluded from the active source ZIP and are not the results of the HazBot reference mission. The legacy replay can still be checked with python3 manuscript/experiments/replay_supervisor.py --check-only.

The paper remains anonymous under the supplied guideline. [Submission readiness](submission/READINESS.md) distinguishes completed mechanical checks from author review and venue-policy decisions. No submission or publication action has been taken.
