import type { Asset } from "@/lib/dto/asset.dto";
import { ConflictError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import { normalizeMacAddress } from "@/lib/utils/normalize";
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
import type { CreateAssetInput, UpdateAssetInput } from "@/lib/validators/asset.schemas";
import { withTransaction } from "@/lib/db/tx";

const PARENT_ALLOWED_TYPES = new Set<Asset["asset_type"]>(["programmable_node", "gateway", "relay_module", "power_unit"]);
const CHILD_DISALLOWED_TYPES = new Set<Asset["asset_type"]>(["programmable_node", "gateway", "power_unit"]);

interface AssetServiceDeps {
  projectRepo?: IProjectRepository;
  sectorRepo?: ISectorRepository;
  locationRepo?: ILocationRepository;
  assetRepo?: IAssetRepository;
  topologyRepo?: ITopologyRepository;
}

export class AssetService {
  private readonly projectRepo: IProjectRepository;
  private readonly sectorRepo: ISectorRepository;
  private readonly locationRepo: ILocationRepository;
  private readonly assetRepo: IAssetRepository;
  private readonly topologyRepo: ITopologyRepository;

  constructor(deps: AssetServiceDeps = {}) {
    this.projectRepo = deps.projectRepo ?? new ProjectRepository();
    this.sectorRepo = deps.sectorRepo ?? new SectorRepository();
    this.locationRepo = deps.locationRepo ?? new LocationRepository();
    this.assetRepo = deps.assetRepo ?? new AssetRepository();
    this.topologyRepo = deps.topologyRepo ?? new TopologyRepository();
  }

  private async validateProjectAndSector(projectId: string, sectorId: string): Promise<void> {
    const project = await this.projectRepo.findById(projectId);
    if (!project) {
      throw new NotFoundError("Project not found");
    }
    const sector = await this.sectorRepo.findById(sectorId);
    if (!sector) {
      throw new NotFoundError("Sector not found");
    }
    if (sector.project_id !== projectId) {
      throw new ConflictError("Sector does not belong to project");
    }
  }

  private async validateParentConstraints(
    input: {
      id?: string;
      project_id: string;
      sector_id: string;
      parent_asset_id?: string | null;
      asset_type: Asset["asset_type"];
    },
    existingTreeRootId?: string
  ): Promise<void> {
    if (!input.parent_asset_id) {
      return;
    }

    if (input.id && input.id === input.parent_asset_id) {
      throw new ConflictError("Asset cannot reference itself as parent");
    }

    const parent = await this.assetRepo.findById(input.parent_asset_id);
    if (!parent) {
      throw new NotFoundError("Parent asset not found");
    }

    if (parent.project_id !== input.project_id) {
      throw new ConflictError("Parent asset belongs to a different project");
    }
    if (parent.sector_id !== input.sector_id) {
      throw new ConflictError("Parent asset belongs to a different sector");
    }
    if (!PARENT_ALLOWED_TYPES.has(parent.asset_type)) {
      throw new ConflictError(`Parent asset type ${parent.asset_type} cannot contain child assets`);
    }
    if (CHILD_DISALLOWED_TYPES.has(input.asset_type)) {
      throw new ConflictError(`Asset type ${input.asset_type} cannot be assigned as child via parent_asset_id`);
    }

    if (existingTreeRootId) {
      const tree = await this.assetRepo.findTree(existingTreeRootId);
      const subtreeIds = new Set(tree.map((item) => item.id));
      if (subtreeIds.has(input.parent_asset_id)) {
        throw new ConflictError("Cannot set parent to an asset within the same subtree");
      }
    }
  }

  async create(input: CreateAssetInput): Promise<Asset> {
    if (!input.subtype.trim()) {
      throw new ValidationError("Asset subtype is required");
    }
    if (!input.name.trim()) {
      throw new ValidationError("Asset name is required");
    }

    await this.validateProjectAndSector(input.project_id, input.sector_id);

    if (input.location_id) {
      const location = await this.locationRepo.findById(input.location_id);
      if (!location) {
        throw new NotFoundError("Location not found");
      }
    }

    await this.validateParentConstraints(input);

    if (input.code) {
      const duplicatedCode = await this.assetRepo.existsProjectCode(input.project_id, input.code);
      if (duplicatedCode) {
        throw new ConflictError("Asset code already exists in project");
      }
    }
    if (input.serial_number) {
      const duplicatedSerial = await this.assetRepo.existsSerialNumber(input.serial_number);
      if (duplicatedSerial) {
        throw new ConflictError("Asset serial number already exists");
      }
    }

    const normalizedMac = normalizeMacAddress(input.mac_address);
    if (normalizedMac) {
      const duplicatedMac = await this.assetRepo.existsNormalizedMac(normalizedMac);
      if (duplicatedMac) {
        throw new ConflictError("Asset mac address already exists");
      }
    }

    return this.assetRepo.create({
      ...input,
      mac_address: normalizedMac
    });
  }

  async getById(id: string): Promise<Asset> {
    const asset = await this.assetRepo.findById(id);
    if (!asset) {
      throw new NotFoundError("Asset not found");
    }
    return asset;
  }

  async listByProject(projectId: string): Promise<Asset[]> {
    const project = await this.projectRepo.findById(projectId);
    if (!project) {
      throw new NotFoundError("Project not found");
    }
    return this.assetRepo.findByProjectId(projectId);
  }

  async listBySector(sectorId: string): Promise<Asset[]> {
    const sector = await this.sectorRepo.findById(sectorId);
    if (!sector) {
      throw new NotFoundError("Sector not found");
    }
    return this.assetRepo.findBySectorId(sectorId);
  }

  async getChildren(id: string): Promise<Asset[]> {
    const asset = await this.assetRepo.findById(id);
    if (!asset) {
      throw new NotFoundError("Asset not found");
    }
    return this.assetRepo.findChildren(id);
  }

  async getTree(id: string) {
    const asset = await this.assetRepo.findById(id);
    if (!asset) {
      throw new NotFoundError("Asset not found");
    }
    return this.assetRepo.findTree(id);
  }

  async getNodeDevices(id: string): Promise<Asset[]> {
    const asset = await this.assetRepo.findById(id);
    if (!asset) {
      throw new NotFoundError("Asset not found");
    }
    if (!PARENT_ALLOWED_TYPES.has(asset.asset_type)) {
      throw new ConflictError(`Asset type ${asset.asset_type} is not a valid device container`);
    }
    return this.assetRepo.findNodeDevices(id);
  }

  async getOfflineAssets(projectId: string, offlineMinutes = 15): Promise<Asset[]> {
    const project = await this.projectRepo.findById(projectId);
    if (!project) {
      throw new NotFoundError("Project not found");
    }
    return this.assetRepo.findOfflineAssets(projectId, offlineMinutes);
  }

  async update(id: string, input: UpdateAssetInput): Promise<Asset> {
    const current = await this.assetRepo.findById(id);
    if (!current) {
      throw new NotFoundError("Asset not found");
    }

    const targetProjectId = current.project_id;
    const targetSectorId = input.sector_id ?? current.sector_id;
    await this.validateProjectAndSector(targetProjectId, targetSectorId);

    if (input.location_id) {
      const location = await this.locationRepo.findById(input.location_id);
      if (!location) {
        throw new NotFoundError("Location not found");
      }
    }

    const children = await this.assetRepo.findChildren(id);
    const targetAssetType = input.asset_type ?? current.asset_type;
    if (children.length > 0 && !PARENT_ALLOWED_TYPES.has(targetAssetType)) {
      throw new ConflictError("Asset type cannot contain children");
    }

    if (input.sector_id && input.sector_id !== current.sector_id && children.length > 0) {
      throw new ConflictError("Cannot move asset with children between sectors without structural reassignment");
    }
    if (input.sector_id && input.sector_id !== current.sector_id) {
      const relatedLinks = await this.topologyRepo.findByAssetId(id);
      const hasSectorRelations = relatedLinks.some((link) => link.source_sector_id || link.target_sector_id);
      if (hasSectorRelations) {
        throw new ConflictError("Cannot move asset between sectors while sector topology links exist");
      }
    }

    const nextParentAssetId = input.parent_asset_id !== undefined ? input.parent_asset_id : current.parent_asset_id;
    await this.validateParentConstraints(
      {
        id,
        project_id: targetProjectId,
        sector_id: targetSectorId,
        parent_asset_id: nextParentAssetId,
        asset_type: targetAssetType
      },
      id
    );

    if (input.code) {
      const duplicatedCode = await this.assetRepo.existsProjectCode(targetProjectId, input.code, id);
      if (duplicatedCode) {
        throw new ConflictError("Asset code already exists in project");
      }
    }
    if (input.serial_number) {
      const duplicatedSerial = await this.assetRepo.existsSerialNumber(input.serial_number, id);
      if (duplicatedSerial) {
        throw new ConflictError("Asset serial number already exists");
      }
    }

    const normalizedMac = normalizeMacAddress(input.mac_address);
    if (normalizedMac) {
      const duplicatedMac = await this.assetRepo.existsNormalizedMac(normalizedMac, id);
      if (duplicatedMac) {
        throw new ConflictError("Asset mac address already exists");
      }
    }

    const updated = await this.assetRepo.update(id, {
      ...input,
      mac_address: normalizedMac ?? input.mac_address
    });
    if (!updated) {
      throw new NotFoundError("Asset not found");
    }
    return updated;
  }

  async deleteSafe(id: string): Promise<Asset> {
    return withTransaction(async (tx) => {
      const txAssetRepo = new AssetRepository(tx);
      const txTopologyRepo = new TopologyRepository(tx);

      const current = await txAssetRepo.findById(id);
      if (!current) {
        throw new NotFoundError("Asset not found");
      }

      const tree = await txAssetRepo.findTree(id);
      const ids = tree.map((node) => node.id);
      for (const nodeId of ids) {
        await txAssetRepo.update(nodeId, {
          status: nodeId === id ? "retired" : "inactive",
          metadata: { is_active: false }
        });
      }
      await txTopologyRepo.deactivateByAssetIds(ids);

      const deleted = await txAssetRepo.findById(id);
      if (!deleted) {
        throw new NotFoundError("Asset not found");
      }
      return deleted;
    });
  }
}
