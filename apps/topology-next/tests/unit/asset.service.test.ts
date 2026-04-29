import { describe, expect, it, vi } from "vitest";
import { AssetService } from "@/lib/services/asset.service";
import type {
  IAssetRepository,
  ILocationRepository,
  IProjectRepository,
  ISectorRepository,
  ITopologyRepository
} from "@/lib/repositories/contracts";
import type { Asset } from "@/lib/dto/asset.dto";

function makeAsset(partial: Partial<Asset>): Asset {
  return {
    id: partial.id ?? "asset-1",
    project_id: partial.project_id ?? "project-1",
    sector_id: partial.sector_id ?? "sector-1",
    location_id: partial.location_id ?? null,
    parent_asset_id: partial.parent_asset_id ?? null,
    asset_type: partial.asset_type ?? "programmable_node",
    subtype: partial.subtype ?? "esp32",
    name: partial.name ?? "Node Principal",
    code: partial.code ?? null,
    description: partial.description ?? null,
    status: partial.status ?? "active",
    role: partial.role ?? null,
    serial_number: partial.serial_number ?? null,
    manufacturer: partial.manufacturer ?? null,
    model: partial.model ?? null,
    firmware_version: partial.firmware_version ?? null,
    hardware_version: partial.hardware_version ?? null,
    mac_address: partial.mac_address ?? null,
    ip_address: partial.ip_address ?? null,
    last_seen_at: partial.last_seen_at ?? null,
    metadata: partial.metadata ?? {},
    created_at: partial.created_at ?? "2026-01-01T00:00:00.000Z",
    updated_at: partial.updated_at ?? "2026-01-01T00:00:00.000Z"
  };
}

describe("AssetService", () => {
  function buildDeps(overrides?: {
    projectRepo?: Partial<IProjectRepository>;
    sectorRepo?: Partial<ISectorRepository>;
    locationRepo?: Partial<ILocationRepository>;
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
      softDeactivateByProject: vi.fn(),
      ...overrides?.sectorRepo
    };
    const locationRepo: ILocationRepository = {
      create: vi.fn(),
      findById: vi.fn().mockResolvedValue(null),
      findAll: vi.fn(),
      update: vi.fn(),
      ...overrides?.locationRepo
    };
    const assetRepo: IAssetRepository = {
      create: vi.fn().mockImplementation(async (input) => makeAsset({ ...input, id: "asset-created" })),
      findById: vi.fn().mockResolvedValue(null),
      findByProjectId: vi.fn().mockResolvedValue([]),
      findBySectorId: vi.fn().mockResolvedValue([]),
      findChildren: vi.fn().mockResolvedValue([]),
      findTree: vi
        .fn()
        .mockResolvedValue([
          { ...makeAsset({ id: "asset-root" }), depth: 0 },
          { ...makeAsset({ id: "asset-child" }), depth: 1 }
        ]),
      findNodeDevices: vi.fn().mockResolvedValue([]),
      findOfflineAssets: vi.fn().mockResolvedValue([]),
      update: vi.fn(),
      deleteSafe: vi.fn(),
      existsProjectCode: vi.fn().mockResolvedValue(false),
      existsSerialNumber: vi.fn().mockResolvedValue(false),
      existsNormalizedMac: vi.fn().mockResolvedValue(false),
      softDeactivateByProject: vi.fn(),
      ...overrides?.assetRepo
    };
    const topologyRepo: ITopologyRepository = {
      create: vi.fn(),
      findById: vi.fn(),
      findByProjectId: vi.fn(),
      findByAssetId: vi.fn().mockResolvedValue([]),
      update: vi.fn(),
      delete: vi.fn(),
      existsExactRelation: vi.fn(),
      deactivateByProject: vi.fn(),
      deactivateBySectorAndAssets: vi.fn(),
      deactivateByAssetIds: vi.fn(),
      ...overrides?.topologyRepo
    };

    return { projectRepo, sectorRepo, locationRepo, assetRepo, topologyRepo };
  }

  it("creates a programmable node with valid payload", async () => {
    const deps = buildDeps();
    const service = new AssetService(deps);

    const result = await service.create({
      project_id: "project-1",
      sector_id: "sector-1",
      location_id: null,
      parent_asset_id: null,
      asset_type: "programmable_node",
      subtype: "esp32",
      name: "ESP32 Principal",
      code: "NODE-001",
      description: null,
      status: "active",
      role: null,
      serial_number: null,
      manufacturer: null,
      model: null,
      firmware_version: null,
      hardware_version: null,
      mac_address: "AA:BB:CC:DD:EE:FF",
      ip_address: null,
      last_seen_at: null,
      metadata: {}
    });

    expect(result.asset_type).toBe("programmable_node");
    expect(deps.assetRepo.create).toHaveBeenCalledTimes(1);
  });

  it("rejects child asset when parent belongs to another project", async () => {
    const deps = buildDeps({
      assetRepo: {
        findById: vi.fn().mockResolvedValue(
          makeAsset({
            id: "parent-1",
            project_id: "project-2",
            sector_id: "sector-1",
            asset_type: "programmable_node"
          })
        )
      }
    });
    const service = new AssetService(deps);

    await expect(
      service.create({
        project_id: "project-1",
        sector_id: "sector-1",
        location_id: null,
        parent_asset_id: "parent-1",
        asset_type: "sensor",
        subtype: "ultrasonic",
        name: "Sensor Nivel",
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
        metadata: {}
      })
    ).rejects.toThrow("Parent asset belongs to a different project");
  });

  it("rejects child asset when parent belongs to another sector", async () => {
    const deps = buildDeps({
      assetRepo: {
        findById: vi.fn().mockResolvedValue(
          makeAsset({
            id: "parent-1",
            project_id: "project-1",
            sector_id: "sector-9",
            asset_type: "programmable_node"
          })
        )
      }
    });
    const service = new AssetService(deps);

    await expect(
      service.create({
        project_id: "project-1",
        sector_id: "sector-1",
        location_id: null,
        parent_asset_id: "parent-1",
        asset_type: "actuator",
        subtype: "pump",
        name: "Bomba",
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
        metadata: {}
      })
    ).rejects.toThrow("Parent asset belongs to a different sector");
  });

  it("returns node children", async () => {
    const deps = buildDeps({
      assetRepo: {
        findById: vi.fn().mockResolvedValue(makeAsset({ id: "node-1", asset_type: "programmable_node" })),
        findChildren: vi.fn().mockResolvedValue([
          makeAsset({ id: "sensor-1", parent_asset_id: "node-1", asset_type: "sensor" })
        ])
      }
    });
    const service = new AssetService(deps);

    const children = await service.getChildren("node-1");
    expect(children).toHaveLength(1);
    expect(children[0].id).toBe("sensor-1");
  });

  it("returns asset tree", async () => {
    const deps = buildDeps({
      assetRepo: {
        findById: vi.fn().mockResolvedValue(makeAsset({ id: "node-1", asset_type: "programmable_node" })),
        findTree: vi.fn().mockResolvedValue([
          { ...makeAsset({ id: "node-1", asset_type: "programmable_node" }), depth: 0 },
          { ...makeAsset({ id: "sensor-1", asset_type: "sensor", parent_asset_id: "node-1" }), depth: 1 }
        ])
      }
    });
    const service = new AssetService(deps);

    const tree = await service.getTree("node-1");
    expect(tree).toHaveLength(2);
    expect(tree[1].depth).toBe(1);
  });

  it("returns offline assets for project", async () => {
    const deps = buildDeps({
      assetRepo: {
        findOfflineAssets: vi.fn().mockResolvedValue([makeAsset({ id: "offline-1", status: "offline" })])
      }
    });
    const service = new AssetService(deps);

    const offline = await service.getOfflineAssets("project-1", 15);
    expect(offline).toHaveLength(1);
    expect(offline[0].status).toBe("offline");
    expect(deps.assetRepo.findOfflineAssets).toHaveBeenCalledWith("project-1", 15);
  });
});
