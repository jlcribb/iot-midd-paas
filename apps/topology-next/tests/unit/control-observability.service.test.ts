import { describe, expect, it, vi } from "vitest";
import { ControlObservabilityService } from "@/lib/services/control-observability.service";
import type { IControlObservabilityRepository } from "@/lib/repositories/contracts";

describe("ControlObservabilityService", () => {
  it("lists recommendations with normalized limit", async () => {
    const findLatestRecommendations = vi.fn().mockResolvedValue([
      {
        audit_id: "audit-1",
        observed_at: "2026-04-29T00:00:00.000Z",
        project_id: "project-1",
        variable_id: "tank_level",
        event_id: "evt-1",
        recommendation_kind: "decrease",
        action_label: "decrease",
        actuator_name: "pump",
        command_value: -2.5,
        summary: "decrease pump",
        measurement_value: 72.5,
        setpoint_value: 70,
        error: -2.5,
        evaluator_name: "proportional",
        policy_id: "policy-1",
        policy_type: "proportional",
        policy_version: 1,
        policy_priority: 10
      }
    ]);

    const repo: IControlObservabilityRepository = {
      findLatestRecommendations,
      findAuditEntries: vi.fn(),
      getStatus: vi.fn()
    };

    const service = new ControlObservabilityService({ observabilityRepo: repo });
    const result = await service.listRecommendations({ projectId: "project-1", limit: 10 });

    expect(findLatestRecommendations).toHaveBeenCalledWith({
      projectId: "project-1",
      limit: 10
    });
    expect(result).toHaveLength(1);
    expect(result[0].policy_priority).toBe(10);
  });

  it("rejects invalid recommendation limit", async () => {
    const repo: IControlObservabilityRepository = {
      findLatestRecommendations: vi.fn(),
      findAuditEntries: vi.fn(),
      getStatus: vi.fn()
    };

    const service = new ControlObservabilityService({ observabilityRepo: repo });

    await expect(service.listRecommendations({ limit: 0 })).rejects.toMatchObject({
      message: "limit must be an integer between 1 and 100"
    });
  });

  it("lists audit entries with status filter", async () => {
    const findAuditEntries = vi.fn().mockResolvedValue([
      {
        id: 1,
        ts: "2026-04-29T00:00:00.000Z",
        action: "CONTROL_SKIPPED_BY_FEATURE_FLAG",
        project_id: "project-1",
        status: "skipped",
        variable_id: "tank_level",
        event_id: "evt-1",
        policy_id: null,
        policy_type: null,
        policy_version: null,
        policy_priority: null,
        summary: "feature_flag_disabled",
        envelope: {}
      }
    ]);

    const repo: IControlObservabilityRepository = {
      findLatestRecommendations: vi.fn(),
      findAuditEntries,
      getStatus: vi.fn()
    };

    const service = new ControlObservabilityService({ observabilityRepo: repo });
    const result = await service.listAudit({
      projectId: "project-1",
      status: "skipped",
      limit: 25
    });

    expect(findAuditEntries).toHaveBeenCalledWith({
      projectId: "project-1",
      status: "skipped",
      limit: 25
    });
    expect(result[0].status).toBe("skipped");
  });

  it("returns status snapshot", async () => {
    const getStatus = vi.fn().mockResolvedValue({
      activity_status: "active",
      latest_audit_at: "2026-04-29T00:00:00.000Z",
      latest_recommendation_at: "2026-04-29T00:00:00.000Z",
      latest_skipped_at: null,
      enabled_projects: 2,
      enabled_policies: 3,
      projects_with_policies: 2,
      audits_last_24h: 10,
      recommendations_last_24h: 7,
      skipped_last_24h: 2,
      errors_last_24h: 1
    });

    const repo: IControlObservabilityRepository = {
      findLatestRecommendations: vi.fn(),
      findAuditEntries: vi.fn(),
      getStatus
    };

    const service = new ControlObservabilityService({ observabilityRepo: repo });
    const result = await service.getStatus();

    expect(getStatus).toHaveBeenCalledTimes(1);
    expect(result.activity_status).toBe("active");
    expect(result.enabled_policies).toBe(3);
  });
});
