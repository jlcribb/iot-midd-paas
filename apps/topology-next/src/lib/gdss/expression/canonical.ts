import { createHash } from "node:crypto";
import type { ASTNode } from "./ast";

export function binary64Hex(value: number): string {
  const normalized = Object.is(value, -0) ? 0 : value;
  if (!Number.isFinite(normalized)) throw new Error("Canonical numbers must be finite");
  const bytes = new ArrayBuffer(8);
  new DataView(bytes).setFloat64(0, normalized, false);
  return [...new Uint8Array(bytes)].map(byte => byte.toString(16).padStart(2,"0")).join("");
}

export function stableValue(value: unknown): unknown {
  if (typeof value === "number") return { $binary64: binary64Hex(value) };
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).sort(([a],[b]) => a.localeCompare(b)).map(([key,item]) => [key, stableValue(item)]));
  return value;
}

export const canonicalJson = (value: unknown) => JSON.stringify(stableValue(value));
export const derivedHash = (schema: string, value: unknown) => createHash("sha256").update(canonicalJson({ schema, value }), "utf8").digest("hex");
export const canonicalAst = (ast: ASTNode) => canonicalJson(ast);
export const expressionAstHash = (ast: ASTNode) => derivedHash("gdss-expr-ast:v1", ast);
