# HazBot submission readiness

The current artifact is an anonymous IEEE-format research draft. The supplied guideline/guide.md is the working specification. Mechanical passes do not constitute author approval, conference acceptance, or application qualification.

## Completed locally

- IEEEtran conference format, two columns, A4, at most six pages including references.
- PDF below 3,000,000 bytes, all fonts embedded, no Type 3 fonts.
- Anonymous author block and empty author metadata.
- Resolved references, no overfull boxes, bounded scan for local identifiers.
- Nine numbered figures: original hardware architecture and seven-phase mission, three compact single-column study diagrams, arm geometry, two annotated photographs and dashboard. Architecture, mission and arm retain editable diagrams; supplied wide study PDFs are preserved alongside the compact vector derivatives.
- Source-isolated characterization, analytical wrist geometry, bounded reference-coordinator verification, saved CSV/JSON evidence, and generated results prose. Numerical tables that duplicate the study diagrams are excluded from print.
- Independent source ZIP compilation and packaging inspection are recorded in package_validation.json after the final build.

The format_report.json records the PDF hash and actual check outcomes. The current paper thanks open-source robotics communities and briefly acknowledges ChatGPT assistance with manuscript preparation. The broader assistance history is recorded below.

## Author review and evidence scope

Authors must review the manuscript, source interpretations, model assumptions, bibliography, and contribution. Results establish source geometry, gateway behavior, and command admissibility/phase reachability within a finite model. They do not establish physical obstacle avoidance, payload, hazardous-object recognition, or successful hazardous-material handling. The stated application is hazardous-object retrieval; the task context is a nonhazardous ball surrogate.

Confirm authorship and order, originality, appropriate attribution, similarity requirements, concurrent-submission rules, presentation availability, and the final venue instructions. IEEE PDF eXpress and similarity certification have not been performed. No account, submission, upload, or external communication was made.

## Unresolved assistance-policy requirement

The supplied guideline requires LLM acknowledgment and states that such use is “solely for non-intellectual purposes.” Assistance in this project included literature synthesis, study design, code, analysis, and drafting. The manuscript contains a brief acknowledgment of assistance with manuscript preparation. The acknowledgment does not certify non-intellectual-only use or completed human review. Venue-policy eligibility remains unresolved for author review.

## Anonymous package boundary

The PDF and Overleaf ZIP omit author identities, deployment configuration, private paths, source hashes, raw resource PDFs, and local audit notes. The complete local repository is not anonymized. The ZIP is a paper source package; reproduce experiments using the local research workspace. Review the final upload against the venue's current double-blind instructions before submission.
