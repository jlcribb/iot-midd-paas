import { describe, expect, it, vi } from "vitest";
import { SectorService } from "@/lib/services/sector.service";
import type {
  IAssetRepository,
  ILocationRepository,
  IProjectRepository,
  ISectorRepository,
  ITopologyRepository
} from "@/lib/repositories/contracts";

describe("SectorService", () => {
  function buildDeps(overrides?: {
    projectRepo?: Partial<IProjectRepository>;
    sectorRepo?: Partial<ISectorRepository>;
    locationRepo?: Partial<ILocationRepository>;
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
      create: vi.fn().mockResolvedValue({
        id: "sector-1",
        project_id: "project-1",
        location_id: null,
        name: "Tanque Norte",
        code: "TN-1",
        description: null,
        metadata: {},
        created_at: "2026-01-01T00:00:00.000Z",
        updated_at: "2026-01-01T00:00:00.000Z"
      }),
      findById: vi.fn(),
      findByProjectId: vi.fn(),
      update: vi.fn(),
      existsNameInProject: vi.fn().mockResolvedValue(false),
      existsCodeInProject: vi.fn().mockResolvedValue(false),
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

    const assetRepo = {} as IAssetRepository;
    const topologyRepo = {} as ITopologyRepository;

    return { projectRepo, sectorRepo, locationRepo, assetRepo, topologyRepo };
  }

  it("creates a sector when project exists and name/code are unique", async () => {
    const deps = buildDeps();
    const service = new SectorService(deps);

    const result = await service.create({
      project_id: "project-1",
      location_id: null,
      name: "Tanque Norte",
      code: "TN-1",
      description: null,
      metadata: {}
    });

    expect(result.id).toBe("sector-1");
    expect(deps.sectorRepo.existsNameInProject).toHaveBeenCalledWith("project-1", "Tanque Norte");
    expect(deps.sectorRepo.create).toHaveBeenCalledTimes(1);
  });

  it("rejects duplicate sector name in same project", async () => {
    const deps = buildDeps({
      sectorRepo: {
        existsNameInProject: vi.fn().mockResolvedValue(true)
      }
    });
    const service = new SectorService(deps);

    await expect(
      service.create({
        project_id: "project-1",
        location_id: null,
        name: "Tanque Norte",
        code: null,
        description: null,
        metadata: {}
      })
    ).rejects.toThrow("Sector name already exists in project");
  });
});
