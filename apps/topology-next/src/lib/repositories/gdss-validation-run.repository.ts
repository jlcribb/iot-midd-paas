import type { PoolClient } from "pg";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import {
  assessPairIntegrity,
  canonicalObservationReference,
  canonicalPairSet,
  canonicalPairingContract,
  canonicalPrediction,
  canonicalValidationJson,
  canonicalValidationRun,
  observationReferenceHash,
  pairIntegrityHash,
  predictionCommitmentHash,
  predictionHash,
  predictionObservationPairHash,
  predictionPairSetHash,
  validationRunHash,
  type ObservationReferenceContent,
  type PairSetContent,
  type PairingContract,
  type PredictionContent,
  type ValidationRunContent,
} from "@/lib/gdss/validation";
import { ValidationRunError } from "@/lib/gdss/validation/run-diagnostics";

const actorId = (a: ControlActor) => a.actor_id ?? a.user_id;
export class GdssValidationRunRepository {
  constructor(
    private readonly transaction: TransactionRunner = withTransaction,
  ) {}
  private audit(
    tx: PoolClient,
    projectId: string,
    entityId: string,
    actor: ControlActor,
    action: string,
    details: unknown,
  ) {
    return tx.query(
      "INSERT INTO iot_schema.auditoria(entidad,entidad_id,accion,cambios,contexto)VALUES('gdss_validation',$1::uuid,$2,$3::jsonb,$4::jsonb)",
      [
        entityId,
        action,
        JSON.stringify(details),
        JSON.stringify({
          project_id: projectId,
          actor: actorId(actor),
          capability: "A1",
          subsystem: "gdss006c",
        }),
      ],
    );
  }
  createRun(
    actor: ControlActor,
    projectId: string,
    input: ValidationRunContent,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const c = canonicalValidationRun(input),
        hash = validationRunHash(c);
      let independence = "INDEPENDENT";
      if (c.holdoutId) {
        const h = (
          await tx.query(
            "SELECT independence_state FROM gdss_governed_holdout WHERE id=$1 AND project_id=$2",
            [c.holdoutId, projectId],
          )
        ).rows[0];
        if (!h || h.independence_state !== "INDEPENDENT")
          throw new ValidationRunError(
            "VALIDATION_RUN_INDEPENDENCE_NOT_ELIGIBLE",
          );
        independence = h.independence_state;
      }
      const row = (
        await tx.query(
          "INSERT INTO gdss_validation_run(project_id,run_mode,protocol_version_id,protocol_hash,model_version_id,model_hash,partition_plan_version_id,partition_plan_hash,snapshot_id,snapshot_hash,validity_domain_version_id,validity_domain_hash,holdout_id,holdout_evaluation_reference_id,independence_state,run_content,canonical_content,content_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16::jsonb,$17,$18,$19,$20)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
          [
            projectId,
            c.runMode,
            c.protocolVersionId,
            c.protocolHash,
            c.modelVersionId,
            c.modelHash,
            c.partitionPlanVersionId,
            c.partitionPlanHash,
            c.snapshotId,
            c.snapshotHash,
            c.validityDomainVersionId,
            c.validityDomainHash,
            c.holdoutId ?? null,
            c.holdoutEvaluationReferenceId ?? null,
            independence,
            JSON.stringify(c),
            canonicalValidationJson(c),
            hash,
            idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      const existing = (
        await tx.query(
          "SELECT 1 FROM gdss_validation_run_event WHERE run_id=$1",
          [row.id],
        )
      ).rowCount;
      if (!existing) {
        await tx.query(
          "INSERT INTO gdss_validation_run_event(run_id,sequence,from_status,to_status,actor,reason,idempotency_key)VALUES($1,1,NULL,'CREATED',$2,'created',$3)",
          [row.id, actorId(actor), `create:${idempotencyKey}`],
        );
        await this.audit(
          tx,
          projectId,
          row.id,
          actor,
          "VALIDATION_RUN_CREATED",
          { content_hash: hash },
        );
      }
      return row;
    });
  }
  getRun(projectId: string, runId: string) {
    return this.transaction(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_validation_run WHERE id=$1 AND project_id=$2",
            [runId, projectId],
          )
        ).rows[0],
    );
  }
  transitionRun(
    actor: ControlActor,
    projectId: string,
    runId: string,
    target: string,
    reason: string,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const row = (
        await tx.query(
          "SELECT * FROM gdss_validation_run WHERE id=$1 AND project_id=$2 FOR UPDATE",
          [runId, projectId],
        )
      ).rows[0];
      if (!row) throw new ValidationRunError("VALIDATION_RUN_BINDING_INVALID");
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_validation_run_event WHERE run_id=$1 AND idempotency_key=$2",
          [runId, idempotencyKey],
        )
      ).rows[0];
      if (prior)
        return (
          await tx.query("SELECT * FROM gdss_validation_run WHERE id=$1", [
            runId,
          ])
        ).rows[0];
      const seq = (
        await tx.query<{ n: number }>(
          "SELECT COALESCE(max(sequence),0)::int+1 n FROM gdss_validation_run_event WHERE run_id=$1",
          [runId],
        )
      ).rows[0].n;
      await tx.query(
        "INSERT INTO gdss_validation_run_event(run_id,sequence,from_status,to_status,actor,reason,idempotency_key)VALUES($1,$2,$3,$4,$5,$6,$7)",
        [
          runId,
          seq,
          row.status,
          target,
          actorId(actor),
          reason,
          idempotencyKey,
        ],
      );
      await this.audit(
        tx,
        projectId,
        runId,
        actor,
        `VALIDATION_RUN_${target}`,
        { from: row.status },
      );
      return (
        await tx.query("SELECT * FROM gdss_validation_run WHERE id=$1", [runId])
      ).rows[0];
    });
  }
  createPrediction(
    actor: ControlActor,
    projectId: string,
    runId: string,
    input: PredictionContent,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const c = canonicalPrediction(input),
        hash = predictionHash(c);
      const row = (
        await tx.query(
          "INSERT INTO gdss_prediction_record(project_id,validation_run_id,model_version_id,model_content_hash,target_key,forecast_origin,horizon_key,horizon_duration,horizon_unit_key,horizon_unit_revision,predicted_value,predicted_unit_key,predicted_unit_revision,input_snapshot_hash,parameter_snapshot_hash,boundary_condition_hash,prediction_mode,trajectory_reference,trajectory_hash,prediction_content,canonical_content,content_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20::jsonb,$21,$22,$23,$24)ON CONFLICT(validation_run_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
          [
            projectId,
            runId,
            c.modelVersionId,
            c.modelHash,
            c.targetKey,
            c.forecastOrigin,
            c.horizonKey,
            c.horizonDuration,
            c.horizonUnit.key,
            c.horizonUnit.revision,
            c.predictedValue,
            c.predictedUnit.key,
            c.predictedUnit.revision,
            c.inputSnapshotHash,
            c.parameterSnapshotHash,
            c.boundaryConditionHash,
            c.predictionMode,
            c.trajectoryReference ?? null,
            c.trajectoryHash ?? null,
            JSON.stringify(c),
            canonicalValidationJson(c),
            hash,
            idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      await this.audit(tx, projectId, row.id, actor, "PREDICTION_CREATED", {
        prediction_hash: hash,
      });
      return row;
    });
  }
  commitPrediction(
    actor: ControlActor,
    projectId: string,
    predictionId: string,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const p = (
        await tx.query(
          "SELECT * FROM gdss_prediction_record WHERE id=$1 AND project_id=$2 FOR UPDATE",
          [predictionId, projectId],
        )
      ).rows[0];
      if (!p) throw new ValidationRunError("PREDICTION_NOT_COMMITTED");
      const existing = (
        await tx.query(
          "SELECT * FROM gdss_prediction_commitment WHERE prediction_id=$1",
          [predictionId],
        )
      ).rows[0];
      if (existing) return existing;
      const hash = predictionCommitmentHash(p.content_hash);
      const row = (
        await tx.query(
          "INSERT INTO gdss_prediction_commitment(project_id,prediction_id,prediction_hash,commitment_hash,trust_class,actor,audit_reference,idempotency_key)VALUES($1,$2,$3,$4,'PLATFORM_PROSPECTIVE',$5,$6,$7)RETURNING *",
          [
            projectId,
            predictionId,
            p.content_hash,
            hash,
            actorId(actor),
            `audit:${idempotencyKey}`,
            idempotencyKey,
          ],
        )
      ).rows[0];
      await this.audit(
        tx,
        projectId,
        predictionId,
        actor,
        "PREDICTION_COMMITTED",
        {
          commitment_hash: hash,
          trust_class: "PLATFORM_PROSPECTIVE",
          committed_at: row.committed_at,
        },
      );
      return row;
    });
  }
  createObservationReference(
    actor: ControlActor,
    projectId: string,
    input: ObservationReferenceContent,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const c = canonicalObservationReference(input),
        hash = observationReferenceHash(c);
      const row = (
        await tx.query(
          "INSERT INTO gdss_observation_reference(project_id,observation_identity,source,target_key,observed_value,unit_key,unit_revision,measurement_time,availability_time,ingestion_time,source_content_hash,quality_provenance_reference,successor_of_id,reference_content,canonical_content,content_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14::jsonb,$15,$16,$17,$18)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
          [
            projectId,
            c.observationIdentity,
            c.source,
            c.targetKey,
            c.observedValue,
            c.unit.key,
            c.unit.revision,
            c.measurementTime,
            c.availabilityTime,
            c.ingestionTime,
            c.sourceContentHash,
            c.qualityProvenanceReference,
            c.successorOfId ?? null,
            JSON.stringify(c),
            canonicalValidationJson(c),
            hash,
            idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "OBSERVATION_REFERENCE_CREATED",
        { content_hash: hash, availability_known: c.availabilityTime !== null },
      );
      return row;
    });
  }
  pairPrediction(
    actor: ControlActor,
    projectId: string,
    predictionId: string,
    observationId: string,
    input: PairingContract,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const p = (
        await tx.query(
          "SELECT p.*,c.committed_at FROM gdss_prediction_record p JOIN gdss_prediction_commitment c ON c.prediction_id=p.id WHERE p.id=$1 AND p.project_id=$2",
          [predictionId, projectId],
        )
      ).rows[0];
      if (!p) throw new ValidationRunError("PREDICTION_NOT_COMMITTED");
      const o = (
        await tx.query(
          "SELECT * FROM gdss_observation_reference WHERE id=$1 AND project_id=$2",
          [observationId, projectId],
        )
      ).rows[0];
      if (!o) throw new ValidationRunError("CROSS_PROJECT_PAIRING");
      const c = canonicalPairingContract(input),
        factors: Record<string, number> = {
          second: 1_000,
          minute: 60_000,
          hour: 3_600_000,
          day: 86_400_000,
        },
        expected =
          Date.parse(p.prediction_content.forecastOrigin) +
          p.prediction_content.horizonDuration *
            (factors[p.prediction_content.horizonUnit.key] ?? NaN),
        hash = predictionObservationPairHash(p.content_hash, o.content_hash, c);
      if (c.pairingRule === "NEAREST_WITHIN_TOLERANCE") {
        const candidates = (
          await tx.query(
            "SELECT id,measurement_time FROM gdss_observation_reference WHERE project_id=$1 AND target_key=$2 AND measurement_time IS NOT NULL",
            [projectId, c.targetKey],
          )
        ).rows
          .map((x: { id: string; measurement_time: Date }) => ({
            id: x.id,
            delta: new Date(x.measurement_time).getTime() - expected,
          }))
          .filter((x: { delta: number }) =>
            c.directionality === "BEFORE_ONLY"
              ? x.delta <= 0
              : c.directionality === "AFTER_ONLY"
                ? x.delta >= 0
                : true,
          )
          .filter(
            (x: { delta: number }) =>
              Math.abs(x.delta) <=
              c.tolerance! * (factors[c.toleranceUnit!.key] ?? NaN),
          )
          .sort(
            (
              a: { id: string; delta: number },
              b: { id: string; delta: number },
            ) =>
              Math.abs(a.delta) - Math.abs(b.delta) || a.id.localeCompare(b.id),
          );
        if (candidates[0]?.id !== observationId)
          throw new ValidationRunError(
            "PAIRING_RULE_VIOLATION",
            "Nearest observation must be selected deterministically",
          );
      }
      const pair = (
        await tx.query(
          "INSERT INTO gdss_prediction_observation_pair(project_id,prediction_id,observation_reference_id,target_key,horizon_key,pairing_rule,tolerance,tolerance_unit_key,tolerance_unit_revision,directionality,aggregate_identity,conversion_identity,conversion_version,pairing_contract,pair_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14::jsonb,$15,$16,$17)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
          [
            projectId,
            predictionId,
            observationId,
            c.targetKey,
            c.horizonKey,
            c.pairingRule,
            c.tolerance ?? null,
            c.toleranceUnit?.key ?? null,
            c.toleranceUnit?.revision ?? null,
            c.directionality ?? null,
            c.aggregateIdentity ?? null,
            c.conversionIdentity ?? null,
            c.conversionVersion ?? null,
            JSON.stringify(c),
            hash,
            idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      const state = assessPairIntegrity(
          p.prediction_content,
          o.reference_content,
          c,
          new Date(p.committed_at).toISOString(),
        ),
        details = {
          committedAt: p.committed_at,
          availabilityTime: o.availability_time ?? "UNKNOWN",
          physicalAuthority: "NONE",
        },
        ih = pairIntegrityHash(hash, state, details);
      await tx.query(
        "INSERT INTO gdss_pair_integrity_assessment(project_id,pair_id,state,details,integrity_hash,assessed_by)VALUES($1,$2,$3,$4::jsonb,$5,$6)ON CONFLICT(pair_id)DO NOTHING",
        [
          projectId,
          pair.id,
          state,
          JSON.stringify(details),
          ih,
          actorId(actor),
        ],
      );
      await this.audit(
        tx,
        projectId,
        pair.id,
        actor,
        "PREDICTION_OBSERVATION_PAIRED",
        { pair_hash: hash },
      );
      await this.audit(
        tx,
        projectId,
        pair.id,
        actor,
        "PAIR_INTEGRITY_ASSESSED",
        { state, integrity_hash: ih },
      );
      return { ...pair, integrity_state: state };
    });
  }
  materializePairSet(
    actor: ControlActor,
    projectId: string,
    input: PairSetContent,
    idempotencyKey: string,
  ) {
    return this.transaction(async (tx) => {
      const c = canonicalPairSet(input),
        hash = predictionPairSetHash(c);
      const row = (
        await tx.query(
          "INSERT INTO gdss_prediction_pair_set(project_id,target_key,horizon_key,scope,pair_set_content,canonical_content,pair_set_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
          [
            projectId,
            c.targetKey,
            c.horizonKey,
            c.scope,
            JSON.stringify(c),
            canonicalValidationJson(c),
            hash,
            idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      for (const [pairHash, ordinal] of c.pairHashes.map(
        (x, i) => [x, i] as const,
      )) {
        const q = await tx.query(
          "INSERT INTO gdss_prediction_pair_set_member(pair_set_id,pair_id,pair_hash,ordinal)SELECT $1,id,pair_hash,$3 FROM gdss_prediction_observation_pair WHERE project_id=$4 AND pair_hash=$2 ON CONFLICT DO NOTHING",
          [row.id, pairHash, ordinal, projectId],
        );
        if (q.rowCount !== 1)
          throw new ValidationRunError(
            "PAIRING_RULE_VIOLATION",
            "Pair set member missing or duplicate",
          );
      }
      await this.audit(
        tx,
        projectId,
        row.id,
        actor,
        "PREDICTION_PAIR_SET_MATERIALIZED",
        { pair_set_hash: hash, pairs: c.pairHashes.length },
      );
      return row;
    });
  }
}
