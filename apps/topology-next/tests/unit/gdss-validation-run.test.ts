import { describe, expect, it } from "vitest";
import { randomUUID } from "node:crypto";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import {
  assessPairIntegrity,
  assertValidationRunAccess,
  canTransitionValidationRun,
  canonicalPairSet,
  observationReferenceHash,
  predictionCommitmentHash,
  predictionHash,
  predictionObservationPairHash,
  predictionPairSetHash,
  type ObservationReferenceContent,
  type PairingContract,
  type PredictionContent,
} from "@/lib/gdss/validation";

const h = (c: string) => c.repeat(64),
  project = "11111111-1111-4111-8111-111111111111";
const prediction = (
  overrides: Partial<PredictionContent> = {},
): PredictionContent => ({
  semanticVersion: "GDSS_PREDICTION_V1",
  modelVersionId: randomUUID(),
  modelHash: h("a"),
  targetKey: "level",
  forecastOrigin: "2026-01-01T00:00:00.000Z",
  horizonKey: "five_min",
  horizonDuration: 5,
  horizonUnit: { key: "minute", revision: 1 },
  predictedValue: 4.2,
  predictedUnit: { key: "meter", revision: 1 },
  inputSnapshotHash: h("b"),
  parameterSnapshotHash: h("c"),
  boundaryConditionHash: h("d"),
  predictionMode: "PROSPECTIVE",
  ...overrides,
});
const observation = (
  overrides: Partial<ObservationReferenceContent> = {},
): ObservationReferenceContent => ({
  semanticVersion: "GDSS_OBSERVATION_REFERENCE_V1",
  observationIdentity: "sensor:1:at",
  source: "sensor:1",
  targetKey: "level",
  observedValue: 4.1,
  unit: { key: "meter", revision: 1 },
  measurementTime: "2026-01-01T00:05:00.000Z",
  availabilityTime: "2026-01-01T00:06:00.000Z",
  ingestionTime: "2026-01-01T00:07:00.000Z",
  sourceContentHash: h("e"),
  qualityProvenanceReference: null,
  ...overrides,
});
const contract: PairingContract = {
  semanticVersion: "GDSS_PREDICTION_OBSERVATION_PAIR_V1",
  targetKey: "level",
  horizonKey: "five_min",
  pairingRule: "EXACT_TIMESTAMP",
};
const actor = (
  role: "viewer" | "operator" | "admin",
  source: "oauth_session" | "dev_fallback" = "oauth_session",
): ControlActor => ({
  user_id: "u",
  actor_id: "u",
  display_name: "u",
  auth_source: source,
  role,
  project_ids: [project],
  project_roles: { [project]: role },
  all_projects: false,
});
describe("GDSS-006C validation run and pairing contracts", () => {
  it("hashes identical prediction semantics deterministically", () => {
    const p = prediction();
    expect(predictionHash(p)).toBe(predictionHash({ ...p }));
    expect(predictionHash(p)).not.toBe(
      predictionHash({ ...p, predictedValue: 4.3 }),
    );
    expect(predictionHash(p)).not.toBe(
      predictionHash({ ...p, horizonDuration: 6 }),
    );
    expect(predictionHash(p)).not.toBe(
      predictionHash({ ...p, modelVersionId: randomUUID() }),
    );
    expect(predictionHash(p)).not.toBe(
      predictionHash({ ...p, inputSnapshotHash: h("f") }),
    );
  });
  it("separates prediction and deterministic commitment identity", () => {
    const hash = predictionHash(prediction());
    expect(predictionCommitmentHash(hash)).toBe(predictionCommitmentHash(hash));
    expect(predictionCommitmentHash(hash)).not.toBe(hash);
  });
  it("hashes pair rule, observation and tolerance", () => {
    const p = predictionHash(prediction()),
      o = observationReferenceHash(observation()),
      base = predictionObservationPairHash(p, o, contract);
    expect(base).toBe(predictionObservationPairHash(p, o, { ...contract }));
    expect(base).not.toBe(
      predictionObservationPairHash(
        p,
        observationReferenceHash(observation({ observationIdentity: "other" })),
        contract,
      ),
    );
    expect(base).not.toBe(
      predictionObservationPairHash(p, o, {
        ...contract,
        pairingRule: "NEAREST_WITHIN_TOLERANCE",
        tolerance: 1,
        toleranceUnit: { key: "second", revision: 1 },
        directionality: "BIDIRECTIONAL",
      }),
    );
  });
  it("canonicalizes pair set order and changes identity for membership/scope", () => {
    const a = h("a"),
      b = h("b"),
      base = {
        semanticVersion: "GDSS_PREDICTION_PAIR_SET_V1" as const,
        targetKey: "level",
        horizonKey: "five_min",
        scope: "validation",
        pairHashes: [a, b],
      };
    expect(predictionPairSetHash(base)).toBe(
      predictionPairSetHash({ ...base, pairHashes: [b, a] }),
    );
    expect(
      canonicalPairSet({ ...base, pairHashes: [a, a, b] }).pairHashes,
    ).toEqual([a, b]);
    expect(predictionPairSetHash(base)).not.toBe(
      predictionPairSetHash({ ...base, pairHashes: [a] }),
    );
    expect(predictionPairSetHash(base)).not.toBe(
      predictionPairSetHash({ ...base, targetKey: "flow" }),
    );
    expect(predictionPairSetHash(base)).not.toBe(
      predictionPairSetHash({ ...base, horizonKey: "hour" }),
    );
  });
  it("fails closed for unknown availability and detects post-observation commitment", () => {
    const p = prediction();
    expect(
      assessPairIntegrity(
        p,
        observation({ availabilityTime: null }),
        contract,
        "2025-12-31T00:00:00.000Z",
      ),
    ).toBe("TEMPORAL_INTEGRITY_UNKNOWN");
    expect(
      assessPairIntegrity(
        p,
        observation(),
        contract,
        "2026-01-01T00:06:00.001Z",
      ),
    ).toBe("PREDICTION_AFTER_OBSERVATION");
    expect(
      assessPairIntegrity(
        p,
        observation(),
        contract,
        "2026-01-01T00:05:59.999Z",
      ),
    ).toBe("PASS");
  });
  it("rejects target, horizon and unit mismatches", () => {
    const p = prediction();
    expect(
      assessPairIntegrity(
        p,
        observation({ targetKey: "humidity" }),
        contract,
        "2025-01-01T00:00:00.000Z",
      ),
    ).toBe("TARGET_MISMATCH");
    expect(
      assessPairIntegrity(
        p,
        observation(),
        { ...contract, horizonKey: "hour" },
        "2025-01-01T00:00:00.000Z",
      ),
    ).toBe("HORIZON_MISMATCH");
    expect(
      assessPairIntegrity(
        p,
        observation({ unit: { key: "siemens", revision: 1 } }),
        contract,
        "2025-01-01T00:00:00.000Z",
      ),
    ).toBe("UNIT_MISMATCH");
  });
  it("enforces lifecycle and RUN_VALIDATION authorization", () => {
    expect(canTransitionValidationRun("CREATED", "READY")).toBe(true);
    expect(canTransitionValidationRun("READY", "COMPLETED")).toBe(false);
    expect(canTransitionValidationRun("COMPLETED", "READY")).toBe(false);
    expect(() =>
      assertValidationRunAccess(actor("operator"), project, "RUN_VALIDATION"),
    ).not.toThrow();
    expect(() =>
      assertValidationRunAccess(actor("viewer"), project, "RUN_VALIDATION"),
    ).toThrow();
    expect(() =>
      assertValidationRunAccess(
        actor("admin", "dev_fallback"),
        project,
        "RUN_VALIDATION",
      ),
    ).toThrow();
  });
  it("does not accept metric, claim, capability or authority fields", () => {
    expect(() =>
      predictionHash({
        ...prediction(),
        ValidationMetricResult: {},
        GovernedPredictiveClaim: {},
        physical_authority: "ALLOW",
      }),
    ).toThrow();
  });
  it("measures prediction and 10k pair-set hashing diagnostically", () => {
    const p = prediction(),
      start = performance.now();
    for (let i = 0; i < 1000; i++) predictionHash({ ...p, predictedValue: i });
    const predictionMs = performance.now() - start,
      pairs = Array.from({ length: 10000 }, (_, i) =>
        i.toString(16).padStart(64, "0"),
      ),
      setStart = performance.now();
    predictionPairSetHash({
      semanticVersion: "GDSS_PREDICTION_PAIR_SET_V1",
      targetKey: "level",
      horizonKey: "five_min",
      scope: "scale",
      pairHashes: pairs,
    });
    console.log(
      "GDSS006C_PERFORMANCE",
      JSON.stringify({
        predictionHashes: 1000,
        predictionHashMs: Number(predictionMs.toFixed(3)),
        pairSetSize: 10000,
        pairSetHashMs: Number((performance.now() - setStart).toFixed(3)),
      }),
    );
  });
});
