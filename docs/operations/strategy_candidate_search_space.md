# Strategy candidate search spaces

M6.4 adds a project-scoped, immutable representation of candidate control configurations. It is a deterministic Grid generator only: it does not create simulation runs, rank candidates, mutate policies, publish commands, or enable physical effects.

Each persisted search space contains the normalized parameter definition, its semantic hash, raw/valid/invalid counts, and a concise invalid-combination summary. `control_strategy_candidates` stores valid candidates in deterministic lexicographic parameter order with contiguous `candidate_index` values.

The generator accepts explicit values or inclusive `{ min, max, step }` numeric ranges. Ranges are expanded using a fixed decimal scale, never by repeated IEEE-754 addition. A request producing more than 1000 raw combinations fails with `SEARCH_SPACE_TOO_LARGE` before any persistence is attempted.

The supported schemas are deliberately the schemas of the real simulation controllers:

* `proportional`: required `gain`, `setpoint_value`; optional `deadband`, `min_action`, `max_action`. Valid candidates require a positive gain, non-negative optional values, and `min_action <= max_action` when both bounds are supplied.
* `threshold`: required `tolerance`, `increase_step`, `decrease_step`; optional `hold_signal`. It requires non-negative tolerance and positive increase/decrease steps.

There are no `lower`/`upper` threshold parameters in the current controller contract. They are rejected rather than creating a synthetic schema. Invalid combinations remain represented solely by persisted counts/reasons; they never become candidates.

`search_space_hash` is semantic and includes strategy type, parameter-schema version, Grid method, normalized definition, search-space schema version, and generator version. It excludes display name, description, actor, and timestamps. The database enforces `UNIQUE(project_id, search_space_hash)`, so exact replays return the same space and do not create a second audit row. `candidate_hash` contains only candidate semantics (strategy type, parameter-schema version, candidate schema version, and canonical parameters), intentionally excluding the parent search-space hash.

Creation, all candidate inserts, and the `STRATEGY_SEARCH_SPACE_CREATED` audit event happen in one PostgreSQL transaction. Rows are immutable. Read APIs require `view_dashboard`; generation requires `edit_policies`; all operations remain project-scoped. `physical_effects_allowed` is fixed to false in the schema and audit context.

The APIs are:

* `POST` / `GET` `/api/control/experiments/projects/:projectId/search-spaces`
* `GET` `/api/control/experiments/projects/:projectId/search-spaces/:searchSpaceId`
* `GET` `/api/control/experiments/projects/:projectId/search-spaces/:searchSpaceId/candidates`

Out of scope: candidate execution, batches, comparisons, Pareto analysis, recommendations, promotions, policy updates, broker publishing, and physical actuation.
