# HazBot contribution and validation roadmap

Active plan, 21 October 2026. The previous ball-pursuit plan is preserved in the dated archive.

## Present contribution

HazBot contributes a source-traceable integration and verification study connecting four embedded subsystems to retrieval-phase handoffs, actual actuator-gateway semantics, and modeled wrist geometry. The concrete results are the exact mixed-zero command omission/magnitude reduction, reproducible geometric constraints relevant to docking, and bounded reference-command guard sensitivity. Do not claim the first Pi robot, first mobile manipulator, new general safety architecture, or demonstrated universal hazard recognition.

The paper is an engineering architecture and characterization study. Its formal scope is command admissibility and existential phase reachability in a seven-phase/twelve-Boolean reference model. Zero reference violations is conformance within this abstraction, not proof of physical safety. All actions are exercised by a constructed nominal witness, so the full policy is not simply an always-HOLD controller.

## Position against prior work

Vega motivates environment-specific hazardous-area engineering; Stretch establishes compact mobile manipulation; HomeRobot connects navigation/recognition/grasp/place and separates simulation from physical evaluation. ROS 2, Nav2 and SLAM Toolbox are established middleware/navigation components. twist_mux and Collision Monitor already implement important forms of authority arbitration and sensor-dependent stopping. These precedents delimit the contribution to this explicit implementation-grounded integration study.

## Next studies and the evidence they need

| Study | Question and comparison | Required measurements |
|---|---|---|
| Concrete command path | Does a magnitude-preserving gateway improve approach/docking over current direction primitives? | Frozen firmware and gateway, encoder/pose calibration, paired physical path logs, stopping distribution, command receipts |
| Dock-to-grasp interface | Does calibrated contact reach reduce failed pickups compared with a fixed stop threshold? | Camera/LiDAR/arm extrinsics, calibrated TCP, object pose/contact ground truth, geometry/collision constraints, paired pickup runs |
| Observation realization | How reliably can stopped-base, stow, grip and release be asserted? | Feedback definitions, timestamps, false positives/negatives, injected faults, independent observations |
| Task-specific recognition | Can designated application objects be localized under expected visual conditions? | Named classes, training/validation/test split, held-out illumination/background/object instances, localization and confidence calibration |
| Mission benchmark | Can complete search-to-deposit missions be repeated? | Frozen hardware/software, environment/map/object layout, independent full-task success criteria, stage timings, aborts, contact and navigation failures |
| Application qualification | Which designated objects and environments are supported? | Object-specific handling, containment, compatibility, load/stability and environmental tests appropriate to the intended application |

Nonhazardous surrogates can support the initial physical mission benchmark. Transfer must be assessed for a named application and object set rather than assumed from ball control. Material identity requires suitable evidence independent of generic visual labels.

Future studies need their own literature review, meaningful baselines, predefined metrics and retained failure cases. No projected accuracy, payload, time, endurance, percentage improvement or acceptance outcome is a present result. The source gateway findings should be resolved before interpreting nominal body-velocity requests as physical robot motion.
