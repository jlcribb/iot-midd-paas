import type { PoolClient } from "pg";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import {
  capabilityAssessmentHash,
  canonicalCapabilityScope,
  canonicalValidationJson,
  evidenceTransferAssessmentHash,
  predictiveClaimAuthorizationHash,
  predictiveClaimHash,
  predictiveClaimReviewHash,
  predictiveClaimRevocationHash,
  projectClaimCurrentness,
  revalidationTriggerAssessmentHash,
  renderPredictiveClaim,
  type CapabilityAssessmentInput,
  type CapabilityScope,
  type CapabilityState,
  type ClaimDraftInput,
  type ClaimState,
  type EvidenceTransferInput,
  type RevalidationTriggerType,
} from "@/lib/gdss/validation";
import { CapabilityClaimError } from "@/lib/gdss/validation/capability-diagnostics";

const actorId = (actor: ControlActor) => actor.actor_id ?? actor.user_id;

export class GdssCapabilityClaimsRepository {
  constructor(
    private readonly transaction: TransactionRunner = withTransaction,
  ) {}

  private audit(
    tx: PoolClient,
    projectId: string,
    entityId: string,
    actor: ControlActor,
    action: string,
    changes: unknown,
  ) {
    return tx.query(
      "INSERT INTO iot_schema.auditoria(entidad,entidad_id,accion,cambios,contexto)VALUES('gdss_validation',$1::uuid,$2,$3::jsonb,$4::jsonb)",
      [
        entityId,
        action,
        JSON.stringify(changes),
        JSON.stringify({
          project_id: projectId,
          actor: actorId(actor),
          capability: "A1",
          subsystem: "gdss006f",
          physical_authority: "NONE",
          control_authority: "NONE",
        }),
      ],
    );
  }

  async getCapabilityFacts(projectId: string, evidenceSetId: string) {
    return this.transaction(async (tx) => {
      const set = (
        await tx.query(
          `SELECT s.*,pi.logical_key AS protocol_family,d.content AS domain_content
           FROM gdss_predictive_evidence_set s
           JOIN gdss_validation_protocol_version pv ON pv.id=s.protocol_version_id
           JOIN gdss_validation_protocol_identity pi ON pi.id=pv.protocol_identity_id
           JOIN gdss_validity_domain_version d ON d.id=s.validity_domain_version_id
           WHERE s.id=$1 AND s.project_id=$2`,
          [evidenceSetId, projectId],
        )
      ).rows[0];
      if (!set) throw new CapabilityClaimError("CAPABILITY_SCOPE_INVALID");
      const profile = (
        await tx.query(
          "SELECT * FROM gdss_evidence_strength_profile WHERE evidence_set_id=$1 AND project_id=$2",
          [evidenceSetId, projectId],
        )
      ).rows[0];
      if (!profile) throw new CapabilityClaimError("INSUFFICIENT_EVIDENCE");
      const axes = (
          await tx.query(
            "SELECT axis,state,evidence FROM gdss_evidence_strength_axis_assessment WHERE profile_id=$1 ORDER BY axis",
            [profile.id],
          )
        ).rows,
        completeness = (
          await tx.query(
            "SELECT state FROM gdss_evidence_completeness_assessment WHERE evidence_set_id=$1",
            [evidenceSetId],
          )
        ).rows[0]?.state;
      const limitations = (
          await tx.query(
            "SELECT l.id,l.limitation_type,l.description,l.content_hash FROM gdss_predictive_evidence_reference r JOIN gdss_predictive_evidence_limitation l ON l.id=r.artifact_id WHERE r.evidence_set_id=$1 AND r.artifact_type='EVIDENCE_LIMITATION' ORDER BY l.id",
            [evidenceSetId],
          )
        ).rows,
        conflicts = (
          await tx.query(
            "SELECT c.id,c.conflict_type,c.description,c.content_hash FROM gdss_predictive_evidence_reference r JOIN gdss_predictive_evidence_conflict c ON c.id=r.artifact_id WHERE r.evidence_set_id=$1 AND r.artifact_type='EVIDENCE_CONFLICT' ORDER BY c.id",
            [evidenceSetId],
          )
        ).rows,
        negativeEvidence = (
          await tx.query(
            "SELECT n.id,n.finding_type,n.description,n.content_hash FROM gdss_predictive_evidence_reference r JOIN gdss_predictive_evidence_negative_finding n ON n.id=r.artifact_id WHERE r.evidence_set_id=$1 AND r.artifact_type='NEGATIVE_FINDING' ORDER BY n.id",
            [evidenceSetId],
          )
        ).rows,
        invalidatingCount = Number(
          (
            await tx.query(
              "SELECT count(*)::int n FROM gdss_predictive_evidence_reference WHERE evidence_set_id=$1 AND role='INVALIDATING'",
              [evidenceSetId],
            )
          ).rows[0].n,
        );
      const profiles = (
        await tx.query(
          `SELECT
             ARRAY(SELECT DISTINCT d.metric_key FROM gdss_predictive_evidence_reference r JOIN gdss_metric_result m ON m.id=r.artifact_id JOIN gdss_metric_definition_version d ON d.id=m.metric_definition_version_id WHERE r.evidence_set_id=$1 AND r.artifact_type='METRIC_RESULT' ORDER BY d.metric_key) metric_profile,
             ARRAY(SELECT DISTINCT b.baseline_key FROM gdss_predictive_evidence_reference r JOIN gdss_baseline_comparison_result c ON c.id=r.artifact_id JOIN gdss_baseline_metric_result bm ON bm.id=c.baseline_metric_result_id JOIN gdss_baseline_version b ON b.id=bm.baseline_version_id WHERE r.evidence_set_id=$1 AND r.artifact_type='BASELINE_COMPARISON_RESULT' ORDER BY b.baseline_key) baseline_profile,
             ARRAY(SELECT DISTINCT u.source_type FROM gdss_predictive_evidence_reference r JOIN gdss_uncertainty_assessment a ON a.id=r.artifact_id JOIN gdss_uncertainty_source u ON u.id=a.source_id WHERE r.evidence_set_id=$1 AND r.artifact_type='UNCERTAINTY_ASSESSMENT' ORDER BY u.source_type) uncertainty_profile`,
          [evidenceSetId],
        )
      ).rows[0];
      const period = (
        await tx.query(
          `SELECT
             floor(extract(epoch FROM min(p.forecast_origin))*1000000)::bigint::text AS start_epoch_micros,
             floor(extract(epoch FROM max(o.measurement_time))*1000000)::bigint::text AS end_epoch_micros
           FROM gdss_prediction_pair_set_member m
           JOIN gdss_prediction_observation_pair po ON po.id=m.pair_id
           JOIN gdss_prediction_record p ON p.id=po.prediction_id
           JOIN gdss_observation_reference o ON o.id=po.observation_reference_id
           WHERE m.pair_set_id=ANY($1::uuid[])`,
          [set.pair_set_ids],
        )
      ).rows[0];
      return {
        set,
        axes,
        completeness,
        limitations,
        conflicts,
        negativeEvidence,
        invalidatingCount,
        metricProfile: profiles.metric_profile,
        baselineProfile: profiles.baseline_profile,
        uncertaintyProfile: profiles.uncertainty_profile,
        evidencePeriod: period,
      };
    });
  }

  createCapabilityAssessment(
    actor: ControlActor,
    projectId: string,
    input: CapabilityAssessmentInput,
    result: {
      state: CapabilityState;
      rationaleCode: string;
      axisExplanation: unknown[];
      limitationManifest: unknown[];
      conflictManifest: unknown[];
      negativeEvidenceManifest: unknown[];
      causalReference?: string;
    },
  ) {
    return this.transaction(async (tx) => {
      const { idempotencyKey: _idempotencyKey, ...semanticInput } = input,
        content = { ...semanticInput, ...result },
        hash = capabilityAssessmentHash(content);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_capability_assessment WHERE project_id=$1 AND (content_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, input.idempotencyKey],
        )
      ).rows[0];
      if (prior) {
        if (prior.content_hash !== hash)
          throw new CapabilityClaimError("CAPABILITY_SCOPE_INVALID");
        return prior;
      }
      const scope = input.scope;
      const row = (
        await tx.query(
          `INSERT INTO gdss_capability_assessment(project_id,semantic_version,evidence_set_id,evidence_set_hash,model_version_id,model_content_hash,target_key,horizon_key,validity_domain_version_id,protocol_family,metric_profile,baseline_profile,uncertainty_profile,evidence_period_start,evidence_period_end,domain_scope,assessment_policy_version,state,rationale_code,axis_explanation,limitation_manifest,conflict_manifest,negative_evidence_manifest,causal_reference,content_hash,predecessor_assessment_id,idempotency_key,created_by)
           VALUES($1,'GDSS_CAPABILITY_ASSESSMENT_V1',$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::bigint,$14::bigint,$15::jsonb,'GDSS_CAPABILITY_POLICY_V1',$16,$17,$18::jsonb,$19::jsonb,$20::jsonb,$21::jsonb,$22,$23,$24,$25,$26) RETURNING *`,
          [
            projectId,
            input.evidenceSetId,
            input.evidenceSetHash,
            scope.modelVersionId,
            scope.modelContentHash,
            scope.targetKey,
            scope.horizonKey,
            scope.validityDomainVersionId,
            scope.protocolFamily,
            scope.metricProfile,
            scope.baselineProfile,
            scope.uncertaintyProfile,
            scope.evidencePeriod.startEpochMicros,
            scope.evidencePeriod.endEpochMicros,
            JSON.stringify(scope.domainConstraints),
            result.state,
            result.rationaleCode,
            JSON.stringify(result.axisExplanation),
            JSON.stringify(result.limitationManifest),
            JSON.stringify(result.conflictManifest),
            JSON.stringify(result.negativeEvidenceManifest),
            result.causalReference ?? null,
            hash,
            input.predecessorAssessmentId ?? null,
            input.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      await this.audit(tx, projectId, row.id, actor, "CAPABILITY_ASSESSED", {
        state: result.state,
        content_hash: hash,
        evidence_set_hash: input.evidenceSetHash,
      });
      if (result.state === "INVALIDATED")
        await this.audit(
          tx,
          projectId,
          row.id,
          actor,
          "CAPABILITY_INVALIDATED",
          { causal_reference: result.causalReference },
        );
      return row;
    });
  }

  getCapabilityAssessment(projectId: string, id: string) {
    return this.transaction(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_capability_assessment WHERE id=$1 AND project_id=$2",
            [id, projectId],
          )
        ).rows[0],
    );
  }

  createClaimIdentity(
    actor: ControlActor,
    projectId: string,
    canonicalKey: string,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const row =
        (
          await tx.query(
            "INSERT INTO gdss_predictive_claim_identity(project_id,canonical_key,idempotency_key,created_by)VALUES($1,$2,$3,$4)ON CONFLICT(project_id,canonical_key)DO NOTHING RETURNING *",
            [projectId, canonicalKey, idempotencyKey, actorId(actor)],
          )
        ).rows[0] ??
        (
          await tx.query(
            "SELECT * FROM gdss_predictive_claim_identity WHERE project_id=$1 AND canonical_key=$2",
            [projectId, canonicalKey],
          )
        ).rows[0];
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "PREDICTIVE_CLAIM_IDENTITY_CREATED",
        { canonical_key: canonicalKey },
      );
      return row;
    });
  }

  createClaimDraft(
    actor: ControlActor,
    projectId: string,
    input: ClaimDraftInput,
    assessment: any,
  ) {
    return this.transaction(async (tx) => {
      await tx.query(
        "SELECT id FROM gdss_predictive_claim_identity WHERE id=$1 AND project_id=$2 FOR UPDATE",
        [input.claimIdentityId, projectId],
      );
      const version = Number(
        (
          await tx.query(
            "SELECT coalesce(max(claim_version),0)+1 AS version FROM gdss_predictive_claim_version WHERE claim_identity_id=$1",
            [input.claimIdentityId],
          )
        ).rows[0].version,
      );
      const scope = canonicalCapabilityScope(input.claimScope),
        limitations = assessment.limitation_manifest,
        negativeEvidence = assessment.negative_evidence_manifest,
        conflicts = assessment.conflict_manifest,
        uncertaintySummary = (assessment.axis_explanation as any[]).filter(
          (item) => item.axis === "UNCERTAINTY_COMPLETENESS",
        ),
        rendered = renderPredictiveClaim({
          state: assessment.state,
          scope,
          evidenceSetHash: assessment.evidence_set_hash,
          limitations,
          negativeEvidence,
          conflicts,
          uncertaintySummary,
        }),
        content = {
          semanticVersion: input.semanticVersion,
          claimIdentityId: input.claimIdentityId,
          claimVersion: version,
          capabilityAssessmentHash: input.capabilityAssessmentHash,
          evidenceSetHash: assessment.evidence_set_hash,
          claimScope: scope,
          limitations,
          negativeEvidence,
          conflicts,
          uncertaintySummary,
          templateVersion: input.templateVersion,
          validThroughEpochMicros: input.validThroughEpochMicros ?? null,
          predecessorClaimId: input.predecessorClaimId ?? null,
        },
        hash = predictiveClaimHash(content);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE project_id=$1 AND (content_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, input.idempotencyKey],
        )
      ).rows[0];
      if (prior) {
        if (prior.content_hash !== hash)
          throw new CapabilityClaimError("CLAIM_IMMUTABLE");
        return prior;
      }
      const row = (
        await tx.query(
          `INSERT INTO gdss_predictive_claim_version(project_id,claim_identity_id,claim_version,semantic_version,capability_assessment_id,capability_assessment_hash,evidence_set_id,evidence_set_hash,model_version_id,model_content_hash,target_key,horizon_key,validity_domain_version_id,claim_scope,limitation_manifest,negative_evidence_manifest,conflict_manifest,uncertainty_summary,template_version,rendered_human_text,status,content_hash,predecessor_claim_id,valid_through_epoch_micros,idempotency_key,authored_by)
           VALUES($1,$2,$3,'GDSS_PREDICTIVE_CLAIM_V1',$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14::jsonb,$15::jsonb,$16::jsonb,$17::jsonb,'GDSS_PREDICTIVE_CLAIM_TEMPLATE_V1',$18,'DRAFT',$19,$20,$21::bigint,$22,$23) RETURNING *`,
          [
            projectId,
            input.claimIdentityId,
            version,
            assessment.id,
            assessment.content_hash,
            assessment.evidence_set_id,
            assessment.evidence_set_hash,
            assessment.model_version_id,
            assessment.model_content_hash,
            assessment.target_key,
            assessment.horizon_key,
            assessment.validity_domain_version_id,
            JSON.stringify(scope),
            JSON.stringify(limitations),
            JSON.stringify(negativeEvidence),
            JSON.stringify(conflicts),
            JSON.stringify(uncertaintySummary),
            rendered,
            hash,
            input.predecessorClaimId ?? null,
            input.validThroughEpochMicros ?? null,
            input.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      await this.insertClaimEvent(
        tx,
        actor,
        row,
        null,
        "DRAFT",
        "draft created",
        `${input.idempotencyKey}:event`,
      );
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "PREDICTIVE_CLAIM_DRAFT_CREATED",
        { claim_hash: hash, claim_version: version },
      );
      return row;
    });
  }

  private async insertClaimEvent(
    tx: PoolClient,
    actor: ControlActor,
    claim: any,
    from: ClaimState | null,
    to: ClaimState,
    reason: string,
    idempotencyKey: string,
  ) {
    const sequence = Number(
        (
          await tx.query(
            "SELECT count(*)::int+1 AS sequence FROM gdss_predictive_claim_event WHERE claim_id=$1",
            [claim.id],
          )
        ).rows[0].sequence,
      ),
      eventHash = predictiveClaimHash({
        kind: "lifecycle-event",
        claimHash: claim.content_hash,
        sequence,
        from,
        to,
        actor: actorId(actor),
        reason,
      });
    return tx.query(
      "INSERT INTO gdss_predictive_claim_event(project_id,claim_id,sequence,from_status,to_status,actor,reason,idempotency_key,event_hash)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)",
      [
        claim.project_id,
        claim.id,
        sequence,
        from,
        to,
        actorId(actor),
        reason,
        idempotencyKey,
        eventHash,
      ],
    );
  }

  getClaim(projectId: string, claimId: string) {
    return this.transaction(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_predictive_claim_version WHERE id=$1 AND project_id=$2",
            [claimId, projectId],
          )
        ).rows[0],
    );
  }

  transitionClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    expectedHash: string,
    expectedState: ClaimState,
    nextState: ClaimState,
    reason: string,
    idempotencyKey: string,
    action: string,
  ) {
    return this.transaction(async (tx) => {
      const claim = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE id=$1 AND project_id=$2 FOR UPDATE",
          [claimId, projectId],
        )
      ).rows[0];
      if (!claim || claim.content_hash !== expectedHash)
        throw new CapabilityClaimError("STALE_AUTHORIZATION_REPLAY");
      if (claim.status !== expectedState)
        throw new CapabilityClaimError(
          expectedState === "DRAFT"
            ? "CLAIM_NOT_DRAFT"
            : expectedState === "EVIDENCE_ASSEMBLED"
              ? "CLAIM_NOT_REVIEWABLE"
              : "CLAIM_ALREADY_TERMINAL",
        );
      const updated = (
        await tx.query(
          "UPDATE gdss_predictive_claim_version SET status=$1,updated_at=clock_timestamp() WHERE id=$2 RETURNING *",
          [nextState, claimId],
        )
      ).rows[0];
      await this.insertClaimEvent(
        tx,
        actor,
        updated,
        expectedState,
        nextState,
        reason,
        idempotencyKey,
      );
      await this.audit(tx, projectId, claimId, actor, action, {
        from: expectedState,
        to: nextState,
        claim_hash: expectedHash,
      });
      return updated;
    });
  }

  updateClaimDraft(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    scope: CapabilityScope,
    validThrough: string | undefined,
    expectedHash: string,
    idempotencyKey: string,
    assessment: any,
  ) {
    return this.transaction(async (tx) => {
      const claim = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE id=$1 AND project_id=$2 FOR UPDATE",
          [claimId, projectId],
        )
      ).rows[0];
      if (!claim || claim.status !== "DRAFT")
        throw new CapabilityClaimError("CLAIM_NOT_DRAFT");
      if (claim.content_hash !== expectedHash)
        throw new CapabilityClaimError("STALE_AUTHORIZATION_REPLAY");
      const rendered = renderPredictiveClaim({
          state: assessment.state,
          scope,
          evidenceSetHash: assessment.evidence_set_hash,
          limitations: claim.limitation_manifest,
          negativeEvidence: claim.negative_evidence_manifest,
          conflicts: claim.conflict_manifest,
          uncertaintySummary: claim.uncertainty_summary,
        }),
        content = {
          semanticVersion: claim.semantic_version,
          claimIdentityId: claim.claim_identity_id,
          claimVersion: claim.claim_version,
          capabilityAssessmentHash: claim.capability_assessment_hash,
          evidenceSetHash: claim.evidence_set_hash,
          claimScope: scope,
          limitations: claim.limitation_manifest,
          negativeEvidence: claim.negative_evidence_manifest,
          conflicts: claim.conflict_manifest,
          uncertaintySummary: claim.uncertainty_summary,
          templateVersion: claim.template_version,
          validThroughEpochMicros: validThrough ?? null,
          predecessorClaimId: claim.predecessor_claim_id,
        },
        hash = predictiveClaimHash(content);
      const updated = (
        await tx.query(
          "UPDATE gdss_predictive_claim_version SET claim_scope=$1::jsonb,rendered_human_text=$2,content_hash=$3,valid_through_epoch_micros=$4::bigint,updated_at=clock_timestamp() WHERE id=$5 RETURNING *",
          [JSON.stringify(scope), rendered, hash, validThrough ?? null, claimId],
        )
      ).rows[0];
      await this.insertClaimEvent(
        tx,
        actor,
        updated,
        "DRAFT",
        "DRAFT",
        "draft updated",
        `${idempotencyKey}:event`,
      );
      await this.audit(
        tx,
        projectId,
        claimId,
        actor,
        "PREDICTIVE_CLAIM_UPDATED",
        { previous_hash: expectedHash, claim_hash: hash },
      );
      return updated;
    });
  }

  reviewClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    input: {
      expectedClaimHash: string;
      decision: string;
      rationale: string;
      scopeFindings: string[];
      evidenceFindings: string[];
      idempotencyKey: string;
    },
  ) {
    return this.transaction(async (tx) => {
      const claim = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE id=$1 AND project_id=$2 FOR UPDATE",
          [claimId, projectId],
        )
      ).rows[0];
      if (!claim || claim.status !== "REVIEW_REQUIRED")
        throw new CapabilityClaimError("CLAIM_NOT_REVIEWABLE");
      if (claim.content_hash !== input.expectedClaimHash)
        throw new CapabilityClaimError("STALE_AUTHORIZATION_REPLAY");
      const content = {
          claimHash: claim.content_hash,
          reviewer: actorId(actor),
          decision: input.decision,
          rationale: input.rationale,
          scopeFindings: [...input.scopeFindings].sort(),
          evidenceFindings: [...input.evidenceFindings].sort(),
        },
        hash = predictiveClaimReviewHash(content);
      const review =
        (
          await tx.query(
            "INSERT INTO gdss_predictive_claim_review(project_id,claim_id,claim_hash,reviewer,decision,rationale,scope_findings,evidence_findings,content_hash,idempotency_key)VALUES($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9,$10)ON CONFLICT(project_id,content_hash)DO NOTHING RETURNING *",
            [
              projectId,
              claimId,
              claim.content_hash,
              actorId(actor),
              input.decision,
              input.rationale,
              JSON.stringify(content.scopeFindings),
              JSON.stringify(content.evidenceFindings),
              hash,
              input.idempotencyKey,
            ],
          )
        ).rows[0] ??
        (
          await tx.query(
            "SELECT * FROM gdss_predictive_claim_review WHERE project_id=$1 AND content_hash=$2",
            [projectId, hash],
          )
        ).rows[0];
      let resultingClaim = claim;
      if (input.decision === "REJECT") {
        resultingClaim = (
          await tx.query(
            "UPDATE gdss_predictive_claim_version SET status='REJECTED',updated_at=clock_timestamp() WHERE id=$1 RETURNING *",
            [claimId],
          )
        ).rows[0];
        await this.insertClaimEvent(
          tx,
          actor,
          resultingClaim,
          "REVIEW_REQUIRED",
          "REJECTED",
          input.rationale,
          `${input.idempotencyKey}:event`,
        );
      }
      await this.audit(
        tx,
        projectId,
        claimId,
        actor,
        input.decision === "REJECT"
          ? "PREDICTIVE_CLAIM_REJECTED"
          : "PREDICTIVE_CLAIM_REVIEWED",
        { decision: input.decision, review_hash: hash },
      );
      return { review, claim: resultingClaim };
    });
  }

  authorizeClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    input: {
      expectedClaimHash: string;
      expectedAssessmentHash: string;
      expectedEvidenceSetHash: string;
      authorizedScope: CapabilityScope;
      sodException?: { reason: string };
      idempotencyKey: string;
    },
  ) {
    return this.transaction(async (tx) => {
      const claim = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE id=$1 AND project_id=$2 FOR UPDATE",
          [claimId, projectId],
        )
      ).rows[0];
      const existing = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_authorization WHERE claim_id=$1",
          [claimId],
        )
      ).rows[0];
      if (existing) return existing;
      if (!claim || claim.status !== "REVIEW_REQUIRED")
        throw new CapabilityClaimError("CLAIM_NOT_AUTHORIZABLE");
      if (
        claim.content_hash !== input.expectedClaimHash ||
        claim.capability_assessment_hash !== input.expectedAssessmentHash ||
        claim.evidence_set_hash !== input.expectedEvidenceSetHash
      )
        throw new CapabilityClaimError("STALE_AUTHORIZATION_REPLAY");
      if (claim.authored_by === actorId(actor)) {
        const admins = Number(
          (
            await tx.query(
              "SELECT count(*)::int n FROM project_control_memberships WHERE project_id=$1 AND enabled AND role='admin'",
              [projectId],
            )
          ).rows[0].n,
        );
        if (admins !== 1 || !input.sodException?.reason)
          throw new CapabilityClaimError("CLAIM_SOD_VIOLATION");
      }
      const scopeHash = predictiveClaimAuthorizationHash({
          kind: "authorized-scope",
          scope: input.authorizedScope,
        }),
        content = {
          claimHash: claim.content_hash,
          assessmentHash: claim.capability_assessment_hash,
          evidenceSetHash: claim.evidence_set_hash,
          authorizedScope: input.authorizedScope,
          decision: "AUTHORIZE",
          authorizer: actorId(actor),
          sodExceptionReason: input.sodException?.reason ?? null,
        },
        hash = predictiveClaimAuthorizationHash(content);
      const authorization = (
        await tx.query(
          "INSERT INTO gdss_predictive_claim_authorization(project_id,claim_id,authorizer,decision,authorized_scope,authorized_scope_hash,claim_hash,assessment_hash,evidence_set_hash,sod_exception_reason,content_hash,idempotency_key)VALUES($1,$2,$3,'AUTHORIZE',$4::jsonb,$5,$6,$7,$8,$9,$10,$11)RETURNING *",
          [
            projectId,
            claimId,
            actorId(actor),
            JSON.stringify(input.authorizedScope),
            scopeHash,
            claim.content_hash,
            claim.capability_assessment_hash,
            claim.evidence_set_hash,
            input.sodException?.reason ?? null,
            hash,
            input.idempotencyKey,
          ],
        )
      ).rows[0];
      const updated = (
        await tx.query(
          "UPDATE gdss_predictive_claim_version SET status='AUTHORIZED',updated_at=clock_timestamp() WHERE id=$1 RETURNING *",
          [claimId],
        )
      ).rows[0];
      await this.insertClaimEvent(
        tx,
        actor,
        updated,
        "REVIEW_REQUIRED",
        "AUTHORIZED",
        "human authorization",
        `${input.idempotencyKey}:event`,
      );
      await this.audit(
        tx,
        projectId,
        claimId,
        actor,
        "PREDICTIVE_CLAIM_AUTHORIZED",
        {
          authorization_hash: hash,
          sod_exception: input.sodException?.reason ?? null,
        },
      );
      return authorization;
    });
  }

  revokeClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    input: {
      authorizationId: string;
      reason: string;
      trigger: RevalidationTriggerType;
      idempotencyKey: string;
    },
  ) {
    return this.transaction(async (tx) => {
      const claim = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE id=$1 AND project_id=$2 FOR UPDATE",
          [claimId, projectId],
        )
      ).rows[0];
      const existing = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_revocation WHERE claim_id=$1",
          [claimId],
        )
      ).rows[0];
      if (existing) return existing;
      if (!claim || claim.status !== "AUTHORIZED")
        throw new CapabilityClaimError("CLAIM_REVOCATION_FORBIDDEN");
      const content = {
          claimHash: claim.content_hash,
          authorizationId: input.authorizationId,
          actor: actorId(actor),
          reason: input.reason,
          trigger: input.trigger,
        },
        hash = predictiveClaimRevocationHash(content);
      const revocation = (
        await tx.query(
          "INSERT INTO gdss_predictive_claim_revocation(project_id,claim_id,authorization_id,actor,reason,trigger_type,content_hash,idempotency_key)VALUES($1,$2,$3,$4,$5,$6,$7,$8)RETURNING *",
          [
            projectId,
            claimId,
            input.authorizationId,
            actorId(actor),
            input.reason,
            input.trigger,
            hash,
            input.idempotencyKey,
          ],
        )
      ).rows[0];
      const updated = (
        await tx.query(
          "UPDATE gdss_predictive_claim_version SET status='REVOKED',updated_at=clock_timestamp() WHERE id=$1 RETURNING *",
          [claimId],
        )
      ).rows[0];
      await this.insertClaimEvent(
        tx,
        actor,
        updated,
        "AUTHORIZED",
        "REVOKED",
        input.reason,
        `${input.idempotencyKey}:event`,
      );
      await this.audit(
        tx,
        projectId,
        claimId,
        actor,
        "PREDICTIVE_CLAIM_REVOKED",
        { revocation_hash: hash, authorization_id: input.authorizationId },
      );
      return revocation;
    });
  }

  supersedeClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    successorClaimId: string,
    reason: string,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const rows = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE id=ANY($1::uuid[]) AND project_id=$2 ORDER BY id FOR UPDATE",
          [[claimId, successorClaimId], projectId],
        )
      ).rows;
      const claim = rows.find((row) => row.id === claimId),
        successor = rows.find((row) => row.id === successorClaimId);
      if (
        !claim ||
        !successor ||
        claim.status !== "AUTHORIZED" ||
        successor.status !== "AUTHORIZED" ||
        successor.claim_identity_id !== claim.claim_identity_id ||
        successor.predecessor_claim_id !== claim.id
      )
        throw new CapabilityClaimError("CLAIM_SCOPE_EXCEEDS_EVIDENCE");
      const updated = (
        await tx.query(
          "UPDATE gdss_predictive_claim_version SET status='SUPERSEDED',updated_at=clock_timestamp() WHERE id=$1 RETURNING *",
          [claimId],
        )
      ).rows[0];
      await this.insertClaimEvent(
        tx,
        actor,
        updated,
        "AUTHORIZED",
        "SUPERSEDED",
        reason,
        idempotencyKey,
      );
      await this.audit(
        tx,
        projectId,
        claimId,
        actor,
        "PREDICTIVE_CLAIM_SUPERSEDED",
        { successor_claim_id: successorClaimId },
      );
      return updated;
    });
  }

  getClaimCurrentness(projectId: string, claimId: string, now: bigint) {
    return this.transaction(async (tx) => {
      const claim = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE id=$1 AND project_id=$2",
          [claimId, projectId],
        )
      ).rows[0];
      if (!claim) throw new CapabilityClaimError("CLAIM_ALREADY_TERMINAL");
      const unresolved = Number(
        (
          await tx.query(
            "SELECT count(*)::int n FROM gdss_revalidation_trigger_assessment t WHERE t.claim_id=$1 AND t.state IN('DETECTED','REVIEW_REQUIRED','REVALIDATION_REQUIRED') AND NOT EXISTS(SELECT 1 FROM gdss_revalidation_trigger_assessment s WHERE s.predecessor_trigger_id=t.id)",
            [claimId],
          )
        ).rows[0].n,
      );
      return {
        claim,
        currentness: projectClaimCurrentness(
          claim.status,
          claim.valid_through_epoch_micros?.toString() ?? null,
          unresolved > 0,
          now,
        ),
      };
    });
  }

  createRevalidationTrigger(
    actor: ControlActor,
    projectId: string,
    input: any,
    state: string,
  ) {
    return this.transaction(async (tx) => {
      const content = {
          capabilityAssessmentId: input.capabilityAssessmentId,
          claimId: input.claimId ?? null,
          evidenceSetId: input.evidenceSetId,
          triggerType: input.triggerType,
          state,
          causalArtifactId: input.causalArtifactId,
          causalArtifactHash: input.causalArtifactHash,
          rationale: input.rationale,
          predecessorTriggerId: input.predecessorTriggerId ?? null,
        },
        hash = revalidationTriggerAssessmentHash(content);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_revalidation_trigger_assessment WHERE project_id=$1 AND (content_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, input.idempotencyKey],
        )
      ).rows[0];
      if (prior) return prior;
      const row = (
        await tx.query(
          "INSERT INTO gdss_revalidation_trigger_assessment(project_id,capability_assessment_id,claim_id,evidence_set_id,trigger_type,state,causal_artifact_id,causal_artifact_hash,rationale,predecessor_trigger_id,content_hash,idempotency_key,assessed_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)RETURNING *",
          [
            projectId,
            input.capabilityAssessmentId,
            input.claimId ?? null,
            input.evidenceSetId,
            input.triggerType,
            state,
            input.causalArtifactId,
            input.causalArtifactHash,
            input.rationale,
            input.predecessorTriggerId ?? null,
            hash,
            input.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "REVALIDATION_TRIGGER_ASSESSED",
        { trigger_type: input.triggerType, state, content_hash: hash },
      );
      if (state === "REVALIDATION_REQUIRED")
        await this.audit(
          tx,
          projectId,
          row.id,
          actor,
          "REVALIDATION_REQUIRED",
          { trigger_type: input.triggerType },
        );
      return row;
    });
  }

  getRevalidationTrigger(projectId: string, triggerId: string) {
    return this.transaction(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_revalidation_trigger_assessment WHERE id=$1 AND project_id=$2",
            [triggerId, projectId],
          )
        ).rows[0],
    );
  }

  createEvidenceTransferAssessment(
    actor: ControlActor,
    projectId: string,
    input: EvidenceTransferInput,
    result: "FULL_REVALIDATION_REQUIRED" | "TRANSFER_REJECTED",
  ) {
    return this.transaction(async (tx) => {
      const { idempotencyKey: _idempotencyKey, ...semanticInput } = input,
        content = { ...semanticInput, result },
        hash = evidenceTransferAssessmentHash(content);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_evidence_transfer_assessment WHERE project_id=$1 AND (content_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, input.idempotencyKey],
        )
      ).rows[0];
      if (prior) return prior;
      const row = (
        await tx.query(
          "INSERT INTO gdss_evidence_transfer_assessment(project_id,source_model_version_id,target_model_version_id,source_evidence_set_id,source_evidence_set_hash,requested_transfer_scope,requested_mode,result,reason,content_hash,idempotency_key,assessed_by)VALUES($1,$2,$3,$4,$5,$6::jsonb,$7,$8,$9,$10,$11,$12)RETURNING *",
          [
            projectId,
            input.sourceModelVersionId,
            input.targetModelVersionId,
            input.sourceEvidenceSetId,
            input.sourceEvidenceSetHash,
            JSON.stringify(input.requestedTransferScope),
            input.requestedMode,
            result,
            input.reason,
            hash,
            input.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "EVIDENCE_TRANSFER_ASSESSED",
        { result, content_hash: hash, policy: "NO_AUTOMATIC_TRANSFER" },
      );
      return row;
    });
  }

  auditSnapshot(projectId: string, claimId: string) {
    return this.transaction(async (tx) => {
      const claim = (
        await tx.query(
          "SELECT * FROM gdss_predictive_claim_version WHERE id=$1 AND project_id=$2",
          [claimId, projectId],
        )
      ).rows[0];
      if (!claim) throw new CapabilityClaimError("CLAIM_ALREADY_TERMINAL");
      const events = (
          await tx.query(
            "SELECT * FROM gdss_predictive_claim_event WHERE claim_id=$1 ORDER BY sequence",
            [claimId],
          )
        ).rows,
        reviews = (
          await tx.query(
            "SELECT * FROM gdss_predictive_claim_review WHERE claim_id=$1 ORDER BY reviewed_at,id",
            [claimId],
          )
        ).rows,
        authorization = (
          await tx.query(
            "SELECT * FROM gdss_predictive_claim_authorization WHERE claim_id=$1",
            [claimId],
          )
        ).rows[0] ?? null,
        revocation = (
          await tx.query(
            "SELECT * FROM gdss_predictive_claim_revocation WHERE claim_id=$1",
            [claimId],
          )
        ).rows[0] ?? null;
      return { claim, events, reviews, authorization, revocation };
    });
  }
}
