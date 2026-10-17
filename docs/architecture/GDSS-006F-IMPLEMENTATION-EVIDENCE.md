# GDSS-006F — Implementation Evidence

Prompt: `MIDD-GDSS-P023-R1`
Status: `COMPLETED_GDSS_006F_PREDICTIVE_CAPABILITY_CLAIMS_AND_REVALIDATION_WITH_WARNINGS`

## A. Baseline

- Checkout: `/Users/joseluis/dev/iot-midd-paas-auth-work`; branch `main`.
- Baseline HEAD: `dee81328f4a73b525f8d7236d8ee799044b9cabc`.
- Initial source head and principal database current: single `0048`.
- Existing local GDSS-006A..E material was classified and preserved; no cleanup, reset, commit,
  push, tag or remote publication occurred.

## B. Scope Implemented

Implemented only exact-scope predictive capability assessment, structured governed claims, human
review/authorization/rejection/revocation, currentness, revalidation triggers and conservative
cross-version evidence-transfer assessment. Recommendation, policy activation, control authorization,
physical actuation, adaptive learning, ML/RL, automatic transfer, equivalence and partial
revalidation remain absent.

## C. Files Changed

- Domain: `capability-contracts.ts`, `capability-canonical.ts`, `capability-engine.ts`,
  `capability-authorization.ts`, `capability-diagnostics.ts` and validation barrel exports.
- Persistence/service: `gdss-capability-claims.repository.ts`,
  `gdss-capability-claims.service.ts`, strict validators and DB-error mappings.
- HTTP: project-scoped routes for capability assessments/invalidation, claim identities, claim
  drafts/updates/assembly/submission/review/authorization/revocation/supersession/audit,
  revalidation trigger assessment/resolution and evidence transfer.
- Database: `0049_gdss006f_capability_claims_revalidation.py`.
- Verification: `gdss-capability-claims.test.ts` and the extended real-PostgreSQL evidence-custody
  integration suite.
- Documentation: this evidence record and the GDSS-006 implementation-plan status.

## D. Migration 0049

Migration `0049`, directly based on `0048`, adds nine normalized tables for capability assessments,
claim identity/version/event/review/authorization/revocation, revalidation trigger assessments and
evidence-transfer assessments. Composite project bindings, semantic uniqueness, exact-hash guards,
legal-transition triggers, post-assembly freezing and append-only history are enforced in PostgreSQL.
The disposable database completed `0048 -> 0049 -> 0048 -> 0049`; the final refreshed 0049 migration
also passed both transactional and durable integration tests.

## E. PredictiveCapabilityAssessment

Assessments are immutable, bind one exact evidence-set ID/hash and retain model/hash, target,
horizon, domain version, protocol family, metric/baseline/uncertainty profiles, evidence period,
per-axis explanation, limitation/conflict/negative manifests, state, rationale, semantic hash and
optional predecessor. Explicit invalidation creates a successor assessment with a causal reference;
it never mutates the prior assessment.

## F. Capability Scope

Scope is structured and exact for model version/hash, target, horizon, validity-domain version,
protocol family and the three profiles. Evidence period and typed numeric/temporal/categorical/boolean
domain constraints are explicit. Horizon, target, model, domain and profiles require exact identity;
evidence period and domain may only narrow.

## G. Capability States

Exactly seven states are executable: `NOT_EVALUATED`, `INSUFFICIENT_EVIDENCE`,
`EVIDENCE_OF_LIMITED_CAPABILITY`, `EVIDENCE_OF_CAPABILITY`, `CONFLICTING_EVIDENCE`,
`EVIDENCE_OF_FAILURE`, and `INVALIDATED`.

## H. Capability Decision Rules

`REGISTER_SCOPE` alone yields `NOT_EVALUATED`. Incomplete evidence or critical unknown/insufficient
independence, temporality, domain or uncertainty fails closed to insufficient. Material conflict is
preserved without voting. Invalidating references or governed adverse failure types yield failure.
Noncritical limitation/insufficiency yields limited capability; full capability requires all V1
minimums. The seven 006E axes remain separate and no total score exists.

## I. Claim Identity & Versioning

A project-scoped canonical identity owns monotonically allocated claim versions. Identity locking and
`(identity, version)` uniqueness serialize allocation; a successor must name the exact immediately
preceding claim. Concurrent competing successors produce one valid successor and one explicit stale
predecessor failure.

## J. Claim Grammar

Scientific meaning is a canonical structured object, not presentation text. It contains exact
assessment/evidence hashes, scope, limitation/negative/conflict manifests, uncertainty summary,
template version, optional validity deadline and predecessor. Versioned human text is deterministically
rendered from that object and avoids universal predictive language.

## K. Claim Lifecycle

The protected lifecycle is `DRAFT -> EVIDENCE_ASSEMBLED -> REVIEW_REQUIRED -> AUTHORIZED|REJECTED`
and `AUTHORIZED -> SUPERSEDED|REVOKED`. Only draft structured fields may change. From assembly onward,
epistemic fields and rendered text are frozen; terminal versions cannot be reopened.

## L. Claim Review

Immutable reviews record reviewer, exact claim hash, decision, rationale, scope findings and evidence
findings. Decisions are `APPROVE_FOR_AUTHORIZATION`, `REQUEST_REVISION` and `REJECT`. Rejection is a
terminal claim transition and preserves the draft and review history.

## M. Claim Authorization

Authorization is a separate immutable entity binding claim hash, assessment hash, evidence-set hash,
authorized scope/hash, decision and human authorizer. It requires an approval review and locked
`REVIEW_REQUIRED` claim. Concurrent attempts return one effective authorization; stale or forged
bindings fail closed.

## N. Scope Subset Proof

Drafting and authorization prove `AUTHORIZED_SCOPE subseteq CLAIM_SCOPE subseteq ASSESSMENT_SCOPE`;
assessment construction independently proves its exact evidence-set binding. Narrow numeric,
temporal, categorical and boolean scopes are allowed; broadening, cross-target/domain/model/horizon,
profile omission or substitution is rejected.

## O. Separation of Duties

Claim author and authorizer differ by default. Same-actor authorization requires both exactly one
enabled project admin and an explicit reason; otherwise `CLAIM_SOD_VIOLATION`. The integration test
proves the multi-/zero-membership default failure. Any accepted exception is recorded in the
authorization and audit record and cannot change evidence strength.

## P. AI Boundary

AI identities are hard-denied for every mutating service entry point and therefore cannot assess,
review, authorize, revoke, alter scope or upgrade capability. Read-only audit remains available under
normal project access. Constants and audit context state physical and control authority `NONE`.

## Q. Claim Revocation

Revocation is a separate append-only entity bound to the historical authorization. It records actor,
reason, trigger and idempotency. The claim transitions to `REVOKED`, while claim, authorization,
review, evidence and lifecycle events remain queryable. Concurrent/repeated attempts resolve to one
effective revocation.

## R. Claim Currentness

Read projection distinguishes current authorization, expired-review-required, human-review-required,
superseded, revoked, rejected and not-authorized without rewriting history. Expiry never auto-revokes;
an unresolved adverse revalidation trigger projects `HUMAN_REVIEW_REQUIRED`.

## S. Revalidation Triggers

All twelve specified trigger kinds and the states `DETECTED`, `REVIEW_REQUIRED`, `ACKNOWLEDGED`,
`REVALIDATION_REQUIRED`, `RESOLVED`, `INVALIDATED` are structured and append-only. Resolution creates
a successor trigger assessment. This phase records and governs the need; it does not execute a new
validation pipeline.

## T. Contradictory Evidence

A later compatible-scope evidence set may be named as causal evidence for
`CONTRADICTORY_EVIDENCE`. The prior assessment and authorization are retained, a
`REVALIDATION_REQUIRED` record is created and claim currentness becomes human-review-required.

## U. Evidence Transfer

Every cross-version request creates an immutable `EvidenceTransferAssessment` with exact source and
target models, source set/hash, requested scope/mode, result, reason and content hash. Reserved
`PARTIAL_REVALIDATION_ALLOWED` and `EQUIVALENCE_ESTABLISHED` requests are rejected before persistence.

## V. Version Transfer Policy

V1 implements `NO_AUTOMATIC_TRANSFER`: both explicit full-revalidation and direct-transfer requests
produce `FULL_REVALIDATION_REQUIRED`. No capability state, evidence strength, claim or authorization
is inherited by another model version, including a minimal parameter-only version change.

## W. Hashing & Determinism

Domain-separated canonical SHA-256 namespaces cover assessments, claims, reviews, authorizations,
revocations, revalidation triggers and transfers. Canonical sorting removes row/input ordering;
assessment retry excludes UUID/actor/session, claim hash excludes rendered formatting, and
authorization hash includes exact actor and all three scientific hashes.

## X. Authorization & RBAC

Project-scoped OAuth maps operator/admin to assessment and authorship, operator/admin to review,
admin to authorization/revocation, and viewer/operator/admin to audit. Development fallback,
cross-project identities, unauthorized roles and AI authority fail closed. Scientific permissions do
not reuse policy-edit authority.

## Y. Audit

All required assessment, identity, claim lifecycle, review, authorization, revocation, revalidation
and transfer events are inserted in the same transaction as scientific state. Audit context includes
project, actor, capability `A1`, subsystem `gdss006f`, `physical_authority=NONE` and
`control_authority=NONE`.

## Z. API/Services

The official Next.js backend exposes all authorized service operations: assess/invalidate capability;
create/update/assemble/submit/review/authorize/reject/supersede/revoke/audit claims; assess/resolve
revalidation; and assess transfer. Route schemas are strict and authenticated actor identity always
comes from the session.

## AA. Domain Errors

Typed errors cover insufficient/conflicting evidence, invalid/immutable assessment, scope expansion,
illegal draft/review/authorization/terminal/mutation transitions, forbidden authorization, SoD,
stale replay, duplicate/forbidden revocation, required revalidation, forbidden/required transfer,
AI/physical authority and unauthorized capability actions. PostgreSQL messages map to this boundary.

## AB. Invariants

Executable coverage preserves VAL-INV-03/04/07/10/11/13/14/35/38/39/40: prediction differs from
evidence and capability; capability is scope-bound; humans cannot upgrade strength; versions require
revalidation; adverse evidence is visible; scopes cannot expand; later contradiction triggers review;
history is append-only; physical/control authority are `NONE`.

## AC. Tests

- GDSS-006F unit suite: 14/14 PASS.
- Real PostgreSQL 006A..F transactional suite: 11/11 PASS.
- Real PostgreSQL durable/concurrency suite: 11/11 PASS.
- topology-next full suite: 536 passed / 74 skipped; exit 0.
- TypeScript no-emit typecheck and Next.js production build: PASS.

## AD. Adversarial Tests

PASS coverage includes incomplete/critical-weak/conflicting/failure evidence, no score, cross-horizon
and expanded-domain rejection, adverse-manifest retention, post-assembly mutation, stale hashes,
illegal transitions, SoD, AI/role denial, expiry without revocation, contradiction-triggered review,
append-only revocation, partial/equivalence transfer denial and cross-version full revalidation.

## AE. Concurrency

Real multi-connection PostgreSQL races prove one effective deterministic assessment, one effective
authorization, one effective revocation and serialized successor version allocation. Advisory locks,
row locks, semantic uniqueness and idempotency keys provide deterministic retry behavior.

## AF. Security

Composite project-aware FKs and service checks reject cross-project bindings. Exact assessment,
evidence and claim hashes prevent substitution/replay. Authentication comes from OAuth session only.
Frozen claims/reviews/authorizations/revocations and audit rows prevent historical rewriting.

## AG. Performance

Diagnostic 1,000-operation sample: capability derivation 4.197 ms, scope subset proof 0.813 ms,
claim rendering 1.002 ms and one 1,000-scope canonical hash 24.130 ms. Integration diagnostics include
transactional and durable runs; these observations are not SLAs.

## AH. Regression

- topology-next: 536 passed / 74 skipped.
- Python runtime: 179 passed / 6 integration tests skipped by environment gating.
- Parametric Control Engine: 40 passed.
- TypeScript typecheck, Next.js production build, migration cycle and static boundary scans: PASS.

## AI. Backward Compatibility

The implementation is additive. GDSS-001..005 and GDSS-006A..E tests remain green. Protocols,
domains, partitions, holdouts, commitments, pairs, metrics, baselines, uncertainty, evidence sets,
strength profiles, Control Engine, MQTT, DTE and actuation semantics were not modified.

## AJ. Alembic Status

Source has one head: `0049`. Disposable PostgreSQL is current at `0049` after the required full
cycle and refreshed-migration tests. Principal PostgreSQL remains at `0048`: its optional deployment
upgrade was not performed because the execution environment required separate explicit authorization
for that shared-database side effect. No principal downgrade occurred.

## AK. Git Status

All GDSS-006A..F implementation, migrations, tests and documents remain local and uncommitted on
`main`; baseline HEAD is unchanged. `git diff --check` passes. No commit, push, tag or remote
publication occurred.

## AL. Risks / Warnings

- The principal local database still requires the separately authorized additive upgrade 0048→0049;
  source and disposable verification are complete.
- The executable AI boundary is deliberately stricter than the prose allowance: AI may summarize or
  suggest outside authoritative mutation APIs, but service-level draft creation is also denied.
- V1 exact profile matching prevents a claim from silently omitting an adverse metric, baseline or
  uncertainty source; future explicit profile-subset semantics require a new contract.
- `FULL_REVALIDATION_REQUIRED` is a governed outcome, not automatic execution of revalidation.
- GDSS-006G remains unauthorized; therefore this document does not declare total GDSS-006 closure.

## AM. Final Status

`COMPLETED_GDSS_006F_PREDICTIVE_CAPABILITY_CLAIMS_AND_REVALIDATION_WITH_WARNINGS`

GDSS-006F can produce a scope-bound epistemic assessment and a human-governed, reviewable,
revocable historical claim. Neither artifact grants recommendation, control or physical authority.

## P024-R3 corrective addendum

P024-R3 preserves the existing hard denial for AI review, authorization and revocation and reuses its
AI provenance predicate in GDSS-006B/E. Capability scope profiles are reconciled to the canonical
maximums of 16 distinct metric references and 8 baseline references in both Zod and PostgreSQL
constraints. The prior 64/32 implementation limits were defects discovered by P024, not historical
contract values. Existing-data assessment found zero incompatible rows and zero affected projects;
no truncation, deletion or normalization occurred. Migration `0051` is current; GDSS-006G remains
pending and no total GDSS-006 closure is asserted here.
