export type EvaluationStage = "SOURCE" | "PARSED" | "SYMBOL_RESOLVED" | "DIMENSIONALLY_VALIDATED" | "EVALUABLE";
export type DiagnosticCode =
  | "PARSE_ERROR" | "UNSUPPORTED_TOKEN" | "UNSUPPORTED_OPERATOR" | "UNSUPPORTED_FUNCTION"
  | "NON_FINITE_LITERAL" | "UNKNOWN_SYMBOL" | "AMBIGUOUS_SYMBOL" | "CROSS_VERSION_REFERENCE"
  | "INVALID_SYMBOL_KIND" | "DECLARED_DEPENDENCY_MISMATCH" | "DIMENSION_MISMATCH"
  | "UNKNOWN_OR_MISSING_DIMENSION" | "AFFINE_QUANTITY_ERROR" | "INVALID_FUNCTION_DOMAIN"
  | "CYCLIC_DEPENDENCY_REQUIRES_DYNAMIC_SEMANTICS" | "MISSING_INPUT" | "UNDECLARED_INPUT"
  | "INVALID_INPUT_UNIT" | "DIVISION_BY_ZERO" | "NON_FINITE_INPUT" | "NON_FINITE_RESULT"
  | "RESOURCE_LIMIT_EXCEEDED" | "VERSION_MISMATCH" | "FORMULA_NOT_FOUND";

export interface SourceSpan { start: number; end: number }
export interface EvaluationDiagnostic {
  code: DiagnosticCode;
  stage: EvaluationStage;
  severity: "ERROR" | "WARNING" | "INFO";
  formulaRef?: string;
  sourceSpan?: SourceSpan;
  symbol?: string;
  expected?: unknown;
  actual?: unknown;
  message: string;
}

export class ExpressionFailure extends Error {
  constructor(readonly diagnostic: EvaluationDiagnostic) {
    super(diagnostic.message);
    this.name = "ExpressionFailure";
  }
}

export function fail(code: DiagnosticCode, stage: EvaluationStage, message: string, details: Partial<EvaluationDiagnostic> = {}): never {
  throw new ExpressionFailure({ code, stage, severity: "ERROR", message, ...details });
}

export function diagnosticFrom(error: unknown, stage: EvaluationStage, formulaRef?: string): EvaluationDiagnostic {
  if (error instanceof ExpressionFailure) return { formulaRef, ...error.diagnostic };
  return { code: "PARSE_ERROR", stage, severity: "ERROR", formulaRef, message: error instanceof Error ? error.message : "Unknown expression failure" };
}
