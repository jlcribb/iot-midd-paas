import { describe, expect, it } from "vitest";
import { ZodError } from "zod";
import { createAssetSchema } from "@/lib/validators/asset.schemas";

describe("Validators", () => {
  it("rejects invalid asset payload", () => {
    expect(() =>
      createAssetSchema.parse({
        project_id: "not-a-uuid",
        sector_id: "also-not-uuid",
        asset_type: "sensor",
        name: "",
        subtype: "",
        status: "active",
        metadata: {}
      })
    ).toThrow(ZodError);
  });
});
