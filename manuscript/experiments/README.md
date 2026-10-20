# Reproducible command replay

Run from the repository root:

```sh
python3 manuscript/experiments/replay_supervisor.py
```

The standard-library-only experiment executes the original metric controller
callbacks and decision loop with memory-only ROS/time/output doubles. Its
constructor and socket transport are bypassed. It never operates the robot.

The output gate is a proposed reference that is not integrated into the runtime
nodes. Read [the protocol](../research/evaluation_protocol.md) for the exact
constructed inputs, contract, metrics, limitations, source hashes, and expected
results. `--check-only` runs all checks without rewriting artifacts.

Generated data live in `../data/`; LaTeX tables live in `../generated/`. `T`
counts any constrained motion (including rotation), `F` counts constrained
forward commands, and `H` counts held clear-scene forward opportunities. These
are deterministic scenario counts, not empirical robot failure rates.
