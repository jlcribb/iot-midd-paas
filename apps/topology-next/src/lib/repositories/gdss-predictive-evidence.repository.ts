import type { PoolClient } from "pg";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import {
  canonicalEvidenceSetInput,
  canonicalValidationJson,
  domainAssessmentHash,
  evidenceConflictHash,
  evidenceLimitationHash,
  evidenceReferenceHash,
  evidenceSetHash,
  evidenceStrengthProfileHash,
  negativeEvidenceHash,
  predictivePositionHash,
  validateStrengthAxes,
  type DomainAssessmentInput,
  type EvidenceArtifactType,
  type EvidenceRole,
  type EvidenceSetInput,
  type PredictivePositionInput,
  type StrengthAxis,
  type StrengthState,
} from "@/lib/gdss/validation";
import { PredictiveEvidenceError } from "@/lib/gdss/validation/evidence-diagnostics";

const actorId = (actor: ControlActor) => actor.actor_id ?? actor.user_id;
type Reference = {
  artifactType: EvidenceArtifactType;
  artifactId: string;
  artifactHash: string;
  sourcePhase:
    "GDSS-006A" | "GDSS-006B" | "GDSS-006C" | "GDSS-006D" | "GDSS-006E";
  role: EvidenceRole;
};

export class GdssPredictiveEvidenceRepository {
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
          subsystem: "gdss006e",
        }),
      ],
    );
  }

  getDomainForAssessment(projectId: string, versionId: string) {
    return this.transaction(
      async (tx) =>
        (
          await tx.query(
            "SELECT v.*,i.project_id FROM gdss_validity_domain_version v JOIN gdss_validity_domain_identity i ON i.id=v.domain_identity_id WHERE v.id=$1 AND i.project_id=$2",
            [versionId, projectId],
          )
        ).rows[0],
    );
  }

  createDomainAssessment(
    actor: ControlActor,
    projectId: string,
    input: DomainAssessmentInput,
    result: string,
    predicates: Array<{ predicateKey: string; result: string; reason: string }>,
  ) {
    return this.transaction(async (tx) => {
      const { idempotencyKey: _idempotencyKey, ...semanticInput } = input;
      const content = {
          ...semanticInput,
          assessmentResult: result,
          predicates,
        },
        hash = domainAssessmentHash(content);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      const existing = (
        await tx.query(
          "SELECT * FROM gdss_domain_validity_assessment WHERE project_id=$1 AND (assessment_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, input.idempotencyKey],
        )
      ).rows[0];
      if (existing) {
        if (existing.assessment_hash !== hash)
          throw new PredictiveEvidenceError("EVIDENCE_REFERENCE_INVALID");
        return existing;
      }
      const row = (
        await tx.query(
          "INSERT INTO gdss_domain_validity_assessment(project_id,model_version_id,model_hash,validity_domain_version_id,validity_domain_hash,validation_run_id,target_key,horizon_key,context_snapshot,assessment_result,assessment_content,assessment_hash,idempotency_key,assessed_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10,$11::jsonb,$12,$13,$14)RETURNING *",
          [
            projectId,
            input.modelVersionId,
            input.modelHash,
            input.validityDomainVersionId,
            input.validityDomainHash,
            input.validationRunId,
            input.targetKey,
            input.horizonKey,
            JSON.stringify(input.contextSnapshot),
            result,
            JSON.stringify(content),
            hash,
            input.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      for (const [ordinal, predicate] of predicates.entries())
        await tx.query(
          "INSERT INTO gdss_domain_predicate_assessment(project_id,domain_assessment_id,predicate_key,result,reason,ordinal)VALUES($1,$2,$3,$4,$5,$6)",
          [
            projectId,
            row.id,
            predicate.predicateKey,
            predicate.result,
            predicate.reason,
            ordinal,
          ],
        );
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "DOMAIN_VALIDITY_ASSESSED",
        {
          result,
          assessment_hash: hash,
        },
      );
      return row;
    });
  }

  getDomainAssessment(projectId: string, assessmentId: string) {
    return this.transaction(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_domain_validity_assessment WHERE id=$1 AND project_id=$2",
            [assessmentId, projectId],
          )
        ).rows[0],
    );
  }

  createPositionAssessment(
    actor: ControlActor,
    projectId: string,
    input: PredictivePositionInput,
    position: string,
  ) {
    return this.transaction(async (tx) => {
      const { idempotencyKey: _idempotencyKey, ...semanticInput } = input;
      const content = { ...semanticInput, position },
        hash = predictivePositionHash(content);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      const existing = (
        await tx.query(
          "SELECT * FROM gdss_predictive_position_assessment WHERE project_id=$1 AND (assessment_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, input.idempotencyKey],
        )
      ).rows[0];
      if (existing) {
        if (existing.assessment_hash !== hash)
          throw new PredictiveEvidenceError("EVIDENCE_REFERENCE_INVALID");
        return existing;
      }
      const row = (
        await tx.query(
          "INSERT INTO gdss_predictive_position_assessment(project_id,domain_assessment_id,model_version_id,validity_domain_version_id,validation_run_id,target_key,horizon_key,position,context_snapshot,support_envelope,assessment_content,assessment_hash,idempotency_key,assessed_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10::jsonb,$11::jsonb,$12,$13,$14)RETURNING *",
          [
            projectId,
            input.domainAssessmentId,
            input.modelVersionId,
            input.validityDomainVersionId,
            input.validationRunId,
            input.targetKey,
            input.horizonKey,
            position,
            JSON.stringify(input.contextSnapshot),
            JSON.stringify(input.supportDimensions),
            JSON.stringify(content),
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
        "PREDICTIVE_POSITION_ASSESSED",
        {
          position,
          assessment_hash: hash,
        },
      );
      return row;
    });
  }

  private async verifySourceArtifact(
    tx: PoolClient,
    projectId: string,
    type: EvidenceArtifactType,
    id: string,
    expectedHash: string,
    scope: {
      modelVersionId: string;
      protocolVersionId: string;
      validityDomainVersionId: string;
      targetKey: string;
      horizonKey: string;
    },
  ) {
    const queries: Partial<Record<EvidenceArtifactType, string>> = {
      VALIDATION_RUN:
        "SELECT r.content_hash hash,r.model_version_id,r.protocol_version_id,r.validity_domain_version_id,$3::text target_key,$4::text horizon_key FROM gdss_validation_run r WHERE r.id=$1 AND r.project_id=$2 AND EXISTS(SELECT 1 FROM gdss_validation_target WHERE protocol_version_id=r.protocol_version_id AND target_key=$3)AND EXISTS(SELECT 1 FROM gdss_validation_horizon WHERE protocol_version_id=r.protocol_version_id AND horizon_key=$4)",
      PREDICTION_PAIR_SET:
        "SELECT s.pair_set_hash hash,p.model_version_id,r.protocol_version_id,r.validity_domain_version_id,s.target_key,s.horizon_key FROM gdss_prediction_pair_set s JOIN gdss_prediction_pair_set_member m ON m.pair_set_id=s.id JOIN gdss_prediction_observation_pair po ON po.id=m.pair_id JOIN gdss_prediction_record p ON p.id=po.prediction_id JOIN gdss_validation_run r ON r.id=p.validation_run_id WHERE s.id=$1 AND s.project_id=$2 LIMIT 1",
      METRIC_RESULT:
        "SELECT m.content_hash hash,m.model_version_id,m.protocol_version_id,p.validity_domain_version_id,m.target_key,m.horizon_key FROM gdss_metric_result m JOIN gdss_validation_protocol_version p ON p.id=m.protocol_version_id WHERE m.id=$1 AND m.project_id=$2",
      BASELINE_COMPARISON_RESULT:
        "SELECT c.content_hash hash,m.model_version_id,m.protocol_version_id,p.validity_domain_version_id,m.target_key,m.horizon_key FROM gdss_baseline_comparison_result c JOIN gdss_metric_result m ON m.id=c.model_metric_result_id JOIN gdss_validation_protocol_version p ON p.id=m.protocol_version_id WHERE c.id=$1 AND c.project_id=$2",
      UNCERTAINTY_ASSESSMENT:
        "SELECT u.content_hash hash,r.model_version_id,r.protocol_version_id,r.validity_domain_version_id,s.target_key,s.horizon_key FROM gdss_uncertainty_assessment u JOIN gdss_validation_run r ON r.id=u.run_id JOIN gdss_prediction_pair_set s ON s.id=u.pair_set_id WHERE u.id=$1 AND u.project_id=$2",
      DOMAIN_VALIDITY_ASSESSMENT:
        "SELECT d.assessment_hash hash,d.model_version_id,r.protocol_version_id,d.validity_domain_version_id,d.target_key,d.horizon_key FROM gdss_domain_validity_assessment d JOIN gdss_validation_run r ON r.id=d.validation_run_id WHERE d.id=$1 AND d.project_id=$2",
      PREDICTIVE_POSITION_ASSESSMENT:
        "SELECT d.assessment_hash hash,d.model_version_id,r.protocol_version_id,d.validity_domain_version_id,d.target_key,d.horizon_key FROM gdss_predictive_position_assessment d JOIN gdss_validation_run r ON r.id=d.validation_run_id WHERE d.id=$1 AND d.project_id=$2",
    };
    const query = queries[type];
    if (!query) throw new PredictiveEvidenceError("EVIDENCE_REFERENCE_INVALID");
    const row = (
      await tx.query(
        query,
        type === "VALIDATION_RUN"
          ? [id, projectId, scope.targetKey, scope.horizonKey]
          : [id, projectId],
      )
    ).rows[0];
    if (
      !row ||
      row.hash !== expectedHash ||
      row.model_version_id !== scope.modelVersionId ||
      row.protocol_version_id !== scope.protocolVersionId ||
      row.validity_domain_version_id !== scope.validityDomainVersionId ||
      row.target_key !== scope.targetKey ||
      row.horizon_key !== scope.horizonKey
    )
      throw new PredictiveEvidenceError("EVIDENCE_REFERENCE_INVALID");
  }

  registerScopedEvidence(
    actor: ControlActor,
    projectId: string,
    kind: "negative" | "conflict" | "limitation",
    input: any,
  ) {
    return this.transaction(async (tx) => {
      await this.verifySourceArtifact(
        tx,
        projectId,
        input.sourceArtifactType,
        input.sourceArtifactId,
        input.sourceArtifactHash,
        input,
      );
      const table =
          kind === "negative"
            ? "gdss_predictive_evidence_negative_finding"
            : kind === "conflict"
              ? "gdss_predictive_evidence_conflict"
              : "gdss_predictive_evidence_limitation",
        typeColumn =
          kind === "negative"
            ? "finding_type"
            : kind === "conflict"
              ? "conflict_type"
              : "limitation_type",
        typeValue =
          input.findingType ?? input.conflictType ?? input.limitationType,
        semanticInput = Object.fromEntries(
          Object.entries(input).filter(([key]) => key !== "idempotencyKey"),
        ),
        hash =
          kind === "negative"
            ? negativeEvidenceHash(semanticInput)
            : kind === "conflict"
              ? evidenceConflictHash(semanticInput)
              : evidenceLimitationHash(semanticInput);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      const extraColumns =
        kind === "conflict" ? ",conflicting_artifact_ids" : "";
      const extraValues = kind === "conflict" ? ",$15::uuid[]" : "";
      const params = [
        projectId,
        input.modelVersionId,
        input.protocolVersionId,
        input.validityDomainVersionId,
        input.targetKey,
        input.horizonKey,
        typeValue,
        input.sourceArtifactType,
        input.sourceArtifactId,
        input.sourceArtifactHash,
        input.description,
        hash,
        input.idempotencyKey,
        actorId(actor),
        ...(kind === "conflict"
          ? [[...new Set(input.conflictingArtifactIds)].sort()]
          : []),
      ];
      const row =
        (
          await tx.query(
            `INSERT INTO ${table}(project_id,model_version_id,protocol_version_id,validity_domain_version_id,target_key,horizon_key,${typeColumn},source_artifact_type,source_artifact_id,source_artifact_hash,description,content_hash,idempotency_key,registered_by${extraColumns})VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14${extraValues})ON CONFLICT(project_id,content_hash)DO NOTHING RETURNING *`,
            params,
          )
        ).rows[0] ??
        (
          await tx.query(
            `SELECT * FROM ${table} WHERE project_id=$1 AND content_hash=$2`,
            [projectId, hash],
          )
        ).rows[0];
      const action =
        kind === "negative"
          ? "NEGATIVE_EVIDENCE_REGISTERED"
          : kind === "conflict"
            ? "EVIDENCE_CONFLICT_REGISTERED"
            : "EVIDENCE_LIMITATION_REGISTERED";
      await this.audit(tx, projectId, row.id, actor, action, {
        type: typeValue,
        content_hash: hash,
      });
      return row;
    });
  }

  private async collectReferences(
    tx: PoolClient,
    projectId: string,
    input: EvidenceSetInput,
  ): Promise<Reference[]> {
    const refs: Reference[] = [
      {
        artifactType: "VALIDATION_PROTOCOL_VERSION",
        artifactId: input.protocolVersionId,
        artifactHash: input.protocolHash,
        sourcePhase: "GDSS-006A",
        role: "CONTEXTUAL",
      },
      {
        artifactType: "PARTITION_PLAN_VERSION",
        artifactId: input.partitionPlanVersionId,
        artifactHash: input.partitionPlanHash,
        sourcePhase: "GDSS-006B",
        role: "CONTEXTUAL",
      },
      {
        artifactType: "DATASET_SNAPSHOT",
        artifactId: input.snapshotId,
        artifactHash: input.snapshotHash,
        sourcePhase: "GDSS-006B",
        role: "CONTEXTUAL",
      },
    ];
    const add = (
      rows: any[],
      artifactType: EvidenceArtifactType,
      sourcePhase: Reference["sourcePhase"],
      role: EvidenceRole | ((row: any) => EvidenceRole),
      hashColumn = "content_hash",
    ) => {
      for (const row of rows)
        refs.push({
          artifactType,
          artifactId: row.id,
          artifactHash: row[hashColumn],
          sourcePhase,
          role: typeof role === "function" ? role(row) : role,
        });
    };
    add(
      (
        await tx.query(
          "SELECT id,content_hash,status FROM gdss_validation_run WHERE project_id=$1 AND id=ANY($2::uuid[]) ORDER BY id",
          [projectId, input.validationRunIds],
        )
      ).rows,
      "VALIDATION_RUN",
      "GDSS-006C",
      (row) =>
        row.status === "FAILED" || row.status === "INVALIDATED"
          ? "INVALIDATING"
          : "CONTEXTUAL",
    );
    add(
      (
        await tx.query(
          "SELECT id,pair_set_hash AS content_hash FROM gdss_prediction_pair_set WHERE project_id=$1 AND id=ANY($2::uuid[]) ORDER BY id",
          [projectId, input.pairSetIds],
        )
      ).rows,
      "PREDICTION_PAIR_SET",
      "GDSS-006C",
      "SUPPORTING",
    );
    add(
      (
        await tx.query(
          "SELECT id,content_hash,status FROM gdss_metric_result WHERE project_id=$1 AND pair_set_id=ANY($2::uuid[]) ORDER BY id",
          [projectId, input.pairSetIds],
        )
      ).rows,
      "METRIC_RESULT",
      "GDSS-006D",
      (row) => (row.status === "INVALIDATED" ? "INVALIDATING" : "SUPPORTING"),
    );
    add(
      (
        await tx.query(
          "SELECT id,content_hash,comparison_state FROM gdss_baseline_comparison_result WHERE project_id=$1 AND pair_set_id=ANY($2::uuid[]) ORDER BY id",
          [projectId, input.pairSetIds],
        )
      ).rows,
      "BASELINE_COMPARISON_RESULT",
      "GDSS-006D",
      (row) =>
        row.comparison_state === "MODEL_UNDERPERFORMS_BASELINE"
          ? "CONTRADICTING"
          : row.comparison_state === "INCONCLUSIVE"
            ? "LIMITING"
            : "SUPPORTING",
    );
    add(
      (
        await tx.query(
          "SELECT id,content_hash,knowledge_state FROM gdss_uncertainty_assessment WHERE project_id=$1 AND (pair_set_id=ANY($2::uuid[]) OR run_id=ANY($3::uuid[])) ORDER BY id",
          [projectId, input.pairSetIds, input.validationRunIds],
        )
      ).rows,
      "UNCERTAINTY_ASSESSMENT",
      "GDSS-006D",
      (row) =>
        ["UNKNOWN", "KNOWN_UNQUANTIFIED"].includes(row.knowledge_state)
          ? "LIMITING"
          : "CONTEXTUAL",
    );
    add(
      (
        await tx.query(
          "SELECT DISTINCT i.id,i.content_hash FROM gdss_prediction_interval i JOIN gdss_prediction_observation_pair p ON p.prediction_id=i.prediction_id JOIN gdss_prediction_pair_set_member m ON m.pair_id=p.id WHERE i.project_id=$1 AND m.pair_set_id=ANY($2::uuid[]) ORDER BY i.id",
          [projectId, input.pairSetIds],
        )
      ).rows,
      "PREDICTION_INTERVAL",
      "GDSS-006D",
      "CONTEXTUAL",
    );
    add(
      (
        await tx.query(
          "SELECT id,content_hash FROM gdss_interval_assessment WHERE project_id=$1 AND pair_set_id=ANY($2::uuid[]) ORDER BY id",
          [projectId, input.pairSetIds],
        )
      ).rows,
      "INTERVAL_ASSESSMENT",
      "GDSS-006D",
      "SUPPORTING",
    );
    add(
      (
        await tx.query(
          "SELECT id,assessment_hash,assessment_result FROM gdss_domain_validity_assessment WHERE project_id=$1 AND id=ANY($2::uuid[]) ORDER BY id",
          [projectId, input.domainAssessmentIds],
        )
      ).rows,
      "DOMAIN_VALIDITY_ASSESSMENT",
      "GDSS-006E",
      (row) =>
        row.assessment_result === "OUTSIDE_VALIDITY_DOMAIN"
          ? "INVALIDATING"
          : row.assessment_result === "DOMAIN_UNKNOWN"
            ? "LIMITING"
            : "CONTEXTUAL",
      "assessment_hash",
    );
    add(
      (
        await tx.query(
          "SELECT id,assessment_hash,position FROM gdss_predictive_position_assessment WHERE project_id=$1 AND id=ANY($2::uuid[]) ORDER BY id",
          [projectId, input.positionAssessmentIds],
        )
      ).rows,
      "PREDICTIVE_POSITION_ASSESSMENT",
      "GDSS-006E",
      (row) =>
        row.position === "EXTRAPOLATION" || row.position === "UNKNOWN_POSITION"
          ? "LIMITING"
          : "CONTEXTUAL",
      "assessment_hash",
    );
    const scopeParams = [
      projectId,
      input.modelVersionId,
      input.protocolVersionId,
      input.validityDomainVersionId,
      input.targetKey,
      input.horizonKey,
    ];
    add(
      (
        await tx.query(
          "SELECT id,content_hash FROM gdss_predictive_evidence_negative_finding WHERE project_id=$1 AND model_version_id=$2 AND protocol_version_id=$3 AND validity_domain_version_id=$4 AND target_key=$5 AND horizon_key=$6 ORDER BY id",
          scopeParams,
        )
      ).rows,
      "NEGATIVE_FINDING",
      "GDSS-006E",
      "CONTRADICTING",
    );
    add(
      (
        await tx.query(
          "SELECT id,content_hash FROM gdss_predictive_evidence_conflict WHERE project_id=$1 AND model_version_id=$2 AND protocol_version_id=$3 AND validity_domain_version_id=$4 AND target_key=$5 AND horizon_key=$6 ORDER BY id",
          scopeParams,
        )
      ).rows,
      "EVIDENCE_CONFLICT",
      "GDSS-006E",
      "CONTRADICTING",
    );
    add(
      (
        await tx.query(
          "SELECT id,content_hash FROM gdss_predictive_evidence_limitation WHERE project_id=$1 AND model_version_id=$2 AND protocol_version_id=$3 AND validity_domain_version_id=$4 AND target_key=$5 AND horizon_key=$6 ORDER BY id",
          scopeParams,
        )
      ).rows,
      "EVIDENCE_LIMITATION",
      "GDSS-006E",
      "LIMITING",
    );
    return refs.sort(
      (a, b) =>
        a.artifactType.localeCompare(b.artifactType) ||
        a.artifactId.localeCompare(b.artifactId),
    );
  }

  materializeEvidenceSet(
    actor: ControlActor,
    projectId: string,
    raw: EvidenceSetInput,
  ) {
    return this.transaction(async (tx) => {
      const input = canonicalEvidenceSetInput(raw),
        refs = await this.collectReferences(tx, projectId, input);
      const required: EvidenceArtifactType[] = [
        "VALIDATION_PROTOCOL_VERSION",
        "PARTITION_PLAN_VERSION",
        "DATASET_SNAPSHOT",
        "VALIDATION_RUN",
        "PREDICTION_PAIR_SET",
        "METRIC_RESULT",
        "BASELINE_COMPARISON_RESULT",
        "UNCERTAINTY_ASSESSMENT",
        "DOMAIN_VALIDITY_ASSESSMENT",
        "PREDICTIVE_POSITION_ASSESSMENT",
      ];
      const present = [...new Set(refs.map((ref) => ref.artifactType))].sort(),
        missing = required.filter((type) => !present.includes(type));
      const requiredMetricVersions = (
          await tx.query(
            "SELECT metric_version FROM gdss_validation_acceptance_criterion WHERE protocol_version_id=$1 AND required ORDER BY metric_version",
            [input.protocolVersionId],
          )
        ).rows.map((row) => row.metric_version),
        presentMetricKeys = (
          await tx.query(
            "SELECT DISTINCT d.metric_key FROM gdss_metric_result r JOIN gdss_metric_definition_version d ON d.id=r.metric_definition_version_id WHERE r.project_id=$1 AND r.pair_set_id=ANY($2::uuid[]) AND r.status='COMPUTED'",
            [projectId, input.pairSetIds],
          )
        ).rows.map((row) => row.metric_key),
        missingMetrics = requiredMetricVersions.filter(
          (metric: string) => !presentMetricKeys.includes(metric),
        );
      if (missingMetrics.length)
        throw new PredictiveEvidenceError(
          "EVIDENCE_SET_INCOMPLETE",
          "Protocol-required metric evidence is missing",
          409,
          { missingMetrics },
        );
      if (missing.length)
        throw new PredictiveEvidenceError(
          "EVIDENCE_SET_INCOMPLETE",
          "Required governed evidence is missing",
          409,
          { missing },
        );
      if (refs.length > 10000)
        throw new PredictiveEvidenceError(
          "EVIDENCE_SET_INCOMPLETE",
          "Evidence reference limit exceeded",
        );
      const manifestRefs = refs.map((ref) => ({
        ...ref,
        referenceHash: evidenceReferenceHash(ref),
      }));
      const { idempotencyKey: _idempotencyKey, ...semanticInput } = input;
      const manifest = { ...semanticInput, references: manifestRefs },
        hash = evidenceSetHash(manifest);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_predictive_evidence_set WHERE project_id=$1 AND (content_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, input.idempotencyKey],
        )
      ).rows[0];
      if (prior) {
        if (prior.content_hash !== hash)
          throw new PredictiveEvidenceError("EVIDENCE_REFERENCE_INVALID");
        return prior;
      }
      const row = (
        await tx.query(
          "INSERT INTO gdss_predictive_evidence_set(project_id,semantic_version,model_version_id,model_hash,protocol_version_id,protocol_hash,validity_domain_version_id,validity_domain_hash,partition_plan_version_id,partition_plan_hash,snapshot_id,snapshot_hash,target_key,horizon_key,validation_run_ids,pair_set_ids,domain_assessment_ids,position_assessment_ids,reference_count,manifest,canonical_manifest,content_hash,idempotency_key,materialized_by)VALUES($1,'GDSS_PREDICTIVE_EVIDENCE_SET_V1',$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14::uuid[],$15::uuid[],$16::uuid[],$17::uuid[],$18,$19::jsonb,$20,$21,$22,$23)RETURNING *",
          [
            projectId,
            input.modelVersionId,
            input.modelHash,
            input.protocolVersionId,
            input.protocolHash,
            input.validityDomainVersionId,
            input.validityDomainHash,
            input.partitionPlanVersionId,
            input.partitionPlanHash,
            input.snapshotId,
            input.snapshotHash,
            input.targetKey,
            input.horizonKey,
            input.validationRunIds,
            input.pairSetIds,
            input.domainAssessmentIds,
            input.positionAssessmentIds,
            refs.length,
            JSON.stringify(manifest),
            canonicalValidationJson(manifest),
            hash,
            input.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      for (const [ordinal, ref] of manifestRefs.entries())
        await tx.query(
          "INSERT INTO gdss_predictive_evidence_reference(project_id,evidence_set_id,ordinal,artifact_type,artifact_id,artifact_hash,source_phase,role,reference_hash)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)",
          [
            projectId,
            row.id,
            ordinal,
            ref.artifactType,
            ref.artifactId,
            ref.artifactHash,
            ref.sourcePhase,
            ref.role,
            ref.referenceHash,
          ],
        );
      const completeness = {
        evidenceSetHash: hash,
        requiredArtifactTypes: [...required].sort(),
        presentArtifactTypes: present,
        missingArtifactTypes: missing,
        state: "COMPLETE",
      };
      await tx.query(
        "INSERT INTO gdss_evidence_completeness_assessment(project_id,evidence_set_id,state,required_artifact_types,present_artifact_types,missing_artifact_types,content_hash,assessed_by)VALUES($1,$2,'COMPLETE',$3,$4,$5,$6,$7)",
        [
          projectId,
          row.id,
          completeness.requiredArtifactTypes,
          present,
          missing,
          evidenceSetHash(completeness),
          actorId(actor),
        ],
      );
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "PREDICTIVE_EVIDENCE_SET_MATERIALIZED",
        { content_hash: hash, reference_count: refs.length },
      );
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "EVIDENCE_COMPLETENESS_ASSESSED",
        { state: "COMPLETE", missing: [] },
      );
      return row;
    });
  }

  deriveStrengthProfile(
    actor: ControlActor,
    projectId: string,
    evidenceSetId: string,
  ) {
    return this.transaction(async (tx) => {
      const set = (
        await tx.query(
          "SELECT * FROM gdss_predictive_evidence_set WHERE id=$1 AND project_id=$2",
          [evidenceSetId, projectId],
        )
      ).rows[0];
      if (!set) throw new PredictiveEvidenceError("EVIDENCE_REFERENCE_INVALID");
      const runs = (
        await tx.query(
          "SELECT independence_state,run_mode,snapshot_id FROM gdss_validation_run WHERE id=ANY($1::uuid[]) ORDER BY id",
          [set.validation_run_ids],
        )
      ).rows;
      const positions = (
        await tx.query(
          "SELECT position FROM gdss_predictive_position_assessment WHERE id=ANY($1::uuid[]) ORDER BY id",
          [set.position_assessment_ids],
        )
      ).rows.map((row) => row.position);
      const uncertainty = (
        await tx.query(
          "SELECT u.knowledge_state FROM gdss_predictive_evidence_reference r JOIN gdss_uncertainty_assessment u ON u.id=r.artifact_id WHERE r.evidence_set_id=$1 AND r.artifact_type='UNCERTAINTY_ASSESSMENT'",
          [evidenceSetId],
        )
      ).rows.map((row) => row.knowledge_state);
      const baselines = (
        await tx.query(
          "SELECT DISTINCT v.baseline_key FROM gdss_predictive_evidence_reference r JOIN gdss_baseline_comparison_result c ON c.id=r.artifact_id JOIN gdss_baseline_metric_result m ON m.id=c.baseline_metric_result_id JOIN gdss_baseline_version v ON v.id=m.baseline_version_id WHERE r.evidence_set_id=$1 AND r.artifact_type='BASELINE_COMPARISON_RESULT'",
          [evidenceSetId],
        )
      ).rows.map((row) => row.baseline_key);
      const quality = (
        await tx.query(
          "SELECT count(*)::int total,count(o.quality_provenance_reference)::int known FROM gdss_prediction_pair_set_member m JOIN gdss_prediction_observation_pair p ON p.id=m.pair_id JOIN gdss_observation_reference o ON o.id=p.observation_reference_id WHERE m.pair_set_id=ANY($1::uuid[])",
          [set.pair_set_ids],
        )
      ).rows[0];
      const independence: StrengthState = runs.some(
        (row) => row.independence_state === "INDEPENDENCE_COMPROMISED",
      )
        ? "INSUFFICIENT"
        : runs.some((row) => row.independence_state === "INDEPENDENCE_UNKNOWN")
          ? "LIMITED"
          : "ADEQUATE";
      const temporality: StrengthState = runs.some(
        (row) => row.run_mode === "RETROSPECTIVE",
      )
        ? "LIMITED"
        : runs.every((row) => row.run_mode === "PROSPECTIVE")
          ? "ADEQUATE"
          : "LIMITED";
      const domain: StrengthState = positions.some(
        (value) => value === "UNKNOWN_POSITION",
      )
        ? "UNKNOWN"
        : positions.some((value) => value === "EXTRAPOLATION")
          ? "INSUFFICIENT"
          : positions.some((value) => value === "BOUNDARY_PREDICTION")
            ? "LIMITED"
            : "ADEQUATE";
      const uncertaintyState: StrengthState =
        uncertainty.length === 0 ||
        uncertainty.every((value) => value === "UNKNOWN")
          ? "UNKNOWN"
          : uncertainty.some((value) => value === "UNKNOWN")
            ? "INSUFFICIENT"
            : uncertainty.some((value) => value === "KNOWN_UNQUANTIFIED")
              ? "LIMITED"
              : "ADEQUATE";
      const baseline: StrengthState =
        baselines.length === 0
          ? "INSUFFICIENT"
          : baselines.includes("AUTHORIZED_REFERENCE_MODEL_V1") &&
              baselines.length >= 2
            ? "STRONG"
            : baselines.includes("NAIVE_LAST_VALUE_V1") &&
                baselines.includes("SEASONAL_NAIVE_V1")
              ? "ADEQUATE"
              : "LIMITED";
      const distinctSnapshots = new Set(runs.map((row) => row.snapshot_id))
        .size;
      const replication: StrengthState =
        runs.length < 2 || distinctSnapshots < 2
          ? "INSUFFICIENT"
          : runs.length >= 3 &&
              distinctSnapshots >= 3 &&
              independence === "ADEQUATE"
            ? "STRONG"
            : "ADEQUATE";
      const dataQuality: StrengthState =
        quality.total === 0 || quality.known === 0
          ? "UNKNOWN"
          : quality.known === quality.total
            ? "ADEQUATE"
            : "LIMITED";
      const axes = validateStrengthAxes(
        (
          [
            [
              "INDEPENDENCE",
              independence,
              { states: runs.map((row) => row.independence_state) },
            ],
            [
              "TEMPORALITY",
              temporality,
              {
                modes: runs.map((row) => row.run_mode),
                trustBoundary: "PLATFORM_ONLY",
              },
            ],
            ["DOMAIN_COVERAGE", domain, { positions }],
            [
              "UNCERTAINTY_COMPLETENESS",
              uncertaintyState,
              { knowledgeStates: uncertainty },
            ],
            ["BASELINE_STRENGTH", baseline, { baselines }],
            [
              "REPLICATION",
              replication,
              { runCount: runs.length, distinctSnapshots },
            ],
            [
              "DATA_QUALITY",
              dataQuality,
              { total: quality.total, known: quality.known },
            ],
          ] as Array<[StrengthAxis, StrengthState, unknown]>
        ).map(([axis, state, evidence]) => ({ axis, state, evidence })),
      );
      const content = {
          evidenceSetId,
          evidenceSetHash: set.content_hash,
          methodVersion: "GDSS_EVIDENCE_STRENGTH_V1",
          axes,
        },
        hash = evidenceStrengthProfileHash(content);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        hash,
      ]);
      let profile = (
        await tx.query(
          "SELECT * FROM gdss_evidence_strength_profile WHERE evidence_set_id=$1 AND method_version='GDSS_EVIDENCE_STRENGTH_V1'",
          [evidenceSetId],
        )
      ).rows[0];
      if (!profile) {
        profile = (
          await tx.query(
            "INSERT INTO gdss_evidence_strength_profile(project_id,evidence_set_id,method_version,content_hash,derived_by)VALUES($1,$2,'GDSS_EVIDENCE_STRENGTH_V1',$3,$4)RETURNING *",
            [projectId, evidenceSetId, hash, actorId(actor)],
          )
        ).rows[0];
        for (const axis of axes)
          await tx.query(
            "INSERT INTO gdss_evidence_strength_axis_assessment(project_id,profile_id,axis,state,evidence,content_hash)VALUES($1,$2,$3,$4,$5::jsonb,$6)",
            [
              projectId,
              profile.id,
              axis.axis,
              axis.state,
              JSON.stringify(axis.evidence),
              evidenceStrengthProfileHash({ profileHash: hash, ...axis }),
            ],
          );
        await this.audit(
          tx,
          projectId,
          profile.id,
          actor,
          "EVIDENCE_STRENGTH_PROFILE_DERIVED",
          {
            content_hash: hash,
            axes: axes.map(({ axis, state }) => ({ axis, state })),
          },
        );
      } else if (profile.content_hash !== hash)
        throw new PredictiveEvidenceError("EVIDENCE_STRENGTH_AXIS_INVALID");
      return { ...profile, axes };
    });
  }
}
