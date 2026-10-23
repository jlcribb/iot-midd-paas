import type { PoolClient } from "pg";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import {
  canonicalComparisonJson,
  canonicalCriterionContent,
  comparisonSetHash,
  criterionDefinitionHash,
  type CriterionDefinitionInput,
  type ComparisonAssemblyInput,
} from "@/lib/gdss/decision";
import { validationHash } from "@/lib/gdss/validation";
import { DecisionError } from "@/lib/gdss/decision/diagnostics";

const actorId = (actor: ControlActor) => actor.actor_id ?? actor.user_id,
  actorKind = (actor: ControlActor) =>
    actor.auth_provider?.toLowerCase() === "ai" ||
    /(^|\s)ai[:_-]/.test(
      `${actor.actor_id ?? ""} ${actor.user_id}`.toLowerCase(),
    )
      ? "AI"
      : "HUMAN";
const codes = [
  "COMPARISON_SET_INCOMPLETE",
  "ADVERSE_ALTERNATIVE_OMITTED",
  "CRITERION_INPUT_INCOMPATIBLE",
  "DOMINANCE_NOT_DETERMINABLE",
  "PREFERENCE_REQUIRED",
  "PREFERENCE_PROFILE_MISMATCH",
  "RISK_UNACCEPTABLE",
  "RESOURCE_LIMIT_EXCEEDED",
  "CROSS_PROJECT_DECISION_REFERENCE",
  "DECISION_INPUT_NOT_CURRENT",
  "IDEMPOTENCY_CONFLICT",
  "INVALID_DECISION_LIFECYCLE",
  "DECISION_HISTORY_IMMUTABLE",
  "AI_AUTHORITY_FORBIDDEN",
] as const;
export type CriterionResultRow = {
  projectId: string;
  problemVersionId: string;
  alternativeVersionId: string;
  criterionVersionId: string;
  scenarioEvaluationId: string;
  outcomeId: string | null;
  state: string;
  numericValue: number | null;
  categoricalValue: string | null;
  unit: unknown;
  uncertaintyState: string;
  limitationState: string;
  methodVersion: string;
  computationInputs: unknown;
  evidence: unknown;
  canonicalContent: string;
  resultHash: string;
  idempotencyKey: string;
};
export type ConstraintResultRow = {
  projectId: string;
  problemVersionId: string;
  alternativeVersionId: string;
  constraintId: string;
  scenarioEvaluationId: string;
  outcomeId: string | null;
  result: string;
  admissibility: string;
  evidence: unknown;
  reason: string;
  canonicalContent: string;
  resultHash: string;
  idempotencyKey: string;
};
export type PreparedComparison = {
  input: ComparisonAssemblyInput;
  members: Array<{
    alternativeVersionId: string;
    admissibility: string;
    completeness: string;
    constraintStatus: string;
    uncertaintyStatus: string;
    reason: string;
    pareto: boolean;
    criterionEvaluationIds: string[];
    constraintEvaluationIds: string[];
  }>;
  relations: Array<{
    left: string;
    right: string;
    relation: string;
    reason: string;
    canonical: string;
    hash: string;
  }>;
  tradeoffs: Array<{
    left: string;
    right: string;
    data: any;
    canonical: string;
    hash: string;
  }>;
  uncertaintyConclusion: string;
};

export class GdssDecisionComparisonRepository {
  constructor(
    private readonly transaction: TransactionRunner = withTransaction,
  ) {}
  private run<T>(work: (tx: PoolClient) => Promise<T>): Promise<T> {
    return this.transaction(work).catch((error: unknown) => {
      if (error instanceof DecisionError) throw error;
      const message = error instanceof Error ? error.message : String(error),
        code =
          codes.find((item) => message.includes(item)) ??
          "DECISION_INPUT_NOT_CURRENT";
      throw new DecisionError(code, message);
    });
  }
  private async audit(
    tx: PoolClient,
    actor: ControlActor,
    projectId: string,
    entityType: string,
    entityId: string,
    eventType: string,
    reason: string,
    key: string,
    metadata: unknown = {},
  ) {
    const content = {
        projectId,
        entityType,
        entityId,
        eventType,
        actor: actorId(actor),
        reason,
        metadata,
      },
      hash = validationHash("midd:gdss:decision-comparison-event:v1", content),
      prior = (
        await tx.query(
          "SELECT * FROM gdss_decision_comparison_event WHERE project_id=$1 AND idempotency_key=$2",
          [projectId, key],
        )
      ).rows[0];
    if (prior) {
      if (prior.event_hash !== hash)
        throw new DecisionError("IDEMPOTENCY_CONFLICT");
      return prior;
    }
    const sequence = Number(
      (
        await tx.query(
          "SELECT coalesce(max(sequence),0)+1 n FROM gdss_decision_comparison_event WHERE entity_type=$1 AND entity_id=$2",
          [entityType, entityId],
        )
      ).rows[0].n,
    );
    return (
      await tx.query(
        "INSERT INTO gdss_decision_comparison_event(project_id,entity_type,entity_id,sequence,event_type,actor,actor_kind,reason,idempotency_key,event_hash,metadata)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb)RETURNING *",
        [
          projectId,
          entityType,
          entityId,
          sequence,
          eventType,
          actorId(actor),
          actorKind(actor),
          reason,
          key,
          hash,
          JSON.stringify(metadata),
        ],
      )
    ).rows[0];
  }
  getProblem(projectId: string, id: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_decision_problem_version WHERE id=$1 AND project_id=$2",
            [id, projectId],
          )
        ).rows[0],
    );
  }
  getPreference(projectId: string, id: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT v.*,coalesce(jsonb_agg(jsonb_build_object('objectiveKey',i.objective_key,'ordinalPriority',i.ordinal_priority,'weight',i.weight) ORDER BY i.objective_key) FILTER(WHERE i.id IS NOT NULL),'[]') items FROM gdss_decision_preference_version v LEFT JOIN gdss_decision_preference_item i ON i.preference_version_id=v.id WHERE v.id=$1 AND v.project_id=$2 GROUP BY v.id",
            [id, projectId],
          )
        ).rows[0],
    );
  }
  getRisk(projectId: string, id: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_decision_risk_version WHERE id=$1 AND project_id=$2",
            [id, projectId],
          )
        ).rows[0],
    );
  }
  getCriterion(projectId: string, id: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_decision_criterion_version WHERE id=$1 AND project_id=$2",
            [id, projectId],
          )
        ).rows[0],
    );
  }
  getConstraint(projectId: string, id: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_decision_constraint WHERE id=$1 AND project_id=$2",
            [id, projectId],
          )
        ).rows[0],
    );
  }
  getEvaluation(projectId: string, id: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_scenario_evaluation WHERE id=$1 AND project_id=$2",
            [id, projectId],
          )
        ).rows[0],
    );
  }
  getOutcomes(projectId: string, ids: string[]) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_scenario_outcome WHERE project_id=$1 AND id=ANY($2::uuid[]) ORDER BY id",
            [projectId, ids],
          )
        ).rows,
    );
  }
  getAdmittedAlternatives(projectId: string, problemId: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_decision_alternative_version WHERE project_id=$1 AND problem_version_id=$2 AND status='ADMITTED' ORDER BY id",
            [projectId, problemId],
          )
        ).rows,
    );
  }
  getProblemConstraints(projectId: string, problemId: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_decision_constraint WHERE project_id=$1 AND problem_version_id=$2 ORDER BY constraint_key",
            [projectId, problemId],
          )
        ).rows,
    );
  }
  getProblemObjectives(projectId: string, problemId: string) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_decision_objective WHERE project_id=$1 AND problem_version_id=$2 ORDER BY ordinal",
            [projectId, problemId],
          )
        ).rows,
    );
  }
  getCriteria(projectId: string, ids: string[]) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT * FROM gdss_decision_criterion_version WHERE project_id=$1 AND id=ANY($2::uuid[]) ORDER BY id",
            [projectId, ids],
          )
        ).rows,
    );
  }
  getCriterionEvaluations(projectId: string, ids: string[]) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT e.*,c.direction,c.target_range,c.criterion_key FROM gdss_criterion_evaluation e JOIN gdss_decision_criterion_version c ON c.id=e.criterion_version_id WHERE e.project_id=$1 AND e.id=ANY($2::uuid[]) ORDER BY e.id",
            [projectId, ids],
          )
        ).rows,
    );
  }
  getConstraintEvaluations(projectId: string, ids: string[]) {
    return this.run(
      async (tx) =>
        (
          await tx.query(
            "SELECT e.*,c.constraint_type,c.constraint_key FROM gdss_constraint_evaluation e JOIN gdss_decision_constraint c ON c.id=e.constraint_id WHERE e.project_id=$1 AND e.id=ANY($2::uuid[]) ORDER BY e.id",
            [projectId, ids],
          )
        ).rows,
    );
  }
  createCriterionIdentity(
    actor: ControlActor,
    projectId: string,
    canonicalKey: string,
    idempotencyKey: string,
  ) {
    return this.run(async (tx) => {
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        `criterion-identity:${projectId}:${canonicalKey}`,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_decision_criterion_identity WHERE project_id=$1 AND (canonical_key=$2 OR idempotency_key=$3)",
          [projectId, canonicalKey, idempotencyKey],
        )
      ).rows[0];
      if (prior) {
        if (prior.canonical_key !== canonicalKey)
          throw new DecisionError("IDEMPOTENCY_CONFLICT");
        return prior;
      }
      return (
        await tx.query(
          "INSERT INTO gdss_decision_criterion_identity(project_id,canonical_key,idempotency_key,created_by)VALUES($1,$2,$3,$4)RETURNING *",
          [projectId, canonicalKey, idempotencyKey, actorId(actor)],
        )
      ).rows[0];
    });
  }
  createCriterionVersion(
    actor: ControlActor,
    projectId: string,
    input: CriterionDefinitionInput,
  ) {
    return this.run(async (tx) => {
      const hash = criterionDefinitionHash(input);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        `criterion:${projectId}:${input.identityId}`,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_decision_criterion_version WHERE project_id=$1 AND (criterion_definition_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, input.idempotencyKey],
        )
      ).rows[0];
      if (prior) {
        if (prior.criterion_definition_hash !== hash)
          throw new DecisionError("IDEMPOTENCY_CONFLICT");
        return prior;
      }
      const number = Number(
          (
            await tx.query(
              "SELECT coalesce(max(version_number),0)+1 n FROM gdss_decision_criterion_version WHERE criterion_identity_id=$1",
              [input.identityId],
            )
          ).rows[0].n,
        ),
        row = (
          await tx.query(
            `INSERT INTO gdss_decision_criterion_version(project_id,criterion_identity_id,version_number,predecessor_version_id,semantic_version,criterion_key,direction,target_key,horizon_key,quantity_key,unit,evaluation_method,method_version,required_inputs,missing_data_semantics,uncertainty_semantics,target_range,applicability,canonical_content,criterion_definition_hash,idempotency_key,authored_by)VALUES($1,$2,$3,$4,'GDSS_DECISION_CRITERION_V1',$5,$6,$7,$8,$9,$10::jsonb,$11,$12,$13::jsonb,$14,$15,$16::jsonb,$17::jsonb,$18,$19,$20,$21)RETURNING *`,
            [
              projectId,
              input.identityId,
              number,
              input.predecessorVersionId ?? null,
              input.criterionKey,
              input.direction,
              input.targetKey,
              input.horizonKey,
              input.quantityKey,
              JSON.stringify(input.unit),
              input.evaluationMethod,
              input.methodVersion,
              JSON.stringify(input.requiredInputs),
              input.missingDataSemantics,
              input.uncertaintySemantics,
              JSON.stringify(input.targetRange ?? null),
              JSON.stringify(input.applicability),
              canonicalComparisonJson(canonicalCriterionContent(input)),
              hash,
              input.idempotencyKey,
              actorId(actor),
            ],
          )
        ).rows[0];
      await this.audit(
        tx,
        actor,
        projectId,
        "CRITERION",
        row.id,
        "CREATE",
        "criterion version created",
        `${input.idempotencyKey}:event`,
        { hash },
      );
      return row;
    });
  }
  sealCriterion(
    actor: ControlActor,
    projectId: string,
    id: string,
    expectedHash: string,
    reason: string,
    key: string,
  ) {
    return this.run(async (tx) => {
      const row = (
        await tx.query(
          "SELECT * FROM gdss_decision_criterion_version WHERE id=$1 AND project_id=$2 FOR UPDATE",
          [id, projectId],
        )
      ).rows[0];
      if (!row) throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_decision_comparison_event WHERE project_id=$1 AND idempotency_key=$2",
          [projectId, key],
        )
      ).rows[0];
      if (prior) return row;
      if (row.criterion_definition_hash !== expectedHash)
        throw new DecisionError("DECISION_INPUT_NOT_CURRENT");
      await this.audit(
        tx,
        actor,
        projectId,
        "CRITERION",
        id,
        "SEAL",
        reason,
        key,
        { hash: expectedHash },
      );
      return (
        await tx.query(
          "UPDATE gdss_decision_criterion_version SET status='SEALED',updated_at=clock_timestamp() WHERE id=$1 RETURNING *",
          [id],
        )
      ).rows[0];
    });
  }
  recordAiDenial(
    actor: ControlActor,
    projectId: string,
    entityType: string,
    entityId: string,
    reason: string,
    key: string,
  ) {
    return this.run((tx) =>
      this.audit(
        tx,
        actor,
        projectId,
        entityType,
        entityId,
        "AI_AUTHORITY_DENIAL",
        reason,
        key,
      ),
    );
  }
  materializeCriterion(actor: ControlActor, row: CriterionResultRow) {
    return this.run(async (tx) => {
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        `criterion-result:${row.projectId}:${row.resultHash}`,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_criterion_evaluation WHERE project_id=$1 AND (criterion_result_hash=$2 OR idempotency_key=$3)",
          [row.projectId, row.resultHash, row.idempotencyKey],
        )
      ).rows[0];
      if (prior) {
        if (prior.criterion_result_hash !== row.resultHash)
          throw new DecisionError("IDEMPOTENCY_CONFLICT");
        return prior;
      }
      const result = (
        await tx.query(
          `INSERT INTO gdss_criterion_evaluation(project_id,problem_version_id,alternative_version_id,criterion_version_id,scenario_evaluation_id,outcome_id,state,numeric_value,categorical_value,unit,uncertainty_state,limitation_state,method_version,computation_inputs,evidence,canonical_content,criterion_result_hash,idempotency_key,materialized_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12,$13,$14::jsonb,$15::jsonb,$16,$17,$18,$19)RETURNING *`,
          [
            row.projectId,
            row.problemVersionId,
            row.alternativeVersionId,
            row.criterionVersionId,
            row.scenarioEvaluationId,
            row.outcomeId,
            row.state,
            row.numericValue,
            row.categoricalValue,
            JSON.stringify(row.unit),
            row.uncertaintyState,
            row.limitationState,
            row.methodVersion,
            JSON.stringify(row.computationInputs),
            JSON.stringify(row.evidence),
            row.canonicalContent,
            row.resultHash,
            row.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      await this.audit(
        tx,
        actor,
        row.projectId,
        "CRITERION_EVALUATION",
        result.id,
        "MATERIALIZE",
        "criterion evaluation materialized",
        `${row.idempotencyKey}:event`,
        { hash: row.resultHash },
      );
      return result;
    });
  }
  materializeConstraint(actor: ControlActor, row: ConstraintResultRow) {
    return this.run(async (tx) => {
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        `constraint-result:${row.projectId}:${row.resultHash}`,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_constraint_evaluation WHERE project_id=$1 AND (constraint_evaluation_hash=$2 OR idempotency_key=$3)",
          [row.projectId, row.resultHash, row.idempotencyKey],
        )
      ).rows[0];
      if (prior) {
        if (prior.constraint_evaluation_hash !== row.resultHash)
          throw new DecisionError("IDEMPOTENCY_CONFLICT");
        return prior;
      }
      const result = (
        await tx.query(
          `INSERT INTO gdss_constraint_evaluation(project_id,problem_version_id,alternative_version_id,constraint_id,scenario_evaluation_id,outcome_id,result,admissibility,evidence,reason,canonical_content,constraint_evaluation_hash,idempotency_key,materialized_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10,$11,$12,$13,$14)RETURNING *`,
          [
            row.projectId,
            row.problemVersionId,
            row.alternativeVersionId,
            row.constraintId,
            row.scenarioEvaluationId,
            row.outcomeId,
            row.result,
            row.admissibility,
            JSON.stringify(row.evidence),
            row.reason,
            row.canonicalContent,
            row.resultHash,
            row.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      await this.audit(
        tx,
        actor,
        row.projectId,
        "CONSTRAINT_EVALUATION",
        result.id,
        "MATERIALIZE",
        "constraint evaluation materialized",
        `${row.idempotencyKey}:event`,
        { hash: row.resultHash },
      );
      return result;
    });
  }
  readComparison(projectId: string, id: string) {
    return this.run(async (tx) => {
      const set = (
        await tx.query(
          "SELECT * FROM gdss_decision_comparison_set WHERE id=$1 AND project_id=$2",
          [id, projectId],
        )
      ).rows[0];
      if (!set) return undefined;
      const members = (
          await tx.query(
            "SELECT * FROM gdss_decision_comparison_member WHERE comparison_set_id=$1 ORDER BY alternative_version_id",
            [id],
          )
        ).rows,
        relations = (
          await tx.query(
            "SELECT * FROM gdss_decision_dominance_relation WHERE comparison_set_id=$1 ORDER BY left_alternative_version_id,right_alternative_version_id",
            [id],
          )
        ).rows,
        tradeoffs = (
          await tx.query(
            "SELECT * FROM gdss_tradeoff_assessment WHERE comparison_set_id=$1 ORDER BY left_alternative_version_id,right_alternative_version_id",
            [id],
          )
        ).rows;
      return { ...set, members, relations, tradeoffs };
    });
  }
  assemble(
    actor: ControlActor,
    projectId: string,
    prepared: PreparedComparison,
  ) {
    return this.run(async (tx) => {
      const hash = comparisonSetHash(prepared.input);
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [
        `comparison:${projectId}:${hash}`,
      ]);
      const prior = (
        await tx.query(
          "SELECT * FROM gdss_decision_comparison_set WHERE project_id=$1 AND (comparison_set_hash=$2 OR idempotency_key=$3)",
          [projectId, hash, prepared.input.idempotencyKey],
        )
      ).rows[0];
      if (prior) {
        if (prior.comparison_set_hash !== hash)
          throw new DecisionError("IDEMPOTENCY_CONFLICT");
        return prior;
      }
      const set = (
        await tx.query(
          `INSERT INTO gdss_decision_comparison_set(project_id,problem_version_id,problem_hash,preference_profile_version_id,preference_profile_hash,risk_profile_version_id,risk_profile_hash,canonical_content,comparison_set_hash,idempotency_key,assembled_by)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)RETURNING *`,
          [
            projectId,
            prepared.input.problemVersionId,
            prepared.input.problemHash,
            prepared.input.preferenceProfileVersionId,
            prepared.input.preferenceProfileHash,
            prepared.input.riskProfileVersionId,
            prepared.input.riskProfileHash,
            canonicalComparisonJson(
              (() => {
                const { idempotencyKey: _, ...content } = prepared.input;
                return content;
              })(),
            ),
            hash,
            prepared.input.idempotencyKey,
            actorId(actor),
          ],
        )
      ).rows[0];
      for (const [ordinal, id] of prepared.input.criterionVersionIds.entries())
        await tx.query(
          "INSERT INTO gdss_decision_comparison_criterion(project_id,comparison_set_id,criterion_version_id,ordinal)VALUES($1,$2,$3,$4)",
          [projectId, set.id, id, ordinal],
        );
      for (const member of prepared.members) {
        const saved = (
          await tx.query(
            `INSERT INTO gdss_decision_comparison_member(project_id,comparison_set_id,alternative_version_id,admissibility,criterion_vector_completeness,constraint_status,uncertainty_status,reason,pareto_front)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)RETURNING *`,
            [
              projectId,
              set.id,
              member.alternativeVersionId,
              member.admissibility,
              member.completeness,
              member.constraintStatus,
              member.uncertaintyStatus,
              member.reason,
              member.pareto,
            ],
          )
        ).rows[0];
        for (const id of member.criterionEvaluationIds)
          await tx.query(
            "INSERT INTO gdss_decision_comparison_cell(project_id,comparison_set_id,member_id,criterion_evaluation_id)VALUES($1,$2,$3,$4)",
            [projectId, set.id, saved.id, id],
          );
        for (const id of member.constraintEvaluationIds)
          await tx.query(
            "INSERT INTO gdss_decision_comparison_constraint_ref(project_id,comparison_set_id,member_id,constraint_evaluation_id)VALUES($1,$2,$3,$4)",
            [projectId, set.id, saved.id, id],
          );
      }
      for (const relation of prepared.relations)
        await tx.query(
          "INSERT INTO gdss_decision_dominance_relation(project_id,comparison_set_id,left_alternative_version_id,right_alternative_version_id,relation,reason,canonical_content,dominance_relation_hash)VALUES($1,$2,$3,$4,$5,$6,$7,$8)",
          [
            projectId,
            set.id,
            relation.left,
            relation.right,
            relation.relation,
            relation.reason,
            relation.canonical,
            relation.hash,
          ],
        );
      for (const item of prepared.tradeoffs)
        await tx.query(
          `INSERT INTO gdss_tradeoff_assessment(project_id,comparison_set_id,left_alternative_version_id,right_alternative_version_id,criterion_deltas,constraint_differences,uncertainty_differences,advantages,disadvantages,unknowns,limitations,canonical_content,tradeoff_hash)VALUES($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7::jsonb,$8::jsonb,$9::jsonb,$10::jsonb,$11::jsonb,$12,$13)`,
          [
            projectId,
            set.id,
            item.left,
            item.right,
            JSON.stringify(item.data.deltas),
            JSON.stringify(item.data.constraintDifferences),
            JSON.stringify(item.data.uncertaintyDifferences),
            JSON.stringify(item.data.advantages),
            JSON.stringify(item.data.disadvantages),
            JSON.stringify(item.data.unknowns),
            JSON.stringify(item.data.limitations),
            item.canonical,
            item.hash,
          ],
        );
      await this.audit(
        tx,
        actor,
        projectId,
        "COMPARISON",
        set.id,
        "ASSEMBLE",
        "complete comparison assembled",
        `${prepared.input.idempotencyKey}:assemble`,
        { hash },
      );
      await this.audit(
        tx,
        actor,
        projectId,
        "COMPARISON",
        set.id,
        "DERIVE_DOMINANCE",
        "bounded pairwise dominance derived",
        `${prepared.input.idempotencyKey}:dominance`,
        { pairs: prepared.relations.length },
      );
      await this.audit(
        tx,
        actor,
        projectId,
        "COMPARISON",
        set.id,
        "MATERIALIZE_TRADEOFF",
        "adverse-preserving tradeoffs materialized",
        `${prepared.input.idempotencyKey}:tradeoff`,
        { pairs: prepared.tradeoffs.length },
      );
      return (
        await tx.query(
          "UPDATE gdss_decision_comparison_set SET status='COMPLETE',uncertainty_conclusion=$2,completed_at=clock_timestamp() WHERE id=$1 RETURNING *",
          [set.id, prepared.uncertaintyConclusion],
        )
      ).rows[0];
    });
  }
}
