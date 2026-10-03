export type SimulationStage = "PREFLIGHT" | "INITIALIZATION" | "ALGEBRAIC" | "RATE" | "TRANSITION" | "CONSTRAINT" | "SERIALIZATION" | "PERSISTENCE" | "RECOVERY";
export type SimulationSeverity = "ERROR" | "WARNING" | "INFO";
export type SimulationDiagnosticCode =
  | "VERSION_MISMATCH" | "INVALID_CONFIGURATION" | "INVALID_TIME_UNIT" | "DIMENSION_FAILURE"
  | "MISSING_INITIAL_CONDITION" | "DUPLICATE_INITIAL_CONDITION" | "MISSING_PARAMETER"
  | "CROSS_VERSION_REFERENCE" | "INVALID_BINDING" | "INSTANTANEOUS_ALGEBRAIC_LOOP_UNSUPPORTED"
  | "NON_FINITE_STATE" | "NON_FINITE_RATE" | "EXPRESSION_FAILURE" | "CONSTRAINT_VIOLATION"
  | "RESOURCE_LIMIT_EXCEEDED" | "SOLVER_FAILURE" | "ARTIFACT_INTEGRITY_FAILURE"
  | "EXECUTION_INTERRUPTED" | "INVALID_TRAJECTORY";

export interface SimulationDiagnostic {
  code: SimulationDiagnosticCode;
  severity: SimulationSeverity;
  stage: SimulationStage;
  stepIndex?: number;
  stateRef?: string;
  rateRef?: string;
  formulaRef?: string;
  details: Record<string, unknown>;
  message: string;
}

export class SimulationFault extends Error {
  constructor(public readonly diagnostic: SimulationDiagnostic) { super(diagnostic.message); }
}

type DiagnosticContext = Partial<Omit<SimulationDiagnostic,"code"|"severity"|"stage"|"message">>;
export function simulationFail(code: SimulationDiagnosticCode, stage: SimulationStage, message: string, details: DiagnosticContext = {}): never {
  throw new SimulationFault({ code, severity:"ERROR", stage, details:details.details ?? {}, message, stepIndex:details.stepIndex, stateRef:details.stateRef, rateRef:details.rateRef, formulaRef:details.formulaRef });
}
