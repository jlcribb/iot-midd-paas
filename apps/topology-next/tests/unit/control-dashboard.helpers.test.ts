import { describe, expect, it } from "vitest";
import type { ControlAuditView, ControlRecommendationView } from "@/lib/dto/control.dto";
import {
  auditKey,
  formatControlTimestamp,
  getActivityBadgeClass,
  getActivityLabel,
  recommendationKey
} from "@/components/control/control-dashboard.helpers";

describe("control-dashboard.helpers", () => {
  it("formats missing timestamps defensively", () => {
    expect(formatControlTimestamp(null)).toBe("Sin datos");
    expect(formatControlTimestamp(undefined)).toBe("Sin datos");
  });

  it("falls back to raw value when timestamp is invalid", () => {
    expect(formatControlTimestamp("not-a-date")).toBe("not-a-date");
  });

  it("maps activity statuses to badge classes and labels", () => {
    expect(getActivityBadgeClass("active")).toBe("status-badge status-active");
    expect(getActivityBadgeClass("stale")).toBe("status-badge status-maintenance");
    expect(getActivityBadgeClass("idle")).toBe("status-badge status-inactive");
    expect(getActivityLabel("active")).toBe("Activo");
    expect(getActivityLabel("stale")).toBe("Sin actividad reciente");
    expect(getActivityLabel("idle")).toBe("Sin actividad");
  });

  it("builds stable recommendation keys", () => {
    const recommendation: ControlRecommendationView = {
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
      policy_version: 2,
      policy_priority: 10
    };

    expect(recommendationKey(recommendation)).toBe("audit-1:evt-1");
  });

  it("builds stable audit keys", () => {
    const audit: ControlAuditView = {
      id: 11,
      ts: "2026-04-29T00:00:00.000Z",
      action: "CONTROL_RECOMMENDATION_EMITTED",
      project_id: "project-1",
      status: "processed",
      variable_id: "tank_level",
      event_id: null,
      policy_id: "policy-1",
      policy_type: "proportional",
      policy_version: 2,
      policy_priority: 10,
      summary: "recommendation emitted",
      envelope: {}
    };

    expect(auditKey(audit)).toBe("11:event");
  });
});
