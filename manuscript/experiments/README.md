# HazBot reproducible analyses

Run from the repository root:

```bash
python3 manuscript/experiments/characterize_hazbot.py
python3 manuscript/experiments/verify_hazbot_mission.py
```

Both use the Python standard library and operate offline. Neither imports the runtime servers, starts ROS, opens sockets or serial ports, loads detector weights, or actuates hardware.

characterize_hazbot.py derives wrist geometry from scripts/robot.urdf, compares analytic FK with a generic homogeneous chain, samples the declared joint bounds, executes the AST-isolated wheel SET branch, and checks the pure arm command mapper. Outputs are hazbot_characterization.json, hazbot_workspace.csv, hazbot_protocol.csv, and hazbot_height_slabs.csv. Its 29 checks establish model/source consistency, not physical accuracy.

verify_hazbot_mission.py defines a new seven-phase reference coordinator, independently checks command admissibility, enumerates all 12-bit observations at every phase for four policies, explores phase reachability, and emits counterexamples and a nominal Boolean witness. Its 109 checks cover the declared abstraction. The full 28,672-case policy has no violating commands; the three guard-removal ablations expose 480, 128, and 288 violating cases. This is not a dynamics or sensor simulation.

The verifier regenerates generated/hazbot_mission_summary.tex from its computed values. Both scripts accept --output-dir to reproduce artifacts in a separate folder. The verifier optionally accepts --generated-dir. A custom output directory defaults to keeping its TeX output under that directory, leaving the active paper summary prose unchanged.

See the [active protocol](../research/evaluation_protocol.md), [mission method](../research/hazbot_mission_method.md), and [claim ledger](../research/claim_evidence.csv). Source and dataset hashes are recorded alongside settings and checks.

The original replay_supervisor.py remains an independent historical supporting experiment. Its 15 behavioral checks concern constructed ball-pursuit command traces and are not counted as HazBot mission trials:

```bash
python3 manuscript/experiments/replay_supervisor.py --check-only
```
