# Abstract mission-coordination verification

Date: 2026-10-21. This is a **new reference coordinator**, added to investigate
the coordination obligations of the Pi-centered mobile manipulator. It is not
the deployed robot program. No robot connection, ROS process, motor/arm command,
sensor processing, detector inference, hazardous object, or physics simulation
is involved. The result concerns bounded command admissibility in a finite
Boolean model.

## Model and complete event alphabet

The coordinator has seven phases:

`SEARCH → APPROACH → DOCK → GRASP → CARRY → PLACE → COMPLETE`.

Each phase also has self transitions. `hold` is an action, not an additional
phase. When a guard blocks progress, hold preserves the phase. Two event-only
transitions—target acquisition from SEARCH to APPROACH and observed release
from PLACE to COMPLETE—advance the logical phase while emitting hold, meaning
no progressing actuation intent is issued with that update. The abstract action
does not establish physical braking, cancellation of an earlier command, or a
bounded stop response; deployment would require explicit lower-level semantics.

There are twelve Boolean observations:

| Bit, least significant first | Observation | Intended external meaning |
| --- | --- | --- |
| 0 | `target_authorized` | Selected object belongs to the allowed mission set. This is not a chemical/material identification result. |
| 1 | `target_fresh` | Target observation satisfies a configured age contract. |
| 2 | `scan_fresh` | Navigation observation satisfies a configured age contract. |
| 3 | `scan_usable` | Navigation data are valid for the intended clearance decision. |
| 4 | `route_clear` | Intended base route is accepted by an external clearance check. |
| 5 | `arm_stowed` | Arm is externally confirmed in the designated base-motion configuration. |
| 6 | `base_stopped` | Base is externally confirmed stopped. |
| 7 | `wrist_reachable` | A target configuration passes an external wrist-reach decision. This is not a calibrated grasp/contact workspace guarantee. |
| 8 | `at_pick_zone` | Base has reached the selected docking region. |
| 9 | `grip_confirmed` | An external confirmation reports object retention. |
| 10 | `at_drop_zone` | Base is at an authorized deposition region. |
| 11 | `release_confirmed` | An external confirmation reports release. |

All `2^12 = 4,096` valuations are examined at every phase, without event
pruning. This includes inconsistent combinations such as simultaneous grip and
release assertions or stale scans with a clear-route assertion. They are
deliberate tests of command guards, not a generated sensor dataset or a model
of likely environmental states. There is no distribution over valuations.

The full observation-to-command table therefore contains
`7 × 4,096 = 28,672` cells per policy. Four policies produce 114,688 evaluated
cells in total.

## Reference transitions

Let target acceptance mean authorized **and** fresh. Scan health means fresh
**and** usable. Base-motion admission additionally requires clear route and
stowed arm. Manipulation admission requires healthy scans, stopped base, an
accepted target, and wrist reachability.

| Phase | Progressing behavior | Otherwise |
| --- | --- | --- |
| SEARCH | Accepted target advances to APPROACH with hold; otherwise admitted base rotation searches. | Hold. |
| APPROACH | Accepted target plus base-motion admission permits advance; at pick zone, request base stop and enter DOCK. | Hold. |
| DOCK | Manipulation admission requests reach and enters GRASP. | Hold. |
| GRASP | Manipulation admission requests close; confirmed grip instead requests arm stow and enters CARRY. | Hold. |
| CARRY | Confirmed grip at drop zone requests base stop and enters PLACE; otherwise admitted base transport carries. | Hold. |
| PLACE | Stopped base, healthy scan, and drop zone permit release request when grip is confirmed; observed release instead enters COMPLETE with hold. | Hold. |
| COMPLETE | Hold, remaining COMPLETE. | Absorbing phase. |

These transitions specify a research reference policy, not an implementation
claim about the earlier arm pickup preset or reactive base controllers. The
model's Boolean conditions do not implement their own sensing/verification.

## Independent command oracle

The oracle is a separately written explicit function. It does not call or reuse
the coordinator's combined target, scan, motion, stationary, or manipulation
guards. It checks:

- Rotate, advance, and transport require fresh usable scans, clear route, and
  stowed arm.
- Advance additionally requires an authorized fresh target.
- Reach, close, stow, and open require stopped base.
- Reach and close additionally require authorized fresh target and wrist reach.
- Transport requires confirmed grip.
- Open requires drop zone and confirmed grip.
- Each nontrivial command belongs to its specified phase/transition; COMPLETE
  is absorbing. Stop and hold need no positive sensor evidence in the oracle.

The coordinator additionally gates its arm phases on scan health. Those extra
conservative gates are not separate arm-command scan obligations in this
oracle. Thus removing scan age may expose additional arm commands without
those commands being counted as scan-obligation violations. This distinction
keeps the tested property explicit.

The oracle does not claim to verify every desirable state-transition
requirement. For example, it examines whether an issued action is admissible,
not every prerequisite of a logical phase update that emits hold. It does not
verify the truth of observations, causal consistency between successive
observations, continuous motion, object contact, or physical safety.

## Ablations and exhaustive results

Each ablation removes only the specified guard category:

- `no_base_arm_interlock`: remove stowed-arm admission for base motion and
  stopped-base admission for arm motion.
- `no_target_authorization`: remove target authorization, retaining target age.
- `no_scan_age`: remove scan freshness, retaining scan usability.

| Policy | Enumerated cells | Violating cells | Shortest violating observation prefix |
| --- | --- | --- | --- |
| Full reference | 28,672 | 0 | None |
| Without base/arm interlock | 28,672 | 480 | 1 event |
| Without target authorization | 28,672 | 128 | 2 events |
| Without scan age | 28,672 | 288 | 1 event |

These are truth-table cell counts. They are **not** measured failure rates or
probabilities. The full reference emits 192 rotate, 32 advance, 64 transport,
64 reach, 32 close, 32 stow, 64 open, 1,056 stop, and 27,136 hold actions across
the complete table; its zero violations are therefore not due to always holding.
COMPLETE alone contributes 4,096 hold cells.

Independent Boolean-cube counting confirms the action histogram and ablation
counts. For example, SEARCH rotation fixes four base-motion flags and excludes
one of four target-flag settings: `3 × 2^6 = 192` cells. Interlock removal adds
288 base commands with unstowed arm and 192 arm commands with moving base,
giving 480 violations. Authorization removal adds 32 inadmissible advances,
64 reaches, and 32 closes, giving 128. Scan-age removal adds 192 rotations,
32 advances, and 64 transport commands, giving 288.

## Reachability and concrete counterexamples

Breadth-first search starts at SEARCH. Every one of the 4,096 outgoing
valuation edges is examined at each reached phase; there is no consistency or
oracle-based pruning. All seven phases are reachable for every policy. Each
phase graph contains thirteen unique directed phase edges (seven self loops,
six forward edges), representing all 28,672 valuation-labeled edges. Shortest
depths are SEARCH 0, APPROACH 1, DOCK 2, GRASP 3, CARRY 4, PLACE 5, COMPLETE 6.

This is existential phase reachability. Arbitrary next observations can assert
grip/release immediately, so depth six is not a task duration, physical action
count, guaranteed progression, or proof that a robot can complete the mission.
A separate eleven-observation nominal witness exercises all nine action types
and reaches COMPLETE with no oracle violations. It is a constructed reference
sequence, not an observed or physically simulated mission.

The shortest counterexample prefix minimizes the number of Boolean observation
events from SEARCH to the first violating command. Ties use the declared phase
order and then increasing bitmask. Full valuations are saved in CSV and JSON:

| Ablation | Concrete shortest witness |
| --- | --- |
| Interlock | At SEARCH, mask 28: scan fresh/usable and route clear; arm not stowed. Rotation is emitted, violating stowed-arm admission. |
| Authorization | Mask 2 moves SEARCH to APPROACH with hold despite unauthorized fresh target. At APPROACH, mask 62 has healthy clear navigation and stowed arm but unauthorized target. Advance violates authorization. |
| Scan age | At SEARCH, mask 56: scan usable, route clear, arm stowed, but scan stale. Rotation violates scan freshness. |

Every shortest trace is replayed against its ablated coordinator; its final
command violates the independent oracle and its earlier commands do not. The
shortest prefix is not a minimum-time, minimum-distance, or most severe physical
failure trace.

## Reproduction and checks

Run from the repository root:

```sh
python3 manuscript/experiments/verify_hazbot_mission.py
python3 manuscript/experiments/verify_hazbot_mission.py --output-dir /tmp/hazbot-mission-repeat
```

The standard-library implementation completes 109 checks covering exhaustive
cardinality, unpruned event retention, phase reachability, counterexample replay
and shortest depth, nominal progression, fifteen independent positive/negative
oracle probe pairs, and independent Boolean-cube counts.

Outputs are `../data/hazbot_mission_results.json`,
`hazbot_mission_counterexamples.json`, and `hazbot_mission_counterexamples.csv`.
The results bind the verifier source and both counterexample files by SHA256.
A separate read-back confirmed all phase/action/count sums, BFS depths, four
counterexample CSV rows, source/dataset hashes, and three byte-identical repeat
outputs. `hazbot_mission_validation.json` records that independent check.

Zero model violations establishes only that this reference transition function
meets the stated oracle over the complete bounded domain. It does not certify
physical safety, real target/material recognition, arm reachability calibration,
navigation performance, payload capacity, or autonomous hazardous-material
retrieval. Those need deployed integration and measured evaluation.
