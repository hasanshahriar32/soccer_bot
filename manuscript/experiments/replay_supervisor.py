#!/usr/bin/env python3
"""Deterministic command-level replay of source policy and proposed supervisors.

No ROS installation, network connection, robot motion, or external dependency is
used.  The source class is AST-extracted and its real callbacks/control_loop are
executed with in-memory message/publisher/time doubles.  Its constructor and
motor transport are never called.  See ../research/evaluation_protocol.md.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/soccer_navigation/soccer_navigation/autonomous_ball_chaser_node.py"
OUT = ROOT / "manuscript/data"
GENERATED = ROOT / "manuscript/generated"
HZ = 20
START_TIME = 100.0
STOP_DISTANCE = 0.3048
BALL_TTL = 1.0
DEFAULT_SCAN_TTL = 0.25
POLICIES = ("source", "freshness_only", "full_supervisor")


class Twist:
    def __init__(self):
        self.linear = SimpleNamespace(x=0.0, y=0.0, z=0.0)
        self.angular = SimpleNamespace(x=0.0, y=0.0, z=0.0)


class Publisher:
    def __init__(self):
        self.last = None

    def publish(self, msg):
        self.last = (float(msg.linear.x), float(msg.angular.z))


class Logger:
    def info(self, *args, **kwargs):
        pass


def load_source_class():
    """Execute original function bodies; do not import ROS or socket modules."""
    parsed = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    retained = [
        node for node in parsed.body
        if (isinstance(node, ast.ClassDef) and node.name == "ActiveDrive12InchController")
        or (isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "STOP_DISTANCE_METERS"
                    for t in node.targets))
    ]
    assert len(retained) == 2, "Expected source constant and controller class"
    clock = SimpleNamespace(now=START_TIME)
    namespace = {
        "Node": object,
        "Twist": Twist,
        "rclpy": SimpleNamespace(ok=lambda: True),
        "time": SimpleNamespace(time=lambda: clock.now),
    }
    exec(compile(ast.Module(body=retained, type_ignores=[]), str(SOURCE), "exec"), namespace)
    assert namespace["STOP_DISTANCE_METERS"] == STOP_DISTANCE
    return namespace["ActiveDrive12InchController"], clock


SourceClass, CLOCK = load_source_class()


class ReplayController:
    def __init__(self, policy, scan_ttl):
        self.policy = policy
        self.scan_ttl = scan_ttl
        # Bypass __init__: in particular, never call connect_pi_motors().
        self.node = SourceClass.__new__(SourceClass)
        self.node.ball_distance_m = 99.0
        self.node.ball_pixel_offset = 0.0
        self.node.ball_lateral_m = 0.0
        self.node.last_ball_time = 0.0
        self.node.lidar_min_dist_m = 99.0
        self.node.last_command_sent = None
        self.node.pub_cmd_vel = Publisher()
        self.node.get_logger = lambda: Logger()
        self.node.send_motor_pwm = lambda left, right, raw: None
        self.last_scan_tick = None
        self.scan_valid = False
        self.scan_min = None
        self.last_ball_kind = "unobserved"

    def ball(self, tick, values):
        msg = SimpleNamespace(x=values[0], y=values[1], z=values[2])
        self.node.ball_callback(msg)
        # Schema is the repository metric tracker contract, not a unit detector.
        if values == (-1.0, -1.0, -1.0):
            self.last_ball_kind = "absent"
        elif all(math.isfinite(x) for x in values) and values[0] >= 0 and values[2] > 0:
            self.last_ball_kind = "present"
        else:
            self.last_ball_kind = "malformed"

    def scan(self, tick, values):
        self.node.scan_callback(SimpleNamespace(ranges=values))
        self.last_scan_tick = tick
        valid = [r for r in values if math.isfinite(r) and 0.05 < r < 20.0]
        self.scan_valid = bool(valid)
        self.scan_min = min(valid) if valid else None

    def scan_fresh(self, tick):
        # Tick arithmetic makes the >= deadline exact and reproducible.
        return (self.last_scan_tick is not None
                and 0 <= tick - self.last_scan_tick < self.scan_ttl * HZ - 1e-10)

    def constraints(self, tick):
        reasons = []
        if not self.scan_fresh(tick):
            reasons.append("unknown_or_stale_scan")
        if self.last_scan_tick is not None and not self.scan_valid:
            reasons.append("invalid_scan")
        if self.last_ball_kind == "malformed":
            reasons.append("malformed_ball")
        if self.scan_valid and self.scan_min <= STOP_DISTANCE:
            reasons.append("near_return")
        return reasons

    def command(self, tick):
        self.node.control_loop()
        desired = self.node.pub_cmd_vel.last
        assert desired is not None
        reasons = self.constraints(tick)
        override = "none"
        if self.policy != "source" and "unknown_or_stale_scan" in reasons:
            override = "unknown_or_stale_scan"
        elif self.policy == "full_supervisor":
            for reason in ("invalid_scan", "malformed_ball", "near_return"):
                if reason in reasons:
                    override = reason
                    break
        output = (0.0, 0.0) if override != "none" else desired
        return desired, output, reasons, override


SCENARIOS = (
    ("healthy_centered", "Healthy centered approach"),
    ("healthy_turn_reversal", "Healthy lateral reversal"),
    ("near_obstacle", "Near return and recovery"),
    ("camera_silence", "Camera stops publishing"),
    ("explicit_ball_loss", "Explicit absence messages"),
    ("startup_without_scan", "No scan at startup"),
    ("scan_dropout", "Scan stream interruption"),
    ("all_invalid_scan", "All ranges invalid"),
    ("empty_scan", "Empty scan messages"),
    ("malformed_ball", "Nonfinite ball coordinate"),
    ("combined_fault", "Scan and camera interruption"),
    ("slow_healthy_scan", "Clear scene at 2.5 Hz scan"),
)


def scenario_events(name, tick):
    """Inputs are constructed, not recorded; each trace lasts four seconds."""
    ball = (1.0, 0.0, 1.0) if tick % 4 == 0 else None
    scan = [2.0, 2.5, 3.0, 2.2] if tick % 2 == 0 else None
    world_clear = True
    if name == "healthy_turn_reversal":
        ball = (1.0, 0.2 if tick < 40 else -0.2, 1.1) if tick % 2 == 0 else None
    elif name == "near_obstacle":
        world_clear = not 20 <= tick < 50
        if scan is not None and not world_clear:
            scan = [STOP_DISTANCE if tick < 36 else 0.25, 2.5, 3.0, 2.2]
    elif name == "camera_silence":
        if tick >= 20:
            ball = None
    elif name == "explicit_ball_loss":
        if tick >= 20 and ball is not None:
            ball = (-1.0, -1.0, -1.0)
    elif name == "startup_without_scan":
        if tick < 20:
            scan = None
    elif name == "scan_dropout":
        if 20 <= tick < 60:
            scan = None
    elif name == "all_invalid_scan":
        if 20 <= tick < 60 and scan is not None:
            scan = [float("nan"), float("inf"), -float("inf"), 0.0, 0.05, 20.0]
    elif name == "empty_scan":
        if 20 <= tick < 60 and scan is not None:
            scan = []
    elif name == "malformed_ball":
        if 20 <= tick < 60 and ball is not None:
            ball = ((1.0, float("nan"), 1.0) if tick < 40
                    else (1.0, 0.0, float("inf")))
    elif name == "combined_fault":
        if 20 <= tick < 60:
            scan = None
            ball = None
    elif name == "slow_healthy_scan":
        scan = [2.0, 2.5, 3.0, 2.2] if tick % 8 == 0 else None
    elif name != "healthy_centered":
        raise ValueError(name)
    return ball, scan, world_clear


def serialize_values(values):
    if values is None:
        return "none"
    def scalar(x):
        if math.isnan(x):
            return "NaN"
        if math.isinf(x):
            return "Infinity" if x > 0 else "-Infinity"
        return format(x, ".10g")
    return "[" + ",".join(scalar(x) for x in values) + "]"


def replay(scan_ttl):
    rows = []
    summary = []
    for scenario, label in SCENARIOS:
        controllers = {p: ReplayController(p, scan_ttl) for p in POLICIES}
        counters = {p: dict(ticks=0, motion_ticks=0, forward_ticks=0,
                            constrained_ticks=0, constrained_motion_ticks=0,
                            constrained_forward_ticks=0, override_ticks=0,
                            clear_forward_opportunities=0, clear_forward_held_ticks=0,
                            output_change_ticks=0)
                    for p in POLICIES}
        for tick in range(80):
            CLOCK.now = START_TIME + tick / HZ
            ball, scan, clear = scenario_events(scenario, tick)
            for policy, controller in controllers.items():
                if ball is not None:
                    controller.ball(tick, ball)
                if scan is not None:
                    controller.scan(tick, scan)
                desired, output, reasons, override = controller.command(tick)
                moving = output != (0.0, 0.0)
                forward = output[0] > 0
                opportunity = clear and desired[0] > 0 and controller.last_ball_kind == "present"
                counts = counters[policy]
                counts["ticks"] += 1
                counts["motion_ticks"] += int(moving)
                counts["forward_ticks"] += int(forward)
                counts["constrained_ticks"] += int(bool(reasons))
                counts["constrained_motion_ticks"] += int(bool(reasons) and moving)
                counts["constrained_forward_ticks"] += int(bool(reasons) and forward)
                counts["override_ticks"] += int(override != "none")
                counts["clear_forward_opportunities"] += int(opportunity)
                counts["clear_forward_held_ticks"] += int(opportunity and not forward)
                counts["output_change_ticks"] += int(output != desired)
                rows.append(dict(
                    scenario=scenario, policy=policy, tick=tick,
                    time_s=format(tick / HZ, ".2f"), scan_ttl_s=scan_ttl,
                    ball_input=serialize_values(ball), scan_input=serialize_values(scan),
                    scan_age_s=("unobserved" if controller.last_scan_tick is None
                                else format((tick - controller.last_scan_tick) / HZ, ".2f")),
                    scan_valid=int(controller.scan_valid), ball_kind=controller.last_ball_kind,
                    desired_linear=format(desired[0], ".6f"),
                    desired_angular=format(desired[1], ".6f"),
                    output_linear=format(output[0], ".6f"),
                    output_angular=format(output[1], ".6f"),
                    constraints="|".join(reasons) or "none", override=override,
                    constructed_world_clear=int(clear),
                ))
        for policy in POLICIES:
            summary.append(dict(scenario=scenario, label=label, policy=policy, **counters[policy]))
    return rows, summary


def aggregate(summary):
    totals = {}
    for policy in POLICIES:
        selected = [r for r in summary if r["policy"] == policy]
        totals[policy] = {key: sum(row[key] for row in selected)
                          for key in selected[0] if isinstance(selected[0][key], int)}
    return totals


def check_behavior(rows, summary):
    checks = []
    def require(name, condition):
        assert condition, name
        checks.append({"name": name, "passed": True})
    def select(scenario, policy):
        return [r for r in rows if r["scenario"] == scenario and r["policy"] == policy]
    def metric(scenario, policy, key):
        return next(r[key] for r in summary if r["scenario"] == scenario and r["policy"] == policy)
    boundary = ReplayController("full_supervisor", DEFAULT_SCAN_TTL)
    require("scan_without_receipt_is_not_fresh", not boundary.scan_fresh(0))
    boundary.scan(10, [2.0])
    require("scan_deadline_is_strict_and_future_receipts_are_rejected",
            boundary.scan_fresh(10) and boundary.scan_fresh(14)
            and not boundary.scan_fresh(15) and not boundary.scan_fresh(16)
            and not boundary.scan_fresh(9))
    require("full_supervisor_enforces_declared_contract_on_all_replayed_ticks",
            all(not (r["constraints"] != "none" and
                     (float(r["output_linear"]) != 0 or float(r["output_angular"]) != 0))
                for r in rows if r["policy"] == "full_supervisor"))
    require("healthy_centered_and_reversal_commands_preserved",
            all(metric(s, p, "output_change_ticks") == 0
                for s in ("healthy_centered", "healthy_turn_reversal")
                for p in ("freshness_only", "full_supervisor")))
    require("source_already_stops_at_near_return",
            all(float(r["output_linear"]) == 0 and float(r["output_angular"]) == 0
                for r in select("near_obstacle", "source") if 20 <= r["tick"] < 50))
    require("source_and_supervisor_stop_at_exact_distance_threshold",
            all(float(r["output_linear"]) == 0 and float(r["output_angular"]) == 0
                for p in POLICIES for r in select("near_obstacle", p) if 20 <= r["tick"] < 36))
    require("source_camera_silence_expiry_is_preserved",
            all(float(r["output_linear"]) == 0 and float(r["output_angular"]) == 0.65
                for r in select("camera_silence", "source") if r["tick"] >= 36))
    require("source_explicit_absence_search_is_preserved",
            all(float(r["output_linear"]) == 0 and float(r["output_angular"]) == 0.65
                for r in select("explicit_ball_loss", "full_supervisor") if r["tick"] >= 20))
    require("source_moves_before_first_scan",
            metric("startup_without_scan", "source", "constrained_forward_ticks") > 0)
    require("freshness_only_does_not_detect_fresh_all_invalid_scans",
            metric("all_invalid_scan", "freshness_only", "constrained_forward_ticks") > 0)
    require("freshness_only_does_not_detect_empty_scans",
            metric("empty_scan", "freshness_only", "constrained_forward_ticks") > 0)
    require("source_nonfinite_lateral_coordinate_still_generates_forward_command",
            metric("malformed_ball", "source", "constrained_forward_ticks") > 0)
    require("source_nonfinite_range_still_generates_forward_command",
            all(float(r["output_linear"]) == 0.28
                for r in select("malformed_ball", "source") if 40 <= r["tick"] < 60))
    require("full_supervisor_resumes_after_valid_scan_and_target_recover",
            all(float(r["output_linear"]) == 0.28
                for s in ("scan_dropout", "all_invalid_scan", "empty_scan", "malformed_ball", "combined_fault")
                for r in select(s, "full_supervisor") if r["tick"] >= 60))
    return checks


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_tables(totals, sweep):
    names = {"source": "Source", "freshness_only": "Age only", "full_supervisor": "Age + validity"}
    lines = ["% Generated by experiments/replay_supervisor.py; do not edit.",
             r"\begin{tabular}{lrrr}", r"\toprule",
             r"Policy & $T$ & $F$ & $H$ \\", r"\midrule"]
    for p in POLICIES:
        r = totals[p]
        lines.append(f"{names[p]} & {r['constrained_motion_ticks']} & {r['constrained_forward_ticks']} & {r['clear_forward_held_ticks']} " + r"\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (GENERATED / "replay_summary.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    lines = ["% Generated by experiments/replay_supervisor.py; do not edit.",
             r"\begin{tabular}{rrrr}", r"\toprule",
             r"$\tau_s$ (s) & $T$ & $H_{\rm slow}$ & $D_{\rm gap}$ (s) \\", r"\midrule"]
    for r in sweep:
        lines.append(f"{r['scan_ttl_s']:.2f} & {r['full_constrained_motion_ticks']} & {r['slow_scan_forward_held_ticks']} & {r['dropout_forward_duration_after_last_scan_s']:.2f} " + r"\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (GENERATED / "timeout_sweep.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def provenance():
    try:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                  check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "unavailable"
    files = [SOURCE, Path(__file__).resolve(),
             ROOT / "src/soccer_vision/soccer_vision/ball_tracker_node.py"]
    return {"git_head": revision, "sha256": {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
    }}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Run behavioral checks without writing artifacts")
    args = parser.parse_args()
    rows, summary = replay(DEFAULT_SCAN_TTL)
    checks = check_behavior(rows, summary)
    totals = aggregate(summary)
    sweep = []
    for ttl in (0.10, 0.25, 0.50):
        sweep_rows, sweep_summary = replay(ttl)
        sweep_totals = aggregate(sweep_summary)
        slow = next(r for r in sweep_summary if r["scenario"] == "slow_healthy_scan" and r["policy"] == "full_supervisor")
        dropout_rows = [r for r in sweep_rows if r["scenario"] == "scan_dropout"
                        and r["policy"] == "full_supervisor" and 18 <= r["tick"] < 60]
        active_after_last_scan = sum(float(r["output_linear"]) > 0 for r in dropout_rows)
        sweep.append(dict(scan_ttl_s=ttl,
                          full_constrained_motion_ticks=sweep_totals["full_supervisor"]["constrained_motion_ticks"],
                          slow_scan_forward_held_ticks=slow["clear_forward_held_ticks"],
                          dropout_forward_duration_after_last_scan_s=active_after_last_scan / HZ))
        assert sweep_totals["full_supervisor"]["constrained_motion_ticks"] == 0
    require_order = [r["slow_scan_forward_held_ticks"] for r in sweep]
    assert require_order[0] > require_order[1] > require_order[2]
    checks.append({"name": "timeout_sweep_exposes_clear_scene_holding_tradeoff", "passed": True})
    result = dict(
        experiment="constructed_source_policy_replay_v1",
        interpretation="Command-level constructed replay; no physical robot, sensor accuracy, collision, latency, or deployment probability measurements.",
        source_execution="Original AST-extracted callback and control_loop bodies; constructor and transport bypassed.",
        supervisor_status="Proposed standalone reference, not integrated into runtime repository nodes.",
        settings=dict(control_hz=HZ, ticks_per_scenario=80, scenarios=len(SCENARIOS),
                      scan_ttl_s=DEFAULT_SCAN_TTL, preserved_ball_ttl_s=BALL_TTL,
                      preserved_stop_distance_m=STOP_DISTANCE, source_range_validity_open_interval_m=[0.05, 20.0]),
        provenance=provenance(), aggregate=totals, per_scenario=summary,
        timeout_sweep=sweep, behavioral_checks=checks,
    )
    if not args.check_only:
        OUT.mkdir(parents=True, exist_ok=True)
        GENERATED.mkdir(parents=True, exist_ok=True)
        write_csv(OUT / "replay_trace.csv", rows)
        write_csv(OUT / "replay_summary.csv", summary)
        write_csv(OUT / "timeout_sweep.csv", sweep)
        (OUT / "replay_results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        write_tables(totals, sweep)
    print(json.dumps({"behavioral_checks_passed": len(checks), "aggregate": totals, "timeout_sweep": sweep}, indent=2))


if __name__ == "__main__":
    main()
