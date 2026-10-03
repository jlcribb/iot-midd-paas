import { FUNCTION_NAMES, type ASTNode, type FunctionName, type ParsedExpression } from "./ast";
import { fail } from "./diagnostics";
import { assertLimit, DEFAULT_EXPRESSION_LIMITS, type ExpressionLimits } from "./limits";
import type { Token, TokenKind } from "./tokens";
import { tokenize } from "./tokenizer";
import { EXPRESSION_LANGUAGE_VERSION } from "./versions";

const arity: Record<FunctionName, [number, number]> = { abs: [1,1], min: [2,16], max: [2,16], sqrt: [1,1], exp: [1,1], ln: [1,1], log10: [1,1], pow: [2,2] };

export function parseExpression(source: string, limits: ExpressionLimits = DEFAULT_EXPRESSION_LIMITS): ParsedExpression {
  const tokens = tokenize(source, limits);
  let current = 0, nodes = 0, functionDepth = 0;
  const peek = () => tokens[current];
  const previous = () => tokens[current - 1];
  const match = (...kinds: TokenKind[]) => kinds.includes(peek().kind) ? (current += 1, true) : false;
  const consume = (kind: TokenKind, message: string) => {
    if (peek().kind !== kind) fail("PARSE_ERROR", "PARSED", message, { sourceSpan: peek().span, actual: peek().lexeme });
    return tokens[current++];
  };
  const node = <T extends ASTNode>(value: T, depth: number): T => {
    nodes += 1;
    assertLimit(nodes, limits.astNodes, "AST node count", "PARSED");
    assertLimit(depth, limits.astDepth, "AST depth", "PARSED");
    return value;
  };
  const guardDepth = (depth: number) => assertLimit(depth,limits.astDepth,"AST depth","PARSED");
  function primary(depth: number): ASTNode {
    guardDepth(depth);
    if (match("number")) {
      const token = previous(), value = Number(token.lexeme);
      if (!Number.isFinite(value)) fail("NON_FINITE_LITERAL", "PARSED", "Numeric literal is not finite", { sourceSpan: token.span, actual: token.lexeme });
      return node({ kind: "NumericLiteral", lexeme: token.lexeme, value, span: token.span }, depth);
    }
    if (match("identifier")) {
      const token = previous();
      if (match("lparen")) {
        if (!FUNCTION_NAMES.has(token.lexeme as FunctionName)) fail("UNSUPPORTED_FUNCTION", "PARSED", "Function is not allowlisted", { sourceSpan: token.span, actual: token.lexeme });
        functionDepth += 1;
        assertLimit(functionDepth, limits.functionNesting, "function nesting", "PARSED");
        const args: ASTNode[] = [];
        if (peek().kind !== "rparen") {
          do { args.push(additive(depth + 1)); } while (match("comma"));
        }
        const close = consume("rparen", "Expected ')' after function arguments");
        functionDepth -= 1;
        const name = token.lexeme as FunctionName;
        const [min,max] = arity[name];
        if (args.length < min || args.length > max) fail("INVALID_FUNCTION_DOMAIN", "PARSED", "Function arity is invalid", { sourceSpan: { start: token.span.start, end: close.span.end }, expected: `${min}..${max}`, actual: args.length });
        return node({ kind: "FunctionCall", functionName: name, arguments: args, span: { start: token.span.start, end: close.span.end } }, depth);
      }
      return node({ kind: "SymbolReference", identifier: token.lexeme, span: token.span }, depth);
    }
    if (match("lparen")) {
      const open = previous(), expression = additive(depth + 1), close = consume("rparen", "Expected ')' after expression");
      expression.span = { start: open.span.start, end: close.span.end };
      return expression;
    }
    fail("PARSE_ERROR", "PARSED", "Expected expression", { sourceSpan: peek().span, actual: peek().lexeme });
  }
  function power(depth: number): ASTNode {
    guardDepth(depth);
    const left = primary(depth + 1);
    if (!match("caret")) return left;
    const right = unary(depth + 1);
    return node({ kind: "BinaryExpression", operator: "^", left, right, span: { start: left.span.start, end: right.span.end } }, depth);
  }
  function unary(depth: number): ASTNode {
    guardDepth(depth);
    if (match("plus", "minus")) {
      const operator = previous(), operand = unary(depth + 1);
      return node({ kind: "UnaryExpression", operator: operator.kind === "plus" ? "+" : "-", operand, span: { start: operator.span.start, end: operand.span.end } }, depth);
    }
    return power(depth + 1);
  }
  function multiplicative(depth: number): ASTNode {
    guardDepth(depth);
    let expression = unary(depth + 1);
    while (match("star", "slash")) {
      const operator = previous(), right = unary(depth + 1);
      expression = node({ kind: "BinaryExpression", operator: operator.kind === "star" ? "*" : "/", left: expression, right, span: { start: expression.span.start, end: right.span.end } }, depth);
    }
    return expression;
  }
  function additive(depth: number): ASTNode {
    guardDepth(depth);
    let expression = multiplicative(depth + 1);
    while (match("plus", "minus")) {
      const operator = previous(), right = multiplicative(depth + 1);
      expression = node({ kind: "BinaryExpression", operator: operator.kind === "plus" ? "+" : "-", left: expression, right, span: { start: expression.span.start, end: right.span.end } }, depth);
    }
    return expression;
  }
  const ast = additive(1);
  consume("eof", "Unexpected trailing token");
  return { sourceExpression: source, expressionLanguageVersion: EXPRESSION_LANGUAGE_VERSION, ast };
}
