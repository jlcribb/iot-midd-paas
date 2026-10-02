# MIDD-IOT — GDSS-001
## Baseline Recovery & Controlled Resume

**Prompt ID:** `MIDD-GDSS-P001-R1`
**Parent mandate:** `MIDD-GDSS-P001`
**Current status:** `BLOCKED_BY_ARCHITECTURAL_CONTRADICTION`
**Purpose:** resolve execution-baseline divergence and resume GDSS-001 without weakening governance.

## 1. Authoritative candidate checkout

Resume reconnaissance using:

```text
/Users/joseluis/dev/iot-midd-paas-auth-work
```

Expected baseline from prior read-only evidence:

```text
branch: main
HEAD: ceafe7b08d803cb9da739ab6dd45c0adb3aa5f86
Alembic code head: 0038
deployed database head: 0038
```

Treat these values as expectations to verify, not facts to force.

Do not use `stamp`, downgrade, migration rewriting, checkout manipulation or database mutation to manufacture alignment.

## 2. Preserve previous checkout

Do not modify:

```text
/Users/joseluis/dev/iot-midd-paas
```

to make it resemble the deployed 0038 baseline.

Its observed 0008/0038 divergence remains evidence from the failed Step 0 attempt.

Do not delete or overwrite its dirty working-tree changes.

## 3. Reconciliation gate

Before any GDSS production change, verify in `iot-midd-paas-auth-work`:

```text
git branch
git HEAD
git status
Alembic code head
database alembic_version
migration 0038 presence
single-head topology
runtime mount relationship
```

Also verify that the source tree contains the governance capabilities observed in the deployed database, including the project-aware authorization mechanisms relevant to P4.

Record exact evidence.

## 4. Gate outcome

If:

```text
code Alembic head = 0038
database Alembic head = 0038
required governance source exists
no unexplained migration divergence exists
```

then set:

```text
BASELINE_RECONCILIATION = PASS
```

and continue automatically with the original `MIDD-GDSS-P001`.

If these conditions are not satisfied:

```text
BASELINE_RECONCILIATION = FAIL
```

STOP.

Do not choose another baseline autonomously.

Report the new contradiction with exact evidence.

## 5. Working-tree protection

Inspect the candidate checkout before writing.

If unrelated existing changes are present:

- preserve them;
- identify them in the report;
- do not reset them;
- do not overwrite them;
- distinguish pre-existing modifications from GDSS changes.

A dirty tree alone is not a reason to stop if GDSS work can be isolated safely.

Stop only if existing modifications materially overlap the files that GDSS must modify and safe preservation cannot be guaranteed.

## 6. Recover GDSS documentation

Ensure the approved GDSS artifacts are available in the authoritative checkout:

```text
Architecture Package v0.2
Implementation Plan v0.1
MIDD-GDSS-P001
Step 0 blocked report
```

Transfer only the required GDSS documentation from the previous workspace if absent.

Do not transfer unrelated source-code changes.

Do not interpret document transfer as implementation.

## 7. Resume Step 0

Repeat repository reconnaissance only where the baseline difference can materially affect the decision.

Do not repeat investigation merely for ceremony.

Re-evaluate and finalize:

```text
P1 — provenance persistence topology
P2 — unit/dimension historical identity
P3 — canonicalization semantics
P4 — authorization/RBAC mapping
```

against the reconciled 0038 source baseline.

The previous findings are evidence, not automatically accepted decisions.

## 8. P4 mandatory reconciliation

Inspect the actual project-aware authorization mechanisms, including the observed equivalents of:

```text
getControlRoleForProject
actor.project_roles
```

and determine how GDSS declarative governance should reuse existing identity, project scope and authorization.

Do not import Control Engine business logic merely to obtain authorization.

Reuse shared authorization/governance infrastructure where appropriate.

Preserve:

```text
IDENTITY
    ≠
AUTHORIZATION

CREATE AUTHORITY
    ≠
PUBLISH AUTHORITY
```

Do not create a parallel GDSS authentication system.

## 9. Architecture boundary remains unchanged

Baseline recovery does NOT authorize architectural expansion.

GDSS-001 remains prohibited from acquiring:

```text
simulation
DTE integration
Control Engine integration
MQTT publishing
telemetry binding
device commands
physical binding
physical actuation
recommendation execution
```

The existence of these capabilities in the 0038 repository does not make them GDSS dependencies.

## 10. Migration rule

Only after:

```text
BASELINE_RECONCILIATION = PASS
P1 = RESOLVED
P2 = RESOLVED
P3 = RESOLVED
P4 = RESOLVED
STEP_0_GATE = PASS
```

may a GDSS migration be created.

Determine the next migration identifier from the actual repository.

Do not assume it from this prompt.

The resulting migration must extend the authoritative migration chain without rewriting historical migrations.

## 11. Resume original implementation

After Step 0 passes, continue the original `MIDD-GDSS-P001` end-to-end:

```text
contracts/types
units/dimensions
persistence
canonicalization/hash
draft aggregate operations
validation/freeze
lifecycle/audit
successor creation
RBAC
declarative API/service surface
two domain fixtures
invariant tests
negative capability tests
dependency tests
full regression
independent verification
```

No additional human confirmation is required for ordinary implementation decisions already governed by the approved architecture and plan.

## 12. Verification

The final report must distinguish:

```text
PREVIOUS FAILED BASELINE
    iot-midd-paas
    code 0008 / DB 0038

AUTHORITATIVE IMPLEMENTATION BASELINE
    iot-midd-paas-auth-work
    verified code/database state

GDSS CHANGES
    exact files/migration/tests

PRE-EXISTING CHANGES
    exact preserved state
```

Report GDS-INV-01..22 individually with evidence.

Never convert `NOT_TESTED` into `PASS` solely because no forbidden capability was intentionally added.

## 13. Git discipline

Do not push unless separately authorized under the project's operational rules.

Do not merge the obsolete/divergent checkout into the authoritative checkout.

Do not commit unrelated pre-existing changes.

If commits are created, they must contain only attributable GDSS changes unless repository mechanics make an inseparable generated artifact necessary and that fact is documented.

## 14. Completion statuses

If baseline reconciliation fails:

```text
BLOCKED_BY_BASELINE_DIVERGENCE
```

If baseline reconciles but GDSS implementation has blocking failures:

```text
INCOMPLETE_GDSS_001
```

If implementation and required verification succeed:

```text
COMPLETED_GOVERNED_DECLARATIVE_SYSTEMS_FOUNDATION
```

or, for documented non-blocking findings:

```text
COMPLETED_GOVERNED_DECLARATIVE_SYSTEMS_FOUNDATION_WITH_WARNINGS
```

## 15. Recovery principle

> The deployed governance baseline must be identified before GDSS is allowed to extend it. Baseline divergence must be reconciled by selecting and verifying the authoritative source/runtime pair, never by rewriting migration history or weakening governance.
