import { describe, expect, it } from "vitest";
import { createEvaluationProfileSchema } from "@/lib/validators/evaluation-profile.schemas";

const metricA = "11111111-1111-4111-8111-111111111111";
const metricB = "22222222-2222-4222-8222-222222222222";

describe("createEvaluationProfileSchema", () => {
  it("accepts a normalized, complete profile", () => {
    expect(createEvaluationProfileSchema.parse({ code: "water_level_control_v1", name: "Water level", metrics: [
      { metric_id: metricA, weight: 0.7 }, { metric_id: metricB, weight: 0.3, required: false }
    ] })).toMatchObject({ description: "", metadata: {}, metrics: [{ required: true }, { required: false }] });
  });

  it("rejects duplicate metrics and non-unitary weights", () => {
    expect(() => createEvaluationProfileSchema.parse({ code: "water_level_control_v1", name: "Water level", metrics: [
      { metric_id: metricA, weight: 0.5 }, { metric_id: metricA, weight: 0.4 }
    ] })).toThrow(/metric_id must be unique|weights must sum to 1/);
  });
});
