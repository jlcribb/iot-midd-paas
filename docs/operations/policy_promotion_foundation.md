# Policy promotion foundation

M7.1 adds a governed proposal and assessment domain after immutable M6 human review. A proposal is not a policy, deployment, activation, runtime mutation, or physical actuation.

Only a `UNIQUE_CANDIDATE` recommendation with an `APPROVE_FOR_FURTHER_TESTING` review can create a proposal. `policy-promotion-proposal:v1` binds recommendation, review, candidate, evaluation, ranking and batch hashes. Creation is idempotent and audited.

`policy-promotion-assessment:v1` evaluates eight deterministic, blocking v1 gates: approved review, unique recommendation, eligible candidate, no critical constraint violation, reproducibility chain, ranking evidence, trace evidence, and the simulation-only boundary. Results are immutable, canonically ordered, and explain their evidence.

Assessment precedence is `BLOCKED > FAILED > PASSED`; an invalid simulation/physical boundary blocks the assessment. The lifecycle is `CREATED → VALIDATION_PENDING → terminal`; assessment persistence and the terminal transition occur in one transaction, so `VALIDATION_PENDING` is never externally committed as a partial assessment. Direct `CREATED → terminal` and any terminal mutation are rejected by PostgreSQL triggers.

A passed assessment transitions its proposal to `VALIDATED`, which does not mean production approval, policy creation, activation, deployment, or actuation. Reads require `view_dashboard`; proposal and assessment creation require `edit_policies` pending dedicated future permissions.
