#!/usr/bin/env python3
"""Annotate the real HazBot prototype without modifying its photograph.

The raster is the user-supplied, uncropped JPEG. All labels, leaders and
registration markers are generated as SVG vectors. No synthetic image is used.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
import io
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image

BASE = Path(__file__).resolve().parents[1]
PHOTO = BASE.parent / "photo/bot.jpeg"
OUT = BASE / "figures"
INK = "#253748"
MUTED = "#627483"
BLUE = "#34799c"
TEAL = "#16858d"
GOLD = "#a87935"
RED = "#ac5c52"
PALE = "#dce5eb"
SOURCE_WIDTH, SOURCE_HEIGHT = 768, 998
EPOCH = str(int(datetime(2026, 10, 21, tzinfo=timezone.utc).timestamp()))
DASHBOARD = BASE.parent / "photo/dashboard_edited.png"

# Pixel anchors refer to the full, current 890 x 1161 photograph. A leader
# terminates at the actual visible component, never at an inferred hidden part.
ANNOTATIONS = [
    dict(id=1, side="right", row=109, title="BALL SURROGATE",
         detail="Nonhazardous task object", anchor=[432, 78], color=RED,
         rationale="Red spherical object visibly held between the end-effector jaws."),
    dict(id=2, side="right", row=218, title="GRIPPER",
         detail="Opposing end-effector jaws", anchor=[430, 112], color=RED,
         rationale="Wooden opposing jaw mechanism surrounds the ball."),
    dict(id=3, side="left", row=220, title="SERVO ACTUATION",
         detail="Exposed servo and wiring", anchor=[407, 158], color=RED,
         rationale="Blue servo body and its wiring are visible beneath the jaw assembly."),
    dict(id=4, side="left", row=345, title="ARTICULATED LINKAGE",
         detail="Arm links and pivot joints", anchor=[315, 310], color=RED,
         rationale="Paired long arm members and pivot fasteners are visible."),
    dict(id=5, side="right", row=393, title="RASPBERRY PI + DISPLAY",
         detail="GPIO-mounted local screen", anchor=[390, 505], color=BLUE,
         rationale="User identifies the Pi behind the screen and confirms the screen is connected directly by GPIO; the marker denotes that assembly."),
    dict(id=6, side="right", row=558, title="LIDAR SCANNER",
         detail="Rotating ranging assembly", anchor=[386, 735], color=TEAL,
         rationale="Rotating scan head and black scanner housing are visible; brand/model is not inferred from the image."),
    dict(id=7, side="left", row=610, title="WHEEL DRIVE",
         detail="Treaded wheel pair", anchor=[205, 780], color=GOLD,
         rationale="Left treaded wheel is marked; the corresponding right wheel is also visible."),
    dict(id=8, side="left", row=715, title="BATTERY CELLS",
         detail="Onboard electrical supply", anchor=[315, 820], color=GOLD,
         rationale="Cylindrical cells in a holder are visible; cell chemistry, voltage and runtime are not inferred."),
    dict(id=9, side="right", row=710, title="CONTROL ELECTRONICS",
         detail="Exposed boards and wiring", anchor=[450, 885], color=BLUE,
         rationale="Lower-platform electronic boards and harness are visible; the marker does not infer a particular board model."),
    dict(id=10, side="left", row=470, title="CAMERA MODULE",
         detail="White CSI ribbon to Pi", anchor=[380, 350], color=BLUE,
         rationale="User identifies the camera at the far end of the white ribbon from the Pi; zoom inspection locates the small board and lens beside the arm."),
]

MARKERS = {1:[650,100], 2:[650,210], 3:[260,220], 4:[150,350],
           5:[650,505], 6:[650,735], 7:[90,780], 8:[95,900],
           9:[650,900], 10:[620,350]}
for annotation in ANNOTATIONS:
    annotation.pop("side"); annotation.pop("row")
    annotation["marker"] = MARKERS[annotation["id"]]

FRONT_ANNOTATIONS = [
    dict(id=1, title="LAPTOP VISUALIZATION", detail="Optional visualization workstation",
         anchor=[330,270], marker=[120,150], color=BLUE,
         rationale="Laptop and robot-monitoring interface are visible; this does not imply offboard ML inference."),
    dict(id=2, title="LIDAR SCANNER", detail="Rotating ranging head",
         anchor=[820,180], marker=[930,100], color=TEAL,
         rationale="Rotating scanner is visible above the robot."),
    dict(id=3, title="ARTICULATED ARM", detail="Links and pivot joints",
         anchor=[810,330], marker=[955,360], color=RED,
         rationale="Articulated wooden links and joints are visible on the robot's right side."),
    dict(id=4, title="GRIPPER", detail="Opposing end-effector jaws",
         anchor=[620,300], marker=[620,150], color=RED,
         rationale="Open jaw mechanism projects toward the laptop."),
    dict(id=5, title="CSI CAMERA", detail="Front-mounted camera module",
         anchor=[690,440], marker=[690,650], color=BLUE,
         rationale="Green camera module with lens and ribbon connector is visible on the front platform."),
    dict(id=6, title="MOBILE BASE", detail="Robot chassis and support platform",
         anchor=[850,480], marker=[950,570], color=GOLD,
         rationale="Robot base, front platform and support structure are visible; no measured mobility performance is inferred."),
    dict(id=7, title="BALL SURROGATE", detail="Nonhazardous task object",
         anchor=[420,650], marker=[560,690], color=RED,
         rationale="Red ball is visible on the floor in front of the robot."),
]

DASHBOARD_ANNOTATIONS = [
    dict(id=1, title="CAMERA VIEW", detail="Ball-detection panel",
         anchor=[175, 365], marker=[110, 120], color=BLUE),
    dict(id=2, title="LIDAR / SLAM MAP", detail="Range-map visualization",
         anchor=[585, 370], marker=[520, 120], color=TEAL),
    dict(id=3, title="WHEEL TELEOP", detail="Manual drive controls",
         anchor=[1070, 150], marker=[1180, 85], color=GOLD),
    dict(id=4, title="ARM CONTROL", detail="Four-servo interface",
         anchor=[1075, 500], marker=[1180, 690], color=RED),
    dict(id=5, title="BALL AUTOPILOT", detail="Mission-control action",
         anchor=[400, 710], marker=[250, 735], color=RED),
]


def strip_private_metadata(jpeg: bytes) -> bytes:
    """Drop nonessential JPEG metadata without decoding/re-encoding pixels.

    Keep JFIF identification, the ICC profile and Adobe color-transform marker.
    The scan header and all entropy-coded image bytes remain unchanged.
    """
    assert jpeg[:2] == b"\xff\xd8"
    result = bytearray(jpeg[:2])
    pos = 2
    while pos < len(jpeg):
        start = pos
        assert jpeg[pos] == 0xff, "Invalid JPEG marker boundary"
        while jpeg[pos] == 0xff:
            pos += 1
        marker = jpeg[pos]
        pos += 1
        if marker in (0xda, 0xd9):
            result.extend(jpeg[start:])
            return bytes(result)
        length = int.from_bytes(jpeg[pos:pos+2], "big")
        end = pos + length
        assert length >= 2 and end <= len(jpeg)
        payload = jpeg[pos+2:end]
        is_app = 0xe0 <= marker <= 0xef
        retain = (not is_app and marker != 0xfe) or (
            marker == 0xe0 and payload.startswith(b"JFIF\0")) or (
            marker == 0xe2 and payload.startswith(b"ICC_PROFILE\0")) or (
            marker == 0xee and payload.startswith(b"Adobe"))
        if retain:
            result.extend(jpeg[start:end])
        pos = end
    raise ValueError("JPEG scan data absent")


def make_svg(photo_bytes: bytes, size, physical_width, annotations, title, description, font_size, media_type="image/jpeg") -> str:
    width, height = size
    physical_height = physical_width*height/width
    parts = []
    data = base64.b64encode(photo_bytes).decode("ascii")
    parts.append(f'<image id="original-photograph" x="0" y="0" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" href="data:{media_type};base64,{data}"/>')
    radius = font_size*.8
    for annotation in annotations:
        ident = annotation["id"]
        ax, ay = annotation["anchor"]
        cx, cy = annotation["marker"]
        color = annotation["color"]
        parts.append(f'<path id="leader-{ident}" d="M{cx},{cy}L{ax},{ay}" stroke="white" stroke-width="6" fill="none"/>')
        parts.append(f'<path d="M{cx},{cy}L{ax},{ay}" stroke="{color}" stroke-width="3" fill="none"/>')
        parts.append(f'<circle cx="{ax}" cy="{ay}" r="4" fill="white" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" stroke="white" stroke-width="3"/>')
        parts.append(f'<text x="{cx}" y="{cy+font_size*.36:g}" text-anchor="middle" font-size="{font_size}" font-weight="700" fill="white">{ident}</text>')
    key = "; ".join(f'{a["id"]}: {a["title"].lower()}' for a in annotations)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{physical_width}in" height="{physical_height}in" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(title)}</title>'
            f'<desc id="desc">{escape(description)} Numbered component key: {escape(key)}.</desc>'
            '<g font-family="Noto Sans,sans-serif">'+"".join(parts)+'</g></svg>\n')


def _render(photo_path, stem, expected_size, physical_width, annotations, json_name, title, description, font_size, provenance) -> dict:
    width, height = expected_size
    dimensions = [physical_width, physical_width*height/width]
    source_path = str(photo_path.relative_to(BASE.parent))
    if not photo_path.is_file():
        return {"available": False, "figure_stem": stem,
                "source_path": source_path, "dimensions_inches": dimensions,
                "reason": "User-supplied prototype photo is absent; existing artifacts were not overwritten."}
    source = photo_path.read_bytes()
    with Image.open(io.BytesIO(source)) as original:
        assert original.size == expected_size, "Review anchor coordinates for a changed photograph."
        exif = original.getexif()
        metadata_presence = {"exif": bool(exif), "gps": bool(exif.get(34853)),
                             "comment": bool(original.info.get("comment")),
                             "icc_color_profile": bool(original.info.get("icc_profile"))}
        assert exif.get(274) in (None, 1), "Review orientation before removing EXIF."
        original_pixels = original.tobytes()
    embedded_photo = strip_private_metadata(source) if source.startswith(b"\xff\xd8") else source
    with Image.open(io.BytesIO(embedded_photo)) as clean:
        assert not clean.getexif() and not clean.info.get("comment")
        assert clean.tobytes() == original_pixels, "Metadata removal must preserve every decoded pixel."
    OUT.mkdir(exist_ok=True)
    svg = OUT / f"{stem}.svg"
    media_type = Image.MIME.get(Image.open(io.BytesIO(embedded_photo)).format, "image/jpeg")
    svg.write_text(make_svg(embedded_photo, expected_size, physical_width, annotations, title, description, font_size, media_type))
    env = dict(os.environ, SOURCE_DATE_EPOCH=EPOCH)
    subprocess.run(["rsvg-convert", "--format=pdf1.5", "--output", str(OUT/f"{stem}.pdf"), str(svg)], check=True, env=env)
    subprocess.run(["rsvg-convert", "--format=png", f"--width={width}", f"--height={height}", "--output", str(OUT/f"{stem}.png"), str(svg)], check=True, env=env)
    tree = ET.fromstring(svg.read_text())
    images = tree.findall(".//{http://www.w3.org/2000/svg}image")
    assert len(images) == 1
    embedded = base64.b64decode(images[0].attrib["href"].split(",", 1)[1])
    assert embedded == embedded_photo, "Embedded photograph must match the losslessly cleaned JPEG."
    assert len({a["id"] for a in annotations}) == len(annotations)
    for a in annotations:
        for point in (a["anchor"], a["marker"]):
            assert 0 <= point[0] <= width and 0 <= point[1] <= height
    with Image.open(OUT/f"{stem}.png") as png:
        assert png.size == expected_size
    metadata = {
        "available": True, "figure_stem": stem,
        "renderer": "Python-authored SVG labels and leaders; original JPEG photograph; librsvg PDF/PNG export",
        "source": source_path, "source_path": source_path, "source_sha256": sha256(source).hexdigest(),
        "original_size_px": [width, height], "original_metadata_presence": metadata_presence,
        "embedded_source_byte_identical": embedded_photo == source,
        "embedded_pixel_identical_to_source": True,
        "embedded_jpeg_sha256": sha256(embedded_photo).hexdigest(),
        "source_pixel_modification": "none; entire current photograph retained; no crop, retouch, synthesis or pixel re-encoding before embedding",
        "source_privacy_review": "Nonessential JPEG metadata removed losslessly, including EXIF/XMP, comments and Photoshop metadata. JFIF/ICC/Adobe color interpretation retained. Original user file remains untouched.",
        "dimensions_inches": dimensions, "png_resolution_dpi": width/physical_width,
        "png_native_size_px": [width, height],
        "photo_viewport_canvas": [0, 0, width, height],
        "photo_bbox_canvas": [0, 0, width, height],
        "canvas_viewbox": [width, height],
        "compact_layout": True, "no_added_canvas": True,
        "layout": "Native-aspect full-frame photograph; numbered circles and short leaders only; component key belongs in paper caption.",
        "font": "Noto Sans", "media_type": "real photograph with vector annotations; not an all-vector illustration",
        "annotations": [{**a, "anchor_normalized": [a["anchor"][0]/width, a["anchor"][1]/height]} for a in annotations],
        "unidentified_components": [],
        "identification_provenance": provenance,
        "evidence_scope": "Visible prototype component identification; no claim of autonomous grasp success or hazardous-material handling follows from the photograph.",
        "generator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "sha256": {ext: sha256((OUT/f"{stem}.{ext}").read_bytes()).hexdigest() for ext in ("svg", "pdf", "png")},
        "validation": {"one_original_photo": True, "all_callout_ids_unique": True,
                       "all_anchor_coordinates_in_source_bounds": True,
                       "png_matches_native_photo_dimensions": True,
                       "no_extra_canvas_or_aspect_change": True,
                       "embedded_pixels_identical_to_source": True,
                       "private_metadata_absent_in_embedded_jpeg": True},
    }
    (BASE/f"data/{json_name}").write_text(json.dumps(metadata, indent=2)+"\n")
    return metadata


def render() -> dict:
    return _render(PHOTO, "hazbot_prototype", (SOURCE_WIDTH, SOURCE_HEIGHT), 2.7,
        ANNOTATIONS, "prototype_annotation.json", "HazBot physical prototype",
        "Full user-supplied prototype photograph. Pi/display and camera identifications are confirmed by the user. Photograph alone does not establish autonomous mission performance.", 30,
        {"Pi_display_assembly": "User confirms screen is directly connected to Raspberry Pi through GPIO.", "camera": "User confirms white ribbon from Raspberry Pi terminates at camera; image zoom used to anchor visible board/lens."})


def render_front() -> dict:
    return _render(BASE.parent/"photo/laptop_front.jpeg", "hazbot_front", (1024,768), 3.45,
        FRONT_ANNOTATIONS, "front_annotation.json", "HazBot front view and visualization workstation",
        "Full user-supplied front-view photograph. Laptop is a visualization workstation; the photograph does not move native ML inference off the Raspberry Pi. Ball is a nonhazardous task surrogate. Photograph alone does not establish autonomous mission performance.", 36,
        {"front_view": "User supplies the front-view photograph with laptop and requests the same component annotation style.", "camera": "Visible green camera board, lens and ribbon connector.", "laptop": "Visible visualization interface; no inference-host claim."})


def render_dashboard() -> dict:
    """Render the user-supplied dashboard with numbered panel callouts."""
    if not DASHBOARD.is_file():
        return {"available": False, "figure_stem": "hazbot_dashboard",
                "source_path": "photo/dashboard_edited.png",
                "reason": "Dashboard image is absent."}
    with Image.open(DASHBOARD) as image:
        width, height = image.size
    source = DASHBOARD.read_bytes()
    data = base64.b64encode(source).decode("ascii")
    parts = [f'<image x="0" y="0" width="{width}" height="{height}" href="data:image/png;base64,{data}"/>']
    for annotation in DASHBOARD_ANNOTATIONS:
        ax, ay = annotation["anchor"]
        cx, cy = annotation["marker"]
        color = annotation["color"]
        ident = annotation["id"]
        parts.extend([
            f'<path d="M{cx},{cy}L{ax},{ay}" stroke="white" stroke-width="7" fill="none"/>',
            f'<path d="M{cx},{cy}L{ax},{ay}" stroke="{color}" stroke-width="3" fill="none"/>',
            f'<circle cx="{ax}" cy="{ay}" r="5" fill="white" stroke="{color}" stroke-width="2"/>',
            f'<circle cx="{cx}" cy="{cy}" r="25" fill="{color}" stroke="white" stroke-width="3"/>',
            f'<text x="{cx}" y="{cy+9}" text-anchor="middle" font-size="25" font-weight="700" fill="white">{ident}</text>',
        ])
    svg = OUT / "hazbot_dashboard.svg"
    svg.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="7.1in" height="{7.1*height/width}in" '
        f'viewBox="0 0 {width} {height}" role="img"><title>HazBot dashboard</title>'
        f'<desc>Numbered callouts identify the camera, LiDAR map, wheel teleoperation, arm control, and ball-autopilot panels.</desc>'
        f'<g font-family="Noto Sans,sans-serif">{"".join(parts)}</g></svg>\n'
    )
    env = dict(os.environ, SOURCE_DATE_EPOCH=EPOCH)
    subprocess.run(["rsvg-convert", "--format=pdf1.5", "--output", str(OUT/"hazbot_dashboard.pdf"), str(svg)], check=True, env=env)
    subprocess.run(["rsvg-convert", "--format=png", f"--width={width}", f"--height={height}", "--output", str(OUT/"hazbot_dashboard.png"), str(svg)], check=True, env=env)
    metadata = {
        "available": True, "figure_stem": "hazbot_dashboard",
        "source": "photo/dashboard_edited.png", "source_sha256": sha256(source).hexdigest(),
        "original_size_px": [width, height], "dimensions_inches": [7.1, 7.1*height/width],
        "media_type": "user-supplied dashboard screenshot with vector annotations",
        "annotations": DASHBOARD_ANNOTATIONS,
        "evidence_scope": "Visible software panels only; screenshot does not establish online connectivity, detector accuracy, SLAM quality, or mission success.",
        "sha256": {ext: sha256((OUT/f"hazbot_dashboard.{ext}").read_bytes()).hexdigest() for ext in ("svg", "pdf", "png")},
    }
    (BASE/"data/dashboard_annotation.json").write_text(json.dumps(metadata, indent=2)+"\n")
    return metadata


if __name__ == "__main__":
    for result in (render(), render_front(), render_dashboard()):
        print(json.dumps({key: result[key] for key in ("available", "figure_stem", "source_sha256", "dimensions_inches", "embedded_source_byte_identical", "sha256", "reason") if key in result}))
