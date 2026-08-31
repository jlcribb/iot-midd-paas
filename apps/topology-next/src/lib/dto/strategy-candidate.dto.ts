export const STRATEGY_CANDIDATE_GENERATOR_VERSION = "strategy-candidate-generator:v1";
export const STRATEGY_PARAMETER_SCHEMA_VERSION = 1 as const;
export const STRATEGY_SEARCH_SPACE_SCHEMA_VERSION = 1 as const;
export const MAX_GRID_CANDIDATES = 1000;

export type StrategyType = "proportional" | "threshold";
export type GenerationMethod = "GRID";
export type SearchSpaceStatus = "GENERATED";
export interface NumericValuesDomain { values: number[]; }
export interface NumericRangeDomain { min: number; max: number; step: number; }
export type ParameterDomain = NumericValuesDomain | NumericRangeDomain;
export type SearchSpaceDefinition = Record<string, ParameterDomain>;
export interface InvalidCombinationSummary { reason: string; count: number; }

export interface CreateStrategySearchSpaceInput {
  name: string; description?: string; strategy_type: StrategyType; generation_method: GenerationMethod;
  parameters: SearchSpaceDefinition;
}
export interface ControlStrategyCandidate {
  id: string; project_id: string; search_space_id: string; strategy_type: StrategyType;
  parameters: Record<string, number>; candidate_index: number; candidate_hash: string;
  source: "GRID_SEARCH"; schema_version: 1; generator_version: string; created_at: string;
}
export interface StrategySearchSpace {
  id: string; project_id: string; name: string; description: string; strategy_type: StrategyType;
  parameter_schema_version: 1; generation_method: GenerationMethod; search_space_definition: SearchSpaceDefinition;
  search_space_hash: string; raw_combination_count: number; candidate_count: number; invalid_combination_count: number;
  invalid_combination_summary: InvalidCombinationSummary[]; status: SearchSpaceStatus; schema_version: 1;
  generator_version: string; created_by: string; created_at: string; candidates?: ControlStrategyCandidate[];
}
export interface GeneratedSearchSpace {
  normalized_definition: SearchSpaceDefinition; search_space_hash: string; raw_combination_count: number;
  invalid_combination_count: number; invalid_combination_summary: InvalidCombinationSummary[];
  candidates: Array<{ candidate_index: number; parameters: Record<string, number>; candidate_hash: string }>;
}
