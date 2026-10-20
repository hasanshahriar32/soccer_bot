# Novelty and validation roadmap

Author-facing plan, 21 October 2026. Proposed studies below have **not** been performed; no improvement magnitude or publication outcome is promised.

## Chosen contribution and present evidence

The current paper is an **executable case study of freshness and interface contracts in one distributed ROS 2 ball-pursuit repository**. It combines a source-grounded interface/actuation audit, a standalone command gate, and an ablation that separates receipt-age rejection from numeric-validity rejection.

The existing evidence is offline only: 12 constructed traces, 80 ticks per trace at 20 Hz, with the original metric controller callbacks executed through in-memory substitutes. The three policies receive the same events. Sensor acquisition, ROS execution, network transport, motor delivery, robot dynamics, and soccer matches are outside that experiment. The proposed gate is not integrated into runtime nodes.

The result establishes behavior under the stated finite command contract. Zero violations of a gate's own rule is conformance, not independent validation of physical safety. Preserve the clear-scene motion-opportunity cost alongside violation counts; an always-stop controller is otherwise a misleading comparator. See [the exact protocol](evaluation_protocol.md) and [source provenance and prior art](related_work.md).

## Position against the closest prior art

- ROS 2 soccer integration predates this project: Scheunemann and van Dijk, `scheunemann2019ros2`.
- Offboard computation and accessible soccer platforms already exist: Passault et al., `passault2022rsk`.
- Layered behavior selection and nominal/fallback control are established: `brooks1986robust` and `seto1998simplex`.
- Nav2 Collision Monitor already implements sensor-based velocity filtering and source timeouts; `twist_mux` already provides priority and timeout arbitration: `nav2collision` and `twistmux`.
- Generation-time information age and ROS transport freshness policies are established: `kaul2012status`, `yates2021aoi`, and `ros2qos`.

The distinction is the reproducible diagnosis of this implementation's contracts and bypass paths. Do not call this the first ROS 2 soccer robot, a new general safety algorithm, or a proven collision-avoidance controller. The studies below could deepen the contribution, but their novelty must be reassessed against method-specific literature before making a stronger claim.

## H1 — Acquisition age and association uncertainty

**Hypothesis.** Under controlled camera/scan delay and robot turning, using capture timestamps and bounded alignment uncertainty reduces incorrect camera–LiDAR associations at a matched association acceptance rate, compared with the current latest-scan fixed-window association. Capture-age rejection may also reduce commands based on old captures while costing more accepted motion opportunities.

**Matched baselines.** (a) Current latest-scan association with receipt limits; (b) same algorithm plus capture-age rejection; (c) capture-age rejection plus timestamp-aware association/uncertainty gating. Keep detector outputs, calibration data, range limits, drive intents, and evaluation recordings identical. Add a capture-age-only ablation so association improvements are not attributed to rejection alone. Compare association error versus acceptance curves, rather than selecting one favorable threshold.

**Inputs needed.** Image capture times, scan acquisition times (and scan/per-ray timing where available), receive times, sequence IDs, synchronized clock offsets or explicit offset-error bounds, camera intrinsics, camera–LiDAR extrinsics, and turning-rate/pose estimates. Obtain independent annotations of ball identity, bearing, and distance, including background objects and laser misses. A scan return selected by the algorithm is not ground truth.

**Uncertainty treatment.** Account separately for calibration/bearing error, clock error, and temporal displacement. An illustrative angular budget includes a turning term `|omega| * |delta_t|`, but this is not a complete motion model: ball motion, translation, rolling capture, and scan sweep timing also matter. Specify assumptions and estimate parameters using calibration/training sessions separate from evaluation sessions.

**Metrics and units.** Wrong-object associations / accepted associations; rejection fraction; absolute and signed range error in metres; bearing error in radians; acquisition-age distributions in milliseconds; constrained nonzero commands / decision ticks; held valid-motion opportunities / opportunities. Report full denominators and error-versus-acceptance tradeoffs.

**Sampling.** A paired camera/scan association is the decision unit; a complete independently recorded approach run is the replication unit. Vary delays, burst losses, ball motion, and turning rate across independent runs. Treat frames from the same run as correlated; any uncertainty intervals must resample runs, not individual adjacent frames.

## H2 — Typed adapters for incompatible observation units

**Hypothesis.** Explicit image-space and metric-space message contracts with checked adapters reduce silent unit mismatches that remain admissible under the existing finite-number checks, without discarding correctly converted observations unnecessarily.

**Matched baselines.** (a) Existing overloaded `geometry_msgs/Point`; (b) the numeric-validity reference gate; (c) distinct stamped detection/state schemas and an explicit calibrated conversion. Keep the controller's metric inputs identical on valid cases. Include an adapter-disabled ablation and deliberate finite pixel tuples that would pass numeric checks.

**Inputs needed.** A written producer/consumer contract: units, frames, valid/absent semantics, capture stamp, detector source, and uncertainty fields. Use independently labeled pixel detections, known camera calibration, independent metric references, and a catalog of corruption events: swapped fields, pixel-to-metre confusion, wrong frame, stale/replayed IDs, missing calibration, nonfinite values, and out-of-domain detections.

**Evaluation oracle.** Label valid conversion and semantic rejection independently of the adapter implementation. Use held-out calibration positions and independently generated corruption cases. Distinct ROS message names help separate interfaces but cannot prove that a producer assigned the correct physical units or frame; test those failure modes explicitly.

**Metrics and units.** Semantically corrupted observations accepted / injected corruptions; correct observations rejected / correct observations; conversion error in metres and radians; extra processing time in milliseconds on the stated processor; changed command decisions / paired decision ticks. Count failures by corruption class, including classes the schema cannot detect.

**Sampling.** One injected semantic corruption is an event unit; one independently collected acquisition session is the replication unit for conversion accuracy. Separate schema-conformance results from physical-estimation results. Do not treat every frame of one fixed-position recording as an independent experiment.

## H3 — Final actuator authority under communication faults

**Hypothesis.** Routing all wheel commands through one endpoint with explicit precedence and a bounded command lifetime reduces stale or conflicting actuator commands compared with concurrent ROS and direct-TCP paths, at a measurable availability cost. This is an integration hypothesis, not a new arbitration principle.

**Matched baselines.** (a) Actual legacy paths; (b) configured `twist_mux` plus Nav2 Collision Monitor; (c) the reference contract integrated ahead of every output. Match observation semantics, speed limits, timeout values, scan geometry, and injected event schedules. Report any feature or geometry mismatch; package defaults are not a fair matched baseline.

**Inputs needed.** An exhaustive inventory of command writers, ROS/topic traces, TCP endpoint/sequence logs, controller clocks, receive/acknowledgement times, and watchdog behavior. First use transport substitutes and fault injection; subsequently measure endpoint behavior and wheel motion in controlled trials. Do not infer physical actuation from `/cmd_vel` alone, because the legacy controller also writes direct TCP commands.

**Fault matrix.** Include scan silence, newly received old data, all-invalid ranges, camera silence, independent command-source conflicts, lost hub process, delayed/reordered commands where supported by the tested transport, reconnection, and stale-command replay after restart. Distinguish TCP's ordered byte-stream behavior from application-level replay or multiple-writer conflicts.

**Metrics and units.** Conflicting-source selections / conflict events; stale nonzero commands accepted / stale-command events; fault-to-zero-command latency at the final endpoint in milliseconds; nominal motion availability / eligible intervals. Physical trials additionally require measured wheel-stop latency and stopping distance in metres, reported separately from requested velocity.

**Sampling.** One independently initiated fault/recovery episode is the replication unit. Repeat across documented link/load conditions and experimental sessions; pair policies by fault schedule. Report censored runs and failures to recover. A physical stopping claim requires measured speed, braking, footprint, delay bounds, and obstacle clearance, not only the configured `0.3048 m` threshold.

## Execution and reporting decisions

Before collecting new data, fix the task conditions, primary metric, experimental unit, baseline configurations, timeout-selection procedure, exclusion rules, and held-out evaluation split. Use a pilot to estimate variability and choose a defensible replication count; do not invent a required sample size or promised effect from the current deterministic traces.

For each study, preserve raw events, annotations, calibration and configuration versions, source hashes, processing scripts, and per-run outputs. Separate tuning from evaluation. Report failed or unsupported cases, availability costs, and the limits of any generalization. Statistical intervals apply to independently sampled trials; deterministic suite totals remain descriptive.

## AI assistance and submission eligibility

The local [conference guideline](../guideline/guide.md) requires an LLM declaration and describes use as **“solely for non-intellectual purposes.”** This preparation included literature discovery, research framing, and draft writing. Do not certify that the assistance was only grammar editing. Keep a truthful assistance record, obtain human review and responsibility for every claim, and resolve eligibility with the actual venue policy before submission. The current artifact is an author research draft; it is not a certified submission.
