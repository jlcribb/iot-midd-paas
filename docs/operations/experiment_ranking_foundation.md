# Experiment ranking foundation (M6.6)

`ranking-policy:v1` produces reproducible presentation ordering for an already evaluated, terminal simulation batch. A ranking is evidence, not a recommendation, approval, deployment, or policy activation; it has no physical effects.

## Semantics

The ordering is strictly: technical evaluability, eligibility, semantic cohort compatibility, Pareto annotation, persisted evaluation score, then rank. Only `COMPLETED` and `COMPLETED_WITH_WARNINGS` evaluations with a score can be eligible. A critical constraint violation is `INELIGIBLE`; missing or non-evaluable evaluations are `UNDETERMINED` and remain unranked. Non-critical violations are warnings only. Scores and KPI values are never recalculated.

The cohort is one project/batch/profile/version/engine/metric-set-compatible group. Incompatible records are visible as unranked with an explicit reason. Pareto uses the existing `computeParetoFront()` semantics and is persisted only as an annotation: it never changes a score or rank.

## Policy, ties, and reproducibility

Eligible items are ordered by persisted score descending. The score epsilon is `0.000001`; scores within it receive the same dense rank and tie group. `candidate_hash ASC` is only a stable technical presentation tie-break, not a merit signal. The ranking hash canonically includes batch semantic identity, sorted candidate/evaluation evidence, eligibility policy, ranking policy/version, epsilon, Pareto engine version, ranking engine version, and schema version—not actor, timestamps, names, or UUID-generated ranking identity.

The same semantic input returns the same persisted ranking via `(project_id, ranking_hash)`. Rankings and items are database-immutable. Changed evidence or policy creates a new hash/ranking, and collision reuse produces no duplicate audit event.

## API and access

- `POST /api/control/experiments/projects/:projectId/batches/:batchId/rankings` creates or reuses `ranking-policy:v1` (`{}` is valid).
- `GET /api/control/experiments/projects/:projectId/batches/:batchId/rankings` lists rankings.
- `GET /api/control/experiments/projects/:projectId/batches/:batchId/rankings/:rankingId` reads one ranking.

Reads require `view_dashboard`; creation requires `edit_policies`. Every creation records `EXPERIMENT_RANKING_CREATED` with simulation context and `physical_effects=false`. No apply, promote, recommendation, activation, MQTT, outbox, or hardware endpoint is provided.

## Limitations

M6.6 orders existing candidates only. It does not search, generate candidates, make recommendations, or feed rank results back into a search space.
