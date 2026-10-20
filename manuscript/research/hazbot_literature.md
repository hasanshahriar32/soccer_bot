# HazBot: research framing and primary literature

Research checked on **21 October 2026**. This note reframes the platform as a Raspberry Pi-centered mobile manipulator. It is a targeted primary-source review, not an exhaustive systematic review. The companion `hazbot_references.bib` contains the verified candidate references; the main bibliography can select the entries that fit the final paper.

## Recommended title and contribution

**HazBot: A Raspberry Pi-Centered Modular Mobile Manipulator Toward Hazardous-Object Retrieval**

The title identifies the actual platform and application trajectory. “Toward” preserves the distinction between a modular prototype with a ball surrogate and a robot whose hazardous-object recognition and retrieval have been validated. An application-led title using “for Hazardous-Object Retrieval” is also reasonable if the abstract immediately identifies the study as a ball-based surrogate simulation and states the actual evaluation boundary.

The engineering contribution is the integration of four explicit subsystems around a common compute hub: navigation through a LiDAR's embedded scan electronics; wheel actuation through an Arduino and motor driver; direct camera acquisition and native visual inference; and robotic-arm actuation through an Arduino. The paper should trace physical interfaces, observation semantics, command authority, and the transition between mobile approach and manipulation. This is more informative than describing a generic perception–decision–action pipeline.

The defensible research gap is **reproducible integration and bounded verification on this particular resource-constrained architecture**. Published mobile manipulators and hazardous-environment robots already combine mobility, sensing, computing, and manipulation. A Raspberry Pi, Arduino, ROS 2, or four-way subsystem decomposition alone does not establish a new robotics algorithm. The available evidence can instead support:

1. A concrete four-subsystem hardware/software architecture, including the intermediate controllers and actual data/control paths.
2. A specified mission lifecycle and handoff contract: acquire a target, estimate a usable pose, approach, stop the base, grasp, carry, deposit, and recover or abort when prerequisites are unavailable.
3. A reproducible software assessment of command freshness, message compatibility, and fault responses. Existing offline replay results remain command-level evidence, separate from physical pick-and-place or hazardous-material trials.

The paper's research question can be: **How can a resource-constrained mobile manipulator coordinate sensing, mobility, and manipulation through explicit interfaces and observable mission prerequisites?** A stronger empirical paper additionally needs timestamped physical mission trials, grasp/placement outcomes, calibrated localization, and native-inference timing.

## Evidence boundaries from the supplied resources

`proposal_resources/Autonomous-Mobile-Manipulator-Engineering-Exam-Report.pdf` explicitly reports a current mobile-base/sensor infrastructure, a **4-DOF arm under integration**, and **manual pick-and-place**, with full autonomous sequencing as a development target. It names Raspberry Pi 3B, Pi Camera V2, YDLIDAR X4, Arduino Uno, and L298N. The presentation names different camera/LiDAR hardware and alternates between 4-DOF and 6-DOF descriptions. Those cannot all be silently combined into one measured configuration.

The user's current architecture clarification takes precedence for the intended system organization. Hardware identities and controller sharing should still be stated only as specifically as the evidence permits. If two functions use an Arduino pathway, do not draw two separate boards unless two physical controllers are confirmed.

The presentation's percentages, inference/grip latencies, battery endurance, incident totals, and hazard-risk matrix are not accompanied by datasets or experimental logs. Use the resources for concept and configuration provenance, not as empirical measurements. The user's latest clarification describes **ball-control simulation**, with no hazardous materials available for trials. Present this as a **nonhazardous surrogate simulation**, not a physical hazardous-material demonstration. Report any newly constructed offline experiments under their actual software abstraction and inputs.

Visual object detection returns a class label, bounding box, and score according to the trained categories. A visible container or label can identify a candidate item for retrieval; it does not establish unknown chemical composition, contamination, radioactivity, biological activity, or safe handling conditions. In this paper, **hazardous-object retrieval is the application goal; verified hazardous-material identification is an additional sensing and validation problem**. Avoid “recognizes any hazardous material.”

## Closest prior systems and what they imply

| Key | Primary source and verified scope | Implication for HazBot |
| --- | --- | --- |
| `bird2022vega` | [Vega, Journal of Field Robotics](https://doi.org/10.1002/rob.22048): small ground robot for nuclear characterization and sample retrieval; includes a small manipulator and environment-specific engineering. | Closest application/platform comparison. Hazard-oriented low-cost mobile robotics is established; HazBot has not inherited Vega's environmental qualification. |
| `kemp2022stretch` | [Stretch, ICRA](https://arxiv.org/abs/2109.10892): compact differential-drive manipulator, mechanical/stability reasoning, home tasks under teleoperation and autonomous control. | Integration and manipulation need physical workspace and stability evidence, not only a software diagram. |
| `yenamandra2023homerobot` | [HomeRobot, CoRL](https://proceedings.mlr.press/v229/yenamandra23a.html): navigation, perception, grasping, placement, and a reproducible simulation/physical platform. | Demonstrates that mobile retrieval is a multi-stage systems problem. Its open-vocabulary capability is not a capability demonstrated by HazBot. |
| `jo2022smartmbot` | [SMARTmBOT author preprint](https://arxiv.org/abs/2203.08903): modular, inexpensive ROS 2 mobile platform with navigation experiments and open hardware/software. | Modularity, affordability, and ROS 2 do not alone differentiate a new platform. This source is a preprint; do not label it an accepted IROS paper. |

## Navigation, perception, and coordination sources

| Key | Primary source | Appropriate use |
| --- | --- | --- |
| `macenski2022ros2` | [ROS 2 architecture paper](https://arxiv.org/abs/2211.07752) | Explain modular communication and lifecycle foundations; a middleware citation does not demonstrate the deployment topology or timing of this robot. |
| `macenski2020marathon2` | [Nav2 paper](https://arxiv.org/abs/2003.00368) | Cite navigation/task orchestration. Do not say Nav2 is experimentally validated here merely because configuration files exist. |
| `macenski2021slamtoolbox` | [SLAM Toolbox, JOSS](https://joss.theoj.org/papers/10.21105/joss.02783) | Cite the mapping/localization component. A driver publishing scans is not itself localization or mapping accuracy evidence. |
| `sandler2018mobilenetv2` | [MobileNetV2, CVPR](https://openaccess.thecvf.com/content_cvpr_2018/html/Sandler_MobileNetV2_Inverted_Residuals_CVPR_2018_paper.html) | Cite lightweight neural inference/SSDLite only if the detector choice is actually implemented or clearly labeled as a candidate. |
| `liu2016ssd` | [SSD, authors' research page](https://research.google/pubs/ssd-single-shot-multibox-detector/) | Cite the detector family where applicable. A generic object detector does not identify hazardous substance properties. |
| `alqahtani2026edge` | [Edge-detector benchmark, version 3](https://arxiv.org/html/2409.16808v3) | Support evaluating accuracy, latency, and energy jointly for native edge inference. Results depend on model/device/runtime; measure HazBot separately. |
| `nav2collision` | [Official Collision Monitor documentation](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/) | Existing sensor stop/slow rules and source timeouts are direct prior art for the reference supervisor. The documentation expressly does not confer hard real-time safety certification. |
| `twistmux` | [Official priority/timeout configuration](https://github.com/ros-teleop/twist_mux/blob/rolling/config/twist_mux_topics.yaml) | Existing command arbitration. A multiplexer cannot control an actuator command path that bypasses it. |

The main paper can usually fit 9–11 of these references by omitting an unused detector family or the SMARTmBOT preprint. Keep prior-art coverage focused on mobile manipulation, the intended hazardous-object application, and the actual methods. Soccer-specific citations need not remain unless the platform's development history is substantively discussed.

## Suggested related-work passage

Mobile manipulation combines platform motion with object-level interaction. Stretch demonstrates a compact manipulator with an explicit relationship between mechanical reach and mobile-base stability, while HomeRobot evaluates the integration of navigation, perception, grasping, and placement [Stretch; HomeRobot]. Vega provides a closer hazardous-environment comparison through a small ground robot designed for inspection, characterization, and sample retrieval [Vega]. These systems establish the platform category; HazBot examines an inexpensive four-subsystem implementation centered on a Raspberry Pi.

ROS 2, Nav2, and SLAM Toolbox supply established communication, navigation, and mapping building blocks [ROS 2; Marathon 2; SLAM Toolbox]. Native detector deployment also involves a model–device tradeoff rather than a blanket real-time guarantee [edge benchmark]. The present study therefore emphasizes interface definition, mission prerequisites, and reproducible command-level verification. It does not claim a new generic navigation, detection, or grasp-planning algorithm.

## Metadata checks and citation details

- **Vega**: issue date **2022**, volume **39**, number **3**, pages **232–245**, DOI **10.1002/rob.22048**. First online publication was 25 November 2021. The publisher's issue citation uses 2022. Correct author spelling is **Jim Hayman**.
- **Stretch**: published ICRA **2022**, pages **3150–3157**, DOI **10.1109/ICRA46639.2022.9811922**. The original preprint was deposited in 2021. Page range was checked against publisher-deposited Crossref metadata, not guessed from the preprint.
- **HomeRobot**: CoRL **2023**, PMLR **229**, pages **1975–2011**. Use the publisher's year and author list; no DOI is invented.
- **Marathon 2**: IROS **2020**, pages **2718–2725**, DOI **10.1109/IROS45743.2020.9341207**. Author preprint and Crossref metadata agree on title and venue.
- **SLAM Toolbox**: JOSS **6(61):2783**, **2021**, DOI **10.21105/joss.02783**.
- **MobileNetV2**: CVPR **2018**, pages **4510–4520**, DOI **10.1109/CVPR.2018.00474**; author list and page range checked against the official CVF record.
- **SSD**: ECCV **2016**, pages **21–37**, DOI **10.1007/978-3-319-46448-0_2**; author page and publisher-deposited metadata checked.
- **Edge benchmark**: the current **v3 (14 July 2026)** has the title **A Comprehensive Evaluation of Deep Learning Object Detection Models on Heterogeneous Edge Devices** and **four authors**: Daghash K. Alqahtani, Muhammad Aamir Cheema, Maria A. Rodriguez, Adel N. Toosi. Older indexed results retain the earlier three-author title. The candidate reference pins v3 and identifies it as an arXiv preprint.
- **ROS 2** retains the existing verified Science Robotics citation, **7(66):eabm6074**, **2022**, DOI **10.1126/scirobotics.abm6074**.
- Software documentation is mutable and is cited with the **21 October 2026** access date. The failed old Jazzy documentation URL is not used; rolling documentation supports general prior-art statements, not exact-version availability claims.

Primary article landing pages/author abstracts were inspected for all listed papers. Full text was additionally inspected for Vega, SLAM Toolbox, and the edge benchmark. HomeRobot's publisher PDF exceeded the web reader's size limit; its publisher abstract, bibliographic entry, and author list were inspected. No secondary news or autogenerated research-summary site is used as evidence.
