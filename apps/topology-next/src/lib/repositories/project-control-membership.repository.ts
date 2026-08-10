import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import type { ProjectControlMembership } from "@/lib/dto/project-control-membership.dto";

function mapMembership(row: QueryResultRow): ProjectControlMembership {
  return {
    actor_email: String(row.actor_email),
    project_id: String(row.project_id),
    role: row.role as ProjectControlMembership["role"],
    enabled: Boolean(row.enabled)
  };
}

export class ProjectControlMembershipRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async findActiveByActorEmail(actorEmail: string): Promise<ProjectControlMembership[]> {
    const result = await this.db.query(
      `
      SELECT actor_email, project_id, role, enabled
      FROM public.project_control_memberships
      WHERE actor_email = $1
        AND enabled = TRUE
      ORDER BY project_id ASC
      `,
      [actorEmail.trim().toLowerCase()]
    );
    return result.rows.map(mapMembership);
  }
}
