# GDSS-004 — Architecture Invariants

Status: `PROPOSED`
Implementation: `NOT_AUTHORIZED`
Test status: every invariant is `NOT_TESTED`

`NOT_TESTED` is deliberate: P010 authorizes architecture documents only. No documentation claim is
reported as an implementation PASS.

## GDS4 invariant baseline

| ID | Normative invariant | Required implementation evidence | Status |
|---|---|---|---|
| GDS4-INV-01 | Experiment identity is distinct from every simulation execution. | Separate types, tables, FKs and negative identity tests. | NOT_TESTED |
| GDS4-INV-02 | Scenario identity is distinct from simulation execution identity. | Scenario hash/row maps to, but is not, a GDSS-003 attempt. | NOT_TESTED |
| GDS4-INV-03 | `COUNTERFACTUAL` never means observed history. | Closed provenance/type assertions and forbidden-claim tests. | NOT_TESTED |
| GDS4-INV-04 | Comparative finding is not empirical finding. | `SIMULATION_DERIVED` only; no empirical status field. | NOT_TESTED |
| GDS4-INV-05 | Comparative finding is not recommendation. | Closed result schema with no recommendation/action contract. | NOT_TESTED |
| GDS4-INV-06 | Experiment result is not prediction. | Prediction authority fixed `NONE`; vocabulary scan. | NOT_TESTED |
| GDS4-INV-07 | Every scenario binds one exact ExperimentVersion. | Non-null composite FK and cross-version rejection. | NOT_TESTED |
| GDS4-INV-08 | Every scenario execution binds exact GDSS-003 identities. | Attempt, input, result and trajectory hash reconciliation. | NOT_TESTED |
| GDS4-INV-09 | Baseline/reference is explicit. | No ordinal fallback; missing/duplicate baseline rejection. | NOT_TESTED |
| GDS4-INV-10 | Experimental factors are explicit. | Closed factor targets/domains and canonical design hash. | NOT_TESTED |
| GDS4-INV-11 | Controlled inputs cannot silently vary. | Full base-versus-materialized diff proof; `UNDECLARED_VARIATION` test. | NOT_TESTED |
| GDS4-INV-12 | Scenario expansion is deterministic. | Same design produces identical ordered scenario hashes. | NOT_TESTED |
| GDS4-INV-13 | Expansion is finite and bounded. | Preflight cardinality/overflow and limit rejection tests. | NOT_TESTED |
| GDS4-INV-14 | Worker order cannot change semantic order. | Permuted scheduling yields identical manifest/result order. | NOT_TESTED |
| GDS4-INV-15 | Parallelism cannot change experiment identity. | Serial/parallel hash equivalence. | NOT_TESTED |
| GDS4-INV-16 | Failed scenario cannot masquerade as completed. | Terminal classification and failed-scenario hash participation. | NOT_TESTED |
| GDS4-INV-17 | Partial evidence is explicitly classified. | Policy-bound completeness plus persisted `INELIGIBLE` comparisons. | NOT_TESTED |
| GDS4-INV-18 | Metric definitions are versioned. | Hash-bound `GDSS_EXPERIMENT_METRICS_V1`; no implicit latest. | NOT_TESTED |
| GDS4-INV-19 | Metric dimensions are governed and validated. | GDSS unit reuse, integral dimension and incompatibility tests. | NOT_TESTED |
| GDS4-INV-20 | Derived metrics preserve simulation provenance. | Exact trajectory/result hashes and `SIMULATION_DERIVED`. | NOT_TESTED |
| GDS4-INV-21 | GDSS-004 never duplicates trajectory authority. | Artifact scan proves references only, no trajectory payload. | NOT_TESTED |
| GDS4-INV-22 | Historical experiment results are immutable. | Append-only guards and update/delete rejection. | NOT_TESTED |
| GDS4-INV-23 | Model successor cannot alter historical experiment. | Exact model version/content hash remains bound. | NOT_TESTED |
| GDS4-INV-24 | Binding successor cannot alter historical experiment. | Exact binding version/hash remains bound. | NOT_TESTED |
| GDS4-INV-25 | Solver successor cannot alter historical experiment. | Exact solver version remains bound. | NOT_TESTED |
| GDS4-INV-26 | Parameter sweep is not calibration. | No observed-data fitting/calibrated status in core. | NOT_TESTED |
| GDS4-INV-27 | Parameter exploration is not optimization. | No objective, optimizer, adaptive loop or optimal status. | NOT_TESTED |
| GDS4-INV-28 | Experiment is not Digital Twin. | No telemetry/state synchronization dependency. | NOT_TESTED |
| GDS4-INV-29 | Experiment is not control policy. | No policy/recommendation/action output dependency. | NOT_TESTED |
| GDS4-INV-30 | Experiment has zero physical authority. | Every result/finding asserts `physicalAuthority=NONE`. | NOT_TESTED |
| GDS4-INV-31 | There is no implicit telemetry acquisition. | Import/config/runtime boundary scans. | NOT_TESTED |
| GDS4-INV-32 | There is no MQTT dependency. | Import/dependency boundary scans. | NOT_TESTED |
| GDS4-INV-33 | There is no Control Engine dependency. | Import/dependency boundary scans. | NOT_TESTED |
| GDS4-INV-34 | There is no DTE dependency. | Import/dependency boundary scans. | NOT_TESTED |
| GDS4-INV-35 | There is no actuation dependency. | Import/API/side-effect boundary scans. | NOT_TESTED |
| GDS4-INV-36 | Experiment resources are independently bounded. | Every `GDSS_EXPERIMENT_LIMITS_V1` dimension has boundary tests. | NOT_TESTED |
| GDS4-INV-37 | Computational identity excludes worker timing. | Actor/time/worker/retry mutation leaves hashes unchanged. | NOT_TESTED |
| GDS4-INV-38 | Same governed experiment reproduces same manifest. | Repeat materialization exact-byte/hash equality. | NOT_TESTED |
| GDS4-INV-39 | Every comparison declares explicit reference and target. | Closed schema and missing-reference rejection. | NOT_TESTED |
| GDS4-INV-40 | Scientific claims require authority beyond GDSS-004. | Scientific authority fixed `NONE`; forbidden-claim schema scan. | NOT_TESTED |

## Architecture-only refinements

These refine the 40 invariants without renumbering them. The Implementation Plan must reconcile them
into the final test matrix.

| ID | Refinement | Related baseline | Status |
|---|---|---|---|
| GDS4-ARCH-INV-01 | Failed, never-dispatched and aborted scenarios participate in result identity. | 16, 17, 37 | NOT_TESTED |
| GDS4-ARCH-INV-02 | Temporal comparability is validated before every numerical comparison. | 19, 39 | NOT_TESTED |
| GDS4-ARCH-INV-03 | Relative and percent comparison against zero yields governed ineligibility. | 19, 39 | NOT_TESTED |
| GDS4-ARCH-INV-04 | No GDSS-003 dispatch occurs before complete materialization Transaction A commits. | 07, 12, 13 | NOT_TESTED |
| GDS4-ARCH-INV-05 | Metric/comparison execution accepts no user-supplied code or expression. | 18, 36 | NOT_TESTED |
| GDS4-ARCH-INV-06 | `ABORTED` preserves all committed evidence and cannot rewrite GDSS-003. | 17, 22 | NOT_TESTED |
| GDS4-ARCH-INV-07 | Recovery cannot duplicate materialized scenario identity. | 12, 38 | NOT_TESTED |
| GDS4-ARCH-INV-08 | Recovery cannot duplicate semantic GDSS-003 dispatch. | 08, 22, 38 | NOT_TESTED |
| GDS4-ARCH-INV-09 | Missing required evidence produces explicit `INELIGIBLE`, never omission. | 17, 39 | NOT_TESTED |
| GDS4-ARCH-INV-10 | Completion order cannot alter artifact bytes or hashes. | 14, 15, 37 | NOT_TESTED |
| GDS4-ARCH-INV-11 | Manifest artifact never contains trajectory bytes. | 21 | NOT_TESTED |
| GDS4-ARCH-INV-12 | One RUNNING event is followed by at most one immutable terminal event. | 16, 22 | NOT_TESTED |

## Target implementation closure

```text
GDS4-INV-01..40
    40 PASS
    0 FAIL
    0 BLOCKED

GDS4-ARCH-INV-01..12
    reconciled into the governed implementation matrix
```

Until implementation is separately authorized, the only truthful status is `NOT_TESTED`.

## Authority boundary

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
