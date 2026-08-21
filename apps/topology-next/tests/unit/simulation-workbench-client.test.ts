import { afterEach, describe, expect, it, vi } from "vitest";
import { simulationWorkbenchClient } from "@/components/control/simulation-workbench-client";

describe("M5.6 workbench policy query", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uses the maximum page size accepted by the governed operations contract", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ success: true, data: { items: [] } }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await simulationWorkbenchClient.policies("11111111-1111-4111-8111-111111111111");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/control/operations/projects/11111111-1111-4111-8111-111111111111/policies?limit=100&offset=0",
      expect.objectContaining({ cache: "no-store" })
    );
  });
});
