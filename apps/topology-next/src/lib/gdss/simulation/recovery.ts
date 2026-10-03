import { RECOVERY_POLICY_VERSION } from "./versions";

export const GDSS_SIM_RECOVERY_V1 = Object.freeze({
  version:RECOVERY_POLICY_VERSION,
  abandonmentThresholdSeconds:900,
  terminalStatus:"FAILED" as const,
  terminationReason:"EXECUTION_INTERRUPTED" as const
});
