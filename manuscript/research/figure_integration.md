# Figure integration, 25 October 2026

The author requests that the original architecture and seven-phase mission be retained and the three study diagrams use compact single-column layouts with a consistent visual design, while the full manuscript stays within six A4 pages.

| Figure | First discussion | Role |
| --- | --- | --- |
| Original hardware architecture | Introduction and III-A | Physical Pi/controller/camera/LiDAR interfaces. Retained unchanged as a full-width figure. |
| Original seven-phase mission | IV-A | Phase-specific handoff conditions and transition commands. Retained unchanged as a full-width figure. |
| Retrieval workflow | III-A, System Architecture | Observation records and task authority feed the reference coordinator and dedicated actuator controllers. |
| Study methodology | Opening of IV | Links four source artifacts to the three offline analyses and integration requirements. |
| Bounded verification | IV-B and V-A | Enumeration, independent oracle, ablation outcomes, shortest counterexamples and full-policy reachability. |
| Arm geometry | IV-C and V-B | Relates modeled wrist geometry to docking requirements. |

All prototype photographs and the dashboard remain in the paper. The mission strip retains the phase-specific handoff view, while the new workflow follows observations through software to actuation. The ablation and characterization tables repeat information in the new figures and results prose; those tables are omitted from print, with their numerical findings retained. Introductory and explanatory passages are shortened to accommodate the graphics; mathematical definitions, joint bounds, study domain, limitations, bibliography and all reported findings are preserved.

## Evidence audit

The supplied methodology and verification diagrams were compared with data/hazbot_characterization.json and data/hazbot_mission_results.json and the two executable studies. They describe offline source/model evidence, not physical task trials. The compact renderer checks the study counts and records current source, style and output hashes in data/compact_study_figures.json.

The workflow's old “Feedback (B)” label mixed base rest with grip and release. The manuscript caption states that these are separate planned observations. The manuscript states the arm/base guards and authorization contracts. The two serial paths remain separate. No claim of deployed end-to-end autonomy is added.

The compact _column.pdf diagrams retain the readable compact organization and match the architecture/mission design. The renderer imports the existing palette directly from scripts/render_hazbot_figures.py, uses Noto Sans, and applies the same numbered badges, pale blue/teal/gold/red panels, slim borders and directional arrows. The verification figure retains small red bars alongside the counts. DejaVu Sans supplies only unsupported mathematical glyphs; all fonts are embedded. Labels remain at least 6.5 pt at the nominal 3.45-inch column width.

The supplied wide PDFs remain unchanged and are included in the source package as references. Figure data and visual style provenance are recorded in data/compact_study_figures.json. The current layout and font checks are in data/figure_integration_validation.json. Regenerate with python3 manuscript/scripts/build_compact_study_figures.py; the main figure builder also calls it.

## Layout reference

IEEE conference template guidance places figures near their discussion, uses captions below figures and permits large figures across both columns. The specific choice of single-column study diagrams follows the author's preference; the paper retains the IEEEtran conference class, standard body font and margins. Reference: [IEEE conference template](https://www.overleaf.com/latex/templates/ieee-conference-template/grfzhhncsfqn), published by IEEE. Final page count, embedding, anonymity and references are checked on the compiled PDF, rather than inferred from the source layout.

Current results are recorded in data/figure_integration_validation.json and submission/format_report.json; the packaged sources are independently compiled before package_validation.json is refreshed.

## Layout correction

The methodology diagram now connects its source panel to the three analysis rows and joins the evidence outputs into a framed needs panel. Equal row heights and gutters keep the flow legible. Text rendering asserts at least 3 pt of padding within the methodology panels. Workflow arrows end exactly at panel borders and the output labels have more vertical space. Verification values and prefixes align to the right; zero violations has no misleading bar. The shared typography, palette and single-column widths are retained.
