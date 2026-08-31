# Governed strategy recommendation (M6.7)

M6.7 converts an immutable experiment ranking into a `REVIEW_REQUIRED` recommendation. It is evidence for human review, not approval, policy activation, deployment, or actuation.

`recommendation-policy:v1` considers eligible items with a persisted rank only. It selects the lowest numeric rank; where several candidates share that rank, it selects the sole Pareto-optimal candidate only when exactly one exists. Otherwise it persists `AMBIGUOUS`, never using candidate hash, ID, or timestamp as merit. No eligible ranked items produce `NO_ELIGIBLE_CANDIDATE`.

The immutable evidence snapshot records candidate parameters, rank, score, eligibility, Pareto, constraints, available metrics, warnings, and a comparison against the next valid rank when possible. Its hash includes ranking identity, selection or canonical ambiguity set, policy/engine versions, and semantic evidence—never actor or timestamps. Repeating the same request returns the same recommendation without a duplicate audit event.

Create with `POST /api/control/experiments/projects/:projectId/rankings/:rankingId/recommendations`; list/read through `/api/control/experiments/projects/:projectId/recommendations`. Reads require `view_dashboard`; creation requires `edit_policies`. `STRATEGY_RECOMMENDATION_CREATED` is recorded with `execution_context=SIMULATION` and `physical_effects=false`.

No UI, approval/rejection endpoint, apply/promote/deploy endpoint, policy mutation, MQTT, outbox, hardware adapter, or physical effect is part of this capability.
