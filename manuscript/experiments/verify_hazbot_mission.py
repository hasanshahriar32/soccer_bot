#!/usr/bin/env python3
"""Exhaustive command-admissibility analysis of an abstract HazBot coordinator.

This is a NEW reference model, not the deployed robot controller, a physics
simulation, a sensor simulator, or evidence of real autonomous mission success.
All 12-Boolean observation valuations are enumerated without consistency
pruning. An independent, explicit oracle judges each issued command.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
import csv
import hashlib
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "manuscript/data"
PHASES = ("SEARCH", "APPROACH", "DOCK", "GRASP", "CARRY", "PLACE", "COMPLETE")
FIELDS = ("target_authorized", "target_fresh", "scan_fresh", "scan_usable",
          "route_clear", "arm_stowed", "base_stopped", "wrist_reachable",
          "at_pick_zone", "grip_confirmed", "at_drop_zone", "release_confirmed")
POLICIES = ("full", "no_base_arm_interlock", "no_target_authorization", "no_scan_age")
ACTIONS = ("rotate", "advance", "transport", "reach", "close_gripper",
           "stow_arm", "open_gripper", "stop_base", "hold")
ALPHABET_SIZE = 2**len(FIELDS)
CHECKS = []


def require(name, condition, detail=None):
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    CHECKS.append({"name": name, "passed": True, "detail": detail})


def observation(mask):
    return {name: bool(mask & (1 << index)) for index, name in enumerate(FIELDS)}


def encode(values):
    return sum((1 << index) for index, name in enumerate(FIELDS) if values[name])


def coordinate(phase, obs, policy="full"):
    """Reference transition function; hold inhibits actuation, not phase updates.

    Blocked guards preserve phase. SEARCH acquisition and PLACE completion can
    update the logical phase while also issuing hold (no progressing actuation).
    """
    if phase not in PHASES or policy not in POLICIES:
        raise ValueError((phase, policy))
    target = obs["target_fresh"] and (obs["target_authorized"] or policy == "no_target_authorization")
    scan = obs["scan_usable"] and (obs["scan_fresh"] or policy == "no_scan_age")
    mobile = scan and obs["route_clear"] and (obs["arm_stowed"] or policy == "no_base_arm_interlock")
    stationary = obs["base_stopped"] or policy == "no_base_arm_interlock"
    manipulate = scan and stationary and target and obs["wrist_reachable"]
    if phase == "SEARCH":
        if target:
            return "APPROACH", "hold"
        return phase, "rotate" if mobile else "hold"
    if phase == "APPROACH":
        if target and mobile:
            if obs["at_pick_zone"]:
                return "DOCK", "stop_base"
            return phase, "advance"
        return phase, "hold"
    if phase == "DOCK":
        return ("GRASP", "reach") if manipulate else (phase, "hold")
    if phase == "GRASP":
        if manipulate:
            return ("CARRY", "stow_arm") if obs["grip_confirmed"] else (phase, "close_gripper")
        return phase, "hold"
    if phase == "CARRY":
        if obs["grip_confirmed"]:
            if obs["at_drop_zone"]:
                return "PLACE", "stop_base"
            if mobile:
                return phase, "transport"
        return phase, "hold"
    if phase == "PLACE":
        if stationary and scan and obs["at_drop_zone"]:
            if obs["release_confirmed"]:
                return "COMPLETE", "hold"
            if obs["grip_confirmed"]:
                return phase, "open_gripper"
        return phase, "hold"
    return phase, "hold"


def admissibility_oracle(phase, next_phase, action, obs):
    """Independent explicit obligations; no coordinator guard helper is reused.

    The oracle checks command admission, not every desirable transition guard.
    In particular, controller scan gating of arm operations is conservative;
    scan freshness is an oracle obligation for BASE MOTION only in this model.
    """
    violations = []
    if phase not in PHASES or next_phase not in PHASES:
        violations.append("unknown_phase")
    if action not in ACTIONS:
        return violations + ["unknown_action"]
    if action in ("rotate", "advance", "transport"):
        if not obs["scan_fresh"]:
            violations.append("base_requires_fresh_scan")
        if not obs["scan_usable"]:
            violations.append("base_requires_usable_scan")
        if not obs["route_clear"]:
            violations.append("base_requires_clear_route")
        if not obs["arm_stowed"]:
            violations.append("base_requires_stowed_arm")
    if action == "advance":
        if not obs["target_authorized"]:
            violations.append("advance_requires_authorized_target")
        if not obs["target_fresh"]:
            violations.append("advance_requires_fresh_target")
    if action in ("reach", "close_gripper", "stow_arm", "open_gripper"):
        if not obs["base_stopped"]:
            violations.append("arm_requires_stopped_base")
    if action in ("reach", "close_gripper"):
        if not obs["target_authorized"]:
            violations.append("grasp_requires_authorized_target")
        if not obs["target_fresh"]:
            violations.append("grasp_requires_fresh_target")
        if not obs["wrist_reachable"]:
            violations.append("grasp_requires_wrist_reachable")
    if action == "transport" and not obs["grip_confirmed"]:
        violations.append("transport_requires_confirmed_grip")
    if action == "open_gripper":
        if not obs["at_drop_zone"]:
            violations.append("release_requires_drop_zone")
        if not obs["grip_confirmed"]:
            violations.append("release_requires_confirmed_grip")
    # Command-to-phase contracts are independently stated rather than inferred
    # from whichever transition the coordinator produced.
    if action == "rotate" and (phase != "SEARCH" or next_phase != "SEARCH"):
        violations.append("rotate_phase_contract")
    if action == "advance" and (phase != "APPROACH" or next_phase != "APPROACH"):
        violations.append("advance_phase_contract")
    if action == "transport" and (phase != "CARRY" or next_phase != "CARRY"):
        violations.append("transport_phase_contract")
    if action == "reach" and (phase != "DOCK" or next_phase != "GRASP"):
        violations.append("reach_phase_contract")
    if action == "close_gripper" and (phase != "GRASP" or next_phase != "GRASP"):
        violations.append("close_phase_contract")
    if action == "stow_arm" and (phase != "GRASP" or next_phase != "CARRY"):
        violations.append("stow_phase_contract")
    if action == "open_gripper" and (phase != "PLACE" or next_phase != "PLACE"):
        violations.append("open_phase_contract")
    if phase == "COMPLETE" and (next_phase != "COMPLETE" or action != "hold"):
        violations.append("complete_absorbing_contract")
    return violations


def check_oracle_semantics():
    # Hand-specified positive/negative probes, independent of coordinate().
    healthy = {name: True for name in FIELDS}
    probes = [
        ("SEARCH", "SEARCH", "rotate", "scan_fresh", "base_requires_fresh_scan"),
        ("SEARCH", "SEARCH", "rotate", "scan_usable", "base_requires_usable_scan"),
        ("SEARCH", "SEARCH", "rotate", "route_clear", "base_requires_clear_route"),
        ("SEARCH", "SEARCH", "rotate", "arm_stowed", "base_requires_stowed_arm"),
        ("APPROACH", "APPROACH", "advance", "target_authorized", "advance_requires_authorized_target"),
        ("APPROACH", "APPROACH", "advance", "target_fresh", "advance_requires_fresh_target"),
        ("DOCK", "GRASP", "reach", "base_stopped", "arm_requires_stopped_base"),
        ("DOCK", "GRASP", "reach", "wrist_reachable", "grasp_requires_wrist_reachable"),
        ("GRASP", "GRASP", "close_gripper", "target_authorized", "grasp_requires_authorized_target"),
        ("GRASP", "GRASP", "close_gripper", "target_fresh", "grasp_requires_fresh_target"),
        ("GRASP", "CARRY", "stow_arm", "base_stopped", "arm_requires_stopped_base"),
        ("CARRY", "CARRY", "transport", "grip_confirmed", "transport_requires_confirmed_grip"),
        ("PLACE", "PLACE", "open_gripper", "at_drop_zone", "release_requires_drop_zone"),
        ("PLACE", "PLACE", "open_gripper", "grip_confirmed", "release_requires_confirmed_grip"),
        ("PLACE", "PLACE", "open_gripper", "base_stopped", "arm_requires_stopped_base"),
    ]
    for phase, next_phase, action, flag, obligation in probes:
        require(f"oracle admits positive {action}/{flag}",
                not admissibility_oracle(phase, next_phase, action, healthy))
        bad = dict(healthy, **{flag: False})
        require(f"oracle rejects missing {flag} for {action}",
                obligation in admissibility_oracle(phase, next_phase, action, bad))
    require("oracle permits stop with all observations false",
            not admissibility_oracle("APPROACH", "DOCK", "stop_base", observation(0)))
    require("oracle permits hold with all observations false",
            not admissibility_oracle("SEARCH", "SEARCH", "hold", observation(0)))
    require("oracle rejects unknown command",
            "unknown_action" in admissibility_oracle("SEARCH", "SEARCH", "invented", healthy))
    require("oracle rejects incorrect command phase",
            "reach_phase_contract" in admissibility_oracle("SEARCH", "SEARCH", "reach", healthy))
    return len(probes)


def exhaustive_policy(policy):
    edges = {}
    phase_results = {}
    violation_total = 0
    obligations = Counter()
    first_by_phase = {}
    for phase in PHASES:
        phase_edges = []
        action_counts, next_counts, violation_action_counts = Counter(), Counter(), Counter()
        invalid = 0
        for mask in range(ALPHABET_SIZE):
            obs = observation(mask)
            next_phase, action = coordinate(phase, obs, policy)
            violations = admissibility_oracle(phase, next_phase, action, obs)
            phase_edges.append((mask, next_phase, action, violations))
            action_counts[action] += 1
            next_counts[next_phase] += 1
            if violations:
                invalid += 1
                violation_action_counts[action] += 1
                obligations.update(violations)
                first_by_phase.setdefault(phase, (mask, next_phase, action, violations))
        edges[phase] = phase_edges
        phase_results[phase] = {"cases": len(phase_edges), "violating_cases": invalid,
                                "action_counts": dict(sorted(action_counts.items())),
                                "next_phase_counts": dict(sorted(next_counts.items())),
                                "violating_action_counts": dict(sorted(violation_action_counts.items()))}
        violation_total += invalid
    require(f"{policy}: complete phase/valuation cardinality",
            sum(len(v) for v in edges.values()) == len(PHASES)*ALPHABET_SIZE)
    require(f"{policy}: every input retained once per phase",
            all([edge[0] for edge in edges[phase]] == list(range(ALPHABET_SIZE)) for phase in PHASES))
    require(f"{policy}: actions belong to defined alphabet",
            all(edge[2] in ACTIONS for phase_edges in edges.values() for edge in phase_edges))
    return {"cases": len(PHASES)*ALPHABET_SIZE, "violating_cases": violation_total,
            "admissible_cases": len(PHASES)*ALPHABET_SIZE - violation_total,
            "violation_obligation_counts": dict(sorted(obligations.items())),
            "phases": phase_results}, edges, first_by_phase


def edge_record(policy, phase, edge, step):
    mask, next_phase, action, violations = edge
    return {"step": step, "policy": policy, "phase_before": phase,
            "observation_mask": mask, "observations": observation(mask),
            "action": action, "phase_after": next_phase,
            "violations": list(violations)}


def phase_bfs(policy, edges):
    """Explore all outgoing valuation edges from every reached phase, unpruned."""
    depth, parent = {"SEARCH": 0}, {}
    pending = deque(["SEARCH"])
    examined = 0
    while pending:
        phase = pending.popleft()
        for edge in edges[phase]:
            examined += 1
            destination = edge[1]
            if destination not in depth:
                depth[destination] = depth[phase] + 1
                parent[destination] = (phase, edge)
                pending.append(destination)
    graph = []
    for phase in PHASES:
        by_destination = Counter(edge[1] for edge in edges[phase])
        for destination, count in sorted(by_destination.items()):
            graph.append({"source": phase, "destination": destination, "valuation_edges": count})
    require(f"{policy}: all seven phases reachable", set(depth) == set(PHASES))
    require(f"{policy}: BFS examines all reachable valuation edges",
            examined == len(PHASES)*ALPHABET_SIZE)
    require(f"{policy}: shortest completion depth six", depth["COMPLETE"] == 6)
    require(f"{policy}: complete state absorbing",
            all(edge[1] == "COMPLETE" and edge[2] == "hold" for edge in edges["COMPLETE"]))
    return {"initial_phase": "SEARCH", "reachable_phases": [p for p in PHASES if p in depth],
            "shortest_depth": depth, "maximum_shortest_depth": max(depth.values()),
            "examined_valuation_edges": examined, "unique_phase_edges": len(graph),
            "phase_edges": graph, "pruning": "none; all 4096 valuations retained at every reached phase"}, parent


def shortest_counterexample(policy, edges, first_by_phase, graph, parents):
    if not first_by_phase:
        return None
    # Deterministic tie break: shortest phase depth, declared phase order, mask.
    phase = min(first_by_phase, key=lambda p: (graph["shortest_depth"][p], PHASES.index(p), first_by_phase[p][0]))
    prefix = []
    current = phase
    while current != "SEARCH":
        previous, edge = parents[current]
        prefix.append((previous, edge))
        current = previous
    prefix.reverse()
    prefix.append((phase, first_by_phase[phase]))
    trace = [edge_record(policy, p, edge, index+1) for index,(p,edge) in enumerate(prefix)]
    minimum_length = min(graph["shortest_depth"][p]+1 for p in first_by_phase)
    require(f"{policy}: counterexample has shortest observation-prefix length", len(trace) == minimum_length)
    require(f"{policy}: counterexample starts at SEARCH", trace[0]["phase_before"] == "SEARCH")
    require(f"{policy}: counterexample final command violates oracle", bool(trace[-1]["violations"]))
    require(f"{policy}: no earlier command in chosen shortest trace violates oracle",
            all(not step["violations"] for step in trace[:-1]))
    actual_phase = "SEARCH"
    for step in trace:
        next_phase, action = coordinate(actual_phase, step["observations"], policy)
        require(f"{policy}: counterexample step {step['step']} replays exactly",
                (actual_phase, next_phase, action) == (step["phase_before"], step["phase_after"], step["action"]))
        actual_phase = next_phase
    return {"minimum_observation_prefix_length": minimum_length,
            "first_violating_phase": phase, "trace": trace}


def nominal_mission():
    baseline = {name: True for name in FIELDS}
    baseline.update(at_pick_zone=False, at_drop_zone=False, grip_confirmed=False,
                    release_confirmed=False)
    specifications = [
        ("Search without an authorized target", {"target_authorized":False,"target_fresh":False}, "SEARCH", "rotate"),
        ("Acquire a fresh authorized surrogate target", {}, "APPROACH", "hold"),
        ("Approach with clear route and stowed arm", {}, "APPROACH", "advance"),
        ("Reach pick zone and request base stop", {"at_pick_zone":True}, "DOCK", "stop_base"),
        ("Stationary, reachable target permits arm reach", {"at_pick_zone":True}, "GRASP", "reach"),
        ("Close gripper while base is stopped", {"at_pick_zone":True,"arm_stowed":False}, "GRASP", "close_gripper"),
        ("Confirmed grip permits stow request", {"grip_confirmed":True,"arm_stowed":False}, "CARRY", "stow_arm"),
        ("Confirmed stow and clear route permit transport", {"grip_confirmed":True}, "CARRY", "transport"),
        ("Reach drop zone and request base stop", {"grip_confirmed":True,"at_drop_zone":True}, "PLACE", "stop_base"),
        ("Stationary at drop zone permits release request", {"grip_confirmed":True,"at_drop_zone":True,"arm_stowed":False}, "PLACE", "open_gripper"),
        ("Observed release completes reference sequence", {"at_drop_zone":True,"release_confirmed":True}, "COMPLETE", "hold"),
    ]
    trace, phase = [], "SEARCH"
    for index,(description, changes, expected_phase, expected_action) in enumerate(specifications):
        obs = dict(baseline, **changes)
        next_phase, action = coordinate(phase, obs)
        violations = admissibility_oracle(phase, next_phase, action, obs)
        require(f"nominal step {index+1}: expected transition/action",
                (next_phase, action) == (expected_phase, expected_action))
        require(f"nominal step {index+1}: independently admissible", not violations)
        record = edge_record("full", phase, (encode(obs), next_phase, action, violations), index+1)
        record["description"] = description
        trace.append(record)
        phase = next_phase
    require("nominal reference sequence reaches COMPLETE", phase == "COMPLETE")
    require("nominal sequence covers all action types", {step["action"] for step in trace} == set(ACTIONS))
    return {"steps": len(trace), "final_phase": phase, "trace": trace,
            "interpretation": "Hand-constructed Boolean witness of reference-model completion, not measured task success or a simulated physical mission."}


def serialize_csv(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def render_tex_summary(policies, counterexamples, nominal):
    """Keep the paper's summary and table bound to computed result values."""
    full = policies["full"]
    graph = full["reachability"]
    interlock, authorization, scan = (policies[name]["violating_cases"] for name in POLICIES[1:])
    prefixes = [counterexamples[name]["minimum_observation_prefix_length"] for name in POLICIES[1:]]
    paragraph = (
        f"The full reference coordinator admits {full['violating_cases']:,} contract-violating commands among "
        f"{full['cases']:,} phase--observation pairs. All {len(graph['reachable_phases'])} phases are reachable, "
        f"with {graph['unique_phase_edges']} unique phase edges (including self-loops) and a shortest "
        f"completion depth of {graph['shortest_depth']['COMPLETE']} transitions. A separate "
        f"{nominal['steps']}-step nominal witness exercises all {len(ACTIONS)} action types and reaches COMPLETE.\n\n"
        f"Removing the base--arm interlock produces {interlock:,} violating pairs; removing target "
        f"authorization produces {authorization:,}; and removing scan-age checks produces {scan:,}. "
        f"Their shortest counterexample prefixes contain {prefixes[0]}, {prefixes[1]}, and {prefixes[2]} "
        "observations, respectively. For example, the interlock ablation permits SEARCH rotation while "
        "the arm is not stowed. These counts demonstrate guard sensitivity over the enumerated domain; "
        "they are not observed mission failure rates.\n"
    )
    lines = [r"\begin{table}[t]", r"\caption{Bounded Reference-Model Ablations}",
             r"\label{tab:mission}", r"\centering\footnotesize",
             r"\begin{tabularx}{\columnwidth}{@{}Xrr@{}}", r"\toprule",
             r"Reference policy & Violating pairs & Prefix length \\", r"\midrule",
             f"All guards & {full['violating_cases']:,} & --- \\",
             f"Without base--arm interlock & {interlock:,} & {prefixes[0]} \\",
             f"Without target authorization & {authorization:,} & {prefixes[1]} \\",
             f"Without scan age & {scan:,} & {prefixes[2]} \\",
             r"\bottomrule", r"\end{tabularx}", "", r"\smallskip",
             rf"\raggedright Each policy evaluates {full['cases']:,} pairs. Prefix length counts observations from SEARCH to the first violating output. Counts concern abstract command admissibility.",
             r"\end{table}"]
    # Python string syntax above gives one terminal slash in f-strings; TeX rows
    # require two. Set the row ending explicitly to avoid escaping ambiguity.
    for index,line in enumerate(lines):
        if " & " in line:
            lines[index] = line.rstrip("\\") + "\\\\"
    return ("% Generated by experiments/verify_hazbot_mission.py; values come from computed results.\n"
            + paragraph + "\n".join(lines) + "\n").encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--generated-dir", type=Path,
                        help="TeX output; defaults to manuscript/generated, or OUTPUT/generated for a custom output directory")
    args = parser.parse_args()
    oracle_probes = check_oracle_semantics()
    policies, counterexamples = {}, {}
    for policy in POLICIES:
        summary, edges, first_by_phase = exhaustive_policy(policy)
        graph, parents = phase_bfs(policy, edges)
        summary["reachability"] = graph
        counterexamples[policy] = shortest_counterexample(policy, edges, first_by_phase, graph, parents)
        policies[policy] = summary
    require("full reference policy admits no violating commands", policies["full"]["violating_cases"] == 0)
    require("every named ablation exposes a counterexample",
            all(policies[p]["violating_cases"] > 0 and counterexamples[p] for p in POLICIES if p != "full"))
    require("exact total policy/phase/valuation case count",
            sum(summary["cases"] for summary in policies.values()) == 4*7*4096)
    # Independent Boolean-cube counting gives these command-cell totals. For
    # example SEARCH rotation fixes four motion flags and excludes one of four
    # two-target-flag settings: 3 * 2**6 cells. This is not a replay-derived count.
    expected_full_actions = {"rotate":3*2**6,"advance":2**5,"transport":2**6,
                             "reach":2**6,"close_gripper":2**5,"stow_arm":2**5,
                             "open_gripper":2**6,"stop_base":2**5+2**10}
    expected_full_actions["hold"] = 7*4096-sum(expected_full_actions.values())
    actual_full_actions = {action:sum(p["action_counts"].get(action,0)
                                     for p in policies["full"]["phases"].values()) for action in ACTIONS}
    require("independent Boolean-cube count matches full action histogram",
            actual_full_actions == expected_full_actions)
    require("independent interlock-ablation Boolean count",
            policies["no_base_arm_interlock"]["violating_cases"] == (3*2**6+2**5+2**6)+(3*2**6))
    require("independent authorization-ablation Boolean count",
            policies["no_target_authorization"]["violating_cases"] == 2**5+2**6+2**5)
    require("independent scan-age-ablation Boolean count",
            policies["no_scan_age"]["violating_cases"] == 3*2**6+2**5+2**6)
    nominal = nominal_mission()
    rows = []
    for policy,counterexample in counterexamples.items():
        if counterexample:
            for step in counterexample["trace"]:
                rows.append({"policy":policy,"step":step["step"],
                             "phase_before":step["phase_before"],"action":step["action"],
                             "phase_after":step["phase_after"],"observation_mask":step["observation_mask"],
                             **{name:int(step["observations"][name]) for name in FIELDS},
                             "violations":";".join(step["violations"])})
    csv_data = serialize_csv(rows)
    counterexample_json = (json.dumps(counterexamples,indent=2,sort_keys=True)+"\n").encode("utf-8")
    tex_data = render_tex_summary(policies, counterexamples, nominal)
    script = Path(__file__).resolve()
    result = {
        "analysis":"Exhaustive abstract HazBot mission command-admissibility study",
        "date":"2026-10-21", "dependencies":"Python standard library only",
        "evidence_type":"New abstract reference coordinator and independent command oracle; not deployed robotics code, physics/sensor simulation, hardware trial, hazard classification, or real mission success",
        "source_binding":{"path":str(script.relative_to(ROOT)),"sha256":hashlib.sha256(script.read_bytes()).hexdigest()},
        "model":{"phases":PHASES,"actions":ACTIONS,"observation_fields_lsb_first":FIELDS,
                 "observation_bitmask_encoding":"bit i is observation_fields_lsb_first[i]; all masks 0..4095",
                 "event_alphabet_size":ALPHABET_SIZE,"phase_count":len(PHASES),
                 "cases_per_policy":len(PHASES)*ALPHABET_SIZE,"policy_count":len(POLICIES),
                 "total_cases":len(POLICIES)*len(PHASES)*ALPHABET_SIZE,
                 "hold_semantics":"Abstract inhibit/no progressing actuation intent. Blocked guards preserve phase; target-acquisition and release-completion observations may advance logical phase while emitting hold. No physical stopping-time or command-cancellation guarantee follows.",
                 "observations":"External Boolean assertions. No generation from RGB, LiDAR, material sensors, odometry or arm feedback is modeled.",
                 "pruning":"none; including logically possible but physically inconsistent combinations",
                 "oracle_scope":"Command obligations and command-to-phase contracts; not exhaustive correctness of every transition guard or physical safety.",
                 "scan_scope":"Fresh usable clear scans required by oracle for base motion. Coordinator also conservatively requires fresh usable scans for DOCK/GRASP/PLACE; these extra arm-phase scan guards are not additional oracle obligations.",
                 "ablation_definitions":{"no_base_arm_interlock":"Remove arm_stowed from base-motion guards and base_stopped from arm-operation guards.",
                                         "no_target_authorization":"Remove target_authorized only; target_fresh remains required.",
                                         "no_scan_age":"Remove scan_fresh only; scan_usable remains required."}},
        "policies":policies,"counterexamples":counterexamples,"nominal_sequence":nominal,
        "validation":{"passed":True,"check_count":len(CHECKS),"oracle_positive_negative_probe_pairs":oracle_probes,"checks":CHECKS},
        "datasets":{"hazbot_mission_counterexamples.csv":{"sha256":hashlib.sha256(csv_data).hexdigest(),"rows":len(rows)},
                    "hazbot_mission_counterexamples.json":{"sha256":hashlib.sha256(counterexample_json).hexdigest()}},
        "generated_documents":{"hazbot_mission_summary.tex":{"path":"manuscript/generated/hazbot_mission_summary.tex",
                                                               "sha256":hashlib.sha256(tex_data).hexdigest()}},
        "limitations":["Seven phases and twelve Booleans are the complete bounded abstraction, not the complete robot state.",
                       "Unconstrained observations include physically inconsistent combinations; no probabilities or observed failure rates are inferred.",
                       "BFS is existential reachability with arbitrary next observations, not guaranteed completion under realistic sensing or environmental dynamics.",
                       "A shortest counterexample minimizes Boolean-observation prefix length, not time, distance, or severity.",
                       "Target authorization, freshness, grip, reachability and release are assumed input facts; their physical verification is outside this model.",
                       "HOLD is an abstract inhibit; deployed motion requires explicit lower-level stop/watchdog and arbitration semantics.",
                       "No collision dynamics, human proximity, hazardous substance properties, payload, contact mechanics, or response latencies are modeled.",
                       "Zero violating model commands is not a claim of physical safety, detector accuracy, or successful autonomous hazardous-material retrieval."],
    }
    output = args.output_dir
    output.mkdir(parents=True,exist_ok=True)
    generated_dir = args.generated_dir or (ROOT/"manuscript/generated" if output.resolve() == OUTPUT.resolve() else output/"generated")
    generated_dir.mkdir(parents=True,exist_ok=True)
    (generated_dir/"hazbot_mission_summary.tex").write_bytes(tex_data)
    (output/"hazbot_mission_counterexamples.csv").write_bytes(csv_data)
    (output/"hazbot_mission_counterexamples.json").write_bytes(counterexample_json)
    (output/"hazbot_mission_results.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    for policy,summary in policies.items():
        cex = counterexamples[policy]
        depth = cex["minimum_observation_prefix_length"] if cex else "none"
        print(f"{policy}: {summary['violating_cases']:,}/{summary['cases']:,} violating cases; shortest counterexample {depth}")
    print(f"Nominal Boolean witness: {nominal['steps']} steps to COMPLETE; checks passed: {len(CHECKS)}")


if __name__ == "__main__":
    main()
