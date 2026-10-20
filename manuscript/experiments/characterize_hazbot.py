#!/usr/bin/env python3
"""Reproducible, source-derived HazBot geometry and interface analysis.

Uses only Python's standard library. Original runtime modules are NEVER imported:
only audited, isolated AST bodies for a string-to-direction branch and a pure
angle-mapping function are executed. No hardware, ROS, networking, model
inference, physical timing, collision checking, or material identification occurs.
The workspace is an ideal URDF WRIST-ORIGIN envelope, not a safe grasp workspace.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import random
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "manuscript/data"
SOURCE_PATHS = {
    "urdf": "scripts/robot.urdf",
    "motor_gateway": "motor_control/motor_server.py",
    "motor_firmware": "motor_control/soccer_bot_motor_driver.ino",
    "arm_gateway": "scripts/arm_server.py",
    "arm_firmware": "scripts/arduino_arm_controller/arduino_arm_controller.ino",
    "arm_firmware_alternative": "scripts/arduino_arm_controller.ino",
    "vision": "scripts/detect_live_picamera2.py",
    "lidar_bridge": "scripts/lidar_bridge.py",
    "raw_lidar": "scripts/raw_lidar_publisher.py",
    "generator": "manuscript/experiments/characterize_hazbot.py",
}
GRID_POINTS_PER_JOINT = 41
RANDOM_VALIDATION_POSES = 1000
RANDOM_SEED = 20261021
ARM_JOINTS = ("base_joint", "shoulder_joint", "elbow_joint")
CHECKS: list[dict] = []


def require(name, condition, detail=None):
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    CHECKS.append({"name": name, "passed": True, "detail": detail})


def read_source(key):
    return (ROOT / SOURCE_PATHS[key]).read_text(encoding="utf-8")


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def source_bindings():
    return {
        key: {"path": rel, "sha256": digest_bytes((ROOT / rel).read_bytes())}
        for key, rel in SOURCE_PATHS.items()
    }


def vector(text):
    return tuple(float(value) for value in text.split())


def identity():
    return [[float(i == j) for j in range(4)] for i in range(4)]


def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def translation(xyz):
    result = identity()
    for index, value in enumerate(xyz):
        result[index][3] = value
    return result


def axis_rotation(axis, angle):
    """Rodrigues rotation, independent of the special arm analytic formula."""
    magnitude = math.sqrt(sum(value * value for value in axis))
    x, y, z = (value / magnitude for value in axis)
    c, s, t = math.cos(angle), math.sin(angle), 1.0 - math.cos(angle)
    result = identity()
    result[:3] = [
        [t*x*x+c, t*x*y-s*z, t*x*z+s*y, 0.0],
        [t*x*y+s*z, t*y*y+c, t*y*z-s*x, 0.0],
        [t*x*z-s*y, t*y*z+s*x, t*z*z+c, 0.0],
    ]
    return result


def rpy_rotation(rpy):
    roll, pitch, yaw = rpy
    return multiply(axis_rotation((0, 0, 1), yaw),
                    multiply(axis_rotation((0, 1, 0), pitch),
                             axis_rotation((1, 0, 0), roll)))


def read_urdf():
    robot = ET.fromstring(read_source("urdf"))
    joints = {}
    for element in robot.findall("joint"):
        origin = element.find("origin")
        axis = element.find("axis")
        limit = element.find("limit")
        joint = {
            "name": element.attrib["name"], "type": element.attrib["type"],
            "parent": element.find("parent").attrib["link"],
            "child": element.find("child").attrib["link"],
            "xyz": vector(origin.attrib.get("xyz", "0 0 0")) if origin is not None else (0., 0., 0.),
            "rpy": vector(origin.attrib.get("rpy", "0 0 0")) if origin is not None else (0., 0., 0.),
            "axis": vector(axis.attrib.get("xyz", "1 0 0")) if axis is not None else None,
        }
        if limit is not None:
            joint["limits"] = (float(limit.attrib["lower"]), float(limit.attrib["upper"]))
        joints[joint["name"]] = joint
    child_to_joint = {joint["child"]: joint for joint in joints.values()}
    chain = []
    child = "arm_wrist_link"
    while child != "base_link":
        joint = child_to_joint[child]
        chain.insert(0, joint)
        child = joint["parent"]
    return robot, joints, chain


def general_fk(chain, angles):
    transform = identity()
    for joint in chain:
        transform = multiply(transform, multiply(translation(joint["xyz"]), rpy_rotation(joint["rpy"])))
        if joint["type"] in ("continuous", "revolute"):
            transform = multiply(transform, axis_rotation(joint["axis"], angles[joint["name"]]))
        elif joint["type"] == "prismatic":
            transform = multiply(transform, translation(tuple(angles[joint["name"]] * v for v in joint["axis"])))
        elif joint["type"] != "fixed":
            raise ValueError(f"Unsupported joint type {joint['type']}")
    return tuple(transform[index][3] for index in range(3))


def analytic_parameters(joints, chain):
    expected_names = ["base_to_chassis", "chassis_to_arm_mount", "base_joint",
                      "shoulder_joint", "elbow_joint", "wrist_joint"]
    require("exact modeled chain recognized", [j["name"] for j in chain] == expected_names)
    require("chain origins have zero rpy", all(j["rpy"] == (0., 0., 0.) for j in chain))
    require("positioning axes match yaw-pitch-pitch",
            [joints[name]["axis"] for name in ARM_JOINTS] == [(0., 0., 1.), (0., 1., 0.), (0., 1., 0.)])
    require("wrist is fixed", joints["wrist_joint"]["type"] == "fixed")
    require("upper link is initially vertical", joints["elbow_joint"]["xyz"][:2] == (0., 0.))
    require("forearm initially points forward", joints["wrist_joint"]["xyz"][1:] == (0., 0.))
    require("yaw to shoulder has only axial offset", joints["shoulder_joint"]["xyz"][:2] == (0., 0.))
    origin = tuple(sum(joints[name]["xyz"][i] for name in expected_names[:4]) for i in range(3))
    return {"shoulder_origin_m": origin,
            "upper_link_length_m": joints["elbow_joint"]["xyz"][2],
            "forearm_length_m": joints["wrist_joint"]["xyz"][0]}


def analytic_fk(qb, qs, qe, geometry):
    l1, l2 = geometry["upper_link_length_m"], geometry["forearm_length_m"]
    x0, y0, z0 = geometry["shoulder_origin_m"]
    radial_signed = l1 * math.sin(qs) + l2 * math.cos(qs + qe)
    return (x0 + radial_signed * math.cos(qb),
            y0 + radial_signed * math.sin(qb),
            z0 + l1 * math.cos(qs) - l2 * math.sin(qs + qe))


def linspace(lower, upper, count):
    return [lower + (upper - lower) * i / (count - 1) for i in range(count)]


def geometric_characterization():
    robot, joints, chain = read_urdf()
    geometry = analytic_parameters(joints, chain)
    bounds = {name: joints[name]["limits"] for name in ARM_JOINTS}
    rng = random.Random(RANDOM_SEED)
    poses = [tuple(rng.uniform(*bounds[name]) for name in ARM_JOINTS)
             for _ in range(RANDOM_VALIDATION_POSES)]
    special = [(0., 0., 0.), (0., 0., -math.pi/2),
               (0., 0., math.pi/2), (0., math.pi/2, -math.pi/2),
               (math.pi/2, math.pi/2, -math.pi/2)]
    special.extend(itertools.product(*(bounds[name] for name in ARM_JOINTS)))
    poses.extend(special)
    require("validation angles inside declared bounds",
            all(bounds[name][0] <= q <= bounds[name][1]
                for pose in poses for name, q in zip(ARM_JOINTS, pose)))
    errors = []
    for pose in poses:
        expected = general_fk(chain, dict(zip(ARM_JOINTS, pose)))
        actual = analytic_fk(*pose, geometry)
        errors.append(math.sqrt(sum((a - b)**2 for a, b in zip(expected, actual))))
    require("analytic FK agrees with independent homogeneous chain", max(errors) < 1e-12,
            {"poses": len(poses), "max_error_m": max(errors)})
    x0, y0, z0 = geometry["shoulder_origin_m"]
    l1, l2 = geometry["upper_link_length_m"], geometry["forearm_length_m"]
    upper_bound = l1 + l2
    extended = analytic_fk(0., 0., -math.pi/2, geometry)
    folded = analytic_fk(0., 0., math.pi/2, geometry)
    require("exact collinear pose attains link-sum bound",
            abs(math.dist(extended, (x0, y0, z0)) - upper_bound) < 1e-12)
    require("folded pose attains link-difference bound",
            abs(math.dist(folded, (x0, y0, z0)) - abs(l1-l2)) < 1e-12)
    monotone_q = linspace(-math.pi/2, math.pi/2, 401)
    reach = [math.dist(analytic_fk(0., 0., qe, geometry), (x0,y0,z0)) for qe in monotone_q]
    require("reach decreases monotonically from extended to folded",
            all(right <= left + 1e-12 for left, right in zip(reach, reach[1:])),
            {"elbow_interval_rad": [-math.pi/2, math.pi/2], "samples": len(reach)})
    samples = []
    grids = [linspace(*bounds[name], GRID_POINTS_PER_JOINT) for name in ARM_JOINTS]
    for index, (qb, qs, qe) in enumerate(itertools.product(*grids)):
        x, y, z = analytic_fk(qb, qs, qe, geometry)
        samples.append({"pose_id": index, "base_rad": qb, "shoulder_rad": qs,
                        "elbow_rad": qe, "wrist_x_m": x, "wrist_y_m": y,
                        "wrist_z_m": z, "radius_from_shoulder_axis_m": math.hypot(x-x0,y-y0),
                        "distance_from_shoulder_origin_m": math.dist((x,y,z),(x0,y0,z0)),
                        "below_base_ground_plane": int(z < 0.)})
    require("joint grid has declared number of points", len(samples) == GRID_POINTS_PER_JOINT**3)
    require("every grid wrist lies within shoulder link-sum bound",
            max(p["distance_from_shoulder_origin_m"] for p in samples) <= upper_bound + 1e-12)
    require("every grid wrist satisfies link-difference lower bound",
            min(p["distance_from_shoulder_origin_m"] for p in samples) >= abs(l1-l2) - 1e-12)
    # Radial distance and height must be yaw-invariant at identical shoulder/elbow angles.
    yaw_stride = GRID_POINTS_PER_JOINT**2
    yaw_error = max(abs(samples[i][key] - samples[i % yaw_stride][key])
                    for i in range(len(samples)) for key in ("wrist_z_m", "distance_from_shoulder_origin_m"))
    require("yaw preserves wrist height and shoulder distance", yaw_error < 1e-12,
            {"maximum_difference_m": yaw_error})
    slices = []
    # Slabs, not exact planar cross sections. Counts include repeated yaw angles.
    for center in (0., .05, .10, .15, .20, .25, .30, .35):
        half_width = .01
        selected = [p for p in samples if center-half_width <= p["wrist_z_m"] <= center+half_width]
        slices.append({"height_center_m": center, "half_width_m": half_width,
                       "sample_count": len(selected),
                       "minimum_radius_from_shoulder_axis_m": min((p["radius_from_shoulder_axis_m"] for p in selected), default=None),
                       "maximum_radius_from_shoulder_axis_m": max((p["radius_from_shoulder_axis_m"] for p in selected), default=None)})
    extrema = {key: {"min": min(p[key] for p in samples), "max": max(p[key] for p in samples)}
               for key in ("wrist_x_m", "wrist_y_m", "wrist_z_m",
                           "radius_from_shoulder_axis_m", "distance_from_shoulder_origin_m")}
    return {
        "frame": "base_link", "endpoint": "arm_wrist_link origin",
        "geometry": geometry, "joint_limits_rad": bounds,
        "joint_chain": [joint["name"] for joint in chain],
        "grid": {"points_per_joint": GRID_POINTS_PER_JOINT, "total_poses": len(samples),
                 "including_limit_endpoints": True, "extrema_m": extrema,
                 "below_ground_plane_count": sum(p["below_base_ground_plane"] for p in samples),
                 "above_or_on_ground_plane_count": sum(not p["below_base_ground_plane"] for p in samples)},
        "shoulder_to_wrist_link_sum_bound_m": upper_bound,
        "shoulder_to_wrist_link_difference_bound_m": abs(l1-l2),
        "height_slabs": slices,
        "fk_validation": {"random_seed": RANDOM_SEED, "random_poses": RANDOM_VALIDATION_POSES,
                          "special_poses": len(special), "total_poses": len(poses),
                          "maximum_disagreement_m": max(errors)},
        "jaw_joint_origins_from_wrist_m": {
            name: joints[name]["xyz"] for name in ("gripper_left_joint", "gripper_right_joint")},
        "jaw_local_geometry": "Each jaw has 0.06m visual length, 0.025m joint x offset, opposite z rotations. No calibrated grasp TCP is defined.",
        "interpretation": "Ideal geometric wrist-origin envelope; not end-effector contact reach, collision-free workspace, payload, stability, or physical accuracy.",
    }, samples


def extract_motor_branch():
    parsed = ast.parse(read_source("motor_gateway"))
    matches = [node for node in ast.walk(parsed)
               if isinstance(node, ast.If) and isinstance(node.test, ast.Call)
               and isinstance(node.test.func, ast.Attribute)
               and node.test.func.attr == "startswith"
               and node.test.args and isinstance(node.test.args[0], ast.Constant)
               and node.test.args[0].value == "SET:"]
    require("exact SET branch uniquely located", len(matches) == 1)
    branch = matches[0]
    require("isolated SET branch contains no imports/global statements",
            not any(isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal))
                    for statement in branch.body for node in ast.walk(statement)))
    names = {node.id for statement in branch.body for node in ast.walk(statement) if isinstance(node, ast.Name)}
    require("isolated SET branch uses only audited names",
            names <= {"line", "vals", "l", "r", "int", "send_to_arduino", "Exception", "err", "print"}, sorted(names))
    emitted = []
    namespace = {"send_to_arduino": emitted.append, "print": lambda *args, **kwargs: None}
    fn = ast.FunctionDef(name="isolated_source_set", args=ast.arguments(
        posonlyargs=[], args=[ast.arg(arg="line")], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=branch.body, decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    exec(compile(module, SOURCE_PATHS["motor_gateway"], "exec"), namespace)
    def mapping(left, right):
        emitted.clear()
        namespace["isolated_source_set"](f"SET:{left},{right}")
        if len(emitted) > 1:
            raise AssertionError("Multiple commands emitted for one SET pair")
        return emitted[0] if emitted else None
    return mapping, {"path": SOURCE_PATHS["motor_gateway"], "first_line": branch.lineno,
                     "last_line": branch.body[-1].end_lineno,
                     "method": "AST-extracted actual SET branch; transport sender replaced by list append; no runtime module imported"}


def expected_direction(left, right):
    if left == right == 0:
        return "S"
    if left * right == 0:
        return None
    return {(True, True): "F", (False, False): "B",
            (False, True): "L", (True, False): "R"}[(left > 0, right > 0)]


def literal_assignments(source):
    result = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = value
    return result


def firmware_constants(source):
    return {name: int(value) for name, value in re.findall(
        r"const\s+(?:byte|int)\s+([A-Z_]+)\s*=\s*(-?\d+)\s*;", source)}


def protocol_characterization():
    mapping, locator = extract_motor_branch()
    values = (-255, -127, -1, 0, 1, 127, 255)
    rows, small_counts, exhaustive_counts = [], Counter(), Counter()
    for left, right in itertools.product(values, repeat=2):
        output = mapping(left, right)
        small_counts[output or "NO_COMMAND"] += 1
        rows.append({"subsystem": "wheel_SET", "left_input": left, "right_input": right,
                     "joint": "", "logical_angle": "", "hardware_angle": "",
                     "emitted_direction": output or "NO_COMMAND"})
    mismatches = 0
    for left, right in itertools.product(range(-255, 256), repeat=2):
        output = mapping(left, right)
        exhaustive_counts[output or "NO_COMMAND"] += 1
        mismatches += output != expected_direction(left, right)
    require("all signed PWM-magnitude pairs match independent sign partition", mismatches == 0,
            {"evaluated_pairs": 511**2, "mismatches": mismatches})
    require("mixed-zero wheel commands emit no command",
            exhaustive_counts["NO_COMMAND"] == 4*255)
    require("all four nonzero sign quadrants erase magnitudes",
            all(exhaustive_counts[direction] == 255**2 for direction in ("F", "B", "L", "R")))
    require("only all-zero pair emits stop", exhaustive_counts["S"] == 1)

    parsed = ast.parse(read_source("arm_gateway"))
    pure = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name == "to_hw_angle"]
    require("pure arm angle map uniquely located", len(pure) == 1)
    require("arm mapping has no calls beyond pure builtins",
            all(isinstance(node.func, ast.Name) and node.func.id in {"str", "int", "min", "max"}
                or isinstance(node.func, ast.Attribute) and node.func.attr == "upper"
                for node in ast.walk(pure[0]) if isinstance(node, ast.Call)))
    namespace = {}
    exec(compile(ast.Module(body=pure, type_ignores=[]), SOURCE_PATHS["arm_gateway"], "exec"), namespace)
    arm_map = namespace["to_hw_angle"]
    arm_summaries, arm_mismatches = {}, 0
    for joint in ("B", "S", "A", "E", "G"):
        outputs = []
        for value in range(-90, 361):
            output = arm_map(joint, value)
            expected = (min(270, max(90, value)) if joint == "G" else
                        min(180, max(0, 180-value if joint in ("S", "A", "E") else value)))
            arm_mismatches += output != expected
            outputs.append(output)
            rows.append({"subsystem": "arm_angle", "left_input": "", "right_input": "",
                         "joint": joint, "logical_angle": value, "hardware_angle": output,
                         "emitted_direction": ""})
        arm_summaries[joint] = {"tested_inputs": len(outputs), "hardware_min": min(outputs),
                                "hardware_max": max(outputs), "distinct_outputs": len(set(outputs)),
                                "reversed": joint in ("S", "A", "E"),
                                "at_input_0": arm_map(joint, 0), "at_input_180": arm_map(joint, 180)}
    require("isolated arm mapping matches independent clamp model", arm_mismatches == 0,
            {"evaluated_cases": 5*451, "mismatches": arm_mismatches})
    arm_constants = firmware_constants(read_source("arm_firmware"))
    alternative = firmware_constants(read_source("arm_firmware_alternative"))
    pins = {key: arm_constants[key] for key in ("BASE_PIN", "SHOULDER_PIN", "ALBO_PIN", "GRIPPER_PIN")}
    require("four distinct arm servo pins", len(set(pins.values())) == 4)
    require("primary firmware clamp ranges agree with gateway",
            all(arm_constants[f"{channel}_MIN"] == 0 and arm_constants[f"{channel}_MAX"] == 180
                for channel in ("BASE", "SHOULDER", "ALBO"))
            and arm_constants["GRIPPER_MIN"] == 90 and arm_constants["GRIPPER_MAX"] == 270)
    return {
        "wheel": {"locator": locator, "small_input_values": values,
                  "small_grid_cases": len(values)**2, "small_grid_output_counts": dict(sorted(small_counts.items())),
                  "exhaustive_input_interval_each_wheel": [-255,255],
                  "exhaustive_cases": 511**2,
                  "exhaustive_output_counts": dict(sorted(exhaustive_counts.items())),
                  "interpretation": "Gateway sign-to-direction semantics; magnitudes discarded; mixed-zero pairs silently emit no new command. No motor displacement, speed, or physical stopping was measured."},
        "arm": {"locator": {"path": SOURCE_PATHS["arm_gateway"], "first_line": pure[0].lineno,
                            "last_line": pure[0].end_lineno},
                "input_interval": [-90,360], "tested_aliases": ["B","S","A","E","G"],
                "total_mapping_cases": 5*451, "channels": arm_summaries, "servo_pins": pins,
                "primary_firmware_constants": arm_constants,
                "alternative_firmware_gripper_constants": {name: alternative[name] for name in (
                    "GRIPPER_MIN","GRIPPER_MAX","GRIPPER_MIN_US","GRIPPER_MAX_US")},
                "interpretation": "Three positioning channels plus gripper; E aliases elbow A. Command units and clamps are software conventions, not calibrated mechanical joint angle measurements."},
    }, rows


def vision_and_lidar_schema():
    vision = literal_assignments(read_source("vision"))
    require("two visual classes extracted from source literal", len(vision["CLASS_NAMES"]) == 2)
    raw = literal_assignments(read_source("raw_lidar"))
    bridge = literal_assignments(read_source("lidar_bridge"))
    return {
        "vision": {"class_names": vision["CLASS_NAMES"], "class_count": len(vision["CLASS_NAMES"]),
                   "confidence_threshold": vision["CONF_THRESHOLD"], "nms_iou_threshold": vision["IOU_THRESHOLD"],
                   "cpu_threads": vision["NUM_THREADS"],
                   "model_description_from_source": "INT8 YOLOv8 TFLite; model weights external and not evaluated",
                   "hazard_class_validation": "none in inspected evidence"},
        "lidar": {"raw_parser_bins": raw["NUM_BINS"], "nominal_bin_width_degrees": 360/raw["NUM_BINS"],
                  "bridge_serial_baud": bridge["baud"],
                  "interface": "sensor controller and CP2102 USB-UART interface to Raspberry Pi; independent of drive/arm Arduino",
                  "interpretation": "Configured serialization/angular discretization, not measured resolution or localization accuracy."},
    }


def csv_bytes(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: f"{value:.12g}" if isinstance(value, float) else value
                         for key,value in row.items()})
    return stream.getvalue().encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    geometry, workspace_rows = geometric_characterization()
    protocols, protocol_rows = protocol_characterization()
    schema = vision_and_lidar_schema()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    datasets = {"hazbot_workspace.csv": csv_bytes(workspace_rows),
                "hazbot_protocol.csv": csv_bytes(protocol_rows),
                "hazbot_height_slabs.csv": csv_bytes(geometry["height_slabs"])}
    for name, data in datasets.items():
        (output/name).write_bytes(data)
    result = {
        "analysis": "Source-derived HazBot geometric and interface characterization",
        "date": "2026-10-21", "dependencies": "Python standard library only",
        "evidence_type": "Analytical geometry and isolated source-code execution; no hardware, trajectory simulation, model inference, hazard tests or physical measurements",
        "source_bindings": source_bindings(), "workspace": geometry, "protocols": protocols,
        "schemas": schema,
        "validation": {"passed": True, "check_count": len(CHECKS), "checks": CHECKS},
        "datasets": {name: {"sha256": digest_bytes(data), "bytes": len(data)} for name,data in datasets.items()},
        "limitations": [
            "URDF geometry is uncalibrated source model geometry, not physical metrology.",
            "Endpoint is fixed wrist origin. No calibrated grasp TCP is defined; jaw geometry is not grasp reach.",
            "No collision, torque, payload, chassis tipping, servo dynamics, cable or contact constraints included.",
            "Below-ground samples retained and flagged to expose model-only envelope limits.",
            "Grid counts and extrema are sample-dependent, not uniform Cartesian volumes or exact continuous workspace boundaries.",
            "Protocol outputs describe code semantics, not physical wheel or arm performance.",
            "No hazardous material was handled or recognized by this characterization.",
        ],
    }
    (output/"hazbot_characterization.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    extrema = geometry["grid"]["extrema_m"]
    print(f"Wrist-origin grid: {len(workspace_rows):,} poses; below modeled ground: {geometry['grid']['below_ground_plane_count']:,}")
    print(f"Wrist z sample range: {extrema['wrist_z_m']['min']:.6f} to {extrema['wrist_z_m']['max']:.6f} m; link-sum bound {geometry['shoulder_to_wrist_link_sum_bound_m']:.3f} m")
    print(f"Independent FK validation: {geometry['fk_validation']['total_poses']} poses, max disagreement {geometry['fk_validation']['maximum_disagreement_m']:.3g} m")
    print(f"Wheel mappings: {protocols['wheel']['exhaustive_cases']:,}; no-command mixed-zero pairs: {protocols['wheel']['exhaustive_output_counts']['NO_COMMAND']:,}")
    print(f"Arm mapping cases: {protocols['arm']['total_mapping_cases']:,}; classes: {schema['vision']['class_count']}; checks passed: {len(CHECKS)}")


if __name__ == "__main__":
    main()
