import { pool } from "@/lib/db/pool";
import { withTransaction, type SqlExecutor, type TransactionRunner } from "@/lib/db/tx";
import { ConflictError, NotFoundError } from "@/lib/errors/domain-errors";
import type { GovernedDeploymentExecution, GovernedDeploymentExecutionAttempt, GovernedDeploymentExecutionResult } from "@/lib/dto/governed-deployment-execution.dto";
import { GOVERNED_DEPLOYMENT_EXECUTION_ENGINE_VERSION, GOVERNED_DEPLOYMENT_EXECUTION_POLICY_VERSION, GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION } from "@/lib/dto/governed-deployment-execution.dto";
import { buildGovernedDeploymentExecutionHash, buildGovernedDeploymentExecutionResultHash } from "@/lib/promotion/governed-deployment-execution-engine";
import { sha256Canonical } from "@/lib/simulation/canonical";

const mapExecution = (row: any): GovernedDeploymentExecution => ({ ...row, id: String(row.id), project_id: String(row.project_id), policy_version_candidate_id: String(row.policy_version_candidate_id), governed_deployment_intent_id: String(row.governed_deployment_intent_id), target_asset_id: String(row.target_asset_id), physical_effects_allowed: false });
const mapAttempt = (row: any): GovernedDeploymentExecutionAttempt => ({ ...row, id: String(row.id), execution_id: String(row.execution_id), target_asset_id: String(row.target_asset_id) });
const mapResult = (row: any): GovernedDeploymentExecutionResult => ({ ...row, execution_id: String(row.execution_id) });

type Provenance = {
  project_id: string; candidate_id: string; intent_id: string; target_asset_id: string; policy_version_hash: string; intent_hash: string;
  delivery_mode: "STAGE" | "FAIL_BEFORE_STAGE" | "STAGE_THEN_FAIL"; provenance_valid: boolean;
};

export class GovernedDeploymentExecutionRepository {
  constructor(private db: SqlExecutor = pool, private transaction: TransactionRunner = withTransaction) {}

  async execute(projectId: string, candidateId: string, intentId: string, actorId: string) {
    return this.transaction(async tx => {
      const provenance = await this.provenance(tx, projectId, candidateId, intentId, true);
      if (!provenance || !provenance.provenance_valid) throw new ConflictError("GOVERNED_DEPLOYMENT_EXECUTION_PROVENANCE_REQUIRED");
      const executionHash = buildGovernedDeploymentExecutionHash(provenance);
      const existing = await this.byIntent(tx, projectId, intentId);
      if (existing) {
        if (existing.execution_hash === executionHash) return existing;
        throw new ConflictError("GOVERNED_DEPLOYMENT_EXECUTION_IDENTITY_CONFLICT");
      }
      const conflicting = await tx.query(`SELECT id FROM public.control_governed_deployment_executions WHERE project_id=$1::uuid AND target_asset_id=$2::uuid AND status IN('PENDING','RUNNING','ROLLBACK_PENDING') FOR UPDATE`, [projectId, provenance.target_asset_id]);
      if (conflicting.rows[0]) throw new ConflictError("GOVERNED_DEPLOYMENT_EXECUTION_CONFLICTING_TARGET_SLOT");

      const created = await tx.query(`INSERT INTO public.control_governed_deployment_executions(project_id,policy_version_candidate_id,governed_deployment_intent_id,target_asset_id,policy_version_hash,intent_hash,execution_hash,execution_policy_version,execution_engine_version,execution_schema_version,delivery_channel,status,rollback_status,created_by,physical_effects_allowed) VALUES($1::uuid,$2::uuid,$3::uuid,$4::uuid,$5,$6,$7,$8,$9,$10,'DATABASE_STAGING','PENDING','NOT_REQUIRED',$11,FALSE) RETURNING *`, [projectId, candidateId, intentId, provenance.target_asset_id, provenance.policy_version_hash, provenance.intent_hash, executionHash, GOVERNED_DEPLOYMENT_EXECUTION_POLICY_VERSION, GOVERNED_DEPLOYMENT_EXECUTION_ENGINE_VERSION, GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION, actorId]);
      let execution = mapExecution(created.rows[0]);
      await this.audit(tx, "GOVERNED_DEPLOYMENT_EXECUTION_CREATED", execution, actorId, { safety_gates: this.safetyGates() });
      execution = await this.transition(tx, execution.id, "RUNNING", "NOT_REQUIRED");
      await this.audit(tx, "GOVERNED_DEPLOYMENT_EXECUTION_STARTED", execution, actorId, { delivery_channel: "DATABASE_STAGING" });

      const before = await this.operationalState(tx, projectId);
      if (provenance.delivery_mode === "FAIL_BEFORE_STAGE") {
        const attempt = await this.attempt(tx, execution, "FAILED", { staged: false, acknowledgement: "SIMULATED_DELIVERY_FAILURE_BEFORE_STAGE" }, "SIMULATED_DELIVERY_FAILURE");
        return this.complete(tx, execution, "FAILED", "NOT_REQUIRED", [attempt], { status: "FAILED", staged: false }, { status: "NOT_REQUIRED", reason: "no_target_side_stage_created" }, actorId, "GOVERNED_DEPLOYMENT_EXECUTION_FAILED");
      }

      const artifactHash = sha256Canonical({ execution_hash: execution.execution_hash, policy_version_hash: execution.policy_version_hash, target_asset_id: execution.target_asset_id, artifact_kind: "NON_ACTIVE_STAGED_POLICY" });
      await tx.query(`INSERT INTO public.control_governed_deployment_staged_artifacts(execution_id,project_id,target_asset_id,policy_version_hash,artifact_hash,status,physical_effects_allowed) VALUES($1::uuid,$2::uuid,$3::uuid,$4,$5,'STAGED',FALSE)`, [execution.id, projectId, provenance.target_asset_id, provenance.policy_version_hash, artifactHash]);
      const afterStage = await this.operationalState(tx, projectId);
      if (JSON.stringify(before) !== JSON.stringify(afterStage)) throw new ConflictError("BLOCKED_M7_6_ACTIVATION_BOUNDARY_VIOLATION");

      if (provenance.delivery_mode === "STAGE_THEN_FAIL") {
        const attempt = await this.attempt(tx, execution, "PARTIALLY_STAGED", { staged: true, artifact_hash: artifactHash, acknowledgement: "SIMULATED_PARTIAL_STAGE" }, "SIMULATED_PARTIAL_DELIVERY_FAILURE");
        execution = await this.transition(tx, execution.id, "FAILED", "PENDING");
        await this.audit(tx, "GOVERNED_DEPLOYMENT_EXECUTION_FAILED", execution, actorId, { staged: true, rollback_required: true });
        execution = await this.transition(tx, execution.id, "ROLLBACK_PENDING", "PENDING");
        await this.audit(tx, "GOVERNED_DEPLOYMENT_ROLLBACK_STARTED", execution, actorId, { artifact_hash: artifactHash });
        await tx.query(`UPDATE public.control_governed_deployment_staged_artifacts SET status='ROLLED_BACK',rolled_back_at=NOW() WHERE execution_id=$1::uuid`, [execution.id]);
        return this.complete(tx, execution, "ROLLED_BACK", "SUCCEEDED", [attempt], { status: "FAILED", staged: true, artifact_hash: artifactHash }, { status: "SUCCEEDED", action: "MARK_STAGED_ARTIFACT_ROLLED_BACK", artifact_hash: artifactHash }, actorId, "GOVERNED_DEPLOYMENT_ROLLBACK_COMPLETED");
      }

      const attempt = await this.attempt(tx, execution, "SUCCEEDED", { staged: true, artifact_hash: artifactHash, acknowledgement: "DATABASE_STAGING_ACK" }, null);
      return this.complete(tx, execution, "SUCCEEDED", "NOT_REQUIRED", [attempt], { status: "STAGED", artifact_hash: artifactHash, acknowledgement: "DATABASE_STAGING_ACK" }, { status: "NOT_REQUIRED", reason: "staging_completed" }, actorId, "GOVERNED_DEPLOYMENT_EXECUTION_SUCCEEDED");
    });
  }

  async list(projectId: string, candidateId: string, intentId: string) {
    await this.requiredProvenance(projectId, candidateId, intentId);
    const result = await this.db.query(`SELECT * FROM public.control_governed_deployment_executions WHERE project_id=$1::uuid AND policy_version_candidate_id=$2::uuid AND governed_deployment_intent_id=$3::uuid ORDER BY created_at`, [projectId, candidateId, intentId]);
    return result.rows.map(mapExecution);
  }

  async get(projectId: string, candidateId: string, intentId: string, executionId: string) {
    await this.requiredProvenance(projectId, candidateId, intentId);
    const execution = await this.db.query(`SELECT * FROM public.control_governed_deployment_executions WHERE id=$1::uuid AND project_id=$2::uuid AND policy_version_candidate_id=$3::uuid AND governed_deployment_intent_id=$4::uuid`, [executionId, projectId, candidateId, intentId]);
    if (!execution.rows[0]) throw new NotFoundError("Governed deployment execution not found in project scope");
    const attempts = await this.db.query(`SELECT * FROM public.control_governed_deployment_execution_attempts WHERE execution_id=$1::uuid ORDER BY attempt_number`, [executionId]);
    const result = await this.db.query(`SELECT * FROM public.control_governed_deployment_execution_results WHERE execution_id=$1::uuid`, [executionId]);
    return { execution: mapExecution(execution.rows[0]), attempts: attempts.rows.map(mapAttempt), result: result.rows[0] ? mapResult(result.rows[0]) : null };
  }

  private async complete(tx: SqlExecutor, execution: GovernedDeploymentExecution, terminalStatus: string, rollbackStatus: string, attempts: GovernedDeploymentExecutionAttempt[], deliveryResult: Record<string, unknown>, rollbackResult: Record<string, unknown>, actorId: string, action: string) {
    const resultHash = buildGovernedDeploymentExecutionResultHash({ execution_hash: execution.execution_hash, attempts: attempts.map(attempt => ({ attempt_number: attempt.attempt_number, request_hash: attempt.request_hash, result_classification: attempt.result_classification, acknowledgement: attempt.acknowledgement, error_class: attempt.error_class })), delivery_result: deliveryResult, rollback_result: rollbackResult });
    const completed = await tx.query(`UPDATE public.control_governed_deployment_executions SET status=$2,rollback_status=$3,result_hash=$4,completed_at=NOW() WHERE id=$1::uuid RETURNING *`, [execution.id, terminalStatus, rollbackStatus, resultHash]);
    const finalExecution = mapExecution(completed.rows[0]);
    await tx.query(`INSERT INTO public.control_governed_deployment_execution_results(execution_id,result_hash,delivery_result,rollback_result) VALUES($1::uuid,$2,$3::jsonb,$4::jsonb)`, [execution.id, resultHash, JSON.stringify(deliveryResult), JSON.stringify(rollbackResult)]);
    await this.audit(tx, action, finalExecution, actorId, { result_hash: resultHash, delivery_result: deliveryResult, rollback_result: rollbackResult });
    return finalExecution;
  }

  private async transition(tx: SqlExecutor, executionId: string, status: string, rollbackStatus: string) {
    const result = await tx.query(`UPDATE public.control_governed_deployment_executions SET status=$2,rollback_status=$3,started_at=CASE WHEN $2='RUNNING' THEN NOW() ELSE started_at END WHERE id=$1::uuid RETURNING *`, [executionId, status, rollbackStatus]);
    return mapExecution(result.rows[0]);
  }

  private async attempt(tx: SqlExecutor, execution: GovernedDeploymentExecution, classification: "SUCCEEDED" | "FAILED" | "PARTIALLY_STAGED" | "BLOCKED", acknowledgement: Record<string, unknown>, errorClass: string | null) {
    const requestHash = sha256Canonical({ execution_hash: execution.execution_hash, attempt_number: 1, delivery_channel: "DATABASE_STAGING", target_asset_id: execution.target_asset_id });
    const result = await tx.query(`INSERT INTO public.control_governed_deployment_execution_attempts(execution_id,attempt_number,delivery_channel,target_asset_id,request_hash,result_classification,acknowledgement,error_class) VALUES($1::uuid,1,'DATABASE_STAGING',$2::uuid,$3,$4,$5::jsonb,$6) RETURNING *`, [execution.id, execution.target_asset_id, requestHash, classification, JSON.stringify(acknowledgement), errorClass]);
    return mapAttempt(result.rows[0]);
  }

  private async requiredProvenance(projectId: string, candidateId: string, intentId: string) {
    const provenance = await this.provenance(this.db, projectId, candidateId, intentId, false);
    if (!provenance || !provenance.provenance_valid) throw new NotFoundError("Governed deployment intent not found in complete project scope");
    return provenance;
  }

  private async byIntent(db: SqlExecutor, projectId: string, intentId: string) {
    const result = await db.query(`SELECT * FROM public.control_governed_deployment_executions WHERE project_id=$1::uuid AND governed_deployment_intent_id=$2::uuid`, [projectId, intentId]);
    return result.rows[0] ? mapExecution(result.rows[0]) : null;
  }

  private async provenance(db: SqlExecutor, projectId: string, candidateId: string, intentId: string, lock: boolean): Promise<Provenance | null> {
    const result = await db.query(`SELECT i.project_id,c.id candidate_id,i.id intent_id,i.target_asset_id,c.policy_version_hash,i.intent_hash,CASE WHEN t.metadata->'control_deployment'->>'delivery_mode' IN ('FAIL_BEFORE_STAGE','STAGE_THEN_FAIL') THEN t.metadata->'control_deployment'->>'delivery_mode' ELSE 'STAGE' END delivery_mode,(i.status='CREATED' AND a.decision='AUTHORIZE_CONTROLLED_DEPLOYMENT_INTENT' AND r.status='PASSED' AND v.status='PASSED' AND ap.decision='APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION' AND i.authorization_id=a.id AND i.deployment_preparation_id=p.id AND i.readiness_assessment_id=r.id AND p.policy_version_candidate_id=c.id AND p.target_asset_id=i.target_asset_id AND a.policy_version_hash=c.policy_version_hash AND a.validation_hash=v.validation_hash AND a.approval_hash=ap.approval_hash AND a.preparation_hash=p.preparation_hash AND a.readiness_hash=r.readiness_hash AND i.policy_version_hash=c.policy_version_hash AND i.preparation_hash=p.preparation_hash AND i.readiness_hash=r.readiness_hash AND i.authorization_hash=a.authorization_hash AND t.project_id=i.project_id) provenance_valid FROM public.control_governed_deployment_intents i JOIN public.control_governed_deployment_authorizations a ON a.id=i.authorization_id JOIN public.control_controlled_deployment_preparations p ON p.id=i.deployment_preparation_id AND p.project_id=i.project_id JOIN public.control_operational_readiness_assessments r ON r.id=i.readiness_assessment_id AND r.deployment_preparation_id=p.id AND r.project_id=i.project_id JOIN public.control_controlled_policy_validations v ON v.id=p.validation_id AND v.project_id=p.project_id JOIN public.control_controlled_policy_approvals ap ON ap.id=p.approval_id AND ap.validation_id=v.id AND ap.project_id=p.project_id JOIN public.control_controlled_policy_version_candidates c ON c.id=i.policy_version_candidate_id AND c.project_id=i.project_id JOIN public.assets t ON t.id=i.target_asset_id WHERE i.project_id=$1::uuid AND i.policy_version_candidate_id=$2::uuid AND i.id=$3::uuid${lock ? " FOR UPDATE OF i" : ""}`, [projectId, candidateId, intentId]);
    return result.rows[0] ? result.rows[0] as Provenance : null;
  }

  private async operationalState(db: SqlExecutor, projectId: string) {
    const result = await db.query(`SELECT (SELECT count(*)::int FROM public.project_control_policies WHERE project_id=$1::uuid) active_policies,(SELECT count(*)::int FROM public.project_control_policy_actuation_bindings WHERE project_id=$1::uuid) runtime_bindings`, [projectId]);
    return result.rows[0];
  }

  private safetyGates() {
    return ["GATE_INTENT_AUTHORIZED", "GATE_PROVENANCE_VALID", "GATE_PROJECT_SCOPE_VALID", "GATE_TARGET_SCOPE_VALID", "GATE_READINESS_PASSED", "GATE_NO_CONFLICTING_EXECUTION", "GATE_NO_ACTIVE_POLICY_MUTATION_PATH", "GATE_DELIVERY_CHANNEL_AVAILABLE", "GATE_ROLLBACK_PATH_DEFINED", "GATE_NO_PHYSICAL_ACTUATION_PATH"];
  }

  private async audit(tx: SqlExecutor, action: string, execution: GovernedDeploymentExecution, actorId: string, changes: Record<string, unknown>) {
    await tx.query(`INSERT INTO iot_schema.auditoria(entidad,entidad_id,accion,cambios,contexto) VALUES('control_governed_deployment_executions',$1::uuid,$2,$3::jsonb,$4::jsonb)`, [execution.id, action, JSON.stringify(changes), JSON.stringify({ project_id: execution.project_id, actor_id: actorId, execution_context: "SIMULATION", delivery_channel: "DATABASE_STAGING", physical_effects: false, rbac_debt: "edit_policies" })]);
  }
}
