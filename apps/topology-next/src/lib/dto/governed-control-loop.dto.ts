export const CONTROL_LOOP_READINESS_POLICY_VERSION="control-loop-readiness:v1",CONTROL_LOOP_READINESS_ENGINE_VERSION="control-loop-readiness-engine:v1",CONTROL_LOOP_READINESS_SCHEMA_VERSION="control-loop-readiness-schema:v1";
export const CONTROL_LOOP_AUTHORIZATION_POLICY_VERSION="governed-control-loop-enablement:v1",CONTROL_LOOP_AUTHORIZATION_SCHEMA_VERSION="governed-control-loop-enablement-schema:v1",CONTROL_LOOP_SESSION_SCHEMA_VERSION="governed-control-loop-session-schema:v1",SHADOW_CONTROL_OUTPUT_SCHEMA_VERSION="shadow-control-output-schema:v1";
export type ControlLoopReadinessStatus="PENDING"|"PASSED"|"FAILED"|"BLOCKED";
export type ControlLoopEnablementDecision="AUTHORIZE_SHADOW_CONTROL_LOOP"|"REJECT_CONTROL_LOOP_ENABLEMENT"|"REQUEST_CONTROL_LOOP_REASSESSMENT";
export type ControlLoopSessionStatus="PENDING"|"RUNNING"|"STOPPING"|"COMPLETED"|"FAILED"|"BLOCKED"|"STOPPED";
export type ShadowExecutionMode="SHADOW"|"DRY_RUN";
