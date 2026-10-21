# HazBot related-work map

Active paper: HazBot: An Embedded Mobile Manipulation Architecture for Hazardous-Object Retrieval.

The detailed primary-source review and verified metadata are in [hazbot_literature.md](hazbot_literature.md). The main bibliography currently cites nine entries:

| BibTeX key | Relevance | Boundary |
|---|---|---|
| bird2022vega | Hazardous-environment ground robotics | Its nuclear-environment engineering does not qualify HazBot |
| kemp2022stretch | Compact mobile manipulation and reach/design analysis | Different mechanics and physical validation |
| yenamandra2023homerobot | Full navigation-to-placement task; simulation/real evaluation split | No transfer of recognition or mission capability |
| macenski2022ros2 | Distributed robotics middleware | Middleware availability is not application success |
| macenski2020marathon2 | Established navigation orchestration | No borrowed localization or obstacle-avoidance score |
| macenski2021slamtoolbox | Established mapping component | Map performance requires local measurement |
| alqahtani2026edge | Model/device inference tradeoffs | No borrowed timing/energy/accuracy for native detector |
| twistmux | Command authority, priority and timeout precedent | Guarding/arbitration are established techniques |
| nav2collision | Sensor-dependent command monitoring precedent | No new general collision monitor is claimed |

Primary source links are retained in references.bib. Source inspection establishes the current native detector as an INT8 TFLite path with tennis/cricket-ball labels; generic MobileNet/SSD citations are not presented as its implemented architecture. The bibliography candidate file retains those entries only as unused alternatives.

The contribution is the explicit connection among source-specific gateway behavior, wrist geometry and mission handoffs in a Pi-centered four-subsystem design. The paper separates this engineering study from physical hazardous-object recognition or handling. Historical soccer/replay literature and audit notes remain in the dated previous-project archive rather than setting the new paper's narrative.
