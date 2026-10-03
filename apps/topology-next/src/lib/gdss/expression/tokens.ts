import type { SourceSpan } from "./diagnostics";

export type TokenKind = "number" | "identifier" | "plus" | "minus" | "star" | "slash" | "caret" | "lparen" | "rparen" | "comma" | "eof";
export interface Token { kind: TokenKind; lexeme: string; span: SourceSpan }
