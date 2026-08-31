# Experiment batch orchestration

M6.5 transforms an explicit, immutable subset of M6.4 candidates into isolated M5 simulation sessions and runs. A batch is not a ranking, policy, recommendation, optimizer, or actuator.

Creation requires a project-scoped M6.4 search space and a complete READY M5 simulation session. Candidate membership is selected explicitly (or all candidates), ordered by the original candidate index, persisted transactionally, and immutable thereafter. A batch is limited to 100 items. Its semantic hash includes project, search-space hash, ordered candidate hashes, frozen base experiment fingerprint, optional evaluation profile/version, schema and orchestrator versions—not descriptive metadata.

Starting a batch is sequential in v1. For every pending item, `candidateToExperimentConfiguration()` creates a new frozen READY session by copying the base experiment context and replacing only controller parameters with the immutable candidate parameters. It then uses the existing `simulation-replay-runner` to produce a run, result and trace. With an evaluation profile, M6.2 evaluation is materialized and linked; `NOT_EVALUABLE` is a warning, not an execution failure.

Items have independent lifecycle states. A failed item does not stop later items; the aggregate becomes `PARTIALLY_FAILED` when at least one item succeeded. Repeating `start` never claims terminal items. Retrying resets only failed items, preserves candidate/session provenance and increments the attempt count. This v1 is sequential and bounded, with no automatic recovery of an interrupted RUNNING item; an operational recovery policy can be introduced with a durable worker lease in a later phase.

APIs are project-scoped under `/api/control/experiments/projects/:projectId/batches`; reads require `view_dashboard`, create/start/retry require `edit_policies`. Batch creation and start are audited. The only execution context is `SIMULATION`; physical effects, outbox, operational transport and actuation remain disabled.
