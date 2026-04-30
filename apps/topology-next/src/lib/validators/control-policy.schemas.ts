import { z } from "zod";
import { uuidSchema } from "@/lib/validators/common";

const jsonObjectSchema = z.record(z.unknown());
const numericValue = z.number().finite();

export const controlPolicyTypeSchema = z.enum(["proportional", "threshold"]);

const proportionalParamsSchema = z.object({
  variable_name: z.string().trim().min(1),
  variable_unit: z.string().trim().min(1).optional(),
  actuator_name: z.string().trim().min(1),
  setpoint_value: numericValue,
  gain: numericValue,
  deadband: numericValue,
  min_action: numericValue,
  max_action: numericValue.nullable().optional()
}).passthrough();

const thresholdParamsSchema = z.object({
  variable_name: z.string().trim().min(1),
  variable_unit: z.string().trim().min(1).optional(),
  actuator_name: z.string().trim().min(1),
  setpoint_value: numericValue,
  tolerance: numericValue,
  increase_step: numericValue,
  decrease_step: numericValue,
  hold_signal: numericValue
}).passthrough();

export function validatePolicyParams(policyType: z.infer<typeof controlPolicyTypeSchema>, params: unknown) {
  if (policyType === "proportional") {
    return proportionalParamsSchema.parse(params);
  }
  return thresholdParamsSchema.parse(params);
}

const createPolicyBaseSchema = z.object({
  project_id: uuidSchema,
  variable: z.string().trim().min(1),
  policy_type: controlPolicyTypeSchema,
  context_selector: jsonObjectSchema.default({}),
  params: jsonObjectSchema,
  priority: z.number().int().min(0).default(0),
  enabled: z.boolean().default(true)
});

export const createControlPolicySchema = createPolicyBaseSchema.superRefine((payload, ctx) => {
  try {
    validatePolicyParams(payload.policy_type, payload.params);
  } catch (error) {
    if (error instanceof z.ZodError) {
      for (const issue of error.issues) {
        ctx.addIssue({
          ...issue,
          path: ["params", ...issue.path]
        });
      }
      return;
    }
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Invalid policy params",
      path: ["params"]
    });
  }
});

export const updateControlPolicySchema = z.object({
  context_selector: jsonObjectSchema.optional(),
  params: jsonObjectSchema.optional(),
  priority: z.number().int().min(0).optional(),
  enabled: z.boolean().optional()
}).refine((payload) => Object.keys(payload).length > 0, "Empty update payload is not allowed");

export type CreateControlPolicyInput = z.infer<typeof createControlPolicySchema>;
export type UpdateControlPolicyInput = z.infer<typeof updateControlPolicySchema>;
