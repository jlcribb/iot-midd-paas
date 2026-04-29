import { z } from "zod";
import { metadataSchema, topologyRelationSchema, topologyStatusSchema, uuidSchema } from "@/lib/validators/common";

const baseTopologySchema = z.object({
  project_id: uuidSchema,
  source_asset_id: uuidSchema.nullable().optional(),
  target_asset_id: uuidSchema.nullable().optional(),
  source_sector_id: uuidSchema.nullable().optional(),
  target_sector_id: uuidSchema.nullable().optional(),
  relation_type: topologyRelationSchema,
  connection_medium: z.string().trim().nullable().optional(),
  protocol: z.string().trim().nullable().optional(),
  ports: z.array(z.unknown()).default([]),
  link_quality: z.number().min(0).max(100).nullable().optional(),
  status: topologyStatusSchema.default("active"),
  metadata: metadataSchema
});

function enforceSourceTarget(payload: z.infer<typeof baseTopologySchema>, ctx: z.RefinementCtx): void {
  const sourceCount = Number(Boolean(payload.source_asset_id)) + Number(Boolean(payload.source_sector_id));
  const targetCount = Number(Boolean(payload.target_asset_id)) + Number(Boolean(payload.target_sector_id));
  if (sourceCount !== 1) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["source_asset_id"],
      message: "exactly one source must be provided"
    });
  }
  if (targetCount !== 1) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["target_asset_id"],
      message: "exactly one target must be provided"
    });
  }
}

export const createTopologyLinkSchema = baseTopologySchema.superRefine(enforceSourceTarget);

export const updateTopologyLinkSchema = baseTopologySchema
  .omit({ project_id: true })
  .partial()
  .refine((payload) => Object.keys(payload).length > 0, "Empty update payload is not allowed");

export const bootstrapNodeWithDevicesSchema = z
  .object({
    project_id: uuidSchema,
    sector_id: uuidSchema.optional(),
    sector: z
      .object({
        name: z.string().trim().min(1),
        code: z.string().trim().min(1).nullable().optional(),
        description: z.string().trim().nullable().optional(),
        location: z
          .object({
            name: z.string().trim().min(1),
            latitude: z.number().min(-90).max(90).nullable().optional(),
            longitude: z.number().min(-180).max(180).nullable().optional(),
            metadata: metadataSchema
          })
          .optional(),
        metadata: metadataSchema
      })
      .optional(),
    node_location: z
      .object({
        name: z.string().trim().min(1),
        latitude: z.number().min(-90).max(90).nullable().optional(),
        longitude: z.number().min(-180).max(180).nullable().optional(),
        metadata: metadataSchema
      })
      .optional(),
    node: z.object({
      subtype: z.string().trim().min(1),
      name: z.string().trim().min(1),
      code: z.string().trim().min(1).nullable().optional(),
      description: z.string().trim().nullable().optional(),
      status: z.enum(["active", "inactive", "provisioning", "online"]).default("active"),
      metadata: metadataSchema
    }),
    devices: z
      .array(
        z.object({
          asset_type: z.enum(["sensor", "actuator"]),
          subtype: z.string().trim().min(1),
          name: z.string().trim().min(1),
          code: z.string().trim().min(1).nullable().optional(),
          description: z.string().trim().nullable().optional(),
          status: z.enum(["active", "inactive", "provisioning", "online"]).default("active"),
          metadata: metadataSchema
        })
      )
      .default([]),
    create_topology_links: z.boolean().default(true)
  })
  .superRefine((payload, ctx) => {
    if (!payload.sector_id && !payload.sector) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["sector_id"],
        message: "sector_id or sector creation payload is required"
      });
    }
    if (payload.sector_id && payload.sector) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["sector"],
        message: "provide sector_id or sector payload, not both"
      });
    }
  });

export type CreateTopologyLinkInput = z.infer<typeof createTopologyLinkSchema>;
export type UpdateTopologyLinkInput = z.infer<typeof updateTopologyLinkSchema>;
export type BootstrapNodeWithDevicesInput = z.infer<typeof bootstrapNodeWithDevicesSchema>;
