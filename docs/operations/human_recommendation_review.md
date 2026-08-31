# Human recommendation review

M6.8 records one immutable human decision over a historical M6.7 recommendation. A review is not a recommendation, policy activation, deployment, or physical actuation.

`human-review-policy:v1` permits `APPROVE_FOR_FURTHER_TESTING`, `REJECT`, and `REQUEST_MORE_EXPERIMENTS`. Only `UNIQUE_CANDIDATE` can be approved for further testing; ambiguous, no-eligible, and no-ranking outcomes may be rejected or request more experiments. Approval means only that controlled experimental work may continue.

The authenticated actor supplies reviewer identity; the request body never does. Rationale is required (trimmed, 3–2000 characters). The immutable review hash binds recommendation hash, decision, canonical rationale, reviewer identity, policy version, and schema version.

There is one authoritative review per recommendation. Identical retries return it without another audit event; a semantically different attempt returns `REVIEW_ALREADY_RECORDED`. Reviews reference immutable recommendation evidence and do not change the recommendation, candidate, batch, ranking, policy, runtime, MQTT, or hardware.

API: `POST /api/control/experiments/projects/:projectId/recommendations/:recommendationId/reviews` requires `edit_policies`; `GET .../:recommendationId/review` requires `view_dashboard`. Creation records `STRATEGY_RECOMMENDATION_REVIEW_RECORDED` with `SIMULATION` and `physical_effects=false`.
