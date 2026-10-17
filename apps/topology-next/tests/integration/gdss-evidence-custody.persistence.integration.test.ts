import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createHash, randomUUID } from "node:crypto";
import type { PoolClient } from "pg";
import { pool } from "@/lib/db/pool";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { canonicalContent, contentHash } from "@/lib/gdss/core";
import { mapDatabaseError } from "@/lib/errors/db-error-mapper";
import {
  datasetSnapshotHash,
  partitionPlanHash,
  type EvidenceUnitContent,
  type PartitionPlanContent,
} from "@/lib/gdss/validation";
import { GdssValidationFoundationRepository } from "@/lib/repositories/gdss-validation-foundation.repository";
import { GdssValidationFoundationService } from "@/lib/services/gdss-validation-foundation.service";
import { GdssEvidenceCustodyRepository } from "@/lib/repositories/gdss-evidence-custody.repository";
import { GdssEvidenceCustodyService } from "@/lib/services/gdss-evidence-custody.service";
import { GdssValidationRunRepository } from "@/lib/repositories/gdss-validation-run.repository";
import { GdssValidationRunService } from "@/lib/services/gdss-validation-run.service";
import { GdssMetricsUncertaintyRepository } from "@/lib/repositories/gdss-metrics-uncertainty.repository";
import { GdssMetricsUncertaintyService } from "@/lib/services/gdss-metrics-uncertainty.service";
import { GdssPredictiveEvidenceRepository } from "@/lib/repositories/gdss-predictive-evidence.repository";
import { GdssPredictiveEvidenceService } from "@/lib/services/gdss-predictive-evidence.service";
import { GdssCapabilityClaimsRepository } from "@/lib/repositories/gdss-capability-claims.repository";
import { GdssCapabilityClaimsService } from "@/lib/services/gdss-capability-claims.service";
const h = (c: string) => c.repeat(64),
  sha = (value: unknown) =>
    createHash("sha256").update(JSON.stringify(value)).digest("hex"),
  projectId = randomUUID(),
  modelIdentityId = randomUUID(),
  modelVersionId = randomUUID();
const actor = (name: string, role: "operator" | "admin"): ControlActor => ({
  user_id: `${name}@example.test`,
  actor_id: `${name}@example.test`,
  display_name: name,
  auth_source: "oauth_session",
  role,
  project_ids: [projectId],
  project_roles: { [projectId]: role },
  all_projects: false,
});
const author = actor("partition-author", "operator"),
  approver = actor("custodian-approver", "admin"),
  opener = actor("holdout-opener", "admin");
const provenance = [
    {
      kind: "EMPIRICAL" as const,
      description: "P019 model",
      asserted_by: "p019",
      metadata: {},
    },
  ],
  modelContent = {
    description: "P019 model",
    validity_domain: {},
    provenance,
    units: [
      {
        key: "meter",
        revision: 1,
        symbol: "m",
        name: "meter",
        dimension: [1, 0, 0, 0, 0, 0, 0] as [
          number,
          number,
          number,
          number,
          number,
          number,
          number,
        ],
        scale: 1,
        offset: 0,
        canonical_unit: "meter",
      },
    ],
    children: [
      {
        kind: "Variable" as const,
        symbol: "V",
        label: "level",
        description: "level",
        provenance,
        unit_ref: "meter",
        dimension: [1, 0, 0, 0, 0, 0, 0] as [
          number,
          number,
          number,
          number,
          number,
          number,
          number,
        ],
        computational_role: "STATE" as const,
        epistemic_kind: "SIMULATED" as const,
      },
    ],
  },
  modelHash = contentHash(modelContent);
const domainContent = {
  semanticVersion: "GDSS_VALIDITY_DOMAIN_V1" as const,
  description: "P019 domain",
  predicates: [
    {
      predicateKey: "level",
      variableKey: "V",
      predicateType: "NUMERIC_RANGE" as const,
      unit: { key: "meter", revision: 1 },
      lowerBound: 0,
      upperBound: 10,
      lowerInclusive: true,
      upperInclusive: true,
      rationale: "bounded",
    },
  ],
  boundaries: [
    {
      boundaryKey: "hard",
      kind: "HARD" as const,
      predicateKeys: ["level"],
      description: "hard",
    },
  ],
};
const protocolContent = (domainVersionId: string, domainHash: string) => ({
  semanticVersion: "GDSS_VALIDATION_PROTOCOL_V1" as const,
  modelIdentityId,
  modelVersionId,
  modelVersionNumber: 1,
  modelContentHash: modelHash,
  validityDomainVersionId: domainVersionId,
  validityDomainHash: domainHash,
  targets: [
    {
      targetKey: "level",
      variableReference: "V",
      unitReference: { key: "meter", revision: 1 },
      aggregation: "NONE" as const,
      transformation: "IDENTITY" as const,
      semanticRole: "OBSERVED_TARGET" as const,
    },
  ],
  horizons: [
    {
      horizonKey: "five_min",
      duration: 5,
      unit: { key: "minute", revision: 1 },
      forecastOriginSemantics: "EXPLICIT_ORIGIN" as const,
    },
  ],
  acceptanceCriteria: [
    {
      criterionKey: "rmse",
      metricKey: "RMSE",
      metricVersion: "RMSE_V1",
      operator: "LTE" as const,
      threshold: 0.2,
      unit: { key: "meter", revision: 1 },
      scope: "TARGET_HORIZON" as const,
      scopeReference: "level:five_min",
      required: true,
    },
  ],
  exclusionPolicy: {
    version: "GDSS_VALIDATION_EXCLUSION_V1" as const,
    rules: [],
  },
  missingnessPolicy: {
    version: "GDSS_VALIDATION_MISSINGNESS_V1" as const,
    mode: "REJECT" as const,
  },
  outlierPolicy: {
    version: "GDSS_VALIDATION_OUTLIER_V1" as const,
    mode: "INCLUDE" as const,
  },
  multiplicityPolicy: {
    version: "GDSS_VALIDATION_MULTIPLICITY_V1" as const,
    mode: "NONE" as const,
  },
  revalidationTriggers: ["MODEL_STRUCTURE_CHANGED" as const],
});
const evidence = (
  source: string,
  hash: string,
  group?: string,
): EvidenceUnitContent => ({
  semanticVersion: "GDSS_EVIDENCE_UNIT_V1",
  sourceType: "DATASET_ROW",
  sourceIdentity: source,
  sourceVersion: "v1",
  sourceHash: h("a"),
  granularity: "SINGLE_OBSERVATION",
  semanticGroup: group,
  availabilityTime: "2026-01-01T00:00:00.000Z",
  contentHash: hash,
});
describe
  .runIf(process.env.GDSS_DB_TEST === "1")
  .sequential("GDSS-006B PostgreSQL persistence and custody", () => {
    const durable = process.env.GDSS_DB_CONCURRENCY_TEST === "1";
    let client: PoolClient,
      service: GdssEvidenceCustodyService,
      calibrationId: string,
      holdoutUnitId: string,
      snapshotId: string,
      snapshotHash: string,
      planId: string,
      planHash: string,
      protocolVersionId: string,
      protocolHash: string,
      holdoutId: string;
    const reject = async (fn: () => Promise<unknown>) => {
      const name = `s_${randomUUID().replaceAll("-", "")}`;
      if (durable) await client.query("BEGIN");
      else await client.query(`SAVEPOINT ${name}`);
      let caught: unknown;
      try {
        await fn();
      } catch (error) {
        caught = error;
      }
      if (durable) await client.query("ROLLBACK");
      else await client.query(`ROLLBACK TO SAVEPOINT ${name}`);
      if (!caught) throw Error("expected rejection");
      expect(caught).toBeTruthy();
      return caught;
    };
    beforeAll(async () => {
      client = await pool.connect();
      await client.query("BEGIN");
      await client.query("INSERT INTO projects(id,name)VALUES($1,$2)", [
        projectId,
        `gdss006b-${projectId}`,
      ]);
      await client.query(
        "INSERT INTO gdss_identity(id,project_id,canonical_name,description,created_by)VALUES($1,$2,$3,'p019','p019')",
        [modelIdentityId, projectId, `p019_${modelIdentityId}`],
      );
      await client.query(
        "INSERT INTO gdss_version(id,identity_id,version_number,content,created_by)VALUES($1,$2,1,$3::jsonb,'p019')",
        [modelVersionId, modelIdentityId, JSON.stringify(modelContent)],
      );
      for (const [from, to] of [
        ["DRAFT", "VALIDATED"],
        ["VALIDATED", "EXPERIMENTAL"],
        ["EXPERIMENTAL", "APPROVED"],
        ["APPROVED", "PUBLISHED"],
      ]) {
        await client.query(
          "UPDATE gdss_version SET lifecycle_status=$2,canonical_content=COALESCE(canonical_content,$3),content_hash=COALESCE(content_hash,$4)WHERE id=$1",
          [modelVersionId, to, canonicalContent(modelContent), modelHash],
        );
        await client.query(
          "INSERT INTO gdss_lifecycle_event(model_version_id,from_status,to_status,actor,reason)VALUES($1,$2,$3,'p019','fixture')",
          [modelVersionId, from, to],
        );
      }
      const foundation = new GdssValidationFoundationService(
          new GdssValidationFoundationRepository(async (fn) => fn(client)),
        ),
        domainIdentity = await foundation.createDomainIdentity(
          author,
          projectId,
          "p019_domain",
        ),
        domain = await foundation.createDomainDraft(
          author,
          projectId,
          domainIdentity.id,
          domainContent,
        );
      await foundation.transitionDomain(
        approver,
        projectId,
        domain.id,
        "APPROVED",
        "approve",
        "domain-approve",
      );
      const sealedDomain = await foundation.transitionDomain(
          approver,
          projectId,
          domain.id,
          "SEALED",
          "seal",
          "domain-seal",
        ),
        protocolIdentity = await foundation.createProtocolIdentity(
          author,
          projectId,
          "p019_protocol",
        ),
        protocol = await foundation.createProtocolDraft(
          author,
          projectId,
          protocolIdentity.id,
          protocolContent(domain.id, sealedDomain.content_hash),
        );
      protocolVersionId = protocol.id;
      await foundation.transitionProtocol(
        author,
        projectId,
        protocol.id,
        "REVIEW_REQUIRED",
        "submit",
        "protocol-submit",
      );
      await foundation.transitionProtocol(
        approver,
        projectId,
        protocol.id,
        "APPROVED",
        "approve",
        "protocol-approve",
      );
      const sealedProtocol = await foundation.transitionProtocol(
        approver,
        projectId,
        protocol.id,
        "SEALED",
        "seal",
        "protocol-seal",
      );
      protocolHash = sealedProtocol.content_hash;
      service = new GdssEvidenceCustodyService(
        new GdssEvidenceCustodyRepository(async (fn) => fn(client)),
      );
      const calibration = await service.createEvidenceUnit(
          author,
          projectId,
          evidence("row-cal", h("b"), "group-cal"),
        ),
        holdout = await service.createEvidenceUnit(
          author,
          projectId,
          evidence("row-hold", h("c"), "group-hold"),
        );
      calibrationId = calibration.id;
      holdoutUnitId = holdout.id;
      const snapshotContent = {
        semanticVersion: "GDSS_DATASET_SNAPSHOT_V1" as const,
        sourceDatasetIdentity: "dataset-p019",
        sourceVersion: "v1",
        sourceHash: h("d"),
        includedEvidenceUnitIds: [holdout.id, calibration.id],
        exclusions: [],
      };
      snapshotHash = datasetSnapshotHash(snapshotContent);
      const snapshot = await service.createDatasetSnapshot(
        author,
        projectId,
        snapshotContent,
      );
      snapshotId = snapshot.id;
      const planContent: PartitionPlanContent = {
        semanticVersion: "GDSS_PARTITION_PLAN_V1",
        snapshotId,
        snapshotHash,
        ruleVersion: "explicit-v1",
        ruleKind: "EXPLICIT_ASSIGNMENT",
        dependentGroups: true,
        duplicateStrategies: [
          "EXACT_CONTENT_HASH",
          "SOURCE_IDENTITY_DUPLICATE",
          "SEMANTIC_DUPLICATE_DECLARED",
        ],
        exclusions: [],
        seed: null,
        justification: "independent reserved row",
        lineageReferences: [],
        assignments: [
          {
            evidenceUnitId: calibration.id,
            role: "CALIBRATION",
            groupKey: "group-cal",
            reason: "fit",
          },
          {
            evidenceUnitId: holdout.id,
            role: "HOLDOUT",
            groupKey: "group-hold",
            reason: "reserve",
          },
        ],
      };
      planHash = partitionPlanHash(planContent);
      const identity = await service.createPartitionPlanIdentity(
          author,
          projectId,
          "p019_partition",
        ),
        plan = await service.createPartitionPlanDraft(
          author,
          projectId,
          identity.id,
          planContent,
        );
      planId = plan.id;
      await service.transitionPartitionPlan(
        author,
        projectId,
        plan.id,
        "REVIEW_REQUIRED",
        "submit",
        "plan-submit",
      );
      await service.transitionPartitionPlan(
        approver,
        projectId,
        plan.id,
        "APPROVED",
        "approve",
        "plan-approve",
      );
      await service.transitionPartitionPlan(
        approver,
        projectId,
        plan.id,
        "PUBLISHED",
        "publish",
        "plan-publish",
      );
      const governed = await service.sealHoldout(approver, projectId, {
        semanticVersion: "GDSS_GOVERNED_HOLDOUT_V1",
        partitionPlanVersionId: planId,
        partitionPlanHash: planHash,
        snapshotId,
        snapshotHash,
        protocolVersionId,
        protocolHash,
        modelVersionId,
        modelHash,
        policy: "SINGLE_USE",
      });
      holdoutId = governed.id;
      if (durable) await client.query("COMMIT");
    });
    afterAll(async () => {
      if (!durable) await client.query("ROLLBACK");
      client.release();
    });
    it("enforces 16 protocol metrics and rejects a 17th through direct SQL", async () => {
      const domain = (
          await client.query(
            "SELECT id,content_hash FROM gdss_validity_domain_version WHERE status='SEALED' AND domain_identity_id IN (SELECT id FROM gdss_validity_domain_identity WHERE project_id=$1) LIMIT 1",
            [projectId],
          )
        ).rows[0],
        foundation = new GdssValidationFoundationService(
          new GdssValidationFoundationRepository(async (fn) => fn(client)),
        ),
        identity = await foundation.createProtocolIdentity(
          author,
          projectId,
          `resource-boundary-${randomUUID()}`,
        ),
        content = protocolContent(domain.id, domain.content_hash);
      content.acceptanceCriteria = Array.from({ length: 16 }, (_, index) => ({
        ...content.acceptanceCriteria[0],
        criterionKey: `metric-limit-${index}`,
        metricKey: `METRIC_${index}`,
      }));
      const draft = await foundation.createProtocolDraft(
        author,
        projectId,
        identity.id,
        content,
      );
      expect(
        (
          await client.query(
            "SELECT count(DISTINCT (metric_key,metric_version))::int n FROM gdss_validation_acceptance_criterion WHERE protocol_version_id=$1",
            [draft.id],
          )
        ).rows[0].n,
      ).toBe(16);
      const error = await reject(() =>
        client.query(
          "INSERT INTO gdss_validation_acceptance_criterion(protocol_version_id,ordinal,criterion_key,metric_key,metric_version,operator,threshold,unit_identity,scope,scope_reference,required)VALUES($1,16,'metric-limit-16','METRIC_16','RMSE_V1','LTE',1,NULL,'GLOBAL',NULL,true)",
          [draft.id],
        ),
      );
      expect(String(error)).toContain(
        "RESOURCE_LIMIT_EXCEEDED resource=METRIC_DEFINITIONS_PER_PROTOCOL limit=16 actual=17",
      );
      await foundation.transitionProtocol(author, projectId, draft.id, "REVIEW_REQUIRED", "submit", "resource-submit");
      await foundation.transitionProtocol(approver, projectId, draft.id, "APPROVED", "approve", "resource-approve");
      await expect(
        foundation.transitionProtocol(approver, projectId, draft.id, "SEALED", "seal", "resource-seal"),
      ).resolves.toMatchObject({ status: "SEALED" });
    });
    it("persists exact units snapshot partition protocol and model bindings", async () => {
      const row = (
        await client.query(
          "SELECT state,partition_plan_hash,snapshot_hash,protocol_hash,model_hash FROM gdss_governed_holdout WHERE id=$1",
          [holdoutId],
        )
      ).rows[0];
      expect(row).toMatchObject({
        state: "SEALED",
        partition_plan_hash: planHash,
        snapshot_hash: snapshotHash,
        protocol_hash: protocolHash,
        model_hash: modelHash,
      });
    });
    it("writes the required audit trail", async () => {
      expect(
        (
          await client.query(
            "SELECT count(*)::int n FROM iot_schema.auditoria WHERE contexto->>'subsystem'='gdss006b'",
            [],
          )
        ).rows[0].n,
      ).toBeGreaterThanOrEqual(8);
    });
    it("rejects cross-project assignment at the database boundary", async () => {
      const other = randomUUID(),
        unit = randomUUID();
      await client.query(
        "INSERT INTO projects(id,name)VALUES($1,'other-p019')",
        [other],
      );
      await client.query(
        "INSERT INTO gdss_evidence_unit(id,project_id,semantic_version,source_type,source_identity,source_version,source_hash,granularity,evidence_content,content_hash,identity_hash,created_by)VALUES($1,$2,'GDSS_EVIDENCE_UNIT_V1','DATASET_ROW','other','v1',$3,'SINGLE_OBSERVATION','{}',$4,$5,'p019')",
        [unit, other, h("a"), h("b"), h("e")],
      );
      await reject(() =>
        client.query(
          "INSERT INTO gdss_partition_assignment(partition_plan_version_id,evidence_unit_id,role,reason)VALUES($1,$2,'HOLDOUT','attack')",
          [planId, unit],
        ),
      );
    });
    it("rejects snapshot and published-plan mutation", async () => {
      await reject(() =>
        client.query(
          "UPDATE gdss_evidence_unit SET source_version='v2' WHERE id=$1",
          [calibrationId],
        ),
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_dataset_snapshot SET source_hash=$2 WHERE id=$1",
          [snapshotId, h("f")],
        ),
      );
      await reject(() =>
        client.query(
          "DELETE FROM gdss_dataset_snapshot_member WHERE snapshot_id=$1 AND evidence_unit_id=$2",
          [snapshotId, holdoutUnitId],
        ),
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_partition_plan_version SET plan_content='{}' WHERE id=$1",
          [planId],
        ),
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_partition_assignment SET role='VALIDATION' WHERE partition_plan_version_id=$1 AND evidence_unit_id=$2",
          [planId, holdoutUnitId],
        ),
      );
    });
    it("rejects derivation cycles in PostgreSQL", async () => {
      const a = await service.createEvidenceUnit(
          author,
          projectId,
          evidence("cycle-a", h("d")),
        ),
        b = await service.createEvidenceUnit(
          author,
          projectId,
          evidence("cycle-b", h("e")),
        );
      await service.linkEvidenceLineage(author, projectId, {
        parentEvidenceUnitId: a.id,
        childEvidenceUnitId: b.id,
        relationType: "DERIVED_FROM",
        transformationReference: "f:v1",
      });
      await reject(() =>
        service.linkEvidenceLineage(author, projectId, {
          parentEvidenceUnitId: b.id,
          childEvidenceUnitId: a.id,
          relationType: "DERIVED_FROM",
          transformationReference: "g:v1",
        }),
      );
    });
    it("enforces lineage depth 8/16/17 at the PostgreSQL boundary", async () => {
      const createChain = async (depth: number, label: string) => {
        const ids = Array.from({ length: depth + 1 }, () => randomUUID());
        for (const [index, id] of ids.entries()) {
          const identityHash = sha({
            kind: "gdss006b-depth-boundary",
            label,
            index,
          });
          await client.query(
            "INSERT INTO gdss_evidence_unit(id,project_id,semantic_version,source_type,source_identity,source_version,source_hash,granularity,evidence_content,content_hash,identity_hash,created_by)VALUES($1,$2,'GDSS_EVIDENCE_UNIT_V1','DERIVED_FEATURE',$3,'v1',$4,'DERIVED_FEATURE',$5::jsonb,$6,$7,'p024-r2')",
            [
              id,
              projectId,
              `${label}-${index}`,
              h("a"),
              JSON.stringify({ label, index }),
              sha({ label, index, content: true }),
              identityHash,
            ],
          );
        }
        return ids;
      };
      for (const depth of [8, 16]) {
        const ids = await createChain(depth, `depth-${depth}-${randomUUID()}`);
        for (let index = 1; index < ids.length; index++)
          await client.query(
            "INSERT INTO gdss_evidence_lineage(project_id,parent_evidence_unit_id,child_evidence_unit_id,relation_type,transformation_reference,created_by)VALUES($1,$2,$3,'DERIVED_FROM',$4,'p024-r2')",
            [projectId, ids[index - 1], ids[index], `edge:${index}`],
          );
        expect(
          (
            await client.query(
              "SELECT count(*)::int n FROM gdss_evidence_lineage WHERE parent_evidence_unit_id=ANY($1::uuid[]) AND child_evidence_unit_id=ANY($1::uuid[])",
              [ids],
            )
          ).rows[0].n,
        ).toBe(depth);
      }
      const ids = await createChain(17, `depth-17-${randomUUID()}`);
      for (let index = 1; index <= 16; index++)
        await client.query(
          "INSERT INTO gdss_evidence_lineage(project_id,parent_evidence_unit_id,child_evidence_unit_id,relation_type,transformation_reference,created_by)VALUES($1,$2,$3,'DERIVED_FROM',$4,'p024-r2')",
          [projectId, ids[index - 1], ids[index], `edge:${index}`],
        );
      const error = await reject(() =>
        client.query(
          "INSERT INTO gdss_evidence_lineage(project_id,parent_evidence_unit_id,child_evidence_unit_id,relation_type,transformation_reference,created_by)VALUES($1,$2,$3,'DERIVED_FROM','edge:17','p024-r2')",
          [projectId, ids[16], ids[17]],
        ),
      );
      expect(mapDatabaseError(error)).toMatchObject({
        code: "LINEAGE_DEPTH_LIMIT_EXCEEDED",
        status: 409,
      });
    });
    it.runIf(durable)(
      "serializes concurrent lineage extensions that would jointly reach depth 17",
      async () => {
        const ids = Array.from({ length: 16 }, () => randomUUID()),
          before = randomUUID(),
          after = randomUUID(),
          all = [before, ...ids, after];
        for (const [index, id] of all.entries()) {
          const identityHash = sha({
            kind: "gdss006b-concurrent-depth",
            projectId,
            index,
          });
          await client.query(
            "INSERT INTO gdss_evidence_unit(id,project_id,semantic_version,source_type,source_identity,source_version,source_hash,granularity,evidence_content,content_hash,identity_hash,created_by)VALUES($1,$2,'GDSS_EVIDENCE_UNIT_V1','DERIVED_FEATURE',$3,'v1',$4,'DERIVED_FEATURE',$5::jsonb,$6,$7,'p024-r2')",
            [
              id,
              projectId,
              `concurrent-depth-${index}`,
              h("b"),
              JSON.stringify({ index }),
              sha({ concurrent: true, index }),
              identityHash,
            ],
          );
        }
        for (let index = 1; index < ids.length; index++)
          await client.query(
            "INSERT INTO gdss_evidence_lineage(project_id,parent_evidence_unit_id,child_evidence_unit_id,relation_type,transformation_reference,created_by)VALUES($1,$2,$3,'DERIVED_FROM',$4,'p024-r2')",
            [projectId, ids[index - 1], ids[index], `base:${index}`],
          );
        const attempts = await Promise.allSettled([
          new GdssEvidenceCustodyService().linkEvidenceLineage(
            author,
            projectId,
            {
              parentEvidenceUnitId: before,
              childEvidenceUnitId: ids[0],
              relationType: "DERIVED_FROM",
              transformationReference: "extend-before",
            },
          ),
          new GdssEvidenceCustodyService().linkEvidenceLineage(
            author,
            projectId,
            {
              parentEvidenceUnitId: ids.at(-1)!,
              childEvidenceUnitId: after,
              relationType: "DERIVED_FROM",
              transformationReference: "extend-after",
            },
          ),
        ]);
        expect(
          attempts.filter((attempt) => attempt.status === "fulfilled"),
        ).toHaveLength(1);
        expect(
          attempts.filter((attempt) => attempt.status === "rejected"),
        ).toHaveLength(1);
      },
    );
    it("opens exactly once and binds a future evaluation reference", async () => {
      const start = performance.now();
      if (durable) {
        const concurrent = new GdssEvidenceCustodyService(),
          results = await Promise.allSettled([
            concurrent.openHoldoutForEvaluation(opener, projectId, holdoutId, {
              evaluationReference: "future-evaluation-1",
              reason: "authorized concurrent opening",
              idempotencyKey: "open-1",
            }),
            concurrent.openHoldoutForEvaluation(opener, projectId, holdoutId, {
              evaluationReference: "future-evaluation-2",
              reason: "competing concurrent opening",
              idempotencyKey: "open-2",
            }),
          ]);
        expect(results.filter((r) => r.status === "fulfilled")).toHaveLength(1);
        expect(results.filter((r) => r.status === "rejected")).toHaveLength(1);
        expect(
          (
            await client.query(
              "SELECT count(*)::int n FROM gdss_holdout_lifecycle_event WHERE holdout_id=$1 AND to_state='OPENED_FOR_EVALUATION'",
              [holdoutId],
            )
          ).rows[0].n,
        ).toBe(1);
      } else {
        const opened = await service.openHoldoutForEvaluation(
          opener,
          projectId,
          holdoutId,
          {
            evaluationReference: "future-evaluation-1",
            reason: "authorized one-time opening",
            idempotencyKey: "open-1",
          },
        );
        expect(opened.state).toBe("OPENED_FOR_EVALUATION");
        await expect(
          service.openHoldoutForEvaluation(opener, projectId, holdoutId, {
            evaluationReference: "future-evaluation-2",
            reason: "second opening",
            idempotencyKey: "open-2",
          }),
        ).rejects.toThrow("HOLDOUT_ALREADY_OPEN");
      }
      console.log(
        "GDSS006B_HOLDOUT_OPEN_MS",
        Number((performance.now() - start).toFixed(3)),
      );
    });
    it("records append-only access and exposure ledger rows", async () => {
      await service.recordHoldoutAccess(opener, projectId, holdoutId, {
        accessType: "METADATA_ONLY",
        scope: "manifest",
        reason: "inspect structure",
        authorizationReference: "open-1",
        result: "COMPLETED",
        resourceHash: h("f"),
        independenceImpact: "NO_EPISTEMIC_IMPACT",
        idempotencyKey: "access-1",
      });
      const event = (
        await client.query(
          "SELECT id FROM gdss_holdout_access_event WHERE holdout_id=$1",
          [holdoutId],
        )
      ).rows[0];
      expect(
        (
          await client.query(
            "SELECT count(*)::int n FROM gdss_holdout_exposure_ledger WHERE holdout_id=$1",
            [holdoutId],
          )
        ).rows[0].n,
      ).toBe(1);
      await reject(() =>
        client.query(
          "UPDATE gdss_holdout_access_event SET reason='rewrite' WHERE id=$1",
          [event.id],
        ),
      );
      await reject(() =>
        client.query(
          "DELETE FROM gdss_holdout_exposure_ledger WHERE holdout_id=$1",
          [holdoutId],
        ),
      );
    });
    it("persists governed runs, DB commitments, temporal violations and immutable pair sets", async () => {
      const runService = new GdssValidationRunService(
          new GdssValidationRunRepository(async (fn) => fn(client)),
        ),
        protocol = (
          await client.query(
            "SELECT validity_domain_version_id,validity_domain_hash FROM gdss_validation_protocol_version WHERE id=$1",
            [protocolVersionId],
          )
        ).rows[0],
        runContent = {
          semanticVersion: "GDSS_VALIDATION_RUN_V1" as const,
          protocolVersionId,
          protocolHash,
          modelVersionId,
          modelHash,
          partitionPlanVersionId: planId,
          partitionPlanHash: planHash,
          snapshotId,
          snapshotHash,
          validityDomainVersionId: protocol.validity_domain_version_id,
          validityDomainHash: protocol.validity_domain_hash,
          runMode: "PROSPECTIVE" as const,
        },
        run = await runService.createValidationRun(
          opener,
          projectId,
          runContent,
          "run-1",
        );
      await runService.markValidationRunReady(
        opener,
        projectId,
        run.id,
        "eligible",
        "ready-1",
      );
      if (durable) {
        const concurrent = new GdssValidationRunService(),
          starts = await Promise.allSettled([
            concurrent.startValidationRun(
              opener,
              projectId,
              run.id,
              "start",
              "start-1",
            ),
            concurrent.startValidationRun(
              opener,
              projectId,
              run.id,
              "competing start",
              "start-2",
            ),
          ]);
        expect(starts.filter((x) => x.status === "fulfilled")).toHaveLength(1);
        expect(starts.filter((x) => x.status === "rejected")).toHaveLength(1);
      } else
        await runService.startValidationRun(
          opener,
          projectId,
          run.id,
          "start",
          "start-1",
        );
      const prediction = await runService.createPrediction(
          opener,
          projectId,
          run.id,
          {
            semanticVersion: "GDSS_PREDICTION_V1",
            modelVersionId,
            modelHash,
            targetKey: "level",
            forecastOrigin: "2026-01-01T00:00:00.000Z",
            horizonKey: "five_min",
            horizonDuration: 5,
            horizonUnit: { key: "minute", revision: 1 },
            predictedValue: 4.2,
            predictedUnit: { key: "meter", revision: 1 },
            inputSnapshotHash: snapshotHash,
            parameterSnapshotHash: h("7"),
            boundaryConditionHash: h("8"),
            predictionMode: "PROSPECTIVE",
          },
          "prediction-1",
        ),
        commitments = durable
          ? await Promise.all([
              new GdssValidationRunService().commitPrediction(
                opener,
                projectId,
                prediction.id,
                "commit-1",
              ),
              new GdssValidationRunService().commitPrediction(
                opener,
                projectId,
                prediction.id,
                "commit-2",
              ),
            ])
          : [
              await runService.commitPrediction(
                opener,
                projectId,
                prediction.id,
                "commit-1",
              ),
            ],
        commitment = commitments[0];
      expect(commitment.trust_class).toBe("PLATFORM_PROSPECTIVE");
      expect(new Set(commitments.map((x) => x.id)).size).toBe(1);
      expect(
        (
          await runService.commitPrediction(
            opener,
            projectId,
            prediction.id,
            "commit-retry",
          )
        ).id,
      ).toBe(commitment.id);
      await reject(() =>
        client.query(
          "UPDATE gdss_prediction_record SET predicted_value=99 WHERE id=$1",
          [prediction.id],
        ),
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_prediction_commitment SET committed_at=clock_timestamp() WHERE id=$1",
          [commitment.id],
        ),
      );
      await reject(() =>
        client.query("DELETE FROM gdss_prediction_commitment WHERE id=$1", [
          commitment.id,
        ]),
      );
      const future = await runService.createObservationReference(
          opener,
          projectId,
          {
            semanticVersion: "GDSS_OBSERVATION_REFERENCE_V1",
            observationIdentity: "sensor-1:future",
            source: "sensor-1",
            targetKey: "level",
            observedValue: 4.1,
            unit: { key: "meter", revision: 1 },
            measurementTime: "2026-01-01T00:05:00.000Z",
            availabilityTime: "2099-01-01T00:06:00.000Z",
            ingestionTime: null,
            sourceContentHash: h("9"),
            qualityProvenanceReference: null,
          },
          "observation-future",
        ),
        pairContract = {
          semanticVersion: "GDSS_PREDICTION_OBSERVATION_PAIR_V1" as const,
          targetKey: "level",
          horizonKey: "five_min",
          pairingRule: "EXACT_TIMESTAMP" as const,
        },
        pairAttempts = durable
          ? await Promise.allSettled([
              new GdssValidationRunService().pairPredictionWithObservation(
                opener,
                projectId,
                prediction.id,
                future.id,
                pairContract,
                "pair-1",
              ),
              new GdssValidationRunService().pairPredictionWithObservation(
                opener,
                projectId,
                prediction.id,
                future.id,
                pairContract,
                "pair-2",
              ),
            ])
          : [
              await runService.pairPredictionWithObservation(
                opener,
                projectId,
                prediction.id,
                future.id,
                pairContract,
                "pair-1",
              ),
            ],
        pair = durable
          ? (
              pairAttempts.find(
                (x) => x.status === "fulfilled",
              ) as PromiseFulfilledResult<any>
            ).value
          : pairAttempts[0];
      if (durable) {
        expect(
          pairAttempts.filter((x) => x.status === "fulfilled"),
        ).toHaveLength(1);
        expect(
          pairAttempts.filter((x) => x.status === "rejected"),
        ).toHaveLength(1);
      }
      expect(pair.integrity_state).toBe("PASS");
      const set = await runService.materializePredictionPairSet(
        opener,
        projectId,
        {
          semanticVersion: "GDSS_PREDICTION_PAIR_SET_V1",
          targetKey: "level",
          horizonKey: "five_min",
          scope: "validation",
          pairHashes: [pair.pair_hash],
        },
        "pair-set-1",
      );
      const metricService = new GdssMetricsUncertaintyService(
          new GdssMetricsUncertaintyRepository(async (fn) => fn(client)),
        ),
        metricIdentity = await metricService.createMetricDefinitionIdentity(
          opener,
          projectId,
          "MAE_V1",
        ),
        metricVersion = await metricService.createMetricDefinitionVersion(
          opener,
          projectId,
          metricIdentity.id,
          {
            semanticVersion: "GDSS_METRIC_DEFINITION_V1",
            metricKey: "MAE_V1",
            name: "Mean absolute error",
            category: "POINT_ERROR",
            formulaVersion: "MAE_V1_FORMULA_1",
            directionality: "LOWER_IS_BETTER",
            requiredInputs: ["prediction", "observation"],
            unitSemantics: "same pair unit",
            aggregationSemantics: "binary64 mean absolute difference",
            missingnessBehavior: "GOVERNED_PAIR_SET_ONLY",
            validityConstraints: ["PASS pairs only"],
            implementationIdentifier: "midd-gdss006d-v1",
          },
        ),
        metricResult = await metricService.computeMetricResult(
          opener,
          projectId,
          metricVersion.id,
          set.id,
          "metric-result-1",
        );
      expect(metricResult.result_value).toBeCloseTo(0.1, 12);
      await reject(() =>
        client.query(
          "UPDATE gdss_metric_result SET result_value=99 WHERE id=$1",
          [metricResult.id],
        ),
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_metric_definition_version SET definition_content='{}'::jsonb WHERE id=$1",
          [metricVersion.id],
        ),
      );
      const interval = await metricService.createPredictionInterval(
        opener,
        projectId,
        {
          semanticVersion: "GDSS_PREDICTION_INTERVAL_V1",
          predictionId: prediction.id,
          lowerBound: 4,
          upperBound: 4.3,
          coverageLevel: 0.95,
          unit: { key: "meter", revision: 1 },
          method: "SUPPLIED_INTERVAL",
          methodVersion: "V1",
        },
        "interval-1",
      );
      expect(interval.coverage_level).toBe(0.95);
      const coverage = await metricService.assessIntervalCoverage(
        opener,
        projectId,
        set.id,
        "coverage-1",
      );
      expect(coverage.empirical_coverage).toBe(1);
      await reject(() =>
        client.query(
          "UPDATE gdss_prediction_pair_set SET scope='rewritten' WHERE id=$1",
          [set.id],
        ),
      );
      const known = await runService.createObservationReference(
          opener,
          projectId,
          {
            semanticVersion: "GDSS_OBSERVATION_REFERENCE_V1",
            observationIdentity: "sensor-1:known",
            source: "sensor-1",
            targetKey: "level",
            observedValue: 4,
            unit: { key: "meter", revision: 1 },
            measurementTime: "2020-01-01T00:00:00.000Z",
            availabilityTime: "2020-01-01T00:01:00.000Z",
            ingestionTime: "2020-01-01T00:02:00.000Z",
            sourceContentHash: h("6"),
            qualityProvenanceReference: null,
          },
          "observation-known",
        ),
        violation = await runService.pairPredictionWithObservation(
          opener,
          projectId,
          prediction.id,
          known.id,
          {
            semanticVersion: "GDSS_PREDICTION_OBSERVATION_PAIR_V1",
            targetKey: "level",
            horizonKey: "five_min",
            pairingRule: "EXACT_TIMESTAMP",
          },
          "pair-violation",
        );
      expect(violation.integrity_state).toBe("PREDICTION_AFTER_OBSERVATION");
      await reject(() =>
        metricService.createPredictionInterval(
          opener,
          projectId,
          {
            semanticVersion: "GDSS_PREDICTION_INTERVAL_V1",
            predictionId: prediction.id,
            lowerBound: 3.9,
            upperBound: 4.4,
            coverageLevel: 0.9,
            unit: { key: "meter", revision: 1 },
            method: "DECLARED_BOUNDS",
            methodVersion: "V1",
          },
          "interval-after-observation",
        ),
      );
      expect(
        (
          await client.query(
            "SELECT count(*)::int n FROM gdss_prediction_observation_pair WHERE id=$1",
            [violation.id],
          )
        ).rows[0].n,
      ).toBe(1);
      const baselineIdentity = await metricService.createBaselineIdentity(
          opener,
          projectId,
          "naive-level",
          "NAIVE_LAST_VALUE_V1",
        ),
        baselineVersion = await metricService.createBaselineVersion(
          opener,
          projectId,
          baselineIdentity.id,
          {
            semanticVersion: "GDSS_BASELINE_V1",
            baselineKey: "NAIVE_LAST_VALUE_V1",
            name: "last available level",
            algorithmVersion: "V1",
            targetKey: "level",
            horizonKey: "five_min",
            inputPolicy:
              "latest observation with availability and measurement at or before origin",
          },
        ),
        baselinePredictions = await metricService.generateBaselinePredictions(
          opener,
          projectId,
          baselineVersion.id,
          set.id,
        );
      expect(baselinePredictions).toHaveLength(1);
      expect(
        new Date(baselinePredictions[0].latest_input_availability).getTime(),
      ).toBeLessThanOrEqual(
        new Date(baselinePredictions[0].forecast_origin).getTime(),
      );
      const baselineResult = await metricService.computeBaselineMetricResult(
          opener,
          projectId,
          baselineVersion.id,
          metricVersion.id,
          set.id,
          "baseline-result-1",
        ),
        comparison = await metricService.compareModelToBaseline(
          opener,
          projectId,
          metricResult.id,
          baselineResult.id,
          {
            semanticVersion: "GDSS_BASELINE_COMPARISON_RULE_V1",
            tolerance: 0.001,
            unit: { key: "meter", revision: 1 },
            metricKey: "MAE_V1",
            directionality: "LOWER_IS_BETTER",
          },
          "comparison-1",
        );
      expect(comparison.pair_set_id).toBe(set.id);
      const adverseSet = await runService.materializePredictionPairSet(
        opener,
        projectId,
        {
          semanticVersion: "GDSS_PREDICTION_PAIR_SET_V1",
          targetKey: "level",
          horizonKey: "five_min",
          scope: "diagnostic-invalid-temporality",
          pairHashes: [violation.pair_hash],
        },
        "adverse-pair-set",
      );
      await reject(() =>
        metricService.computeMetricResult(
          opener,
          projectId,
          metricVersion.id,
          adverseSet.id,
          "hidden-exclusion-attempt",
        ),
      );
      await reject(() =>
        client.query(
          "INSERT INTO gdss_baseline_comparison_result(project_id,model_metric_result_id,baseline_metric_result_id,pair_set_id,metric_definition_version_id,comparison_state,model_value,baseline_value,difference,tolerance,comparison_rule,content_hash,idempotency_key,created_by)VALUES($1,$2,$3,$4,$5,'INCONCLUSIVE',$6,$7,0,0,'{}',$8,'mismatch','attack')",
          [
            projectId,
            metricResult.id,
            baselineResult.id,
            adverseSet.id,
            metricVersion.id,
            metricResult.result_value,
            baselineResult.result_value,
            h("2"),
          ],
        ),
      );
      await reject(() =>
        client.query(
          "INSERT INTO gdss_baseline_prediction_record(project_id,baseline_version_id,pair_id,forecast_origin,target_key,horizon_key,predicted_value,unit_key,unit_revision,input_reference,latest_input_availability,content_hash,created_by)VALUES($1,$2,$3,$4,'level','five_min',4,'meter',1,'[]',$5,$6,'attack')",
          [
            projectId,
            baselineVersion.id,
            pair.id,
            prediction.forecast_origin,
            "2099-01-01T00:00:00.000Z",
            h("3"),
          ],
        ),
      );
      const unknownUncertainty =
          await metricService.createUncertaintyAssessment(
            opener,
            projectId,
            {
              semanticVersion: "GDSS_UNCERTAINTY_ASSESSMENT_V1",
              sourceType: "MODEL_STRUCTURAL_UNCERTAINTY",
              knowledgeState: "UNKNOWN",
              method: null,
              unit: null,
              assumptions: [],
              dependencies: [],
              coverageTarget: null,
              qualityProvenanceReference: null,
              scope: `run:${run.id}`,
            },
            run.id,
            set.id,
            "uncertainty-unknown",
          ),
        quantifiedUncertainty = await metricService.createUncertaintyAssessment(
          opener,
          projectId,
          {
            semanticVersion: "GDSS_UNCERTAINTY_ASSESSMENT_V1",
            sourceType: "MEASUREMENT_UNCERTAINTY",
            knowledgeState: "KNOWN_QUANTIFIED",
            method: "DECLARED_BOUNDS",
            lowerBound: -0.1,
            upperBound: 0.1,
            unit: { key: "meter", revision: 1 },
            assumptions: ["calibration certificate current"],
            dependencies: [],
            coverageTarget: 0.95,
            qualityProvenanceReference: "certificate:v1",
            scope: `run:${run.id}`,
          },
          run.id,
          set.id,
          "uncertainty-quantified",
        ),
        completeness = await metricService.assessUncertaintyCompleteness(
          opener,
          projectId,
          `run:${run.id}`,
          [unknownUncertainty.id, quantifiedUncertainty.id],
          "uncertainty-completeness",
        );
      expect(completeness.state).toBe("INSUFFICIENT");
      const rmseIdentity = await metricService.createMetricDefinitionIdentity(
          opener,
          projectId,
          "RMSE_V1",
        ),
        rmseVersion = await metricService.createMetricDefinitionVersion(
          opener,
          projectId,
          rmseIdentity.id,
          {
            semanticVersion: "GDSS_METRIC_DEFINITION_V1",
            metricKey: "RMSE_V1",
            name: "Root mean squared error",
            category: "POINT_ERROR",
            formulaVersion: "RMSE_V1_FORMULA_1",
            directionality: "LOWER_IS_BETTER",
            requiredInputs: ["prediction", "observation"],
            unitSemantics: "same pair unit",
            aggregationSemantics:
              "binary64 square root of mean squared difference",
            missingnessBehavior: "GOVERNED_PAIR_SET_ONLY",
            validityConstraints: ["PASS pairs only"],
            implementationIdentifier: "midd-gdss006d-v1",
          },
        );
      await metricService.computeMetricResult(
        opener,
        projectId,
        rmseVersion.id,
        set.id,
        "rmse-result-1",
      );
      const evidenceService = new GdssPredictiveEvidenceService(
          new GdssPredictiveEvidenceRepository(async (fn) => fn(client)),
        ),
        supportAssessment = await evidenceService.assessValidityDomain(
          opener,
          projectId,
          {
            semanticVersion: "GDSS_DOMAIN_ASSESSMENT_V1",
            modelVersionId,
            modelHash,
            validityDomainVersionId: protocol.validity_domain_version_id,
            validityDomainHash: protocol.validity_domain_hash,
            validationRunId: run.id,
            targetKey: "level",
            horizonKey: "five_min",
            contextSnapshot: {
              semanticVersion: "GDSS_DOMAIN_CONTEXT_V1",
              values: [
                {
                  kind: "NUMERIC",
                  variableKey: "V",
                  value: 2,
                  unit: { key: "meter", revision: 1 },
                },
              ],
            },
            idempotencyKey: "domain-support",
          },
        ),
        currentAssessment = await evidenceService.assessValidityDomain(
          opener,
          projectId,
          {
            semanticVersion: "GDSS_DOMAIN_ASSESSMENT_V1",
            modelVersionId,
            modelHash,
            validityDomainVersionId: protocol.validity_domain_version_id,
            validityDomainHash: protocol.validity_domain_hash,
            validationRunId: run.id,
            targetKey: "level",
            horizonKey: "five_min",
            contextSnapshot: {
              semanticVersion: "GDSS_DOMAIN_CONTEXT_V1",
              values: [
                {
                  kind: "NUMERIC",
                  variableKey: "V",
                  value: 4.2,
                  unit: { key: "meter", revision: 1 },
                },
              ],
            },
            idempotencyKey: "domain-current",
          },
        );
      expect(currentAssessment.assessment_result).toBe(
        "WITHIN_VALIDITY_DOMAIN",
      );
      const position = await evidenceService.assessPredictivePosition(
        opener,
        projectId,
        {
          semanticVersion: "GDSS_PREDICTIVE_POSITION_V1",
          domainAssessmentId: currentAssessment.id,
          modelVersionId,
          validityDomainVersionId: protocol.validity_domain_version_id,
          validationRunId: run.id,
          targetKey: "level",
          horizonKey: "five_min",
          contextSnapshot: currentAssessment.context_snapshot,
          supportDimensions: [
            {
              kind: "NUMERIC_RANGE",
              variableKey: "V",
              lowerBound: 2,
              upperBound: 2,
              unit: { key: "meter", revision: 1 },
              evidenceAssessmentIds: [supportAssessment.id],
            },
          ],
          idempotencyKey: "position-current",
        },
      );
      expect(position.position).toBe("EXTRAPOLATION");
      const negative = await evidenceService.registerNegativeEvidence(
          opener,
          projectId,
          {
            modelVersionId,
            protocolVersionId,
            validityDomainVersionId: protocol.validity_domain_version_id,
            targetKey: "level",
            horizonKey: "five_min",
            findingType: "UNCERTAINTY_INSUFFICIENT",
            sourceArtifactType: "UNCERTAINTY_ASSESSMENT",
            sourceArtifactId: unknownUncertainty.id,
            sourceArtifactHash: unknownUncertainty.content_hash,
            description: "Structural uncertainty remains unknown",
            idempotencyKey: "negative-uncertainty",
          },
        ),
        conflictInput = {
          modelVersionId,
          protocolVersionId,
          validityDomainVersionId: protocol.validity_domain_version_id,
          targetKey: "level",
          horizonKey: "five_min",
          conflictType: "UNCERTAINTY_CONFLICT" as const,
          sourceArtifactType: "UNCERTAINTY_ASSESSMENT" as const,
          sourceArtifactId: unknownUncertainty.id,
          sourceArtifactHash: unknownUncertainty.content_hash,
          conflictingArtifactIds: [
            unknownUncertainty.id,
            quantifiedUncertainty.id,
          ],
          description:
            "Quantified measurement uncertainty and unknown structural uncertainty coexist",
          idempotencyKey: "conflict-uncertainty",
        },
        conflictAttempts = durable
          ? await Promise.all([
              new GdssPredictiveEvidenceService().registerEvidenceConflict(
                opener,
                projectId,
                conflictInput,
              ),
              new GdssPredictiveEvidenceService().registerEvidenceConflict(
                opener,
                projectId,
                { ...conflictInput, idempotencyKey: "conflict-uncertainty-2" },
              ),
            ])
          : [
              await evidenceService.registerEvidenceConflict(
                opener,
                projectId,
                conflictInput,
              ),
            ];
      expect(new Set(conflictAttempts.map((value) => value.id)).size).toBe(1);
      await evidenceService.registerEvidenceLimitation(opener, projectId, {
        modelVersionId,
        protocolVersionId,
        validityDomainVersionId: protocol.validity_domain_version_id,
        targetKey: "level",
        horizonKey: "five_min",
        limitationType: "UNCERTAINTY_PARTIAL",
        sourceArtifactType: "UNCERTAINTY_ASSESSMENT",
        sourceArtifactId: unknownUncertainty.id,
        sourceArtifactHash: unknownUncertainty.content_hash,
        description: "Unknown structural uncertainty limits interpretation",
        idempotencyKey: "limitation-uncertainty",
      });
      const setInput = {
          semanticVersion: "GDSS_PREDICTIVE_EVIDENCE_SET_V1" as const,
          modelVersionId,
          modelHash,
          protocolVersionId,
          protocolHash,
          validityDomainVersionId: protocol.validity_domain_version_id,
          validityDomainHash: protocol.validity_domain_hash,
          partitionPlanVersionId: planId,
          partitionPlanHash: planHash,
          snapshotId,
          snapshotHash,
          targetKey: "level",
          horizonKey: "five_min",
          validationRunIds: [run.id],
          pairSetIds: [set.id],
          domainAssessmentIds: [currentAssessment.id],
          positionAssessmentIds: [position.id],
          idempotencyKey: "evidence-set-1",
        },
        evidenceAttempts = durable
          ? await Promise.all([
              new GdssPredictiveEvidenceService().materializePredictiveEvidenceSet(
                opener,
                projectId,
                setInput,
              ),
              new GdssPredictiveEvidenceService().materializePredictiveEvidenceSet(
                opener,
                projectId,
                { ...setInput, idempotencyKey: "evidence-set-2" },
              ),
            ])
          : [
              await evidenceService.materializePredictiveEvidenceSet(
                opener,
                projectId,
                setInput,
              ),
            ],
        evidenceSet = evidenceAttempts[0];
      expect(new Set(evidenceAttempts.map((value) => value.id)).size).toBe(1);
      expect(evidenceSet.reference_count).toBeGreaterThanOrEqual(13);
      expect(
        (
          await client.query(
            "SELECT count(*)::int n FROM gdss_predictive_evidence_reference WHERE evidence_set_id=$1 AND artifact_type='NEGATIVE_FINDING' AND artifact_id=$2",
            [evidenceSet.id, negative.id],
          )
        ).rows[0].n,
      ).toBe(1);
      await reject(() =>
        client.query(
          "INSERT INTO gdss_predictive_evidence_reference(project_id,evidence_set_id,ordinal,artifact_type,artifact_id,artifact_hash,source_phase,role,reference_hash)VALUES($1,$2,$3,'NEGATIVE_FINDING',$4,$5,'GDSS-006E','CONTRADICTING',$6)",
          [
            projectId,
            evidenceSet.id,
            evidenceSet.reference_count,
            negative.id,
            negative.content_hash,
            h("e"),
          ],
        ),
      );
      await reject(() =>
        client.query(
          "DELETE FROM gdss_predictive_evidence_reference WHERE evidence_set_id=$1 AND artifact_id=$2",
          [evidenceSet.id, negative.id],
        ),
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_predictive_evidence_set SET target_key='other' WHERE id=$1",
          [evidenceSet.id],
        ),
      );
      const profileAttempts = durable
        ? await Promise.all([
            new GdssPredictiveEvidenceService().deriveEvidenceStrengthProfile(
              opener,
              projectId,
              evidenceSet.id,
            ),
            new GdssPredictiveEvidenceService().deriveEvidenceStrengthProfile(
              opener,
              projectId,
              evidenceSet.id,
            ),
          ])
        : [
            await evidenceService.deriveEvidenceStrengthProfile(
              opener,
              projectId,
              evidenceSet.id,
            ),
          ];
      expect(new Set(profileAttempts.map((value) => value.id)).size).toBe(1);
      const profile = profileAttempts[0];
      expect(profile.axes).toHaveLength(7);
      expect(
        profile.axes.find(
          (axis: { axis: string }) => axis.axis === "REPLICATION",
        ).state,
      ).toBe("INSUFFICIENT");
      expect(
        profile.axes.find(
          (axis: { axis: string }) => axis.axis === "UNCERTAINTY_COMPLETENESS",
        ).state,
      ).toBe("INSUFFICIENT");
      expect(JSON.stringify(profile.axes)).not.toMatch(/overall|score/i);
      const capabilityRepository = new GdssCapabilityClaimsRepository(
          async (fn) => fn(client),
        ),
        capabilityService = durable
          ? new GdssCapabilityClaimsService()
          : new GdssCapabilityClaimsService(capabilityRepository),
        capabilityFacts = await capabilityRepository.getCapabilityFacts(
          projectId,
          evidenceSet.id,
        ),
        capabilityScope = {
          modelVersionId,
          modelContentHash: modelHash,
          targetKey: "level",
          horizonKey: "five_min",
          validityDomainVersionId: protocol.validity_domain_version_id,
          protocolFamily: capabilityFacts.set.protocol_family,
          metricProfile: capabilityFacts.metricProfile,
          baselineProfile: capabilityFacts.baselineProfile,
          uncertaintyProfile: capabilityFacts.uncertaintyProfile,
          evidencePeriod: {
            startEpochMicros: capabilityFacts.evidencePeriod.start_epoch_micros,
            endEpochMicros: capabilityFacts.evidencePeriod.end_epoch_micros,
          },
          domainConstraints: [
            {
              kind: "NUMERIC_RANGE" as const,
              variableKey: "V",
              lowerBound: 0,
              upperBound: 10,
              lowerInclusive: true,
              upperInclusive: true,
              unit: { key: "meter", revision: 1 },
            },
          ],
        },
        capabilityInput = {
          semanticVersion: "GDSS_CAPABILITY_ASSESSMENT_V1" as const,
          evidenceSetId: evidenceSet.id,
          evidenceSetHash: evidenceSet.content_hash,
          assessmentPolicyVersion: "GDSS_CAPABILITY_POLICY_V1" as const,
          requestedAction: "EVALUATE" as const,
          scope: capabilityScope,
          idempotencyKey: "capability-conflicting-1",
        },
        capabilityAttempts = durable
          ? await Promise.all([
              capabilityService.assessPredictiveCapability(
                opener,
                projectId,
                capabilityInput,
              ),
              new GdssCapabilityClaimsService().assessPredictiveCapability(
                opener,
                projectId,
                {
                  ...capabilityInput,
                  idempotencyKey: "capability-conflicting-2",
                },
              ),
            ])
          : [
              await capabilityService.assessPredictiveCapability(
                opener,
                projectId,
                capabilityInput,
              ),
            ],
        conflicting = capabilityAttempts[0];
      expect(new Set(capabilityAttempts.map((item) => item.id)).size).toBe(1);
      expect(conflicting.state).toBe("CONFLICTING_EVIDENCE");
      expect(conflicting.conflict_manifest).not.toHaveLength(0);
      expect(conflicting.negative_evidence_manifest).not.toHaveLength(0);
      const limitedAssessment = (
        await client.query(
          `INSERT INTO gdss_capability_assessment(project_id,semantic_version,evidence_set_id,evidence_set_hash,model_version_id,model_content_hash,target_key,horizon_key,validity_domain_version_id,protocol_family,metric_profile,baseline_profile,uncertainty_profile,evidence_period_start,evidence_period_end,domain_scope,assessment_policy_version,state,rationale_code,axis_explanation,limitation_manifest,conflict_manifest,negative_evidence_manifest,content_hash,idempotency_key,created_by)
           VALUES($1,'GDSS_CAPABILITY_ASSESSMENT_V1',$2,$3,$4,$5,'level','five_min',$6,$7,$8,$9,$10,$11::bigint,$12::bigint,$13::jsonb,'GDSS_CAPABILITY_POLICY_V1','EVIDENCE_OF_LIMITED_CAPABILITY','TEST_LIMITED_POLICY',$14::jsonb,$15::jsonb,$16::jsonb,$17::jsonb,$18,'capability-limited-fixture','fixture') RETURNING *`,
          [
            projectId,
            evidenceSet.id,
            evidenceSet.content_hash,
            modelVersionId,
            modelHash,
            protocol.validity_domain_version_id,
            capabilityFacts.set.protocol_family,
            capabilityFacts.metricProfile,
            capabilityFacts.baselineProfile,
            capabilityFacts.uncertaintyProfile,
            capabilityFacts.evidencePeriod.start_epoch_micros,
            capabilityFacts.evidencePeriod.end_epoch_micros,
            JSON.stringify(capabilityScope.domainConstraints),
            JSON.stringify(profile.axes),
            JSON.stringify(capabilityFacts.limitations),
            JSON.stringify(capabilityFacts.conflicts),
            JSON.stringify(capabilityFacts.negativeEvidence),
            h("7"),
          ],
        )
      ).rows[0];
      const claimIdentity = await capabilityService.createPredictiveClaimIdentity(
          author,
          projectId,
          {
            canonicalKey: "level-five-min-limited",
            idempotencyKey: "claim-identity-1",
          },
        ),
        claim = await capabilityService.createPredictiveClaimDraft(
          author,
          projectId,
          {
            semanticVersion: "GDSS_PREDICTIVE_CLAIM_V1",
            claimIdentityId: claimIdentity.id,
            capabilityAssessmentId: limitedAssessment.id,
            capabilityAssessmentHash: limitedAssessment.content_hash,
            claimScope: capabilityScope,
            templateVersion: "GDSS_PREDICTIVE_CLAIM_TEMPLATE_V1",
            validThroughEpochMicros: "9999999999999999",
            idempotencyKey: "claim-draft-1",
          },
        );
      expect(claim.rendered_human_text).toContain("EVIDENCE_OF_LIMITED_CAPABILITY");
      await expect(
        capabilityService.createPredictiveClaimDraft(author, projectId, {
          semanticVersion: "GDSS_PREDICTIVE_CLAIM_V1",
          claimIdentityId: claimIdentity.id,
          capabilityAssessmentId: limitedAssessment.id,
          capabilityAssessmentHash: limitedAssessment.content_hash,
          claimScope: {
            ...capabilityScope,
            domainConstraints: [
              { ...capabilityScope.domainConstraints[0], upperBound: 11 },
            ],
          },
          templateVersion: "GDSS_PREDICTIVE_CLAIM_TEMPLATE_V1",
          idempotencyKey: "claim-expanded-forbidden",
        }),
      ).rejects.toThrow("CLAIM_SCOPE_EXCEEDS_CAPABILITY");
      const assembled = await capabilityService.assembleClaimEvidence(
          author,
          projectId,
          claim.id,
          {
            expectedClaimHash: claim.content_hash,
            reason: "evidence complete",
            idempotencyKey: "claim-assemble-1",
          },
        ),
        submitted = await capabilityService.submitClaimForReview(
          author,
          projectId,
          claim.id,
          {
            expectedClaimHash: assembled.content_hash,
            reason: "human review requested",
            idempotencyKey: "claim-submit-1",
          },
        );
      await capabilityService.reviewPredictiveClaim(
        opener,
        projectId,
        claim.id,
        {
          expectedClaimHash: submitted.content_hash,
          decision: "APPROVE_FOR_AUTHORIZATION",
          rationale: "limited scope and adverse evidence are explicit",
          scopeFindings: [],
          evidenceFindings: ["limited capability only"],
          idempotencyKey: "claim-review-1",
        },
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_predictive_claim_version SET rendered_human_text='rewritten' WHERE id=$1",
          [claim.id],
        ),
      );
      const authorizationInput = {
          expectedClaimHash: claim.content_hash,
          expectedAssessmentHash: limitedAssessment.content_hash,
          expectedEvidenceSetHash: evidenceSet.content_hash,
          authorizedScope: capabilityScope,
          decision: "AUTHORIZE" as const,
          idempotencyKey: "claim-authorization-1",
        },
        authorizationAttempts = durable
          ? await Promise.all([
              capabilityService.authorizePredictiveClaim(
                approver,
                projectId,
                claim.id,
                authorizationInput,
              ),
              new GdssCapabilityClaimsService().authorizePredictiveClaim(
                opener,
                projectId,
                claim.id,
                {
                  ...authorizationInput,
                  idempotencyKey: "claim-authorization-2",
                },
              ),
            ])
          : [
              await capabilityService.authorizePredictiveClaim(
                approver,
                projectId,
                claim.id,
                authorizationInput,
              ),
            ],
        authorization = authorizationAttempts[0];
      expect(new Set(authorizationAttempts.map((item) => item.id)).size).toBe(
        1,
      );
      expect(
        (
          await capabilityService.getClaimCurrentness(
            approver,
            projectId,
            claim.id,
            100n,
          )
        ).currentness,
      ).toBe("AUTHORIZED_CURRENT");
      expect(
        (
          await capabilityService.getClaimCurrentness(
            approver,
            projectId,
            claim.id,
            10000000000000000n,
          )
        ).currentness,
      ).toBe("AUTHORIZED_EXPIRED_REVIEW_REQUIRED");
      const trigger = await capabilityService.assessRevalidationTrigger(
        opener,
        projectId,
        {
          capabilityAssessmentId: limitedAssessment.id,
          claimId: claim.id,
          evidenceSetId: evidenceSet.id,
          triggerType: "CONTRADICTORY_EVIDENCE",
          causalArtifactId: conflicting.id,
          causalArtifactHash: conflicting.content_hash,
          rationale: "successor evidence conflicts materially",
          idempotencyKey: "revalidation-trigger-1",
        },
      );
      expect(trigger.state).toBe("REVALIDATION_REQUIRED");
      expect(
        (
          await capabilityService.getClaimCurrentness(
            approver,
            projectId,
            claim.id,
            100n,
          )
        ).currentness,
      ).toBe("HUMAN_REVIEW_REQUIRED");
      await capabilityService.resolveRevalidationTrigger(
        opener,
        projectId,
        trigger.id,
        {
          expectedContentHash: trigger.content_hash,
          resolution: "ACKNOWLEDGED",
          rationale: "full revalidation queued outside this phase",
          idempotencyKey: "revalidation-resolution-1",
        },
      );
      const revocationInput = {
          authorizationId: authorization.id,
          reason: "contradictory evidence requires withdrawal",
          trigger: "CONTRADICTORY_EVIDENCE" as const,
          idempotencyKey: "claim-revocation-1",
        },
        revocationAttempts = durable
          ? await Promise.all([
              capabilityService.revokePredictiveClaim(
                approver,
                projectId,
                claim.id,
                revocationInput,
              ),
              new GdssCapabilityClaimsService().revokePredictiveClaim(
                opener,
                projectId,
                claim.id,
                {
                  ...revocationInput,
                  idempotencyKey: "claim-revocation-2",
                },
              ),
            ])
          : [
              await capabilityService.revokePredictiveClaim(
                approver,
                projectId,
                claim.id,
                revocationInput,
              ),
            ],
        revocation = revocationAttempts[0];
      expect(new Set(revocationAttempts.map((item) => item.id)).size).toBe(1);
      expect(
        (
          await capabilityService.revokePredictiveClaim(
            approver,
            projectId,
            claim.id,
            {
              authorizationId: authorization.id,
              reason: "contradictory evidence requires withdrawal",
              trigger: "CONTRADICTORY_EVIDENCE",
              idempotencyKey: "claim-revocation-1-retry",
            },
          )
        ).id,
      ).toBe(revocation.id);
      const audit = await capabilityService.auditPredictiveClaim(
        approver,
        projectId,
        claim.id,
      );
      expect(audit.authorization.id).toBe(authorization.id);
      expect(audit.revocation.id).toBe(revocation.id);
      expect(audit.events.map((event: any) => event.to_status)).toEqual([
        "DRAFT",
        "EVIDENCE_ASSEMBLED",
        "REVIEW_REQUIRED",
        "AUTHORIZED",
        "REVOKED",
      ]);
      if (durable) {
        const successorAttempts = await Promise.allSettled([
          capabilityService.createPredictiveClaimDraft(author, projectId, {
            semanticVersion: "GDSS_PREDICTIVE_CLAIM_V1",
            claimIdentityId: claimIdentity.id,
            capabilityAssessmentId: limitedAssessment.id,
            capabilityAssessmentHash: limitedAssessment.content_hash,
            claimScope: capabilityScope,
            templateVersion: "GDSS_PREDICTIVE_CLAIM_TEMPLATE_V1",
            predecessorClaimId: claim.id,
            idempotencyKey: "claim-successor-1",
          }),
          new GdssCapabilityClaimsService().createPredictiveClaimDraft(
            author,
            projectId,
            {
              semanticVersion: "GDSS_PREDICTIVE_CLAIM_V1",
              claimIdentityId: claimIdentity.id,
              capabilityAssessmentId: limitedAssessment.id,
              capabilityAssessmentHash: limitedAssessment.content_hash,
              claimScope: capabilityScope,
              templateVersion: "GDSS_PREDICTIVE_CLAIM_TEMPLATE_V1",
              predecessorClaimId: claim.id,
              idempotencyKey: "claim-successor-2",
            },
          ),
        ]);
        expect(
          successorAttempts.filter((item) => item.status === "fulfilled"),
        ).toHaveLength(1);
        expect(
          successorAttempts.filter((item) => item.status === "rejected"),
        ).toHaveLength(1);
      }
      const sodIdentity = await capabilityService.createPredictiveClaimIdentity(
          opener,
          projectId,
          {
            canonicalKey: "level-five-min-sod",
            idempotencyKey: "sod-identity-1",
          },
        ),
        sodDraft = await capabilityService.createPredictiveClaimDraft(
          opener,
          projectId,
          {
            semanticVersion: "GDSS_PREDICTIVE_CLAIM_V1",
            claimIdentityId: sodIdentity.id,
            capabilityAssessmentId: limitedAssessment.id,
            capabilityAssessmentHash: limitedAssessment.content_hash,
            claimScope: capabilityScope,
            templateVersion: "GDSS_PREDICTIVE_CLAIM_TEMPLATE_V1",
            idempotencyKey: "sod-draft-1",
          },
        ),
        sodAssembled = await capabilityService.assembleClaimEvidence(
          opener,
          projectId,
          sodDraft.id,
          {
            expectedClaimHash: sodDraft.content_hash,
            reason: "assemble",
            idempotencyKey: "sod-assemble-1",
          },
        ),
        sodSubmitted = await capabilityService.submitClaimForReview(
          opener,
          projectId,
          sodDraft.id,
          {
            expectedClaimHash: sodAssembled.content_hash,
            reason: "review",
            idempotencyKey: "sod-submit-1",
          },
        );
      await capabilityService.reviewPredictiveClaim(
        approver,
        projectId,
        sodDraft.id,
        {
          expectedClaimHash: sodSubmitted.content_hash,
          decision: "APPROVE_FOR_AUTHORIZATION",
          rationale: "review only",
          scopeFindings: [],
          evidenceFindings: [],
          idempotencyKey: "sod-review-1",
        },
      );
      await expect(
        capabilityService.authorizePredictiveClaim(
          opener,
          projectId,
          sodDraft.id,
          {
            expectedClaimHash: sodDraft.content_hash,
            expectedAssessmentHash: limitedAssessment.content_hash,
            expectedEvidenceSetHash: evidenceSet.content_hash,
            authorizedScope: capabilityScope,
            decision: "AUTHORIZE",
            idempotencyKey: "sod-authorization-forbidden",
          },
        ),
      ).rejects.toThrow("CLAIM_SOD_VIOLATION");
      const targetModelVersionId = randomUUID();
      await client.query(
        "INSERT INTO gdss_version(id,identity_id,version_number,content,created_by)VALUES($1,$2,2,$3::jsonb,'p023')",
        [targetModelVersionId, modelIdentityId, JSON.stringify(modelContent)],
      );
      const transfer = await capabilityService.assessEvidenceTransfer(
        opener,
        projectId,
        {
          sourceModelVersionId: modelVersionId,
          targetModelVersionId,
          sourceEvidenceSetId: evidenceSet.id,
          sourceEvidenceSetHash: evidenceSet.content_hash,
          requestedTransferScope: capabilityScope,
          requestedMode: "DIRECT_TRANSFER",
          reason: "even a minimal version change requires revalidation",
          idempotencyKey: "transfer-assessment-1",
        },
      );
      expect(transfer.result).toBe("FULL_REVALIDATION_REQUIRED");
      expect(() =>
        capabilityService.assessEvidenceTransfer(opener, projectId, {
          sourceModelVersionId: modelVersionId,
          targetModelVersionId,
          sourceEvidenceSetId: evidenceSet.id,
          sourceEvidenceSetHash: evidenceSet.content_hash,
          requestedTransferScope: capabilityScope,
          requestedMode: "PARTIAL_REVALIDATION_ALLOWED",
          reason: "reserved vocabulary must remain non-executable",
          idempotencyKey: "transfer-partial-forbidden",
        }),
      ).toThrow("EVIDENCE_TRANSFER_FORBIDDEN");
      if (durable) {
        const concurrent = new GdssMetricsUncertaintyService(),
          biasIdentity = await metricService.createMetricDefinitionIdentity(
            opener,
            projectId,
            "BIAS_V1",
          ),
          biasVersion = await metricService.createMetricDefinitionVersion(
            opener,
            projectId,
            biasIdentity.id,
            {
              semanticVersion: "GDSS_METRIC_DEFINITION_V1",
              metricKey: "BIAS_V1",
              name: "Signed bias",
              category: "POINT_ERROR",
              formulaVersion: "BIAS_V1_FORMULA_1",
              directionality: "CLOSER_TO_ZERO_IS_BETTER",
              requiredInputs: ["prediction", "observation"],
              unitSemantics: "same pair unit",
              aggregationSemantics: "binary64 signed mean",
              missingnessBehavior: "GOVERNED_PAIR_SET_ONLY",
              validityConstraints: ["PASS pairs only"],
              implementationIdentifier: "midd-gdss006d-v1",
            },
          ),
          metricAttempts = await Promise.allSettled([
            concurrent.computeMetricResult(
              opener,
              projectId,
              biasVersion.id,
              set.id,
              "bias-concurrent-1",
            ),
            concurrent.computeMetricResult(
              opener,
              projectId,
              biasVersion.id,
              set.id,
              "bias-concurrent-2",
            ),
          ]);
        expect(
          metricAttempts.filter((x) => x.status === "fulfilled"),
        ).toHaveLength(1);
        const biasResult = (
            metricAttempts.find(
              (x) => x.status === "fulfilled",
            ) as PromiseFulfilledResult<any>
          ).value,
          historicalIdentity = await metricService.createBaselineIdentity(
            opener,
            projectId,
            "historical-level",
            "HISTORICAL_MEAN_V1",
          ),
          historicalVersion = await metricService.createBaselineVersion(
            opener,
            projectId,
            historicalIdentity.id,
            {
              semanticVersion: "GDSS_BASELINE_V1",
              baselineKey: "HISTORICAL_MEAN_V1",
              name: "historical level",
              algorithmVersion: "V1",
              targetKey: "level",
              horizonKey: "five_min",
              inputPolicy: "available observations in declared period",
              referenceWindowStart: "2019-01-01T00:00:00.000Z",
              referenceWindowEnd: "2025-12-31T23:59:59.000Z",
            },
          ),
          generationAttempts = await Promise.all([
            concurrent.generateBaselinePredictions(
              opener,
              projectId,
              historicalVersion.id,
              set.id,
            ),
            concurrent.generateBaselinePredictions(
              opener,
              projectId,
              historicalVersion.id,
              set.id,
            ),
          ]);
        expect(new Set(generationAttempts.flat().map((x) => x.id)).size).toBe(
          1,
        );
        const historicalResult =
            await metricService.computeBaselineMetricResult(
              opener,
              projectId,
              historicalVersion.id,
              biasVersion.id,
              set.id,
              "historical-bias-result",
            ),
          rule = {
            semanticVersion: "GDSS_BASELINE_COMPARISON_RULE_V1" as const,
            tolerance: 0.001,
            unit: { key: "meter", revision: 1 },
            metricKey: "BIAS_V1" as const,
            directionality: "CLOSER_TO_ZERO_IS_BETTER" as const,
          },
          comparisonAttempts = await Promise.allSettled([
            concurrent.compareModelToBaseline(
              opener,
              projectId,
              biasResult.id,
              historicalResult.id,
              rule,
              "bias-comparison-1",
            ),
            concurrent.compareModelToBaseline(
              opener,
              projectId,
              biasResult.id,
              historicalResult.id,
              rule,
              "bias-comparison-2",
            ),
          ]);
        expect(
          comparisonAttempts.filter((x) => x.status === "fulfilled"),
        ).toHaveLength(1);
        const uncertaintyContent = {
            semanticVersion: "GDSS_UNCERTAINTY_ASSESSMENT_V1" as const,
            sourceType: "INPUT_UNCERTAINTY" as const,
            knowledgeState: "UNKNOWN" as const,
            method: null,
            unit: null,
            assumptions: [],
            dependencies: [],
            coverageTarget: null,
            qualityProvenanceReference: null,
            scope: `concurrent:${run.id}`,
          },
          uncertaintyAttempts = await Promise.allSettled([
            concurrent.createUncertaintyAssessment(
              opener,
              projectId,
              uncertaintyContent,
              run.id,
              set.id,
              "input-uncertainty-1",
            ),
            concurrent.createUncertaintyAssessment(
              opener,
              projectId,
              uncertaintyContent,
              run.id,
              set.id,
              "input-uncertainty-2",
            ),
          ]);
        expect(
          uncertaintyAttempts.filter((x) => x.status === "fulfilled"),
        ).toHaveLength(1);
      }
      const unknown = await runService.createObservationReference(
          opener,
          projectId,
          {
            semanticVersion: "GDSS_OBSERVATION_REFERENCE_V1",
            observationIdentity: "sensor-1:unknown-availability",
            source: "sensor-1",
            targetKey: "level",
            observedValue: 4,
            unit: { key: "meter", revision: 1 },
            measurementTime: "2026-01-01T00:05:00.000Z",
            availabilityTime: null,
            ingestionTime: null,
            sourceContentHash: h("5"),
            qualityProvenanceReference: null,
          },
          "observation-unknown",
        ),
        unknownPair = await runService.pairPredictionWithObservation(
          opener,
          projectId,
          prediction.id,
          unknown.id,
          pairContract,
          "pair-unknown",
        );
      expect(unknownPair.integrity_state).toBe("TEMPORAL_INTEGRITY_UNKNOWN");
      await reject(() =>
        runService.createPrediction(
          opener,
          projectId,
          run.id,
          { ...prediction.prediction_content, modelHash: h("0") },
          "wrong-model",
        ),
      );
      await reject(() =>
        runService.pairPredictionWithObservation(
          opener,
          projectId,
          prediction.id,
          future.id,
          { ...pairContract, targetKey: "humidity" },
          "wrong-target",
        ),
      );
      await reject(() =>
        runService.pairPredictionWithObservation(
          opener,
          projectId,
          prediction.id,
          future.id,
          { ...pairContract, horizonKey: "one_hour" },
          "wrong-horizon",
        ),
      );
      const incompatible = await runService.createObservationReference(
        opener,
        projectId,
        {
          semanticVersion: "GDSS_OBSERVATION_REFERENCE_V1",
          observationIdentity: "sensor-ec",
          source: "sensor-ec",
          targetKey: "level",
          observedValue: 2,
          unit: { key: "siemens_per_meter", revision: 1 },
          measurementTime: "2026-01-01T00:05:00.000Z",
          availabilityTime: "2099-01-01T00:06:00.000Z",
          ingestionTime: null,
          sourceContentHash: h("4"),
          qualityProvenanceReference: null,
        },
        "observation-unit-mismatch",
      );
      await reject(() =>
        runService.pairPredictionWithObservation(
          opener,
          projectId,
          prediction.id,
          incompatible.id,
          pairContract,
          "wrong-unit",
        ),
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_prediction_observation_pair SET pairing_rule='EXACT_EVENT_ID' WHERE id=$1",
          [pair.id],
        ),
      );
      await reject(() =>
        client.query(
          "UPDATE gdss_validation_run SET run_mode='RETROSPECTIVE' WHERE id=$1",
          [run.id],
        ),
      );
      await reject(() =>
        runService.createValidationRun(
          opener,
          projectId,
          { ...runContent, protocolHash: h("0") },
          "wrong-protocol",
        ),
      );
      const overLimitBaselines: Array<{ id: string }> = [];
      for (let index = 3; index <= 10; index++) {
        const extraIdentity = await metricService.createBaselineIdentity(
            opener,
            projectId,
            `resource-baseline-${index}`,
            "NAIVE_LAST_VALUE_V1",
          ),
          extraVersion = await metricService.createBaselineVersion(
            opener,
            projectId,
            extraIdentity.id,
            {
              semanticVersion: "GDSS_BASELINE_V1",
              baselineKey: "NAIVE_LAST_VALUE_V1",
              name: `resource baseline ${index}`,
              algorithmVersion: `V${index}`,
              targetKey: "level",
              horizonKey: "five_min",
              inputPolicy: "latest governed observation available at forecast origin",
            },
          );
        await metricService.generateBaselinePredictions(
          opener,
          projectId,
          extraVersion.id,
          set.id,
        );
        if (index <= 8)
          await metricService.computeBaselineMetricResult(
            opener,
            projectId,
            extraVersion.id,
            metricVersion.id,
            set.id,
            `resource-baseline-result-${index}`,
          );
        else overLimitBaselines.push(extraVersion);
      }
      expect(
        (
          await client.query(
            "SELECT count(DISTINCT baseline_version_id)::int n FROM gdss_baseline_metric_result WHERE pair_set_id=$1",
            [set.id],
          )
        ).rows[0].n,
      ).toBe(8);
      const insertOverLimit = (queryable: Pick<PoolClient, "query">, versionId: string, suffix: string) =>
        queryable.query(
          "INSERT INTO gdss_baseline_metric_result(project_id,baseline_version_id,metric_definition_version_id,pair_set_id,target_key,horizon_key,unit_key,unit_revision,result_value,result_content,content_hash,idempotency_key,computed_by)VALUES($1,$2,$3,$4,'level','five_min','meter',1,0,'{}'::jsonb,$5,$6,'direct-sql')",
          [projectId, versionId, metricVersion.id, set.id, sha(`over-limit-${suffix}`), `over-limit-${suffix}`],
        );
      if (durable) {
        const attempts = await Promise.allSettled([
          insertOverLimit(pool, overLimitBaselines[0].id, "9a"),
          insertOverLimit(pool, overLimitBaselines[1].id, "9b"),
        ]);
        expect(attempts.every((attempt) => attempt.status === "rejected")).toBe(true);
        for (const attempt of attempts)
          if (attempt.status === "rejected")
            expect(String(attempt.reason)).toContain(
              "RESOURCE_LIMIT_EXCEEDED resource=BASELINES_PER_PROTOCOL limit=8 actual=9",
            );
      } else {
        const error = await reject(() =>
          insertOverLimit(client, overLimitBaselines[0].id, "9"),
        );
        expect(String(error)).toContain(
          "RESOURCE_LIMIT_EXCEEDED resource=BASELINES_PER_PROTOCOL limit=8 actual=9",
        );
      }
      await runService.completeValidationRun(
        opener,
        projectId,
        run.id,
        "execution finished; no validation claim",
        "complete-1",
      );
    });
    it("consumes a single-use holdout and permanently forbids reopen or reseal", async () => {
      expect(
        (
          await service.transitionHoldout(
            approver,
            projectId,
            holdoutId,
            "CONSUMED",
            "evaluation completed",
            "consume-1",
          )
        ).state,
      ).toBe("CONSUMED");
      await expect(
        service.openHoldoutForEvaluation(opener, projectId, holdoutId, {
          evaluationReference: "reuse",
          reason: "forbidden",
          idempotencyKey: "open-3",
        }),
      ).rejects.toThrow("HOLDOUT_REUSE_FORBIDDEN");
      await expect(
        service.transitionHoldout(
          approver,
          projectId,
          holdoutId,
          "SEALED",
          "reseal",
          "reseal-1",
        ),
      ).rejects.toThrow("HOLDOUT_REUSE_FORBIDDEN");
    });
    it("persists independence compromise after material result exposure", async () => {
      await service.recordHoldoutAccess(opener, projectId, holdoutId, {
        accessType: "RESULT_ACCESS",
        scope: "outcomes",
        reason: "result disclosed before tuning",
        authorizationReference: "open-1",
        result: "COMPLETED",
        resourceHash: h("e"),
        independenceImpact: "INDEPENDENCE_COMPROMISED",
        idempotencyKey: "access-2",
      });
      expect(
        await service.assessHoldoutIndependence(opener, projectId, holdoutId),
      ).toMatchObject({
        state: "CONSUMED",
        independence_state: "INDEPENDENCE_COMPROMISED",
      });
    });
    it("retains exact calibration and holdout assignment separation", async () => {
      const rows = (
        await client.query(
          "SELECT evidence_unit_id,role FROM gdss_partition_assignment WHERE partition_plan_version_id=$1 ORDER BY role",
          [planId],
        )
      ).rows;
      expect(rows).toEqual([
        { evidence_unit_id: calibrationId, role: "CALIBRATION" },
        { evidence_unit_id: holdoutUnitId, role: "HOLDOUT" },
      ]);
    });
  });
