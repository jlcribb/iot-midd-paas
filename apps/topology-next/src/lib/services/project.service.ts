import { AssetRepository } from "@/lib/repositories/asset.repository";
import type { IAssetRepository, IProjectRepository, ISectorRepository, ITopologyRepository } from "@/lib/repositories/contracts";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { SectorRepository } from "@/lib/repositories/sector.repository";
import { TopologyRepository } from "@/lib/repositories/topology.repository";
import { NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import type { CreateProjectInput, UpdateProjectInput } from "@/lib/validators/project.schemas";
import { withTransaction } from "@/lib/db/tx";

interface ProjectServiceDeps {
  projectRepo?: IProjectRepository;
  sectorRepo?: ISectorRepository;
  assetRepo?: IAssetRepository;
  topologyRepo?: ITopologyRepository;
}

export class ProjectService {
  private readonly projectRepo: IProjectRepository;
  private readonly sectorRepo: ISectorRepository;
  private readonly assetRepo: IAssetRepository;
  private readonly topologyRepo: ITopologyRepository;

  constructor(deps: ProjectServiceDeps = {}) {
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
    this.sectorRepo = deps.sectorRepo ?? new SectorRepository();
    this.assetRepo = deps.assetRepo ?? new AssetRepository();
    this.topologyRepo = deps.topologyRepo ?? new TopologyRepository();
  }

  async create(input: CreateProjectInput) {
    if (!input.name.trim()) {
      throw new ValidationError("Project name is required");
    }
    return this.projectRepo.create(input);
  }

  async getById(id: string) {
    const project = await this.projectRepo.findById(id);
    if (!project) {
      throw new NotFoundError("Project not found");
    }
    return project;
  }

  async list(status?: "draft" | "active" | "inactive" | "archived") {
    return this.projectRepo.findAll(status ? { status } : undefined);
  }

  async update(id: string, input: UpdateProjectInput) {
    const existing = await this.projectRepo.findById(id);
    if (!existing) {
      throw new NotFoundError("Project not found");
    }

    const updated = await this.projectRepo.update(id, input);
    if (!updated) {
      throw new NotFoundError("Project not found");
    }

    if (input.status === "archived") {
      await withTransaction(async (tx) => {
        const txSectorRepo = new SectorRepository(tx);
        const txAssetRepo = new AssetRepository(tx);
        const txTopologyRepo = new TopologyRepository(tx);
        await txSectorRepo.softDeactivateByProject(id);
        await txAssetRepo.softDeactivateByProject(id);
        await txTopologyRepo.deactivateByProject(id);
      });
    }

    return updated;
  }
}
