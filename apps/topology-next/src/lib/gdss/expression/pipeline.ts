import { validateContent, type ModelContent } from "@/lib/gdss/core";
import { derivedHash, expressionAstHash } from "./canonical";
import { assertAcyclic, buildDependencyGraph, type DependencyGraph, type FormulaDependency } from "./dependencies";
import { diagnosticFrom, fail, type EvaluationDiagnostic, type EvaluationStage } from "./diagnostics";
import { dimensionsEqual } from "./dimensions";
import { analyzeAst, evaluateAst, formatOutput, prepareInputs, type EvaluationInputs } from "./evaluator";
import { DEFAULT_EXPRESSION_LIMITS, type ExpressionLimits } from "./limits";
import { parseExpression } from "./parser";
import { findFormula, resolveSymbols, type FormulaContent } from "./symbols";
import { getUnitCatalog, type QuantitySemantics, type UnitIdentity } from "./units";
import { EVALUATOR_VERSION, EXPRESSION_LANGUAGE_VERSION, RESOURCE_LIMITS_PROFILE, type UnitConversionCatalogVersion } from "./versions";

export interface ModelVersionSnapshot { id: string; content: ModelContent; content_hash?: string | null; lifecycle_status?: string }
export interface EvaluationContext {
  projectId: string;
  modelVersionId: string;
  formulaSymbol: string;
  expressionLanguageVersion: typeof EXPRESSION_LANGUAGE_VERSION;
  evaluatorVersion: typeof EVALUATOR_VERSION;
  conversionCatalogVersion: UnitConversionCatalogVersion;
  resourceLimitsProfile: typeof RESOURCE_LIMITS_PROFILE;
  inputs: EvaluationInputs;
  requestedOutputUnit?: UnitIdentity;
  expectedOutputQuantitySemantics?: QuantitySemantics;
}
export interface EvaluationSuccess {
  status: "SUCCEEDED";
  stage: "EVALUABLE";
  modelVersionId: string;
  formulaSymbol: string;
  expressionLanguageVersion: typeof EXPRESSION_LANGUAGE_VERSION;
  evaluatorVersion: typeof EVALUATOR_VERSION;
  conversionCatalogVersion: UnitConversionCatalogVersion;
  resourceLimitsProfile: typeof RESOURCE_LIMITS_PROFILE;
  result: { value: number; unit: UnitIdentity; dimension: readonly number[]; quantitySemantics?: QuantitySemantics };
  dependencyGraph: DependencyGraph;
  expression_ast_hash: string;
  evaluation_input_hash: string;
  evaluation_result_hash: string;
  epistemic_kind: "DERIVED";
  physical_authority: "NONE";
  diagnostics: readonly EvaluationDiagnostic[];
}
export interface EvaluationFailure { status: "FAILED"; stage: EvaluationStage; modelVersionId: string; formulaSymbol: string; diagnostics: readonly EvaluationDiagnostic[]; expression_ast_hash?: string; evaluation_input_hash?: string }
export type ExpressionEvaluationResult = EvaluationSuccess | EvaluationFailure;

function preflightOwnership(model: ModelContent, formulaSymbol: string) {
  const counts = new Map<string,number>();
  for (const child of model.children) counts.set(child.symbol,(counts.get(child.symbol) ?? 0)+1);
  const duplicate = [...counts].find(([,count]) => count > 1);
  if (duplicate) fail("AMBIGUOUS_SYMBOL", "SYMBOL_RESOLVED", "Model contains an ambiguous local symbol", { symbol:duplicate[0], actual:duplicate[1] });
  const formula = model.children.find(child => child.symbol === formulaSymbol);
  if (!formula) fail("FORMULA_NOT_FOUND", "SOURCE", "Formula was not found", { symbol:formulaSymbol });
  if (formula.kind !== "Formula") fail("INVALID_SYMBOL_KIND", "SOURCE", "Requested artifact is not a Formula", { symbol:formulaSymbol, actual:formula.kind });
  for (const symbol of [...formula.input_refs,formula.output_ref]) {
    const target = model.children.find(child => child.symbol === symbol);
    if (!target) fail("UNKNOWN_SYMBOL", "SYMBOL_RESOLVED", "Formula reference is unknown in exact model version", { symbol });
    if (target.kind !== "Variable" && target.kind !== "Parameter") fail("INVALID_SYMBOL_KIND", "SYMBOL_RESOLVED", "Formula reference is not a computational quantity", { symbol, actual:target.kind });
  }
}

function assertVersions(context: EvaluationContext, snapshot: ModelVersionSnapshot) {
  if (context.modelVersionId !== snapshot.id) fail("CROSS_VERSION_REFERENCE", "SOURCE", "Evaluation context does not match exact model version", { expected: snapshot.id, actual: context.modelVersionId });
  const expected = { expressionLanguageVersion:EXPRESSION_LANGUAGE_VERSION, evaluatorVersion:EVALUATOR_VERSION, resourceLimitsProfile:RESOURCE_LIMITS_PROFILE };
  for (const [field,value] of Object.entries(expected)) if (context[field as keyof EvaluationContext] !== value) fail("VERSION_MISMATCH", "SOURCE", `${field} is not supported`, { expected:value, actual:context[field as keyof EvaluationContext] });
  getUnitCatalog(context.conversionCatalogVersion);
}

function compileDependencies(model: ModelContent, limits: ExpressionLimits): { records: FormulaDependency[]; compiled: Map<string,{formula:FormulaContent;ast:ReturnType<typeof parseExpression>["ast"]}> } {
  const records: FormulaDependency[] = [], compiled = new Map<string,{formula:FormulaContent;ast:ReturnType<typeof parseExpression>["ast"]}>();
  for (const child of model.children) if (child.kind === "Formula") {
    const parsed = parseExpression(child.expression_source,limits);
    const resolved = resolveSymbols(model,child,parsed.ast,limits);
    records.push({ formula:child.symbol, output:child.output_ref, inputs:resolved.references });
    compiled.set(child.symbol,{formula:child,ast:parsed.ast});
  }
  return {records,compiled};
}

export function evaluateExpression(snapshot: ModelVersionSnapshot, context: EvaluationContext, limits: ExpressionLimits = DEFAULT_EXPRESSION_LIMITS): ExpressionEvaluationResult {
  let stage: EvaluationStage = "SOURCE", astHash: string | undefined, inputHash: string | undefined;
  try {
    assertVersions(context,snapshot);
    preflightOwnership(snapshot.content,context.formulaSymbol);
    const model = validateContent(snapshot.content);
    const formula = findFormula(model,context.formulaSymbol);
    const parsed = parseExpression(formula.expression_source,limits);
    stage = "PARSED"; astHash = expressionAstHash(parsed.ast);
    const resolved = resolveSymbols(model,formula,parsed.ast,limits);
    const dependencies = compileDependencies(model,limits);
    const graph = buildDependencyGraph(dependencies.records,limits);
    assertAcyclic(graph);
    stage = "SYMBOL_RESOLVED";
    inputHash = derivedHash("gdss-eval-input:v1", { modelVersionId:snapshot.id, formulaSymbol:formula.symbol, expressionLanguageVersion:context.expressionLanguageVersion, evaluatorVersion:context.evaluatorVersion, conversionCatalogVersion:context.conversionCatalogVersion, resourceLimitsProfile:context.resourceLimitsProfile, inputs:context.inputs, requestedOutputUnit:context.requestedOutputUnit, expectedOutputQuantitySemantics:context.expectedOutputQuantitySemantics });
    const values = prepareInputs(model,resolved,context.inputs,limits,context.conversionCatalogVersion);
    const dimensional = analyzeAst(parsed.ast,values);
    if (!dimensionsEqual(dimensional.dimension,resolved.output.dimension)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Expression dimension does not match output artifact", { expected:resolved.output.dimension, actual:dimensional.dimension });
    if (dimensional.quantitySemantics !== context.expectedOutputQuantitySemantics && (dimensional.quantitySemantics || context.expectedOutputQuantitySemantics)) fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Derived output quantity semantics differ from evaluation context", { expected:context.expectedOutputQuantitySemantics, actual:dimensional.quantitySemantics });
    stage = "DIMENSIONALLY_VALIDATED";
    const canonicalValue = evaluateAst(parsed.ast,values,limits);
    const output = formatOutput(canonicalValue,model,resolved.output.unit_ref,context.requestedOutputUnit,dimensional.quantitySemantics,context.conversionCatalogVersion);
    const resultBase = { value:output.value, unit:output.unit, dimension:dimensional.dimension, quantitySemantics:output.quantitySemantics };
    const resultHash = derivedHash("gdss-eval-result:v1", { evaluation_input_hash:inputHash, expression_ast_hash:astHash, result:resultBase, epistemic_kind:"DERIVED", physical_authority:"NONE" });
    return { status:"SUCCEEDED", stage:"EVALUABLE", modelVersionId:snapshot.id, formulaSymbol:formula.symbol, expressionLanguageVersion:EXPRESSION_LANGUAGE_VERSION, evaluatorVersion:EVALUATOR_VERSION, conversionCatalogVersion:context.conversionCatalogVersion, resourceLimitsProfile:RESOURCE_LIMITS_PROFILE, result:resultBase, dependencyGraph:graph, expression_ast_hash:astHash, evaluation_input_hash:inputHash, evaluation_result_hash:resultHash, epistemic_kind:"DERIVED", physical_authority:"NONE", diagnostics:[] };
  } catch (error) {
    const diagnostic = diagnosticFrom(error,stage,context.formulaSymbol);
    return { status:"FAILED", stage:diagnostic.stage, modelVersionId:snapshot.id, formulaSymbol:context.formulaSymbol, diagnostics:[diagnostic], expression_ast_hash:astHash, evaluation_input_hash:inputHash };
  }
}
