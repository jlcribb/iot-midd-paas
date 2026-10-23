import type { PoolClient } from "pg";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import {
  canonicalDecisionJson,
  decisionProblemHash,
  preferenceProfileHash,
  riskProfileHash,
  type DecisionProblemDraftInput,
  type PreferenceDraftInput,
  type RiskDraftInput,
} from "@/lib/gdss/decision";
import { validationHash } from "@/lib/gdss/validation";
import { DecisionError } from "@/lib/gdss/decision/diagnostics";

type EntityType = "DECISION_PROBLEM" | "PREFERENCE_PROFILE" | "RISK_PROFILE";
type IdentityKind = "problem" | "preference" | "risk";
const actorId = (actor: ControlActor) => actor.actor_id ?? actor.user_id;
const actorKind = (actor: ControlActor) => actor.auth_provider?.toLowerCase() === "ai" || /(^|\s)ai[:_-]/.test(`${actor.actor_id ?? ""} ${actor.user_id}`.toLowerCase()) ? "AI" : "HUMAN";
const tables = {
  problem: { identity: "gdss_decision_problem_identity", version: "gdss_decision_problem_version", identityColumn: "problem_identity_id" },
  preference: { identity: "gdss_decision_preference_identity", version: "gdss_decision_preference_version", identityColumn: "preference_identity_id" },
  risk: { identity: "gdss_decision_risk_identity", version: "gdss_decision_risk_version", identityColumn: "risk_identity_id" },
} as const;

export class GdssDecisionRepository {
  constructor(private readonly transaction: TransactionRunner = withTransaction) {}

  private run<T>(work:(tx:PoolClient)=>Promise<T>):Promise<T>{
    return this.transaction(work).catch((error:unknown)=>{
      if(error instanceof DecisionError)throw error;
      const message=error instanceof Error?error.message:String(error);
      const codes=["RESOURCE_LIMIT_EXCEEDED","CROSS_PROJECT_DECISION_REFERENCE","PREFERENCE_REQUIRED","PREFERENCE_PROFILE_MISMATCH","RISK_UNACCEPTABLE","SOD_VIOLATION","AI_AUTHORITY_FORBIDDEN","DECISION_PROBLEM_FROZEN","IDEMPOTENCY_CONFLICT","INVALID_DECISION_LIFECYCLE","CLAIM_NOT_CURRENT"] as const;
      const code=codes.find(candidate=>message.includes(candidate))??"DECISION_INPUT_NOT_CURRENT";
      throw new DecisionError(code);
    });
  }

  private async audit(tx: PoolClient, actor: ControlActor, projectId: string, entityType: EntityType, entityId: string, eventType: string, fromStatus: string | null, toStatus: string | null, reason: string, idempotencyKey: string, metadata: unknown = {}) {
    const content = { projectId, entityType, entityId, eventType, fromStatus, toStatus, actor: actorId(actor), reason, metadata };
    const eventHash = validationHash("midd:gdss:decision-audit-event:v1", content);
    const prior = (await tx.query("SELECT * FROM gdss_decision_audit_event WHERE project_id=$1 AND idempotency_key=$2", [projectId, idempotencyKey])).rows[0];
    if (prior) {
      if (prior.event_hash !== eventHash) throw new DecisionError("IDEMPOTENCY_CONFLICT");
      return prior;
    }
    const sequence = Number((await tx.query("SELECT coalesce(max(sequence),0)+1 n FROM gdss_decision_audit_event WHERE entity_type=$1 AND entity_id=$2", [entityType, entityId])).rows[0].n);
    return (await tx.query(
      `INSERT INTO gdss_decision_audit_event(project_id,entity_type,entity_id,sequence,event_type,from_status,to_status,actor,actor_kind,reason,idempotency_key,event_hash,metadata)
       VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb) RETURNING *`,
      [projectId, entityType, entityId, sequence, eventType, fromStatus, toStatus, actorId(actor), actorKind(actor), reason, idempotencyKey, eventHash, JSON.stringify(metadata)],
    )).rows[0];
  }

  createIdentity(actor: ControlActor, projectId: string, kind: IdentityKind, canonicalKey: string, idempotencyKey: string) {
    return this.run(async (tx) => {
      const table = tables[kind].identity;
      await tx.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", [`${table}:${projectId}:${canonicalKey}`]);
      const byKey = (await tx.query(`SELECT * FROM ${table} WHERE project_id=$1 AND canonical_key=$2`, [projectId, canonicalKey])).rows[0];
      const byIdempotency = (await tx.query(`SELECT * FROM ${table} WHERE project_id=$1 AND idempotency_key=$2`, [projectId, idempotencyKey])).rows[0];
      if (byIdempotency && byIdempotency.canonical_key !== canonicalKey) throw new DecisionError("IDEMPOTENCY_CONFLICT");
      if (byKey) return byKey;
      return (await tx.query(`INSERT INTO ${table}(project_id,canonical_key,idempotency_key,created_by)VALUES($1,$2,$3,$4)RETURNING *`, [projectId, canonicalKey, idempotencyKey, actorId(actor)])).rows[0];
    });
  }

  createPreferenceDraft(actor: ControlActor, projectId: string, input: PreferenceDraftInput) {
    return this.run(async (tx) => {
      const hash = preferenceProfileHash(input);
      await tx.query("SELECT id FROM gdss_decision_preference_identity WHERE id=$1 AND project_id=$2 FOR UPDATE", [input.identityId, projectId]);
      const prior = (await tx.query("SELECT * FROM gdss_decision_preference_version WHERE project_id=$1 AND (content_hash=$2 OR idempotency_key=$3)", [projectId, hash, input.idempotencyKey])).rows[0];
      if (prior) { if (prior.content_hash !== hash || prior.preference_identity_id !== input.identityId) throw new DecisionError("IDEMPOTENCY_CONFLICT"); return prior; }
      const version = Number((await tx.query("SELECT coalesce(max(version_number),0)+1 n FROM gdss_decision_preference_version WHERE preference_identity_id=$1", [input.identityId])).rows[0].n);
      const row = (await tx.query(
        `INSERT INTO gdss_decision_preference_version(project_id,preference_identity_id,version_number,predecessor_version_id,semantic_version,mode,scope,canonical_content,content_hash,idempotency_key,authored_by)
         VALUES($1,$2,$3,$4,'GDSS_DECISION_PREFERENCE_V1',$5,$6::jsonb,$7,$8,$9,$10) RETURNING *`,
        [projectId,input.identityId,version,input.predecessorVersionId??null,input.mode,JSON.stringify(input.scope),canonicalDecisionJson(input),hash,input.idempotencyKey,actorId(actor)],
      )).rows[0];
      for (const item of input.items) await tx.query("INSERT INTO gdss_decision_preference_item(project_id,preference_version_id,objective_key,ordinal_priority,weight)VALUES($1,$2,$3,$4,$5)", [projectId,row.id,item.objectiveKey,item.ordinalPriority??null,item.weight??null]);
      await this.audit(tx,actor,projectId,"PREFERENCE_PROFILE",row.id,"CREATE",null,"DRAFT","create preference draft",`${input.idempotencyKey}:event`,{content_hash:hash});
      return row;
    });
  }

  createRiskDraft(actor: ControlActor, projectId: string, input: RiskDraftInput) {
    return this.run(async (tx) => {
      const hash = riskProfileHash(input);
      await tx.query("SELECT id FROM gdss_decision_risk_identity WHERE id=$1 AND project_id=$2 FOR UPDATE", [input.identityId, projectId]);
      const prior = (await tx.query("SELECT * FROM gdss_decision_risk_version WHERE project_id=$1 AND (content_hash=$2 OR idempotency_key=$3)", [projectId,hash,input.idempotencyKey])).rows[0];
      if (prior) { if (prior.content_hash !== hash || prior.risk_identity_id !== input.identityId) throw new DecisionError("IDEMPOTENCY_CONFLICT"); return prior; }
      const version = Number((await tx.query("SELECT coalesce(max(version_number),0)+1 n FROM gdss_decision_risk_version WHERE risk_identity_id=$1", [input.identityId])).rows[0].n);
      const row = (await tx.query(
        `INSERT INTO gdss_decision_risk_version(project_id,risk_identity_id,version_number,predecessor_version_id,semantic_version,scope,canonical_content,content_hash,idempotency_key,authored_by)
         VALUES($1,$2,$3,$4,'GDSS_DECISION_RISK_V1',$5::jsonb,$6,$7,$8,$9) RETURNING *`,
        [projectId,input.identityId,version,input.predecessorVersionId??null,JSON.stringify(input.scope),canonicalDecisionJson(input),hash,input.idempotencyKey,actorId(actor)],
      )).rows[0];
      for (const item of input.dimensions) await tx.query(
        `INSERT INTO gdss_decision_risk_dimension(project_id,risk_version_id,ordinal,dimension_key,source,severity,likelihood_knowledge_state,reversibility,recoverability,uncertainty,state,unknown_handling,acceptance_rule,scope)
         VALUES($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10,$11,$12,$13,$14::jsonb)`,
        [projectId,row.id,item.ordinal,item.key,JSON.stringify(item.source),item.severity,item.likelihoodKnowledgeState,item.reversibility,item.recoverability,item.uncertainty,item.state,item.unknownHandling,item.acceptanceRule,JSON.stringify(item.scope)],
      );
      await this.audit(tx,actor,projectId,"RISK_PROFILE",row.id,"CREATE",null,"DRAFT","create risk draft",`${input.idempotencyKey}:event`,{content_hash:hash});
      return row;
    });
  }

  updatePreferenceDraft(actor:ControlActor,projectId:string,id:string,input:PreferenceDraftInput){
    return this.run(async tx=>{
      const row=(await tx.query("SELECT * FROM gdss_decision_preference_version WHERE id=$1 AND project_id=$2 FOR UPDATE",[id,projectId])).rows[0];
      if(!row)throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
      if(row.status!=="DRAFT")throw new DecisionError("DECISION_PROBLEM_FROZEN");
      if(row.preference_identity_id!==input.identityId)throw new DecisionError("PREFERENCE_PROFILE_MISMATCH");
      const hash=preferenceProfileHash(input),collision=(await tx.query("SELECT id,content_hash FROM gdss_decision_preference_version WHERE project_id=$1 AND id<>$2 AND (content_hash=$3 OR idempotency_key=$4)",[projectId,id,hash,input.idempotencyKey])).rows[0];
      if(collision)throw new DecisionError("IDEMPOTENCY_CONFLICT");
      await tx.query("DELETE FROM gdss_decision_preference_item WHERE preference_version_id=$1",[id]);
      const updated=(await tx.query("UPDATE gdss_decision_preference_version SET mode=$2,scope=$3::jsonb,canonical_content=$4,content_hash=$5,idempotency_key=$6,updated_at=clock_timestamp() WHERE id=$1 RETURNING *",[id,input.mode,JSON.stringify(input.scope),canonicalDecisionJson(input),hash,input.idempotencyKey])).rows[0];
      for(const item of input.items)await tx.query("INSERT INTO gdss_decision_preference_item(project_id,preference_version_id,objective_key,ordinal_priority,weight)VALUES($1,$2,$3,$4,$5)",[projectId,id,item.objectiveKey,item.ordinalPriority??null,item.weight??null]);
      await this.audit(tx,actor,projectId,"PREFERENCE_PROFILE",id,"UPDATE_DRAFT","DRAFT","DRAFT","update preference draft",`${input.idempotencyKey}:event`,{content_hash:hash});
      return updated;
    });
  }

  updateRiskDraft(actor:ControlActor,projectId:string,id:string,input:RiskDraftInput){
    return this.run(async tx=>{
      const row=(await tx.query("SELECT * FROM gdss_decision_risk_version WHERE id=$1 AND project_id=$2 FOR UPDATE",[id,projectId])).rows[0];
      if(!row)throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
      if(row.status!=="DRAFT")throw new DecisionError("DECISION_PROBLEM_FROZEN");
      if(row.risk_identity_id!==input.identityId)throw new DecisionError("DECISION_INPUT_NOT_CURRENT");
      const hash=riskProfileHash(input),collision=(await tx.query("SELECT id FROM gdss_decision_risk_version WHERE project_id=$1 AND id<>$2 AND (content_hash=$3 OR idempotency_key=$4)",[projectId,id,hash,input.idempotencyKey])).rows[0];
      if(collision)throw new DecisionError("IDEMPOTENCY_CONFLICT");
      await tx.query("DELETE FROM gdss_decision_risk_dimension WHERE risk_version_id=$1",[id]);
      const updated=(await tx.query("UPDATE gdss_decision_risk_version SET scope=$2::jsonb,canonical_content=$3,content_hash=$4,idempotency_key=$5,updated_at=clock_timestamp() WHERE id=$1 RETURNING *",[id,JSON.stringify(input.scope),canonicalDecisionJson(input),hash,input.idempotencyKey])).rows[0];
      for(const item of input.dimensions)await tx.query(`INSERT INTO gdss_decision_risk_dimension(project_id,risk_version_id,ordinal,dimension_key,source,severity,likelihood_knowledge_state,reversibility,recoverability,uncertainty,state,unknown_handling,acceptance_rule,scope)VALUES($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10,$11,$12,$13,$14::jsonb)`,[projectId,id,item.ordinal,item.key,JSON.stringify(item.source),item.severity,item.likelihoodKnowledgeState,item.reversibility,item.recoverability,item.uncertainty,item.state,item.unknownHandling,item.acceptanceRule,JSON.stringify(item.scope)]);
      await this.audit(tx,actor,projectId,"RISK_PROFILE",id,"UPDATE_DRAFT","DRAFT","DRAFT","update risk draft",`${input.idempotencyKey}:event`,{content_hash:hash});
      return updated;
    });
  }

  async getEvidenceFacts(projectId: string, binding: DecisionProblemDraftInput["context"]["evidenceBindings"][number]) {
    return this.run(async (tx) => {
      const row = (await tx.query(
        `SELECT e.*,c.state capability_state,c.content_hash capability_hash,c.domain_scope,c.protocol_family,c.metric_profile,c.baseline_profile,c.uncertainty_profile,c.evidence_period_start,c.evidence_period_end,
                q.status claim_status,q.content_hash claim_hash,q.claim_scope,q.valid_through_epoch_micros,
                EXISTS(SELECT 1 FROM gdss_predictive_claim_revocation x WHERE x.claim_id=q.id) revoked,
                EXISTS(SELECT 1 FROM gdss_revalidation_trigger_assessment t WHERE t.claim_id=q.id AND t.state IN('DETECTED','REVIEW_REQUIRED','REVALIDATION_REQUIRED') AND NOT EXISTS(SELECT 1 FROM gdss_revalidation_trigger_assessment s WHERE s.predecessor_trigger_id=t.id)) unresolved
         FROM gdss_predictive_evidence_set e JOIN gdss_capability_assessment c ON c.id=$3 AND c.evidence_set_id=e.id
         JOIN gdss_predictive_claim_version q ON q.id=$4 AND q.capability_assessment_id=c.id AND q.evidence_set_id=e.id
         WHERE e.id=$2 AND e.project_id=$1`,
        [projectId,binding.evidenceSetId,binding.capabilityAssessmentId,binding.predictiveClaimId],
      )).rows[0];
      if (!row || row.content_hash!==binding.evidenceSetHash || row.capability_hash!==binding.capabilityAssessmentHash || row.claim_hash!==binding.predictiveClaimHash || row.validity_domain_version_id!==binding.validityDomainVersionId) throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
      const now = BigInt(Date.now())*1000n;
      const currentness = row.revoked ? "REVOKED" : row.claim_status!=="AUTHORIZED" ? row.claim_status : row.unresolved ? "STALE" : row.valid_through_epoch_micros!==null && BigInt(row.valid_through_epoch_micros)<now ? "EXPIRED_REVIEW_REQUIRED" : "AUTHORIZED_CURRENT";
      const capabilityScope = {
        modelVersionId: row.model_version_id, modelContentHash: row.model_hash, targetKey: row.target_key, horizonKey: row.horizon_key,
        validityDomainVersionId: row.validity_domain_version_id, protocolFamily: row.protocol_family,
        metricProfile: row.metric_profile, baselineProfile: row.baseline_profile, uncertaintyProfile: row.uncertainty_profile,
        evidencePeriod: {startEpochMicros:String(row.evidence_period_start),endEpochMicros:String(row.evidence_period_end)}, domainConstraints: row.domain_scope,
      };
      return { evidenceScope: capabilityScope, capabilityScope, claimScope: row.claim_scope, capabilityState: row.capability_state, claimCurrentness: currentness };
    });
  }

  createProblemDraft(actor: ControlActor, projectId: string, input: DecisionProblemDraftInput, eligibility: {eligibility:string;reviewRequired:boolean}) {
    return this.run(async (tx) => {
      const hash=decisionProblemHash(input);
      await tx.query("SELECT id FROM gdss_decision_problem_identity WHERE id=$1 AND project_id=$2 FOR UPDATE",[input.identityId,projectId]);
      const prior=(await tx.query("SELECT * FROM gdss_decision_problem_version WHERE project_id=$1 AND (decision_problem_hash=$2 OR idempotency_key=$3)",[projectId,hash,input.idempotencyKey])).rows[0];
      if(prior){if(prior.decision_problem_hash!==hash||prior.problem_identity_id!==input.identityId)throw new DecisionError("IDEMPOTENCY_CONFLICT");return prior;}
      const version=Number((await tx.query("SELECT coalesce(max(version_number),0)+1 n FROM gdss_decision_problem_version WHERE problem_identity_id=$1",[input.identityId])).rows[0].n);
      const row=(await tx.query(
        `INSERT INTO gdss_decision_problem_version(project_id,problem_identity_id,version_number,predecessor_version_id,semantic_version,context_snapshot,decision_scope,decision_horizon,target_variables,preference_profile_version_id,preference_profile_hash,risk_profile_version_id,risk_profile_hash,resource_profile,allowed_alternative_provenance,allowed_scenario_methods,recommendation_eligibility,decision_support_review_required,canonical_content,decision_problem_hash,idempotency_key,authored_by)
         VALUES($1,$2,$3,$4,'GDSS_DECISION_PROBLEM_V1',$5::jsonb,$6::jsonb,$7::jsonb,$8,$9,$10,$11,$12,'GDSS_DECISION_LIMITS_V1',$13,$14,$15,$16,$17,$18,$19,$20)RETURNING *`,
        [projectId,input.identityId,version,input.predecessorVersionId??null,JSON.stringify(input.context),JSON.stringify(input.context.scope),JSON.stringify(input.context.decisionHorizon),input.context.targetVariables,input.preferenceProfileVersionId,input.preferenceProfileHash,input.riskProfileVersionId,input.riskProfileHash,input.allowedAlternativeProvenance,input.allowedScenarioMethods,eligibility.eligibility,eligibility.reviewRequired,canonicalDecisionJson(input),hash,input.idempotencyKey,actorId(actor)],
      )).rows[0];
      for(const [ordinal,item] of input.context.modelBindings.entries())await tx.query("INSERT INTO gdss_decision_problem_model_ref(project_id,problem_version_id,ordinal,model_version_id,model_content_hash,binding_version_id,binding_content_hash)VALUES($1,$2,$3,$4,$5,$6,$7)",[projectId,row.id,ordinal,item.modelVersionId,item.modelContentHash,item.bindingVersionId,item.bindingContentHash]);
      for(const [ordinal,item] of input.context.evidenceBindings.entries())await tx.query("INSERT INTO gdss_decision_problem_evidence_ref(project_id,problem_version_id,ordinal,evidence_set_id,evidence_set_hash,capability_assessment_id,capability_assessment_hash,predictive_claim_id,predictive_claim_hash,validity_domain_version_id,validity_domain_hash)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",[projectId,row.id,ordinal,item.evidenceSetId,item.evidenceSetHash,item.capabilityAssessmentId,item.capabilityAssessmentHash,item.predictiveClaimId,item.predictiveClaimHash,item.validityDomainVersionId,item.validityDomainHash]);
      for(const item of input.objectives)await tx.query(`INSERT INTO gdss_decision_objective(project_id,problem_version_id,objective_key,direction,quantity_key,unit,target,horizon_key,criterion_version_id,criterion_content_hash,aspiration_bounds,acceptance_bounds,required,ordinal)VALUES($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8,$9,$10,$11::jsonb,$12::jsonb,$13,$14)`,[projectId,row.id,item.key,item.direction,item.quantityKey,JSON.stringify(item.unit),JSON.stringify(item.target),item.horizonKey,item.criterionVersionId,item.criterionContentHash,JSON.stringify(item.aspirationBounds),JSON.stringify(item.acceptanceBounds),item.required,item.ordinal]);
      for(const item of input.constraints)await tx.query(`INSERT INTO gdss_decision_constraint(project_id,problem_version_id,constraint_key,constraint_type,scope,predicate_method,unit,threshold,required_inputs,missing_semantics,provenance,explanation,ordinal)VALUES($1,$2,$3,$4,$5::jsonb,$6,$7::jsonb,$8::jsonb,$9::jsonb,$10,$11::jsonb,$12,$13)`,[projectId,row.id,item.key,item.type,JSON.stringify(item.scope),item.predicateMethod,item.unit?JSON.stringify(item.unit):null,JSON.stringify(item.threshold),JSON.stringify(item.requiredInputs),item.missingSemantics,JSON.stringify(item.provenance),item.explanation,item.ordinal]);
      await this.audit(tx,actor,projectId,"DECISION_PROBLEM",row.id,"CREATE",null,"DRAFT","create decision problem draft",`${input.idempotencyKey}:event`,{decision_problem_hash:hash});
      return row;
    });
  }

  updateProblemDraft(actor:ControlActor,projectId:string,id:string,input:DecisionProblemDraftInput,eligibility:{eligibility:string;reviewRequired:boolean}){
    return this.run(async tx=>{
      const row=(await tx.query("SELECT * FROM gdss_decision_problem_version WHERE id=$1 AND project_id=$2 FOR UPDATE",[id,projectId])).rows[0];
      if(!row)throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
      if(row.status!=="DRAFT")throw new DecisionError("DECISION_PROBLEM_FROZEN");
      if(row.problem_identity_id!==input.identityId)throw new DecisionError("DECISION_INPUT_NOT_CURRENT");
      const hash=decisionProblemHash(input),collision=(await tx.query("SELECT id FROM gdss_decision_problem_version WHERE project_id=$1 AND id<>$2 AND (decision_problem_hash=$3 OR idempotency_key=$4)",[projectId,id,hash,input.idempotencyKey])).rows[0];
      if(collision)throw new DecisionError("IDEMPOTENCY_CONFLICT");
      await tx.query("DELETE FROM gdss_decision_constraint WHERE problem_version_id=$1",[id]);
      await tx.query("DELETE FROM gdss_decision_objective WHERE problem_version_id=$1",[id]);
      await tx.query("DELETE FROM gdss_decision_problem_evidence_ref WHERE problem_version_id=$1",[id]);
      await tx.query("DELETE FROM gdss_decision_problem_model_ref WHERE problem_version_id=$1",[id]);
      const updated=(await tx.query(`UPDATE gdss_decision_problem_version SET context_snapshot=$2::jsonb,decision_scope=$3::jsonb,decision_horizon=$4::jsonb,target_variables=$5,preference_profile_version_id=$6,preference_profile_hash=$7,risk_profile_version_id=$8,risk_profile_hash=$9,allowed_alternative_provenance=$10,allowed_scenario_methods=$11,recommendation_eligibility=$12,decision_support_review_required=$13,canonical_content=$14,decision_problem_hash=$15,idempotency_key=$16,updated_at=clock_timestamp() WHERE id=$1 RETURNING *`,[id,JSON.stringify(input.context),JSON.stringify(input.context.scope),JSON.stringify(input.context.decisionHorizon),input.context.targetVariables,input.preferenceProfileVersionId,input.preferenceProfileHash,input.riskProfileVersionId,input.riskProfileHash,input.allowedAlternativeProvenance,input.allowedScenarioMethods,eligibility.eligibility,eligibility.reviewRequired,canonicalDecisionJson(input),hash,input.idempotencyKey])).rows[0];
      for(const [ordinal,item] of input.context.modelBindings.entries())await tx.query("INSERT INTO gdss_decision_problem_model_ref(project_id,problem_version_id,ordinal,model_version_id,model_content_hash,binding_version_id,binding_content_hash)VALUES($1,$2,$3,$4,$5,$6,$7)",[projectId,id,ordinal,item.modelVersionId,item.modelContentHash,item.bindingVersionId,item.bindingContentHash]);
      for(const [ordinal,item] of input.context.evidenceBindings.entries())await tx.query("INSERT INTO gdss_decision_problem_evidence_ref(project_id,problem_version_id,ordinal,evidence_set_id,evidence_set_hash,capability_assessment_id,capability_assessment_hash,predictive_claim_id,predictive_claim_hash,validity_domain_version_id,validity_domain_hash)VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",[projectId,id,ordinal,item.evidenceSetId,item.evidenceSetHash,item.capabilityAssessmentId,item.capabilityAssessmentHash,item.predictiveClaimId,item.predictiveClaimHash,item.validityDomainVersionId,item.validityDomainHash]);
      for(const item of input.objectives)await tx.query(`INSERT INTO gdss_decision_objective(project_id,problem_version_id,objective_key,direction,quantity_key,unit,target,horizon_key,criterion_version_id,criterion_content_hash,aspiration_bounds,acceptance_bounds,required,ordinal)VALUES($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8,$9,$10,$11::jsonb,$12::jsonb,$13,$14)`,[projectId,id,item.key,item.direction,item.quantityKey,JSON.stringify(item.unit),JSON.stringify(item.target),item.horizonKey,item.criterionVersionId,item.criterionContentHash,JSON.stringify(item.aspirationBounds),JSON.stringify(item.acceptanceBounds),item.required,item.ordinal]);
      for(const item of input.constraints)await tx.query(`INSERT INTO gdss_decision_constraint(project_id,problem_version_id,constraint_key,constraint_type,scope,predicate_method,unit,threshold,required_inputs,missing_semantics,provenance,explanation,ordinal)VALUES($1,$2,$3,$4,$5::jsonb,$6,$7::jsonb,$8::jsonb,$9::jsonb,$10,$11::jsonb,$12,$13)`,[projectId,id,item.key,item.type,JSON.stringify(item.scope),item.predicateMethod,item.unit?JSON.stringify(item.unit):null,JSON.stringify(item.threshold),JSON.stringify(item.requiredInputs),item.missingSemantics,JSON.stringify(item.provenance),item.explanation,item.ordinal]);
      await this.audit(tx,actor,projectId,"DECISION_PROBLEM",id,"UPDATE_DRAFT","DRAFT","DRAFT","update decision problem draft",`${input.idempotencyKey}:event`,{decision_problem_hash:hash});
      return updated;
    });
  }

  getVersion(projectId:string,kind:IdentityKind,id:string){const table=tables[kind].version;return this.run(async tx=>(await tx.query(`SELECT * FROM ${table} WHERE id=$1 AND project_id=$2`,[id,projectId])).rows[0]);}

  transition(actor:ControlActor,projectId:string,kind:IdentityKind,id:string,toStatus:"REVIEW_REQUIRED"|"SEALED"|"INVALIDATED",reason:string,idempotencyKey:string,expectedHash?:string,sodExceptionReason?:string){
    return this.run(async tx=>{
      const table=tables[kind].version,entityType:EntityType=kind==="problem"?"DECISION_PROBLEM":kind==="preference"?"PREFERENCE_PROFILE":"RISK_PROFILE",hashColumn=kind==="problem"?"decision_problem_hash":"content_hash";
      const row=(await tx.query(`SELECT * FROM ${table} WHERE id=$1 AND project_id=$2 FOR UPDATE`,[id,projectId])).rows[0];
      if(!row)throw new DecisionError("CROSS_PROJECT_DECISION_REFERENCE");
      const replay=(await tx.query("SELECT * FROM gdss_decision_audit_event WHERE project_id=$1 AND idempotency_key=$2",[projectId,idempotencyKey])).rows[0];
      if(replay){if(replay.entity_type!==entityType||replay.entity_id!==id||replay.to_status!==toStatus||replay.reason!==reason)throw new DecisionError("IDEMPOTENCY_CONFLICT");return row;}
      if(expectedHash&&row[hashColumn]!==expectedHash)throw new DecisionError("DECISION_INPUT_NOT_CURRENT");
      const allowed=(row.status==="DRAFT"&&(toStatus==="REVIEW_REQUIRED"||toStatus==="INVALIDATED"))||(row.status==="REVIEW_REQUIRED"&&(toStatus==="SEALED"||toStatus==="INVALIDATED"));
      if(!allowed)throw new DecisionError("INVALID_DECISION_LIFECYCLE");
      if(toStatus==="SEALED"&&row.authored_by===actorId(actor)&&!sodExceptionReason)throw new DecisionError("SOD_VIOLATION");
      if(toStatus==="SEALED"&&sodExceptionReason)await this.audit(tx,actor,projectId,entityType,id,"SOD_EXCEPTION",row.status,row.status,sodExceptionReason,`${idempotencyKey}:sod`,{sod_exception:true});
      await this.audit(tx,actor,projectId,entityType,id,toStatus==="REVIEW_REQUIRED"?"SUBMIT_REVIEW":toStatus==="SEALED"?"SEAL":"INVALIDATE",row.status,toStatus,reason,idempotencyKey,{sod_exception:Boolean(sodExceptionReason),sod_exception_reason:sodExceptionReason??null});
      return (await tx.query(`UPDATE ${table} SET status=$2,updated_at=clock_timestamp() WHERE id=$1 RETURNING *`,[id,toStatus])).rows[0];
    });
  }

  recordAiDenial(actor:ControlActor,projectId:string,kind:IdentityKind,id:string,reason:string,idempotencyKey:string){
    return this.run(async tx=>this.audit(tx,actor,projectId,kind==="problem"?"DECISION_PROBLEM":kind==="preference"?"PREFERENCE_PROFILE":"RISK_PROFILE",id,"AI_AUTHORITY_DENIAL",null,null,reason,idempotencyKey));
  }
}
