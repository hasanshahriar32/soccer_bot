#!/usr/bin/env python3
"""Check local, mechanically verifiable requirements; not venue certification."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
PDF = BASE / "submission/HazBot_IEEE_Anonymous.pdf"


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main():
    checks = []

    def require(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})

    if not PDF.exists():
        raise SystemExit("Compile first: bash manuscript/compile.sh")
    info = run("pdfinfo", str(PDF))
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M)[1])
    require("maximum_six_pages", 1 <= pages <= 6, f"{pages} pages, maximum 6")
    require("maximum_three_MB", PDF.stat().st_size <= 3_000_000, f"{PDF.stat().st_size} bytes")
    boxes = run("pdfinfo", "-f", "1", "-l", str(pages), "-box", str(PDF))
    sizes = re.findall(r"(?:Page\s+\d+\s+size|Page size):\s+([\d.]+)\s+x\s+([\d.]+)", boxes)
    require("A4_all_pages", len(sizes) == pages and all(abs(float(w)-595.28) < 1 and abs(float(h)-841.89) < 1 for w, h in sizes), f"{len(sizes)} A4 page sizes checked")
    fonts = run("pdffonts", str(PDF))
    entries = fonts.strip().splitlines()[2:]
    flags = [re.search(r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", line) for line in entries]
    require("embedded_fonts", bool(entries) and all(m and m[1] == "yes" for m in flags), f"{len(entries)} font entries")
    require("no_Type_3_fonts", not re.search(r"Type\s*3", fonts, re.I), "pdffonts inspection")
    author = re.search(r"^Author:\s*(.*)$", info, re.M)
    require("anonymous_PDF_author_metadata", author is None or not author[1].strip(), "Author metadata empty or absent")
    text = run("pdftotext", str(PDF), "-")
    require("anonymous_author_block", "Anonymous Authors" in text, "Anonymous author block present")
    identifiers = ["/home/", "/Users/", "192.168.", "10.127."]
    leaked = [s for s in identifiers if s.lower() in text.lower()]
    require("no_known_local_identifiers_in_PDF", not leaked, "No known machine paths or private network identifiers" if not leaked else "Known identifier detected")
    require("no_email_addresses_in_anonymous_PDF", not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text), "No email addresses in PDF text")
    require("no_unresolved_reference_markers", "??" not in text, "No double-question reference markers")
    log = BASE / "build/main.log"
    if log.exists():
        log_text = log.read_text(errors="replace")
        unresolved = re.search(r"(?:Citation|Reference)[^\n]*undefined|There were undefined", log_text, re.I)
        require("resolved_TeX_references", not unresolved, "Compiler log inspected")
        require("no_overfull_boxes", "Overfull \\hbox" not in log_text and "Overfull \\vbox" not in log_text, "Compiler log inspected; underfull spacing warnings are permitted")
    normalized = re.sub(r"\s+", " ", text)
    require("LLM_acknowledgment_present", "ChatGPT" in normalized and "large language model" in normalized,
            "Explicit model name and assistance disclosure in acknowledgment")
    require("retired_wheel_plot_absent", "WHEEL GATEWAY / EXACT SIGN PARTITION" not in normalized,
            "Retired sign-partition figure excluded")
    require("prototype_photograph_present", (BASE/"figures/hazbot_prototype.pdf").exists()
            and "Physical HazBot prototype" in normalized,
            "Annotated real photograph asset and caption present")
    require("front_view_photograph_present", (BASE/"figures/hazbot_front.pdf").exists()
            and "Front view with laptop visualization" in normalized,
            "Compact annotated front-view photograph and caption present")
    source = "\n".join(p.read_text() for p in [BASE/"main.tex", *sorted((BASE/"sections").glob("*.tex"))])
    cites = {k.strip() for group in re.findall(r"\\cite\{([^}]+)\}", source) for k in group.split(",")}
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,]+),", (BASE/"references.bib").read_text()))
    require("citation_keys_exist", cites <= bib_keys, f"{len(cites)} cited keys; missing {sorted(cites-bib_keys)}")
    result = {
        "scope": "Local format checks only. Not IEEE PDF eXpress certification, novelty certification, similarity checking, authorship approval, or venue-policy approval.",
        "pdf": PDF.name, "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "checks": checks, "all_mechanical_checks_pass": all(c["passed"] for c in checks),
        "pending_author_decisions": [
            "The manuscript acknowledges substantive ChatGPT assistance. The supplied guideline restricts LLM use to non-intellectual purposes; eligibility under that restriction and human approval remain unresolved. Mechanical passes do not establish eligibility.",
            "Human verification and approval of research, source interpretations, bibliography, and submission are required.",
            "No similarity service, IEEE PDF eXpress, originality certification, or simultaneous-submission check was run.",
            "Results concern source geometry, isolated command execution and a new abstract mission reference model, not physical hazard handling."
        ]
    }
    (BASE / "submission/format_report.json").write_text(json.dumps(result, indent=2)+"\n")
    for item in checks:
        print(f"{'PASS' if item['passed'] else 'FAIL'} {item['check']}: {item['detail']}")
    print("Venue eligibility and author approval remain pending; see submission/READINESS.md.")
    return 0 if result["all_mechanical_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
