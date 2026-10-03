import type { DimensionDefinition, ModelContent } from "@/lib/gdss/core";
import type { ASTNode, FunctionCall } from "./ast";
import { fail } from "./diagnostics";
import { compatibleForAddSubtract, dimensionsEqual, divideDimensions, DIMENSIONLESS, isDimensionless, multiplyDimensions, powerDimension, sqrtDimension } from "./dimensions";
import { assertLimit, DEFAULT_EXPRESSION_LIMITS, type ExpressionLimits } from "./limits";
import type { ResolvedSymbols } from "./symbols";
import { assertConvertible, assertModelUnit, assertQuantitySemantics, catalogUnit, fromCanonical, toCanonical, type QuantitySemantics, type UnitIdentity } from "./units";

export interface EvaluationInput { value: number; unit: UnitIdentity; quantitySemantics?: QuantitySemantics }
export interface EvaluationInputs { [symbol: string]: EvaluationInput }
export interface SemanticValue { value: number; dimension: DimensionDefinition; quantitySemantics?: QuantitySemantics }
export interface DimensionalValue { dimension: DimensionDefinition; quantitySemantics?: QuantitySemantics }

function finite(value: number, code: "NON_FINITE_INPUT" | "NON_FINITE_RESULT", span?: {start:number;end:number}) {
  if (!Number.isFinite(value)) fail(code, code === "NON_FINITE_INPUT" ? "DIMENSIONALLY_VALIDATED" : "EVALUABLE", "Numeric value must be finite", { sourceSpan: span, actual: value });
  return Object.is(value,-0) ? 0 : value;
}

function literalInteger(node: ASTNode): number | undefined {
  if (node.kind === "NumericLiteral" && Number.isSafeInteger(node.value)) return node.value;
  if (node.kind === "UnaryExpression") {
    const value = literalInteger(node.operand);
    if (value !== undefined) return node.operator === "-" ? -value : value;
  }
  return undefined;
}

function combineAffine(operator: "+" | "-", left: QuantitySemantics | undefined, right: QuantitySemantics | undefined, span: {start:number;end:number}) {
  if (!left && !right) return undefined;
  if (!left || !right) fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Affine arithmetic requires explicit semantics on both operands", { sourceSpan: span });
  if (operator === "+") {
    if (left === "ABSOLUTE" && right === "ABSOLUTE") fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Absolute affine quantities cannot be added", { sourceSpan: span });
    if (left === "ABSOLUTE" || right === "ABSOLUTE") return "ABSOLUTE" as const;
    return "INTERVAL" as const;
  }
  if (left === "INTERVAL" && right === "ABSOLUTE") fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "An absolute affine quantity cannot be subtracted from an interval", { sourceSpan: span });
  if (left === "ABSOLUTE" && right === "ABSOLUTE") return "INTERVAL" as const;
  return left;
}

function analyzeFunction(node: FunctionCall, values: DimensionalValue[]): DimensionalValue {
  const first = values[0];
  if (node.functionName === "abs") {
    if (first.quantitySemantics === "ABSOLUTE") fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "abs of an absolute affine quantity is not defined in v1", { sourceSpan: node.span });
    return first;
  }
  if (node.functionName === "min" || node.functionName === "max") {
    values.slice(1).forEach(value => compatibleForAddSubtract(first.dimension,value.dimension,node.span));
    if (values.some(value => value.quantitySemantics === "ABSOLUTE")) fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "min/max of absolute affine quantities is not defined in v1", { sourceSpan: node.span });
    if (values.some(value => value.quantitySemantics !== first.quantitySemantics)) fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "min/max requires matching quantity semantics", { sourceSpan: node.span });
    return first;
  }
  if (node.functionName === "sqrt") {
    if (first.quantitySemantics === "ABSOLUTE") fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "sqrt of an absolute affine quantity is not defined", { sourceSpan: node.span });
    return { dimension: sqrtDimension(first.dimension,node.span) };
  }
  if (["exp","ln","log10"].includes(node.functionName)) {
    if (!isDimensionless(first.dimension)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", `${node.functionName} requires a dimensionless argument`, { sourceSpan: node.span, actual: first.dimension });
    return { dimension: DIMENSIONLESS };
  }
  const exponent = values[1];
  if (!isDimensionless(exponent.dimension)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "pow exponent must be dimensionless", { sourceSpan: node.arguments[1].span });
  if (isDimensionless(first.dimension)) return { dimension: DIMENSIONLESS };
  if (first.quantitySemantics === "ABSOLUTE") fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Absolute affine quantities cannot be exponentiated", { sourceSpan: node.span });
  const integer = literalInteger(node.arguments[1]);
  if (integer === undefined) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Dimensioned pow requires an integer literal exponent", { sourceSpan: node.arguments[1].span });
  return { dimension: powerDimension(first.dimension,integer,node.span), quantitySemantics: integer === 1 ? first.quantitySemantics : undefined };
}

export function prepareInputs(model: ModelContent, resolved: ResolvedSymbols, inputs: EvaluationInputs, limits: ExpressionLimits = DEFAULT_EXPRESSION_LIMITS): ReadonlyMap<string,SemanticValue> {
  assertLimit(Object.keys(inputs).length,limits.suppliedInputs,"supplied inputs","EVALUABLE");
  const declared = new Set(resolved.references);
  for (const symbol of Object.keys(inputs)) if (!declared.has(symbol)) fail("UNDECLARED_INPUT", "EVALUABLE", "Input is not declared by formula", { symbol });
  const units = new Map(model.units.map(unit => [unit.key,unit]));
  const prepared = new Map<string,SemanticValue>();
  for (const symbol of resolved.references) {
    const input = inputs[symbol];
    if (!input) fail("MISSING_INPUT", "EVALUABLE", "Declared formula input is missing", { symbol });
    finite(input.value,"NON_FINITE_INPUT");
    const artifact = resolved.symbols.get(symbol)!;
    const modelDefinition = units.get(artifact.unit_ref);
    if (!modelDefinition) fail("INVALID_INPUT_UNIT", "DIMENSIONALLY_VALIDATED", "Governed model unit is missing", { symbol, actual: artifact.unit_ref });
    const modelUnit = assertModelUnit(modelDefinition);
    const suppliedUnit = catalogUnit(input.unit);
    assertConvertible(suppliedUnit,modelUnit);
    if (!dimensionsEqual(artifact.dimension,modelUnit.dimension)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Artifact dimension differs from governed unit", { symbol, expected: artifact.dimension, actual: modelUnit.dimension });
    const semantics = assertQuantitySemantics(suppliedUnit,input.quantitySemantics);
    if (modelUnit.affineFamily && !input.quantitySemantics) fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Affine model quantity requires explicit semantics", { symbol });
    prepared.set(symbol,{ value: finite(toCanonical(input.value,suppliedUnit,semantics),"NON_FINITE_RESULT"), dimension: artifact.dimension, quantitySemantics: modelUnit.affineFamily ? semantics : undefined });
  }
  return prepared;
}

export function analyzeAst(ast: ASTNode, symbols: ReadonlyMap<string,SemanticValue>): DimensionalValue {
  if (ast.kind === "NumericLiteral") return { dimension: DIMENSIONLESS };
  if (ast.kind === "SymbolReference") return symbols.get(ast.identifier)!;
  if (ast.kind === "UnaryExpression") {
    const value = analyzeAst(ast.operand,symbols);
    if (ast.operator === "-" && value.quantitySemantics === "ABSOLUTE") fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Absolute affine quantities cannot be negated", { sourceSpan: ast.span });
    return value;
  }
  if (ast.kind === "FunctionCall") return analyzeFunction(ast,ast.arguments.map(arg => analyzeAst(arg,symbols)));
  const left = analyzeAst(ast.left,symbols), right = analyzeAst(ast.right,symbols);
  if (ast.operator === "+" || ast.operator === "-") return { dimension: compatibleForAddSubtract(left.dimension,right.dimension,ast.span), quantitySemantics: combineAffine(ast.operator,left.quantitySemantics,right.quantitySemantics,ast.span) };
  if (left.quantitySemantics === "ABSOLUTE" || right.quantitySemantics === "ABSOLUTE") fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Absolute affine quantities cannot be multiplied, divided or exponentiated", { sourceSpan: ast.span });
  if (ast.operator === "*") {
    const dimension = multiplyDimensions(left.dimension,right.dimension);
    const semantics = isDimensionless(left.dimension) ? right.quantitySemantics : isDimensionless(right.dimension) ? left.quantitySemantics : undefined;
    return { dimension, quantitySemantics: semantics };
  }
  if (ast.operator === "/") {
    const dimension = divideDimensions(left.dimension,right.dimension);
    return { dimension, quantitySemantics: isDimensionless(right.dimension) ? left.quantitySemantics : undefined };
  }
  if (!isDimensionless(right.dimension)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Power exponent must be dimensionless", { sourceSpan: ast.right.span });
  if (isDimensionless(left.dimension)) return { dimension: DIMENSIONLESS };
  const exponent = literalInteger(ast.right);
  if (exponent === undefined) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Dimensioned power requires an integer literal exponent", { sourceSpan: ast.right.span });
  return { dimension: powerDimension(left.dimension,exponent,ast.span), quantitySemantics: exponent === 1 ? left.quantitySemantics : undefined };
}

function realPower(base: number, exponent: number, span: {start:number;end:number}) {
  if ((base === 0 && exponent <= 0) || (base < 0 && !Number.isInteger(exponent))) fail("INVALID_FUNCTION_DOMAIN", "EVALUABLE", "Power is outside the supported real domain", { sourceSpan: span, actual: {base,exponent} });
  return Math.pow(base,exponent);
}

export function evaluateAst(ast: ASTNode, symbols: ReadonlyMap<string,SemanticValue>, limits: ExpressionLimits = DEFAULT_EXPRESSION_LIMITS): number {
  let operations = 0;
  const evaluate = (node: ASTNode): number => {
    operations += 1; assertLimit(operations,limits.evaluatorOperations,"evaluator operations","EVALUABLE");
    if (node.kind === "NumericLiteral") return node.value;
    if (node.kind === "SymbolReference") return symbols.get(node.identifier)!.value;
    if (node.kind === "UnaryExpression") { const value = evaluate(node.operand); return finite(node.operator === "-" ? -value : value,"NON_FINITE_RESULT",node.span); }
    if (node.kind === "BinaryExpression") {
      const left = evaluate(node.left), right = evaluate(node.right); let result: number;
      if (node.operator === "+") result = left + right;
      else if (node.operator === "-") result = left - right;
      else if (node.operator === "*") result = left * right;
      else if (node.operator === "/") { if (right === 0) fail("DIVISION_BY_ZERO", "EVALUABLE", "Division by zero", { sourceSpan: node.right.span }); result = left / right; }
      else result = realPower(left,right,node.span);
      return finite(result,"NON_FINITE_RESULT",node.span);
    }
    const values = node.arguments.map(evaluate); let result: number;
    if (node.functionName === "abs") result = Math.abs(values[0]);
    else if (node.functionName === "min") result = Math.min(...values);
    else if (node.functionName === "max") result = Math.max(...values);
    else if (node.functionName === "sqrt") { if (values[0] < 0) fail("INVALID_FUNCTION_DOMAIN", "EVALUABLE", "sqrt requires a non-negative value", { sourceSpan: node.span }); result = Math.sqrt(values[0]); }
    else if (node.functionName === "exp") result = Math.exp(values[0]);
    else if (node.functionName === "ln") { if (values[0] <= 0) fail("INVALID_FUNCTION_DOMAIN", "EVALUABLE", "ln requires a positive value", { sourceSpan: node.span }); result = Math.log(values[0]); }
    else if (node.functionName === "log10") { if (values[0] <= 0) fail("INVALID_FUNCTION_DOMAIN", "EVALUABLE", "log10 requires a positive value", { sourceSpan: node.span }); result = Math.log10(values[0]); }
    else result = realPower(values[0],values[1],node.span);
    return finite(result,"NON_FINITE_RESULT",node.span);
  };
  return evaluate(ast);
}

export function formatOutput(canonicalValue: number, model: ModelContent, outputUnitRef: string, requested: UnitIdentity | undefined, semantics: QuantitySemantics | undefined) {
  const definition = model.units.find(unit => unit.key === outputUnitRef);
  if (!definition) fail("INVALID_INPUT_UNIT", "DIMENSIONALLY_VALIDATED", "Output unit is absent from model", { actual: outputUnitRef });
  const governed = assertModelUnit(definition), target = requested ? catalogUnit(requested) : governed;
  assertConvertible(governed,target);
  const resolvedSemantics = assertQuantitySemantics(target,semantics);
  return { value: finite(fromCanonical(canonicalValue,target,resolvedSemantics),"NON_FINITE_RESULT"), unit: {key:target.key,revision:target.revision}, quantitySemantics: target.affineFamily ? resolvedSemantics : undefined };
}
