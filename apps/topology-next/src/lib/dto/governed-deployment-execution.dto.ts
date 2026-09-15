export const GOVERNED_DEPLOYMENT_EXECUTION_POLICY_VERSION = "governed-deployment-execution:v1";
export const GOVERNED_DEPLOYMENT_EXECUTION_ENGINE_VERSION = "governed-deployment-execution-engine:v1";
export const GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION = "governed-deployment-execution-schema:v1";

export type GovernedDeploymentExecutionStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED" | "BLOCKED" | "ROLLBACK_PENDING" | "ROLLED_BACK" | "ROLLBACK_FAILED";
export type GovernedDeploymentRollbackStatus = "NOT_REQUIRED" | "PENDING" | "SUCCEEDED" | "FAILED";
export type GovernedDeploymentDeliveryMode = "STAGE" | "FAIL_BEFORE_STAGE" | "STAGE_THEN_FAIL";

export interface GovernedDeploymentExecution {
  id: string;
  project_id: string;
  policy_version_candidate_id: string;
  governed_deployment_intent_id: string;
  target_asset_id: string;
  policy_version_hash: string;
  intent_hash: string;
  execution_hash: string;
  execution_policy_version: string;
  execution_engine_version: string;
  execution_schema_version: string;
  delivery_channel: "DATABASE_STAGING";
  status: GovernedDeploymentExecutionStatus;
  rollback_status: GovernedDeploymentRollbackStatus;
  result_hash: string | null;
  created_by: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  physical_effects_allowed: false;
}

export interface GovernedDeploymentExecutionAttempt {
  id: string;
  execution_id: string;
  attempt_number: number;
  delivery_channel: "DATABASE_STAGING";
  target_asset_id: string;
  request_hash: string;
  result_classification: "SUCCEEDED" | "FAILED" | "PARTIALLY_STAGED" | "BLOCKED";
  acknowledgement: Record<string, unknown>;
  error_class: string | null;
  created_at: string;
}

export interface GovernedDeploymentExecutionResult {
  execution_id: string;
  result_hash: string;
  delivery_result: Record<string, unknown>;
  rollback_result: Record<string, unknown>;
  created_at: string;
}
