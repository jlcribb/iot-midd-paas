# GDSS-004 — Architecture Decision Record

Status: `PROPOSED`
Package: `MIDD-GDSS-P010`
Baseline: `10d454e985f904228c5b62dd5cb12c6b2171e6d2` / Alembic `0041`
Implementation: `NOT_AUTHORIZED`

## Context

GDSS-003 owns one governed deterministic simulation execution, its canonical trajectory and its
immutable terminal result. GDSS-004 adds a governed experiment: a versioned design whose complete,
finite scenario universe is materialized before any scenario is dispatched, and whose evidence is
derived from exact GDSS-003 results.

An experiment is not a batch convenience API. It distinguishes design, materialization, execution,
trajectory-local measurement, comparison and finding. All output remains computational evidence
about a model under declared assumptions.

## Decision

Adopt `GDSS_EXPERIMENT_V1` with these architectural decisions:

1. `Experiment`, `Scenario`, `ExperimentExecution` and GDSS-003 simulation execution are distinct
   identities.
2. A published immutable `ExperimentVersion` binds one exact base GDSS-003 simulation manifest,
   factors, controlled inputs, metrics, comparisons, completeness policy and semantic versions.
3. V1 expansion is a finite Cartesian product under `GDSS_EXPERIMENT_EXPANSION_V1`.
4. The complete ordered materialized scenario set and execution manifest are committed before any
   GDSS-003 dispatch.
5. Every materialized scenario binds its exact scenario hash and the fully materialized GDSS-003
   input manifest. A scenario execution references, but never owns, GDSS-003 evidence.
6. Metrics operate through `GovernedTrajectoryReader` over verified canonical GDSS-003 artifacts.
   They do not copy or reinterpret trajectory authority.
7. Trajectory metrics and cross-scenario comparisons use separate closed versioned vocabularies.
8. Comparison eligibility is explicit. Missing or incompatible evidence produces `INELIGIBLE`, not
   omission.
9. Experiment orchestration uses local PostgreSQL transactions around experiment evidence and
   independent idempotent GDSS-003 commits. There is no distributed transaction fiction.
10. Experiment evidence is append-only. One `RUNNING` event is followed by exactly one immutable
    terminal event.
11. Actor, time, worker and retry data are audit/operational metadata and do not influence semantic
    hashes.
12. `RUN_EXPERIMENT` is distinct from `RUN_SIMULATION`, publication and abort authority.
13. V1 accepts no user-supplied executable code, adaptive search, optimization or calibration.
14. `GDSS_EXPERIMENT_LIMITS_V1` is independent of expression and simulation limits; exact numeric
    values require the Implementation Plan and benchmark evidence.
15. Migration architecture decision: `0042_LIKELY_REQUIRED`. This ADR does not authorize or create
    migration `0042`.

## Normative boundaries

```text
EXPERIMENT != SIMULATION_EXECUTION
SCENARIO != SIMULATION_EXECUTION
TRAJECTORY_METRIC != COMPARISON_OPERATION
COMPARATIVE_FINDING != EMPIRICAL_FINDING
COMPARATIVE_FINDING != PREDICTION
COMPARATIVE_FINDING != RECOMMENDATION
PARAMETER_SWEEP != CALIBRATION
PARAMETER_SWEEP != OPTIMIZATION
EXPERIMENT != DIGITAL_TWIN
EXPERIMENT != CONTROL_POLICY
```

`VALIDATED` means structurally valid, computationally coherent, bounded and expandable. It never
means empirically or scientifically validated. `PUBLISHED` means governance-authorized
computational design, not scientific truth or operational recommendation.

## Ownership

```text
GDSS-003 owns:
  simulation attempt and terminal state
  simulation input/result hashes
  canonical trajectory bytes and trajectory hash

GDSS-004 owns:
  experiment design and scenario expansion
  ordered materialized scenario manifest
  scenario-to-GDSS-003 evidence mapping
  metric, comparison and comparative-finding evidence
  experiment execution state and canonical result artifact
```

GDSS-004 artifacts may contain GDSS-003 hashes and immutable references. They must not embed the
canonical trajectory payload.

## Lifecycle

```text
DRAFT -> VALIDATED -> PUBLISHED -> DEPRECATED
```

Only `DRAFT` content is editable. Validation freezes an exact candidate. Only `PUBLISHED` versions
are executable. `VALIDATED`, `PUBLISHED` and `DEPRECATED` content is immutable; changes require a
successor DRAFT version. Existing executions remain bound to their historical version.

## Execution states

```text
RUNNING
  -> COMPLETED
  -> COMPLETED_WITH_FAILURES
  -> FAILED
  -> ABORTED
```

- `COMPLETED`: all required scenarios and required metric/comparison evidence succeeded.
- `COMPLETED_WITH_FAILURES`: orchestration ended, failures remain explicit, and the published
  `ALLOW_PARTIAL_EXPLICIT` policy permits a coherent partial result.
- `FAILED`: the applicable completeness policy cannot yield a valid governed result, or foundational
  evidence is invalid.
- `ABORTED`: an authorized request stopped future dispatch. All committed evidence is retained.

No terminal state can be replaced or followed by another execution event.

## Authorization decision

Logical capabilities are `READ_EXPERIMENT`, `CREATE_EXPERIMENT`, `VALIDATE_EXPERIMENT`,
`PUBLISH_EXPERIMENT`, `RUN_EXPERIMENT`, `DEPRECATE_EXPERIMENT` and `ABORT_EXPERIMENT`.

Proposed project-role mapping:

| Capability | viewer | operator | admin |
|---|---:|---:|---:|
| READ_EXPERIMENT | yes | yes | yes |
| CREATE_EXPERIMENT | no | yes | yes |
| VALIDATE_EXPERIMENT | no | yes | yes |
| PUBLISH_EXPERIMENT | no | no | yes |
| RUN_EXPERIMENT | no | yes | yes |
| DEPRECATE_EXPERIMENT | no | no | yes |
| ABORT_EXPERIMENT | no | no | yes |

All authorization requires an OAuth session and exact project scope. There is no header fallback,
implicit global authority or inheritance from `RUN_SIMULATION`.

## Strategic finding resolution index

| Finding | Architectural resolution | Normative document | Status |
|---|---|---|---|
| F-01 | Metrics are trajectory-local; deltas are explicit comparison operations. | Metrics and Comparison | RESOLVED |
| F-02 | Every metric/comparison has exact discrete, finite, unit-aware v1 mathematics. | Metrics and Comparison | RESOLVED |
| F-03 | Complete ordered scenarios and manifest commit before dispatch. | Experiment Design; Execution and Persistence | RESOLVED |
| F-04 | Closed relevant-input universe, expected-value check and controlled-input proof. | Contracts; Experiment Design | RESOLVED |
| F-05 | Metric-specific conservative temporal compatibility with no normalization. | Metrics and Comparison | RESOLVED |
| F-06 | Relational governance plus two content-addressed artifacts; no trajectory copy. | Execution and Persistence | RESOLVED |
| F-07 | Transaction A, independent dispatch and atomic Transaction B. | Execution and Persistence | RESOLVED |
| F-08 | One RUNNING plus exactly one immutable terminal event. | ADR; Execution and Persistence | RESOLVED |
| F-09 | Closed completeness policies and explicit `INELIGIBLE` evidence. | Contracts; Metrics and Comparison | RESOLVED |
| F-10 | Four domain-separated hashes with exact inclusions/exclusions. | Contracts | RESOLVED |
| F-11 | Seven independent OAuth/project-scoped capabilities and RBAC proposal. | ADR; Contracts | RESOLVED |
| F-12 | Immutable DRAFT→VALIDATED→PUBLISHED→DEPRECATED lifecycle. | ADR; Contracts | RESOLVED |
| F-13 | Independent experiment-limit dimensions, numeric values deferred to plan. | Execution and Persistence | RESOLVED |
| F-14 | Authorized non-destructive abort with immutable post-abort evidence. | Execution and Persistence | RESOLVED |
| F-15 | Closed versioned vocabularies; no author-supplied executable code. | Metrics and Comparison; Execution and Persistence | RESOLVED |

## Consequences

- Experiment execution is recoverable after crashes and independent scenario commits.
- Parallel completion order cannot change result identity.
- Scenario expansion and artifact storage impose explicit aggregate resource limits.
- Partial results are visible and cannot hash like complete results.
- Implementation will require relational structures and therefore likely migration `0042`.
- This architecture adds no solver, trajectory semantics, GDSS-002 semantics or GDSS-003 terminal
  semantics.

## Rejected alternatives

- Generate scenarios lazily while dispatching: rejected because the scenario universe would not be
  committed before execution.
- Store factors only and reconstruct historical scenarios: rejected as insufficient primary
  execution evidence.
- Copy trajectories into experiment artifacts: rejected as duplicate authority and amplification.
- Treat deltas as trajectory metrics: rejected because reference semantics belong to comparison.
- Distributed transaction across N simulations: rejected because GDSS-003 commits independently.
- Custom metric expressions or callbacks: rejected as executable, unbounded semantics.
- Infer baseline from order: rejected because reference identity must be explicit.

## Explicit authority report

```text
Control Engine dependency: NONE
DTE dependency:            NONE
MQTT dependency:           NONE
Telemetry binding:         NONE
Physical actuation:        NONE
Prediction authority:      NONE
Recommendation authority:  NONE
Scientific authority:      NONE
```
