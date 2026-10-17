import { z } from "zod";
export const governedContentSchema = z
  .object({
    content: z.unknown(),
    idempotencyKey: z.string().trim().min(1).max(256),
  })
  .strict();
export const runTransitionSchema = z
  .object({
    reason: z.string().trim().min(1).max(2000),
    idempotencyKey: z.string().trim().min(1).max(256),
  })
  .strict();
export const predictionCreateSchema = z
  .object({
    content: z.unknown(),
    idempotencyKey: z.string().trim().min(1).max(256),
  })
  .strict();
export const pairCreateSchema = z
  .object({
    observationReferenceId: z.string().uuid(),
    contract: z.unknown(),
    idempotencyKey: z.string().trim().min(1).max(256),
  })
  .strict();
