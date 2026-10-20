# IEEE template provenance

The paper uses `\documentclass[conference,a4paper]{IEEEtran}` with the standard
IEEE class layout. It does not reuse GOAD's single-column styling or adjust
margins, leading, or body font size to meet the page limit.

Two unmodified upstream support files are included for reproducible compilation:

| File | Upstream version | SHA-256 |
| --- | --- | --- |
| `IEEEtran.cls` | V1.8b, 2015-08-26 | `da751920a317ed318b7b5cd7fa585a6cc7d28502d457856382e9be24b10a3bd7` |
| `IEEEtran.bst` | V1.14, 2015-08-26 | `314f0ece704568faf827011bac498650691b2b5ee06320720830e782416d5a5f` |

The files came from Tectonic's TeX distribution bundle during the local build.
Their upstream copyright, contributor notices, and LPPL 1.3 license terms are
preserved in their headers. See the [IEEEtran package](https://ctan.org/pkg/ieeetran),
the [maintainer's documentation](https://www.michaelshell.org/tex/ieeetran/),
and [IEEE authoring resources](https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/authoring-tools-and-templates/).
The venue's eventual supplied template should be checked for additional
requirements before submission.

Source-package compilation requires a standard LaTeX distribution with the
packages listed in `main.tex`. The vector figures and generated tables are
already included. The ZIP excludes local logs, source fingerprints, runtime
files, research notes, and identification-bearing screenshots.
