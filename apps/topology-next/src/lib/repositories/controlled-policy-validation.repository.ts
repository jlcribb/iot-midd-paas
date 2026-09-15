import { pool } from "@/lib/db/pool";
import { withTransaction, type SqlExecutor, type TransactionRunner } from "@/lib/db/tx";
import { ConflictError } from "@/lib/errors/domain-errors";
import { CONTROLLED_POLICY_APPROVAL_POLICY_VERSION, CONTROLLED_POLICY_VALIDATION_ENGINE_VERSION, CONTROLLED_POLICY_VALIDATION_POLICY_VERSION, type ControlledPolicyApprovalDecision, type ControlledPolicyValidation } from "@/lib/dto/controlled-policy-validation.dto";
import { buildControlledPolicyApprovalHash, evaluateControlledPolicyValidation, type ControlledPolicyValidationInput } from "@/lib/promotion/controlled-policy-validation-engine";

const mapValidation = (row: any): ControlledPolicyValidation => ({ ...row, id: String(row.id), project_id: String(row.project_id), policy_version_candidate_id: String(row.policy_version_candidate_id), gate_results: row.gate_results ?? [], physical_effects_allowed: false });
const mapApproval = (row: any) => ({ ...row, id: String(row.id), project_id: String(row.project_id), policy_version_candidate_id: String(row.policy_version_candidate_id), validation_id: String(row.validation_id), physical_effects_allowed: false });

export class ControlledPolicyValidationRepository {
  constructor(private db: SqlExecutor = pool, private transaction: TransactionRunner = withTransaction) {}

  async createOrGet(projectId: string, candidateId: string, actorId: string) {
    return this.transaction(async tx => {
      const input = await this.input(tx, projectId, candidateId);
      if (!input) throw new ConflictError("CONTROLLED_POLICY_VALIDATION_PROVENANCE_CONFLICT");
      const existing = await this.validation(tx, projectId, candidateId);
      if (existing) return existing;
      const built = evaluateControlledPolicyValidation(input);
      const inserted = await tx.query(`INSERT INTO public.control_controlled_policy_validations(project_id,policy_version_candidate_id,policy_version_hash,validation_hash,validation_policy_version,validation_engine_version,status,blocking_pass_count,blocking_fail_count,warning_count,schema_version,created_by,physical_effects_allowed) VALUES($1::uuid,$2::uuid,$3,$4,$5,$6,$7,$8,$9,0,1,$10,FALSE) ON CONFLICT(project_id,policy_version_candidate_id,validation_policy_version) DO NOTHING RETURNING id`, [projectId,candidateId,input.policy_version_hash,built.validation_hash,CONTROLLED_POLICY_VALIDATION_POLICY_VERSION,CONTROLLED_POLICY_VALIDATION_ENGINE_VERSION,built.status,built.results.filter(g=>g.status==="PASS").length,built.results.filter(g=>g.status!=="PASS").length,actorId]);
      if (!inserted.rows[0]) return this.validation(tx, projectId, candidateId);
      const validationId = String(inserted.rows[0].id);
      for (const gate of built.results) await tx.query(`INSERT INTO public.control_controlled_policy_validation_gate_results(validation_id,gate_code,gate_version,status,severity,reason_code,details,evidence_reference) VALUES($1::uuid,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb)`, [validationId,gate.gate_code,gate.gate_version,gate.status,gate.severity,gate.reason_code,JSON.stringify(gate.details),JSON.stringify(gate.evidence_reference)]);
      await tx.query(`INSERT INTO iot_schema.auditoria(entidad,entidad_id,accion,cambios,contexto) VALUES('control_controlled_policy_validations',$1::uuid,'CONTROLLED_POLICY_VALIDATION_CREATED',$2::jsonb,$3::jsonb)`, [validationId,JSON.stringify({policy_version_hash:input.policy_version_hash,validation_hash:built.validation_hash,status:built.status,blocking_pass_count:built.results.filter(g=>g.status==="PASS").length,blocking_fail_count:built.results.filter(g=>g.status!=="PASS").length}),JSON.stringify({project_id:projectId,actor_id:actorId,execution_context:"SIMULATION",physical_effects:false})]);
      return this.validation(tx, projectId, candidateId);
    });
  }

  async list(projectId: string, candidateId: string) { const result = await this.db.query(this.validationQuery("WHERE v.project_id=$1::uuid AND v.policy_version_candidate_id=$2::uuid"), [projectId,candidateId]); return result.rows.map(mapValidation); }
  async get(projectId: string, candidateId: string, validationId: string) { return this.validation(this.db, projectId, candidateId, validationId); }

  async approve(projectId: string, candidateId: string, validationId: string, decision: ControlledPolicyApprovalDecision, rationale: string, reviewerId: string) {
    return this.transaction(async tx => {
      const validation = await this.validation(tx, projectId, candidateId, validationId);
      if (!validation) throw new ConflictError("CONTROLLED_POLICY_VALIDATION_NOT_FOUND");
      if (decision === "APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION" && validation.status !== "PASSED") throw new ConflictError("CONTROLLED_POLICY_APPROVAL_REQUIRES_PASSED_VALIDATION");
      const candidate = await tx.query("SELECT policy_version_hash FROM public.control_controlled_policy_version_candidates WHERE project_id=$1::uuid AND id=$2::uuid", [projectId,candidateId]);
      if (!candidate.rows[0]) throw new ConflictError("CONTROLLED_POLICY_VALIDATION_PROVENANCE_CONFLICT");
      const approvalHash = buildControlledPolicyApprovalHash({policy_version_hash:String(candidate.rows[0].policy_version_hash),validation_hash:validation.validation_hash,decision,rationale,reviewer_id:reviewerId});
      const inserted = await tx.query(`INSERT INTO public.control_controlled_policy_approvals(project_id,policy_version_candidate_id,validation_id,validation_hash,decision,rationale,reviewer_id,approval_hash,approval_policy_version,schema_version,physical_effects_allowed) VALUES($1::uuid,$2::uuid,$3::uuid,$4,$5,$6,$7,$8,$9,1,FALSE) ON CONFLICT(validation_id) DO NOTHING RETURNING *`, [projectId,candidateId,validationId,validation.validation_hash,decision,rationale.trim(),reviewerId,approvalHash,CONTROLLED_POLICY_APPROVAL_POLICY_VERSION]);
      if (!inserted.rows[0]) { const existing = await this.approvalFrom(tx,projectId,candidateId,validationId); if (existing?.approval_hash === approvalHash) return existing; throw new ConflictError("CONTROLLED_POLICY_APPROVAL_ALREADY_RECORDED"); }
      const approval = mapApproval(inserted.rows[0]);
      await tx.query(`INSERT INTO iot_schema.auditoria(entidad,entidad_id,accion,cambios,contexto) VALUES('control_controlled_policy_approvals',$1::uuid,'CONTROLLED_POLICY_APPROVAL_RECORDED',$2::jsonb,$3::jsonb)`, [approval.id,JSON.stringify({policy_version_hash:candidate.rows[0].policy_version_hash,validation_hash:validation.validation_hash,decision,approval_hash:approvalHash,reviewer_id:reviewerId}),JSON.stringify({project_id:projectId,actor_id:reviewerId,execution_context:"SIMULATION",physical_effects:false})]);
      return approval;
    });
  }

  async approval(projectId: string, candidateId: string, validationId: string) { return this.approvalFrom(this.db, projectId, candidateId, validationId); }
  private validationQuery(where: string) { return `SELECT v.*,COALESCE((SELECT jsonb_agg(jsonb_build_object('gate_code',g.gate_code,'gate_version',g.gate_version,'status',g.status,'severity',g.severity,'reason_code',g.reason_code,'details',g.details,'evidence_reference',g.evidence_reference) ORDER BY g.gate_code) FROM public.control_controlled_policy_validation_gate_results g WHERE g.validation_id=v.id),'[]'::jsonb) gate_results FROM public.control_controlled_policy_validations v ${where}`; }
  private async validation(db: SqlExecutor, projectId: string, candidateId: string, validationId?: string) { const result = await db.query(this.validationQuery(`WHERE v.project_id=$1::uuid AND v.policy_version_candidate_id=$2::uuid${validationId ? " AND v.id=$3::uuid" : ""}`),validationId?[projectId,candidateId,validationId]:[projectId,candidateId]); return result.rows[0] ? mapValidation(result.rows[0]) : null; }
  private async approvalFrom(db: SqlExecutor, projectId: string, candidateId: string, validationId: string) { const result = await db.query("SELECT * FROM public.control_controlled_policy_approvals WHERE project_id=$1::uuid AND policy_version_candidate_id=$2::uuid AND validation_id=$3::uuid",[projectId,candidateId,validationId]); return result.rows[0] ? mapApproval(result.rows[0]) : null; }
  private async input(db: SqlExecutor, projectId: string, candidateId: string): Promise<ControlledPolicyValidationInput | null> { const result = await db.query(`SELECT c.project_id,c.id candidate_id,c.project_id candidate_project_id,c.policy_version_hash,c.configuration_snapshot,c.configuration_hash,c.strategy_type,c.strategy_schema_version,c.version_number,c.proposal_hash,c.assessment_hash,c.candidate_hash,c.provenance_snapshot,a.status assessment_status,c.status='CANDIDATE' candidate_immutable,FALSE operational_binding FROM public.control_controlled_policy_version_candidates c LEFT JOIN public.control_policy_promotion_assessments a ON a.id=c.promotion_assessment_id WHERE c.project_id=$1::uuid AND c.id=$2::uuid`,[projectId,candidateId]); return result.rows[0] as ControlledPolicyValidationInput | undefined ?? null; }
}
