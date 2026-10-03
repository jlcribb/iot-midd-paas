import type { SourceSpan } from "./diagnostics";

interface NodeBase { span: SourceSpan }
export interface NumericLiteral extends NodeBase { kind: "NumericLiteral"; lexeme: string; value: number }
export interface SymbolReference extends NodeBase { kind: "SymbolReference"; identifier: string }
export interface UnaryExpression extends NodeBase { kind: "UnaryExpression"; operator: "+" | "-"; operand: ASTNode }
export interface BinaryExpression extends NodeBase { kind: "BinaryExpression"; operator: "+" | "-" | "*" | "/" | "^"; left: ASTNode; right: ASTNode }
export interface FunctionCall extends NodeBase { kind: "FunctionCall"; functionName: FunctionName; arguments: ASTNode[] }
export type FunctionName = "abs" | "min" | "max" | "sqrt" | "exp" | "ln" | "log10" | "pow";
export type ASTNode = NumericLiteral | SymbolReference | UnaryExpression | BinaryExpression | FunctionCall;

export interface ParsedExpression {
  sourceExpression: string;
  expressionLanguageVersion: "GDSS_EXPR_V1";
  ast: ASTNode;
}

export const FUNCTION_NAMES = new Set<FunctionName>(["abs", "min", "max", "sqrt", "exp", "ln", "log10", "pow"]);
