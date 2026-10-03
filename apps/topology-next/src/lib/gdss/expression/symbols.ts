import type { Child, ModelContent } from "@/lib/gdss/core";
import type { ASTNode } from "./ast";
import { fail } from "./diagnostics";
import { assertLimit, DEFAULT_EXPRESSION_LIMITS, type ExpressionLimits } from "./limits";

export type FormulaContent = Extract<Child,{kind:"Formula"}>;
export type Quantity = Extract<Child,{kind:"Variable" | "Parameter"}>;
export interface ResolvedSymbols { symbols: ReadonlyMap<string,Quantity>; references: readonly string[]; output: Quantity }

export function astReferences(ast: ASTNode): string[] {
  const found = new Set<string>();
  const visit = (node: ASTNode) => {
    if (node.kind === "SymbolReference") found.add(node.identifier);
    else if (node.kind === "UnaryExpression") visit(node.operand);
    else if (node.kind === "BinaryExpression") { visit(node.left); visit(node.right); }
    else if (node.kind === "FunctionCall") node.arguments.forEach(visit);
  };
  visit(ast);
  return [...found].sort();
}

function quantity(matches: Child[], symbol: string): Quantity {
  if (!matches.length) fail("UNKNOWN_SYMBOL", "SYMBOL_RESOLVED", "Symbol does not exist in model version", { symbol });
  if (matches.length > 1) fail("AMBIGUOUS_SYMBOL", "SYMBOL_RESOLVED", "Symbol is ambiguous in model version", { symbol, actual: matches.length });
  if (matches[0].kind !== "Variable" && matches[0].kind !== "Parameter") fail("INVALID_SYMBOL_KIND", "SYMBOL_RESOLVED", "Symbol is not a computational quantity", { symbol, actual: matches[0].kind });
  return matches[0] as Quantity;
}

export function resolveSymbols(model: ModelContent, formula: FormulaContent, ast: ASTNode, limits: ExpressionLimits = DEFAULT_EXPRESSION_LIMITS): ResolvedSymbols {
  const references = astReferences(ast);
  assertLimit(references.length,limits.distinctSymbols,"distinct symbol references","SYMBOL_RESOLVED");
  const declared = [...new Set(formula.input_refs)].sort();
  if (JSON.stringify(references) !== JSON.stringify(declared))
    fail("DECLARED_DEPENDENCY_MISMATCH", "SYMBOL_RESOLVED", "AST references must equal governed input_refs", { expected: declared, actual: references });
  const entries = references.map(symbol => [symbol,quantity(model.children.filter(child => child.symbol === symbol),symbol)] as const);
  const output = quantity(model.children.filter(child => child.symbol === formula.output_ref),formula.output_ref);
  return { symbols: new Map(entries), references, output };
}

export function findFormula(model: ModelContent, symbol: string): FormulaContent {
  const matches = model.children.filter(child => child.symbol === symbol);
  if (!matches.length) fail("FORMULA_NOT_FOUND", "SOURCE", "Formula was not found", { symbol });
  if (matches.length > 1) fail("AMBIGUOUS_SYMBOL", "SOURCE", "Formula symbol is ambiguous", { symbol });
  if (matches[0].kind !== "Formula") fail("INVALID_SYMBOL_KIND", "SOURCE", "Requested artifact is not a Formula", { symbol, actual: matches[0].kind });
  return matches[0] as FormulaContent;
}
