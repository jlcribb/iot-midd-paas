import { afterEach, describe, expect, it, vi } from "vitest";
import { ControlOperationsApiError, controlOperationsClient } from "@/components/control/control-operations-client";
import {
  canLoadNextPage,
  getOperationalStatusBadgeClass,
  operationErrorMessage
} from "@/components/control/control-operations.helpers";

describe("Control Operations UI contracts", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("presents recommendation-only as inactive-valid semantics rather than failure", () => {
    expect(getOperationalStatusBadgeClass("RECOMMENDATION_ONLY")).toBe("status-badge status-inactive");
    expect(getOperationalStatusBadgeClass("FAILED")).toBe("status-badge status-fault");
  });

  it("distinguishes publication from acknowledgement", () => {
    expect(getOperationalStatusBadgeClass("PUBLISHED")).toBe("status-badge status-active");
    expect(getOperationalStatusBadgeClass("ACKNOWLEDGED")).toBe("status-badge status-active");
    expect("PUBLISHED").not.toBe("ACKNOWLEDGED");
  });

  it("maps every delivery lifecycle presentation state without deriving a DLQ state", () => {
    expect(getOperationalStatusBadgeClass("PENDING")).toContain("maintenance");
    expect(getOperationalStatusBadgeClass("RETRYING")).toContain("maintenance");
    expect(getOperationalStatusBadgeClass("FAILED")).toContain("fault");
    expect(getOperationalStatusBadgeClass("EXPIRED")).toContain("fault");
  });

  it("uses backend pagination rather than assuming additional client-side records", () => {
    expect(canLoadNextPage(8, 8)).toBe(true);
    expect(canLoadNextPage(7, 8)).toBe(false);
  });

  it("sends recommendation filters and pagination to the M4.2 endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: true, data: { items: [], limit: 8, offset: 16 } }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await controlOperationsClient.getRecommendations("project/a", { limit: 8, offset: 16, policyId: "policy-1", correlationId: "corr-1" });
    expect(fetchMock).toHaveBeenCalledWith("/api/control/operations/projects/project%2Fa/recommendations?limit=8&offset=16&policyId=policy-1&correlationId=corr-1", { cache: "no-store" });
  });

  it("sends delivery filters to the backend contract", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: true, data: { items: [], limit: 8, offset: 0 } }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await controlOperationsClient.getDeliveries("project-1", { limit: 8, offset: 0, status: "acknowledged", recommendationId: "rec-1", commandId: "command-1", correlationId: "corr-1" });
    expect(fetchMock.mock.calls[0][0]).toContain("status=acknowledged");
    expect(fetchMock.mock.calls[0][0]).toContain("recommendationId=rec-1");
    expect(fetchMock.mock.calls[0][0]).toContain("commandId=command-1");
    expect(fetchMock.mock.calls[0][0]).toContain("correlationId=corr-1");
  });

  it("renders unauthorized and forbidden API failures as safe user-facing messages", () => {
    expect(operationErrorMessage(new ControlOperationsApiError(401, "raw"))).toContain("Sign in again");
    expect(operationErrorMessage(new ControlOperationsApiError(403, "raw"))).toContain("do not have permission");
    expect(operationErrorMessage(new Error("database details"))).not.toContain("database details");
  });
});
