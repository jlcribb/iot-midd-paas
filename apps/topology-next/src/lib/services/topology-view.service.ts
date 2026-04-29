import { withTransaction } from "@/lib/db/tx";
import { ConflictError, NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import type { TopologyView } from "@/lib/dto/topology-view.dto";
import type {
  CreateTopologyViewInput,
  SaveTopologyViewLayoutInput,
  UpdateTopologyViewInput
} from "@/lib/validators/topology-view.schemas";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { TopologyViewRepository } from "@/lib/repositories/topology-view.repository";
import { AssetRepository } from "@/lib/repositories/asset.repository";
import { SectorRepository } from "@/lib/repositories/sector.repository";
import { TopologyRepository } from "@/lib/repositories/topology.repository";

export class TopologyViewService {
  async listByProject(projectId: string, viewType?: TopologyView["view_type"]) {
    const projectRepo = new ProjectRepository();
    const topologyViewRepo = new TopologyViewRepository();

    const project = await projectRepo.findById(projectId);
    if (!project) {
      throw new NotFoundError("Project not found");
    }

    return topologyViewRepo.findByProjectId(projectId, viewType);
  }

  async create(projectId: string, input: CreateTopologyViewInput) {
    if (!input.name.trim()) {
      throw new ValidationError("View name is required");
    }

    return withTransaction(async (tx) => {
      const projectRepo = new ProjectRepository(tx);
      const topologyViewRepo = new TopologyViewRepository(tx);

      const project = await projectRepo.findById(projectId);
      if (!project) {
        throw new NotFoundError("Project not found");
      }

      if (input.is_default) {
        await topologyViewRepo.clearDefaults(projectId, input.view_type);
      }

      return topologyViewRepo.create(projectId, input);
    });
  }

  async getById(id: string) {
    const topologyViewRepo = new TopologyViewRepository();
    const view = await topologyViewRepo.findById(id);
    if (!view) {
      throw new NotFoundError("Topology view not found");
    }
    return view;
  }

  async update(id: string, input: UpdateTopologyViewInput) {
    return withTransaction(async (tx) => {
      const topologyViewRepo = new TopologyViewRepository(tx);

      const current = await topologyViewRepo.findById(id);
      if (!current) {
        throw new NotFoundError("Topology view not found");
      }

      if (input.is_default) {
        await topologyViewRepo.clearDefaults(current.project_id, current.view_type);
      }

      const updated = await topologyViewRepo.update(id, input);
      if (!updated) {
        throw new NotFoundError("Topology view not found");
      }
      return updated;
    });
  }

  async getLayout(viewId: string) {
    const topologyViewRepo = new TopologyViewRepository();
    const view = await topologyViewRepo.findById(viewId);
    if (!view) {
      throw new NotFoundError("Topology view not found");
    }

    const layout = await topologyViewRepo.getLayout(viewId);
    return {
      view,
      layout
    };
  }

  async saveLayout(viewId: string, input: SaveTopologyViewLayoutInput) {
    const topologyViewRepo = new TopologyViewRepository();
    const assetRepo = new AssetRepository();
    const sectorRepo = new SectorRepository();
    const topologyRepo = new TopologyRepository();

    const view = await topologyViewRepo.findById(viewId);
    if (!view) {
      throw new NotFoundError("Topology view not found");
    }

    const [assets, sectors, topologyLinks] = await Promise.all([
      assetRepo.findByProjectId(view.project_id),
      sectorRepo.findByProjectId(view.project_id),
      topologyRepo.findByProjectId(view.project_id)
    ]);

    const assetIds = new Set(assets.map((item) => item.id));
    const sectorIds = new Set(sectors.map((item) => item.id));
    const topologyLinkIds = new Set(topologyLinks.map((item) => item.id));

    for (const node of input.node_layouts) {
      if (node.asset_id && !assetIds.has(node.asset_id)) {
        throw new ConflictError("Node layout references asset from another project or unknown asset");
      }
      if (node.sector_id && !sectorIds.has(node.sector_id)) {
        throw new ConflictError("Node layout references sector from another project or unknown sector");
      }
    }

    for (const link of input.link_layouts) {
      if (!topologyLinkIds.has(link.topology_link_id)) {
        throw new ConflictError("Link layout references topology link from another project or unknown link");
      }
    }

    return withTransaction(async (tx) => {
      const txTopologyViewRepo = new TopologyViewRepository(tx);
      const persistedView = await txTopologyViewRepo.findById(viewId);
      if (!persistedView) {
        throw new NotFoundError("Topology view not found");
      }

      const layout = await txTopologyViewRepo.replaceLayout(viewId, input);
      return {
        view: persistedView,
        layout
      };
    });
  }
}
