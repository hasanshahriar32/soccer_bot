# Constructed source-policy replay protocol

This experiment measures commands emitted during deliberately constructed input
sequences. It is not a robot trial, a physics simulation, recorded sensor replay,
sensor-accuracy evaluation, collision study, or estimate of deployment failure
probability. The supervisor is a proposed standalone reference implementation;
the runtime robot nodes were not changed. The artifact supports a narrow claim:
explicit receipt-age and numeric-validity contracts alter otherwise permitted
commands under the specific asynchronous faults represented here.

## Source and execution boundary

The tested baseline is
`src/soccer_navigation/soccer_navigation/autonomous_ball_chaser_node.py`, class
`ActiveDrive12InchController`. This controller consumes the metric ball fields
published by `src/soccer_vision/soccer_vision/ball_tracker_node.py`: forward
coordinate `x`, lateral coordinate `y`, and distance `z`, all in meters; the
tracker emits `(-1,-1,-1)` for absence. Other repository controllers that expect
pixel coordinates/radius are not combined with this metric path in this replay.

`experiments/replay_supervisor.py` parses the baseline with Python's `ast`
module, retains its actual class and `STOP_DISTANCE_METERS` assignment, and
executes the unchanged callback and `control_loop` function bodies. It bypasses
the constructor and replaces ROS clock, publisher, logger, and motor output with
in-memory doubles. ROS is neither imported nor installed. No socket is opened;
no command is sent to a robot. The replay records the published planar
`Twist` intent `(linear.x, angular.z)`, not actual motor dynamics or TCP delivery.
In particular, this does not evaluate correspondence between PWM signs and ROS
rotation direction.

Preserved source behavior includes 20 Hz decisions, a one-second camera
receipt grace period, the all-angle minimum of ranges strictly inside
`(0.05,20)` meters, the `<=0.3048 m` stop threshold, lateral turn thresholds
`+/-0.1 m`, forward command `0.28 m/s`, target-turn commands `+/-0.6 rad/s`,
and search command `0.65 rad/s`. An all-invalid nonempty scan sets the source
minimum to `99`; an empty scan returns without changing the cached minimum.
Neither path records scan age. The replay starts the simulated clock at 100 s,
avoiding zero-as-uninitialized clock ambiguity while preserving subtraction in
the original time-dependent code.

The results JSON records the Git revision and SHA-256 of the exact source,
metric tracker, and experiment script. Uncommitted source versions are therefore
distinguishable even when the Git revision alone is insufficient.

## Policies

The three policies receive identical inputs and execute identical source desired
commands. Only the final in-memory output gate differs.

1. **Source:** the original callbacks and decision loop, with no additional gate.
2. **Age only:** output zero linear and angular velocity before the first scan
   or when scan receipt age is greater than or equal to `tau_s`. Other source
   decisions are unchanged.
3. **Age + validity:** apply the age gate, and also output zero if the latest
   scan contains no finite return strictly inside the source's `(0.05,20) m`
   interval, the latest ball tuple violates the metric numeric contract, or a
   valid scan minimum is `<=0.3048 m`. A ball tuple is admissible if it is the
   exact absence sentinel `(-1,-1,-1)`, or all three fields are finite, `x>=0`,
   and `z>0`. A malformed latest ball tuple latches this conservative hold until
   the next admissible target or absence message. This is an explicit design
   choice, not a baseline property. The existing source already stops for a
   valid near return; that rule is preserved and made explicit in the gate.

This wrapper cannot distinguish a finite pixel tuple from a finite metric tuple.
It does not validate coordinate consistency, detector quality, target identity,
or whether a close return is the ball. It deliberately preserves the existing
all-angle range domain, rather than introducing a geometry change or a detector
association method. Values outside the fixed interval, including returns at
`0.05 m` or `20 m`, are excluded; very close returns below the lower limit are
not separately resolved by this reference.

## Time and constructed traces

Each of 12 scenarios contains 80 decision ticks at 20 Hz: 960 ticks per policy,
2,880 output rows at the default `tau_s=0.25 s`. Tick `k` represents the command
held over `[k/20,(k+1)/20)` seconds. Receipts at a tick are processed before that
tick's decision. The first command occurs at 0 s; the last at 3.95 s. Integer
tick differences implement the supervisor deadline exactly; the source continues
to use its original floating-point time calculations. There are no random seeds,
unreported repeats, fitted parameters, or statistical confidence intervals.

Unless stated otherwise, scans arrive at 10 Hz, ball tuples at 5 Hz, ranges are
`[2.0,2.5,3.0,2.2] m`, and the centered ball tuple is `(1,0,1) m`. This gives
four intentionally simple all-angle samples; scan geometry is not used by this
baseline. All timestamps are receipt times, not sensor acquisition times.

| Scenario | Construction and purpose |
| --- | --- |
| Healthy centered | Regular clear scans and centered ball; check unchanged approach commands. |
| Healthy lateral reversal | Ball at `y=+0.2 m` for ticks 0--39, then `-0.2 m`; 10 Hz tuples; check unchanged turn reversal. |
| Near return and recovery | Minimum exactly `0.3048 m` on ticks 20--35, then `0.25 m` on ticks 36--49, clear thereafter; verify the pre-existing stop, including equality. |
| Camera stops publishing | No ball receipt from tick 20 onward; latest positive receipt was tick 16; verify the source's existing one-second expiry and subsequent search. |
| Explicit absence | Replace tuples with `(-1,-1,-1)` from tick 20 onward; verify existing immediate search. |
| No scan at startup | Suppress scans on ticks 0--19, despite continuing valid ball tuples; test unknown-scan behavior. |
| Scan interruption | Suppress scans on ticks 20--59; last pre-gap scan was tick 18; resume on tick 60. |
| All ranges invalid | During ticks 20--59 publish `[NaN,+Inf,-Inf,0,0.05,20]`; receipt age remains current, but no return belongs to the admissible interval. |
| Empty scan | During ticks 20--59 publish empty arrays; source retains its previous clear minimum. |
| Nonfinite ball tuple | Ticks 20--39 publish `(1,NaN,1)`; ticks 40--59 publish `(1,0,+Inf)`; restore valid tuples at tick 60. |
| Combined interruption | Suppress both streams on ticks 20--59; source eventually searches after its camera timeout while scan age remains stale. |
| Slow healthy scan | Clear scans every eight ticks (2.5 Hz), continuing valid ball tuples; expose progress lost through short scan deadlines. |

The constructed scene remains clear except during the near-return interval.
For interruption cases, this is scenario metadata, not information available to
the policies. The claim that a scene is clear in this metadata must not be
treated as measured ground truth from the workspace robot.

## Metrics and denominators

For each command tick, the full contract is constrained if any of these hold:
unknown/stale scan, latest scan invalid, latest ball tuple malformed, or a valid
near return. All policies are scored against this *same* full contract, so the
age-only variant intentionally does not satisfy all of it. The default suite
contains **274 constrained ticks out of 960**, including **30 near-return
ticks on which the source already emits zero**.

- `T` / `constrained_motion_ticks`: count constrained ticks with either nonzero
  linear or angular output. Search rotation therefore counts as motion.
- `F` / `constrained_forward_ticks`: count constrained ticks with positive
  linear output. These are a subset of `T`.
- `H` / `clear_forward_held_ticks`: count ticks whose constructed scene is
  clear, whose latest ball tuple is admissible and positive, and whose source
  desired command is forward, but whose policy output is not forward. The
  default denominator is **682 clear forward opportunities**. This measures
  intentionally conservative progress loss in the constructed scenes, not
  robot task completion or real-world false-positive rate.
- `motion_ticks` and `forward_ticks`: unconditioned command counts.
- `override_ticks`: ticks on which a gate is active, including a near-return
  tick where the source was already stopped; this differs from
  `output_change_ticks`.

Each tick is 50 ms. Durations derived from these counters are commanded
occupancy under the hold convention, not measured motor stopping time. Counts
across distinct scenarios are descriptive suite totals; scenario proportions
were chosen by the experiment author and have no deployment-frequency meaning.
The full supervisor's zero violations is a direct consequence of its gate on
these modeled inputs, not independent evidence of physical safety.

## Default results and timeout tradeoff

| Policy | `T` | `F` | `H` | Total forward ticks |
| --- | ---: | ---: | ---: | ---: |
| Source | 244 | 220 | 0 | 722 |
| Age only | 120 | 120 | 100 | 622 |
| Age + validity | 0 | 0 | 180 | 502 |

Both healthy traces retain all source commands under all three policies at the
default timeout. The full supervisor removes motion on the 244 constrained
ticks where the source moves, while also holding 180 constructed clear forward
opportunities. The age-only variant leaves the three 40-tick malformed-input
intervals unhandled, accounting for its 120 constrained motion ticks. Existing
camera expiry and near-range stop are credited to the baseline, not presented
as contributions of the supervisor.

An additional timeout sweep reruns all scenarios for `0.10`, `0.25`, and `0.50 s`.
Full-contract violations remain zero for the corresponding timeout contract.
In the slow, clear 2.5 Hz scan scenario, the full supervisor holds **60, 30, and
0 of 80 ticks**, respectively. In the scan-interruption scenario, source forward
intent persists after the final received scan for **0.10, 0.25, and 0.50 s**,
respectively, before the gate stops it. These values follow the configured
deadline at 50 ms resolution; they do not establish a physically safe timeout.

## Reproduction and checks

From the repository root, run:

```sh
python3 manuscript/experiments/replay_supervisor.py
python3 manuscript/experiments/replay_supervisor.py --check-only
```

Python 3.10 or later and the standard library are sufficient. The first command
regenerates CSV traces, per-scenario summaries, JSON results/provenance, and two
LaTeX tables. The second reruns the protocol without writing output artifacts.
Both fail on assertion errors. Behavioral checks cover full-contract gating,
healthy command preservation, near-stop threshold equality, source camera
expiry, explicit absence, startup without scans, age-only failure on fresh
invalid/empty scans, nonfinite ball acceptance in the source, recovery, and the
deadline/progress tradeoff. These are checks of policy behavior, not ROS message
delivery, motor transport, concurrency, or hardware performance.

Artifacts:

- `data/replay_trace.csv`: every constructed input receipt and per-policy command;
  nonfinite inputs use explicit text tokens inside CSV cells.
- `data/replay_summary.csv`: per-scenario counters, including zeros and preserved
  baseline behavior.
- `data/replay_results.json`: settings, source hashes, aggregate and per-scenario
  counters, sweep, and behavioral-check results.
- `data/timeout_sweep.csv`: timeout-dependent holding and persistence measures.
- `generated/replay_summary.tex`, `generated/timeout_sweep.tex`: generated compact
  tables using `booktabs` for inclusion in the manuscript.

## Limits and required next experiments

The source baseline is one repository controller, not a claim about every
available launch configuration. ROS scheduling, network transport, source
timestamps, and physical actuation are outside the experiment. Receipt age can
remain small for delayed or replayed sensor data; stamped messages and explicit
clock handling are needed before interpreting acquisition age. Numeric validity
cannot establish unit correctness or observation truth. Finite pixel tuples can
still pass this metric contract. All-invalid scans can also arise from a valid
no-return sensing condition; this reference conservatively holds and makes that
availability cost visible.

The baseline emits direct TCP motor commands as well as `/cmd_vel`. A physical
integration must place the contract gate before **both** command paths, or
replace them with a single authoritative arbiter. Adding a gate only to a ROS
subscriber would not intercept the source's direct motor output. Sensor
acquisition timestamps, ROS replay with recorded bags, contract boundary cases,
measured communication jitter, detector calibration, braking distance, actuator
watchdogs, and controlled robot trials remain necessary work. No physical
safety, ball-detection accuracy, mapping quality, score rate, real-time latency,
energy efficiency, or general novelty is established by this experiment.
