import { describe, expect, it, vi } from "vitest";
import type { ControlActor, ControlRole } from "@/lib/dto/control-access.dto";
import {
  assertCapabilityGovernanceAccess,
  assertEvidenceCustodyAccess,
  assertPredictiveEvidenceAccess,
  capabilityScopeSchema,
  validationProtocolContentSchema,
} from "@/lib/gdss/validation";
import { GdssEvidenceCustodyService } from "@/lib/services/gdss-evidence-custody.service";
import { GdssPredictiveEvidenceService } from "@/lib/services/gdss-predictive-evidence.service";

const projectId = "11111111-1111-4111-8111-111111111111";
const uuid = "22222222-2222-4222-8222-222222222222";
const hash = "a".repeat(64);
const actor = (role: ControlRole, ai = false): ControlActor => ({
  user_id: ai ? `ai:${role}` : `${role}@example.test`,
  actor_id: ai ? `ai:${role}` : `${role}@example.test`,
  display_name: role,
  auth_provider: ai ? "ai" : "oauth",
  auth_source: "oauth_session",
  role,
  project_ids: [projectId],
  project_roles: { [projectId]: role },
  all_projects: false,
});
const criteria = (count: number) =>
  Array.from({ length: count }, (_, index) => ({
    criterionKey: `criterion-${index}`,
    metricKey: `METRIC_${index}`,
    metricVersion: "V1",
    operator: "LTE" as const,
    threshold: index,
    unit: null,
    scope: "GLOBAL" as const,
    scopeReference: null,
    required: true,
  }));
const protocol = (count: number) => ({
  semanticVersion: "GDSS_VALIDATION_PROTOCOL_V1" as const,
  modelIdentityId: uuid,
  modelVersionId: uuid,
  modelVersionNumber: 1,
  modelContentHash: hash,
  validityDomainVersionId: uuid,
  validityDomainHash: hash,
  targets: [{ targetKey: "level", variableReference: "V", unitReference: { key: "meter", revision: 1 }, aggregation: "NONE" as const, transformation: "IDENTITY" as const, semanticRole: "OBSERVED_TARGET" as const }],
  horizons: [{ horizonKey: "h1", duration: 1, unit: { key: "second", revision: 1 }, forecastOriginSemantics: "EXPLICIT_ORIGIN" as const }],
  acceptanceCriteria: criteria(count),
  exclusionPolicy: { version: "GDSS_VALIDATION_EXCLUSION_V1" as const, rules: [] },
  missingnessPolicy: { version: "GDSS_VALIDATION_MISSINGNESS_V1" as const, mode: "REJECT" as const },
  outlierPolicy: { version: "GDSS_VALIDATION_OUTLIER_V1" as const, mode: "INCLUDE" as const },
  multiplicityPolicy: { version: "GDSS_VALIDATION_MULTIPLICITY_V1" as const, mode: "NONE" as const },
  revalidationTriggers: ["METRIC_CHANGED" as const],
});
const scope = (metrics: number, baselines: number) => ({
  modelVersionId: uuid,
  modelContentHash: hash,
  targetKey: "level",
  horizonKey: "h1",
  validityDomainVersionId: uuid,
  protocolFamily: "family",
  metricProfile: Array.from({ length: metrics }, (_, index) => `metric-${index}`),
  baselineProfile: Array.from({ length: baselines }, (_, index) => `baseline-${index}`),
  uncertaintyProfile: ["declared"],
  evidencePeriod: { startEpochMicros: "1", endEpochMicros: "2" },
  domainConstraints: [{ kind: "BOOLEAN_SET" as const, variableKey: "enabled", values: [true] }],
});

describe("P024-R3 resource and AI authority remediation", () => {
  it("enforces distinct protocol metric definitions at 8, 16 and 17", () => {
    expect(validationProtocolContentSchema.safeParse(protocol(8)).success).toBe(true);
    expect(validationProtocolContentSchema.safeParse(protocol(16)).success).toBe(true);
    const result = validationProtocolContentSchema.safeParse(protocol(17));
    expect(result.success).toBe(false);
    if (!result.success) expect(result.error.message).toContain("METRIC_DEFINITIONS_PER_PROTOCOL limit=16 actual=17");
  });

  it("counts metric identities rather than total acceptance criteria", () => {
    const value = protocol(17);
    value.acceptanceCriteria[16] = { ...value.acceptanceCriteria[16], metricKey: "METRIC_0" };
    expect(validationProtocolContentSchema.safeParse(value).success).toBe(true);
  });

  it("enforces capability metric and baseline profiles at their exact boundaries", () => {
    expect(capabilityScopeSchema.safeParse(scope(8, 4)).success).toBe(true);
    expect(capabilityScopeSchema.safeParse(scope(16, 8)).success).toBe(true);
    expect(capabilityScopeSchema.safeParse(scope(17, 8)).success).toBe(false);
    expect(capabilityScopeSchema.safeParse(scope(16, 9)).success).toBe(false);
  });

  it("keeps human RBAC and denies AI role elevation for all protected operations", () => {
    expect(() => assertEvidenceCustodyAccess(actor("admin"), projectId, "OPEN_HOLDOUT")).not.toThrow();
    expect(() => assertPredictiveEvidenceAccess(actor("admin"), projectId, "ASSEMBLE_PREDICTIVE_EVIDENCE")).not.toThrow();
    for (const role of ["admin", "operator"] as const) {
      expect(() => assertEvidenceCustodyAccess(actor(role, true), projectId, "OPEN_HOLDOUT")).toThrow("AI_AUTHORITY_FORBIDDEN");
      expect(() => assertPredictiveEvidenceAccess(actor(role, true), projectId, "ASSEMBLE_PREDICTIVE_EVIDENCE")).toThrow("AI_AUTHORITY_FORBIDDEN");
      for (const permission of ["REVIEW_CAPABILITY_ASSESSMENT", "AUTHORIZE_PREDICTIVE_CLAIM", "REVOKE_PREDICTIVE_CLAIM"] as const)
        expect(() => assertCapabilityGovernanceAccess(actor(role, true), projectId, permission)).toThrow("AI_AUTHORITY_FORBIDDEN");
    }
    for (const operation of [
      () => assertEvidenceCustodyAccess(actor("viewer"), projectId, "OPEN_HOLDOUT"),
      () => assertPredictiveEvidenceAccess(actor("viewer"), projectId, "ASSEMBLE_PREDICTIVE_EVIDENCE"),
      () => assertCapabilityGovernanceAccess(actor("viewer"), projectId, "AUTHORIZE_PREDICTIVE_CLAIM"),
    ]) expect(operation).toThrow();
  });

  it("denies at the service boundary before parsing or repository mutation", () => {
    const custodyRepository = { openHoldout: vi.fn() }, evidenceRepository = { materializeEvidenceSet: vi.fn() };
    const custody = new GdssEvidenceCustodyService(custodyRepository as never);
    const evidence = new GdssPredictiveEvidenceService(evidenceRepository as never);
    expect(() => custody.openHoldoutForEvaluation(actor("admin", true), projectId, uuid, {})).toThrow("AI_AUTHORITY_FORBIDDEN");
    expect(() => evidence.materializePredictiveEvidenceSet(actor("admin", true), projectId, {})).toThrow("AI_AUTHORITY_FORBIDDEN");
    expect(custodyRepository.openHoldout).not.toHaveBeenCalled();
    expect(evidenceRepository.materializeEvidenceSet).not.toHaveBeenCalled();
  });
});
