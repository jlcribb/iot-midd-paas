# GDSS-006E — Implementation Evidence

Prompt: `MIDD-GDSS-P022-R1`
Status: `COMPLETED_GDSS_006E_VALIDITY_DOMAIN_AND_PREDICTIVE_EVIDENCE_ASSEMBLY`

## A. Baseline

- Checkout: `/Users/joseluis/dev/iot-midd-paas-auth-work`.
- Branch: `main`; baseline HEAD: `dee81328f4a73b525f8d7236d8ee799044b9cabc`.
- Initial source and principal database revision: single Alembic head/current `0047`.
- Existing uncommitted GDSS-006A/B/C/D material was preserved without reopening GDSS-001..005.

## B. Scope Implemented

Implemented only executable validity-domain assessment, empirical-support position assessment,
immutable predictive-evidence assembly, first-class adverse evidence, completeness and a seven-axis
strength profile. No capability assessment, predictive claim, claim authorization, evidence transfer,
automatic revalidation or physical authority was introduced.

## C. Files Changed

- Domain: `evidence-contracts.ts`, `evidence-canonical.ts`, `evidence-engine.ts`,
  `evidence-diagnostics.ts`, `evidence-authorization.ts` and validation barrel exports.
- Persistence/service: `gdss-predictive-evidence.repository.ts`,
  `gdss-predictive-evidence.service.ts`, strict request schemas and DB error mappings.
- HTTP: project-scoped routes for domain and position assessments, negative findings, conflicts,
  limitations, evidence sets and strength profiles.
- Database: `0048_gdss006e_domain_assessment_predictive_evidence.py`.
- Verification: `gdss-predictive-evidence.test.ts` and the extended PostgreSQL custody/run suite.
- Documentation: this evidence record and the GDSS-006 implementation-plan status.

## D. Migration 0048

Migration `0048`, directly based on `0047`, adds eleven normalized tables: domain validity and
predicate assessments; predictive position; negative findings, conflicts and limitations; evidence
sets and references; completeness; strength profiles and axis assessments. Composite project/scope
foreign keys, allowlists, unique semantic hashes, reference-count guards and immutable-history
triggers protect the boundary. Isolated cycle `0047 -> 0048 -> 0047 -> 0048`: PASS.

## E. Domain Evaluation Model

`DomainValidityAssessment` binds the exact project, model version/hash, reused GDSS-006A validity
domain version/hash, validation run, target, horizon and canonical context snapshot. Its only results
are `WITHIN_VALIDITY_DOMAIN`, `NEAR_DOMAIN_BOUNDARY`, `OUTSIDE_VALIDITY_DOMAIN` and
`DOMAIN_UNKNOWN`; no boolean in-domain shortcut exists.

## F. Domain Predicate Execution

Numeric and parameter ranges enforce finite typed values, exact unit key/revision, bounds and declared
inclusivity. Temporal ranges compare canonical integer microseconds. Categories use exact membership
and boolean predicates use the existing declarative expected value. Missing, mistyped or unit-
incompatible values fail closed to `DOMAIN_UNKNOWN`; no fuzzy or AI inference is used.

## G. Boundary Evaluation

No arbitrary distance or undeclared tolerance was invented. In V1 an included numeric or temporal
bound is `NEAR_DOMAIN_BOUNDARY` only when the context equals that exact declared bound. Otherwise an
eligible interior point is `WITHIN_VALIDITY_DOMAIN`; an exclusive-bound equality is outside.

## H. Predictive Position

Position results are exactly `INTERPOLATION`, `BOUNDARY_PREDICTION`, `EXTRAPOLATION` and
`UNKNOWN_POSITION`. Domain unknown remains position unknown; outside-domain is extrapolation. A point
inside the declared domain can still be extrapolation when it lies outside governed empirical support.

## I. Empirical Support

Support dimensions cover numeric/input/parameter ranges, temporal regimes, exact category sets and
boolean states for the evidence's target and horizon. Every dimension names governed domain-assessment
IDs. The service recomputes min/max or exact sets from those assessments and rejects caller-expanded
envelopes. V1 intentionally has no convex hull, clustering, learned OOD or fuzzy geometry.

## J. PredictiveEvidenceSet

The immutable set binds exact model, protocol, domain, partition, snapshot, target, horizon, runs,
pair sets, domain assessments and position assessments. Assembly discovers all in-scope GDSS-006A..E
artifacts itself, verifies core and protocol-required evidence, writes a canonical manifest plus
relational projection and uses advisory locking for deterministic idempotency. Callers cannot select
individual favorable results.

## K. Evidence References

Each reference stores exact `artifact_type`, `artifact_id`, `artifact_hash`, `source_phase`, role and
reference hash. Roles are `SUPPORTING`, `CONTRADICTING`, `LIMITING`, `CONTEXTUAL` or `INVALIDATING`.
Database guards reject cross-scope/hash-invalid references, non-sequential materialization, late
addition, update or deletion.

## L. Negative Evidence

`PredictiveEvidenceNegativeFinding` represents underperforming baselines, high bias, low coverage,
insufficient uncertainty, out-of-domain use, unknown temporal integrity and compromised independence.
All matching scope rows are automatically included as contradicting evidence; a favorable-only set
cannot be produced through the service. The source artifact and source hash are verified by both
service/repository logic and PostgreSQL scope guards.

## M. Conflicts

`PredictiveEvidenceConflict` preserves metric-direction, baseline-comparison, domain/support and
uncertainty conflicts, including the exact conflicting artifact IDs. Conflicts are included as
contradicting evidence. No majority vote, conflict resolution, weighted score or capability conclusion
is performed.

## N. Limitations

`PredictiveEvidenceLimitation` is first-class for partial uncertainty, absent external validation,
narrow domain coverage, consumed single-use holdout, platform-only prospectivity, dependent groups,
unavailable near-duplicate detection, sparse horizons and unknown data quality. In-scope limitations
are always included with role `LIMITING`.

## O. Evidence Completeness

Completeness is stored separately from strength. V1 materialization requires protocol, partition,
snapshot, run, pair set, computed protocol-required metrics, baseline comparison, uncertainty, domain
and position evidence. Missing required evidence raises `EVIDENCE_SET_INCOMPLETE`; a successful set
receives an immutable `COMPLETE` assessment with required, present and missing type lists.

## P. EvidenceStrengthProfile

Profiles are immutable, deterministically derived from the exact evidence set, method-versioned and
idempotent. They contain no aggregate state or total score. A change in evidence requires a new set
and therefore a separately derived profile.

## Q. Strength Axes

Exactly seven axes use only `UNKNOWN | INSUFFICIENT | LIMITED | ADEQUATE | STRONG`:

- `INDEPENDENCE`: compromised is insufficient; unknown is limited; otherwise adequate.
- `TEMPORALITY`: retrospective is limited; governed prospective runs can be adequate but retain the
  explicit platform-only trust boundary.
- `DOMAIN_COVERAGE`: unknown, extrapolation and boundary positions degrade independently of sample size.
- `UNCERTAINTY_COMPLETENESS`: unknown/unquantified knowledge cannot be promoted to adequate.
- `BASELINE_STRENGTH`: none is insufficient; one/basic baseline limited; naive plus seasonal adequate;
  an authorized reference plus breadth can be strong.
- `REPLICATION`: requires multiple runs and distinct snapshots; many pairs in one run remain insufficient.
- `DATA_QUALITY`: derives only from observation quality provenance; absent provenance is unknown.

## R. Hashing & Determinism

Domain-separated SHA-256 covers assessments, positions, references, adverse evidence, sets and strength
profiles. Canonical key ordering plus sorted context/support/reference collections makes input order
irrelevant. Adding, removing or altering any epistemically relevant reference changes the set hash.

## S. Authorization

All mutations require project-scoped OAuth and the distinct
`ASSEMBLE_PREDICTIVE_EVIDENCE` permission, mapped in V1 to operator/admin roles. Viewer and development
fallback identities are rejected. This permission does not authorize claims, conclusions or action.

## T. AI Boundary

The executable boundary allows AI to summarize evidence or suggest conflicts only. AI cannot alter
membership, upgrade strength or authorize a scientific conclusion. No AI-generated value participates
as authoritative domain, support, strength or membership state.

## U. Audit

Scientific writes and their audit records share one transaction. Events cover domain and position
assessment, negative evidence, conflict and limitation registration, evidence-set materialization,
completeness assessment and strength-profile derivation. Audit payloads carry identifiers, state and
hashes rather than duplicating scientific payloads.

## V. API/Services

The official Next.js backend exposes seven project-scoped route families backed by
`GdssPredictiveEvidenceService`: assess domain, assess position, register negative evidence, register
conflict, register limitation, materialize/assess completeness, and derive strength. Strict schemas
reject extra fields and services compute authoritative results rather than accepting them from callers.

## W. Domain Errors

Typed errors cover incomplete/unknown/evaluation-failed domain context, unknown position, incomplete or
immutable sets, invalid/invalidated references, model/target/horizon/domain mismatches, omitted negative
evidence, conflicting evidence, invalid strength axes and unauthorized assembly. PostgreSQL guard
messages are mapped back into the same application error boundary.

## X. Invariants

Executable coverage includes the GDSS-006E subset of VAL-INV-01..40: in-domain differs from
out-of-domain, unknown fails closed, interpolation differs from extrapolation, predictive evidence is
not predictive capability, adverse/conflicting evidence is retained, evidence sets are immutable,
strength remains multidimensional, no global score exists and physical authority remains `NONE`.

## Y. Tests

- GDSS-006E domain/unit suite: 12/12 PASS.
- Real PostgreSQL GDSS-006A/B/C/D/E focused regression: 24/24 PASS.
- Durable disposable-PostgreSQL custody/run/006D/006E concurrency suite: 11/11 PASS.
- TypeScript typecheck, isolated migration cycle and static boundary scans: PASS.

## Z. Adversarial Tests

PASS: exact included/excluded boundaries; missing and incompatible context; exact categorical/boolean
membership; declared-domain but unsupported extrapolation; unknown position; order-independent hashes;
membership-sensitive hashes; invalid seven-axis sets; completeness/strength separation; unauthorized
assembly; cross-project/scope references; source-hash mismatch; caller-expanded support; missing metrics
or uncertainty; unfavorable baseline retention; late reference insertion; reference/set mutation;
unknown-uncertainty promotion prevention; compromised independence and fake replication prevention.

## AA. Concurrency

Real PostgreSQL races cover identical negative finding, conflict, evidence set and strength profile.
Advisory locks plus semantic uniqueness produce one effective materialization or the same deterministic
idempotent record, without duplicate scientific state.

## AB. Performance

Focal diagnostic sample: 64 predicates in 0.109 ms, support assessment in 0.106 ms, canonical hashing
of 100 references in 2.403 ms, 1,000 references in 1.772 ms and profile derivation in 0.407 ms. A
separate isolated run measured 0.668/0.132/0.516/1.694/0.045 ms respectively. These are diagnostic
observations, not SLAs; scheduling/JIT effects explain non-monotonic wall-clock samples.

## AC. Regression

- topology-next: 522 passed / 74 skipped; exit 0.
- Python runtime: 179 passed / 6 skipped; exit 0.
- Parametric Control Engine: 40 passed; exit 0.
- TypeScript no-emit typecheck: PASS.
- Next.js production build: PASS and includes all seven GDSS-006E route families.
- Migration cycle and forbidden-boundary scan: PASS.

## AD. Backward Compatibility

GDSS-001..005 and GDSS-006A/B/C/D regressions remain green. The change is additive and does not alter
Control Engine, MQTT/DTE, telemetry ingestion, calibration meaning, simulation behavior or prior
evidence. Domain membership remains distinct from empirical support and validation evidence remains
distinct from capability.

## AE. Alembic Status

Source: one head, `0048`. Principal local database: `0048 (head)`. The isolated disposable database
completed `0047 -> 0048 -> 0047 -> 0048` before cleanup; the principal database was upgraded only and
was never downgraded. Post-test principal counts were zero in all eleven 006E tables.

## AF. Git Status

All GDSS-006A/B/C/D/E code, migrations, tests and canonical documents remain local and uncommitted on
`main`, as authorized. Baseline HEAD remains `dee81328f4a73b525f8d7236d8ee799044b9cabc`.
No commit, push, tag or remote publication occurred.

## AG. Risks / Warnings

- Exact-boundary V1 intentionally cannot claim a near-boundary buffer that GDSS-006A did not declare.
- Empirical support uses conservative axis-aligned typed dimensions, not multidimensional geometry.
- `PLATFORM_PROSPECTIVE` is internal governed ordering, not independent external timestamp evidence.
- Completeness means required records exist; it does not mean the evidence is strong or favorable.
- Strength rules are method-versioned heuristics for evidence description, never a capability decision.
- Data quality can only be as strong as the governed provenance supplied by observations.

## AH. Final Status

`COMPLETED_GDSS_006E_VALIDITY_DOMAIN_AND_PREDICTIVE_EVIDENCE_ASSEMBLY`

GDSS-006E now produces a governed, exact-version evidence dossier containing supporting,
contradicting, limiting and invalidating material. It does not conclude predictive capability, issue a
claim or authorize any physical action; those semantics remain outside this authorization.

## P024-R3 corrective addendum

P024 found that AI provenance was not independently denied for authoritative evidence-set assembly.
P024-R3 reuses the shared AI predicate and rejects `ASSEMBLE_PREDICTIVE_EVIDENCE` with
`403 AI_AUTHORITY_FORBIDDEN` before input materialization or repository mutation. Consequently an AI
actor cannot choose favorable-only membership, suppress scoped negative/contradictory evidence or
materialize an authoritative exclusion. Existing deterministic completeness checks still return
`NEGATIVE_EVIDENCE_OMITTED` for prohibited human-authored omissions. Non-authoritative summarization,
drafting and explanation remain outside these mutation permissions. GDSS-006G remains pending.
