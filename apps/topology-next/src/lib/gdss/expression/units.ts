import type { DimensionDefinition, UnitDefinition } from "@/lib/gdss/core";
import { fail, type SourceSpan } from "./diagnostics";
import { dimensionsEqual } from "./dimensions";
import { UNIT_CONVERSION_CATALOG_VERSION } from "./versions";

export type QuantitySemantics = "ABSOLUTE" | "INTERVAL";
export interface UnitIdentity { key: string; revision: number }
export interface CatalogUnit extends UnitDefinition {
  quantitySemantics: readonly QuantitySemantics[];
  affineFamily: boolean;
}

const L: DimensionDefinition = [1,0,0,0,0,0,0];
const AREA: DimensionDefinition = [2,0,0,0,0,0,0];
const VELOCITY: DimensionDefinition = [1,0,-1,0,0,0,0];
const FLOW: DimensionDefinition = [3,0,-1,0,0,0,0];
const TEMPERATURE: DimensionDefinition = [0,0,0,1,0,0,0];
const TRANSMITTANCE: DimensionDefinition = [0,1,-3,-1,0,0,0];
const POWER: DimensionDefinition = [2,1,-3,0,0,0,0];
const LINEAR = ["INTERVAL"] as const;
const AFFINE = ["ABSOLUTE","INTERVAL"] as const;

export const UNIT_CONVERSION_CATALOG: Readonly<Record<string,CatalogUnit>> = Object.freeze({
  "meter@1": { key:"meter", revision:1, symbol:"m", name:"meter", dimension:L, scale:1, offset:0, canonical_unit:"meter", quantitySemantics:LINEAR, affineFamily:false },
  "centimeter@1": { key:"centimeter", revision:1, symbol:"cm", name:"centimeter", dimension:L, scale:0.01, offset:0, canonical_unit:"meter", quantitySemantics:LINEAR, affineFamily:false },
  "square_meter@1": { key:"square_meter", revision:1, symbol:"m2", name:"square meter", dimension:AREA, scale:1, offset:0, canonical_unit:"square_meter", quantitySemantics:LINEAR, affineFamily:false },
  "meter_per_second@1": { key:"meter_per_second", revision:1, symbol:"m/s", name:"meter per second", dimension:VELOCITY, scale:1, offset:0, canonical_unit:"meter_per_second", quantitySemantics:LINEAR, affineFamily:false },
  "cubic_meter_per_second@1": { key:"cubic_meter_per_second", revision:1, symbol:"m3/s", name:"cubic meter per second", dimension:FLOW, scale:1, offset:0, canonical_unit:"cubic_meter_per_second", quantitySemantics:LINEAR, affineFamily:false },
  "kelvin@1": { key:"kelvin", revision:1, symbol:"K", name:"kelvin", dimension:TEMPERATURE, scale:1, offset:0, canonical_unit:"kelvin", quantitySemantics:AFFINE, affineFamily:true },
  "celsius@1": { key:"celsius", revision:1, symbol:"degC", name:"degree Celsius", dimension:TEMPERATURE, scale:1, offset:273.15, canonical_unit:"kelvin", quantitySemantics:AFFINE, affineFamily:true },
  "watt_per_square_meter_kelvin@1": { key:"watt_per_square_meter_kelvin", revision:1, symbol:"W/(m2*K)", name:"watt per square meter kelvin", dimension:TRANSMITTANCE, scale:1, offset:0, canonical_unit:"watt_per_square_meter_kelvin", quantitySemantics:LINEAR, affineFamily:false },
  "watt@1": { key:"watt", revision:1, symbol:"W", name:"watt", dimension:POWER, scale:1, offset:0, canonical_unit:"watt", quantitySemantics:LINEAR, affineFamily:false }
});

const catalogKey = (identity: UnitIdentity) => `${identity.key}@${identity.revision}`;
export function catalogUnit(identity: UnitIdentity, span?: SourceSpan): CatalogUnit {
  const unit = UNIT_CONVERSION_CATALOG[catalogKey(identity)];
  if (!unit) fail("INVALID_INPUT_UNIT", "DIMENSIONALLY_VALIDATED", "Unit is not supported by the closed conversion catalog", { sourceSpan: span, actual: identity, expected: UNIT_CONVERSION_CATALOG_VERSION });
  return unit;
}

export function assertModelUnit(definition: UnitDefinition, span?: SourceSpan): CatalogUnit {
  const expected = catalogUnit(definition,span);
  const fields: (keyof UnitDefinition)[] = ["key","revision","symbol","name","scale","offset","canonical_unit"];
  if (fields.some(field => definition[field] !== expected[field]) || !dimensionsEqual(definition.dimension,expected.dimension))
    fail("INVALID_INPUT_UNIT", "DIMENSIONALLY_VALIDATED", "Model unit does not match the versioned conversion catalog", { sourceSpan: span, expected, actual: definition });
  return expected;
}

export function assertQuantitySemantics(unit: CatalogUnit, semantics: QuantitySemantics | undefined, span?: SourceSpan) {
  if (unit.affineFamily && !semantics) fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Affine unit requires explicit quantity semantics", { sourceSpan: span, expected: unit.quantitySemantics });
  const resolved = semantics ?? "INTERVAL";
  if (!unit.quantitySemantics.includes(resolved)) fail("AFFINE_QUANTITY_ERROR", "DIMENSIONALLY_VALIDATED", "Quantity semantics are not supported by unit", { sourceSpan: span, expected: unit.quantitySemantics, actual: resolved });
  return resolved;
}

export function toCanonical(value: number, unit: CatalogUnit, semantics: QuantitySemantics): number {
  return semantics === "ABSOLUTE" ? value * unit.scale + unit.offset : value * unit.scale;
}

export function fromCanonical(value: number, unit: CatalogUnit, semantics: QuantitySemantics): number {
  return semantics === "ABSOLUTE" ? (value - unit.offset) / unit.scale : value / unit.scale;
}

export function assertConvertible(source: CatalogUnit, target: CatalogUnit) {
  if (!dimensionsEqual(source.dimension,target.dimension) || source.canonical_unit !== target.canonical_unit)
    fail("INVALID_INPUT_UNIT", "DIMENSIONALLY_VALIDATED", "Units do not belong to the same conversion family", { expected: source.canonical_unit, actual: target.canonical_unit });
}
