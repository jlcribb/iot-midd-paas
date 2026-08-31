import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import { withTransaction, type SqlExecutor, type TransactionRunner } from "@/lib/db/tx";
import { STRATEGY_CANDIDATE_GENERATOR_VERSION, type ControlStrategyCandidate, type CreateStrategySearchSpaceInput, type GeneratedSearchSpace, type StrategySearchSpace } from "@/lib/dto/strategy-candidate.dto";

function record(value: unknown): Record<string, unknown> { return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {}; }
function mapCandidate(row: QueryResultRow): ControlStrategyCandidate {
  return { id: String(row.id), project_id: String(row.project_id), search_space_id: String(row.search_space_id), strategy_type: String(row.strategy_type) as ControlStrategyCandidate["strategy_type"], parameters: record(row.parameters) as Record<string, number>, candidate_index: Number(row.candidate_index), candidate_hash: String(row.candidate_hash), source: "GRID_SEARCH", schema_version: 1, generator_version: String(row.generator_version), created_at: String(row.created_at) };
}
function mapSearchSpace(row: QueryResultRow, candidates?: ControlStrategyCandidate[]): StrategySearchSpace {
  return { id: String(row.id), project_id: String(row.project_id), name: String(row.name), description: String(row.description), strategy_type: String(row.strategy_type) as StrategySearchSpace["strategy_type"], parameter_schema_version: 1, generation_method: "GRID", search_space_definition: record(row.search_space_definition) as StrategySearchSpace["search_space_definition"], search_space_hash: String(row.search_space_hash), raw_combination_count: Number(row.raw_combination_count), candidate_count: Number(row.candidate_count), invalid_combination_count: Number(row.invalid_combination_count), invalid_combination_summary: Array.isArray(row.invalid_combination_summary) ? row.invalid_combination_summary as StrategySearchSpace["invalid_combination_summary"] : [], status: "GENERATED", schema_version: 1, generator_version: String(row.generator_version), created_by: String(row.created_by), created_at: String(row.created_at), ...(candidates ? { candidates } : {}) };
}

export class StrategySearchSpaceRepository {
  constructor(private readonly db: SqlExecutor = pool, private readonly transaction: TransactionRunner = withTransaction) {}

  async createOrGet(projectId: string, createdBy: string, input: CreateStrategySearchSpaceInput, generated: GeneratedSearchSpace): Promise<StrategySearchSpace> {
    return this.transaction(async (tx) => {
      const inserted = await tx.query(`INSERT INTO public.control_strategy_search_spaces (project_id,name,description,strategy_type,parameter_schema_version,generation_method,search_space_definition,search_space_hash,raw_combination_count,candidate_count,invalid_combination_count,invalid_combination_summary,status,schema_version,generator_version,created_by,physical_effects_allowed) VALUES ($1::uuid,$2,$3,$4,1,'GRID',$5::jsonb,$6,$7,$8,$9,$10::jsonb,'GENERATED',1,$11,$12,FALSE) ON CONFLICT (project_id,search_space_hash) DO NOTHING RETURNING id`, [projectId, input.name, input.description ?? "", input.strategy_type, JSON.stringify(generated.normalized_definition), generated.search_space_hash, generated.raw_combination_count, generated.candidates.length, generated.invalid_combination_count, JSON.stringify(generated.invalid_combination_summary), STRATEGY_CANDIDATE_GENERATOR_VERSION, createdBy]);
      const id = inserted.rows[0]?.id as string | undefined;
      if (!id) return this.requireByIdentity(tx, projectId, generated.search_space_hash);
      for (const candidate of generated.candidates) await tx.query(`INSERT INTO public.control_strategy_candidates (project_id,search_space_id,strategy_type,parameters,candidate_index,candidate_hash,source,schema_version,generator_version) VALUES ($1::uuid,$2::uuid,$3,$4::jsonb,$5,$6,'GRID_SEARCH',1,$7)`, [projectId, id, input.strategy_type, JSON.stringify(candidate.parameters), candidate.candidate_index, candidate.candidate_hash, STRATEGY_CANDIDATE_GENERATOR_VERSION]);
      await tx.query(`INSERT INTO iot_schema.auditoria (entidad,entidad_id,accion,cambios,contexto) VALUES ('control_strategy_search_spaces',$1::uuid,'STRATEGY_SEARCH_SPACE_CREATED',$2::jsonb,$3::jsonb)`, [id, JSON.stringify({ search_space_hash: generated.search_space_hash, strategy_type: input.strategy_type, generation_method: "GRID", raw_combination_count: generated.raw_combination_count, candidate_count: generated.candidates.length, invalid_combination_count: generated.invalid_combination_count }), JSON.stringify({ subsystem: "apps/topology-next", capability: "strategy-candidate-generator", project_id: projectId, actor_id: createdBy, execution_context: "SIMULATION", physical_effects: false })]);
      return this.requireById(tx, projectId, id);
    });
  }
  async listByProject(projectId: string): Promise<StrategySearchSpace[]> { const result = await this.db.query(this.searchQuery("WHERE s.project_id=$1::uuid"), [projectId]); return result.rows.map((row) => mapSearchSpace(row)); }
  async findByProjectAndId(projectId: string, id: string): Promise<StrategySearchSpace | null> { const result = await this.db.query(this.searchQuery("WHERE s.project_id=$1::uuid AND s.id=$2::uuid"), [projectId, id]); return result.rows[0] ? mapSearchSpace(result.rows[0]) : null; }
  async listCandidates(projectId: string, searchSpaceId: string): Promise<ControlStrategyCandidate[]> { const result = await this.db.query("SELECT * FROM public.control_strategy_candidates WHERE project_id=$1::uuid AND search_space_id=$2::uuid ORDER BY candidate_index", [projectId, searchSpaceId]); return result.rows.map(mapCandidate); }
  private async requireById(tx: SqlExecutor, projectId: string, id: string): Promise<StrategySearchSpace> { const result = await tx.query(this.searchQuery("WHERE s.project_id=$1::uuid AND s.id=$2::uuid"), [projectId, id]); return mapSearchSpace(result.rows[0]); }
  private async requireByIdentity(tx: SqlExecutor, projectId: string, hash: string): Promise<StrategySearchSpace> { const result = await tx.query(this.searchQuery("WHERE s.project_id=$1::uuid AND s.search_space_hash=$2"), [projectId, hash]); return mapSearchSpace(result.rows[0]); }
  private searchQuery(where: string): string { return `SELECT s.* FROM public.control_strategy_search_spaces s ${where} ORDER BY s.created_at DESC, s.id DESC`; }
}
