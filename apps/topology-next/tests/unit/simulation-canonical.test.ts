import { describe, expect, it } from "vitest";
import { canonicalSerialize, experimentFingerprint, sha256Canonical } from "@/lib/simulation/canonical";

describe("simulation snapshot canonicalization", () => {
  it("is stable across object ordering and normalizes optional undefined values", () => {
    expect(canonicalSerialize({ b: 2, a: { z: null, ignored: undefined } })).toBe(canonicalSerialize({ a: { z: null }, b: 2 }));
  });

  it("uses lowercase SHA-256 component hashes and a deterministic experiment fingerprint", () => {
    const hashes = {
      policy_snapshot_hash: sha256Canonical({ policy: "p" }), topology_snapshot_hash: sha256Canonical({ topology: "t" }),
      dataset_snapshot_hash: sha256Canonical({ dataset: [1] }), configuration_snapshot_hash: sha256Canonical({ config: 1 })
    };
    expect(hashes.policy_snapshot_hash).toMatch(/^[0-9a-f]{64}$/);
    expect(experimentFingerprint(hashes)).toBe(experimentFingerprint({ ...hashes }));
    expect(experimentFingerprint({ ...hashes, dataset_snapshot_hash: sha256Canonical({ dataset: [2] }) })).not.toBe(experimentFingerprint(hashes));
  });
});
