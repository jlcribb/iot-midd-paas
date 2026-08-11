import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import type { ControlPolicyActuationBinding, ControlOperation } from "@/lib/dto/control-policy.dto";

export type ActuationBindingInput = Pick<ControlPolicyActuationBinding, "target_asset_id" | "control_point" | "operation">;

function mapBinding(row: QueryResultRow): ControlPolicyActuationBinding {
  return {
    id: String(row.actuation_binding_id ?? row.id),
    source_asset_id: String(row.source_asset_id),
    target_asset_id: String(row.target_asset_id),
    control_point: String(row.control_point),
    operation: String(row.operation) as ControlOperation,
    enabled: Boolean(row.actuation_binding_enabled ?? row.enabled),
    version: Number(row.actuation_binding_version ?? row.version),
    created_at: String(row.actuation_binding_created_at ?? row.created_at),
    updated_at: String(row.actuation_binding_updated_at ?? row.updated_at)
  };
}

export class ControlPolicyActuationBindingRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async findByPolicyId(policyId: string): Promise<ControlPolicyActuationBinding | null> {
    const result = await this.db.query(
      "SELECT * FROM public.project_control_policy_actuation_bindings WHERE policy_id = $1::uuid",
      [policyId]
    );
    return result.rows[0] ? mapBinding(result.rows[0]) : null;
  }

  async upsert(args: { policyId: string; projectId: string; sourceAssetId: string; input: ActuationBindingInput }): Promise<ControlPolicyActuationBinding> {
    const result = await this.db.query(
      `
      INSERT INTO public.project_control_policy_actuation_bindings (
        policy_id, project_id, source_asset_id, target_asset_id, control_point, operation
      ) VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6)
      ON CONFLICT (policy_id) DO UPDATE SET
        project_id = EXCLUDED.project_id,
        source_asset_id = EXCLUDED.source_asset_id,
        target_asset_id = EXCLUDED.target_asset_id,
        control_point = EXCLUDED.control_point,
        operation = EXCLUDED.operation,
        enabled = TRUE,
        version = public.project_control_policy_actuation_bindings.version + 1
      RETURNING *
      `,
      [args.policyId, args.projectId, args.sourceAssetId, args.input.target_asset_id, args.input.control_point, args.input.operation]
    );
    return mapBinding(result.rows[0]);
  }

  async remove(policyId: string): Promise<ControlPolicyActuationBinding | null> {
    const result = await this.db.query(
      "DELETE FROM public.project_control_policy_actuation_bindings WHERE policy_id = $1::uuid RETURNING *",
      [policyId]
    );
    return result.rows[0] ? mapBinding(result.rows[0]) : null;
  }
}
