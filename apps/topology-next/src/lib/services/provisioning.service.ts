import type { PoolClient } from "pg";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import { AssetRepository } from "@/lib/repositories/asset.repository";
import { LocationRepository } from "@/lib/repositories/location.repository";
import { ProjectRepository } from "@/lib/repositories/project.repository";
import { SectorRepository } from "@/lib/repositories/sector.repository";
import { TopologyRepository } from "@/lib/repositories/topology.repository";
import { ConflictError, NotFoundError } from "@/lib/errors/domain-errors";
import type { BootstrapNodeWithDevicesInput } from "@/lib/validators/topology.schemas";
import { AssetService } from "@/lib/services/asset.service";
import { SectorService } from "@/lib/services/sector.service";
import { TopologyService } from "@/lib/services/topology.service";
import type { IAssetRepository, ILocationRepository, IProjectRepository, ISectorRepository, ITopologyRepository } from "@/lib/repositories/contracts";

interface ProvisioningServiceDeps {
  transactionRunner?: TransactionRunner;
  contextFactory?: ProvisioningContextFactory;
}

export interface BootstrapNodeWithDevicesResult {
  project_id: string;
  sector_id: string;
  node_id: string;
  device_ids: string[];
  topology_link_ids: string[];
}

interface ProvisioningContext {
  projectRepo: IProjectRepository;
  sectorRepo: ISectorRepository;
  locationRepo: ILocationRepository;
  assetRepo: IAssetRepository;
  topologyRepo: ITopologyRepository;
  sectorService: SectorService;
  assetService: AssetService;
  topologyService: TopologyService;
}

type ProvisioningContextFactory = (tx: PoolClient) => ProvisioningContext;

function defaultContextFactory(tx: PoolClient): ProvisioningContext {
  const projectRepo = new ProjectRepository(tx);
  const sectorRepo = new SectorRepository(tx);
  const locationRepo = new LocationRepository(tx);
  const assetRepo = new AssetRepository(tx);
  const topologyRepo = new TopologyRepository(tx);

  return {
    projectRepo,
    sectorRepo,
    locationRepo,
    assetRepo,
    topologyRepo,
    sectorService: new SectorService({
      projectRepo,
      sectorRepo,
      locationRepo,
      assetRepo,
      topologyRepo
    }),
    assetService: new AssetService({
      projectRepo,
      sectorRepo,
      locationRepo,
      assetRepo,
      topologyRepo
    }),
    topologyService: new TopologyService({
      projectRepo,
      sectorRepo,
      assetRepo,
      topologyRepo
    })
  };
}

export class ProvisioningService {
  private readonly transactionRunner: TransactionRunner;
  private readonly contextFactory: ProvisioningContextFactory;

  constructor(deps: ProvisioningServiceDeps = {}) {
    this.transactionRunner = deps.transactionRunner ?? withTransaction;
    this.contextFactory = deps.contextFactory ?? defaultContextFactory;
  }

  async bootstrapNodeWithDevices(input: BootstrapNodeWithDevicesInput): Promise<BootstrapNodeWithDevicesResult> {
    return this.transactionRunner(async (tx: PoolClient) => {
      const {
        projectRepo,
        sectorRepo,
        locationRepo,
        sectorService,
        assetService,
        topologyService
      } = this.contextFactory(tx);

      const project = await projectRepo.findById(input.project_id);
      if (!project) {
        throw new NotFoundError("Project not found");
      }

      let sectorId: string;
      if (input.sector_id) {
        const sector = await sectorRepo.findById(input.sector_id);
        if (!sector) {
          throw new NotFoundError("Sector not found");
        }
        if (sector.project_id !== input.project_id) {
          throw new ConflictError("Sector does not belong to project");
        }
        sectorId = sector.id;
      } else if (input.sector) {
        let sectorLocationId: string | null = null;
        if (input.sector.location) {
          const createdLocation = await locationRepo.create({
            name: input.sector.location.name,
            latitude: input.sector.location.latitude ?? null,
            longitude: input.sector.location.longitude ?? null,
            metadata: input.sector.location.metadata ?? {},
            description: null,
            altitude: null,
            accuracy_meters: null,
            country: null,
            province: null,
            city: null,
            address_text: null,
            building: null,
            floor: null,
            zone: null,
            rack: null,
            position: null
          });
          sectorLocationId = createdLocation.id;
        }
        const createdSector = await sectorService.create({
          project_id: input.project_id,
          location_id: sectorLocationId,
          name: input.sector.name,
          code: input.sector.code ?? null,
          description: input.sector.description ?? null,
          metadata: input.sector.metadata ?? {}
        });
        sectorId = createdSector.id;
      } else {
        throw new NotFoundError("Sector payload missing");
      }

      let nodeLocationId: string | null = null;
      if (input.node_location) {
        const createdNodeLocation = await locationRepo.create({
          name: input.node_location.name,
          latitude: input.node_location.latitude ?? null,
          longitude: input.node_location.longitude ?? null,
          metadata: input.node_location.metadata ?? {},
          description: null,
          altitude: null,
          accuracy_meters: null,
          country: null,
          province: null,
          city: null,
          address_text: null,
          building: null,
          floor: null,
          zone: null,
          rack: null,
          position: null
        });
        nodeLocationId = createdNodeLocation.id;
      }

      const node = await assetService.create({
        project_id: input.project_id,
        sector_id: sectorId,
        location_id: nodeLocationId,
        parent_asset_id: null,
        asset_type: "programmable_node",
        subtype: input.node.subtype,
        name: input.node.name,
        code: input.node.code ?? null,
        description: input.node.description ?? null,
        status: input.node.status,
        role: null,
        serial_number: null,
        manufacturer: null,
        model: null,
        firmware_version: null,
        hardware_version: null,
        mac_address: null,
        ip_address: null,
        last_seen_at: null,
        metadata: input.node.metadata ?? {}
      });

      const createdDevices = [];
      for (const device of input.devices) {
        const createdDevice = await assetService.create({
          project_id: input.project_id,
          sector_id: sectorId,
          location_id: null,
          parent_asset_id: node.id,
          asset_type: device.asset_type,
          subtype: device.subtype,
          name: device.name,
          code: device.code ?? null,
          description: device.description ?? null,
          status: device.status,
          role: null,
          serial_number: null,
          manufacturer: null,
          model: null,
          firmware_version: null,
          hardware_version: null,
          mac_address: null,
          ip_address: null,
          last_seen_at: null,
          metadata: device.metadata ?? {}
        });
        createdDevices.push(createdDevice);
      }

      const linkIds: string[] = [];
      if (input.create_topology_links) {
        const containsLink = await topologyService.create({
          project_id: input.project_id,
          source_sector_id: sectorId,
          target_asset_id: node.id,
          relation_type: "contains",
          source_asset_id: null,
          target_sector_id: null,
          connection_medium: null,
          protocol: null,
          ports: [],
          link_quality: null,
          status: "active",
          metadata: { auto_provisioned: true }
        });
        linkIds.push(containsLink.id);

        for (const device of createdDevices) {
          const relation = device.asset_type === "sensor" ? "reads" : "controls";
          const link = await topologyService.create({
            project_id: input.project_id,
            source_asset_id: node.id,
            target_asset_id: device.id,
            relation_type: relation,
            source_sector_id: null,
            target_sector_id: null,
            connection_medium: null,
            protocol: null,
            ports: [],
            link_quality: null,
            status: "active",
            metadata: { auto_provisioned: true }
          });
          linkIds.push(link.id);
        }
      }

      return {
        project_id: input.project_id,
        sector_id: sectorId,
        node_id: node.id,
        device_ids: createdDevices.map((device) => device.id),
        topology_link_ids: linkIds
      };
    });
  }
}
