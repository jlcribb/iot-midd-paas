import { sha256Canonical } from "@/lib/simulation/canonical";
import {
  GOVERNED_DEPLOYMENT_EXECUTION_ENGINE_VERSION,
  GOVERNED_DEPLOYMENT_EXECUTION_POLICY_VERSION,
  GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION,
} from "@/lib/dto/governed-deployment-execution.dto";

export function buildGovernedDeploymentExecutionHash(input: { intent_hash: string; policy_version_hash: string; target_asset_id: string }) {
  return sha256Canonical({
    deployment_intent_hash: input.intent_hash,
    policy_version_hash: input.policy_version_hash,
    target_scope_kind: "asset",
    target_asset_id: input.target_asset_id,
    delivery_channel: "DATABASE_STAGING",
    execution_policy_version: GOVERNED_DEPLOYMENT_EXECUTION_POLICY_VERSION,
    execution_engine_version: GOVERNED_DEPLOYMENT_EXECUTION_ENGINE_VERSION,
    execution_schema_version: GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION,
  });
}

export function buildGovernedDeploymentExecutionResultHash(input: { execution_hash: string; attempts: unknown[]; delivery_result: unknown; rollback_result: unknown }) {
  return sha256Canonical({
    execution_hash: input.execution_hash,
    attempts: input.attempts,
    delivery_result: input.delivery_result,
    rollback_result: input.rollback_result,
    result_schema_version: GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION,
  });
}
