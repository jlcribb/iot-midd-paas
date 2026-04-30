import type { SqlExecutor } from "@/lib/db/tx";
import { pool } from "@/lib/db/pool";
import type { IControlPolicyAuditRepository } from "@/lib/repositories/contracts";

export class ControlPolicyAuditRepository implements IControlPolicyAuditRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async recordChange(entry: {
    entityId: string;
    action: "CONTROL_POLICY_CREATED" | "CONTROL_POLICY_UPDATED" | "CONTROL_POLICY_DISABLED";
    before: unknown;
    after: unknown;
    context?: Record<string, unknown>;
  }): Promise<void> {
    await this.db.query(
      `
      INSERT INTO iot_schema.auditoria (
        entidad,
        entidad_id,
        accion,
        cambios,
        contexto
      )
      VALUES ($1, $2::uuid, $3, $4::jsonb, $5::jsonb)
      `,
      [
        "project_control_policies",
        entry.entityId,
        entry.action,
        JSON.stringify({
          antes: entry.before,
          despues: entry.after
        }),
        JSON.stringify({
          subsystem: "apps/topology-next",
          capability: "control-policy-management",
          ...(entry.context ?? {})
        })
      ]
    );
  }
}
