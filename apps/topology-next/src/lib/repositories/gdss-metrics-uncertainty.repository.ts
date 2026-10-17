import type { PoolClient } from "pg";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import {
  baselineComparisonHash,
  baselineHash,
  baselinePredictionHash,
  baselineResultHash,
  canonicalBaselineDefinition,
  canonicalComparisonRule,
  canonicalMetricDefinition,
  canonicalPredictionInterval,
  canonicalUncertaintyAssessment,
  canonicalValidationJson,
  compareMetric,
  computeMetric,
  intervalAssessmentHash,
  metricDefinitionHash,
  metricResultHash,
  predictionIntervalHash,
  uncertaintyAssessmentHash,
  uncertaintyCompleteness,
  uncertaintySourceHash,
  validationHash,
  type BaselineDefinitionContent,
  type ComparisonRule,
  type MetricDefinitionContent,
  type MetricPoint,
  type PredictionIntervalContent,
  type UncertaintyAssessmentContent,
} from "@/lib/gdss/validation";
import { MetricFoundationError } from "@/lib/gdss/validation/metric-diagnostics";
const actorId = (a: ControlActor) => a.actor_id ?? a.user_id;
export class GdssMetricsUncertaintyRepository {
  constructor(
    private readonly transaction: TransactionRunner = withTransaction,
  ) {}
  private audit(
    tx: PoolClient,
    p: string,
    id: string,
    a: ControlActor,
    action: string,
    details: unknown,
  ) {
    return tx.query(
      "INSERT INTO iot_schema.auditoria(entidad,entidad_id,accion,cambios,contexto)VALUES('gdss_validation',$1::uuid,$2,$3::jsonb,$4::jsonb)",
      [
        id,
        action,
        JSON.stringify(details),
        JSON.stringify({
          project_id: p,
          actor: actorId(a),
          capability: "A1",
          subsystem: "gdss006d",
        }),
      ],
    );
  }
  createMetricIdentity(a: ControlActor, p: string, key: string) {
    return this.transaction(async (tx) => {
      const row = (
        await tx.query(
          "INSERT INTO gdss_metric_definition_identity(project_id,metric_key,created_by)VALUES($1,$2,$3)ON CONFLICT(project_id,metric_key)DO UPDATE SET metric_key=EXCLUDED.metric_key RETURNING *",
          [p, key, actorId(a)],
        )
      ).rows[0];
      return row;
    });
  }
  createMetricVersion(
    a: ControlActor,
    p: string,
    identityId: string,
    input: MetricDefinitionContent,
  ) {
    return this.transaction(async (tx) => {
      const c = canonicalMetricDefinition(input),
        hash = metricDefinitionHash(c),
        n = (
          await tx.query<{ n: number }>(
            "SELECT COALESCE(max(version_number),0)::int+1 n FROM gdss_metric_definition_version WHERE metric_identity_id=$1",
            [identityId],
          )
        ).rows[0].n,
        row = (
          await tx.query(
            "INSERT INTO gdss_metric_definition_version(project_id,metric_identity_id,version_number,metric_key,category,directionality,implementation_identifier,definition_content,canonical_content,content_hash,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8::jsonb,$9,$10,$11)ON CONFLICT(project_id,content_hash)DO UPDATE SET content_hash=EXCLUDED.content_hash RETURNING *",
            [
              p,
              identityId,
              n,
              c.metricKey,
              c.category,
              c.directionality,
              c.implementationIdentifier,
              JSON.stringify(c),
              canonicalValidationJson(c),
              hash,
              actorId(a),
            ],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "METRIC_DEFINITION_VERSION_CREATED", {
        metric_key: c.metricKey,
        content_hash: hash,
      });
      return row;
    });
  }
  private async metricContext(
    tx: PoolClient,
    p: string,
    versionId: string,
    pairSetId: string,
  ) {
    const d = (
        await tx.query(
          "SELECT * FROM gdss_metric_definition_version WHERE id=$1 AND project_id=$2",
          [versionId, p],
        )
      ).rows[0],
      set = (
        await tx.query(
          "SELECT * FROM gdss_prediction_pair_set WHERE id=$1 AND project_id=$2",
          [pairSetId, p],
        )
      ).rows[0];
    if (!d || !set) throw new MetricFoundationError("METRIC_PAIRSET_INVALID");
    const rows = (
      await tx.query(
        "SELECT po.id pair_id,p.id prediction_id,p.predicted_value prediction,o.observed_value observation,p.forecast_origin,p.horizon_duration,p.horizon_unit_key,p.predicted_unit_key unit_key,p.predicted_unit_revision unit_revision,p.model_version_id,p.model_content_hash model_hash,r.protocol_version_id,r.run_content,o.measurement_time,i.lower_bound,i.upper_bound,i.coverage_level,a.state FROM gdss_prediction_pair_set_member m JOIN gdss_prediction_observation_pair po ON po.id=m.pair_id JOIN gdss_pair_integrity_assessment a ON a.pair_id=po.id JOIN gdss_prediction_record p ON p.id=po.prediction_id JOIN gdss_validation_run r ON r.id=p.validation_run_id JOIN gdss_observation_reference o ON o.id=po.observation_reference_id LEFT JOIN gdss_prediction_interval i ON i.prediction_id=p.id WHERE m.pair_set_id=$1 ORDER BY o.measurement_time NULLS LAST,po.id",
        [pairSetId],
      )
    ).rows;
    if (!rows.length || rows.some((x) => x.state !== "PASS"))
      throw new MetricFoundationError("METRIC_PAIRSET_INVALID");
    if (new Set(rows.map((x) => `${x.unit_key}:${x.unit_revision}`)).size !== 1)
      throw new MetricFoundationError("METRIC_UNIT_MISMATCH");
    return {
      definition: d,
      definitionContent: d.definition_content as MetricDefinitionContent,
      set,
      rows,
    };
  }
  computeMetricResult(
    a: ControlActor,
    p: string,
    versionId: string,
    pairSetId: string,
    key: string,
  ) {
    return this.transaction(async (tx) => {
      const c = await this.metricContext(tx, p, versionId, pairSetId),
        points: MetricPoint[] = c.rows.map((x) => ({
          prediction: x.prediction,
          observation: x.observation,
          predictionTime:
            new Date(x.forecast_origin).getTime() +
            Number(x.horizon_duration) *
              ({ second: 1000, minute: 60000, hour: 3600000, day: 86400000 }[
                x.horizon_unit_key as "second"
              ] ?? Number.NaN),
          observationTime: x.measurement_time
            ? new Date(x.measurement_time).getTime()
            : undefined,
          lower: x.lower_bound ?? undefined,
          upper: x.upper_bound ?? undefined,
        })),
        value = computeMetric(
          c.definition.metric_key,
          points,
          c.definitionContent,
        ),
        exclusionPolicyHash = validationHash(
          "gdss006:exclusion-policy:v1",
          c.rows[0].run_content.exclusionPolicy ?? {
            mode: "GOVERNED_PAIR_SET_ONLY",
          },
        ),
        content = {
          metricDefinitionVersionId: versionId,
          metricDefinitionHash: c.definition.content_hash,
          pairSetId,
          pairSetHash: c.set.pair_set_hash,
          targetKey: c.set.target_key,
          horizonKey: c.set.horizon_key,
          modelVersionId: c.rows[0].model_version_id,
          modelHash: c.rows[0].model_hash,
          protocolVersionId: c.rows[0].protocol_version_id,
          unit: { key: c.rows[0].unit_key, revision: c.rows[0].unit_revision },
          exclusionPolicyHash,
          value,
          numericPolicy: "IEEE_754_BINARY64",
          pairCount: c.rows.length,
        },
        hash = metricResultHash(content),
        row = (
          await tx.query(
            "INSERT INTO gdss_metric_result(project_id,metric_definition_version_id,pair_set_id,model_version_id,model_hash,protocol_version_id,target_key,horizon_key,unit_key,unit_revision,exclusion_policy_hash,result_value,result_content,content_hash,idempotency_key,computed_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14,$15,$16)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
            [
              p,
              versionId,
              pairSetId,
              content.modelVersionId,
              content.modelHash,
              content.protocolVersionId,
              content.targetKey,
              content.horizonKey,
              content.unit.key,
              content.unit.revision,
              exclusionPolicyHash,
              value,
              JSON.stringify(content),
              hash,
              key,
              actorId(a),
            ],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "METRIC_RESULT_COMPUTED", {
        metric_key: c.definition.metric_key,
        value,
        pair_set_hash: c.set.pair_set_hash,
      });
      return row;
    });
  }
  createBaselineIdentity(
    a: ControlActor,
    p: string,
    logicalName: string,
    baselineKey: string,
  ) {
    return this.transaction(
      async (tx) =>
        (
          await tx.query(
            "INSERT INTO gdss_baseline_identity(project_id,baseline_key,logical_name,created_by)VALUES($1,$2,$3,$4)ON CONFLICT(project_id,logical_name)DO UPDATE SET logical_name=EXCLUDED.logical_name RETURNING *",
            [p, baselineKey, logicalName, actorId(a)],
          )
        ).rows[0],
    );
  }
  createBaselineVersion(
    a: ControlActor,
    p: string,
    id: string,
    input: BaselineDefinitionContent,
  ) {
    return this.transaction(async (tx) => {
      const c = canonicalBaselineDefinition(input),
        hash = baselineHash(c),
        n = (
          await tx.query<{ n: number }>(
            "SELECT COALESCE(max(version_number),0)::int+1 n FROM gdss_baseline_version WHERE baseline_identity_id=$1",
            [id],
          )
        ).rows[0].n,
        row = (
          await tx.query(
            "INSERT INTO gdss_baseline_version(project_id,baseline_identity_id,version_number,baseline_key,target_key,horizon_key,reference_model_version_id,reference_model_hash,definition_content,canonical_content,content_hash,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10,$11,$12)ON CONFLICT(project_id,content_hash)DO UPDATE SET content_hash=EXCLUDED.content_hash RETURNING *",
            [
              p,
              id,
              n,
              c.baselineKey,
              c.targetKey,
              c.horizonKey,
              c.referenceModelVersionId ?? null,
              c.referenceModelHash ?? null,
              JSON.stringify(c),
              canonicalValidationJson(c),
              hash,
              actorId(a),
            ],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "BASELINE_VERSION_CREATED", {
        baseline_key: c.baselineKey,
        content_hash: hash,
      });
      return row;
    });
  }
  generateBaselinePredictions(
    a: ControlActor,
    p: string,
    versionId: string,
    pairSetId: string,
  ) {
    return this.transaction(async (tx) => {
      const b = (
          await tx.query(
            "SELECT * FROM gdss_baseline_version WHERE id=$1 AND project_id=$2",
            [versionId, p],
          )
        ).rows[0],
        set = (
          await tx.query(
            "SELECT * FROM gdss_prediction_pair_set WHERE id=$1 AND project_id=$2",
            [pairSetId, p],
          )
        ).rows[0];
      if (
        !b ||
        !set ||
        b.target_key !== set.target_key ||
        b.horizon_key !== set.horizon_key
      )
        throw new MetricFoundationError("BASELINE_PAIRSET_MISMATCH");
      const spec = b.definition_content as BaselineDefinitionContent,
        pairs = (
          await tx.query(
            "SELECT po.id pair_id,pr.forecast_origin,pr.target_key,pr.horizon_key,pr.predicted_unit_key unit_key,pr.predicted_unit_revision unit_revision FROM gdss_prediction_pair_set_member m JOIN gdss_prediction_observation_pair po ON po.id=m.pair_id JOIN gdss_prediction_record pr ON pr.id=po.prediction_id WHERE m.pair_set_id=$1 ORDER BY po.id",
            [pairSetId],
          )
        ).rows,
        out = [];
      for (const pair of pairs) {
        let source: any[] = [],
          useMean = spec.baselineKey === "HISTORICAL_MEAN_V1";
        if (spec.baselineKey === "AUTHORIZED_REFERENCE_MODEL_V1")
          source = (
            await tx.query(
              "SELECT pr.id,pr.predicted_value value,c.committed_at availability FROM gdss_prediction_record pr JOIN gdss_prediction_commitment c ON c.prediction_id=pr.id WHERE pr.project_id=$1 AND pr.model_version_id=$2 AND pr.model_content_hash=$3 AND pr.target_key=$4 AND pr.horizon_key=$5 AND pr.forecast_origin=$6 AND c.committed_at<=$6 ORDER BY c.committed_at,pr.id LIMIT 1",
              [
                p,
                spec.referenceModelVersionId,
                spec.referenceModelHash,
                pair.target_key,
                pair.horizon_key,
                pair.forecast_origin,
              ],
            )
          ).rows;
        else {
          let sql =
              "SELECT id,observed_value value,availability_time availability,measurement_time FROM gdss_observation_reference WHERE project_id=$1 AND target_key=$2 AND unit_key=$3 AND unit_revision=$4 AND availability_time<=$5 AND measurement_time<=$5",
            args: any[] = [
              p,
              pair.target_key,
              pair.unit_key,
              pair.unit_revision,
              pair.forecast_origin,
            ];
          if (spec.baselineKey === "HISTORICAL_MEAN_V1") {
            sql +=
              " AND measurement_time>=$6 AND measurement_time<=$7 ORDER BY measurement_time";
            args.push(spec.referenceWindowStart, spec.referenceWindowEnd);
          } else if (spec.baselineKey === "SEASONAL_NAIVE_V1")
            ((sql +=
              " ORDER BY abs(extract(epoch from(measurement_time-($5::timestamptz-($6||' '||$7)::interval)))),measurement_time DESC LIMIT 1"),
              args.push(spec.seasonalOffset, spec.seasonalUnit!.key));
          else
            sql +=
              " ORDER BY availability_time DESC,measurement_time DESC LIMIT 1";
          source = (await tx.query(sql, args)).rows;
          if (
            !source.length &&
            spec.baselineKey === "SEASONAL_NAIVE_V1" &&
            spec.missingFallback === "HISTORICAL_MEAN"
          ) {
            source = (
              await tx.query(
                "SELECT id,observed_value value,availability_time availability,measurement_time FROM gdss_observation_reference WHERE project_id=$1 AND target_key=$2 AND unit_key=$3 AND unit_revision=$4 AND availability_time<=$5 AND measurement_time<=$5 ORDER BY measurement_time",
                [
                  p,
                  pair.target_key,
                  pair.unit_key,
                  pair.unit_revision,
                  pair.forecast_origin,
                ],
              )
            ).rows;
            useMean = true;
          }
        }
        if (!source.length)
          throw new MetricFoundationError(
            "BASELINE_FUTURE_LEAKAGE",
            "No eligible pre-origin baseline input",
          );
        const value = useMean
            ? source.reduce((s, x) => s + Number(x.value), 0) / source.length
            : Number(source[0].value),
          latest = source.reduce(
            (m, x) =>
              !x.availability
                ? m
                : !m || new Date(x.availability) > new Date(m)
                  ? x.availability
                  : m,
            null,
          ),
          content = {
            baselineVersionId: versionId,
            baselineHash: b.content_hash,
            pairId: pair.pair_id,
            targetKey: pair.target_key,
            forecastOrigin: new Date(pair.forecast_origin).toISOString(),
            horizonKey: pair.horizon_key,
            predictedValue: value,
            unit: { key: pair.unit_key, revision: pair.unit_revision },
            inputIds: source.map((x) => x.id).sort(),
            latestInputAvailability: latest
              ? new Date(latest).toISOString()
              : null,
          },
          hash = baselinePredictionHash(content),
          inserted = (
            await tx.query(
              "INSERT INTO gdss_baseline_prediction_record(project_id,baseline_version_id,pair_id,forecast_origin,target_key,horizon_key,predicted_value,unit_key,unit_revision,input_reference,latest_input_availability,content_hash,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12,$13)ON CONFLICT(baseline_version_id,pair_id)DO NOTHING RETURNING *",
              [
                p,
                versionId,
                pair.pair_id,
                pair.forecast_origin,
                pair.target_key,
                pair.horizon_key,
                value,
                pair.unit_key,
                pair.unit_revision,
                JSON.stringify(content.inputIds),
                latest,
                hash,
                actorId(a),
              ],
            )
          ).rows[0],
          row =
            inserted ??
            (
              await tx.query(
                "SELECT * FROM gdss_baseline_prediction_record WHERE baseline_version_id=$1 AND pair_id=$2",
                [versionId, pair.pair_id],
              )
            ).rows[0];
        await this.audit(tx, p, row.id, a, "BASELINE_PREDICTION_GENERATED", {
          baseline_version_id: versionId,
          pair_id: pair.pair_id,
        });
        out.push(row);
      }
      return out;
    });
  }
  computeBaselineMetricResult(
    a: ControlActor,
    p: string,
    baselineVersionId: string,
    metricVersionId: string,
    pairSetId: string,
    key: string,
  ) {
    return this.transaction(async (tx) => {
      const d = (
          await tx.query(
            "SELECT * FROM gdss_metric_definition_version WHERE id=$1 AND project_id=$2",
            [metricVersionId, p],
          )
        ).rows[0],
        b = (
          await tx.query(
            "SELECT * FROM gdss_baseline_version WHERE id=$1 AND project_id=$2",
            [baselineVersionId, p],
          )
        ).rows[0],
        set = (
          await tx.query(
            "SELECT * FROM gdss_prediction_pair_set WHERE id=$1 AND project_id=$2",
            [pairSetId, p],
          )
        ).rows[0],
        rows = (
          await tx.query(
            "SELECT bp.predicted_value prediction,o.observed_value observation,bp.unit_key,bp.unit_revision FROM gdss_prediction_pair_set_member m JOIN gdss_prediction_observation_pair po ON po.id=m.pair_id JOIN gdss_observation_reference o ON o.id=po.observation_reference_id JOIN gdss_baseline_prediction_record bp ON bp.pair_id=po.id AND bp.baseline_version_id=$2 WHERE m.pair_set_id=$1",
            [pairSetId, baselineVersionId],
          )
        ).rows,
        total = (
          await tx.query(
            "SELECT count(*)::int n FROM gdss_prediction_pair_set_member WHERE pair_set_id=$1",
            [pairSetId],
          )
        ).rows[0].n;
      if (!d || !b || !set || rows.length !== total)
        throw new MetricFoundationError("BASELINE_PAIRSET_MISMATCH");
      const value = computeMetric(d.metric_key, rows, d.definition_content),
        content = {
          baselineVersionId,
          baselineHash: b.content_hash,
          metricVersionId,
          metricHash: d.content_hash,
          pairSetId,
          pairSetHash: set.pair_set_hash,
          targetKey: set.target_key,
          horizonKey: set.horizon_key,
          value,
        },
        hash = baselineResultHash(content),
        row = (
          await tx.query(
            "INSERT INTO gdss_baseline_metric_result(project_id,baseline_version_id,metric_definition_version_id,pair_set_id,target_key,horizon_key,unit_key,unit_revision,result_value,result_content,content_hash,idempotency_key,computed_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12,$13)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
            [
              p,
              baselineVersionId,
              metricVersionId,
              pairSetId,
              set.target_key,
              set.horizon_key,
              rows[0].unit_key,
              rows[0].unit_revision,
              value,
              JSON.stringify(content),
              hash,
              key,
              actorId(a),
            ],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "BASELINE_METRIC_RESULT_COMPUTED", {
        value,
        pair_set_hash: set.pair_set_hash,
      });
      return row;
    });
  }
  compare(
    a: ControlActor,
    p: string,
    modelResultId: string,
    baselineResultId: string,
    input: ComparisonRule,
    key: string,
  ) {
    return this.transaction(async (tx) => {
      const rule = canonicalComparisonRule(input),
        m = (
          await tx.query(
            "SELECT * FROM gdss_metric_result WHERE id=$1 AND project_id=$2",
            [modelResultId, p],
          )
        ).rows[0],
        b = (
          await tx.query(
            "SELECT * FROM gdss_baseline_metric_result WHERE id=$1 AND project_id=$2",
            [baselineResultId, p],
          )
        ).rows[0];
      if (
        !m ||
        !b ||
        m.pair_set_id !== b.pair_set_id ||
        m.metric_definition_version_id !== b.metric_definition_version_id
      )
        throw new MetricFoundationError("BASELINE_PAIRSET_MISMATCH");
      const state = compareMetric(m.result_value, b.result_value, rule),
        content = {
          modelResultId,
          baselineResultId,
          pairSetId: m.pair_set_id,
          metricVersionId: m.metric_definition_version_id,
          modelValue: m.result_value,
          baselineValue: b.result_value,
          rule,
          state,
        },
        hash = baselineComparisonHash(content),
        row = (
          await tx.query(
            "INSERT INTO gdss_baseline_comparison_result(project_id,model_metric_result_id,baseline_metric_result_id,pair_set_id,metric_definition_version_id,comparison_state,model_value,baseline_value,difference,tolerance,comparison_rule,content_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12,$13,$14)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
            [
              p,
              modelResultId,
              baselineResultId,
              m.pair_set_id,
              m.metric_definition_version_id,
              state,
              m.result_value,
              b.result_value,
              m.result_value - b.result_value,
              rule.tolerance,
              JSON.stringify(rule),
              hash,
              key,
              actorId(a),
            ],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "BASELINE_COMPARISON_CREATED", {
        state,
      });
      return row;
    });
  }
  createUncertaintyAssessment(
    a: ControlActor,
    p: string,
    input: UncertaintyAssessmentContent,
    runId: string | null,
    pairSetId: string | null,
    key: string,
  ) {
    return this.transaction(async (tx) => {
      const c = canonicalUncertaintyAssessment(input),
        sourceHash = uncertaintySourceHash({
          sourceType: c.sourceType,
          scope: c.scope,
        }),
        insertedSource = (
          await tx.query(
            "INSERT INTO gdss_uncertainty_source(project_id,source_type,scope,source_hash,created_by)VALUES($1,$2,$3,$4,$5)ON CONFLICT(project_id,source_type,scope)DO NOTHING RETURNING *",
            [p, c.sourceType, c.scope, sourceHash, actorId(a)],
          )
        ).rows[0],
        source =
          insertedSource ??
          (
            await tx.query(
              "SELECT * FROM gdss_uncertainty_source WHERE project_id=$1 AND source_type=$2 AND scope=$3",
              [p, c.sourceType, c.scope],
            )
          ).rows[0];
      if (c.method)
        await tx.query(
          "INSERT INTO gdss_uncertainty_propagation_method_version(project_id,method,version,contract,content_hash,created_by)VALUES($1,$2,'V1',$3::jsonb,$4,$5)ON CONFLICT(project_id,method,version)DO NOTHING",
          [
            p,
            c.method,
            JSON.stringify({
              method: c.method,
              assumptions: c.assumptions,
              dependencies: c.dependencies,
            }),
            validationHash("gdss006:uncertainty-method:v1", {
              method: c.method,
            }),
            actorId(a),
          ],
        );
      const hash = uncertaintyAssessmentHash(c),
        row = (
          await tx.query(
            "INSERT INTO gdss_uncertainty_assessment(project_id,source_id,run_id,pair_set_id,knowledge_state,method,lower_bound,upper_bound,unit_key,unit_revision,assessment_content,content_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12,$13,$14)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
            [
              p,
              source.id,
              runId,
              pairSetId,
              c.knowledgeState,
              c.method,
              c.lowerBound ?? null,
              c.upperBound ?? null,
              c.unit?.key ?? null,
              c.unit?.revision ?? null,
              JSON.stringify(c),
              hash,
              key,
              actorId(a),
            ],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "UNCERTAINTY_ASSESSMENT_CREATED", {
        source_type: c.sourceType,
        knowledge_state: c.knowledgeState,
      });
      return row;
    });
  }
  createPredictionInterval(
    a: ControlActor,
    p: string,
    input: PredictionIntervalContent,
    key: string,
  ) {
    return this.transaction(async (tx) => {
      const c = canonicalPredictionInterval(input),
        hash = predictionIntervalHash(c),
        row = (
          await tx.query(
            "INSERT INTO gdss_prediction_interval(project_id,prediction_id,lower_bound,upper_bound,coverage_level,unit_key,unit_revision,method,method_version,content_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
            [
              p,
              c.predictionId,
              c.lowerBound,
              c.upperBound,
              c.coverageLevel,
              c.unit.key,
              c.unit.revision,
              c.method,
              c.methodVersion,
              hash,
              key,
              actorId(a),
            ],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "PREDICTION_INTERVAL_CREATED", {
        coverage_level: c.coverageLevel,
        method: c.method,
      });
      return row;
    });
  }
  assessIntervalCoverage(
    a: ControlActor,
    p: string,
    pairSetId: string,
    key: string,
  ) {
    return this.transaction(async (tx) => {
      const rows = (
          await tx.query(
            "SELECT o.observed_value,i.lower_bound,i.upper_bound,i.coverage_level FROM gdss_prediction_pair_set_member m JOIN gdss_prediction_observation_pair po ON po.id=m.pair_id JOIN gdss_observation_reference o ON o.id=po.observation_reference_id JOIN gdss_prediction_interval i ON i.prediction_id=po.prediction_id WHERE m.pair_set_id=$1",
            [pairSetId],
          )
        ).rows,
        total = (
          await tx.query(
            "SELECT count(*)::int n FROM gdss_prediction_pair_set_member WHERE pair_set_id=$1",
            [pairSetId],
          )
        ).rows[0].n;
      if (
        !total ||
        rows.length !== total ||
        new Set(rows.map((x) => x.coverage_level)).size !== 1
      )
        throw new MetricFoundationError("PREDICTION_INTERVAL_INVALID");
      const points = rows.map((x) => ({
          prediction: 0,
          observation: x.observed_value,
          lower: x.lower_bound,
          upper: x.upper_bound,
        })),
        coverage = computeMetric("INTERVAL_COVERAGE_V1", points, {
          semanticVersion: "GDSS_METRIC_DEFINITION_V1",
          metricKey: "INTERVAL_COVERAGE_V1",
          name: "coverage",
          category: "INTERVAL",
          formulaVersion: "V1",
          directionality: "HIGHER_IS_BETTER",
          requiredInputs: ["interval", "observation"],
          unitSemantics: "dimensionless",
          aggregationSemantics: "fraction",
          missingnessBehavior: "REJECT",
          validityConstraints: [],
          implementationIdentifier: "midd-gdss006d-v1",
        }),
        width = computeMetric("MEAN_INTERVAL_WIDTH_V1", points, {
          semanticVersion: "GDSS_METRIC_DEFINITION_V1",
          metricKey: "MEAN_INTERVAL_WIDTH_V1",
          name: "width",
          category: "INTERVAL",
          formulaVersion: "V1",
          directionality: "LOWER_IS_BETTER",
          requiredInputs: ["interval"],
          unitSemantics: "prediction unit",
          aggregationSemantics: "mean",
          missingnessBehavior: "REJECT",
          validityConstraints: [],
          implementationIdentifier: "midd-gdss006d-v1",
        }),
        content = {
          pairSetId,
          coverageLevel: rows[0].coverage_level,
          empiricalCoverage: coverage,
          meanIntervalWidth: width,
          count: total,
        },
        hash = intervalAssessmentHash(content),
        row = (
          await tx.query(
            "INSERT INTO gdss_interval_assessment(project_id,pair_set_id,coverage_level,empirical_coverage,mean_interval_width,eligible_count,total_count,content_hash,idempotency_key,assessed_by)VALUES($1,$2,$3,$4,$5,$6,$6,$7,$8,$9)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
            [
              p,
              pairSetId,
              rows[0].coverage_level,
              coverage,
              width,
              total,
              hash,
              key,
              actorId(a),
            ],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "INTERVAL_COVERAGE_ASSESSED", {
        empirical_coverage: coverage,
        mean_interval_width: width,
      });
      return row;
    });
  }
  assessCompleteness(
    a: ControlActor,
    p: string,
    scope: string,
    assessmentIds: string[],
    key: string,
  ) {
    return this.transaction(async (tx) => {
      const rows = (
        await tx.query(
          "SELECT id,knowledge_state FROM gdss_uncertainty_assessment WHERE project_id=$1 AND id=ANY($2::uuid[])",
          [p, assessmentIds],
        )
      ).rows;
      if (rows.length !== assessmentIds.length)
        throw new MetricFoundationError("UNCERTAINTY_SOURCE_INVALID");
      const state = uncertaintyCompleteness(rows.map((x) => x.knowledge_state)),
        content = { scope, assessmentIds: [...assessmentIds].sort(), state },
        hash = validationHash("gdss006:uncertainty-completeness:v1", content),
        row = (
          await tx.query(
            "INSERT INTO gdss_uncertainty_completeness_assessment(project_id,scope,state,assessment_ids,content_hash,idempotency_key,assessed_by)VALUES($1,$2,$3,$4,$5,$6,$7)ON CONFLICT(project_id,idempotency_key)DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *",
            [p, scope, state, content.assessmentIds, hash, key, actorId(a)],
          )
        ).rows[0];
      await this.audit(tx, p, row.id, a, "UNCERTAINTY_COMPLETENESS_ASSESSED", {
        state,
      });
      return row;
    });
  }
}
