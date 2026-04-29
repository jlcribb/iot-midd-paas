import { z } from "zod";
import { metadataSchema } from "@/lib/validators/common";

const baseLocationSchema = z.object({
  name: z.string().trim().min(1),
  description: z.string().trim().nullable().optional(),
  latitude: z.number().min(-90).max(90).nullable().optional(),
  longitude: z.number().min(-180).max(180).nullable().optional(),
  altitude: z.number().nullable().optional(),
  accuracy_meters: z.number().min(0).nullable().optional(),
  country: z.string().trim().nullable().optional(),
  province: z.string().trim().nullable().optional(),
  city: z.string().trim().nullable().optional(),
  address_text: z.string().trim().nullable().optional(),
  building: z.string().trim().nullable().optional(),
  floor: z.string().trim().nullable().optional(),
  zone: z.string().trim().nullable().optional(),
  rack: z.string().trim().nullable().optional(),
  position: z.string().trim().nullable().optional(),
  metadata: metadataSchema
});

export const createLocationSchema = baseLocationSchema.superRefine((payload, ctx) => {
  const hasLat = payload.latitude !== undefined && payload.latitude !== null;
  const hasLon = payload.longitude !== undefined && payload.longitude !== null;
  if (hasLat !== hasLon) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["longitude"],
      message: "latitude and longitude must be provided together"
    });
  }
});

export const updateLocationSchema = baseLocationSchema
  .partial()
  .refine((payload) => Object.keys(payload).length > 0, "Empty update payload is not allowed")
  .superRefine((payload, ctx) => {
    const hasLat = "latitude" in payload;
    const hasLon = "longitude" in payload;
    if (hasLat !== hasLon) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["longitude"],
        message: "latitude and longitude must be provided together"
      });
    }
  });

export type CreateLocationInput = z.infer<typeof createLocationSchema>;
export type UpdateLocationInput = z.infer<typeof updateLocationSchema>;
