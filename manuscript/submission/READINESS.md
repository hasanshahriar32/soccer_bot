# Submission readiness

This is a mechanically checked **anonymous research draft**, not a submission
approved by the authors or conference. The requirements were read from the
original `../guideline/guide.md`; no authorship information is copied from GOAD.

## Implemented and checked locally

- Standard IEEEtran conference mode, double column, A4, default IEEE typography.
- At most six pages including figures, tables, acknowledgment, and references.
- PDF no larger than 3,000,000 bytes; embedded fonts; no Type 3 fonts.
- Anonymous author block and empty PDF author metadata.
- PDF text checked for known local paths, private network identifiers,
  credentials, and local author details; this is a bounded identifier scan.
- Resolved citations and references, no overfull boxes, source ZIP allowlist.
- Reproducible source-execution experiment with raw constructed trace data.
- Three integrated technical figures and two optional figure sets, with PDF/SVG/PNG exports and two editable draw.io diagrams. Figure provenance and rendering checks are recorded in `../data/figure_manifest.json` and `../data/figure_validation.json`.
- Explicit limitations and truthful AI disclosure.

`format_report.json` records the actual result, PDF hash, page count, byte size,
and checked font count. These local checks do not replace IEEE PDF eXpress or
manual review of the final venue template and anonymity requirements.

## Unresolved venue restriction: substantive AI assistance

The supplied `guideline/guide.md` says:

> “such models were employed solely for non-intellectual purposes”

The user's requested work includes research synthesis, novelty investigation,
experimental design, coding, and manuscript drafting. Those activities exceed
copyediting. The paper's acknowledgment accurately identifies them; it does
not falsely certify non-intellectual-only use or human author approval.
Consequently **eligibility under this requirement is unresolved**. Authors
must obtain an applicable venue determination or choose an appropriate venue
before submitting this draft. Merely replacing the disclosure with a narrower
statement would not fix the underlying provenance.

## Author and scientific decisions before any submission

1. Independently review and approve the source audit, implemented experiment,
   generated tables, citations, contribution framing, and all manuscript text.
2. Decide whether the bounded offline case study is sufficient for the chosen
   track. No physical robot benchmark or deployed supervisor is available;
   stronger robotics claims need the planned measurements.
3. Confirm originality, appropriate attribution, accurate contribution and
   authorship order, no concurrent submission, and the venue's similarity
   criterion using an authorized process. None was certified here.
4. Verify the current conference template, deadlines, policies, and review
   requirements with the venue. The supplied guide is the local working spec;
   this work does not establish that an online 2027 policy page is final.
5. Run the conference's IEEE PDF eXpress workflow if required and inspect the
   final upload. Create the required CMT accounts and confirm presentation
   availability. No account, upload, publication, or communication was made.

## Artifact anonymity

The PDF and Overleaf source package omit repository links, source hashes,
machine paths, hardware screenshots, personal names, and runtime sources.
The local `research/`, `data/`, and experiment provenance retain paths and
commit fingerprints for reproducibility and should not automatically be sent
to anonymous reviewers. The full local repository is not claimed to be
anonymized. Do not upload runtime configuration or credential-bearing files.
