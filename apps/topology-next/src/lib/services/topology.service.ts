import type { TopologyLink } from "@/lib/dto/topology.dto";
import { ConflictError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import type {
  IAssetRepository,
  IProjectRepository,
  ISectorRepository,
  ITopologyRepository
} from "@/lib/repositories/contracts";
import { AssetRepository } from "@/lib/repositories/asset.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { SectorRepository } from "@/lib/repositories/sector.repository";
import { TopologyRepository } from "@/lib/repositories/topology.repository";
import type {
  CreateTopologyLinkInput,
  UpdateTopologyLinkInput
} from "@/lib/validators/topology.schemas";

interface TopologyServiceDeps {
  projectRepo?: IProjectRepository;
  sectorRepo?: ISectorRepository;
  assetRepo?: IAssetRepository;
  topologyRepo?: ITopologyRepository;
}

export class TopologyService {
  private readonly projectRepo: IProjectRepository;
  private readonly sectorRepo: ISectorRepository;
  private readonly assetRepo: IAssetRepository;
  private readonly topologyRepo: ITopologyRepository;

  constructor(deps: TopologyServiceDeps = {}) {
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
    this.sectorRepo = deps.sectorRepo ?? new SectorRepository();
    this.assetRepo = deps.assetRepo ?? new AssetRepository();
    this.topologyRepo = deps.topologyRepo ?? new TopologyRepository();
  }

  private validateSourceTarget(
    sourceAssetId: string | null | undefined,
    sourceSectorId: string | null | undefined,
    targetAssetId: string | null | undefined,
    targetSectorId: string | null | undefined
  ): void {
    const sourceCount = Number(Boolean(sourceAssetId)) + Number(Boolean(sourceSectorId));
    const targetCount = Number(Boolean(targetAssetId)) + Number(Boolean(targetSectorId));

    if (sourceCount !== 1) {
      throw new ValidationError("Exactly one source (asset or sector) is required");
    }
    if (targetCount !== 1) {
      throw new ValidationError("Exactly one target (asset or sector) is required");
    }
    if (sourceAssetId && targetAssetId && sourceAssetId === targetAssetId) {
      throw new ConflictError("Invalid self-link between same asset");
    }
    if (sourceSectorId && targetSectorId && sourceSectorId === targetSectorId) {
      throw new ConflictError("Invalid self-link between same sector");
    }
  }

  private async validateProjectOwnership(input: {
    project_id: string;
    source_asset_id?: string | null;
    target_asset_id?: string | null;
    source_sector_id?: string | null;
    target_sector_id?: string | null;
  }): Promise<void> {
    const project = await this.projectRepo.findById(input.project_id);
    if (!project) {
      throw new NotFoundError("Project not found");
    }

    if (input.source_asset_id) {
      const asset = await this.assetRepo.findById(input.source_asset_id);
      if (!asset) throw new NotFoundError("source_asset_id not found");
      if (asset.project_id !== input.project_id) {
        throw new ConflictError("source_asset_id belongs to a different project");
      }
    }
    if (input.target_asset_id) {
      const asset = await this.assetRepo.findById(input.target_asset_id);
      if (!asset) throw new NotFoundError("target_asset_id not found");
      if (asset.project_id !== input.project_id) {
        throw new ConflictError("target_asset_id belongs to a different project");
      }
    }
    if (input.source_sector_id) {
      const sector = await this.sectorRepo.findById(input.source_sector_id);
      if (!sector) throw new NotFoundError("source_sector_id not found");
      if (sector.project_id !== input.project_id) {
        throw new ConflictError("source_sector_id belongs to a different project");
      }
    }
    if (input.target_sector_id) {
      const sector = await this.sectorRepo.findById(input.target_sector_id);
      if (!sector) throw new NotFoundError("target_sector_id not found");
      if (sector.project_id !== input.project_id) {
        throw new ConflictError("target_sector_id belongs to a different project");
      }
    }
  }

  async create(input: CreateTopologyLinkInput): Promise<TopologyLink> {
    this.validateSourceTarget(input.source_asset_id, input.source_sector_id, input.target_asset_id, input.target_sector_id);
    await this.validateProjectOwnership(input);

    const duplicated = await this.topologyRepo.existsExactRelation(
      input.project_id,
      input.relation_type,
      input.source_asset_id ?? null,
      input.source_sector_id ?? null,
      input.target_asset_id ?? null,
      input.target_sector_id ?? null
    );
    if (duplicated) {
      throw new ConflictError("Duplicate topology link");
    }

    return this.topologyRepo.create(input);
  }

  async getById(id: string): Promise<TopologyLink> {
    const topology = await this.topologyRepo.findById(id);
    if (!topology) {
      throw new NotFoundError("Topology link not found");
    }
    return topology;
  }

  async getProjectTopology(projectId: string): Promise<TopologyLink[]> {
    const project = await this.projectRepo.findById(projectId);
    if (!project) {
      throw new NotFoundError("Project not found");
    }
    return this.topologyRepo.findByProjectId(projectId);
  }

  async update(id: string, input: UpdateTopologyLinkInput): Promise<TopologyLink> {
    const current = await this.topologyRepo.findById(id);
    if (!current) {
      throw new NotFoundError("Topology link not found");
    }

    const merged = {
      ...current,
      ...input
    };
    this.validateSourceTarget(
      merged.source_asset_id,
      merged.source_sector_id,
      merged.target_asset_id,
      merged.target_sector_id
    );
    await this.validateProjectOwnership({
      project_id: current.project_id,
      source_asset_id: merged.source_asset_id,
      source_sector_id: merged.source_sector_id,
      target_asset_id: merged.target_asset_id,
      target_sector_id: merged.target_sector_id
    });

    const duplicated = await this.topologyRepo.existsExactRelation(
      current.project_id,
      merged.relation_type,
      merged.source_asset_id,
      merged.source_sector_id,
      merged.target_asset_id,
      merged.target_sector_id,
      id
    );
    if (duplicated) {
      throw new ConflictError("Duplicate topology link");
    }

    const updated = await this.topologyRepo.update(id, input);
    if (!updated) {
      throw new NotFoundError("Topology link not found");
    }
    return updated;
  }

  async delete(id: string): Promise<void> {
    const deleted = await this.topologyRepo.delete(id);
    if (!deleted) {
      throw new NotFoundError("Topology link not found");
    }
  }

  async listByAsset(assetId: string): Promise<TopologyLink[]> {
    const asset = await this.assetRepo.findById(assetId);
    if (!asset) {
      throw new NotFoundError("Asset not found");
    }
    return this.topologyRepo.findByAssetId(assetId);
  }
}
