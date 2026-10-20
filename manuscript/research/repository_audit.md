# Repository evidence audit

Audit date: 2026-10-21. Repository HEAD at inspection: `c31ba9c`.
Paths and line numbers below refer to the inspected workspace snapshot. They are
evidence locators, not a claim that every listed component runs together.
The audit used source inspection only: no robot, network service, deployment
script, motor test, sensor stream, or inference model was executed. Local
screenshots and a saved map are illustrative artifacts; they do not establish
accuracy, timing, or successful autonomous operation.

## Recommended paper scope

**Scope selection update:** The completed manuscript selects an executable
case study of the metric chaser's observation contracts, receipt-age gating and
payload validation. `manuscript/experiments/replay_supervisor.py` is a newly
created offline research artifact; its constructed traces are distinct from
the pre-existing runtime repository and are not robot measurements. That
selected scope supersedes the initial bearing-association recommendation below.
The source limitations in this audit still apply to integrated-system claims.

The defensible present scope is a **repository-grounded design and integration
study of distributed ball perception and reactive approach**, with an explicit
evaluation protocol and disclosed integration limits. The central implemented
mechanism is bearing-window association between visual detections and planar
LiDAR, with monocular fallback. A publishable empirical claim would require new
calibrated measurements and a corrected, frozen execution configuration.

Candidate title: *Bearing-Gated Camera–LiDAR Ball Localization for a Distributed
ROS 2 Mobile Robot: Design and Integration Analysis*.

Do not describe a complete competitive soccer player. There is no evidenced
goal localization, opponent/team reasoning, team coordination, rule compliance,
field localization, scoring experiment, or integrated kicking/grasping trial.
The legacy brain's `KICKING` branch is a forward-push command, not proof of a
ball-striking mechanism (`src/core_brain/soccer_brain_node.py:191–204`).

The vocabulary should be precise:

- Say **latest-scan association**, not capture-time synchronization.
- Say **LiDAR range estimate**, not ground truth.
- Say **implemented branch/nominal timer setting**, not measured performance.
- Say **candidate research question**, not established novelty.
- Say **reactive approach/proximity stop**, not collision-free navigation.

## Source-grounded component inventory

| Component | Implemented behavior | Exact evidence | Integration/evaluation status |
|---|---|---|---|
| Edge visual detector | TFLite model loading, image preprocessing, NMS, class-specific size fallback, TCP detections and MJPEG | `scripts/detect_live_picamera2.py:39–55,196–215,322–340,407–474` | Model path is external to this repository. No model weights, training set, held-out metrics, quantization comparison, or measured inference log was found in the inspected tracked source/artifact inventory. |
| Host image bridge | Attempts HTTP MJPEG then size-prefixed TCP JPEG; publishes `/image_raw` | `src/soccer_vision/soccer_vision/camera_hub_node.py:44–106` | Receipt-time ROS stamping at lines 70–73; transport code does not establish capture latency. |
| Visual fallback | Broad HSV masks, opening/closing, circularity/area filtering; highest area × circularity; EMA with alpha 0.40 | `src/soccer_vision/soccer_vision/ball_tracker_node.py:44–48,85–99,247–267,300–343` | Implemented. Broad multicolor acceptance is not object-class discrimination or demonstrated illumination invariance. |
| Bearing/range association | Latest LiDAR accepted for 1.2 s; ±0.12 rad bearing window; valid ray minimum + 0.0325 m ball-radius correction; AI branch optionally range-gated | `src/soccer_vision/soccer_vision/ball_tracker_node.py:188–230` | No capture-time pair matching, covariance, calibration procedure, ground-truth comparison, or extrinsic transformation in this function. |
| Detection source handover | Recent AI detections suppress HSV image processing for 1.5 s | `src/soccer_vision/soccer_vision/ball_tracker_node.py:184–186,232–236` | Heuristic prioritization, not probabilistic fusion of independent detections. |
| Host metric output | `/ball_position` encodes forward x, lateral y, total range z | `src/soccer_vision/soccer_vision/ball_tracker_node.py:169–179,279–288` | Unstamped `Point` overloads z as range. Consumers must agree on units and frame; two incompatible producers/consumers remain. |
| Metric chaser | 20 Hz nominal timer; nearest whole-scan or recent-ball distance; stop at 0.3048 m; ±0.10 m lateral alignment; otherwise turn/advance/search | `src/soccer_navigation/soccer_navigation/autonomous_ball_chaser_node.py:28,43–57,90–168` | Metric-compatible with host tracker; not installed as a navigation console script or included in the SLAM launch. Physical stopping distance and performance unmeasured. |
| Web autopilot | 0.08 s sleep loop; stop at 0.35 m; ±0.12 lateral threshold; sends discrete letters; stop on target loss | `motor_control/web_teleop_server.py:211–264` | Started by `scripts/start_slam_mapping.sh:47–49`; uses multiple incompatible writers to shared ball state (details below). |
| Legacy PD brain | Pixel-center steering with a difference term, radius-dependent speed, coasting, directional search, conditional avoidance, forward-push branch | `src/core_brain/soccer_brain_node.py:35–59,105–126,162–223` | Pixel interface conflicts with current metric tracker. The difference term is not divided by elapsed time. Source existence does not establish valid integration. |
| Independent avoidance | Minimum valid scan range in nominal −90° to +90° forward sector; 0.4 m threshold; publishes escape Twist | `src/soccer_navigation/soccer_navigation/obstacle_avoidance_node.py:23–26,38–75` | Publishes `/obstacle_avoidance/cmd_vel`; no inspected subscriber or arbiter connects this topic to motor control. |
| LiDAR transport | Bidirectional serial/TCP bridge with DTR/RTS and STOP-SCAN reset | `scripts/lidar_bridge.py:31–54,69–100` | Used with a pseudo-terminal and vendor ROS driver by the mapping launcher; also alternative custom raw and JSON paths exist. |
| Raw scan parser | Header parsing, angle interpolation/calibration, 720 bins, ROS `LaserScan` output | `scripts/raw_lidar_publisher.py:71–145` | Alternative to vendor driver, not a new LiDAR sensor or demonstrated angular-resolution improvement. No checksum validation in the inspected parse path. |
| Motor gateway | TCP port 9000; serial discovery/reconnection; maps PWM-format signs to letters and forwards at 9600 baud | `motor_control/motor_server.py:43–81,105–163,193–204` | Magnitudes are discarded. Cannot use this path as evidence of continuous wheel PWM or physical velocity tracking. |
| Motor firmware | F/B/L/R/S commands, fixed PWM magnitude, safe initialization | `src/arduino/motor_driver/soccer_bot_motor_driver.ino:17–74,78–145` | Multiple firmware variants exist with different default speed/direction assumptions. Deployment identity and physical calibration not established. |
| Vendor SLAM integration | Launches vendor LiDAR driver, SLAM Toolbox async mapping, phone orientation bridge, coordinate tracker, RViz and host perception | `src/soccer_slam/launch/soccer_slam_launch.py:34–142` | Existing SLAM dependency integration, not a new SLAM algorithm. Launch excludes a motor bridge or autonomous brain. |
| Phone orientation bridge | Publishes IMU orientation/angular rate, orientation-only odometry, zero-translation `odom -> base_link` | `src/soccer_slam/soccer_slam/phone_imu_bridge.py:609–645` | Does not provide measured x/y motion or encoder odometry. |
| Local occupancy view | 240 × 240 grid, 0.03 m cells, fixed scan origin, Bresenham rays, 2 Hz nominal publishing | `scripts/fast_occupancy_mapper.py:22–26,49–68,70–115` | No robot-pose compensation. Occupied cells persist; this is not evidence of global SLAM while moving. |
| Fixed-reference ICP | Startup reference scan, nearest-neighbor/SVD matching, deadzones and alpha 0.1 output smoothing | `scripts/laser_scan_matcher.py:62–132,134–205` | Alternative standalone estimator. Does not prove zero drift, global convergence, or loop closure. |
| Command-integrated pose | Integrates commanded `/cmd_vel` at nominal 20 Hz and publishes `map -> base_link` | `scripts/robot_odometry.py:42–97` | Command integration is not measured wheel odometry; no encoder feedback/slip estimation here. |
| Pose display | TF lookup copied to `/robot_map_pose` and a bounded trajectory | `src/soccer_slam/soccer_slam/coordinate_tracker.py:58–88` | Repackages an available transform; it is not independent localization or ground truth. |

## Inconsistencies that constrain paper claims

1. **Pixel/metric contract conflict.** Current host tracker publishes meters,
   but the PD brain and `decision_logic.py` interpret `Point.x` as horizontal
   pixels and `Point.z` as pixel radius. Compare tracker lines 283–288 with
   brain lines 105–126,178–204 and
   `src/soccer_navigation/soccer_navigation/decision_logic.py:19–22,26–55`.
   The autonomous launcher explicitly selects the incompatible PD brain
   (`scripts/start_autonomous_soccer.sh:39–44`).
2. **A third `/ball_position` contract.** The edge detector's optional native
   ROS publisher sends `(range_m,pixel_offset,bearing_deg)` directly on the same
   topic (`scripts/detect_live_picamera2.py:196–203,274–280`), distinct from
   the host tracker's `(forward_m,lateral_m,range_m)`. Both must not be treated
   as interchangeable messages.
3. **AI/HSV bearing sign conflict.** Edge AI bearing uses `cx - W/2`, positive
   toward image-right (`scripts/detect_live_picamera2.py:427–430`). Host AI
   conversion preserves that sign as positive lateral
   (`ball_tracker_node.py:150–170`), whereas its HSV branch uses `W/2 - cx`,
   positive image-left (`ball_tracker_node.py:265–267`). Camera orientation
   must be calibrated before claiming consistent steering/fusion.
4. **Web state unit race.** ROS updates shared ball y in meters
   (`motor_control/web_teleop_server.py:314–320`), while a separate AI TCP
   worker writes `data.y`, which is a pixel offset, into the same variable
   (`motor_control/web_teleop_server.py:408–427` and edge payload lines
   209–214). The autopilot compares this variable with ±0.12 as though it
   were metric (web server lines 248–255). Its `SEARCHING` status actually
   sends stop, not a rotation (lines 260–263).
5. **Latest-scan fusion is not temporal synchronization.** Association uses
   wall-clock receipt age, not image/scan capture-time skew (tracker
   lines 188–200). Camera bridge stamps at host receipt (camera hub
   lines 70–73); the raw LiDAR publisher similarly restamps at publication
   (`scripts/raw_lidar_publisher.py:131–140`). No extrinsic transform is
   applied in the association function, although the SLAM launch places the
   camera 0.1 m forward of `base_link` (launch lines 107–113).
6. **Association can select background.** HSV fallback applies no predicted
   range gate; it takes the nearest valid range within the bearing window
   (tracker lines 269–275 and 207–228). The AI path applies
   `max(0.18,0.35*expected_range)` gating (lines 160–161,217–220), but its
   supplied expected range may already have been LiDAR-derived at the edge
   (edge detector lines 432–449). Avoid describing it as independent
   probabilistic sensor fusion.
7. **Different stop policies.** The ROS metric chaser stops at 0.3048 m from
   the minimum entire scan or ball range; the web autopilot stops at 0.35 m
   ball range alone. They are separate variants. The ROS chaser does not
   expire its retained LiDAR minimum after scan loss (chaser lines 90–99,
   107–124), and its ball age is reception-based. A threshold is not a
   verified physical stopping distance or safety guarantee.
8. **Avoidance is not unconditional.** PD brain avoidance executes only for
   `front_blocked and not ball_detected` (brain line 168); detected-ball rays
   within ±15° are skipped (lines 148–150). Frontal indices assume a scan
   beginning at forward zero (lines 132–146). Neither its docstring's
   highest-priority avoidance nor guaranteed collision prevention is
   supported for arbitrary scan layouts and target detections.
9. **Motor protocol truncates control.** Port 9000 converts `SET:l,r` to
   letter direction by sign (motor server lines 149–163). It ignores the
   speed digit sent by the metric chaser (chaser lines 69,85), since the
   server's recognized branches omit digits. The older port-6000 motor
   bridge prioritizes nonzero linear speed over angular commands
   (`src/arduino/motor_driver/motor_bridge_node.py:50–67`). Neither path
   establishes faithful simultaneous Twist linear/angular realization.
10. **Liveness is not a watchdog.** Port-9000 gateway stops on client
    disconnect (motor server lines 183–191) but lacks a command-age stop
    in the inspected receive loop. Firmware loops contain no watchdog
    (`src/arduino/motor_driver/soccer_bot_motor_driver.ino:45–74`). A socket
    remaining open with stale commands is a separate condition. Chaser
    deduplicates unchanged command strings and does not reconnect after
    send failure (chaser lines 76–88). Do not claim bounded response under
    network faults without fault-injection measurements and fixes.
11. **Mapping alternatives are separate.** SLAM Toolbox launch,
    fixed-origin occupancy mapper, fixed-reference ICP and command-integrated
    pose are different pipelines. Combining their advertised benefits into
    one architecture would be unsupported. Running standalone direct
    `map -> base_link` broadcasters alongside SLAM's `map -> odom ->
    base_link` chain can create competing transform authority.
12. **Packaging is incomplete.** Navigation setup installs only obstacle
    avoidance (`src/soccer_navigation/setup.py:21–24`), not metric chaser,
    motor control or `decision_logic`. Brain is outside an installed ROS
    package. Vision package declares several dependencies, but omits
    `visualization_msgs` used by tracker (`src/soccer_vision/package.xml:10–13`
    versus tracker line 28). The SLAM launcher references external packages,
    configurations and environment-specific deployment paths; launch source
    is evidence of intended composition, not a successful clean install.
13. **Alternative scan layouts need validation.** The custom parser uses 720
    bins (`scripts/raw_lidar_publisher.py:54,131–144`); edge detector's native
    callback simply copies the first 360 values and later treats each index
    as one degree (`scripts/detect_live_picamera2.py:281–285,432–439`). Its
    convention is incompatible with that 720-bin source without conversion.

## Defensible research questions and required evaluation

These are hypotheses to investigate, not findings or first-of-kind claims.

| Candidate question | Existing support | Evidence still needed |
|---|---|---|
| Does range-gated visual-bearing association reduce background substitutions compared with ungated cone minimum and monocular size? | AI range gate, ungated HSV branch and fallback all exist. | Frozen detector outputs, measured range truth, association labels, matched samples across methods, range/bearing error, substitution rate and failure examples. |
| When does fallback improve target availability under LiDAR miss geometry? | Explicit no-match/no-LiDAR fallback branches. | Controlled beam-height, range, bearing, occlusion and lighting conditions; annotate beam/ball intersection; report availability together with error and false positives. |
| How much do stale observations affect reactive stopping and steering? | Receipt-age checks, distributed transport, multiple nominal control periods. | Capture timestamps, synchronization/clock analysis, injected delay/loss, end-to-end latency quantiles, physical stopping error, obstacle clearance, independent emergency stop. |
| How does interface-contract enforcement change reproducibility of a small ROS 2 robot? | Repeated semantic and unit mismatches identified above. | Corrected typed/stamped message schema, deterministic replay/fault tests, a frozen launch, reproducible before/after violation and task outcomes. This would be new work, not an already implemented contribution. |

The first question is the closest fit to existing code. Cite prior bearing-based
camera/range association and robotic soccer perception; do not infer novelty
from source inspection. A literature review must establish the comparison gap.

Suggested experimental stages: (i) passive calibrated perception data collection;
(ii) offline common-input association ablations; (iii) guarded low-speed physical
approach trials after interface and watchdog fixes; (iv) optional separate SLAM
evaluation. Prespecify environments, target sizes, held-out scenes, sampling
unit, number of independent trials, failure definition and confidence intervals.
Keep synthetic calculations, software regression checks, recorded replay,
hardware measurements and illustrative screenshots visibly separate.

## Evidence currently absent or insufficient

- No independently labeled detection test set, train/test split, external model
  provenance, inference artifact or training/quantization evaluation in the
  inspected source/artifact inventory.
- No synchronized sensor recording, calibrated camera intrinsics/extrinsics,
  independent target-range ground truth or association annotations.
- No repeated autonomous task dataset with success/collision counts,
  stopping-distance error, latency/bandwidth/CPU/power measurements or baseline
  ablations.
- A saved map (`src/soccer_slam/maps/test_first_map.yaml:1–7`) supplies resolution
  and origin metadata, not trajectory error, map accuracy or loop-closure
  evaluation.
- Files named `test_motors.py`, motor diagnostic scripts and `test_cmd_vel.sh`
  issue hardware/transport commands; they are not a unit-test suite or
  publication-quality quantitative evidence. Their execution was intentionally
  outside this audit.
- Several source comments assert "exact", "ground truth", "zero drift",
  "instantly" or "all systems connected". Such comments were not counted as
  validation.

## Submission-specific constraints from the supplied guide

`manuscript/guideline/guide.md` requires IEEE double-column A4, at most six pages
including references/figures/tables, a PDF no larger than 3 MB, embedded fonts
with no Type 3 fonts, double-blind anonymization and LLM-use acknowledgement.
Anonymized material should exclude account names, machine paths, addresses,
screen overlays, private network identifiers and embedded author metadata.

The guide's stated restriction of LLM use to non-intellectual purposes cannot
be certified automatically when a model has helped formulate research
questions or technical prose. Authors must review contribution provenance,
follow the venue's applicable policy, and make an accurate disclosure; an
acknowledgement must not falsely claim only copyediting if use was broader.
Source inspection cannot establish authorship approval, originality/similarity
percentage, non-simultaneous submission or venue acceptance.

Machine-readable claim decisions are in `claim_evidence.csv` alongside this
audit. Runtime source files were not modified.
