import { RECOVERY_VERSION } from "./versions";
export const GDSS_EXPERIMENT_RECOVERY_V1=Object.freeze({version:RECOVERY_VERSION,
  dispatchLeaseSeconds:60,claimDurationSeconds:60,claimBatchSize:8,
  abandonmentThresholdSeconds:900,maximumDispatchAttempts:3,
  dispatchBackoffSeconds:[1,5] as const,maximumTerminalizationAttempts:3,
  terminalizationBackoffSeconds:[1,5] as const,recoveryScanIntervalSeconds:30,
  orchestrationDurationSeconds:3600});
