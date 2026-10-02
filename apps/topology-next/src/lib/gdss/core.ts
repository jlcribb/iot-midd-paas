import { createHash } from "node:crypto";
import { z } from "zod";

const text = z.string().min(1).max(2000);
const key = z.string().regex(/^[a-zA-Z][a-zA-Z0-9_]*$/).max(120);
const finite = z.number().finite();
const json: z.ZodType<unknown> = z.lazy(() => z.union([
  z.null(), z.boolean(), finite, z.string(), z.array(json), z.record(json)
]));
export const lifecycle = ["DRAFT", "VALIDATED", "EXPERIMENTAL", "APPROVED", "PUBLISHED", "DEPRECATED"] as const;
export type Lifecycle = typeof lifecycle[number];
export const provenanceSchema = z.object({
  kind: z.enum(["LITERATURE", "EMPIRICAL", "DERIVED", "CALIBRATED", "HUMAN_PROPOSED", "AI_PROPOSED"]),
  source_reference: z.string().max(2000).optional(),
  description: text,
  asserted_by: text,
  metadata: z.record(json).default({})
}).strict().superRefine((p, ctx) => {
  if (p.kind === "LITERATURE" && !p.source_reference?.trim())
    ctx.addIssue({ code: "custom", message: "Literature requires source_reference" });
});
export type Provenance = z.infer<typeof provenanceSchema>;
export const dimensionSchema = z.tuple([
  z.number().int(), z.number().int(), z.number().int(), z.number().int(),
  z.number().int(), z.number().int(), z.number().int()
]);
export const unitSchema = z.object({
  key, revision: z.number().int().positive(), symbol: text, name: text,
  dimension: dimensionSchema, scale: finite.positive(), offset: finite,
  canonical_unit: text
}).strict();
export type UnitDefinition = z.infer<typeof unitSchema>;
export type DimensionDefinition = z.infer<typeof dimensionSchema>;
const common = {
  symbol: key, label: text, description: z.string().max(10000),
  provenance: z.array(provenanceSchema).min(1).max(100)
};
export const componentSchema = z.object({ ...common, kind: z.literal("Component"), component_type: text, metadata: z.record(json).default({}) }).strict();
export const variableSchema = z.object({
  ...common, kind: z.literal("Variable"), unit_ref: key, dimension: dimensionSchema,
  computational_role: z.enum(["INPUT", "OUTPUT", "STATE", "AUXILIARY", "EXTERNAL"]),
  epistemic_kind: z.enum(["OBSERVED", "SIMULATED", "PREDICTED", "DERIVED", "CALIBRATED", "COUNTERFACTUAL"])
}).strict();
export const parameterSchema = z.object({
  ...common, kind: z.literal("Parameter"), unit_ref: key, dimension: dimensionSchema,
  default_value: finite, valid_range: z.tuple([finite, finite])
}).strict();
export const formulaSchema = z.object({
  ...common, kind: z.literal("Formula"), expression_source: text,
  input_refs: z.array(key).max(1000), output_ref: key, validity_domain: z.record(json)
}).strict();
export const constraintSchema = z.object({
  ...common, kind: z.literal("Constraint"),
  constraint_type: z.enum(["range", "compatibility", "required_relationship", "boundary_condition", "domain_validity"]),
  refs: z.array(key).max(1000), declaration: z.record(json)
}).strict();
export const boundarySchema = z.object({
  ...common, kind: z.literal("Boundary"), boundary_type: text,
  included_components: z.array(key).max(1000), external_interfaces: z.array(text).max(1000)
}).strict();
export const childSchema = z.discriminatedUnion("kind", [componentSchema, variableSchema, parameterSchema, formulaSchema, constraintSchema, boundarySchema]);
export type Child = z.infer<typeof childSchema>;
export type Component = z.infer<typeof componentSchema> & { model_version_id: string };
export type Variable = z.infer<typeof variableSchema> & { model_version_id: string };
export type Parameter = z.infer<typeof parameterSchema> & { model_version_id: string };
export type Formula = z.infer<typeof formulaSchema> & { model_version_id: string };
export type Constraint = z.infer<typeof constraintSchema> & { model_version_id: string };
export type Boundary = z.infer<typeof boundarySchema> & { model_version_id: string };
export const modelSchema = z.object({
  description: z.string().max(10000), validity_domain: z.record(json),
  provenance: z.array(provenanceSchema).min(1).max(100),
  units: z.array(unitSchema).min(1).max(1000),
  children: z.array(childSchema).max(1000)
}).strict();
export type ModelContent = z.infer<typeof modelSchema>;
export interface SystemModelIdentity {
  id: string; project_id: string; canonical_name: string; description: string; created_at: string; created_by: string;
}
export interface SystemModelVersion {
  id: string; identity_id: string; version_number: number; predecessor_version_id: string | null;
  lifecycle_status: Lifecycle; content_hash: string | null; content: ModelContent; created_by: string; created_at: string;
}
export interface LifecycleEvent {
  model_version_id: string; from_status: Lifecycle; to_status: Lifecycle;
  actor: string; timestamp: string; reason: string; metadata: Record<string, unknown>;
}
export function compatible(a: DimensionDefinition, b: DimensionDefinition) {
  return dimensionSchema.parse(a).every((v, i) => v === dimensionSchema.parse(b)[i]);
}
export function references(c: Child): string[] {
  if (c.kind === "Formula") return [...c.input_refs, c.output_ref];
  if (c.kind === "Constraint") return c.refs;
  if (c.kind === "Boundary") return c.included_components;
  return [];
}
export function validateContent(input: unknown): ModelContent {
  const m = modelSchema.parse(input);
  const children = new Map(m.children.map(c => [c.symbol, c]));
  const units = new Map(m.units.map(u => [u.key, u]));
  if (children.size !== m.children.length || units.size !== m.units.length) throw Error("Duplicate local key");
  for (const c of m.children) {
    for (const ref of references(c)) {
      const target = children.get(ref);
      if (!target) throw Error("Unresolved version-local reference");
      if (c.kind === "Boundary" && target.kind !== "Component") throw Error("Boundary requires components");
      if (c.kind === "Formula" && !["Variable", "Parameter"].includes(target.kind)) throw Error("Formula reference requires quantity");
    }
    if (c.kind === "Variable" || c.kind === "Parameter") {
      const unit = units.get(c.unit_ref);
      if (!unit || !compatible(c.dimension, unit.dimension)) throw Error("Incompatible unit declaration");
    }
    if (c.kind === "Parameter" && (c.valid_range[0] > c.valid_range[1] || c.default_value < c.valid_range[0] || c.default_value > c.valid_range[1]))
      throw Error("Invalid parameter range");
    if (c.kind === "Constraint" && c.constraint_type === "compatibility") {
      const quantities = c.refs.map(r => children.get(r)!);
      if (quantities.length < 2 || quantities.some(q => !("dimension" in q))) throw Error("Compatibility requires quantities");
      const dimensions = quantities.map(q => (q as z.infer<typeof variableSchema>).dimension);
      if (dimensions.some(d => !compatible(d, dimensions[0]))) throw Error("Incompatible dimensions");
    }
  }
  return m;
}
// Arrays are ordered by default. Only explicitly registered dependency sets are sorted.
export const canonicalizationRegistry = Object.freeze({
  children: "UNORDERED", units: "UNORDERED", provenance: "UNORDERED",
  input_refs: "UNORDERED_REFERENCE", refs: "UNORDERED_REFERENCE",
  included_components: "UNORDERED_REFERENCE", output_ref: "REFERENCE", unit_ref: "REFERENCE",
  valid_range: "ORDERED", external_interfaces: "ORDERED",
  dimension: "ORDERED", metadata_arrays: "ORDERED", validity_domain_arrays: "ORDERED",
  other_fields: "SCALAR_OR_OBJECT", technical_ids_and_lifecycle: "EXCLUDED"
});
function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([k, v]) => [k, stable(v)]));
  return value;
}
const encode = (v: unknown) => JSON.stringify(stable(v));
const sorted = <T>(values: T[]) => [...values].sort((a, b) => encode(a) < encode(b) ? -1 : encode(a) > encode(b) ? 1 : 0);
export function canonicalContent(input: unknown) {
  const m = validateContent(input);
  const normalized = {
    ...m, provenance: sorted(m.provenance), units: sorted(m.units),
    children: sorted(m.children.map(c => {
      const result = { ...c, provenance: sorted(c.provenance) };
      if (result.kind === "Formula") result.input_refs = [...new Set(result.input_refs)].sort();
      if (result.kind === "Constraint") result.refs = [...new Set(result.refs)].sort();
      if (result.kind === "Boundary") result.included_components = [...new Set(result.included_components)].sort();
      return result;
    }))
  };
  return encode(normalized);
}
export function contentHash(input: unknown) {
  return createHash("sha256").update(canonicalContent(input), "utf8").digest("hex");
}
export function nextStatus(current: Lifecycle): Lifecycle | undefined {
  return lifecycle[lifecycle.indexOf(current) + 1];
}
