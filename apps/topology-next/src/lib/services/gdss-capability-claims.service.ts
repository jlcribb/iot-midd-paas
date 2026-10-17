import type { ControlActor } from "@/lib/dto/control-access.dto";
import {
  assertCapabilityGovernanceAccess,
  assertScopeSubset,
  canonicalCapabilityAssessment,
  canonicalCapabilityScope,
  canonicalClaimDraft,
  canonicalValidationJson,
  capabilityAssessmentInputSchema,
  capabilityInvalidationInputSchema,
  capabilityScopeSchema,
  claimAuthorizationInputSchema,
  claimDraftInputSchema,
  claimDraftUpdateInputSchema,
  claimIdentityInputSchema,
  claimReviewInputSchema,
  claimRevocationInputSchema,
  claimSupersessionInputSchema,
  claimTransitionInputSchema,
  deriveCapabilityState,
  evidenceTransferInputSchema,
  revalidationResolutionInputSchema,
  revalidationTriggerInputSchema,
  triggerInitialState,
  validityDomainContentSchema,
  type CapabilityScope,
} from "@/lib/gdss/validation";
import { CapabilityClaimError } from "@/lib/gdss/validation/capability-diagnostics";
import { GdssCapabilityClaimsRepository } from "@/lib/repositories/gdss-capability-claims.repository";

function declaredDomainScope(content: unknown) {
  const domain = validityDomainContentSchema.parse(content);
  return domain.predicates.map((predicate) => {
    if (
      predicate.predicateType === "NUMERIC_RANGE" ||
      predicate.predicateType === "PARAMETER_RANGE"
    )
      return {
        kind: "NUMERIC_RANGE" as const,
        variableKey: predicate.variableKey,
        lowerBound: predicate.lowerBound,
        upperBound: predicate.upperBound,
        lowerInclusive: predicate.lowerInclusive,
        upperInclusive: predicate.upperInclusive,
        unit: predicate.unit!,
      };
    if (predicate.predicateType === "TEMPORAL_RANGE")
      return {
        kind: "TEMPORAL_RANGE" as const,
        variableKey: predicate.variableKey,
        startEpochMicros: predicate.startEpochMicros,
        endEpochMicros: predicate.endEpochMicros,
      };
    if (predicate.predicateType === "CATEGORICAL_MEMBERSHIP")
      return {
        kind: "CATEGORICAL_SET" as const,
        variableKey: predicate.variableKey,
        values: [...predicate.allowedValues].sort(),
      };
    return {
      kind: "BOOLEAN_SET" as const,
      variableKey: predicate.variableKey,
      values: [predicate.expected],
    };
  });
}

export class GdssCapabilityClaimsService {
  constructor(
    private readonly repository = new GdssCapabilityClaimsRepository(),
  ) {}

  private authorize(
    actor: ControlActor,
    projectId: string,
    permission: Parameters<typeof assertCapabilityGovernanceAccess>[2],
  ) {
    assertCapabilityGovernanceAccess(actor, projectId, permission);
  }

  private async assertCapabilityScope(
    projectId: string,
    input: ReturnType<typeof canonicalCapabilityAssessment>,
  ) {
    const facts = await this.repository.getCapabilityFacts(
        projectId,
        input.evidenceSetId,
      ),
      set = facts.set,
      evidencePeriod = facts.evidencePeriod;
    if (
      set.content_hash !== input.evidenceSetHash ||
      set.model_version_id !== input.scope.modelVersionId ||
      set.model_hash !== input.scope.modelContentHash ||
      set.target_key !== input.scope.targetKey ||
      set.horizon_key !== input.scope.horizonKey ||
      set.validity_domain_version_id !== input.scope.validityDomainVersionId ||
      set.protocol_family !== input.scope.protocolFamily ||
      !evidencePeriod.start_epoch_micros ||
      !evidencePeriod.end_epoch_micros ||
      evidencePeriod.start_epoch_micros !==
        input.scope.evidencePeriod.startEpochMicros ||
      evidencePeriod.end_epoch_micros !==
        input.scope.evidencePeriod.endEpochMicros ||
      canonicalValidationJson(facts.metricProfile) !==
        canonicalValidationJson(input.scope.metricProfile) ||
      canonicalValidationJson(facts.baselineProfile) !==
        canonicalValidationJson(input.scope.baselineProfile) ||
      canonicalValidationJson(facts.uncertaintyProfile) !==
        canonicalValidationJson(input.scope.uncertaintyProfile)
    )
      throw new CapabilityClaimError("CAPABILITY_SCOPE_INVALID");
    const declaredScope: CapabilityScope = {
      ...input.scope,
      domainConstraints: declaredDomainScope(set.domain_content),
    };
    assertScopeSubset(input.scope, canonicalCapabilityScope(declaredScope));
    return facts;
  }

  async assessPredictiveCapability(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "ASSESS_PREDICTIVE_CAPABILITY");
    const input = canonicalCapabilityAssessment(
        capabilityAssessmentInputSchema.parse(raw),
      ),
      facts = await this.assertCapabilityScope(projectId, input),
      derived = deriveCapabilityState({
        requestedAction: input.requestedAction,
        completeness: facts.completeness,
        axes: facts.axes as any,
        conflictCount: facts.conflicts.length,
        invalidatingCount: facts.invalidatingCount,
        negativeFindingTypes: facts.negativeEvidence.map(
          (item: any) => item.finding_type,
        ),
      });
    return this.repository.createCapabilityAssessment(
      actor,
      projectId,
      input,
      {
        ...derived,
        limitationManifest: facts.limitations,
        conflictManifest: facts.conflicts,
        negativeEvidenceManifest: facts.negativeEvidence,
      },
    );
  }

  async invalidatePredictiveCapability(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "REVIEW_CAPABILITY_ASSESSMENT");
    const input = capabilityInvalidationInputSchema.parse(raw),
      prior = await this.repository.getCapabilityAssessment(
        projectId,
        input.assessmentId,
      );
    if (!prior) throw new CapabilityClaimError("CAPABILITY_SCOPE_INVALID");
    const assessmentInput = canonicalCapabilityAssessment({
      semanticVersion: "GDSS_CAPABILITY_ASSESSMENT_V1",
      evidenceSetId: prior.evidence_set_id,
      evidenceSetHash: prior.evidence_set_hash,
      assessmentPolicyVersion: prior.assessment_policy_version,
      requestedAction: "EVALUATE",
      scope: {
        modelVersionId: prior.model_version_id,
        modelContentHash: prior.model_content_hash,
        targetKey: prior.target_key,
        horizonKey: prior.horizon_key,
        validityDomainVersionId: prior.validity_domain_version_id,
        protocolFamily: prior.protocol_family,
        metricProfile: prior.metric_profile,
        baselineProfile: prior.baseline_profile,
        uncertaintyProfile: prior.uncertainty_profile,
        evidencePeriod: {
          startEpochMicros: prior.evidence_period_start.toString(),
          endEpochMicros: prior.evidence_period_end.toString(),
        },
        domainConstraints: prior.domain_scope,
      },
      predecessorAssessmentId: prior.id,
      idempotencyKey: input.idempotencyKey,
    });
    return this.repository.createCapabilityAssessment(
      actor,
      projectId,
      assessmentInput,
      {
        state: "INVALIDATED",
        rationaleCode: "EXPLICIT_GOVERNED_INVALIDATION",
        axisExplanation: prior.axis_explanation,
        limitationManifest: prior.limitation_manifest,
        conflictManifest: prior.conflict_manifest,
        negativeEvidenceManifest: prior.negative_evidence_manifest,
        causalReference: `${input.causalReference}: ${input.reason}`,
      },
    );
  }

  createPredictiveClaimIdentity(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "AUTHOR_PREDICTIVE_CLAIM");
    const input = claimIdentityInputSchema.parse(raw);
    return this.repository.createClaimIdentity(
      actor,
      projectId,
      input.canonicalKey,
      input.idempotencyKey,
    );
  }

  async createPredictiveClaimDraft(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "AUTHOR_PREDICTIVE_CLAIM");
    const input = canonicalClaimDraft(claimDraftInputSchema.parse(raw)),
      assessment = await this.repository.getCapabilityAssessment(
        projectId,
        input.capabilityAssessmentId,
      );
    if (
      !assessment ||
      assessment.content_hash !== input.capabilityAssessmentHash
    )
      throw new CapabilityClaimError("CAPABILITY_SCOPE_INVALID");
    assertScopeSubset(
      input.claimScope,
      capabilityScopeSchema.parse({
        modelVersionId: assessment.model_version_id,
        modelContentHash: assessment.model_content_hash,
        targetKey: assessment.target_key,
        horizonKey: assessment.horizon_key,
        validityDomainVersionId: assessment.validity_domain_version_id,
        protocolFamily: assessment.protocol_family,
        metricProfile: assessment.metric_profile,
        baselineProfile: assessment.baseline_profile,
        uncertaintyProfile: assessment.uncertainty_profile,
        evidencePeriod: {
          startEpochMicros: assessment.evidence_period_start.toString(),
          endEpochMicros: assessment.evidence_period_end.toString(),
        },
        domainConstraints: assessment.domain_scope,
      }),
    );
    return this.repository.createClaimDraft(
      actor,
      projectId,
      input,
      assessment,
    );
  }

  async updatePredictiveClaimDraft(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "AUTHOR_PREDICTIVE_CLAIM");
    const input = claimDraftUpdateInputSchema.parse(raw),
      scope = canonicalCapabilityScope(input.claimScope),
      claim = await this.repository.getClaim(projectId, claimId);
    if (!claim) throw new CapabilityClaimError("CLAIM_NOT_DRAFT");
    const assessment = await this.repository.getCapabilityAssessment(
      projectId,
      claim.capability_assessment_id,
    );
    assertScopeSubset(
      scope,
      capabilityScopeSchema.parse({
        modelVersionId: assessment.model_version_id,
        modelContentHash: assessment.model_content_hash,
        targetKey: assessment.target_key,
        horizonKey: assessment.horizon_key,
        validityDomainVersionId: assessment.validity_domain_version_id,
        protocolFamily: assessment.protocol_family,
        metricProfile: assessment.metric_profile,
        baselineProfile: assessment.baseline_profile,
        uncertaintyProfile: assessment.uncertainty_profile,
        evidencePeriod: {
          startEpochMicros: assessment.evidence_period_start.toString(),
          endEpochMicros: assessment.evidence_period_end.toString(),
        },
        domainConstraints: assessment.domain_scope,
      }),
    );
    return this.repository.updateClaimDraft(
      actor,
      projectId,
      claimId,
      scope,
      input.validThroughEpochMicros,
      input.expectedClaimHash,
      input.idempotencyKey,
      assessment,
    );
  }

  assembleClaimEvidence(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "AUTHOR_PREDICTIVE_CLAIM");
    const input = claimTransitionInputSchema.parse(raw);
    return this.repository.transitionClaim(
      actor,
      projectId,
      claimId,
      input.expectedClaimHash,
      "DRAFT",
      "EVIDENCE_ASSEMBLED",
      input.reason,
      input.idempotencyKey,
      "PREDICTIVE_CLAIM_EVIDENCE_ASSEMBLED",
    );
  }

  submitClaimForReview(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "AUTHOR_PREDICTIVE_CLAIM");
    const input = claimTransitionInputSchema.parse(raw);
    return this.repository.transitionClaim(
      actor,
      projectId,
      claimId,
      input.expectedClaimHash,
      "EVIDENCE_ASSEMBLED",
      "REVIEW_REQUIRED",
      input.reason,
      input.idempotencyKey,
      "PREDICTIVE_CLAIM_SUBMITTED",
    );
  }

  reviewPredictiveClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "REVIEW_CAPABILITY_ASSESSMENT");
    return this.repository.reviewClaim(
      actor,
      projectId,
      claimId,
      claimReviewInputSchema.parse(raw),
    );
  }

  async authorizePredictiveClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "AUTHORIZE_PREDICTIVE_CLAIM");
    const input = claimAuthorizationInputSchema.parse(raw),
      claim = await this.repository.getClaim(projectId, claimId);
    if (!claim) throw new CapabilityClaimError("CLAIM_NOT_AUTHORIZABLE");
    const assessment = await this.repository.getCapabilityAssessment(
      projectId,
      claim.capability_assessment_id,
    );
    if (
      ![
        "EVIDENCE_OF_LIMITED_CAPABILITY",
        "EVIDENCE_OF_CAPABILITY",
      ].includes(assessment.state)
    )
      throw new CapabilityClaimError("CLAIM_NOT_AUTHORIZABLE");
    assertScopeSubset(input.authorizedScope, claim.claim_scope);
    assertScopeSubset(
      input.authorizedScope,
      capabilityScopeSchema.parse({
        modelVersionId: assessment.model_version_id,
        modelContentHash: assessment.model_content_hash,
        targetKey: assessment.target_key,
        horizonKey: assessment.horizon_key,
        validityDomainVersionId: assessment.validity_domain_version_id,
        protocolFamily: assessment.protocol_family,
        metricProfile: assessment.metric_profile,
        baselineProfile: assessment.baseline_profile,
        uncertaintyProfile: assessment.uncertainty_profile,
        evidencePeriod: {
          startEpochMicros: assessment.evidence_period_start.toString(),
          endEpochMicros: assessment.evidence_period_end.toString(),
        },
        domainConstraints: assessment.domain_scope,
      }),
    );
    return this.repository.authorizeClaim(
      actor,
      projectId,
      claimId,
      input,
    );
  }

  rejectPredictiveClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    raw: unknown,
  ) {
    const parsed = claimReviewInputSchema.parse(raw);
    if (parsed.decision !== "REJECT")
      throw new CapabilityClaimError("CLAIM_NOT_REVIEWABLE");
    return this.reviewPredictiveClaim(actor, projectId, claimId, parsed);
  }

  revokePredictiveClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "REVOKE_PREDICTIVE_CLAIM");
    return this.repository.revokeClaim(
      actor,
      projectId,
      claimId,
      claimRevocationInputSchema.parse(raw),
    );
  }

  supersedePredictiveClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "AUTHORIZE_PREDICTIVE_CLAIM");
    const input = claimSupersessionInputSchema.parse(raw);
    return this.repository.supersedeClaim(
      actor,
      projectId,
      claimId,
      input.successorClaimId,
      input.reason,
      input.idempotencyKey,
    );
  }

  getClaimCurrentness(
    actor: ControlActor,
    projectId: string,
    claimId: string,
    nowEpochMicros = BigInt(Date.now()) * 1000n,
  ) {
    this.authorize(actor, projectId, "AUDIT_PREDICTIVE_EVIDENCE");
    return this.repository.getClaimCurrentness(
      projectId,
      claimId,
      nowEpochMicros,
    );
  }

  auditPredictiveClaim(
    actor: ControlActor,
    projectId: string,
    claimId: string,
  ) {
    this.authorize(actor, projectId, "AUDIT_PREDICTIVE_EVIDENCE");
    return this.repository.auditSnapshot(projectId, claimId);
  }

  async assessRevalidationTrigger(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "REVIEW_CAPABILITY_ASSESSMENT");
    const input = revalidationTriggerInputSchema.parse(raw),
      assessment = await this.repository.getCapabilityAssessment(
        projectId,
        input.capabilityAssessmentId,
      ),
      successorFacts = await this.repository.getCapabilityFacts(
        projectId,
        input.evidenceSetId,
      );
    if (
      !assessment ||
      successorFacts.set.model_version_id !== assessment.model_version_id ||
      successorFacts.set.model_hash !== assessment.model_content_hash ||
      successorFacts.set.target_key !== assessment.target_key ||
      successorFacts.set.horizon_key !== assessment.horizon_key ||
      successorFacts.set.validity_domain_version_id !==
        assessment.validity_domain_version_id ||
      successorFacts.set.protocol_family !== assessment.protocol_family
    )
      throw new CapabilityClaimError("CAPABILITY_SCOPE_INVALID");
    if (input.claimId) {
      const claim = await this.repository.getClaim(projectId, input.claimId);
      if (!claim || claim.capability_assessment_id !== assessment.id)
        throw new CapabilityClaimError("CAPABILITY_SCOPE_INVALID");
    }
    return this.repository.createRevalidationTrigger(
      actor,
      projectId,
      input,
      triggerInitialState(input.triggerType),
    );
  }

  async resolveRevalidationTrigger(
    actor: ControlActor,
    projectId: string,
    triggerId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "REVIEW_CAPABILITY_ASSESSMENT");
    const input = revalidationResolutionInputSchema.parse(raw),
      prior = await this.repository.getRevalidationTrigger(
        projectId,
        triggerId,
      );
    if (!prior || prior.content_hash !== input.expectedContentHash)
      throw new CapabilityClaimError("REVALIDATION_REQUIRED");
    return this.repository.createRevalidationTrigger(
      actor,
      projectId,
      {
        capabilityAssessmentId: prior.capability_assessment_id,
        claimId: prior.claim_id ?? undefined,
        evidenceSetId: prior.evidence_set_id,
        triggerType: prior.trigger_type,
        causalArtifactId: prior.causal_artifact_id,
        causalArtifactHash: prior.causal_artifact_hash,
        rationale: input.rationale,
        predecessorTriggerId: prior.id,
        idempotencyKey: input.idempotencyKey,
      },
      input.resolution,
    );
  }

  assessEvidenceTransfer(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId, "REVIEW_CAPABILITY_ASSESSMENT");
    const input = evidenceTransferInputSchema.parse(raw);
    if (
      ["PARTIAL_REVALIDATION_ALLOWED", "EQUIVALENCE_ESTABLISHED"].includes(
        input.requestedMode,
      )
    )
      throw new CapabilityClaimError("EVIDENCE_TRANSFER_FORBIDDEN");
    return this.repository.createEvidenceTransferAssessment(
      actor,
      projectId,
      input,
      "FULL_REVALIDATION_REQUIRED",
    );
  }
}
