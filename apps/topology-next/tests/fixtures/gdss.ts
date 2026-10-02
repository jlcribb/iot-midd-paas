import type { ModelContent } from "@/lib/gdss/core";
export function fixture(domain: "hydroponic" | "thermal"): ModelContent {
  const provenance = [{ kind: "AI_PROPOSED" as const, description: "Illustrative declaration; no scientific claim", asserted_by: "fixture", metadata: {} }];
  const symbol = domain === "hydroponic" ? "nutrient_solution" : "room";
  const temperature = domain === "hydroponic" ? "water_temperature" : "internal_temperature";
  const dimension: [number,number,number,number,number,number,number] = [0,0,0,0,1,0,0];
  return {
    description: domain, validity_domain: { assumptions: ["illustrative", "not calibrated"] }, provenance,
    units: [{ key: "kelvin", revision: 1, symbol: "K", name: "kelvin", dimension, scale: 1, offset: 0, canonical_unit: "K" }],
    children: [
      { kind: "Component", symbol, label: symbol, description: "", component_type: symbol, provenance, metadata: {} },
      { kind: "Variable", symbol: temperature, label: temperature, description: "", provenance, unit_ref: "kelvin", dimension, computational_role: "INPUT", epistemic_kind: "OBSERVED" },
      { kind: "Parameter", symbol: "reference", label: "Reference", description: "", provenance, unit_ref: "kelvin", dimension, default_value: 295, valid_range: [270,310] },
      { kind: "Formula", symbol: "relation", label: "Relation", description: "", provenance, expression_source: temperature + " - reference", input_refs: [temperature,"reference"], output_ref: temperature, validity_domain: {} },
      { kind: "Constraint", symbol: "compatible", label: "Dimensions", description: "", provenance, constraint_type: "compatibility", refs: [temperature,"reference"], declaration: {} },
      { kind: "Boundary", symbol: "system", label: "System", description: "", provenance, boundary_type: "conceptual", included_components: [symbol], external_interfaces: [] }
    ]
  };
}
