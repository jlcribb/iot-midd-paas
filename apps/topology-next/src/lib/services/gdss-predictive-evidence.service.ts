import type { ControlActor } from "@/lib/dto/control-access.dto";
import {
  assertPredictiveEvidenceAccess,
  assessPosition,
  canonicalDomainAssessment,
  canonicalPredictivePosition,
  canonicalValidationJson,
  conflictInputSchema,
  domainAssessmentInputSchema,
  evidenceSetInputSchema,
  evaluateDomain,
  limitationInputSchema,
  negativeFindingInputSchema,
  predictivePositionInputSchema,
  validityDomainContentSchema,
} from "@/lib/gdss/validation";
import { PredictiveEvidenceError } from "@/lib/gdss/validation/evidence-diagnostics";
import { GdssPredictiveEvidenceRepository } from "@/lib/repositories/gdss-predictive-evidence.repository";

export class GdssPredictiveEvidenceService {
  constructor(
    private readonly repository = new GdssPredictiveEvidenceRepository(),
  ) {}

  private authorize(actor: ControlActor, projectId: string) {
    assertPredictiveEvidenceAccess(
      actor,
      projectId,
      "ASSEMBLE_PREDICTIVE_EVIDENCE",
    );
  }

  async assessValidityDomain(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId);
    const input = canonicalDomainAssessment(
      domainAssessmentInputSchema.parse(raw),
    );
    const domain = await this.repository.getDomainForAssessment(
      projectId,
      input.validityDomainVersionId,
    );
    if (
      !domain ||
      domain.status === "INVALIDATED" ||
      domain.content_hash !== input.validityDomainHash
    )
      throw new PredictiveEvidenceError("DOMAIN_EVIDENCE_MISMATCH");
    const content = validityDomainContentSchema.parse(domain.content);
    const evaluation = evaluateDomain(
      content.predicates,
      input.contextSnapshot,
    );
    return this.repository.createDomainAssessment(
      actor,
      projectId,
      input,
      evaluation.result,
      evaluation.assessments,
    );
  }

  async assessPredictivePosition(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId);
    const input = canonicalPredictivePosition(
      predictivePositionInputSchema.parse(raw),
    );
    const domain = await this.repository.getDomainAssessment(
      projectId,
      input.domainAssessmentId,
    );
    if (
      !domain ||
      domain.model_version_id !== input.modelVersionId ||
      domain.validity_domain_version_id !== input.validityDomainVersionId ||
      domain.validation_run_id !== input.validationRunId ||
      domain.target_key !== input.targetKey ||
      domain.horizon_key !== input.horizonKey
    )
      throw new PredictiveEvidenceError("DOMAIN_EVIDENCE_MISMATCH");
    if (
      canonicalValidationJson(domain.context_snapshot) !==
      canonicalValidationJson(input.contextSnapshot)
    )
      throw new PredictiveEvidenceError(
        "DOMAIN_EVIDENCE_MISMATCH",
        "Position must evaluate the same context snapshot",
      );
    const supportIds = [
      ...new Set(
        input.supportDimensions.flatMap((item) => item.evidenceAssessmentIds),
      ),
    ];
    const supportAssessments = [];
    for (const id of supportIds) {
      const support = await this.repository.getDomainAssessment(projectId, id);
      if (
        !support ||
        support.model_version_id !== input.modelVersionId ||
        support.validity_domain_version_id !== input.validityDomainVersionId ||
        support.target_key !== input.targetKey ||
        support.horizon_key !== input.horizonKey ||
        !["WITHIN_VALIDITY_DOMAIN", "NEAR_DOMAIN_BOUNDARY"].includes(
          support.assessment_result,
        )
      )
        throw new PredictiveEvidenceError(
          "PREDICTIVE_POSITION_UNKNOWN",
          "Support envelope must be backed by eligible governed assessments",
        );
      supportAssessments.push(support);
    }
    for (const dimension of input.supportDimensions) {
      const values = supportAssessments
        .filter((assessment) =>
          dimension.evidenceAssessmentIds.includes(assessment.id),
        )
        .map((assessment) =>
          assessment.context_snapshot.values.find(
            (value: { variableKey: string }) =>
              value.variableKey === dimension.variableKey,
          ),
        );
      if (
        values.length !== dimension.evidenceAssessmentIds.length ||
        values.some((value) => !value)
      )
        throw new PredictiveEvidenceError(
          "PREDICTIVE_POSITION_UNKNOWN",
          "Support dimension is not derivable from its governed assessments",
        );
      if (dimension.kind === "NUMERIC_RANGE") {
        if (
          values.some(
            (value) =>
              value.kind !== "NUMERIC" ||
              value.unit.key !== dimension.unit.key ||
              value.unit.revision !== dimension.unit.revision,
          )
        )
          throw new PredictiveEvidenceError("PREDICTIVE_POSITION_UNKNOWN");
        const observed = values.map((value) => Number(value.value));
        if (
          Math.min(...observed) !== dimension.lowerBound ||
          Math.max(...observed) !== dimension.upperBound
        )
          throw new PredictiveEvidenceError(
            "PREDICTIVE_POSITION_UNKNOWN",
            "Numeric support envelope must equal observed governed support",
          );
      } else if (dimension.kind === "TEMPORAL_RANGE") {
        if (values.some((value) => value.kind !== "TEMPORAL"))
          throw new PredictiveEvidenceError("PREDICTIVE_POSITION_UNKNOWN");
        const observed = values
          .map((value) => BigInt(value.epochMicros))
          .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
        if (
          observed[0].toString() !== dimension.startEpochMicros ||
          observed[observed.length - 1].toString() !== dimension.endEpochMicros
        )
          throw new PredictiveEvidenceError(
            "PREDICTIVE_POSITION_UNKNOWN",
            "Temporal support envelope must equal observed governed support",
          );
      } else if (dimension.kind === "CATEGORICAL_SET") {
        if (values.some((value) => value.kind !== "CATEGORICAL"))
          throw new PredictiveEvidenceError("PREDICTIVE_POSITION_UNKNOWN");
        const observed = [
          ...new Set(values.map((value) => String(value.value))),
        ].sort();
        if (
          canonicalValidationJson(observed) !==
          canonicalValidationJson([...dimension.values].sort())
        )
          throw new PredictiveEvidenceError(
            "PREDICTIVE_POSITION_UNKNOWN",
            "Categorical support must equal observed governed support",
          );
      } else {
        if (values.some((value) => value.kind !== "BOOLEAN"))
          throw new PredictiveEvidenceError("PREDICTIVE_POSITION_UNKNOWN");
        const observed = [
          ...new Set(values.map((value) => Boolean(value.value))),
        ].sort();
        if (
          canonicalValidationJson(observed) !==
          canonicalValidationJson([...dimension.values].sort())
        )
          throw new PredictiveEvidenceError(
            "PREDICTIVE_POSITION_UNKNOWN",
            "Boolean support must equal observed governed support",
          );
      }
    }
    const position = assessPosition(
      domain.assessment_result,
      input.contextSnapshot,
      input.supportDimensions,
    );
    return this.repository.createPositionAssessment(
      actor,
      projectId,
      input,
      position,
    );
  }

  registerNegativeEvidence(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId);
    return this.repository.registerScopedEvidence(
      actor,
      projectId,
      "negative",
      negativeFindingInputSchema.parse(raw),
    );
  }

  registerEvidenceConflict(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId);
    return this.repository.registerScopedEvidence(
      actor,
      projectId,
      "conflict",
      conflictInputSchema.parse(raw),
    );
  }

  registerEvidenceLimitation(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId);
    return this.repository.registerScopedEvidence(
      actor,
      projectId,
      "limitation",
      limitationInputSchema.parse(raw),
    );
  }

  materializePredictiveEvidenceSet(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    this.authorize(actor, projectId);
    return this.repository.materializeEvidenceSet(
      actor,
      projectId,
      evidenceSetInputSchema.parse(raw),
    );
  }

  assessEvidenceCompleteness(
    actor: ControlActor,
    projectId: string,
    raw: unknown,
  ) {
    return this.materializePredictiveEvidenceSet(actor, projectId, raw);
  }

  deriveEvidenceStrengthProfile(
    actor: ControlActor,
    projectId: string,
    evidenceSetId: string,
  ) {
    this.authorize(actor, projectId);
    return this.repository.deriveStrengthProfile(
      actor,
      projectId,
      evidenceSetId,
    );
  }
}
