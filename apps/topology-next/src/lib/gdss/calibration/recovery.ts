export const GDSS_CALIBRATION_RECOVERY_V1=Object.freeze({
  claimLeaseSeconds:120,claimTimeoutSeconds:120,recoveryScanSeconds:30,abandonmentThresholdSeconds:900,
  dispatchAttempts:3,retryBackoffSeconds:[1,5] as const,terminalizationAttempts:3,
  terminalizationBackoffSeconds:[1,5] as const,maximumDurationSeconds:900,
});
