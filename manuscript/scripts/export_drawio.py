#!/usr/bin/env python3
"""Export the original architecture SVG to separately editable draw.io objects.

This deliberately supports the element types used by architecture.svg. Text,
rectangles, and orthogonal connectors become native mxGraph cells. Each original
technical glyph is its own self-contained SVG image cell, rather than a flattened
picture of the complete diagram. No network, external icons, or icon font is used.
"""
from __future__ import annotations

import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
PAPER = Path(__file__).resolve().parents[1]
NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?")


def _num(value):
    return f"{float(value):.5f}".rstrip("0").rstrip(".") or "0"


def _style(**values):
    return ";".join(f"{key}={value}" for key, value in values.items()) + ";"


def _svg_data(element, viewbox):
    root = ET.Element(f"{{{SVG}}}svg", {
        "viewBox": " ".join(_num(v) for v in viewbox),
        "width": _num(viewbox[2]), "height": _num(viewbox[3]),
    })
    root.append(copy.deepcopy(element))
    return "data:image/svg+xml," + quote(ET.tostring(root, encoding="unicode"), safe="")


def _outline_bounds(element):
    """Tight bounds for the architecture's straight M/L/H/V decorative paths."""
    tokens = re.findall(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?", element.attrib["d"])
    x = y = 0.0
    first = (x, y)
    points = []
    command = None
    index = 0
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
        if command in "Zz":
            x, y = first
            points.append((x, y))
            command = None
            continue
        if command not in ("M", "m", "L", "l", "H", "h", "V", "v"):
            raise ValueError("Only straight architecture paths have editable export bounds")
        relative = command.islower()
        if command.upper() in ("M", "L"):
            nx, ny = float(tokens[index]), float(tokens[index+1])
            index += 2
            x, y = (x+nx, y+ny) if relative else (nx, ny)
            if command.upper() == "M":
                first = (x, y)
                command = "l" if relative else "L"
        elif command.upper() == "H":
            nx = float(tokens[index]); index += 1
            x = x+nx if relative else nx
        else:
            ny = float(tokens[index]); index += 1
            y = y+ny if relative else ny
        points.append((x, y))
    pad = max(2, float(element.attrib.get("stroke-width", 1)))
    x0 = min(p[0] for p in points)-pad
    y0 = min(p[1] for p in points)-pad
    x1 = max(p[0] for p in points)+pad
    y1 = max(p[1] for p in points)+pad
    return [x0, y0, x1-x0, y1-y0]


def export_drawio(svg_path, output_path):
    """Write deterministic uncompressed draw.io XML; return auditable counts.

    The editable SVG is the publication master. Browser text metrics may require
    small adjustments after draw.io import. Glyph internals remain SVG geometry;
    each glyph can be moved/resized/replaced independently in draw.io.
    """
    svg_path, output_path = Path(svg_path), Path(output_path)
    source = svg_path.read_bytes()
    svg = ET.fromstring(source)
    viewbox = [float(v) for v in svg.attrib["viewBox"].split()]
    symbols = {e.attrib["id"]: e for e in svg.iter(f"{{{SVG}}}symbol")}
    file = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device",
                                "compressed": "false"})
    diagram = ET.SubElement(file, "diagram", {"id": "soccerbot-technical-architecture",
                                              "name": "SoccerBot architecture"})
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": _num(viewbox[2]), "dy": _num(viewbox[3]), "grid": "0", "gridSize": "10",
        "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
        "fold": "1", "page": "1", "pageScale": "1",
        "pageWidth": _num(viewbox[2]), "pageHeight": _num(viewbox[3]),
        "math": "0", "shadow": "0", "background": "#ffffff",
    })
    cells = ET.SubElement(model, "root")
    ET.SubElement(cells, "mxCell", {"id": "0"})
    ET.SubElement(cells, "mxCell", {"id": "1", "parent": "0"})
    counts = {"text_cells": 0, "rectangle_cells": 0, "icon_cells": 0,
              "connector_cells": 0, "waypoint_points": 0,
              "attached_terminals": 0, "decorative_svg_cells": 0}
    serial = 0
    icon_boxes = []
    flattened = []

    def walk(element, inherited):
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"defs", "title", "desc"}:
            return
        attrs = dict(inherited)
        attrs.update(element.attrib)
        if tag in {"svg", "g"}:
            for child in element:
                walk(child, attrs)
        else:
            flattened.append((element, tag, attrs))

    walk(svg, {})

    def vertex(kind, value, style, x, y, width, height):
        nonlocal serial
        serial += 1
        ident = f"{kind}-{serial:03d}"
        cell = ET.SubElement(cells, "mxCell", {"id": ident, "value": value,
            "style": style, "vertex": "1", "parent": "1"})
        ET.SubElement(cell, "mxGeometry", {"x": _num(x), "y": _num(y),
            "width": _num(width), "height": _num(height), "as": "geometry"})
        return ident

    # Reserve icon IDs first so edges can attach to movable objects regardless
    # of their order in the source SVG; rendering order still follows the SVG.
    icon_ids = {}
    future_serial = 0
    for element, tag, attrs in flattened:
        if tag == "rect" and "x" not in element.attrib and "y" not in element.attrib:
            continue  # The mxGraph page supplies the white canvas.
        future_serial += 1
        if tag == "use":
            ident = f"icon-{future_serial:03d}"
            icon_ids[id(element)] = ident
            icon_boxes.append((ident, *[float(attrs.get(k, 0)) for k in ("x", "y", "width", "height")]))

    def terminal(point):
        x, y = point
        candidates = []
        for ident, bx, by, bw, bh in icon_boxes:
            dx = max(bx-x, 0, x-(bx+bw))
            dy = max(by-y, 0, y-(by+bh))
            if dx*dx+dy*dy <= 12**2:
                candidates.append((dx*dx+dy*dy, bw*bh, ident, bx, by, bw, bh))
        if not candidates:
            return None
        _, _, ident, bx, by, bw, bh = min(candidates)
        return ident, min(1, max(0, (x-bx)/bw)), min(1, max(0, (y-by)/bh))

    for element, tag, attrs in flattened:
        if tag == "rect" and "x" not in element.attrib and "y" not in element.attrib:
            continue
        if tag == "use":
            name = attrs.get("href", attrs.get(f"{{{SVG}}}href", "")).lstrip("#")
            symbol = symbols[name]
            inner = ET.Element(f"{{{SVG}}}g")
            for child in symbol:
                inner.append(copy.deepcopy(child))
            image = _svg_data(inner, [float(v) for v in symbol.attrib["viewBox"].split()])
            ident = vertex("icon", "", _style(shape="image", imageAspect=0,
                aspect="fixed", image=image, opacity=100*float(attrs.get("opacity", 1)),
                resizable=1, movable=1),
                *[float(attrs.get(k, 0)) for k in ("x", "y", "width", "height")])
            assert ident == icon_ids[id(element)]
            counts["icon_cells"] += 1
        elif tag == "text":
            text = "".join(element.itertext())
            size = float(attrs.get("font-size", 20))
            # Conservative boxes preserve native left/center/right text anchors.
            # No optional font-measurement dependency changes exported geometry.
            bold = float(attrs.get("font-weight", 400)) >= 600
            width = max(size, len(text)*size*.68 + 6)
            x, y = float(attrs.get("x", 0)), float(attrs.get("y", 0))
            anchor = attrs.get("text-anchor", "start")
            if anchor == "middle":
                x -= width/2
            elif anchor == "end":
                x -= width
            vertex("text", text, _style(text="", html=0, strokeColor="none", fillColor="none",
                align={"start":"left", "middle":"center", "end":"right"}[anchor],
                verticalAlign="middle", whiteSpace="nowrap", overflow="visible", spacing=0,
                fontFamily="Noto Sans", fontSize=_num(size), fontStyle=1 if bold else 0,
                fontColor=attrs.get("fill", "#263645")), x, y-size*1.12, width, size*1.4)
            counts["text_cells"] += 1
        elif tag == "rect":
            vertex("rect", "", _style(shape="rectangle", rounded=1 if float(attrs.get("rx", 0)) else 0,
                arcSize=2, fillColor=attrs.get("fill", "none"),
                strokeColor=attrs.get("stroke", "none"), strokeWidth=attrs.get("stroke-width", "1"),
                dashed=1 if "stroke-dasharray" in attrs else 0, dashPattern="7 5"),
                *[float(attrs.get(k, 0)) for k in ("x", "y", "width", "height")])
            counts["rectangle_cells"] += 1
        elif tag == "polyline":
            coords = [float(v) for v in NUMBER.findall(attrs["points"])]
            points = list(zip(coords[::2], coords[1::2]))
            serial += 1
            style = dict(edgeStyle="none", rounded=0, html=0,
                strokeColor=attrs.get("stroke", "#8a96a1"),
                strokeWidth=attrs.get("stroke-width", "2.3"),
                dashed=1 if "stroke-dasharray" in attrs else 0, dashPattern="8 5",
                startArrow="none", endArrow="open" if "marker-end" in attrs else "none",
                endFill=0, endSize=8)
            cell_attrs = {"id": f"route-{serial:03d}", "value": "", "edge": "1", "parent": "1"}
            for point, key, prefix in ((points[0], "source", "exit"), (points[-1], "target", "entry")):
                attached = terminal(point)
                if attached:
                    cell_attrs[key] = attached[0]
                    style[prefix+"X"], style[prefix+"Y"] = map(_num, attached[1:])
                    style[prefix+"Perimeter"] = 0
                    counts["attached_terminals"] += 1
            cell_attrs["style"] = _style(**style)
            cell = ET.SubElement(cells, "mxCell", cell_attrs)
            geom = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            for point, label in ((points[0], "sourcePoint"), (points[-1], "targetPoint")):
                ET.SubElement(geom, "mxPoint", {"x": _num(point[0]), "y": _num(point[1]), "as": label})
            if len(points) > 2:
                waypoints = ET.SubElement(geom, "Array", {"as": "points"})
                for x, y in points[1:-1]:
                    ET.SubElement(waypoints, "mxPoint", {"x": _num(x), "y": _num(y)})
                counts["waypoint_points"] += len(points)-2
            counts["connector_cells"] += 1
        elif tag == "path":
            # Decorative display outlines and separator rules remain independent
            # tightly bounded SVG objects. They can be selected and moved;
            # edit their internal geometry in the original SVG.
            bounds = _outline_bounds(element)
            image = _svg_data(element, bounds)
            vertex("decoration", "", _style(shape="image", imageAspect=0,
                image=image), *bounds)
            counts["decorative_svg_cells"] += 1
        else:
            raise ValueError(f"Unsupported architecture element: {tag}")

    ET.indent(file, space="  ")
    payload = ET.tostring(file, encoding="utf-8", xml_declaration=True) + b"\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)
    assert len({cell.attrib["id"] for cell in cells}) == len(cells)
    return {"format": "draw.io uncompressed mxGraph XML", "file": output_path.name,
        "source_svg_sha256": sha256(source).hexdigest(), "sha256": sha256(payload).hexdigest(),
        "canvas_units": viewbox,
        "text_metric_methods": ["Fixed conservative text-box widths with native left/center/right alignment; no font-measurement dependency"],
        **counts,
        "limitations": ["Glyph internals and decorative paths are independent SVG image cells; text, rectangles and routes are native editable cells.",
                        "Text requests Noto Sans with approximate baseline placement; browser font rendering can require minor adjustment after import.",
                        "Connector terminal attachment is inferred from nearby glyph bounds; publication SVG/PDF remains the authoritative visual.",
                        "XML structure and geometry were checked programmatically; interactive draw.io import was not exercised."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", nargs="?", type=Path, default=PAPER/"figures/architecture.svg")
    parser.add_argument("output", nargs="?", type=Path, default=PAPER/"figures/architecture.drawio")
    args = parser.parse_args()
    print(json.dumps(export_drawio(args.svg, args.output), indent=2))


if __name__ == "__main__":
    main()
