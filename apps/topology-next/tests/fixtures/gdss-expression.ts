import type { ModelContent, Provenance, UnitDefinition } from "@/lib/gdss/core";
import { EVALUATOR_VERSION, EXPRESSION_LANGUAGE_VERSION, RESOURCE_LIMITS_PROFILE, UNIT_CONVERSION_CATALOG, UNIT_CONVERSION_CATALOG_VERSION, type EvaluationContext } from "@/lib/gdss/expression";

const provenance: Provenance[] = [{ kind:"HUMAN_PROPOSED", description:"GDSS-002 neutral test fixture", asserted_by:"test", metadata:{} }];
const unit = (key: string): UnitDefinition => {
  const found = UNIT_CONVERSION_CATALOG[`${key}@1`];
  if (!found) throw Error(`Unknown fixture unit ${key}`);
  const { quantitySemantics: _quantitySemantics, affineFamily: _affineFamily, ...definition } = found;
  return structuredClone(definition);
};
const variable = (symbol:string, unitKey:string, role:"INPUT"|"OUTPUT" = "INPUT") => ({ kind:"Variable" as const, symbol, label:symbol, description:"", provenance, unit_ref:unitKey, dimension:unit(unitKey).dimension, computational_role:role, epistemic_kind:"DERIVED" as const });
const formula = (symbol:string, expression_source:string, input_refs:string[], output_ref:string) => ({ kind:"Formula" as const, symbol, label:symbol, description:"", provenance, expression_source, input_refs, output_ref, validity_domain:{} });

export function expressionFixture(domain: "hydroponic" | "thermal"): ModelContent {
  if (domain === "hydroponic") return {
    description:"Neutral fluid geometry fixture", validity_domain:{}, provenance,
    units:[unit("square_meter"),unit("meter_per_second"),unit("cubic_meter_per_second")],
    children:[
      variable("cross_section_area","square_meter"), variable("fluid_velocity","meter_per_second"), variable("flow_rate","cubic_meter_per_second","OUTPUT"),
      formula("flow_formula","cross_section_area * fluid_velocity",["cross_section_area","fluid_velocity"],"flow_rate")
    ]
  };
  return {
    description:"Neutral heat transfer fixture", validity_domain:{}, provenance,
    units:[unit("watt_per_square_meter_kelvin"),unit("square_meter"),unit("kelvin"),unit("watt")],
    children:[
      variable("thermal_transmittance","watt_per_square_meter_kelvin"), variable("area","square_meter"), variable("temperature_difference","kelvin"), variable("heat_loss","watt","OUTPUT"),
      formula("heat_formula","thermal_transmittance * area * temperature_difference",["thermal_transmittance","area","temperature_difference"],"heat_loss")
    ]
  };
}

export function affineFixture(expression: "convert" | "subtract" | "add" | "absolute_add"): ModelContent {
  const expression_source = expression === "convert" ? "temperature" : expression === "subtract" ? "hot - cold" : "base + change";
  const input_refs = expression === "convert" ? ["temperature"] : expression === "subtract" ? ["hot","cold"] : ["base","change"];
  const output = expression === "convert" ? variable("result","kelvin","OUTPUT") : variable("result","celsius","OUTPUT");
  return {
    description:"Affine semantic fixture", validity_domain:{}, provenance, units:[unit("celsius"),unit("kelvin")],
    children:[variable("temperature","celsius"),variable("hot","celsius"),variable("cold","celsius"),variable("base","celsius"),variable("change","celsius"),output,formula("affine_formula",expression_source,input_refs,"result")]
  };
}

export function context(modelVersionId:string, formulaSymbol:string, inputs:EvaluationContext["inputs"], extra:Partial<EvaluationContext> = {}): EvaluationContext {
  return { projectId:"00000000-0000-4000-8000-000000000001", modelVersionId, formulaSymbol, expressionLanguageVersion:EXPRESSION_LANGUAGE_VERSION, evaluatorVersion:EVALUATOR_VERSION, conversionCatalogVersion:UNIT_CONVERSION_CATALOG_VERSION, resourceLimitsProfile:RESOURCE_LIMITS_PROFILE, inputs, ...extra };
}
