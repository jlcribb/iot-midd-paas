import type { DimensionDefinition } from "@/lib/gdss/core";
import { fail, type SourceSpan } from "./diagnostics";

export const DIMENSIONLESS: DimensionDefinition = [0,0,0,0,0,0,0];

export function assertKnownDimension(value: unknown, span?: SourceSpan): DimensionDefinition {
  if (!Array.isArray(value) || value.length !== 7 || value.some(item => !Number.isInteger(item)))
    fail("UNKNOWN_OR_MISSING_DIMENSION", "DIMENSIONALLY_VALIDATED", "Dimension must contain seven integer exponents", { sourceSpan: span, actual: value });
  return value as DimensionDefinition;
}

export function dimensionsEqual(left: DimensionDefinition, right: DimensionDefinition) {
  return left.every((value,index) => value === right[index]);
}

export function compatibleForAddSubtract(left: DimensionDefinition, right: DimensionDefinition, span?: SourceSpan) {
  if (!dimensionsEqual(left,right)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Addition/subtraction requires equal dimensions", { sourceSpan: span, expected: left, actual: right });
  return left;
}

function combine(left: DimensionDefinition, right: DimensionDefinition, sign: 1 | -1): DimensionDefinition {
  return left.map((value,index) => {
    const result = value + sign * right[index];
    if (!Number.isSafeInteger(result)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Dimension exponent is not representable", { actual: result });
    return result;
  }) as DimensionDefinition;
}

export const multiplyDimensions = (left: DimensionDefinition, right: DimensionDefinition) => combine(left,right,1);
export const divideDimensions = (left: DimensionDefinition, right: DimensionDefinition) => combine(left,right,-1);

export function powerDimension(base: DimensionDefinition, exponent: number, span?: SourceSpan): DimensionDefinition {
  if (!Number.isSafeInteger(exponent)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Dimensioned power requires an integer literal exponent", { sourceSpan: span, actual: exponent });
  return base.map(value => {
    const result = value * exponent;
    if (!Number.isSafeInteger(result)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "Powered dimension is not representable", { sourceSpan: span, actual: result });
    return result;
  }) as DimensionDefinition;
}

export function sqrtDimension(value: DimensionDefinition, span?: SourceSpan): DimensionDefinition {
  if (value.some(exponent => exponent % 2 !== 0)) fail("DIMENSION_MISMATCH", "DIMENSIONALLY_VALIDATED", "sqrt requires even dimensional exponents", { sourceSpan: span, actual: value });
  return value.map(exponent => exponent / 2) as DimensionDefinition;
}

export const isDimensionless = (value: DimensionDefinition) => dimensionsEqual(value,DIMENSIONLESS);
