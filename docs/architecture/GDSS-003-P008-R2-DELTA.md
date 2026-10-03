# MIDD-IOT — MIDD-GDSS-P008-R2
## GDSS-003 Operational Prompt Reconciliation Delta

**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `NOT_YET_AUTHORIZED`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Alembic baseline:** `0040`

This delta is suitable for issuance as P008-R2. It does not resume P008.

Replace every GDSS-003 requirement selecting:

```text
GDSS_UNIT_CONVERSION_V1
```

with explicit:

```text
GDSS_UNIT_CONVERSION_V2
```

For GDSS-003 v1:

```text
TemporalConfiguration.timeUnit = second@1
unitConversionCatalogVersion = GDSS_UNIT_CONVERSION_V2
```

`simulation_input_hash` must bind that exact catalog version. V1 remains available only for
historical GDSS-002 evaluation and must reject `second@1`. V2 preserves inherited units and adds
the governed temporal interval required to prove `dimension(rate × dt) = dimension(state)`.

All other P008 authorization, scope, persistence, solver, resource, invariant, safety, migration,
Git and STOP conditions remain unchanged. R2 must explicitly reauthorize implementation and
migration `0041`; this delta alone grants neither.
