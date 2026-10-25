# Figure integration, 25 October 2026

The author requests that the original architecture and seven-phase mission be retained and the three supplied study diagrams be compact single-column figures, while the full manuscript stays within six A4 pages.

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

The supplied methodology and verification diagrams were compared with data/hazbot_characterization.json and data/hazbot_mission_results.json and the two executable studies. They describe offline source/model evidence, not physical task trials. The compact renderer checks the source counts and captures source/output SHA-256 hashes in data/compact_study_figures.json.

The workflow's old “Feedback (B)” label mixed base rest with grip and release. The compact caption states that these are separate planned observations. The drawing gates arm motion on B and drive motion on S, C and A; authorization T remains part of the coordinator's contracts. The two serial paths remain separate. No claim of deployed end-to-end autonomy is added.

The original supplied wide PDFs are preserved byte-for-byte. The _column.pdf derivatives reflow their content rather than halve the original 6.5 pt labels. The derivatives are 3.45 inches wide, use embedded DejaVu Sans at 6.5 pt or above, and contain vector drawing/text. Regeneration: python3 manuscript/scripts/build_compact_study_figures.py.

## Layout reference

IEEE conference template guidance places figures near their discussion, uses captions below figures and permits large figures across both columns. The specific choice of single-column study diagrams follows the author's preference; the paper retains the IEEEtran conference class, standard body font and margins. Reference: [IEEE conference template](https://www.overleaf.com/latex/templates/ieee-conference-template/grfzhhncsfqn), published by IEEE. Final page count, embedding, anonymity and references are checked on the compiled PDF, rather than inferred from the source layout.

Current results are recorded in data/figure_integration_validation.json and submission/format_report.json; the packaged sources are independently compiled before package_validation.json is refreshed.
