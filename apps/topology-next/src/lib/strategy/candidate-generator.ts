import { canonicalNumber } from "@/lib/evaluation/normalization";
import { sha256Canonical } from "@/lib/simulation/canonical";
import { MAX_GRID_CANDIDATES, STRATEGY_CANDIDATE_GENERATOR_VERSION, STRATEGY_PARAMETER_SCHEMA_VERSION, STRATEGY_SEARCH_SPACE_SCHEMA_VERSION, type GeneratedSearchSpace, type ParameterDomain, type SearchSpaceDefinition, type StrategyType } from "@/lib/dto/strategy-candidate.dto";
import { ValidationError } from "@/lib/errors/domain-errors";

const SCALE = 1_000_000_000;
const schemas: Record<StrategyType, { required: string[]; optional: string[] }> = {
  proportional: { required: ["gain", "setpoint_value"], optional: ["deadband", "min_action", "max_action"] },
  threshold: { required: ["tolerance", "increase_step", "decrease_step"], optional: ["hold_signal"] }
};
function scaled(value: number): bigint { if (!Number.isFinite(value)) throw new ValidationError("Search-space numbers must be finite"); return BigInt(Math.round(canonicalNumber(value) * SCALE)); }
function unscaled(value: bigint): number { return canonicalNumber(Number(value) / SCALE); }
function domainValues(domain: ParameterDomain): number[] {
  if ("values" in domain) {
    if (!Array.isArray(domain.values) || domain.values.length === 0) throw new ValidationError("Explicit parameter values must be non-empty");
    return [...new Set(domain.values.map((value) => canonicalNumber(value)))].sort((a, b) => a - b);
  }
  const min = scaled(domain.min); const max = scaled(domain.max); const step = scaled(domain.step);
  if (step <= 0n) throw new ValidationError("Range step must be greater than zero");
  if (min > max) throw new ValidationError("Range min must not exceed max");
  if ((max - min) % step !== 0n) throw new ValidationError("Inclusive range max must align exactly with step");
  const values: number[] = []; for (let value = min; value <= max; value += step) values.push(unscaled(value)); return values;
}

export function normalizeSearchSpace(strategyType: StrategyType, definition: SearchSpaceDefinition): SearchSpaceDefinition {
  const schema = schemas[strategyType]; const keys = Object.keys(definition).sort();
  if (keys.length === 0) throw new ValidationError("A search space requires at least one parameter domain");
  for (const required of schema.required) if (!keys.includes(required)) throw new ValidationError(`${strategyType} requires ${required}`);
  for (const key of keys) if (!schema.required.includes(key) && !schema.optional.includes(key)) throw new ValidationError(`${key} is not supported by ${strategyType}`);
  return Object.fromEntries(keys.map((key) => [key, { values: domainValues(definition[key]) }]));
}
export function validateCandidateCombination(strategyType: StrategyType, parameters: Record<string, number>): string | null {
  if (strategyType === "proportional") {
    if (!(parameters.gain > 0)) return "gain_must_be_positive";
    if (parameters.deadband !== undefined && parameters.deadband < 0) return "deadband_must_be_non_negative";
    if (parameters.min_action !== undefined && parameters.min_action < 0) return "min_action_must_be_non_negative";
    if (parameters.max_action !== undefined && parameters.max_action < 0) return "max_action_must_be_non_negative";
    if (parameters.max_action !== undefined && parameters.min_action !== undefined && parameters.min_action > parameters.max_action) return "min_action_must_not_exceed_max_action";
    return null;
  }
  if (parameters.tolerance < 0) return "tolerance_must_be_non_negative";
  if (!(parameters.increase_step > 0)) return "increase_step_must_be_positive";
  if (!(parameters.decrease_step > 0)) return "decrease_step_must_be_positive";
  return null;
}
export function hashSearchSpace(strategyType: StrategyType, definition: SearchSpaceDefinition): string {
  return sha256Canonical({ schema_version: STRATEGY_SEARCH_SPACE_SCHEMA_VERSION, strategy_type: strategyType,
    parameter_schema_version: STRATEGY_PARAMETER_SCHEMA_VERSION, generation_method: "GRID", generator_version: STRATEGY_CANDIDATE_GENERATOR_VERSION,
    search_space_definition: definition });
}
export function hashCandidate(strategyType: StrategyType, parameters: Record<string, number>): string {
  return sha256Canonical({ schema_version: STRATEGY_SEARCH_SPACE_SCHEMA_VERSION, strategy_type: strategyType,
    parameter_schema_version: STRATEGY_PARAMETER_SCHEMA_VERSION, parameters });
}
export function generateGridSearch(strategyType: StrategyType, definition: SearchSpaceDefinition, maximum = MAX_GRID_CANDIDATES): GeneratedSearchSpace {
  const normalized_definition = normalizeSearchSpace(strategyType, definition); const names = Object.keys(normalized_definition).sort();
  const domains = names.map((name) => (normalized_definition[name] as { values: number[] }).values);
  const raw_combination_count = domains.reduce((count, values) => count * values.length, 1);
  if (raw_combination_count > maximum) throw new ValidationError(`SEARCH_SPACE_TOO_LARGE: ${raw_combination_count} exceeds ${maximum}`);
  const invalid = new Map<string, number>(); const candidates: GeneratedSearchSpace["candidates"] = [];
  const visit = (index: number, current: Record<string, number>) => {
    if (index === names.length) { const parameters = Object.fromEntries(names.map((name) => [name, current[name]])); const reason = validateCandidateCombination(strategyType, parameters);
      if (reason) invalid.set(reason, (invalid.get(reason) ?? 0) + 1); else candidates.push({ candidate_index: candidates.length + 1, parameters, candidate_hash: hashCandidate(strategyType, parameters) }); return; }
    for (const value of domains[index]) visit(index + 1, { ...current, [names[index]]: value });
  };
  visit(0, {});
  return { normalized_definition, search_space_hash: hashSearchSpace(strategyType, normalized_definition), raw_combination_count,
    invalid_combination_count: raw_combination_count - candidates.length,
    invalid_combination_summary: [...invalid.entries()].sort(([left], [right]) => left.localeCompare(right)).map(([reason, count]) => ({ reason, count })), candidates };
}
