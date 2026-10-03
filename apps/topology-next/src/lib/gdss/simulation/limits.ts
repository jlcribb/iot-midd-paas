import { SIMULATION_LIMITS_VERSION } from "./versions";

export const GDSS_SIM_LIMITS_V1 = Object.freeze({
  profileVersion: SIMULATION_LIMITS_VERSION,
  states: 64,
  rates: 64,
  ratesPerState: 1,
  algebraicBindings: 256,
  parameterBindings: 256,
  constraints: 256,
  stepCount: 10_000,
  trajectoryPoints: 10_001,
  evaluatorOperationsPerStep: 8_192,
  totalEvaluatorOperations: 10_000_000,
  trajectoryBytes: 16_777_216,
  diagnostics: 256
});

export type SimulationLimits = typeof GDSS_SIM_LIMITS_V1;
