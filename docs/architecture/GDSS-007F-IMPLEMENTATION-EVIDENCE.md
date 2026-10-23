# GDSS-007F — Governed Recommendation, Human Review & Decision Record

Status: `COMPLETED_GDSS_007F_GOVERNED_RECOMMENDATION_HUMAN_REVIEW_AND_DECISION_RECORD`

Date: 2026-10-23. Authorization: `MIDD-GDSS-P034-R1`. No commit, push, tag or release was performed.

## A. Baseline

- Checkout: `/Users/joseluis/dev/iot-midd-paas-auth-work`; branch `main`.
- `HEAD = origin/main = edf2be84004cc691ef2dbb0456e4e8b536765382`; ahead/behind `0/0`.
- Preflight source/principal revision: single head `0056`; dirty inventory contained only the authorized accumulated GDSS-007A..E candidate.
- Final source, isolated DB and principal DB: single head/current `0057`.

## B. Scope

Implemented only recommendation assembly, human review/authorization/revocation, separate human decision records, outcome references, reevaluation, canonical identity, persistence, RBAC, audit, idempotency and concurrency. GDSS-007G and every policy/control/physical bridge remain unauthorized and absent.

## C. Recommendation Identity

`RecommendationCandidate` binds exact problem, comparison, sensitivity, robustness, risk, preference, claim/capability/evidence, preferred and considered alternatives, evidence polarities, limitations, quality dimensions, rationale, scope, validity and provenance. Scientific identity excludes idempotency metadata.

## D. Lifecycle

PostgreSQL enforces `DRAFT -> EVIDENCE_ASSEMBLED -> REVIEW_REQUIRED -> AUTHORIZED|REJECTED`, followed only by `REVOKED|SUPERSEDED|INVALIDATED` where valid. Scientific children freeze after assembly; corrections use immutable successors.

## E. Evidence Admission

Candidate creation accepts exact limited-capability evidence for exploration/review, while authorization requires every bound capability to be `EVIDENCE_OF_CAPABILITY` and each exact claim to be authorized, current, unrevoked and unexpired. Failed, conflicting, insufficient, limited, not-evaluated and invalidated states fail closed at authorization.

## F. Scope Reconciliation

Authorization may only preserve or narrow target, horizon, domain, model and alternative set. Exact project-aware references and hashes prevent cross-project or latest-version substitution.

## G. Quality Dimensions

Seven separate dimensions are preserved: evidence adequacy, domain fit, uncertainty acceptability, robustness, constraint satisfaction, trade-off clarity and risk acceptability. No universal confidence or quality score exists.

## H. Constraint Reconciliation

Preferred alternatives must be admitted and hard-constraint-satisfied in contracts and PostgreSQL. Constraint violations cannot be compensated by preference or outcome.

## I. Risk Reconciliation

Unacceptable risk is non-compensable. Review-required/unknown conclusions cannot be silently upgraded to acceptable by authorization.

## J. Sensitivity/Robustness Reconciliation

Exact assessment IDs/hashes are bound. Non-stable sensitivity and non-robust/unknown conditions require explicit structured limitations; best expected, robust and low risk remain distinct.

## K. Adverse Evidence

At least one supporting and one non-supporting reference are mandatory. Supporting, contradicting, negative and limiting polarities are retained, and every compared alternative remains represented with its disposition and reason.

## L. Rationale

The authoritative rationale is structured into supporting/adverse factors, constraint/risk/robustness/sensitivity conclusions, uncertainties, trade-offs and change conditions. Optional AI narrative cannot introduce authority or replace those facts.

## M. Reviews

Human review records exact candidate ID/hash, decision, reason, adverse disclosure, actor, timestamp and idempotency key. Authorization requires an approval and rejects any unresolved reject/more-evidence/revision review, at both service and DB layers.

## N. Authorization

Authorization binds all exact scientific hashes and a non-widening scope. It means only human authorization for decision support; it cannot improve evidence, risk, robustness or uncertainty and cannot create policy/control authority.

## O. SoD

Author and authorizer must differ. A human-only explicit `SOD_EXCEPTION` reason is audited; AI cannot invoke it.

## P. AI Boundary

AI is hard-denied for authoritative review, authorization, revocation, human decision recording and SoD exception, including an AI actor holding an admin role.

## Q. Revocation

Revocation is append-only, binds the exact authorization/candidate/hash, records actor/reason/trigger/hash/time and preserves historical authorization.

## R. Expiry

Expired validity projects `AUTHORIZED_EXPIRED_REVIEW_REQUIRED`; no automatic renewal, revocation or successor authorization occurs.

## S. Staleness

Open/acknowledged reevaluation triggers and live claim drift project `STALE_REVIEW_REQUIRED`. Revoked, expired, non-authorized or hash-drifted claims can never project current.

## T. Reevaluation Triggers

All twelve mandated trigger types and four effects are implemented. Trigger state is projected from append-only events with legal `OPEN -> ACKNOWLEDGED|RESOLVED` and `ACKNOWLEDGED -> RESOLVED` transitions, exact sequencing, transaction locking and idempotency.

## U. Human Decision Record

`DecisionRecord` is separate from recommendation authorization and supports accept, reject, defer, request-more-evidence and select-different-alternative. It is append-only and correctable only by a successor/supersession reference.

## V. Human Override

The PostgreSQL workflow proved a recommendation preferring A with a human selecting another admissible B, preserving reason and exceptions as `SELECT_DIFFERENT_ALTERNATIVE` without treating it as an automatic error.

## W. Decision Outcome Observation

Outcome linkage requires `OUTCOME_ONLY_NOT_VALIDATION_EVIDENCE`. The integration test proves linking an observation creates no GDSS-006 evidence unit.

## X. Resource Limits

Recommendation evidence references: 5,000 pass; 10,000 pass; 10,001 reject with `RESOURCE_LIMIT_EXCEEDED`. Final focused benchmark: 10,000 accepted in 71.580 ms, 10,001 rejected in 24.477 ms, 12,730,368 RSS-byte delta, 2,271,930 canonical bytes. Full-suite timing is diagnostic only.

## Y. Hashing

Domain-separated SHA-256 namespaces include `midd:gdss:recommendation-candidate:v1` and `midd:gdss:human-decision-record:v1`, plus review, authorization, revocation, trigger, trigger-event and outcome namespaces. Golden tests prove insertion-order determinism and semantic sensitivity.

## Z. Persistence

Migration 0057 creates all mandated recommendation, alternative, evidence, limitation, review, authorization, revocation, decision, decision-alternative, outcome, reevaluation-trigger and reevaluation-event tables, plus append-only governance events.

## AA. PostgreSQL Enforcement

Project-aware FKs/triggers enforce exact references, hashes, lifecycle, immutable history, scientific freeze, human-only protected actions, SoD, current claim/capability prerequisites, review completeness, non-widening scope, uniqueness and transition sequence.

## AB. RBAC

Dedicated permissions are `AUTHOR_RECOMMENDATION`, `REVIEW_RECOMMENDATION`, `AUTHORIZE_RECOMMENDATION`, `REVOKE_RECOMMENDATION`, `RECORD_HUMAN_DECISION` and `AUDIT_DECISION_SUPPORT`; policy-edit authority is not reused.

## AC. Audit

Candidate assembly and every human/governance event share the transaction with append-only, actor-kind-aware audit, exact entity sequence, canonical event hash and idempotency.

## AD. Idempotency

Scientific candidate materialization is create-or-get by canonical hash. Human events require explicit idempotency keys; same-key/different-semantics raises `IDEMPOTENCY_CONFLICT`.

## AE. Concurrency

Advisory and row locks cover candidate successors, reviews, authorization, revocation, decisions, triggers and reevaluation transitions. Real PostgreSQL tests proved one effective result without duplicate authorization, event, decision or limit bypass.

## AF. Invariants

007F owns and tests DEC-INV-01, 02, 09, 10, 15, 16, 19, 20, 21 and 33–40 while the complete topology suite preserves prior invariants.

## AG. Adversarial Tests

Covered AI elevation, stale/revoked evidence denial, limited/failed capability denial, hard constraint and unacceptable risk, omitted adverse evidence/alternatives/limitations, scope widening, exact-hash substitution, expiry/staleness projection, immutable override/history, cross-project references, double authorization and 10,001 references.

## AH. End-to-End Workflow

Real PostgreSQL executed the accumulated problem-to-risk foundation through candidate, review, authorization and a separate human decision. The final authority boundary remained recommendation-only.

## AI. Migration

- Clean isolated chain from empty DB through `0056`: pass.
- `0056 -> 0057 -> 0056 -> 0057`: pass.
- Principal upgraded/reconciled to final `0057` only after the isolated cycle; principal was never downgraded.
- Final `alembic heads`: exactly `0057 (head)`; principal and isolated current: `0057`.

## AJ. Regression

- Focused 007F unit: 47/47 pass.
- Real PostgreSQL 007A..F: 45/45 pass (007A rerun sequentially after parallel fixture interference; 007B..F 32/32 pass).
- Full topology-next: 117 files passed, 21 environment-gated files skipped; 709 passed, 122 skipped.
- TypeScript no-emit: pass. Next.js production build: pass.
- Python middleware: 179 passed, 6 environment-gated skipped.
- Parametric Control Engine: 40 passed.

## AK. Static Boundary

`git diff --check` passes. Forbidden-term scan finds only the intentional strict-contract denylist. Executable import scan finds no MQTT, AMQP, DTE, Control Engine, policy activation, actuator or physical-channel dependency in the recommendation domain/repository/service.

```text
RecommendationAuthority = HUMAN_GOVERNED_DECISION_SUPPORT_ONLY
PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE
```

## AL. Known Limitations

No GDSS-007 decision-support HTTP API is introduced in this phase; services/repositories are the authorized boundary. Reevaluation trigger creation is explicit rather than an automatic cross-domain event consumer. Consolidated 40-invariant/20-adversarial closure remains GDSS-007G work and is not authorized here.

## AM. Git Status

The working tree intentionally preserves the accumulated authorized GDSS-007A..F candidate. Baseline commit and remote remain unchanged and synchronized. No commit, push, tag or release occurred.

## AN. Final Status

```text
GDSS_007A_IMPLEMENTED
GDSS_007B_IMPLEMENTED
GDSS_007C_IMPLEMENTED
GDSS_007D_IMPLEMENTED
GDSS_007E_IMPLEMENTED
GDSS_007F_IMPLEMENTED
GDSS_007G_NOT_AUTHORIZED

COMPLETED_GDSS_007F_GOVERNED_RECOMMENDATION_HUMAN_REVIEW_AND_DECISION_RECORD
```

The system explains what it recommends, why, with which evidence, limitations, risk and uncertainty. A human authorizes decision support and separately records the decision. The recommendation executes nothing.
