import { sha256Canonical } from "@/lib/simulation/canonical";
import { buildControlledPolicyConfigurationHash, buildControlledPolicyVersionHash } from "@/lib/promotion/controlled-policy-version-materializer";
import { buildControlledPolicyApprovalHash } from "@/lib/promotion/controlled-policy-validation-engine";
import { CONTROLLED_DEPLOYMENT_PREPARATION_POLICY_VERSION, CONTROLLED_DEPLOYMENT_PREPARATION_SCHEMA_VERSION, OPERATIONAL_READINESS_ENGINE_VERSION, OPERATIONAL_READINESS_POLICY_VERSION, type OperationalReadinessGateResult, type OperationalReadinessStatus } from "@/lib/dto/controlled-deployment-preparation.dto";

export const OPERATIONAL_READINESS_GATES = ["GATE_M7_3_APPROVAL_VALID","GATE_POLICY_VERSION_IDENTITY_VALID","GATE_PREPARATION_PROVENANCE_COMPLETE","GATE_TARGET_SCOPE_VALID","GATE_TARGET_TOPOLOGY_EXISTS","GATE_TARGET_COMPATIBILITY_VALID","GATE_REQUIRED_RUNTIME_CAPABILITIES_DECLARED","GATE_SECURITY_BOUNDARY_VALID","GATE_NO_CONFLICTING_ACTIVE_BINDING","GATE_ROLLBACK_PRECONDITIONS_DEFINED","GATE_OBSERVABILITY_PRECONDITIONS_DEFINED","GATE_NO_DEPLOYMENT_EXECUTED"] as const;
const requiredCapabilities = ["strategy_evaluator","input_signal","output_channel","policy_schema"];
const gate = (gate_code: string, pass: boolean, reason_code: string, evidence_reference: Record<string, unknown>, error = false): OperationalReadinessGateResult => ({ gate_code, gate_version: "v1", status: pass ? "PASS" : error ? "ERROR" : "FAIL", severity: "BLOCKING", reason_code, details: {}, evidence_reference });

export interface DeploymentPreparationIdentityInput { project_id: string; policy_version_candidate_id: string; policy_version_hash: string; validation_hash: string; approval_hash: string; target_asset_id: string; }
export function buildControlledDeploymentPreparationHash(input: DeploymentPreparationIdentityInput) { return sha256Canonical({ project_id: input.project_id, policy_version_candidate_id: input.policy_version_candidate_id, policy_version_hash: input.policy_version_hash, validation_hash: input.validation_hash, approval_hash: input.approval_hash, target_asset_id: input.target_asset_id, target_scope_kind: "asset", preparation_policy_version: CONTROLLED_DEPLOYMENT_PREPARATION_POLICY_VERSION, preparation_schema_version: CONTROLLED_DEPLOYMENT_PREPARATION_SCHEMA_VERSION }); }

export interface OperationalReadinessInput extends DeploymentPreparationIdentityInput {
  validation_id: string; approval_id: string; approval_decision: string; validation_status: string;
  configuration_snapshot: any; configuration_hash: string; strategy_type: "proportional" | "threshold"; strategy_schema_version: number; version_number: number;
  proposal_hash: string; assessment_hash: string; candidate_hash: string; provenance_snapshot: Record<string, string>;
  approval_rationale: string; reviewer_id: string; stored_preparation_hash: string;
  target_project_id: string | null; target_status: string | null; target_asset_type: string | null; target_metadata: Record<string, any> | null;
  has_conflicting_active_binding: boolean; rollback_status: "NO_PRIOR_POLICY" | "INACTIVE_POLICY_AVAILABLE" | "MISSING";
  development_fallback_enabled: boolean; no_deployment_executed: boolean;
}

export function evaluateOperationalReadiness(input: OperationalReadinessInput) {
  const readiness = input.target_metadata?.control_readiness ?? {};
  const configurationHash = (() => { try { return buildControlledPolicyConfigurationHash(input.configuration_snapshot) === input.configuration_hash; } catch { return false; } })();
  const policyHash = (() => { try { return buildControlledPolicyVersionHash({ project_id: input.project_id, configuration_hash: input.configuration_hash, proposal_hash: input.proposal_hash, assessment_hash: input.assessment_hash, candidate_hash: input.candidate_hash, strategy_type: input.strategy_type, version_number: input.version_number }) === input.policy_version_hash; } catch { return false; } })();
  const approvalHash = (() => { try { return buildControlledPolicyApprovalHash({ policy_version_hash: input.policy_version_hash, validation_hash: input.validation_hash, decision: input.approval_decision as any, rationale: input.approval_rationale, reviewer_id: input.reviewer_id }) === input.approval_hash; } catch { return false; } })();
  const preparationHash = buildControlledDeploymentPreparationHash(input) === input.stored_preparation_hash;
  const provenance = [input.proposal_hash,input.assessment_hash,input.candidate_hash,input.provenance_snapshot?.recommendation_hash,input.provenance_snapshot?.review_hash,input.provenance_snapshot?.evaluation_hash,input.provenance_snapshot?.ranking_hash,input.validation_id,input.approval_id,input.validation_hash,input.approval_hash].every(Boolean) && preparationHash;
  const declaredCapabilities = Array.isArray(readiness.runtime_capabilities) && requiredCapabilities.every(capability => readiness.runtime_capabilities.includes(capability));
  const compatible = Array.isArray(readiness.supported_strategy_types) && readiness.supported_strategy_types.includes(input.strategy_type) && Array.isArray(readiness.supported_strategy_schema_versions) && readiness.supported_strategy_schema_versions.includes(input.strategy_schema_version);
  const observable = Boolean(readiness.observability?.telemetry && readiness.observability?.runtime_status && readiness.observability?.control_output && readiness.observability?.audit_path);
  const results = [
    gate("GATE_M7_3_APPROVAL_VALID", input.validation_status === "PASSED" && input.approval_decision === "APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION" && approvalHash, "M7_3_APPROVAL", { validation_id: input.validation_id, approval_id: input.approval_id }, true),
    gate("GATE_POLICY_VERSION_IDENTITY_VALID", configurationHash && policyHash, "POLICY_VERSION_IDENTITY", { policy_version_hash: input.policy_version_hash, configuration_hash: input.configuration_hash }, true),
    gate("GATE_PREPARATION_PROVENANCE_COMPLETE", provenance, "PREPARATION_PROVENANCE", { preparation_hash: input.stored_preparation_hash }, true),
    gate("GATE_TARGET_SCOPE_VALID", input.target_project_id === input.project_id, "TARGET_PROJECT_SCOPE", { target_asset_id: input.target_asset_id }, input.target_project_id !== input.project_id),
    gate("GATE_TARGET_TOPOLOGY_EXISTS", Boolean(input.target_asset_type && ["active","online"].includes(input.target_status ?? "")), "TARGET_TOPOLOGY", { target_asset_id: input.target_asset_id, target_status: input.target_status }),
    gate("GATE_TARGET_COMPATIBILITY_VALID", compatible, "TARGET_COMPATIBILITY", { strategy_type: input.strategy_type, strategy_schema_version: input.strategy_schema_version }),
    gate("GATE_REQUIRED_RUNTIME_CAPABILITIES_DECLARED", declaredCapabilities, "RUNTIME_CAPABILITIES", { required_capabilities: requiredCapabilities }),
    gate("GATE_SECURITY_BOUNDARY_VALID", Boolean(readiness.security_boundary?.governed_control) && !input.development_fallback_enabled, "SECURITY_BOUNDARY", { development_fallback_enabled: input.development_fallback_enabled }, true),
    gate("GATE_NO_CONFLICTING_ACTIVE_BINDING", !input.has_conflicting_active_binding, "CONFLICTING_ACTIVE_BINDING", { target_asset_id: input.target_asset_id }, input.has_conflicting_active_binding),
    gate("GATE_ROLLBACK_PRECONDITIONS_DEFINED", input.rollback_status !== "MISSING", "ROLLBACK_PRECONDITIONS", { rollback_status: input.rollback_status }),
    gate("GATE_OBSERVABILITY_PRECONDITIONS_DEFINED", observable, "OBSERVABILITY_PRECONDITIONS", { target_asset_id: input.target_asset_id }),
    gate("GATE_NO_DEPLOYMENT_EXECUTED", input.no_deployment_executed, "NO_DEPLOYMENT_EXECUTED", { physical_effects: false }, true),
  ].sort((left, right) => left.gate_code.localeCompare(right.gate_code));
  const status: OperationalReadinessStatus = results.some(result => result.status === "ERROR") ? "BLOCKED" : results.some(result => result.status === "FAIL") ? "FAILED" : "PASSED";
  return { results, status, readiness_hash: sha256Canonical({ preparation_hash: input.stored_preparation_hash, readiness_policy_version: OPERATIONAL_READINESS_POLICY_VERSION, readiness_engine_version: OPERATIONAL_READINESS_ENGINE_VERSION, schema_version: 1, gate_results: results }) };
}
