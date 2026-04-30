import { describe, expect, it, vi } from "vitest";
import { ControlPolicyService } from "@/lib/services/control-policy.service";
import type { IControlPolicyRepository, IProjectRepository } from "@/lib/repositories/contracts";

describe("ControlPolicyService", () => {
  it("creates policies only for existing projects", async () => {
    const create = vi.fn().mockResolvedValue({
      id: "policy-1",
      project_id: "project-1",
      variable: "tank_level",
      context_selector: {},
      policy_type: "proportional",
      params: {
        variable_name: "Tank",
        actuator_name: "pump",
        setpoint_value: 70,
        gain: 1,
        deadband: 0,
        min_action: 0
      },
      priority: 0,
      enabled: true,
      version: 1,
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z"
    });

    const controlPolicyRepo: IControlPolicyRepository = {
      create,
      findById: vi.fn(),
      findAll: vi.fn(),
      update: vi.fn()
    };

    const projectRepo: IProjectRepository = {
      create: vi.fn(),
      findById: vi.fn().mockResolvedValue({
        id: "project-1",
        name: "Proyecto Demo",
        description: null,
        status: "active",
        metadata: {},
        created_at: "2026-01-01T00:00:00.000Z",
        updated_at: "2026-01-01T00:00:00.000Z"
      }),
      findAll: vi.fn(),
      update: vi.fn()
    };

    const service = new ControlPolicyService({ controlPolicyRepo, projectRepo });
    const created = await service.create({
      project_id: "project-1",
      variable: "tank_level",
      policy_type: "proportional",
      context_selector: {},
      params: {
        variable_name: "Tank",
        actuator_name: "pump",
        setpoint_value: 70,
        gain: 1,
        deadband: 0,
        min_action: 0
      },
      priority: 0,
      enabled: true
    });

    expect(create).toHaveBeenCalledTimes(1);
    expect(created.id).toBe("policy-1");
  });

  it("increments version when updating mutable policy fields", async () => {
    const update = vi.fn().mockResolvedValue({
      id: "policy-1",
      project_id: "project-1",
      variable: "tank_level",
      context_selector: { sector: "tank_B" },
      policy_type: "proportional",
      params: {
        variable_name: "Tank",
        actuator_name: "pump",
        setpoint_value: 70,
        gain: 2,
        deadband: 0,
        min_action: 0
      },
      priority: 9,
      enabled: true,
      version: 4,
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-02T00:00:00.000Z"
    });

    const controlPolicyRepo: IControlPolicyRepository = {
      create: vi.fn(),
      findById: vi.fn().mockResolvedValue({
        id: "policy-1",
        project_id: "project-1",
        variable: "tank_level",
        context_selector: { sector: "tank_A" },
        policy_type: "proportional",
        params: {
          variable_name: "Tank",
          actuator_name: "pump",
          setpoint_value: 70,
          gain: 1,
          deadband: 0,
          min_action: 0
        },
        priority: 8,
        enabled: true,
        version: 3,
        created_at: "2026-01-01T00:00:00.000Z",
        updated_at: "2026-01-01T00:00:00.000Z"
      }),
      findAll: vi.fn(),
      update
    };

    const projectRepo: IProjectRepository = {
      create: vi.fn(),
      findById: vi.fn(),
      findAll: vi.fn(),
      update: vi.fn()
    };

    const service = new ControlPolicyService({ controlPolicyRepo, projectRepo });
    const updated = await service.update("policy-1", {
      context_selector: { sector: "tank_B" },
      params: {
        variable_name: "Tank",
        actuator_name: "pump",
        setpoint_value: 70,
        gain: 2,
        deadband: 0,
        min_action: 0
      },
      priority: 9,
      enabled: true
    });

    expect(update).toHaveBeenCalledWith("policy-1", expect.objectContaining({ version: 4 }));
    expect(updated.version).toBe(4);
  });

  it("returns existing policy for noop updates", async () => {
    const existing = {
      id: "policy-1",
      project_id: "project-1",
      variable: "tank_level",
      context_selector: {},
      policy_type: "threshold" as const,
      params: {
        variable_name: "Tank",
        actuator_name: "pump",
        setpoint_value: 70,
        tolerance: 2,
        increase_step: 1,
        decrease_step: 1,
        hold_signal: 0
      },
      priority: 2,
      enabled: true,
      version: 7,
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z"
    };

    const controlPolicyRepo: IControlPolicyRepository = {
      create: vi.fn(),
      findById: vi.fn().mockResolvedValue(existing),
      findAll: vi.fn(),
      update: vi.fn()
    };

    const service = new ControlPolicyService({
      controlPolicyRepo,
      projectRepo: {
        create: vi.fn(),
        findById: vi.fn(),
        findAll: vi.fn(),
        update: vi.fn()
      }
    });

    const result = await service.update("policy-1", {
      context_selector: {},
      params: existing.params,
      priority: 2,
      enabled: true
    });

    expect(controlPolicyRepo.update).not.toHaveBeenCalled();
    expect(result.version).toBe(7);
  });
});
