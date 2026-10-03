import { z } from "zod";
import type { PoolClient } from "pg";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { canAccessProject, getControlRoleForProject } from "@/lib/auth/control-access";
import { ForbiddenError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import { canonicalContent, contentHash, nextStatus, type Lifecycle, type SystemModelVersion } from "./core";

const uuid = z.string().uuid();
const nonempty = z.string().trim().min(1).max(2000);
export type GdssOperation = "read" | "create" | "edit" | "validate" | "experimental" | "approve" | "publish" | "deprecate" | "successor" | "evaluate";
export const GDSS_EVALUATE_CAPABILITY = "EVALUATE_MODEL" as const;
export function assertGdssAccess(actor: ControlActor, projectId: string, operation: GdssOperation) {
  uuid.parse(projectId);
  if (actor.auth_source !== "oauth_session" || !actor.user_id || !canAccessProject(actor, projectId))
    throw new ForbiddenError("GDSS requires scoped authenticated membership");
  const role = getControlRoleForProject(actor, projectId);
  if (operation !== "read" && role === "viewer") throw new ForbiddenError("GDSS editing denied");
  if (["approve", "publish", "deprecate"].includes(operation) && role !== "admin")
    throw new ForbiddenError("GDSS publication authority required");
}
const transitionPermission: Record<Exclude<Lifecycle, "DRAFT">, GdssOperation> = {
  VALIDATED: "validate", EXPERIMENTAL: "experimental", APPROVED: "approve", PUBLISHED: "publish", DEPRECATED: "deprecate"
};
export class GdssService {
  constructor(private readonly transaction: TransactionRunner = withTransaction) {}

  private async identity(tx: PoolClient, project: string, id: string) {
    uuid.parse(id);
    const result = await tx.query("SELECT * FROM public.gdss_identity WHERE id=$1 AND project_id=$2 FOR UPDATE", [id, project]);
    if (!result.rows[0]) throw new NotFoundError("GDSS model not found");
    return result.rows[0];
  }
  private async version(tx: PoolClient, project: string, id: string): Promise<SystemModelVersion> {
    uuid.parse(id);
    const result = await tx.query(
      "SELECT v.* FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=$1 AND i.project_id=$2 FOR UPDATE OF v",
      [id, project]);
    if (!result.rows[0]) throw new NotFoundError("GDSS version not found");
    return result.rows[0] as SystemModelVersion;
  }
  private async audit(tx: PoolClient, project: string, id: string, actor: ControlActor, action: string, details: unknown) {
    await tx.query(
      "INSERT INTO iot_schema.auditoria(entidad,entidad_id,accion,cambios,contexto) VALUES('gdss',$1::uuid,$2,$3::jsonb,$4::jsonb)",
      [id, action, JSON.stringify(details), JSON.stringify({ project_id: project, actor: actor.user_id, capability: "A1", subsystem: "gdss" })]);
  }
  async createModelIdentity(actor: ControlActor, project: string, input: unknown) {
    assertGdssAccess(actor, project, "create");
    const data = z.object({ canonical_name: nonempty, description: z.string().max(10000) }).strict().parse(input);
    return this.transaction(async tx => {
      const result = await tx.query(
        "INSERT INTO public.gdss_identity(project_id,canonical_name,description,created_by) VALUES($1,$2,$3,$4) RETURNING *",
        [project, data.canonical_name, data.description, actor.user_id]);
      await this.audit(tx, project, result.rows[0].id, actor, "GDSS_IDENTITY_CREATED", data);
      return result.rows[0];
    });
  }
  async createDraftVersion(actor: ControlActor, project: string, identityId: string, input: unknown) {
    assertGdssAccess(actor, project, "create");
    const content = canonicalContent(input);
    return this.transaction(async tx => {
      await this.identity(tx, project, identityId);
      const result = await tx.query(
        "INSERT INTO public.gdss_version(identity_id,version_number,content,created_by) SELECT $1,COALESCE(MAX(version_number),0)+1,$2::jsonb,$3 FROM public.gdss_version WHERE identity_id=$1 RETURNING *",
        [identityId, content, actor.user_id]);
      await this.audit(tx, project, result.rows[0].id, actor, "GDSS_DRAFT_CREATED", { identityId });
      return result.rows[0] as SystemModelVersion;
    });
  }
  async updateDraft(actor: ControlActor, project: string, versionId: string, input: unknown) {
    assertGdssAccess(actor, project, "edit");
    const content = canonicalContent(input);
    return this.transaction(async tx => {
      const version = await this.version(tx, project, versionId);
      if (version.lifecycle_status !== "DRAFT") throw new ValidationError("GDSS content frozen");
      const result = await tx.query("UPDATE public.gdss_version SET content=$2::jsonb WHERE id=$1 RETURNING *", [versionId, content]);
      await this.audit(tx, project, versionId, actor, "GDSS_DRAFT_UPDATED", { before: version.content, after: JSON.parse(content) });
      return result.rows[0] as SystemModelVersion;
    });
  }
  async transition(actor: ControlActor, project: string, versionId: string, target: Exclude<Lifecycle, "DRAFT">, reason: string) {
    z.enum(["VALIDATED", "EXPERIMENTAL", "APPROVED", "PUBLISHED", "DEPRECATED"]).parse(target);
    assertGdssAccess(actor, project, transitionPermission[target]);
    nonempty.parse(reason);
    return this.transaction(async tx => {
      const version = await this.version(tx, project, versionId);
      if (nextStatus(version.lifecycle_status) !== target) throw new ValidationError("GDSS illegal lifecycle transition");
      const canonical = canonicalContent(version.content);
      const hash = contentHash(version.content);
      const result = await tx.query(
        "UPDATE public.gdss_version SET lifecycle_status=$2,canonical_content=$3,content_hash=$4 WHERE id=$1 RETURNING *",
        [versionId, target, canonical, hash]);
      await tx.query(
        "INSERT INTO public.gdss_lifecycle_event(model_version_id,from_status,to_status,actor,reason) VALUES($1,$2,$3,$4,$5)",
        [versionId, version.lifecycle_status, target, actor.user_id, reason.trim()]);
      await this.audit(tx, project, versionId, actor, "GDSS_LIFECYCLE_TRANSITION", { from: version.lifecycle_status, to: target, content_hash: hash, reason });
      return result.rows[0] as SystemModelVersion;
    });
  }
  async createSuccessor(actor: ControlActor, project: string, versionId: string) {
    assertGdssAccess(actor, project, "successor");
    return this.transaction(async tx => {
      const original = await this.version(tx, project, versionId);
      await this.identity(tx, project, original.identity_id);
      const result = await tx.query(
        "INSERT INTO public.gdss_version(identity_id,version_number,predecessor_version_id,content,created_by) SELECT $1,COALESCE(MAX(version_number),0)+1,$2,$3::jsonb,$4 FROM public.gdss_version WHERE identity_id=$1 RETURNING *",
        [original.identity_id, original.id, canonicalContent(original.content), actor.user_id]);
      await this.audit(tx, project, result.rows[0].id, actor, "GDSS_SUCCESSOR_CREATED", { predecessor_version_id: original.id });
      return result.rows[0] as SystemModelVersion;
    });
  }
  async getModel(actor: ControlActor, project: string, identityId: string) {
    assertGdssAccess(actor, project, "read");
    return this.transaction(tx => this.identity(tx, project, identityId));
  }
  async listVersions(actor: ControlActor, project: string, identityId: string) {
    assertGdssAccess(actor, project, "read");
    return this.transaction(async tx => {
      await this.identity(tx, project, identityId);
      const result = await tx.query("SELECT * FROM public.gdss_version WHERE identity_id=$1 ORDER BY version_number", [identityId]);
      return result.rows as SystemModelVersion[];
    });
  }
  async getVersion(actor: ControlActor, project: string, versionId: string) {
    assertGdssAccess(actor, project, "read");
    return this.transaction(async tx => {
      const v = await this.version(tx, project, versionId);
      return { ...v, children: v.content.children.map(c => ({ ...c, model_version_id: v.id })) };
    });
  }
}
