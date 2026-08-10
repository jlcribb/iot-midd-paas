import type { SqlExecutor } from "@/lib/db/tx";
import type { ControlActor } from "@/lib/dto/control-access.dto";

export class ProjectControlGovernanceAuditRepository {
  constructor(private readonly db: SqlExecutor) {}

  async recordParametricControlChange(entry: {
    projectId: string;
    actor: ControlActor;
    before: boolean;
    after: boolean;
    correlationId?: string | null;
  }): Promise<void> {
    const timestamp = new Date().toISOString();
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
        "projects",
        entry.projectId,
        "PARAMETRIC_CONTROL_ENABLED_CHANGED",
        JSON.stringify({
          antes: { parametric_control_enabled: entry.before },
          despues: { parametric_control_enabled: entry.after },
          resultado: "changed"
        }),
        JSON.stringify({
          subsystem: "apps/topology-next",
          capability: "project-control-governance",
          project_id: entry.projectId,
          actor: {
            actor_id: entry.actor.actor_id ?? entry.actor.user_id,
            email: entry.actor.email ?? null,
            role: entry.actor.role,
            auth_source: entry.actor.auth_source ?? null
          },
          correlation_id: entry.correlationId ?? null,
          occurred_at: timestamp
        })
      ]
    );
  }
}
