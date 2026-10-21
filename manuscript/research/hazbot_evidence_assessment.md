# HazBot source and attachment evidence assessment

Assessment date: 2026-10-21. This document supports reframing the platform as a
Raspberry Pi centered mobile manipulator for autonomous object retrieval and
future hazardous-object handling. It records what the available evidence can
support; it is not a hardware test report. Inspection was read-only apart from
this report and its source inventory. No deployment, robot connection, motor,
servo, sensor, or inference script was executed.

## Scope established by the authors

The current author clarification takes precedence over the older soccer-only
framing: Raspberry Pi is the central computer, with four subsystems:

1. Navigation: LiDAR and its embedded controller/interface connect to the Pi.
2. Wheel control: Pi communicates with an Arduino, which controls the drive.
3. Visual perception and ML: camera connects directly to the Pi; inference is
   intended to execute natively on the Pi.
4. Robotic manipulation: Pi communicates with an Arduino that drives the arm.

The authors clarify that they **simulated with ball control**. This establishes
an author-reported nonhazardous surrogate/simulation context, not a verified
physical ball pick-and-place experiment. No counts, success denominator, trial
conditions, payload measurement, or timing records accompany that statement.
It does not establish a complete autonomous mission. Ball retrieval is a bounded
surrogate task within the larger mobile-manipulation design.

Hazardous-object recognition and relocation are the intended application. The
available detector is not trained or validated for arbitrary hazards. A strong
paper can present the modular architecture **toward hazardous-object retrieval**,
its implemented component mechanisms, and clearly identified offline analyses.
It cannot state that arbitrary hazardous materials have already been recognized
or safely handled.

## Supplied attachments

Both PDFs were extracted in full with `pdftotext -layout`. Relevant pages were
also rendered and inspected visually. The engineering report is six A4 pages;
the presentation is eighteen 1440 × 810 point slides. Their hashes are recorded
in `../data/hazbot_source_inventory.json`.

### Engineering examination report

`proposal_resources/Autonomous-Mobile-Manipulator-Engineering-Exam-Report.pdf`
is dated 2026-09-30 in PDF metadata. Its title is *Autonomous Mobile Manipulator
with 4-DOF Arm & Edge-AI with LiDAR Fusion for Pick-and-Place Tasks*.

| Page | Relevant content | Evidence interpretation |
| --- | --- | --- |
| 1 | Current-status banner states base/sensor infrastructure and remote control established; arm integration and manual pick-and-place current; autonomous operation intended. | Supports phased development, not already complete autonomy. |
| 1 | Pi, Uno, L298N, two 12 V JGA25-370 geared motors with encoders, YDLIDAR X4, Pi Camera V2, ROS 2 Jazzy. | Hardware description of that report revision. |
| 1–2 | Five stages: base complete, manual arm current, automatic detection/fusion/full pick-and-place planned. | Development roadmap; newer source implements more visual processing than this report describes. |
| 3 | HSV centroid and bearing, scan-index association, differential-drive equations, arm mechanics. | Design equations; rendered equations contain literal TeX commands and are not a measurement record. |
| 3 | Four positioning joints plus separate gripper described: base/shoulder/elbow MG996R, wrist/gripper SG90. | Conflicts with current firmware/URDF, which expose three positioning axes and a gripper. |
| 3 | Manual test protocol mentions 50–150 g spherical targets, electrical isolation, thermal behavior, stability. | A stated protocol/range, without tabulated trials or measured outcomes. Do not report 150 g as a certified payload. |
| 4 | Planned 16-step mission, including docking at about 18 cm, carry height about 80 mm. | Nominal design values, not measured stopping accuracy or achieved mission timing. |
| 4 | Apparatus table identifies Raspberry Pi 3B, 3S LiPo, separate 5 V logic / 6 V servo supply. | Reported revision; exact Pi model differs elsewhere. |
| 5 | Estimated total budget 34,850–59,000 BDT; incremental arm cost 8,000–15,500 BDT. | Historical cost estimate, not current supplier research or actual expenditure. |
| 6 | Conclusion says arm operated manually; roadmap includes calibration, IK, autonomous gripper triggers, unified mission state machine, and quantitative benchmarking. | Explicitly identifies uncompleted autonomy/measurement work. |

No raw experimental table, independent trajectory/range truth, repeated task
success counts, confidence intervals, detector test split, inference benchmark,
payload test log, or material classification dataset is supplied. No individual
author names are present in the extracted text.

### HazBot presentation

`proposal_resources/HazBot_Presentation.pptx.pdf` has a 2026-10-21 creation date.
Its title identifies HazBot as an autonomous hazardous material handling robot.
It supplies a useful application narrative and proposed mission sequence.

| Slide | Relevant content | Evidence interpretation |
| --- | --- | --- |
| 1–3 | Hazard handling concept; three functional layers and ROS 2 integration. | Design framing. The authors' newer four-subsystem Pi-centered description should guide the new architecture figure. |
| 2 | Incident/death/cost/response percentages. | Unsourced presentation statistics; omit unless independently verified from authoritative sources. |
| 5 | URDF/Gazebo/ros2_control/SLAM/Nav2 simulation pipeline. | Proposed pipeline; no simulation run log or model validation is provided. |
| 6 | LiPo distribution, Nano, RPLidar A1, OAK-D Lite, five servos. | Different proposed hardware revision from current source/exam report. Do not silently substitute it for the evidenced X4/CSI camera configuration. |
| 8 | RPLidar A1 and OAK-D Lite specifications. | Proposed component specifications, not tested robot performance. |
| 9–10 | SLAM and Nav2 architecture diagrams. | Desired navigation composition. Existing repository has SLAM Toolbox integration and reactive control; this slide does not establish a deployed Nav2 stack. |
| 12 | YOLO/depth fusion diagram and table showing acid vial 94%, bio bag 87%, fuel can 91%, safe container 78%, with distances. | Figure is explicitly headed **SIMULATED DETECTION OUTPUT**. These are illustrative values and must not become experimental results. |
| 13 | Confidence/proximity risk matrix. | Proposed decision policy. Detection confidence alone does not certify material identity, consequence severity, or safe handling. |
| 14–15 | Six-DOF, five-finger tendon hand; five MG996R servos; 500 g; response <200 ms. | Concept specification. Conflicts with current four-servo articulated arm source and has no supporting hardware test data. “kg·cm” describes torque, not grip force. |
| 16 | Detect→locate→navigate→align→grip→contain→confirm→return; 25–40 s cycle. | Useful mission concept; cycle time is unvalidated. |
| 17 | <50 ms detection, <100 ms replanning, <200 ms grip, 98% accuracy, 10 h battery. | Unsubstantiated performance assertions. No measurement method or dataset accompanies them; exclude from results. |
| 18 | Nuclear, biological, chemical, fire, mining, oil applications. | Motivating future application domains, not demonstrated deployments. |

Visually inspected slides 6, 12, and 15 confirm the power diagram, explicitly
simulated detection illustration, and proposed tendon hand. Their drawings are
concept graphics rather than photographs of an instrumented experiment. PDF
metadata names `ECE 21`, not an individual author; no individual names are in
the extracted slide text.

## Current implemented source mechanisms

| Subsystem | Source evidence | Defensible statement and limit |
| --- | --- | --- |
| Direct camera and native inference | `scripts/detect_live_picamera2.py:19–55,237–310,322–340` | Uses Picamera2, 640 × 480 capture, TFLite interpreter with two CPU threads. Source describes an INT8 YOLOv8 model. It loads an external file; no inference was executed here. |
| Detector class scope | `scripts/detect_live_picamera2.py:39–55` | Exactly two named classes: Tennis Ball and Cricket Ball. Confidence threshold 0.40; NMS IoU threshold 0.45. These settings are not detection accuracy. |
| Model artifact | `scripts/detect_live_picamera2.py:39,232–239` | Model expected at `~/ball_detector_pi/pi_inference/model_int8.tflite`; no `.tflite`, `.onnx`, or `.pt` weights were found in the inspected repository. Architecture/quantization/training quality cannot be independently verified from this path alone. |
| Camera–range association | `scripts/detect_live_picamera2.py:424–449` | Uses 62° nominal FOV, bbox center bearing, latest scan ±2° average, else known-ball-diameter pinhole fallback (0.067/0.072 m). This object-size fallback is ball-specific and cannot be transferred to arbitrary hazard containers without a size model. |
| LiDAR interface | `scripts/lidar_bridge.py:19–37,69–100` | CP2102 USB–UART interface, serial/TCP bridge, 115200 baud in this variant. The LiDAR's controller acquires ranges; SLAM/decision computation belongs to host software. No separate Arduino should be inserted into this branch. |
| Scan and mapping | `scripts/raw_lidar_publisher.py:52–145`; `src/soccer_slam/launch/soccer_slam_launch.py:34–142` | Alternatives include a custom 720-bin parser and vendor-driver SLAM Toolbox launch. Do not merge them into one simultaneously validated pipeline. |
| Wheel drive | `motor_control/motor_server.py:30–81`; `motor_control/soccer_bot_motor_driver.ino:8–42,98–148` | Pi gateway→USB serial→Arduino Uno→L298N→two DC wheels. This firmware uses serial 9600, PWM D5/D6 and direction D9–D12. |
| Encoder feedback | `motor_control/soccer_bot_motor_driver.ino:17–20,35–38` | Encoder pins are configured, but this firmware contains no pulse counters/interrupt handlers/velocity feedback loop. Do not claim demonstrated closed-loop wheel speed or encoder odometry from this variant. |
| Arm transport | `scripts/arm_server.py:19–49,63–80,113–130` | A separate CH340 USB–serial arm board, 115200 baud; arm server carries joint commands/status. Source describes Uno/Nano; exact fitted board is not independently established. |
| Arm channels | `scripts/arduino_arm_controller/arduino_arm_controller.ino:7–51` | Four servo channels: B/S/A/G on D9/D10/D11/D12; B/S/A command ranges 0–180, G 90–270 with 1000–2000 µs mapping. Logical labels do not prove measured joint excursions. |
| Firmware variants | `scripts/arduino_arm_controller.ino:27–32` | A second variant sets gripper minimum 115 and 1150–2000 µs. Deployment must freeze the actual flashed variant; do not combine calibration constants. |
| Arm pickup macro | `scripts/arm_server.py:394–405` | JSON `pickup` performs open→shoulder70/elbow80→close→lift using presets/delays. This is an operator-triggered pickup sequence, not perception-derived IK or a complete autonomous transport/place mission. |
| Arm kinematics | `scripts/robot.urdf:173–271` | Three positioning axes, a fixed wrist bracket, and two jaw joints. The two visual jaws represent a gripper, not two independently controlled positioning DOFs. |

Drive and arm use overlapping D9–D12 pins in **different firmware and serial
devices**. The architecture figure should show separate drive and arm Arduino
controllers rather than one shared board with conflicting pin assignments.
The LiDAR controller/interface is a third, sensor-specific embedded path.

The precise Pi model is unresolved: the engineering report and detector comments
say Pi 3B, whereas `docs/SOCCER_BOT_VERIFIED_CONFIGURATION.txt` says Pi 4. Use
“Raspberry Pi” in the manuscript pending confirmation. That configuration file
also contains private deployment information; do not copy it into figures,
anonymous manuscripts, or public packages.

## Arm geometry suitable for new offline analysis

The source URDF is a visual geometry model; its dimensions are model parameters,
not independently measured hardware dimensions. Relevant quantities are:

| Quantity | URDF value |
| --- | --- |
| Chassis box | 0.33 × 0.17 × 0.11 m |
| Wheel radius / width | 0.033 / 0.040 m |
| Wheel center y coordinates | ±0.105 m (modeled track 0.210 m) |
| Arm shoulder origin in `base_link` | (0.100, 0, 0.155) m |
| Shoulder→elbow and elbow→wrist lengths | 0.100 m each |
| Base yaw bound | [−1.5708, 1.5708] rad |
| Shoulder bound | [−0.5000, 2.6179] rad |
| Elbow bound | [−1.5708, 2.6179] rad |
| Wrist | fixed |
| Left/right jaw bound | [0, 0.8] rad, opposite z axes |

The initial upper link points along +z and the forearm along +x. Consequently,
with yaw q_b, shoulder q_s, elbow q_e, the fixed-wrist origin is

```
r = 0.10 sin(q_s) + 0.10 cos(q_s + q_e)
z_rel = 0.10 cos(q_s) - 0.10 sin(q_s + q_e)
x_base = 0.10 + r cos(q_b)
y_base = r sin(q_b)
z_base = 0.155 + z_rel
```

An offline sampling of this geometry can produce a reproducible workspace
envelope and pose examples. It must be labeled **URDF-derived geometric analysis**.
It excludes self-collision, motor torque, payload, compliance, cable routing,
ground collision, calibration, and tipping. The sum 0.20 m is an upper bound on
shoulder-to-wrist link reach, not a measured end-effector reach. Wrist-to-claw
geometry adds offsets, and the modeled joint limits are not calibrated servo
command transforms. Do not label sampled points as physically safe grasps.

## Consequences for manuscript and figure design

- Lead with a Pi-centered four-subsystem architecture and recognizable camera,
  LiDAR, controller, motor, and manipulator glyphs. Label physical interfaces
  (CSI, USB/serial, PWM, H-bridge) and distinguish sensor data from commands.
- Use hazardous-object retrieval as the application direction. The author-reported
  simulation object remains a ball; “any hazardous material”
  is not a validated class-generalization claim.
- Show the proposed mission with a distinct implementation-status legend.
  The preset pickup macro is implemented; integrated identify→navigate→grasp→
  contain→confirm autonomy is not established by the inspected evidence.
- Preserve previous offline behavioral evidence as software analysis. Fifteen
  passing checks do not imply fifteen successful robot missions or hazard trials.
- A proposed hazard-recognition extension requires explicit class labels and
  training/test data, calibrated localization, object-specific grasp constraints,
  and independent physical evaluation. Chemical identity cannot be inferred
  merely from a generic RGB object category or a confidence score.
- Do not import the slide's simulated detections, 98% accuracy, millisecond
  timings, 10 h runtime, 500 g payload, or 25–40 s cycle into an experimental
  results table. These can appear only as separately labeled future targets if
  their engineering rationale is supplied.

This assessment supplements the earlier `repository_audit.md`; the broader
mobile-manipulation framing supersedes its selected ball-chaser-only scope.
Its interface-contract, receipt-age, variant-composition, and evaluation limits
remain relevant. No runtime implementation was modified by this assessment.

## New source-derived analytical characterization

`../experiments/characterize_hazbot.py` now implements and executes the geometry
and interface analyses described above. It uses only the Python standard
library. It does not import runtime modules. The exact motor `SET:` branch is
AST-extracted with its sender replaced by a list append; the pure arm angle
mapper is separately extracted. The full robot servers and their startup code
are never executed.

| Computed quantity | Result | Meaning |
| --- | --- | --- |
| Deterministic joint grid | 41 × 41 × 41 = 68,921 poses | Uniform samples in declared joint coordinates, including bounds; not uniform Cartesian volume. |
| Ideal shoulder-to-wrist link bound | 0.200 m | Sum of modeled 0.100 m links; attained at a permitted collinear special pose. |
| Sampled wrist z in `base_link` | −0.031598 to 0.354896 m | Model envelope includes below-ground configurations; not feasible task reach. |
| Samples below modeled z = 0 plane | 2,747; 66,174 on/above plane | A simple geometric flag; on/above does not imply collision-free or stable. |
| Independent FK agreement | 1,013 poses, maximum difference 6.8 × 10⁻¹⁷ m | General URDF homogeneous transforms versus independent closed-form formula; numerical implementation agreement, not physical accuracy. |
| Exhaustive wheel-pair inputs | 511² = 261,121 | All integer command values −255…255 for each wheel; no motors actuated. |
| Inputs per F/B/L/R output | 65,025 each | Nonzero sign quadrants collapse to four direction commands; magnitude information is discarded. |
| All-zero / mixed-zero pairs | 1 stop / 1,020 no-command pairs | One stationary wheel plus one nonzero wheel emits no new `SET:` branch command in this gateway. |
| Arm map evaluations | 2,255 | B/S/A/E/G aliases × 451 inputs −90…360; four physical servo channels, with E an A alias. |
| Current named visual classes | 2 | Tennis Ball, Cricket Ball; no hazard-class validation. |
| Internal analytical/source checks | 29 passed | Chain recognition, joint-bound checks, FK, reach invariants, exhaustive sign partition, arm mapping, source schema. |

Wrist samples are in `../data/hazbot_workspace.csv`; the smaller protocol and
height-slab datasets are `hazbot_protocol.csv` and `hazbot_height_slabs.csv`.
`hazbot_characterization.json` records ten source SHA256 bindings (including
the generator), three dataset hashes, exact computation settings, results,
and all 29 checks. Height slabs have ±0.010 m half-width and should not be
presented as exact continuous planar workspace intersections.

Reproduce from the repository root:

```sh
python3 manuscript/experiments/characterize_hazbot.py
python3 manuscript/experiments/characterize_hazbot.py --output-dir /tmp/hazbot-characterization-repeat
```

An independent read-back check confirmed all four primary outputs were byte
identical across repeat generation; all ten source and three dataset hashes
matched; CSV counts matched JSON; eight CSV poses agreed with a separately
written matrix-chain calculation within 2 × 10⁻¹² m after decimal CSV rounding.
Those results support reproducible source-model analysis. They add no claim of
physical payload, safe hazard handling, detection accuracy, mission success,
runtime latency, or collision-free autonomy.

## Added prototype photograph

The author supplied photo/bot.jpeg during the acknowledgment/figure revision. It shows a physical mobile base, articulated linkage, gripper enclosing a red ball surrogate, servo hardware, display, scanner assembly, wheel pair, battery cells, and lower electronics. The original JPEG is preserved; the annotation renderer records its hash and exact callout anchors. The author confirmed that the screen is mounted directly to the Raspberry Pi through GPIO and that the camera is at the end of the white ribbon emerging from that assembly. These assembly identifications are recorded in the callout provenance. A static photograph documents assembly and visible arrangement, not a timed or independently verified autonomous mission, hazard recognition, or material handling result.
