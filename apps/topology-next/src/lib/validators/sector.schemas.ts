import { z } from "zod";
import { metadataSchema, uuidSchema } from "@/lib/validators/common";

const baseSectorSchema = z.object({
  project_id: uuidSchema,
  location_id: uuidSchema.nullable().optional(),
  name: z.string().trim().min(1),
  code: z.string().trim().min(1).nullable().optional(),
  description: z.string().trim().nullable().optional(),
  metadata: metadataSchema
});

export const createSectorSchema = baseSectorSchema;

export const updateSectorSchema = baseSectorSchema
  .omit({ project_id: true })
  .partial()
  .refine((payload) => Object.keys(payload).length > 0, "Empty update payload is not allowed");

export type CreateSectorInput = z.infer<typeof createSectorSchema>;
export type UpdateSectorInput = z.infer<typeof updateSectorSchema>;
