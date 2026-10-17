import { z } from "zod";
const key = z.string().trim().min(1).max(256),
  uuid = z.string().uuid();
export const metricIdentityInput = z.object({ metricKey: key }).strict();
export const versionInput = z.object({ content: z.unknown() }).strict();
export const metricExecutionInput = z
  .object({
    metricDefinitionVersionId: uuid,
    pairSetId: uuid,
    idempotencyKey: key,
  })
  .strict();
export const baselineIdentityInput = z
  .object({ logicalName: key, baselineKey: key })
  .strict();
export const baselineGenerationInput = z.object({ pairSetId: uuid }).strict();
export const baselineMetricInput = z
  .object({
    baselineVersionId: uuid,
    metricDefinitionVersionId: uuid,
    pairSetId: uuid,
    idempotencyKey: key,
  })
  .strict();
export const comparisonInput = z
  .object({
    modelMetricResultId: uuid,
    baselineMetricResultId: uuid,
    rule: z.unknown(),
    idempotencyKey: key,
  })
  .strict();
export const uncertaintyInput = z
  .object({
    content: z.unknown(),
    runId: uuid.nullable(),
    pairSetId: uuid.nullable(),
    idempotencyKey: key,
  })
  .strict();
export const intervalInput = z
  .object({ content: z.unknown(), idempotencyKey: key })
  .strict();
export const pairSetActionInput = z
  .object({ pairSetId: uuid, idempotencyKey: key })
  .strict();
export const completenessInput = z
  .object({
    scope: key,
    assessmentIds: z.array(uuid).min(1).max(8),
    idempotencyKey: key,
  })
  .strict();
