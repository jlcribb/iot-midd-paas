export const CONTROLLED_DEPLOYMENT_PREPARATION_POLICY_VERSION = "controlled-deployment-preparation:v1";
export const CONTROLLED_DEPLOYMENT_PREPARATION_SCHEMA_VERSION = "controlled-deployment-preparation-schema:v1";
export const OPERATIONAL_READINESS_POLICY_VERSION = "operational-readiness:v1";
export const OPERATIONAL_READINESS_ENGINE_VERSION = "operational-readiness-engine:v1";

export type OperationalReadinessStatus = "PENDING" | "PASSED" | "FAILED" | "BLOCKED";
export type OperationalReadinessGateStatus = "PASS" | "FAIL" | "ERROR";

export interface ControlledDeploymentPreparation {
  id: string; project_id: string; policy_version_candidate_id: string; target_asset_id: string;
  target_scope_kind: "asset"; policy_version_hash: string; validation_id: string; validation_hash: string;
  approval_id: string; approval_hash: string; strategy_type: "proportional" | "threshold";
  strategy_schema_version: number; version_number: number; preparation_hash: string;
  preparation_policy_version: string; preparation_schema_version: string; status: "CREATED";
  created_by: string; created_at: string; physical_effects_allowed: false;
}

export interface OperationalReadinessGateResult {
  gate_code: string; gate_version: string; status: OperationalReadinessGateStatus; severity: "BLOCKING";
  reason_code: string; details: Record<string, unknown>; evidence_reference: Record<string, unknown>;
}

export interface OperationalReadinessAssessment {
  id: string; project_id: string; deployment_preparation_id: string; preparation_hash: string;
  readiness_hash: string; readiness_policy_version: string; readiness_engine_version: string;
  status: OperationalReadinessStatus; blocking_pass_count: number; blocking_fail_count: number;
  warning_count: number; gate_results: OperationalReadinessGateResult[]; created_by: string;
  created_at: string; physical_effects_allowed: false;
}
