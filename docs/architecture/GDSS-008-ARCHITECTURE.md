# GDSS-008 — Governed Recommendation-to-Policy Transition Foundation

Architecture contract: MIDD-GDSS-P038-R1. Date: 2026-10-23.
Status: `COMPLETED_GDSS_008_ARCHITECTURE_AND_IMPLEMENTATION_PLAN_CONTRACT`.
This status closes the design contract only. Every implementation phase remains NOT_AUTHORIZED.
All entities, services, tables, endpoints, checks and benchmarks below are future requirements,
not implemented or executed features. Capabilities strengthened: C5 policies and C6 audit.

## 1. Purpose

Define how an exact governed recommendation and explicit human decision can support a versioned,
reviewable policy intention whose maximum authority is `AUTHORIZED_POLICY_PROPOSAL`.
That state means: A HUMAN-GOVERNED, REVIEWED, SCOPE-BOUND, AUDITED POLICY PROPOSAL THAT MAY BE
CONSIDERED FOR A FUTURE POLICY-CANDIDATE PROCESS. It authorizes consideration only, never deployment,
activation, control or actuation. The corresponding implementation plan is
[GDSS-008-IMPLEMENTATION-PLAN.md](GDSS-008-IMPLEMENTATION-PLAN.md).

Preflight: checkout `iot-midd-paas-auth-work`, branch `main`, HEAD and origin/main
`d5e6897902de035e69846d1bb3f3f325683b2989`, ahead/behind 0/0, clean tree, staged 0.
Live `git ls-remote --heads origin main` matched that hash without updating local references.
Existing `iotmw-api` returned exactly `0057 (head)` for both `python -m alembic heads` and
`python -m alembic current`, with `PGOPTIONS=-c default_transaction_read_only=on` and bytecode writes
disabled. No migration is created by P038; source and principal remain at 0057.

## 2. Constitutional Boundary

```text
OBSERVATION != PREDICTION != PREDICTIVE EVIDENCE != PREDICTIVE CAPABILITY
!= PREDICTIVE CLAIM != DECISION OPTION != SCENARIO != SCENARIO EVALUATION
!= COMPARISON != RECOMMENDATION != HUMAN DECISION != POLICY PROPOSAL
!= AUTHORIZED POLICY PROPOSAL != POLICY CANDIDATE != POLICY AUTHORIZATION
!= POLICY ACTIVATION != CONTROL AUTHORIZATION != PHYSICAL ACTUATION
```

Each distinction requires a separate artifact and a separate authorization where applicable.
`POLICY PROPOSAL != POLICY`; `POLICY INTENT != EXECUTABLE POLICY RULE`.
A recommendation can inform a policy proposal but cannot automatically create one. An authorized
proposal cannot automatically create a candidate. There is no event subscriber, outbox handler,
background materializer, runtime hook or implicit promotion for either transition in V1.

## 3. Relationship to GDSS-007

GDSS-007 is closed as `COMPLETED_GDSS_007_VERIFICATION_ADVERSARIAL_VALIDATION_AND_CLOSURE` and
published as `COMPLETED_CONTROLLED_GDSS_007_REMOTE_PUBLICATION_WITH_WARNINGS`.
Its architecture and plan remain unchanged. Source contracts are the existing decision domain,
`recommendation-contracts.ts`, `recommendation-canonical.ts` and migration 0057.
The clean isolated A–F PostgreSQL closure is 46/46 PASS. P035-F01 retains classification
`NONDETERMINISTIC_POSTGRESQL_VERIFICATION_ASSERTION`, historical severity BLOCKING, status REMEDIATED,
10/10 isolated executions and 60/60 tests PASS. These are inherited records, not new P038 test runs.
The principal fixture warning remains `TEST_ENVIRONMENT_HYGIENE_WARNING`, `NON_BLOCKING`; only a clean
isolated disposable database is authoritative for future verification.

GDSS-008 reads exact source artifacts and their lifecycle projections. It adds no authority to
GDSS-007, changes no decision, preference or risk profile, and never treats outcome observation as
validation evidence. Parent model/evidence/claim identities remain distinguishable from proposals.

## 4. Relationship to M7

`GDSS PolicyProposal != M7 ControlledPolicyVersionCandidate`.
The existing `ControlledPolicyVersionRepository.createOrGet` loads
`control_policy_promotion_proposals`, promotion assessments and strategy candidates to materialize
`control_controlled_policy_version_candidates`. That is a distinct M7.2 chain. Its `proposalId` is
not a GDSS proposal ID; shared vocabulary does not establish compatibility.
V1 must not import/call that repository, its materializer, activation repositories or promotion
services. It must not write M7 tables or reuse their proposal/assessment tables. No executable
configuration snapshot, strategy parameters, deployment artifact or operational binding belongs to
GDSS-008. The future translation boundary in section 32 is design-only.

## 5. Authority Model

```text
RecommendationAuthority = HUMAN_GOVERNED_DECISION_SUPPORT_ONLY
PolicyProposalAuthority = HUMAN_GOVERNED_PROPOSAL_ONLY
PolicyCandidateAuthority = NONE
PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE
```

This is the target V1 contract, not an authority enabled by P038. Before implementation the runtime
retains its inherited authority unchanged. Authorization is `AUTHORIZED FOR CONSIDERATION IN A
FUTURE POLICY-CANDIDATE GOVERNANCE PROCESS`; no caller may interpret it as approved/active/deployable
policy, control rule or actuator instruction. Authority fields are server constants, not client input.

## 6. Policy Proposal Identity

`PolicyProposalIdentity` contains persistence ID, project ID, stable canonical intent key, title,
creator and creation audit metadata. Unique `(project_id, canonical_key)` identifies a logical
intention, not an operational policy. Identity is immutable; semantic changes belong to versions.
The intention remains domain-neutral; no hydroponics, fertigation or temperature-control entities
enter core. One identity binds a single origin DecisionRecord; changing origin creates a new identity.
Before the first identity, a human project admin registers an immutable, unique canonical project
namespace in `gdss_policy_proposal_project_namespace` (project FK plus semantic namespace key).
Registration is a proposal-domain operation, not a project rename or source-table change. One namespace
per project and one project per namespace are enforced; no UUID/name fallback or automatic allocation.
The namespace is retained permanently for hash stability and cannot be reassigned to another project.

## 7. Policy Proposal Version

`PolicyProposalVersion` records identity, project, monotonically allocated version number,
predecessor exact ID/hash, schema version, draft revision, author, provenance and resource profile.
Its semantic package binds exact recommendation candidate, recommendation authorization, decision,
selected alternative, problem, comparison, sensitivity, robustness, preference/risk profile and
model/evidence/claim manifests. References include project, artifact type, ID, declared source
version when present, and verified content hash. Unversioned source events have an explicit event
schema version; no fabricated numeric version is assigned to them.

Content includes policy objectives, proposed constraints/conditions/thresholds, scope, validity,
monitoring, impact/risk assessments, supporting/adverse evidence, limitations, uncertainty,
tradeoffs, structured rationale and provenance. Persist canonical bytes plus `policy_proposal_hash`;
normalized children must reconstruct exactly those bytes. Lifecycle, audit timestamps and grants
are outside the scientific content. Only one effective nonterminal version per identity is allowed;
a successor is prepared separately and predecessor supersession occurs atomically at successor
assembly. Unique hashes deduplicate within identity; they do not merge distinct intentions.

## 8. Source Recommendation

Require `AUTHORIZED_CURRENT` from the exact candidate and exact authorization, matching hashes,
project, authorized scope and complete evidence basis. A stored `AUTHORIZED` status alone is
insufficient: revocation, supersession, expiry, unresolved triggers, changed bindings or absent
references fail closed. Reconcile hashes by recomputation/projection checks, not client assertions.
Validate at draft creation, assembly, review, authorization and each currentness read. A draft may
remain available for correction when sources become stale, but cannot progress.

## 9. Source Human Decision

V1 accepts only human `DecisionRecord.action = ACCEPT`, with exactly one selected alternative.
It must be in the recommendation's preferred alternatives, considered roster and authorized scope.
`REJECT`, `DEFER`, `REQUEST_MORE_EVIDENCE` do not provide policy intent. V1 also rejects
`SELECT_DIFFERENT_ALTERNATIVE`: an explicit override does not establish policy eligibility or
recommendation authorization for that alternative. A new governed recommendation, its authorization
and ACCEPT decision are required. Multi-selection requires separate future scope/composition design.
This conservative rule avoids interpreting a human override as an increase in scientific evidence.

Require exact decision hash, source authorization/candidate consistency, HUMAN actor provenance,
complete selected-alternative rows, no successor referencing `supersedes_decision_record_id`, and
no conflicting branches. GDSS-007 DecisionRecord has no explicit scope field. Define
`HumanDecisionScope` as the exact recommendation authorized scope restricted to the one selected
alternative; the proposal stores this derived snapshot and its derivation version/hash. Never
invent a scope in the source row or infer one from narrative. Exceptions recorded on the decision
remain visible; they cannot waive violated hard constraints or unacceptable risk for this transition.

## 10. Scope

Enforce `PolicyProposalScope <= HumanDecisionScope <= RecommendationScope <= DecisionProblemScope`.
The recommendation term means its effective authorized scope. Project, target, horizon, model and
alternative must match; domain sets may only shrink. Proposed time interval must be contained in
all finite source intervals. Asset class, process, system-state, operational-domain and population/
cohort qualifiers use versioned governed vocabulary references, not executable selectors. Each
qualifier must be explicitly admitted by the source scope; absence means unknown/unsupported,
never universal. New qualifier types need a reviewed contract revision, not arbitrary JSON keys.
Set containment, interval containment and typed predicate containment are separate checks.
V1 supports only provable conjunction narrowing; unknown semantic implication returns
`POLICY_PROPOSAL_SCOPE_MISMATCH`. No arbitrary code/SQL/regex expression proves scope.

## 11. Objectives

`PolicyObjective` has stable key, exact source objective binding, target quantity/unit, intended
direction, declarative intended outcome and derivation rationale. Each maps to at least one existing
DecisionProblem objective. All required source objectives remain represented or explicitly marked
unchanged; no objective is invented or silently dropped. Policy wording may clarify intent but
cannot claim performance unsupported by the source. Acceptance conditions do not become execution.

## 12. Constraints

`PolicyConstraint` has key, category MANDATORY/PROHIBITIVE/ADVISORY, source constraint/evaluation
bindings, applicability, declarative restriction, rationale and preservation disposition.
`DECISION CONSTRAINT != POLICY CONSTRAINT`: HARD/SOFT/ADVISORY analysis categories are not an
automatic mapping. A reviewed translation ledger covers every source constraint and preserves every
required hard restriction. A prohibition is independently justified; a soft analytical preference
cannot become mandatory merely through renaming. Exclusion requires structured inapplicability
proof within narrowed scope, human review, and no weakening of a required constraint.
Unknown hard feasibility or violated hard conditions block assembly and authorization.

## 13. Conditions

`PolicyCondition` states when a future policy could apply: governed quantity/vocabulary reference,
unit where relevant, comparator from a bounded declarative enum, threshold reference and scope.
V1 accepts conjunctions of `EQ`, `IN_SET`, `LT`, `LE`, `GT`, `GE`, `BETWEEN`; no recursive programs,
scripts, callbacks, cron schedules or executable trigger language. Sets have bounded canonical
members. These predicates are data used for review/containment only; no evaluator drives runtime.
Unknown values are explicitly UNKNOWN, requiring review; absence never evaluates true.

## 14. Thresholds

`ANALYTICAL THRESHOLD != POLICY THRESHOLD != CONTROL SETPOINT`.
`PolicyThreshold` binds source analytical threshold/bounds, quantity/unit, proposed finite decimal
value or interval, derivation method/version, uncertainty and human justification. A proposed
threshold outside a source-admitted envelope needs new upstream evaluation and cannot be waived
by proposal authorization. Changing thresholds after assembly requires successor/review. A value is
reviewable policy intent, never a command/setpoint or strategy-configuration parameter.

## 15. Monitoring Requirements

`PolicyMonitoringRequirement` declares required evidence quantity/type, quality, freshness,
review cadence, responsible human role and failure response of REVIEW_REQUIRED. Sensor/data/compute
needs are conceptual metadata. No subscriptions, topics, routing keys, collectors, telemetry flows,
provisioning or runtime jobs are created. Monitoring statements cannot assert data already exists.

## 16. Evidence Package

Required manifest: RecommendationCandidate, RecommendationAuthorization, DecisionRecord,
DecisionProblemVersion, selected AlternativeVersion, DecisionComparisonSet, SensitivityAssessment,
RobustnessAssessment for the selected alternative, RiskProfileVersion and PreferenceProfileVersion.
The complete source roster includes other considered/rejected alternatives, model/scenario/
evaluation bindings, GovernedPredictiveClaim, PredictiveCapabilityAssessment and PredictiveEvidenceSet
when the recommendation uses them. Conditional absence is explicit NOT_APPLICABLE plus rationale
and source proof; it is never a missing silently optional prerequisite. Store exact ID/version/hash
locators separately from semantic content bindings. Check source-to-source and source-to-child
relational consistency and artifacts, not just that each ID exists.

## 17. Adverse Evidence

Copy the full supporting, contradicting, negative and limiting reference manifest from the exact
recommendation; retain uncertainty, tradeoffs, rejected/inadmissible alternatives and limitations.
Narrowing scope may add an applicability annotation but cannot delete unfavorable evidence.
Reconcile expected counts and the complete set of semantic bindings. New adverse evidence blocks
currentness until reevaluated; no favorable-only selection or confidence uplift is allowed.

## 18. Policy Impact

Include a separate `PolicyImpactAssessment` in 008C (reviewed in 008D), with independent dimensions
for objectives, constraints, resources, compute/sensor/data requirements, human roles/workload,
review/monitoring burden, evidence maintenance, organizational dependencies and reversibility.
Each dimension records expected effect, bounds/unit where meaningful, knowledge state, source
bindings, assumptions and limitations. No sum or scalar rank. Rollback concept, withdrawal
feasibility and reversibility are conceptual governance properties; no rollback operation exists.

## 19. Policy Risk

Use a separate `PolicyProposalRiskAssessment`, frozen with the proposal, not an alias of
DecisionRiskProfile. `DECISION RISK != POLICY IMPLEMENTATION RISK != PHYSICAL ACTUATION RISK`.
Here implementation risk means adoption/governance feasibility (maintenance, staffing, monitoring,
interpretation, dependencies), not simulation of physical deployment. Dimensions carry source,
severity, likelihood knowledge, uncertainty, reversibility, recoverability, acceptance rule and
state ACCEPTABLE/CONDITIONALLY_ACCEPTABLE/UNACCEPTABLE/UNKNOWN. Unknown is never zero.
UNACCEPTABLE and UNKNOWN required dimensions block authorization. Conditional dimensions require
explicit bounded mitigations, responsible roles and accepted residual limitations. They cannot
change source risk acceptance or hide an unacceptable decision risk. No physical-risk approval.

## 20. Rationale

Normalize decision, evidence, constraint, risk, sensitivity, robustness, limitations, assumptions
and scope basis. Each assertion has a key, exact supporting/adverse semantic bindings, declared
knowledge state and applicability; explanatory text supplements these components. Required answers:
why consider this policy, which decision led to it, supporting and contradicting evidence, remaining
risk, limiting conditions and invalidating changes. Narrative alone never satisfies a basis.
No causal-effect claim is inferred from a counterfactual or proposal adoption expectation.

## 21. Lifecycle

```text
DRAFT -> EVIDENCE_ASSEMBLED -> REVIEW_REQUIRED -> REVIEWED
      -> AUTHORIZATION_REQUIRED -> AUTHORIZED_POLICY_PROPOSAL
```

Assembly freezes the complete hash and children in one transaction, then requests review.
REVIEWED means all mandatory reviews are affirmative on this exact hash; transition to
AUTHORIZATION_REQUIRED records completion, not a grant. Authorization is a separate immutable
entity. REJECTED is a human negative review outcome; WITHDRAWN and INVALIDATED are terminal effective
states, SUPERSEDED refers to a historical predecessor. DRAFT alone permits content edits with
expected draft revision; editing increments revision and invalidates draft hash/previews.
Assembly and later content are immutable, including evidence and assessments. REJECTED corrections
require a successor, not editing. No ACTIVE, DEPLOYED or EXECUTING states are defined.

Stored workflow history and derived currentness are separate. Read effective state with priority:
INVALIDATED > WITHDRAWN > SUPERSEDED > SOURCE_INVALIDATED > STALE_REVIEW_REQUIRED >
EXPIRED_REVIEW_REQUIRED > AUTHORIZED_POLICY_PROPOSAL > remaining workflow state.
SOURCE_INVALIDATED projects INVALIDATED; simultaneous reasons remain in diagnostics. Current
requires validFrom <= trusted DB time <= validThrough and reviewDue not passed; otherwise explicitly
NOT_YET_VALID or review required. No single stored status conceals temporal/dependency invalidity.

## 22. Human Review

`PolicyProposalReview` binds frozen proposal hash, reviewer principal/role, review-policy version,
source-currentness digest, scope digest, adverse disclosures, decision, reason and idempotency key.
Decisions: APPROVE_FOR_AUTHORIZATION, REJECT, REQUEST_REVISION, REQUEST_MORE_EVIDENCE,
REQUEST_SCOPE_NARROWING. V1 mandates separate semantic/evidence and adoption-risk review slots;
one independent qualified human may fill both with separate records. Every adverse reference must
be acknowledged. A blocking decision is not overwritten by a later approval; revised content uses
a successor. Missing evidence/scope requests block authorization. Review never changes thresholds.
If sources change after review, its currentness digest ceases to qualify; no silent reuse.

## 23. SoD

Required: proposal author != proposal authorizer; reviewer != proposal author. Reinforced V1 rule:
recommendation authorizer != policy proposal authorizer. This reduces authority concentration across
the analytical and policy-intent gates. Role equality never proves principal inequality; use the
verified canonical human principal. Reviewer may also authorize if independent of both authorship
and recommendation authorization. AI coauthorship never counts as independent review.

A single-admin SOD_EXCEPTION may waive named principal inequalities only, with human authenticated
request, explicit reason, operational necessity, identities/roles, affected checks and audit event.
It requires a server-configured project exception policy and current human eligibility; default
is disabled. An exception does not skip review slots or waive scope, evidence, risk, currentness,
resource or no-execution rules. AI cannot request, grant or use it. Hash-bound exception events are
included in authorization provenance. P038 does not configure any such policy.

## 24. Authorization

`PolicyProposalAuthorization` is a separate append-only human event referencing proposal version,
proposal hash, source/decision hashes, review manifest, currentness digest, exact accepted/narrowed
scope, authorization policy version, principal, reason and optional permitted SoD exception.
Check all prerequisites again inside the commit transaction with row/dependency locks; validate
HUMAN principal and DB-recorded review/actor provenance. Authorization cannot widen scope, change
thresholds/objectives, remove adverse evidence/uncertainty or improve quality. Its narrowed scope
is an overlay; frozen proposal bytes remain unchanged. One grant per proposal version, never a
second effective grant. Rejected authorization attempts create audit denials, not grants.

## 25. Authorized Policy Proposal

Effective `AUTHORIZED_POLICY_PROPOSAL` requires the separate grant and all currentness predicates.
It is consideration-ready intent only. Export/read includes proposal/grant hashes, currentness,
source versions, effective scope, limitations and all authority constants. Consumers must not
interpret a historical grant as current. A future transfer process must independently recheck all
facts; this export is not an M7 input accepted by existing endpoints.

## 26. Expiry

Require proposed `valid_from`, `valid_through`, `review_due` as UTC microsecond instants with
valid_from < valid_through and valid_from <= review_due <= valid_through. These are semantic proposal
values and enter its hash. They are bounded by every finite source window. Earliest source expiry,
proposal expiry or review deadline wins; no scheduler is necessary to stop presenting current.
Expiry projects EXPIRED_REVIEW_REQUIRED (source expiry also records stale-source cause).
No auto-renew; new evidence/validity requires a successor and fresh review/authorization.

## 27. Withdrawal

`PolicyProposalWithdrawal` is append-only, binding version, proposal/grant hash if granted, human
actor, reason, trusted timestamp and idempotency key. Allowed for drafts and assembled/granted
versions; preserve content, reviews and grants. Withdrawn never remains authorized-current and cannot
be reauthorized; a successor is independently governed. Withdrawal is local proposal governance,
not revocation or rollback of any M7 policy. Audit survives any retention/archive mechanism.

## 28. Supersession

Successor version carries exact predecessor ID/hash, correction rationale and new semantic hash.
Allocate under identity lock; no branches or duplicate effective versions. Freeze successor and
append predecessor supersession atomically; any grant on the predecessor remains historical only.
A failed successor leaves predecessor status intact. Source decision supersession invalidates all
dependent currentness immediately; no inferred replacement decision or proposal rebind occurs.

## 29. Currentness

Recompute against recommendation/grant/revocation, current unsuperseded decision, exact model,
evidence, claim, objective, constraint, preference/risk, scenario/evaluation, comparison, sensitivity
and robustness. Because existing GDSS-007 sources lack a universal dependency epoch, V1 must not
invent one: lock/check the concrete source rows/events and inspect exact successor/trigger relations.
Missing or unverifiable bindings fail closed. Read projections include checkedAt and reasons;
cached status is advisory and may never independently authorize an operation.

Currentness reads use one consistent database snapshot; authorization serialization is in section 36.
A source change after authorization makes subsequent reads non-current; it does not rewrite history.
If a source is provably tampered/invalid, project INVALIDATED; revocation, supersession, changed
semantics or incomplete revalidation project STALE_REVIEW_REQUIRED. A fresh unchanged-source review
can resolve a review-only trigger via an append-only resolution; material changes always require a
successor. A terminal source/withdrawal cannot be cleared by acknowledging a trigger.

## 30. Reevaluation

`PolicyProposalReevaluationTrigger` is immutable evidence of change, exact causal artifact/hash,
reason, effect and deduplication key. Events sequence OPEN -> ACKNOWLEDGED -> RESOLVED with verified
resolution basis; ACKNOWLEDGED never restores currentness. Required types:
RECOMMENDATION_REVOKED, RECOMMENDATION_EXPIRED, DECISION_SUPERSEDED, MODEL_CHANGED,
EVIDENCE_CHANGED, CLAIM_REVOKED, CLAIM_EXPIRED, OBJECTIVE_CHANGED, CONSTRAINT_CHANGED,
PREFERENCE_CHANGED, RISK_PROFILE_CHANGED, NEW_ADVERSE_EVIDENCE, POLICY_SCOPE_CHANGED,
SCENARIO_CHANGED, COMPARISON_CHANGED, SENSITIVITY_CHANGED and ROBUSTNESS_CHANGED.

All semantic changes produce stale/reevaluation required; verified integrity failure invalidates.
Review-only incompleteness produces REVIEW_REQUIRED, expiration produces EXPIRED_REVIEW_REQUIRED.
Triggers add diagnostics and never replace a proposal, create a candidate, activate policy or renew
a grant. Direct dependency checks protect reads even if trigger delivery is delayed or missing.

## 31. AI Governance

AI may draft wording, summarize rationale, identify policy implications, constraints, risks and
missing evidence. Provenance is HUMAN_AUTHORED, DETERMINISTICALLY_DERIVED or AI_ASSISTED and does not
increase authority. DETERMINISTICALLY_DERIVED describes content assisted by a human-requested,
versioned transformation; it never authorizes automatic proposal creation.
A human must explicitly initiate and adopt every origin binding and assembly. AI drafts stay DRAFT
until that adoption. Verified AI identity comes from trusted auth context, never request body flags.
AI cannot approve/review as authority, authorize, change decision/preference/risk, use SoD exception,
create M7 candidates, activate policy or authorize control/actuation. Human acceptance of AI text
is recorded; masquerading as a human service account is denied and audited.

## 32. M7 Transfer Boundary

Concept only, OUT OF SCOPE for V1:
`AUTHORIZED_POLICY_PROPOSAL -> FUTURE TRANSFER REQUEST -> CONTROLLED POLICY CANDIDATE`.
A later architecture/authorization must define exact source grant/currentness, explicit human
request, translation version/hash, candidate strategy configuration, eligibility assessment,
independent M7 checks, SoD, provenance, failure recovery and replay protection. No existing M7
`proposalId` API is overloaded. No translation function, adapter, endpoint, outbox or candidate table
is introduced in 008F. 008F owns a documented rejection boundary and future interface vocabulary;
it has no persistence need and therefore no 0063 migration. NO AUTOMATIC TRANSFER.

## 33. Persistence

Future PostgreSQL design only; no DDL accompanies P038. Every table includes project_id and exact
project-scoped parent FKs. Child keys are unique within version; no cascading deletes of history.

| Proposed table | Representation and constraints | Owner |
|---|---|---|
| gdss_policy_proposal_project_namespace | immutable project-to-semantic-namespace registry; unique project and namespace key; human admin only | A |
| gdss_policy_proposal_identity | logical intent key, origin decision; unique project/key; immutable | A |
| gdss_policy_proposal_version | identity/version/predecessor, draft revision, canonical bytes/hash, workflow projection; unique identity/version and identity/hash | A |
| gdss_policy_proposal_recommendation_ref | one exact candidate and authorization tuple; hashes and scopes independently reconciled | A |
| gdss_policy_proposal_decision_ref | one exact decision, selected alternative, derived human scope and derivation hash | A |
| gdss_policy_proposal_objective | keyed source objective translation, required coverage | B |
| gdss_policy_proposal_constraint | typed category, source ledger and preservation justification | B |
| gdss_policy_proposal_condition | flat conjunction member, typed comparator and threshold refs | B |
| gdss_policy_proposal_threshold | quantity/unit, exact decimal bounds, derivation and source envelope | B |
| gdss_policy_proposal_monitoring_requirement | bounded quantity/quality/freshness/role requirements; no subscription | B |
| gdss_policy_proposal_evidence_ref | exact typed refs, polarity, source manifest coverage; unique semantic binding | C |
| gdss_policy_proposal_limitation | key/category/knowledge/applicability; source adverse links | C |
| gdss_policy_proposal_impact_assessment | one frozen manifest per version; bounded JSONB dimensions | C |
| gdss_policy_proposal_risk_assessment | one frozen manifest per version; bounded JSONB dimensions and acceptance rules | C |
| gdss_policy_proposal_review | append-only review slot, reviewer, exact hashes, decision/reason; unique scoped idempotency | D |
| gdss_policy_proposal_authorization | separate one-per-version human grant, narrowed scope, review digest, hash | D |
| gdss_policy_proposal_withdrawal | one effective withdrawal/version; append-only actor/reason/grant binding | E |
| gdss_policy_proposal_reevaluation_trigger | immutable causal binding/type/effect, semantic deduplication | E |
| gdss_policy_proposal_reevaluation_event | append-only resolution sequence and exact basis | E |
| gdss_policy_proposal_audit_event | append-only aggregate sequence, actor, operation, before/after hashes, reason, request key | A; extended D/E |

Bounded JSONB is limited to scope vocabulary qualifiers, rationale components, typed assessment
dimensions and frozen manifests; evidence/objectives/constraints/conditions/thresholds/reviews/grants
use relational rows for FK/coverage/uniqueness checks. Do not use unconstrained freeform metadata.
DB checks enforce known keys/types, finite decimals, sizes and nested limits. Composite FKs include
project and parent identity; triggers reconcile referenced hashes/version/lineage, not just UUIDs.
Post-assembly freeze covers children and assessment JSONB. Human-event tables prohibit UPDATE/DELETE.
Critical scope, resource, exact-reference, source-currentness and grant checks repeat in DB triggers
under the same locks. Application principals cannot disable triggers or write M7 tables. A dedicated
restricted proposal DB role and trusted human principal mapping are implementation prerequisites;
`actor_kind=HUMAN` in untrusted JSON is not DB authentication. Owner/superuser tests may bypass
triggers only for explicit negative harness setup, never as a product path.

## 34. Hashing

`CONTENT_HASH != PERSISTENCE_ID`. Use SHA-256 of domain separator, a single NUL byte and UTF-8
canonical JSON; separator for proposal is `midd:gdss:policy-proposal:v1`. Canonical schema V1 sorts
object keys lexicographically by code point, normalizes strings to NFC, encodes finite decimal
values as normalized decimal strings (no exponent, negative zero becomes zero), and UTC instants
as integer microsecond strings. Set-like arrays sort by semantic key and reject duplicates;
ordered priorities retain explicit ordinal. Missing, null, unknown and explicit zero differ.

Include project semantic namespace, logical intent key, explicit semantic version/predecessor
content hash, origin recommendation/authorization/decision content hashes, selected alternative
content hash/key, problem/comparison/sensitivity/robustness/risk/preference/model/evidence/claim
content bindings, scope, objectives, constraints, conditions, thresholds, validity, monitoring,
impact/risk, all adverse evidence/limitations/uncertainty and structured provenance/rationale.
Exclude persistence UUIDs, server-assigned version allocation number, DB timestamps, sessions,
workers, retries, idempotency keys, physical row order and workflow state. Semantic validity dates
are included; incidental audit dates are excluded. Different projects remain distinct via immutable
canonical project namespace; absence of a stable namespace blocks hashing, not fallback to random ID.

Store exact persistence ID/version/hash reference manifest alongside a canonical semantic manifest.
Resolve UUID locators into source content hashes and stable semantic keys before hashing; keep exact
FK locators outside the semantic bytes. Imported GDSS-007 hashes may internally include legacy IDs:
treat those existing hashes as opaque source content identities, never change their algorithm.
Re-materializing 008 with different local row UUIDs but the same verified semantic source identities
must hash identically; substituting a source with a different hash must change the proposal hash.
Golden vectors must explicitly test that distinction and reconcile every locator to its hash.

Separate separators `midd:gdss:policy-proposal-authorization:v1`, `-review:v1`, `-withdrawal:v1`,
`-impact:v1`, `-risk:v1` and `-reevaluation:v1` use the same encoding rules with the complete prefix
`midd:gdss:policy-proposal` before each suffix. Authorization hash includes proposal/source hashes,
review semantic hashes, grant scope, human principal semantic key, reason, authorization-policy
version and explicit exception record hash; excludes grant UUID/session/idempotency/audit timestamp.
Any semantic change invalidates the corresponding hash; grants cannot overwrite proposal content.

## 35. Idempotency

Scientific assembly is create-or-get within `(project, identity, policy_proposal_hash)`; draft
creation/editing uses explicit request keys plus expected draft revision. Human events require
explicit `(project, operation, actor, idempotency_key)` uniqueness and a canonical request digest.
Same key/same digest returns the same recorded event; same key/different digest is
IDEMPOTENCY_CONFLICT. Replay of an old grant returns history with freshly computed currentness;
it does not restore effective authority after withdrawal/expiry. Denial audit keys never collide
with successful event keys. Failed transactions leave no partial semantic children or grant.

## 36. Concurrency

Lock order: project/decision quota guard, identity, proposal version, then source rows in deterministic
table/key order, then review/grant/withdrawal events. Successor allocation and assembly serialize
per identity; authorization and withdrawal serialize on the same version. Source decision successor,
recommendation revocation and dependency mutations must contend on the actual rows/FK locks or be
observed through SERIALIZABLE predicate checks. An integration test must prove that the existing
007 write paths conflict appropriately; a new lock convention followed only by 008 is insufficient.
If an existing source path cannot participate without changes, implementation stops for a scoped
authorization request; this design does not authorize modifying GDSS-007 through the back door.

Use SERIALIZABLE transactions with bounded retries (maximum three) for authorization/source races,
unique indexes for version/grant/idempotency, parent locks for quota counts, and transaction-local
source and normalized-manifest reconciliation. On retry exhaustion return a concurrency conflict,
not success. Linearization order is explicit: source change first means no grant; grant first may
exist historically but immediately becomes non-current after source change. Withdrawal first denies
grant; grant first followed by withdrawal preserves both history and withdrawn currentness. Two
effective grants, one-over persisted children and authorization/withdrawal split-brain are forbidden.

## 37. RBAC

Future project-scoped permissions, checked independently of existing `edit_policies`:

| Permission | V1 roles/principal | Restrictions |
|---|---|---|
| AUTHOR_POLICY_PROPOSAL | human operator/admin; AI draft assistant only through distinct draft capability | human origin/adoption required; no assembly by AI |
| REVIEW_POLICY_PROPOSAL | human admin with review qualification | mandatory slots; author separation |
| AUTHORIZE_POLICY_PROPOSAL | human admin | reinforced SoD, currentness, one exact grant |
| WITHDRAW_POLICY_PROPOSAL | human author with operator/admin or project admin | project scoped, explicit reason, no AI |
| AUDIT_POLICY_PROPOSAL | authenticated viewer/operator/admin | project scope; full adverse/currentness history |

No privilege inheritance from active-policy editing. Service, API and DB role boundaries all deny
AI authority. Project flags or admin status cannot increase PolicyAuthority. Assembly/adoption is an
explicit AUTHOR_POLICY_PROPOSAL human operation; hashing preview by AI grants no seal capability.

## 38. Errors

| Code | Fail-closed meaning |
|---|---|
| POLICY_PROPOSAL_NOT_DRAFT / POLICY_PROPOSAL_FROZEN | draft edit precondition or frozen-content mutation |
| POLICY_PROPOSAL_SCOPE_MISMATCH | no provable contained scope or threshold applicability |
| POLICY_PROPOSAL_SOURCE_NOT_CURRENT | exact upstream chain missing, stale, expired or hash mismatch |
| POLICY_PROPOSAL_DECISION_REQUIRED | absent/non-ACCEPT/multi-selected/AI/superseded human decision |
| POLICY_PROPOSAL_EVIDENCE_INSUFFICIENT | incomplete manifests, required adverse evidence or hard feasibility |
| POLICY_PROPOSAL_RISK_UNACCEPTABLE | unacceptable/unknown required adoption risk |
| POLICY_PROPOSAL_REVIEW_INCOMPLETE | missing/blocking/obsolete exact review slots |
| POLICY_PROPOSAL_AUTHORIZATION_FORBIDDEN | principal, SoD or grant-policy denial |
| POLICY_PROPOSAL_STALE / POLICY_PROPOSAL_WITHDRAWN | cannot progress effective non-current/withdrawn artifact |
| POLICY_CANDIDATE_AUTHORITY_FORBIDDEN | attempted candidate transfer/materialization |
| POLICY_ACTIVATION_AUTHORITY_FORBIDDEN | attempted activation or deployable rule |
| CONTROL_AUTHORITY_FORBIDDEN / PHYSICAL_AUTHORITY_FORBIDDEN | attempted control/physical effect |
| CROSS_PROJECT_POLICY_REFERENCE | any project-aware reference mismatch |
| IDEMPOTENCY_CONFLICT | key reused with changed canonical request |
| RESOURCE_LIMIT_EXCEEDED | payload/count/dimension bound exceeded |
| POLICY_PROPOSAL_CONCURRENCY_CONFLICT | stale draft revision, serialization/retry exhaustion |
| POLICY_PROPOSAL_INTEGRITY_FAILURE | canonical bytes/projection/hash disagreement |

Future HTTP semantics: 400 malformed payload, 403 authority/project permission denial, 404 scoped
absence, 409 lifecycle/hash/idempotency/concurrency conflict, 422 scientific/scope/completeness
precondition, 413 resource overflow. Errors include bounded code/field/resource/limit and request
correlation, never credentials or other-project existence. Audit denial without disclosing secrets.

## 39. Security

Threat controls and tests are assigned in sections 41–42. Recommendation-to-policy escalation is
blocked by explicit human initiation, ACCEPT and independent proposal grant. Decision substitution
and stale reuse require exact source hashes, scope and successor checks. Constraint removal,
threshold tampering, evidence omission and risk suppression fail manifest/translation reconciliation.
Scope widening fails typed subset checks; AI elevation and SoD bypass fail trusted identity checks.
Cross-project injection fails composite FK and source-row reconciliation. Grant replay returns
history, not currentness. Withdrawal suppression fails direct DB read and append-only audit.
Direct M7 creation, policy activation and control/actuator escapes fail schema allowlists, import/
call-graph checks and database role restrictions. Denials are append-only with actor and reason.
Bounded strings and references cannot be interpreted as SQL, code or commands. Reject operational
payloads at nested structured fields and artifact manifest boundaries, including aliases/unknown keys.

## 40. Resource Limits

Proposed V1 profile `GDSS_POLICY_PROPOSAL_LIMITS_V1` is a conservative admission budget, not an
observed capacity claim. Limits align with 007 objective/constraint rosters and bounded human review;
no benchmark below has yet run. Future G must measure wall time, peak RSS, canonical bytes, DB lock
wait/transaction time and exact persisted counts at 50%, 100% and concurrent one-over. Hardware,
runtime, sample size, cold/warm runs and non-SLA results must be recorded; resource profile changes
need a versioned contract review. Counts include failed/rejected/history where stated, never erase
unfavorable rows to regain capacity.

| Resource | V1 cap | Rationale | 50% / 100% / rejected one-over |
|---|---:|---|---|
| Logical proposal identities per DecisionRecord | 16 | bounds competing policy intentions and review load; versions share the same intention quota | 8 / 16 / 17 |
| Objectives per version | 16 | full 007 maximum objective coverage without new objectives | 8 / 16 / 17 |
| Constraints per version | 64 | full 007 required-constraint roster | 32 / 64 / 65 |
| Conditions per version | 64 | one declared applicability condition per possible constraint | 32 / 64 / 65 |
| Thresholds per version | 64 | bounded typed threshold ledger, shared refs avoid duplicate bounds | 32 / 64 / 65 |
| Monitoring requirements per version | 32 | at most two primary evidence checks per objective; aggregate when necessary | 16 / 32 / 33 |
| Evidence refs per version | 10000 | preserves 007 maximum evidence roster; no truncation | 5000 / 10000 / 10001 |
| Reviews per version, including negative/history | 32 | two mandatory slots and bounded additional specialist submissions; exhaustion needs successor | 16 / 32 / 33 |
| Impact dimensions per assessment | 16 | covers the independent organizational/resource axes with explicit extensions | 8 / 16 / 17 |
| Risk dimensions per assessment | 32 | bounded adoption-risk analysis independent of inherited source-risk references | 16 / 32 / 33 |

Additional guards: 16 MiB canonical proposal package (8/16/one byte over MiB), 256-character semantic
keys, 8000-character rationale component, 64 qualifier members/dimension, 64 members/condition set,
64 limitations and 64 assumptions; no nesting deeper than the fixed typed schemas. Manifest limits
must include all required adverse source refs; if the package cannot fit, reject for explicit scope/
upstream redesign, never silently omit. Quotas are validated before allocation and under parent locks
at commit; SQL bypass and race tests must prove the same caps. No immutable audit-history truncation;
project storage exhaustion fails admission with retention handled outside V1, never delete history.
Namespace registration is unique per project rather than a recurring quota; namespace key obeys the
256-character bound. Source-ref manifests and normalized risk/impact records remain inside the
proposal package byte budget, including all mandatory/adverse dependencies.

## 41. Invariants

The matrix below is a future executable-proof obligation, not a PASS report.
Mechanisms: U = unit/contract/hash; P = PostgreSQL direct-bypass/isolation/race;
S = static import/call/schema/role boundary; W = complete human workflow.

| ID | Invariant | Enforcement / proof | Owner | Evidence |
|---|---|---|---|---|
| POL-INV-01 | Recommendation != PolicyProposal | Explicit human initiation and ACCEPT required; no event materializer | A | U/P/W |
| POL-INV-02 | HumanDecision != PolicyProposal | Separate proposal identity/version, no implicit conversion | A | U/P/W |
| POL-INV-03 | PolicyProposal != AuthorizedPolicyProposal | Separate exact human grant and review | D | U/P/W |
| POL-INV-04 | AuthorizedPolicyProposal != PolicyCandidate | No transfer API/materializer; no M7 writes | F | S/P |
| POL-INV-05 | PolicyCandidate != PolicyAuthorization | Existing M7 grant remains separate and untouched | F | S/W |
| POL-INV-06 | PolicyAuthorization != PolicyActivation | No activation calls or artifacts | F | S/P |
| POL-INV-07 | PolicyActivation != ControlAuthorization | Proposal grants never map to control capability | F | S/P |
| POL-INV-08 | ControlAuthorization != PhysicalActuation | No physical authority/subscription/endpoint | F | S/P |
| POL-INV-09 | Proposal scope cannot exceed human decision scope | Typed subset and exact selected alternative | A | U/P |
| POL-INV-10 | Authorization cannot widen proposal scope | Narrow overlay only, frozen bytes unchanged | D | U/P |
| POL-INV-11 | Adverse evidence remains traceable | Complete source roster plus negative/limiting references | C | U/P/W |
| POL-INV-12 | Unknown risk != zero risk | Required UNKNOWN prevents grant | C/D | U/P |
| POL-INV-13 | Policy implementation risk != decision risk | Separate assessment with adoption axes | C | U/P |
| POL-INV-14 | Authorization cannot improve evidence | No scientific mutation or quality uplift | D | U/P |
| POL-INV-15 | Authorization cannot remove uncertainty | Frozen limitations and unknown semantics | C/D | U/P |
| POL-INV-16 | AI cannot authorize policy proposal | Trusted principal/DB-role human-only grant | D | U/P/W |
| POL-INV-17 | AI cannot create policy candidate as authority | No candidate capability or M7 write path | F | S/P |
| POL-INV-18 | AI cannot use SoD exception | Human-only trusted exception event | D | U/P |
| POL-INV-19 | Author != authorizer unless governed exception | Named independent principals, reasoned exception policy | D | U/P |
| POL-INV-20 | Source recommendation must be exact and current | Grant/revocation/expiry/dependency reconciliation | A/E | U/P/W |
| POL-INV-21 | Source decision must be exact and current | Human ACCEPT single selection, no superseding record | A/E | U/P/W |
| POL-INV-22 | Proposal is non-executable | Strict schemas and no runtime consumers | B/F | U/S/P |
| POL-INV-23 | Proposal cannot contain control command | Nested allowlist rejects commands and aliases | B/F | U/S/P |
| POL-INV-24 | Proposal cannot contain actuator endpoint | No physical locators, topics or routes | B/F | U/S/P |
| POL-INV-25 | Decision constraint != policy constraint | Explicit reviewed translation ledger | B | U/P/W |
| POL-INV-26 | Analytical threshold != policy threshold | Exact derivation and source envelope | B | U/P |
| POL-INV-27 | Policy threshold != control setpoint | No strategy configuration/command export | B/F | U/S |
| POL-INV-28 | Expired proposal != current proposal | Trusted-time projection, no auto-renew | E | U/P |
| POL-INV-29 | Withdrawn proposal cannot remain authorized-current | Withdrawal takes precedence over historical grant | E | U/P/W |
| POL-INV-30 | Superseded proposal cannot remain current | One effective version and atomic successor assembly | E | U/P |
| POL-INV-31 | Evidence change requires reevaluation | Exact direct read plus causal trigger | E | U/P |
| POL-INV-32 | Recommendation revocation requires reevaluation | Source revocation race and missing-trigger proof | E | U/P/W |
| POL-INV-33 | Decision supersession requires reevaluation | Source successor race and exact currentness | E | U/P/W |
| POL-INV-34 | Policy proposal risk remains multidimensional | Typed dimensions, no universal scalar | C | U/P/S |
| POL-INV-35 | No universal policy score | Reject policy_score/proposal_score/policy_confidence/overall_policy_value | B/C | U/S/P |
| POL-INV-36 | Policy impact remains multidimensional | Independent effects, burden, reversibility and unknowns | C | U/P |
| POL-INV-37 | Proposal history is append-only | Frozen content and immutable human/reevaluation/audit events | A/D/E | P/W |
| POL-INV-38 | Content hash != persistence ID | UUID-independent semantic manifest, exact locator reconciliation | A/C/D | U/P |
| POL-INV-39 | Cross-project proposal references fail closed | Composite FK plus exact hashes and namespace | A–E | U/P |
| POL-INV-40 | Policy/Control/Physical authority remain NONE | Proposal-only authority constants across all artifacts | F/G | U/S/P/W |

Additional mandatory proof obligations: exact canonical/projection reconciliation, one grant/version,
serializable withdrawal/source races, draft-only mutability, quota races, and reinforced SoD.
All forty invariants must have an enabled executable proof; static-only claims require actual
checked dependency/role artifacts. A documented claim is not a passing test.

## 42. Adversarial Cases

Each case must test rejection, unchanged protected state, bounded error and append-only denial audit
where a transaction can safely record it. No test may grant policy/control/physical authority.

| # | Attack | Required result | Owner |
|---|---|---|---|
| 01 | AI authorizes policy proposal | AUTHORIZATION_FORBIDDEN; no grant | D |
| 02 | Revoked recommendation but proposal presented current | STALE_REVIEW_REQUIRED, including absent/delayed trigger | E |
| 03 | Superseded human decision but proposal presented current | STALE_REVIEW_REQUIRED from exact successor lookup | E |
| 04 | Proposal widens recommendation scope | SCOPE_MISMATCH before assembly and via SQL bypass | A |
| 05 | Authorization widens proposal scope | SCOPE_MISMATCH; frozen scope intact | D |
| 06 | Adverse evidence omitted | EVIDENCE_INSUFFICIENT with exact missing bindings | C |
| 07 | Unacceptable adoption risk hidden | Manifest integrity/risk rejection; no grant | C/D |
| 08 | Unknown risk converted to zero | UNKNOWN retained; grant denied | C |
| 09 | Policy threshold silently becomes control setpoint | Schema/static boundary rejection; no executable configuration | B/F |
| 10 | Proposal embeds MQTT topic | Nested operational-field rejection | B/F |
| 11 | Proposal embeds actuator endpoint | PHYSICAL_AUTHORITY_FORBIDDEN | B/F |
| 12 | Proposal automatically creates M7 candidate | No call path; M7 write privilege denied | F |
| 13 | Proposal directly activates policy | POLICY_ACTIVATION_AUTHORITY_FORBIDDEN | F |
| 14 | Proposal directly calls Control Engine | CONTROL_AUTHORITY_FORBIDDEN; no network call | F |
| 15 | Cross-project recommendation injected | CROSS_PROJECT_POLICY_REFERENCE including same-hash substitution | A |
| 16 | Recommendation version silently substituted | SOURCE_NOT_CURRENT/integrity rejection | A/E |
| 17 | Author self-authorizes without SoD exception | AUTHORIZATION_FORBIDDEN; no grant | D |
| 18 | Withdrawn proposal remains current | WITHDRAWN even on grant replay/racing read | E |
| 19 | Expired proposal auto-renewed | EXPIRED_REVIEW_REQUIRED; no new window/grant | E |
| 20 | AI converts draft into authorized proposal | Human adoption/review/grant checks independently deny | A/D |
| 21 | Recommendation authorizer also authorizes proposal | Reinforced SoD denial unless valid named human exception | D |
| 22 | Decision selects an override or multiple alternatives | DECISION_REQUIRED; no recommendation-only or override escalation | A |
| 23 | Source revocation races with authorization | Serializable linearization, never current after revocation | D/E |
| 24 | One-over evidence/review count raced via SQL | RESOURCE_LIMIT_EXCEEDED and exact persisted cap | C/D |
| 25 | UUIDs/order/session change without semantic change | Same 008 hash; different source hash changes it | A/C |
| 26 | Same idempotency key with changed reason or scope | IDEMPOTENCY_CONFLICT; original event intact | D/E |
| 27 | Assembled threshold or evidence edited via SQL | FROZEN/immutable rejection | B/C |
| 28 | Withdrawal races with two grant requests | At most one historical grant and correct withdrawn projection | D/E |

## 43. Non-goals

V1 excludes automatic policy generation, automatic policy candidate creation, policy approval,
policy activation, control execution, physical actuation, reinforcement learning, online policy
optimization, automatic reward learning, automatic preference learning, self-modifying policy and
real-time autonomous policy switching. No provisioning, runtime rollback, M7 mutation or UI.
No `mqtt_topic`, `amqp_route`, `actuator_id`, `physical_endpoint`, `control_command`,
`runtime_command`, `deployment_target` or `activation_command` is accepted as proposal structure.
No universal `policy_score`, `proposal_score`, `policy_confidence` or `overall_policy_value`.

## 44. Phase Decomposition

| Phase | Ownership | Proposed migration, not created |
|---|---|---|
| 008A | Identity, source binding, human scope, canonical core, audit | 0058 after 0057 |
| 008B | Objectives, translation, conditions, thresholds, monitoring | 0059 after 0058 |
| 008C | Evidence, impact, independent adoption risk, frozen assembly | 0060 after 0059 |
| 008D | Review, human authority, reinforced SoD, separate grant | 0061 after 0060 |
| 008E | Currentness, reevaluation, withdrawal, supersession | 0062 after 0061 |
| 008F | Static M7 transfer boundary and future interface contract only | none; 0063 unallocated |
| 008G | Full verification, adversarial validation and closure | none |

Stages require separate explicit implementation authorization. A–C can prepare/assemble intent;
only D can define proposal grants once E currentness gates are available. Until E is implemented
and verified, D grant paths remain disabled. F may strengthen rejection tests but cannot create a
transfer implementation. Production enablement, if ever separately authorized, requires A–G closure.

## 45. Closure Criteria

Design acceptance: coherent separated artifacts, explicit ACCEPT rule, derived human scope,
source-currentness proof, multidimensional risk/impact, complete persistence/API/limits/errors,
forty invariants, twenty-eight adversarial cases and seven fully specified future phases.
Implementation closure later requires all 40 invariant proofs, 28 adversarial cases, every resource
50%/100%/one-over boundary/race, golden hashes, SQL bypass/append-only tests, clean isolated
PostgreSQL A–E end-to-end workflow and source revocation/decision/withdrawal races; no critical skips.
Verify fresh migration chain 0057 through 0062 and isolated upgrade/downgrade cycles only under later
explicit authorization. Source Alembic stays 0057 throughout P038. No principal fixture cleanup.
Run future unit/integration/regression, TypeScript, production build and static M7/control/physical
scans; record versions/hardware/counts and retained adverse evidence. Historical warnings remain.
No claim of executable GDSS-008 evidence is made by this architecture-only contract.

```text
GDSS_008A_NOT_AUTHORIZED
GDSS_008B_NOT_AUTHORIZED
GDSS_008C_NOT_AUTHORIZED
GDSS_008D_NOT_AUTHORIZED
GDSS_008E_NOT_AUTHORIZED
GDSS_008F_NOT_AUTHORIZED
GDSS_008G_NOT_AUTHORIZED

COMPLETED_GDSS_008_ARCHITECTURE_AND_IMPLEMENTATION_PLAN_CONTRACT
YES — AUTHORIZED POLICY PROPOSAL WITHOUT POLICY EXECUTION AUTHORITY
```

The closure question is answered YES as a coherent design: a governed recommendation and explicit
human ACCEPT can support reviewed, versioned and auditable proposal consideration without creating
candidate, policy, control or physical execution authority. Implementation remains unauthorized.
