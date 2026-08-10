import type { ControlActor } from "@/lib/dto/control-access.dto";
import { assertControlPermission } from "@/lib/auth/control-access";
import { withTransaction, type SqlExecutor, type TransactionRunner } from "@/lib/db/tx";
import { NotFoundError, UnauthorizedError } from "@/lib/errors/domain-errors";
import { ProjectControlGovernanceAuditRepository } from "@/lib/repositories/project-control-governance-audit.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import type { IProjectRepository } from "@/lib/repositories/contracts";
import type { UpdateProjectInput } from "@/lib/validators/project.schemas";

interface ProjectControlGovernanceServiceDeps {
  projectRepo?: IProjectRepository;
  transactionRunner?: TransactionRunner;
  projectRepositoryFactory?: (db: SqlExecutor) => IProjectRepository;
  auditRepositoryFactory?: (db: SqlExecutor) => Pick<ProjectControlGovernanceAuditRepository, "recordParametricControlChange">;
}

export class ProjectControlGovernanceService {
  private readonly projectRepo: IProjectRepository;
  private readonly transactionRunner: TransactionRunner;
  private readonly projectRepositoryFactory: (db: SqlExecutor) => IProjectRepository;
  private readonly auditRepositoryFactory: (db: SqlExecutor) => Pick<ProjectControlGovernanceAuditRepository, "recordParametricControlChange">;

  constructor(deps: ProjectControlGovernanceServiceDeps = {}) {
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
    this.transactionRunner = deps.transactionRunner ?? withTransaction;
    this.projectRepositoryFactory = deps.projectRepositoryFactory ?? ((db) => new ProjectRepository(db));
    this.auditRepositoryFactory = deps.auditRepositoryFactory ?? ((db) => new ProjectControlGovernanceAuditRepository(db));
  }

  async updateProjectWithParametricControl(
    actor: ControlActor | null,
    projectId: string,
    input: UpdateProjectInput,
    correlationId?: string | null
  ) {
    if (!actor) {
      throw new UnauthorizedError("Authentication required to change parametric control");
    }
    if (input.parametric_control_enabled === undefined) {
      throw new Error("parametric_control_enabled is required for governed project updates");
    }

    const existing = await this.projectRepo.findById(projectId);
    if (!existing) {
      throw new NotFoundError("Project not found");
    }

    assertControlPermission(actor, "manage_parametric_control", projectId);
    const flagChanged = existing.parametric_control_enabled !== input.parametric_control_enabled;

    if (!flagChanged) {
      const updated = await this.projectRepo.update(projectId, input);
      if (!updated) throw new NotFoundError("Project not found");
      return updated;
    }

    return this.transactionRunner(async (tx) => {
      const transactionalProjectRepo = this.projectRepositoryFactory(tx);
      const transactionalAuditRepo = this.auditRepositoryFactory(tx);
      const updated = await transactionalProjectRepo.update(projectId, input);
      if (!updated) throw new NotFoundError("Project not found");

      await transactionalAuditRepo.recordParametricControlChange({
        projectId,
        actor,
        before: existing.parametric_control_enabled,
        after: updated.parametric_control_enabled,
        correlationId
      });
      return updated;
    });
  }
}
