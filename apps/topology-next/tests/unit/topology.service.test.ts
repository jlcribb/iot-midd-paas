import { describe, expect, it, vi } from "vitest";
import { TopologyService } from "@/lib/services/topology.service";
import type {
  IAssetRepository,
  IProjectRepository,
  ISectorRepository,
  ITopologyRepository
} from "@/lib/repositories/contracts";

describe("TopologyService", () => {
  function buildDeps(overrides?: {
    projectRepo?: Partial<IProjectRepository>;
    assetRepo?: Partial<IAssetRepository>;
    topologyRepo?: Partial<ITopologyRepository>;
  }) {
    const projectRepo: IProjectRepository = {
      create: vi.fn(),
      findById: vi.fn().mockResolvedValue({
        id: "project-1",
        name: "P1",
        description: null,
        status: "active",
        parametric_control_enabled: false,
        metadata: {},
        created_at: "2026-01-01T00:00:00.000Z",
        updated_at: "2026-01-01T00:00:00.000Z"
      }),
      findAll: vi.fn(),
      update: vi.fn(),
      ...overrides?.projectRepo
    };
    const sectorRepo: ISectorRepository = {
      create: vi.fn(),
      findById: vi.fn().mockResolvedValue({
        id: "sector-1",
        project_id: "project-1",
        location_id: null,
        name: "S1",
        code: null,
        description: null,
        metadata: {},
        created_at: "2026-01-01T00:00:00.000Z",
        updated_at: "2026-01-01T00:00:00.000Z"
      }),
      findByProjectId: vi.fn(),
      update: vi.fn(),
      existsNameInProject: vi.fn(),
      existsCodeInProject: vi.fn(),
      softDeactivate: vi.fn(),
      softDeactivateByProject: vi.fn()
    };
    const assetRepo: IAssetRepository = {
      create: vi.fn(),
      findById: vi.fn().mockResolvedValue({
        id: "node-1",
        project_id: "project-1",
        sector_id: "sector-1",
        location_id: null,
        parent_asset_id: null,
        asset_type: "programmable_node",
        subtype: "esp32",
        name: "Node",
        code: null,
        description: null,
        status: "active",
        role: null,
        serial_number: null,
        manufacturer: null,
        model: null,
        firmware_version: null,
        hardware_version: null,
        mac_address: null,
        ip_address: null,
        last_seen_at: null,
        metadata: {},
        created_at: "2026-01-01T00:00:00.000Z",
        updated_at: "2026-01-01T00:00:00.000Z"
      }),
      findByProjectId: vi.fn(),
      findBySectorId: vi.fn(),
      findChildren: vi.fn(),
      findTree: vi.fn(),
      findNodeDevices: vi.fn(),
      findOfflineAssets: vi.fn(),
      update: vi.fn(),
      deleteSafe: vi.fn(),
      existsProjectCode: vi.fn(),
      existsSerialNumber: vi.fn(),
      existsNormalizedMac: vi.fn(),
      softDeactivateByProject: vi.fn(),
      ...overrides?.assetRepo
    };
    const topologyRepo: ITopologyRepository = {
      create: vi.fn(),
      findById: vi.fn(),
      findByProjectId: vi.fn().mockResolvedValue([
        {
          id: "link-1",
          project_id: "project-1",
          source_asset_id: "node-1",
          target_asset_id: "sensor-1",
          source_sector_id: null,
          target_sector_id: null,
          relation_type: "reads",
          connection_medium: null,
          protocol: null,
          ports: [],
          link_quality: null,
          status: "active",
          metadata: {},
          created_at: "2026-01-01T00:00:00.000Z",
          updated_at: "2026-01-01T00:00:00.000Z"
        }
      ]),
      findByAssetId: vi.fn().mockResolvedValue([]),
      update: vi.fn(),
      delete: vi.fn(),
      existsExactRelation: vi.fn().mockResolvedValue(false),
      deactivateByProject: vi.fn(),
      deactivateBySectorAndAssets: vi.fn(),
      deactivateByAssetIds: vi.fn(),
      ...overrides?.topologyRepo
    };

    return { projectRepo, sectorRepo, assetRepo, topologyRepo };
  }

  it("rejects topology link between assets from different projects", async () => {
    const deps = buildDeps({
      assetRepo: {
        findById: vi
          .fn()
          .mockResolvedValueOnce({
            id: "node-1",
            project_id: "project-1",
            sector_id: "sector-1",
            location_id: null,
            parent_asset_id: null,
            asset_type: "programmable_node",
            subtype: "esp32",
            name: "Node",
            code: null,
            description: null,
            status: "active",
            role: null,
            serial_number: null,
            manufacturer: null,
            model: null,
            firmware_version: null,
            hardware_version: null,
            mac_address: null,
            ip_address: null,
            last_seen_at: null,
            metadata: {},
            created_at: "2026-01-01T00:00:00.000Z",
            updated_at: "2026-01-01T00:00:00.000Z"
          })
          .mockResolvedValueOnce({
            id: "sensor-2",
            project_id: "project-2",
            sector_id: "sector-2",
            location_id: null,
            parent_asset_id: null,
            asset_type: "sensor",
            subtype: "ultrasonic",
            name: "Sensor",
            code: null,
            description: null,
            status: "active",
            role: null,
            serial_number: null,
            manufacturer: null,
            model: null,
            firmware_version: null,
            hardware_version: null,
            mac_address: null,
            ip_address: null,
            last_seen_at: null,
            metadata: {},
            created_at: "2026-01-01T00:00:00.000Z",
            updated_at: "2026-01-01T00:00:00.000Z"
          })
      }
    });
    const service = new TopologyService(deps);

    await expect(
      service.create({
        project_id: "project-1",
        source_asset_id: "node-1",
        source_sector_id: null,
        target_asset_id: "sensor-2",
        target_sector_id: null,
        relation_type: "reads",
        connection_medium: null,
        protocol: null,
        ports: [],
        link_quality: null,
        status: "active",
        metadata: {}
      })
    ).rejects.toThrow("target_asset_id belongs to a different project");
  });

  it("returns project topology", async () => {
    const deps = buildDeps();
    const service = new TopologyService(deps);

    const topology = await service.getProjectTopology("project-1");
    expect(topology).toHaveLength(1);
    expect(topology[0].relation_type).toBe("reads");
  });
});
