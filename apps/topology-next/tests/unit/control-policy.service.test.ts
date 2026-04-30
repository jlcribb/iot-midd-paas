import { describe, expect, it, vi } from "vitest";
import { ConflictError } from "@/lib/errors/domain-errors";
import { ControlPolicyService } from "@/lib/services/control-policy.service";
import type {
  IControlPolicyAuditRepository,
  IControlPolicyRepository,
  IProjectRepository
} from "@/lib/repositories/contracts";

function createAuditRepoMock(): IControlPolicyAuditRepository {
  return {
    recordChange: vi.fn().mockResolvedValue(undefined)
  };
}

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
      findAll: vi.fn().mockResolvedValue([]),
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

    const auditRepo = createAuditRepoMock();
    const service = new ControlPolicyService({ controlPolicyRepo, projectRepo, controlPolicyAuditRepo: auditRepo });
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
    expect(auditRepo.recordChange).toHaveBeenCalledWith(expect.objectContaining({
      entityId: "policy-1",
      action: "CONTROL_POLICY_CREATED"
    }));
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
      findAll: vi.fn().mockResolvedValue([]),
      update
    };

    const projectRepo: IProjectRepository = {
      create: vi.fn(),
      findById: vi.fn(),
      findAll: vi.fn(),
      update: vi.fn()
    };

    const auditRepo = createAuditRepoMock();
    const service = new ControlPolicyService({ controlPolicyRepo, projectRepo, controlPolicyAuditRepo: auditRepo });
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
    expect(auditRepo.recordChange).toHaveBeenCalledWith(expect.objectContaining({
      entityId: "policy-1",
      action: "CONTROL_POLICY_UPDATED"
    }));
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
      findAll: vi.fn().mockResolvedValue([]),
      update: vi.fn()
    };

    const auditRepo = createAuditRepoMock();

    const service = new ControlPolicyService({
      controlPolicyRepo,
      controlPolicyAuditRepo: auditRepo,
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
    expect(auditRepo.recordChange).not.toHaveBeenCalled();
  });

  it("blocks creation when another enabled policy has the same exact scope and selection rank", async () => {
    const controlPolicyRepo: IControlPolicyRepository = {
      create: vi.fn(),
      findById: vi.fn(),
      findAll: vi.fn().mockResolvedValue([
        {
          id: "policy-existing",
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
          priority: 4,
          enabled: true,
          version: 1,
          created_at: "2026-01-01T00:00:00.000Z",
          updated_at: "2026-01-01T00:00:00.000Z"
        }
      ]),
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

    const service = new ControlPolicyService({
      controlPolicyRepo,
      projectRepo,
      controlPolicyAuditRepo: createAuditRepoMock()
    });

    await expect(service.create({
      project_id: "project-1",
      variable: "tank_level",
      policy_type: "proportional",
      context_selector: { sector: "tank_A" },
      params: {
        variable_name: "Tank",
        actuator_name: "pump",
        setpoint_value: 70,
        gain: 1,
        deadband: 0,
        min_action: 0
      },
      priority: 4,
      enabled: true
    })).rejects.toBeInstanceOf(ConflictError);
  });

  it("returns a selection preview using existing and candidate policies", async () => {
    const controlPolicyRepo: IControlPolicyRepository = {
      create: vi.fn(),
      findById: vi.fn(),
      findAll: vi.fn().mockResolvedValue([
        {
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
          priority: 1,
          enabled: true,
          version: 1,
          created_at: "2026-01-01T00:00:00.000Z",
          updated_at: "2026-01-01T00:00:00.000Z"
        }
      ]),
      update: vi.fn()
    };

    const service = new ControlPolicyService({
      controlPolicyRepo,
      projectRepo: {
        create: vi.fn(),
        findById: vi.fn(),
        findAll: vi.fn(),
        update: vi.fn()
      },
      controlPolicyAuditRepo: createAuditRepoMock()
    });

    const preview = await service.previewSelection({
      projectId: "project-1",
      variable: "tank_level",
      context: { sector: "tank_A" },
      candidatePolicy: {
        project_id: "project-1",
        variable: "tank_level",
        policy_type: "proportional",
        context_selector: { sector: "tank_A" },
        params: {
          variable_name: "Tank",
          actuator_name: "pump",
          setpoint_value: 70,
          gain: 2,
          deadband: 0,
          min_action: 0
        },
        priority: 4,
        enabled: true,
        version: 1
      }
    });

    expect(preview.current_selected_policy?.id).toBe("policy-1");
    expect(preview.hypothetical_selected_policy?.id).toBe("preview-candidate");
    expect(preview.candidate_would_be_selected).toBe(true);
  });
});
