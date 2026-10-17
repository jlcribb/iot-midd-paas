import { z } from "zod";
export const validationIdentityInputSchema=z.object({logicalKey:z.string().trim().min(1).max(128)}).strict();
export const validationVersionInputSchema=z.object({content:z.unknown(),predecessorVersionId:z.string().uuid().optional()}).strict();
export const validationDraftUpdateSchema=z.object({content:z.unknown()}).strict();
export const validationTransitionSchema=z.object({reason:z.string().trim().min(1).max(2000),idempotencyKey:z.string().trim().min(1).max(200),sodExceptionReason:z.string().trim().min(1).max(2000).optional()}).strict();
