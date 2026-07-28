import { z } from "zod";
import { metadataSchema, projectStatusSchema } from "@/lib/validators/common";

export const createProjectSchema = z.object({
  name: z.string().trim().min(1),
  description: z.string().trim().nullable().optional(),
  status: projectStatusSchema.default("draft"),
  parametric_control_enabled: z.boolean().default(false),
  metadata: metadataSchema
});

export const updateProjectSchema = createProjectSchema
  .pick({
    name: true,
    description: true,
    status: true,
    parametric_control_enabled: true,
    metadata: true
  })
  .partial()
  .refine((payload) => Object.keys(payload).length > 0, "Empty update payload is not allowed");

export type CreateProjectInput = z.infer<typeof createProjectSchema>;
export type UpdateProjectInput = z.infer<typeof updateProjectSchema>;
