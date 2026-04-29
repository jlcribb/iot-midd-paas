import { z } from "zod";
import { metadataSchema, topologyViewTypeSchema, uuidSchema } from "@/lib/validators/common";

export const createTopologyViewSchema = z.object({
  name: z.string().trim().min(1),
  view_type: topologyViewTypeSchema.default("logical"),
  is_default: z.boolean().default(false),
  metadata: metadataSchema
});

export const updateTopologyViewSchema = createTopologyViewSchema
  .pick({
    name: true,
    is_default: true,
    metadata: true
  })
  .partial()
  .refine((payload) => Object.keys(payload).length > 0, "Empty update payload is not allowed");

const topologyNodeLayoutInputSchema = z
  .object({
    asset_id: uuidSchema.nullable().optional(),
    sector_id: uuidSchema.nullable().optional(),
    x: z.number().finite(),
    y: z.number().finite(),
    width: z.number().positive().nullable().optional(),
    height: z.number().positive().nullable().optional(),
    collapsed: z.boolean().default(false),
    hidden: z.boolean().default(false),
    z_index: z.number().int().default(0),
    metadata: metadataSchema
  })
  .superRefine((payload, ctx) => {
    const hasAsset = Boolean(payload.asset_id);
    const hasSector = Boolean(payload.sector_id);
    if (Number(hasAsset) + Number(hasSector) !== 1) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["asset_id"],
        message: "exactly one entity reference is required (asset_id or sector_id)"
      });
    }
  });

const topologyLinkLayoutInputSchema = z.object({
  topology_link_id: uuidSchema,
  hidden: z.boolean().default(false),
  label_offset_x: z.number().finite().default(0),
  label_offset_y: z.number().finite().default(0),
  metadata: metadataSchema
});

export const saveTopologyViewLayoutSchema = z.object({
  node_layouts: z.array(topologyNodeLayoutInputSchema).default([]),
  link_layouts: z.array(topologyLinkLayoutInputSchema).default([])
});

export type CreateTopologyViewInput = z.infer<typeof createTopologyViewSchema>;
export type UpdateTopologyViewInput = z.infer<typeof updateTopologyViewSchema>;
export type SaveTopologyViewLayoutInput = z.infer<typeof saveTopologyViewLayoutSchema>;
export type TopologyNodeLayoutInput = z.infer<typeof topologyNodeLayoutInputSchema>;
export type TopologyLinkLayoutInput = z.infer<typeof topologyLinkLayoutInputSchema>;
