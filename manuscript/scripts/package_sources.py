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
    selected.extend(sorted((BASE/"sections").glob("*.tex")))
    selected.extend(sorted((BASE/"generated").glob("hazbot_*.tex")))
    active = ("hazbot_architecture", "hazbot_mission", "hazbot_arm_geometry", "hazbot_prototype", "hazbot_front", "hazbot_dashboard")
    for stem in active:
        for extension in ("pdf", "svg", "drawio"):
            asset = BASE/"figures"/f"{stem}.{extension}"
            if asset.exists():
                selected.append(asset)
    photo_dir = BASE/"figures/photos"
    if photo_dir.exists():
        selected.extend(sorted(p for p in photo_dir.iterdir()
                               if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".pdf", ".md")))
    assert all(p.is_file() and not p.is_symlink() for p in selected)
    DEST.parent.mkdir(exist_ok=True)
    with ZipFile(DEST, "w", ZIP_DEFLATED) as archive:
        for path in selected:
            archive.write(path, path.relative_to(BASE).as_posix())
        archive.writestr("OVERLEAF_README.txt", "HazBot: A Modular Raspberry Pi-Centered Mobile Manipulator for Hazardous-Object Retrieval\nCompile main.tex with pdfLaTeX (TeX Live + IEEEtran) and BibTeX, or run bash compile.sh.\nPre-rendered vector PDFs need no Python, ROS or robot hardware.\nEditable SVG and draw.io diagram assets are included.\nThe annotated real prototype photograph is included as figures/hazbot_prototype.pdf.\nThe retired wheel partition diagram is excluded.\nReported evidence is model-based and source-derived, with a ball-based nonhazardous surrogate context.\nThis is an anonymous research draft. Authors must review evidence and venue requirements before submission.\nRuntime sources, private paths, credentials, source hashes, and local research notes are excluded.\n")
    shutil.copyfile(DEST, BASE/"submission/SoccerBot_IEEE_Overleaf.zip")
    print(f"Created {DEST.relative_to(BASE)} ({DEST.stat().st_size} bytes; {len(selected)+1} files)")


if __name__ == "__main__":
    main()
