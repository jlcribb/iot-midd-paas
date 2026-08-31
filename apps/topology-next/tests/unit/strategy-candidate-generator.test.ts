import { describe, expect, it } from "vitest";
import { ValidationError } from "@/lib/errors/domain-errors";
import { generateGridSearch, hashCandidate, hashSearchSpace } from "@/lib/strategy/candidate-generator";

describe("strategy candidate Grid generator", () => {
  it("uses decimal-safe inclusive ranges and canonical lexicographic candidate order", () => {
    const generated = generateGridSearch("proportional", { setpoint_value: { values: [60, 50] }, gain: { min: 0.1, max: 0.3, step: 0.1 } });
    expect(generated.raw_combination_count).toBe(6);
    expect(generated.candidates.map((item) => item.parameters)).toEqual([
      { gain: 0.1, setpoint_value: 50 }, { gain: 0.1, setpoint_value: 60 },
      { gain: 0.2, setpoint_value: 50 }, { gain: 0.2, setpoint_value: 60 },
      { gain: 0.3, setpoint_value: 50 }, { gain: 0.3, setpoint_value: 60 }
    ]);
    expect(generated.candidates.map((item) => item.candidate_index)).toEqual([1, 2, 3, 4, 5, 6]);
  });

  it("is invariant to JSON key and explicit-value ordering", () => {
    const first = generateGridSearch("proportional", { gain: { values: [0.2, 0.1] }, setpoint_value: { values: [60, 50] } });
    const second = generateGridSearch("proportional", { setpoint_value: { values: [50, 60] }, gain: { values: [0.1, 0.2] } });
    expect(second.search_space_hash).toBe(first.search_space_hash);
    expect(second.candidates).toEqual(first.candidates);
    expect(hashSearchSpace("proportional", first.normalized_definition)).toBe(first.search_space_hash);
    expect(hashCandidate("proportional", { setpoint_value: 50, gain: 0.1 })).toBe(first.candidates[0].candidate_hash);
  });

  it("records invalid real-controller combinations without assigning their indices", () => {
    const generated = generateGridSearch("proportional", { gain: { values: [1] }, setpoint_value: { values: [50] }, min_action: { values: [1, 3] }, max_action: { values: [2, 4] } });
    expect(generated.raw_combination_count).toBe(4);
    expect(generated.invalid_combination_count).toBe(1);
    expect(generated.invalid_combination_summary).toEqual([{ reason: "min_action_must_not_exceed_max_action", count: 1 }]);
    expect(generated.candidates.map((candidate) => candidate.candidate_index)).toEqual([1, 2, 3]);
  });

  it("supports the actual threshold schema and rejects synthetic parameters", () => {
    expect(generateGridSearch("threshold", { tolerance: { values: [0, 0.5] }, increase_step: { values: [1] }, decrease_step: { values: [1, 2] } }).candidates).toHaveLength(4);
    expect(() => generateGridSearch("threshold", { tolerance: { values: [0] }, increase_step: { values: [1] }, decrease_step: { values: [1] }, lower: { values: [0] } })).toThrow(ValidationError);
  });

  it("rejects misaligned ranges and oversized spaces before enumeration", () => {
    expect(() => generateGridSearch("proportional", { gain: { min: 0, max: 1, step: 0.3 }, setpoint_value: { values: [50] } })).toThrow(ValidationError);
    expect(() => generateGridSearch("proportional", { gain: { values: Array.from({ length: 1001 }, (_, index) => index + 1) }, setpoint_value: { values: [50] } })).toThrow(/SEARCH_SPACE_TOO_LARGE/);
  });
});
