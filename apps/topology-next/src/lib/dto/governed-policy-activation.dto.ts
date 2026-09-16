export const ACTIVATION_READINESS_POLICY_VERSION="policy-activation-readiness:v1", ACTIVATION_READINESS_ENGINE_VERSION="policy-activation-readiness-engine:v1", ACTIVATION_READINESS_SCHEMA_VERSION="policy-activation-readiness-schema:v1";
export const ACTIVATION_AUTHORIZATION_POLICY_VERSION="governed-policy-activation:v1", ACTIVATION_AUTHORIZATION_SCHEMA_VERSION="governed-policy-activation-schema:v1";
export const GOVERNED_POLICY_ACTIVATION_POLICY_VERSION="governed-policy-activation:v1", GOVERNED_POLICY_ACTIVATION_SCHEMA_VERSION="governed-policy-activation-schema:v1";
export type ActivationReadinessStatus="PENDING"|"PASSED"|"FAILED"|"BLOCKED";
export type ActivationDecision="AUTHORIZE_POLICY_ACTIVATION"|"REJECT_ACTIVATION"|"REQUEST_ACTIVATION_REASSESSMENT";
export type ActivationStatus="PENDING"|"RUNNING"|"SUCCEEDED"|"FAILED"|"BLOCKED"|"ROLLBACK_PENDING"|"ROLLED_BACK"|"ROLLBACK_FAILED";
export type RollbackStatus="NOT_REQUIRED"|"PENDING"|"SUCCEEDED"|"FAILED";
