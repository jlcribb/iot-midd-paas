# M7.1A promotion E2E validation

The runner-backed test `apps/topology-next/tests/integration/experiment-batch.e2e.test.ts` reuses the real persisted M6 chain: search space, candidates, batch, simulation, trace, evaluation, ranking, recommendation and human review. It then creates the M7.1 proposal and assessment through `PolicyPromotionService`.

The assessment transition is transactional: `CREATED → VALIDATION_PENDING → terminal` is persisted within one transaction. The pending state is therefore never committed with a partial gate set. PostgreSQL rejects direct `CREATED → terminal`, terminal reversals and immutable evidence updates.

| Gate | Version | Severity | Status | Evidence |
| --- | --- | --- | --- | --- |
| `GATE_HUMAN_REVIEW_APPROVED` | v1 | BLOCKING | PASS | review hash |
| `GATE_RECOMMENDATION_UNIQUE` | v1 | BLOCKING | PASS | recommendation hash |
| `GATE_CANDIDATE_ELIGIBLE` | v1 | BLOCKING | PASS | ranking hash |
| `GATE_NO_CRITICAL_CONSTRAINT_VIOLATION` | v1 | BLOCKING | PASS | evaluation hash |
| `GATE_REPRODUCIBILITY_EVIDENCE` | v1 | BLOCKING | PASS | batch hash chain |
| `GATE_RANKING_EVIDENCE` | v1 | BLOCKING | PASS | rank 1 |
| `GATE_TRACE_EVIDENCE` | v1 | BLOCKING | PASS | trace hash |
| `GATE_SIMULATION_ONLY_BOUNDARY` | v1 | BLOCKING | PASS | `SIMULATION` / `false` |

The test also proves proposal and assessment idempotency, one audit event per semantic creation, proposal/assessment/gate immutability, rejected and ambiguous controlled PostgreSQL fixtures, cross-project rejection, no active-policy mutation and deterministic fixture cleanup. It does not create a policy, activate or deploy one, invoke MQTT, write the operational outbox or perform physical actuation.

Run the real E2E from the local Docker stack:

```bash
docker exec -e M65_E2E_RUNNER=1 -e M65_E2E_REPORT=1 iotmw-topology-ui sh -lc 'npm test -- --run tests/integration/experiment-batch.e2e.test.ts'
```
