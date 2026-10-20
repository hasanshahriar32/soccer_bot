#!/usr/bin/env python3
"""Build an anonymous Overleaf source package from an explicit allowlist."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import shutil

BASE = Path(__file__).resolve().parents[1]
DEST = BASE / "submission/HazBot_IEEE_Overleaf.zip"


def main():
    selected = [BASE/"main.tex", BASE/"references.bib", BASE/"compile.sh"]
    for name in ("IEEEtran.cls", "IEEEtran.bst", "TEMPLATE_PROVENANCE.md"):
        if (BASE/name).exists():
            selected.append(BASE/name)
    for directory, pattern in (("sections", "*.tex"), ("figures", "hazbot_*.pdf"),
                               ("figures", "hazbot_*.svg"), ("figures", "hazbot_*.drawio"), ("generated", "hazbot_*.tex")):
        selected.extend(sorted((BASE/directory).glob(pattern)))
    assert all(p.is_file() and not p.is_symlink() for p in selected)
    DEST.parent.mkdir(exist_ok=True)
    with ZipFile(DEST, "w", ZIP_DEFLATED) as archive:
        for path in selected:
            archive.write(path, path.relative_to(BASE).as_posix())
        archive.writestr("OVERLEAF_README.txt", "HazBot: A Modular Raspberry Pi-Centered Mobile Manipulator for Hazardous-Object Retrieval\nCompile main.tex with pdfLaTeX (TeX Live + IEEEtran) and BibTeX, or run bash compile.sh.\nPre-rendered vector PDFs need no Python, ROS or robot hardware.\nEditable SVG and draw.io diagram assets are included.\nReported evidence is model-based and source-derived, with a ball-based nonhazardous surrogate context.\nThis is an anonymous research draft. Authors must review evidence and venue requirements before submission.\nRuntime sources, private paths, credentials, source hashes, and local research notes are excluded.\n")
    shutil.copyfile(DEST, BASE/"submission/SoccerBot_IEEE_Overleaf.zip")
    print(f"Created {DEST.relative_to(BASE)} ({DEST.stat().st_size} bytes; {len(selected)+1} files)")


if __name__ == "__main__":
    main()
