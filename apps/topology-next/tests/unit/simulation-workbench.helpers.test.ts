import { describe, expect, it } from "vitest";
import { reproducibilityEvidence } from "@/components/control/simulation-workbench.helpers";

describe("M5.5 workbench presentation helpers", () => {
  it("only compares backend-materialized opaque result fingerprints", () => {
    expect(reproducibilityEvidence([{ result_fingerprint: "same" }, { result_fingerprint: "same" }] as never)).toEqual({ status: "CONSISTENT", count: 2 });
    expect(reproducibilityEvidence([{ result_fingerprint: "one" }, { result_fingerprint: "two" }] as never)).toEqual({ status: "DIFFERENT", count: 2 });
    expect(reproducibilityEvidence([{ result_fingerprint: "one" }] as never)).toEqual({ status: "PENDING", count: 1 });
  });
});
