import { z } from "zod";
import { uuidSchema } from "@/lib/validators/common";

const jsonObjectSchema = z.record(z.unknown());
const numericValue = z.number().finite();

export const controlPolicyTypeSchema = z.enum(["proportional", "threshold"]);

export function normalizeControlVariableKey(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

const canonicalVariableKeySchema = z.string().trim().min(1).transform(normalizeControlVariableKey).refine(
  (value) => value.length > 0,
  "variable must contain at least one alphanumeric character"
);

const policyBindingSchema = z.object({
  asset_id: uuidSchema,
  variable_key: canonicalVariableKeySchema
});

export const controlOperationSchema = z.enum(["set", "increase", "decrease", "toggle"]);
const actuationBindingSchema = z.object({
  target_asset_id: uuidSchema,
  control_point: z.string().trim().min(1),
  operation: controlOperationSchema
});

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
  variable: canonicalVariableKeySchema,
  binding: policyBindingSchema,
  actuation_binding: actuationBindingSchema.optional(),
  policy_type: controlPolicyTypeSchema,
  context_selector: jsonObjectSchema.default({}),
  params: jsonObjectSchema,
  priority: z.number().int().min(0).default(0),
  enabled: z.boolean().default(true)
});

export const createControlPolicySchema = createPolicyBaseSchema.superRefine((payload, ctx) => {
  if (payload.binding.variable_key !== payload.variable) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "binding.variable_key must match variable",
      path: ["binding", "variable_key"]
    });
  }
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
  binding: policyBindingSchema.optional(),
  actuation_binding: actuationBindingSchema.nullable().optional(),
  context_selector: jsonObjectSchema.optional(),
  params: jsonObjectSchema.optional(),
  priority: z.number().int().min(0).optional(),
  enabled: z.boolean().optional()
}).refine((payload) => Object.keys(payload).length > 0, "Empty update payload is not allowed");

const previewCandidateSchema = z.object({
  id: uuidSchema.optional(),
  project_id: uuidSchema,
  variable: canonicalVariableKeySchema,
  binding: policyBindingSchema.nullable().default(null),
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
  variable: canonicalVariableKeySchema,
  asset_id: uuidSchema.optional(),
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
  if (payload.candidate_policy?.binding && payload.candidate_policy.binding.variable_key !== payload.variable) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "candidate_policy.binding.variable_key must match variable",
      path: ["candidate_policy", "binding", "variable_key"]
    });
  }
  if (
    payload.candidate_policy?.binding &&
    payload.asset_id &&
    payload.candidate_policy.binding.asset_id !== payload.asset_id
  ) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "candidate_policy.binding.asset_id must match asset_id",
      path: ["candidate_policy", "binding", "asset_id"]
    });
  }
});

export type CreateControlPolicyInput = z.infer<typeof createControlPolicySchema>;
export type UpdateControlPolicyInput = z.infer<typeof updateControlPolicySchema>;
export type PreviewControlPolicyInput = z.infer<typeof previewControlPolicySchema>;
