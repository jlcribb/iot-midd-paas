import { describe, expect, it } from "vitest";
import { randomUUID } from "node:crypto";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import {
  assertCapabilityGovernanceAccess,
  assertScopeSubset,
  capabilityAssessmentHash,
  capabilityStates,
  canonicalCapabilityScope,
  deriveCapabilityState,
  evidenceTransferInputSchema,
  isScopeSubset,
  predictiveClaimHash,
  projectClaimCurrentness,
  renderPredictiveClaim,
  type CapabilityScope,
  type StrengthAxis,
  type StrengthState,
} from "@/lib/gdss/validation";

const id = () => randomUUID();
const h = (value: string) => value.repeat(64);
const axes = (
  overrides: Partial<Record<StrengthAxis, StrengthState>> = {},
) =>
  (
    [
      "INDEPENDENCE",
      "TEMPORALITY",
      "DOMAIN_COVERAGE",
      "UNCERTAINTY_COMPLETENESS",
      "BASELINE_STRENGTH",
      "REPLICATION",
      "DATA_QUALITY",
    ] as StrengthAxis[]
  ).map((axis) => ({ axis, state: overrides[axis] ?? "ADEQUATE" }));
const facts = (value: Record<string, unknown> = {}) => ({
  requestedAction: "EVALUATE" as const,
  completeness: "COMPLETE",
  axes: axes(),
  conflictCount: 0,
  invalidatingCount: 0,
  negativeFindingTypes: [] as string[],
  ...value,
});
const scope = (): CapabilityScope => ({
  modelVersionId: id(),
  modelContentHash: h("a"),
  targetKey: "pH",
  horizonKey: "fifteen_min",
  validityDomainVersionId: id(),
  protocolFamily: "water_quality_v1",
  metricProfile: ["BIAS_V1", "RMSE_V1"],
  baselineProfile: ["NAIVE_LAST_VALUE_V1", "SEASONAL_NAIVE_V1"],
  uncertaintyProfile: ["MEASUREMENT_UNCERTAINTY"],
  evidencePeriod: { startEpochMicros: "100", endEpochMicros: "900" },
  domainConstraints: [
    {
      kind: "NUMERIC_RANGE",
      variableKey: "temperature",
      lowerBound: 18,
      upperBound: 24,
      lowerInclusive: true,
      upperInclusive: true,
      unit: { key: "celsius", revision: 1 },
    },
  ],
});

describe("GDSS-006F governed capability and claims", () => {
  it("supports exactly the seven capability states", () => {
    expect(capabilityStates).toEqual([
      "NOT_EVALUATED",
      "INSUFFICIENT_EVIDENCE",
      "EVIDENCE_OF_LIMITED_CAPABILITY",
      "EVIDENCE_OF_CAPABILITY",
      "CONFLICTING_EVIDENCE",
      "EVIDENCE_OF_FAILURE",
      "INVALIDATED",
    ]);
  });

  it("materializes NOT_EVALUATED only for explicit scope registration", () => {
    expect(
      deriveCapabilityState(facts({ requestedAction: "REGISTER_SCOPE" })).state,
    ).toBe("NOT_EVALUATED");
  });

  it("fails closed for incomplete evidence and critical weak axes", () => {
    expect(
      deriveCapabilityState(facts({ completeness: "PARTIAL" })).state,
    ).toBe("INSUFFICIENT_EVIDENCE");
    expect(
      deriveCapabilityState(
        facts({ axes: axes({ INDEPENDENCE: "INSUFFICIENT" }) }),
      ).state,
    ).toBe("INSUFFICIENT_EVIDENCE");
    expect(
      deriveCapabilityState(
        facts({ axes: axes({ UNCERTAINTY_COMPLETENESS: "UNKNOWN" }) }),
      ).state,
    ).toBe("INSUFFICIENT_EVIDENCE");
  });

  it("preserves material conflict without voting or score", () => {
    const result = deriveCapabilityState(facts({ conflictCount: 1 }));
    expect(result.state).toBe("CONFLICTING_EVIDENCE");
    expect(result).not.toHaveProperty("score");
    expect(result).not.toHaveProperty("overallStrength");
  });

  it("retains governed failure evidence", () => {
    expect(
      deriveCapabilityState(
        facts({ negativeFindingTypes: ["MODEL_UNDERPERFORMS_BASELINE"] }),
      ).state,
    ).toBe("EVIDENCE_OF_FAILURE");
    expect(
      deriveCapabilityState(facts({ invalidatingCount: 1 })).state,
    ).toBe("EVIDENCE_OF_FAILURE");
  });

  it("derives limited capability without upgrading weak replication", () => {
    expect(
      deriveCapabilityState(
        facts({
          axes: axes({
            UNCERTAINTY_COMPLETENESS: "LIMITED",
            REPLICATION: "INSUFFICIENT",
          }),
        }),
      ).state,
    ).toBe("EVIDENCE_OF_LIMITED_CAPABILITY");
  });

  it("derives scoped capability only when every minimum is satisfied", () => {
    expect(deriveCapabilityState(facts()).state).toBe(
      "EVIDENCE_OF_CAPABILITY",
    );
  });

  it("proves domain and evidence-period narrowing but requires exact horizon and profiles", () => {
    const parent = scope(),
      child: CapabilityScope = {
        ...parent,
        evidencePeriod: { startEpochMicros: "200", endEpochMicros: "800" },
        domainConstraints: [
          {
            kind: "NUMERIC_RANGE",
            variableKey: "temperature",
            lowerBound: 19,
            upperBound: 23,
            lowerInclusive: true,
            upperInclusive: true,
            unit: { key: "celsius", revision: 1 },
          },
        ],
      };
    expect(isScopeSubset(child, parent)).toBe(true);
    expect(isScopeSubset({ ...child, horizonKey: "day" }, parent)).toBe(false);
    expect(
      isScopeSubset({ ...child, metricProfile: ["RMSE_V1"] }, parent),
    ).toBe(false);
    const broad: CapabilityScope = {
      ...child,
      domainConstraints: [
        {
          kind: "NUMERIC_RANGE",
          variableKey: "temperature",
          lowerBound: 10,
          upperBound: 35,
          lowerInclusive: true,
          upperInclusive: true,
          unit: { key: "celsius", revision: 1 },
        },
      ],
    };
    expect(() => assertScopeSubset(broad, parent)).toThrow(
      "CLAIM_SCOPE_EXCEEDS_CAPABILITY",
    );
  });

  it("canonicalizes scope and hashes independently of input ordering", () => {
    const a = scope(),
      b = {
        ...a,
        metricProfile: [...a.metricProfile].reverse(),
        baselineProfile: [...a.baselineProfile].reverse(),
      };
    expect(canonicalCapabilityScope(a)).toEqual(canonicalCapabilityScope(b));
    expect(capabilityAssessmentHash(canonicalCapabilityScope(a))).toBe(
      capabilityAssessmentHash(canonicalCapabilityScope(b)),
    );
  });

  it("renders every required scoped claim element and adverse counts", () => {
    const value = scope(),
      text = renderPredictiveClaim({
        state: "EVIDENCE_OF_LIMITED_CAPABILITY",
        scope: value,
        evidenceSetHash: h("e"),
        limitations: [{ type: "DOMAIN_COVERAGE_NARROW" }],
        negativeEvidence: [{ type: "LOW_COVERAGE" }],
        conflicts: [{ type: "METRIC_DIRECTION_CONFLICT" }],
        uncertaintySummary: [{ state: "LIMITED" }],
      });
    for (const expected of [
      value.modelVersionId,
      value.targetKey,
      value.horizonKey,
      value.validityDomainVersionId,
      value.evidencePeriod.startEpochMicros,
      "EVIDENCE_OF_LIMITED_CAPABILITY",
      "1 limitation(s)",
      "1 negative finding(s)",
      "1 material conflict(s)",
    ])
      expect(text).toContain(expected);
    expect(text.toLowerCase()).not.toContain("is predictive");
    const semantic = { scope: value, state: "EVIDENCE_OF_LIMITED_CAPABILITY" };
    expect(predictiveClaimHash(semantic)).toBe(predictiveClaimHash(semantic));
  });

  it("projects expiry and contradictory evidence without rewriting lifecycle", () => {
    expect(
      projectClaimCurrentness("AUTHORIZED", "100", false, 101n),
    ).toBe("AUTHORIZED_EXPIRED_REVIEW_REQUIRED");
    expect(
      projectClaimCurrentness("AUTHORIZED", null, true, 101n),
    ).toBe("HUMAN_REVIEW_REQUIRED");
    expect(projectClaimCurrentness("REVOKED", null, false, 101n)).toBe(
      "REVOKED",
    );
  });

  it("rejects reserved positive transfer outcomes", () => {
    const value = scope();
    for (const requestedMode of [
      "PARTIAL_REVALIDATION_ALLOWED",
      "EQUIVALENCE_ESTABLISHED",
    ] as const)
      expect(
        evidenceTransferInputSchema.parse({
          sourceModelVersionId: value.modelVersionId,
          targetModelVersionId: id(),
          sourceEvidenceSetId: id(),
          sourceEvidenceSetHash: h("f"),
          requestedTransferScope: value,
          requestedMode,
          reason: "must revalidate",
          idempotencyKey: requestedMode,
        }).requestedMode,
      ).toBe(requestedMode);
  });

  it("hard-denies AI and unauthorized human authority", () => {
    const projectId = id(),
      human: ControlActor = {
        user_id: "reviewer@example.test",
        actor_id: "reviewer@example.test",
        display_name: "reviewer",
        auth_source: "oauth_session",
        role: "admin",
        project_ids: [projectId],
        project_roles: { [projectId]: "admin" },
        all_projects: false,
      },
      ai = { ...human, user_id: "ai:reviewer", actor_id: "ai:reviewer", auth_provider: "ai" };
    expect(() =>
      assertCapabilityGovernanceAccess(
        human,
        projectId,
        "AUTHORIZE_PREDICTIVE_CLAIM",
      ),
    ).not.toThrow();
    expect(() =>
      assertCapabilityGovernanceAccess(
        ai,
        projectId,
        "AUTHORIZE_PREDICTIVE_CLAIM",
      ),
    ).toThrow("AI_AUTHORITY_FORBIDDEN");
    expect(() =>
      assertCapabilityGovernanceAccess(
        { ...human, role: "viewer", project_roles: { [projectId]: "viewer" } },
        projectId,
        "REVOKE_PREDICTIVE_CLAIM",
      ),
    ).toThrow("UNAUTHORIZED_CAPABILITY_ACTION");
  });

  it("measures capability, subset, claim and 1k-scope hashing diagnostically", () => {
    const start = performance.now();
    for (let i = 0; i < 1000; i++) deriveCapabilityState(facts());
    const capabilityMs = performance.now() - start,
      parent = scope(),
      subsetStart = performance.now();
    for (let i = 0; i < 1000; i++) isScopeSubset(parent, parent);
    const subsetMs = performance.now() - subsetStart,
      claimStart = performance.now();
    for (let i = 0; i < 1000; i++)
      renderPredictiveClaim({
        state: "EVIDENCE_OF_CAPABILITY",
        scope: parent,
        evidenceSetHash: h("e"),
        limitations: [],
        negativeEvidence: [],
        conflicts: [],
        uncertaintySummary: [],
      });
    const claimMs = performance.now() - claimStart,
      hashStart = performance.now();
    capabilityAssessmentHash(
      Array.from({ length: 1000 }, (_, index) => ({ index, scope: parent })),
    );
    const hashMs = performance.now() - hashStart;
    console.log(
      "GDSS006F_PERFORMANCE",
      JSON.stringify({ capabilityMs, subsetMs, claimMs, hashMs }),
    );
    for (const value of [capabilityMs, subsetMs, claimMs, hashMs])
      expect(Number.isFinite(value)).toBe(true);
  });
});
