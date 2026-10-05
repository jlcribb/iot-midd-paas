import { LIMITS_VERSION } from "./versions";
export const GDSS_EXPERIMENT_LIMITS_V1=Object.freeze({
  profileVersion:LIMITS_VERSION,canonicalDesignBytes:262_144,factors:8,valuesPerFactor:32,
  expandedScenarios:256,overridesPerScenario:32,controlledInputs:256,metricDefinitions:32,
  comparisonDefinitions:64,totalReferencedTrajectoryPoints:1_000_000,
  aggregateReferencedTrajectoryBytes:268_435_456,metricOperations:32_000_000,
  comparisonOperations:4_096,diagnostics:512,concurrentScenarioDispatches:8,
  dispatchAttemptsPerScenario:3,orchestrationDurationSeconds:3_600,
  manifestArtifactBytes:4_194_304,resultArtifactBytes:16_777_216
});
