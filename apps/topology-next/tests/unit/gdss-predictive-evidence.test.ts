import { describe, expect, it } from "vitest";
import {
  assertPredictiveEvidenceAccess,
  assessPosition,
  canonicalPredictivePosition,
  domainAssessmentHash,
  domainContextSnapshotSchema,
  evidenceSetHash,
  evaluateDomain,
  predictivePositionHash,
  strengthAxes,
  validateStrengthAxes,
  type DomainPredicate,
} from "@/lib/gdss/validation";

const uuid = (n: number) =>
  `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const unit = { key: "celsius", revision: 1 };
const range: DomainPredicate = {
  predicateKey: "temperature-range",
  predicateType: "NUMERIC_RANGE",
  variableKey: "temperature",
  unit,
  rationale: "declared range",
  lowerBound: 10,
  upperBound: 40,
  lowerInclusive: true,
  upperInclusive: true,
};
const context = (temperature?: number) => ({
  semanticVersion: "GDSS_DOMAIN_CONTEXT_V1" as const,
  values:
    temperature === undefined
      ? []
      : [
          {
            kind: "NUMERIC" as const,
            variableKey: "temperature",
            value: temperature,
            unit,
          },
        ],
});

describe("GDSS-006E governed domain and predictive evidence", () => {
  it("evaluates numeric ranges and exact declared boundaries deterministically", () => {
    expect(evaluateDomain([range], context(20)).result).toBe(
      "WITHIN_VALIDITY_DOMAIN",
    );
    expect(evaluateDomain([range], context(10)).result).toBe(
      "NEAR_DOMAIN_BOUNDARY",
    );
    expect(evaluateDomain([range], context(41)).result).toBe(
      "OUTSIDE_VALIDITY_DOMAIN",
    );
  });

  it("fails closed when required context is absent or incompatible", () => {
    expect(evaluateDomain([range], context()).result).toBe("DOMAIN_UNKNOWN");
    expect(
      evaluateDomain([range], {
        semanticVersion: "GDSS_DOMAIN_CONTEXT_V1",
        values: [
          { kind: "CATEGORICAL", variableKey: "temperature", value: "warm" },
        ],
      }).result,
    ).toBe("DOMAIN_UNKNOWN");
  });

  it("uses exact categorical and boolean membership without fuzzy inference", () => {
    const predicates: DomainPredicate[] = [
      {
        predicateKey: "regime",
        predicateType: "CATEGORICAL_MEMBERSHIP",
        variableKey: "regime",
        unit: null,
        rationale: "exact",
        allowedValues: ["summer"],
      },
      {
        predicateKey: "enabled",
        predicateType: "BOOLEAN_CONDITION",
        variableKey: "enabled",
        unit: null,
        rationale: "declared",
        expected: true,
      },
    ];
    expect(
      evaluateDomain(predicates, {
        semanticVersion: "GDSS_DOMAIN_CONTEXT_V1",
        values: [
          { kind: "CATEGORICAL", variableKey: "regime", value: "summer" },
          { kind: "BOOLEAN", variableKey: "enabled", value: true },
        ],
      }).result,
    ).toBe("WITHIN_VALIDITY_DOMAIN");
    expect(
      evaluateDomain(predicates, {
        semanticVersion: "GDSS_DOMAIN_CONTEXT_V1",
        values: [
          { kind: "CATEGORICAL", variableKey: "regime", value: "Summer" },
          { kind: "BOOLEAN", variableKey: "enabled", value: true },
        ],
      }).result,
    ).toBe("OUTSIDE_VALIDITY_DOMAIN");
  });

  it("distinguishes declared-domain membership from empirical support", () => {
    const support = [
      {
        kind: "NUMERIC_RANGE" as const,
        variableKey: "temperature",
        lowerBound: 18,
        upperBound: 24,
        unit,
        evidenceAssessmentIds: [uuid(1)],
      },
    ];
    expect(evaluateDomain([range], context(30)).result).toBe(
      "WITHIN_VALIDITY_DOMAIN",
    );
    expect(assessPosition("WITHIN_VALIDITY_DOMAIN", context(30), support)).toBe(
      "EXTRAPOLATION",
    );
    expect(assessPosition("WITHIN_VALIDITY_DOMAIN", context(20), support)).toBe(
      "INTERPOLATION",
    );
    expect(assessPosition("WITHIN_VALIDITY_DOMAIN", context(18), support)).toBe(
      "BOUNDARY_PREDICTION",
    );
  });

  it("preserves unknown position instead of inferring interpolation", () => {
    expect(
      assessPosition("DOMAIN_UNKNOWN", context(), [
        {
          kind: "NUMERIC_RANGE",
          variableKey: "temperature",
          lowerBound: 18,
          upperBound: 24,
          unit,
          evidenceAssessmentIds: [uuid(1)],
        },
      ]),
    ).toBe("UNKNOWN_POSITION");
  });

  it("canonicalizes support and context order before hashing", () => {
    const base = {
      semanticVersion: "GDSS_PREDICTIVE_POSITION_V1" as const,
      domainAssessmentId: uuid(1),
      modelVersionId: uuid(2),
      validityDomainVersionId: uuid(3),
      validationRunId: uuid(4),
      targetKey: "level",
      horizonKey: "5m",
      contextSnapshot: {
        semanticVersion: "GDSS_DOMAIN_CONTEXT_V1" as const,
        values: [
          { kind: "BOOLEAN" as const, variableKey: "b", value: true },
          { kind: "NUMERIC" as const, variableKey: "a", value: 2, unit },
        ],
      },
      supportDimensions: [
        {
          kind: "BOOLEAN_SET" as const,
          variableKey: "b",
          values: [true],
          evidenceAssessmentIds: [uuid(6), uuid(5)],
        },
        {
          kind: "NUMERIC_RANGE" as const,
          variableKey: "a",
          lowerBound: 1,
          upperBound: 3,
          unit,
          evidenceAssessmentIds: [uuid(7)],
        },
      ],
      idempotencyKey: "position-1",
    };
    const canonical = canonicalPredictivePosition(base);
    expect(
      canonical.contextSnapshot.values.map((value) => value.variableKey),
    ).toEqual(["a", "b"]);
    expect(
      canonical.supportDimensions.map((value) => value.variableKey),
    ).toEqual(["a", "b"]);
    expect(predictivePositionHash(canonical)).toBe(
      predictivePositionHash(
        canonicalPredictivePosition({
          ...base,
          contextSnapshot: {
            ...base.contextSnapshot,
            values: [...base.contextSnapshot.values].reverse(),
          },
          supportDimensions: [...base.supportDimensions].reverse(),
        }),
      ),
    );
  });

  it("makes any epistemically relevant evidence membership change alter the hash", () => {
    const one = evidenceSetHash({
      model: uuid(1),
      references: [{ id: uuid(2), role: "SUPPORTING" }],
    });
    expect(
      evidenceSetHash({
        model: uuid(1),
        references: [{ id: uuid(2), role: "SUPPORTING" }],
      }),
    ).toBe(one);
    expect(
      evidenceSetHash({
        model: uuid(1),
        references: [
          { id: uuid(2), role: "SUPPORTING" },
          { id: uuid(3), role: "CONTRADICTING" },
        ],
      }),
    ).not.toBe(one);
  });

  it("requires exactly seven independent strength axes and never a global score", () => {
    const axes = strengthAxes.map((axis) => ({
      axis,
      state: "LIMITED" as const,
    }));
    expect(validateStrengthAxes(axes)).toHaveLength(7);
    expect(() => validateStrengthAxes(axes.slice(1))).toThrow(
      "EVIDENCE_STRENGTH_AXIS_INVALID",
    );
    expect(JSON.stringify(axes)).not.toMatch(/score|overall/i);
  });

  it("keeps evidence completeness separate from strength", () => {
    const complete = { state: "COMPLETE", missing: [] as string[] };
    const axes = strengthAxes.map((axis) => ({
      axis,
      state:
        axis === "REPLICATION"
          ? ("INSUFFICIENT" as const)
          : ("ADEQUATE" as const),
    }));
    expect(complete.state).toBe("COMPLETE");
    expect(axes.find((item) => item.axis === "REPLICATION")?.state).toBe(
      "INSUFFICIENT",
    );
  });

  it("enforces project-scoped OAuth assembly authorization", () => {
    const projectId = uuid(99);
    const operator = {
      user_id: "operator@example.test",
      display_name: "Operator",
      auth_source: "oauth_session" as const,
      role: "operator" as const,
      project_ids: [projectId],
      project_roles: { [projectId]: "operator" as const },
      all_projects: false,
    };
    expect(() =>
      assertPredictiveEvidenceAccess(
        operator,
        projectId,
        "ASSEMBLE_PREDICTIVE_EVIDENCE",
      ),
    ).not.toThrow();
    expect(() =>
      assertPredictiveEvidenceAccess(
        {
          ...operator,
          role: "viewer",
          project_roles: { [projectId]: "viewer" },
        },
        projectId,
        "ASSEMBLE_PREDICTIVE_EVIDENCE",
      ),
    ).toThrow();
    expect(() =>
      assertPredictiveEvidenceAccess(
        { ...operator, auth_source: "dev_fallback" },
        projectId,
        "ASSEMBLE_PREDICTIVE_EVIDENCE",
      ),
    ).toThrow();
  });

  it("rejects duplicate context variables", () => {
    expect(() =>
      domainContextSnapshotSchema.parse({
        semanticVersion: "GDSS_DOMAIN_CONTEXT_V1",
        values: [
          { kind: "BOOLEAN", variableKey: "x", value: true },
          { kind: "BOOLEAN", variableKey: "x", value: false },
        ],
      }),
    ).toThrow();
  });

  it("measures domain, support, profile and 100/1000-reference hashing diagnostically", () => {
    const predicates = Array.from({ length: 64 }, (_, index) => ({
      ...range,
      predicateKey: `p${index}`,
      variableKey: `v${index}`,
    }));
    const values = Array.from({ length: 64 }, (_, index) => ({
      kind: "NUMERIC" as const,
      variableKey: `v${index}`,
      value: 20,
      unit,
    }));
    const start = performance.now();
    evaluateDomain(predicates, {
      semanticVersion: "GDSS_DOMAIN_CONTEXT_V1",
      values,
    });
    const domainMs = performance.now() - start;
    const supportStart = performance.now();
    assessPosition(
      "WITHIN_VALIDITY_DOMAIN",
      { semanticVersion: "GDSS_DOMAIN_CONTEXT_V1", values },
      predicates.map((predicate, index) => ({
        kind: "NUMERIC_RANGE" as const,
        variableKey: predicate.variableKey,
        lowerBound: 18,
        upperBound: 24,
        unit,
        evidenceAssessmentIds: [uuid(index + 1)],
      })),
    );
    const supportMs = performance.now() - supportStart;
    const hashStart = performance.now();
    const hash100 = evidenceSetHash({
      references: Array.from({ length: 100 }, (_, index) => ({
        id: uuid(index + 1),
      })),
    });
    const hash100Ms = performance.now() - hashStart;
    const thousandStart = performance.now();
    const hash1000 = evidenceSetHash({
      references: Array.from({ length: 1000 }, (_, index) => ({
        id: uuid(index + 1),
      })),
    });
    const hash1000Ms = performance.now() - thousandStart;
    const profileStart = performance.now();
    validateStrengthAxes(
      strengthAxes.map((axis) => ({ axis, state: "ADEQUATE" })),
    );
    const profileMs = performance.now() - profileStart;
    expect(hash100).not.toBe(hash1000);
    console.log(
      "GDSS006E_PERFORMANCE",
      JSON.stringify({
        predicates: 64,
        domainMs: +domainMs.toFixed(3),
        supportMs: +supportMs.toFixed(3),
        references100HashMs: +hash100Ms.toFixed(3),
        references1000HashMs: +hash1000Ms.toFixed(3),
        profileMs: +profileMs.toFixed(3),
      }),
    );
  });
});
