import { fail } from "./diagnostics";
import { assertLimit, DEFAULT_EXPRESSION_LIMITS, type ExpressionLimits } from "./limits";
import type { Token, TokenKind } from "./tokens";

const punctuation: Record<string, TokenKind> = { "+": "plus", "-": "minus", "*": "star", "/": "slash", "^": "caret", "(": "lparen", ")": "rparen", ",": "comma" };
const asciiLetter = (value: string) => /^[A-Za-z]$/.test(value);
const asciiDigit = (value: string) => /^[0-9]$/.test(value);
const identifierPart = (value: string) => /^[A-Za-z0-9_]$/.test(value);

export function tokenize(source: string, limits: ExpressionLimits = DEFAULT_EXPRESSION_LIMITS): Token[] {
  if (!source.trim()) fail("PARSE_ERROR", "SOURCE", "Expression source is empty");
  assertLimit(source.length, limits.sourceLength, "source length", "SOURCE");
  const tokens: Token[] = [];
  let cursor = 0;
  const push = (kind: TokenKind, start: number, end: number) => {
    tokens.push({ kind, lexeme: source.slice(start, end), span: { start, end } });
    assertLimit(tokens.length, limits.tokenCount, "token count", "SOURCE");
  };
  while (cursor < source.length) {
    const value = source[cursor];
    if (/\s/u.test(value)) { cursor += 1; continue; }
    if (punctuation[value]) { push(punctuation[value], cursor, cursor + 1); cursor += 1; continue; }
    if ("%=<>!&|".includes(value)) fail("UNSUPPORTED_OPERATOR", "SOURCE", "Operator is not supported by GDSS_EXPR_V1", { sourceSpan: { start: cursor, end: cursor + 1 }, actual: value });
    if (asciiLetter(value)) {
      const start = cursor++;
      while (cursor < source.length && identifierPart(source[cursor])) cursor += 1;
      assertLimit(cursor-start,120,"identifier length","SOURCE");
      push("identifier", start, cursor);
      continue;
    }
    if (asciiDigit(value)) {
      const start = cursor++;
      if (value === "0" && cursor < source.length && asciiDigit(source[cursor]))
        fail("PARSE_ERROR", "SOURCE", "Leading zero is not permitted", { sourceSpan: { start, end: cursor + 1 } });
      while (cursor < source.length && asciiDigit(source[cursor])) cursor += 1;
      if (source[cursor] === ".") {
        cursor += 1;
        if (!asciiDigit(source[cursor] ?? "")) fail("PARSE_ERROR", "SOURCE", "Fraction requires digits", { sourceSpan: { start, end: cursor } });
        while (cursor < source.length && asciiDigit(source[cursor])) cursor += 1;
      }
      if (source[cursor] === "e" || source[cursor] === "E") {
        cursor += 1;
        if (source[cursor] === "+" || source[cursor] === "-") cursor += 1;
        if (!asciiDigit(source[cursor] ?? "")) fail("PARSE_ERROR", "SOURCE", "Exponent requires digits", { sourceSpan: { start, end: cursor } });
        while (cursor < source.length && asciiDigit(source[cursor])) cursor += 1;
      }
      push("number", start, cursor);
      continue;
    }
    fail("UNSUPPORTED_TOKEN", "SOURCE", "Unsupported token", { sourceSpan: { start: cursor, end: cursor + 1 }, actual: value });
  }
  push("eof", cursor, cursor);
  return tokens;
}
