# MIDD-IOT — GDSS-003
## Governed Dynamic Simulation Runtime Foundation
### Invariants v0.1

**Version:** `v0.1`
**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `IMPLEMENTED_BY_MIDD-GDSS-P008-R2`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Alembic baseline:** `0040`

Statuses below are backed by the individually named executable cases in
`tests/unit/gdss-simulation.invariants.test.ts`, reinforced by the runtime, adversarial and real
PostgreSQL suites. Documentation alone is not treated as evidence.

| ID | Statement | Rationale | Planned enforcement | Planned verification | Status |
|---|---|---|---|---|---|
| GDS3-INV-01 | A run binds one exact SystemModelVersion. | Historical identity. | exact ID/hash manifest | cross-version negatives | PASS |
| GDS3-INV-02 | Simulation time differs from wall/observation/device time. | No hidden reality claim. | temporal contract | clock/import inspection | PASS |
| GDS3-INV-03 | Every state has exactly one explicit initial condition. | No hidden defaults. | preflight cardinality | missing/duplicate cases | PASS |
| GDS3-INV-04 | STATE, RATE, ALGEBRAIC and PARAMETER are distinct. | Unambiguous execution. | closed binding schema | role matrix | PASS |
| GDS3-INV-05 | Dynamic roles are never inferred from syntax or names. | Syntax is not meaning. | explicit mappings only | misleading-name fixtures | PASS |
| GDS3-INV-06 | Rate dimension equals state dimension divided by TIME. | Valid integration. | preflight with explicit `GDSS_UNIT_CONVERSION_V2` / `second@1` | compatible/mismatch cases | PASS |
| GDS3-INV-07 | Solver identity/version are explicit. | Reproducibility. | closed registry | missing/spoofed versions | PASS |
| GDS3-INV-08 | Temporal configuration is explicit and hashed. | Reproducibility. | strict manifest | changed-field hashes | PASS |
| GDS3-INV-09 | No implicit timestep exists. | No hidden semantics. | required positive step | omitted/invalid step | PASS |
| GDS3-INV-10 | Equal governed deterministic inputs yield equal trajectory identity. | Determinism. | canonical execution/hash | repeated golden runs | PASS |
| GDS3-INV-11 | All rates in a step share one pre-step snapshot. | Simultaneous Euler. | immutable snapshot/candidate map | coupled-state fixture | PASS |
| GDS3-INV-12 | Algebraic loops are not temporal feedback. | No implicit solver. | SCC rejection | algebraic vs state loop | PASS |
| GDS3-INV-13 | Every trajectory output is SIMULATED. | Epistemic integrity. | constant output classification | contract assertions | PASS |
| GDS3-INV-14 | Simulation output is not automatically PREDICTED. | No reality claim. | closed result schema | forbidden status tests | PASS |
| GDS3-INV-15 | Solver success does not imply scientific validity. | Separate evidence layers. | no validity promotion | schema/source inspection | PASS |
| GDS3-INV-16 | Observed initial provenance does not propagate to outputs. | Preserve provenance boundary. | input/output classifications | observed-input fixture | PASS |
| GDS3-INV-17 | Runtime performs no implicit telemetry retrieval. | Explicit inputs only. | capability-free core | import and missing-input tests | PASS |
| GDS3-INV-18 | Runtime performs no MQTT operation. | Operational isolation. | forbidden dependency | import graph | PASS |
| GDS3-INV-19 | Runtime performs no Control Engine operation. | Domain isolation. | separate namespace/module | dependency scan | PASS |
| GDS3-INV-20 | Runtime performs no DTE operation. | Domain isolation. | forbidden dependency | dependency scan | PASS |
| GDS3-INV-21 | Simulation confers zero physical authority. | Safety. | `physicalAuthority: NONE` | closed output assertions | PASS |
| GDS3-INV-22 | Simulation cannot create/authorize actuation artifacts. | M7 separation. | no ports/dependencies | negative integration | PASS |
| GDS3-INV-23 | Every run is resource bounded. | Availability. | versioned finite profile/counters | all boundary categories | PASS |
| GDS3-INV-24 | Non-finite state/rate/intermediate fails closed. | Numeric safety. | finite guards | NaN/Infinity/overflow | PASS |
| GDS3-INV-25 | Incomplete simulation is never complete. | Honest evidence. | status/completeness invariant | injected failures | PASS |
| GDS3-INV-26 | Persisted completed/failed attempts are immutable. | Historical evidence. | append-only DB/artifact guards | SQL mutation negatives | PASS |
| GDS3-INV-27 | Model changes never change an existing execution. | Historical identity. | snapshot/hash binding | successor isolation | PASS |
| GDS3-INV-28 | Solver semantic changes require a new version. | Reproducibility. | version registry governance | version golden vectors | PASS |
| GDS3-INV-29 | Input identity differs from result identity. | Separate cause/evidence. | domain-separated hashes | hash sensitivity tests | PASS |
| GDS3-INV-30 | Forrester semantics are not universal GDSS ontology. | Domain neutrality. | package boundary | vocabulary/import scan | PASS |
| GDS3-INV-31 | GDSSSimulationExecution is not an Experiment. | Governance separation. | distinct contracts | no experiment fields/ports | PASS |
| GDS3-INV-32 | A run is not a Digital Shadow or Digital Twin. | No physical linkage claim. | no sync/asset identity | boundary inspection | PASS |
| GDS3-INV-33 | Constraint violation is never silently corrected. | Explainability. | v1 FAIL_RUN policy | negative-state fixture | PASS |
| GDS3-INV-34 | Dynamic feedback differs from instantaneous cycles. | Correct temporal semantics. | snapshot boundary plus SCC | paired fixtures | PASS |
| GDS3-INV-35 | Simulation leaves GDSS-002/model identities unchanged. | Layer integrity. | read-only snapshots/separate hashes | before/after hashes | PASS |
| GDS3-INV-36 | GDSS execution identity differs from Control replay identity. | Collision safety. | GDSS namespace/no FK | schema/service inspection | PASS |
| GDS3-INV-37 | DynamicModelBinding never alters GDSS content_hash. | Non-retrofit contract. | separate persisted aggregate | mutation/hash snapshots | PASS |
| GDS3-INV-38 | step_index is authoritative temporal ordering. | Stable time identity. | integer primary sequence | drift/order fixtures | PASS |
| GDS3-INV-39 | Trajectory order never depends on DB/object order. | Determinism. | sorted canonical serialization | permutation tests | PASS |
| GDS3-INV-40 | Attempt identity differs from computational identity. | Audit without nondeterminism. | UUID outside hashes | repeated equal inputs | PASS |

## Reserved future semantics

Adaptive solvers, algebraic-loop solvers, stochastic seeds, events, hybrid systems, calibration,
prediction, experiment comparison and Forrester-specific validation require new versioned contracts.
Their absence is an explicit boundary, not a claim of implementation.
