import { z } from "zod";
import { assetStatusSchema, assetTypeSchema, metadataSchema, uuidSchema } from "@/lib/validators/common";

const baseAssetSchema = z.object({
  project_id: uuidSchema,
  sector_id: uuidSchema,
  location_id: uuidSchema.nullable().optional(),
  parent_asset_id: uuidSchema.nullable().optional(),
  asset_type: assetTypeSchema,
  subtype: z.string().trim().min(1),
  name: z.string().trim().min(1),
  code: z.string().trim().min(1).nullable().optional(),
  description: z.string().trim().nullable().optional(),
  status: assetStatusSchema.default("inactive"),
  role: z.string().trim().nullable().optional(),
  serial_number: z.string().trim().min(1).nullable().optional(),
  manufacturer: z.string().trim().nullable().optional(),
  model: z.string().trim().nullable().optional(),
  firmware_version: z.string().trim().nullable().optional(),
  hardware_version: z.string().trim().nullable().optional(),
  mac_address: z.string().trim().min(1).nullable().optional(),
  ip_address: z.string().trim().min(1).nullable().optional(),
  last_seen_at: z.string().datetime().nullable().optional(),
  metadata: metadataSchema
});

export const createAssetSchema = baseAssetSchema;

export const updateAssetSchema = baseAssetSchema
  .omit({ project_id: true })
  .partial()
  .refine((payload) => Object.keys(payload).length > 0, "Empty update payload is not allowed");

export type CreateAssetInput = z.infer<typeof createAssetSchema>;
export type UpdateAssetInput = z.infer<typeof updateAssetSchema>;
