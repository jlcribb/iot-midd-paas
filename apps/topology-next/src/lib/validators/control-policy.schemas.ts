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
}).passthrough().superRefine((payload, ctx) => {
  if (payload.gain <= 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "gain must be greater than 0",
      path: ["gain"]
    });
  }
  if (payload.deadband < 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "deadband must be greater than or equal to 0",
      path: ["deadband"]
    });
  }
  if (payload.min_action < 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "min_action must be greater than or equal to 0",
      path: ["min_action"]
    });
  }
  if (payload.max_action !== undefined && payload.max_action !== null && payload.max_action < payload.min_action) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "max_action must be greater than or equal to min_action",
      path: ["max_action"]
    });
  }
});

const thresholdParamsSchema = z.object({
  variable_name: z.string().trim().min(1),
  variable_unit: z.string().trim().min(1).optional(),
  actuator_name: z.string().trim().min(1),
  setpoint_value: numericValue,
  tolerance: numericValue,
  increase_step: numericValue,
  decrease_step: numericValue,
  hold_signal: numericValue
}).passthrough().superRefine((payload, ctx) => {
  if (payload.tolerance < 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "tolerance must be greater than or equal to 0",
      path: ["tolerance"]
    });
  }
  if (payload.increase_step < 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "increase_step must be greater than or equal to 0",
      path: ["increase_step"]
    });
  }
  if (payload.decrease_step < 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "decrease_step must be greater than or equal to 0",
      path: ["decrease_step"]
    });
  }
});

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

const previewCandidateSchema = z.object({
  id: uuidSchema.optional(),
  project_id: uuidSchema,
  variable: z.string().trim().min(1),
  policy_type: controlPolicyTypeSchema,
  context_selector: jsonObjectSchema.default({}),
  params: jsonObjectSchema,
  priority: z.number().int().min(0),
  enabled: z.boolean(),
  version: z.number().int().min(1).optional()
}).superRefine((payload, ctx) => {
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
    }
  }
});

export const previewControlPolicySchema = z.object({
  project_id: uuidSchema,
  variable: z.string().trim().min(1),
  context: jsonObjectSchema.default({}),
  candidate_policy: previewCandidateSchema.optional()
}).superRefine((payload, ctx) => {
  if (payload.candidate_policy && payload.candidate_policy.project_id !== payload.project_id) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "candidate_policy.project_id must match project_id",
      path: ["candidate_policy", "project_id"]
    });
  }
  if (payload.candidate_policy && payload.candidate_policy.variable !== payload.variable) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "candidate_policy.variable must match variable",
      path: ["candidate_policy", "variable"]
    });
  }
});

export type CreateControlPolicyInput = z.infer<typeof createControlPolicySchema>;
export type UpdateControlPolicyInput = z.infer<typeof updateControlPolicySchema>;
export type PreviewControlPolicyInput = z.infer<typeof previewControlPolicySchema>;
