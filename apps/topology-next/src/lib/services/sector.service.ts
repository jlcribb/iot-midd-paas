import type {
  IAssetRepository,
  ILocationRepository,
  IProjectRepository,
  ISectorRepository,
  ITopologyRepository
} from "@/lib/repositories/contracts";
import { AssetRepository } from "@/lib/repositories/asset.repository";
import { LocationRepository } from "@/lib/repositories/location.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { SectorRepository } from "@/lib/repositories/sector.repository";
import { TopologyRepository } from "@/lib/repositories/topology.repository";
import { ConflictError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import type { CreateSectorInput, UpdateSectorInput } from "@/lib/validators/sector.schemas";
import { withTransaction } from "@/lib/db/tx";

interface SectorServiceDeps {
  projectRepo?: IProjectRepository;
  sectorRepo?: ISectorRepository;
  locationRepo?: ILocationRepository;
  assetRepo?: IAssetRepository;
  topologyRepo?: ITopologyRepository;
}

export class SectorService {
  private readonly projectRepo: IProjectRepository;
  private readonly sectorRepo: ISectorRepository;
  private readonly locationRepo: ILocationRepository;
  private readonly assetRepo: IAssetRepository;
  private readonly topologyRepo: ITopologyRepository;

  constructor(deps: SectorServiceDeps = {}) {
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
    this.sectorRepo = deps.sectorRepo ?? new SectorRepository();
    this.locationRepo = deps.locationRepo ?? new LocationRepository();
    this.assetRepo = deps.assetRepo ?? new AssetRepository();
    this.topologyRepo = deps.topologyRepo ?? new TopologyRepository();
  }

  async create(input: CreateSectorInput) {
    if (!input.name.trim()) {
      throw new ValidationError("Sector name is required");
    }

    const project = await this.projectRepo.findById(input.project_id);
    if (!project) {
      throw new NotFoundError("Project not found");
    }

    if (input.location_id) {
      const location = await this.locationRepo.findById(input.location_id);
      if (!location) {
        throw new NotFoundError("Location not found");
      }
    }

    const nameExists = await this.sectorRepo.existsNameInProject(input.project_id, input.name);
    if (nameExists) {
      throw new ConflictError("Sector name already exists in project");
    }

    if (input.code) {
      const codeExists = await this.sectorRepo.existsCodeInProject(input.project_id, input.code);
      if (codeExists) {
        throw new ConflictError("Sector code already exists in project");
      }
    }

    return this.sectorRepo.create(input);
  }

  async getById(id: string) {
    const sector = await this.sectorRepo.findById(id);
    if (!sector) {
      throw new NotFoundError("Sector not found");
    }
    return sector;
  }

  async listByProject(projectId: string) {
    const project = await this.projectRepo.findById(projectId);
    if (!project) {
      throw new NotFoundError("Project not found");
    }
    return this.sectorRepo.findByProjectId(projectId);
  }

  async update(id: string, input: UpdateSectorInput) {
    const existing = await this.sectorRepo.findById(id);
    if (!existing) {
      throw new NotFoundError("Sector not found");
    }

    if (input.location_id) {
      const location = await this.locationRepo.findById(input.location_id);
      if (!location) {
        throw new NotFoundError("Location not found");
      }
    }

    if (input.name) {
      const nameExists = await this.sectorRepo.existsNameInProject(existing.project_id, input.name, id);
      if (nameExists) {
        throw new ConflictError("Sector name already exists in project");
      }
    }

    if (input.code) {
      const codeExists = await this.sectorRepo.existsCodeInProject(existing.project_id, input.code, id);
      if (codeExists) {
        throw new ConflictError("Sector code already exists in project");
      }
    }

    const updated = await this.sectorRepo.update(id, input);
    if (!updated) {
      throw new NotFoundError("Sector not found");
    }
    return updated;
  }

  async softDelete(id: string) {
    const sector = await this.sectorRepo.findById(id);
    if (!sector) {
      throw new NotFoundError("Sector not found");
    }

    const assets = await this.assetRepo.findBySectorId(id);
    const assetIds = assets.map((asset) => asset.id);

    return withTransaction(async (tx) => {
      const txSectorRepo = new SectorRepository(tx);
      const txAssetRepo = new AssetRepository(tx);
      const txTopologyRepo = new TopologyRepository(tx);

      const deactivated = await txSectorRepo.softDeactivate(id);
      if (!deactivated) {
        throw new NotFoundError("Sector not found");
      }

      for (const assetId of assetIds) {
        await txAssetRepo.update(assetId, {
          status: "inactive",
          metadata: { is_active: false }
        });
      }
      await txTopologyRepo.deactivateBySectorAndAssets(id, assetIds);
      return deactivated;
    });
  }
}
