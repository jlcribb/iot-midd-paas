import { z } from "zod";

const code = z.string().trim().regex(/^[a-z][a-z0-9_]{2,63}$/, "code must be snake_case and 3..64 characters");

const constraintSchema = z.discriminatedUnion("kind", [
  z.object({ metric_id: z.string().uuid(), kind: z.literal("MINIMUM"), lower_bound: z.number().finite(), critical: z.boolean().default(false) }).strict(),
  z.object({ metric_id: z.string().uuid(), kind: z.literal("MAXIMUM"), upper_bound: z.number().finite(), critical: z.boolean().default(false) }).strict(),
  z.object({ metric_id: z.string().uuid(), kind: z.literal("RANGE"), lower_bound: z.number().finite(), upper_bound: z.number().finite(), critical: z.boolean().default(false) }).strict()
]);

export const createEvaluationProfileSchema = z.object({
  code,
  name: z.string().trim().min(1).max(160),
  description: z.string().trim().max(2000).default(""),
  metadata: z.record(z.unknown()).default({}),
  metrics: z.array(z.object({
    metric_id: z.string().uuid(),
    weight: z.number().finite().positive().max(1),
    required: z.boolean().default(true)
  }).strict()).min(1).max(32),
  constraints: z.array(constraintSchema).max(32).default([])
}).strict().superRefine((value, context) => {
  const ids = new Set<string>();
  for (const metric of value.metrics) {
    if (ids.has(metric.metric_id)) context.addIssue({ code: z.ZodIssueCode.custom, path: ["metrics"], message: "metric_id must be unique within a profile" });
    ids.add(metric.metric_id);
  }
  const sum = value.metrics.reduce((total, metric) => total + metric.weight, 0);
  if (Math.abs(sum - 1) > 1e-9) context.addIssue({ code: z.ZodIssueCode.custom, path: ["metrics"], message: "metric weights must sum to 1" });
  const constraintMetrics = new Set<string>();
  for (const [index, constraint] of value.constraints.entries()) {
    if (!ids.has(constraint.metric_id)) context.addIssue({ code: z.ZodIssueCode.custom, path: ["constraints", index, "metric_id"], message: "constraint metric must be included in metrics" });
    if (constraintMetrics.has(constraint.metric_id)) context.addIssue({ code: z.ZodIssueCode.custom, path: ["constraints", index, "metric_id"], message: "only one constraint is permitted per metric" });
    constraintMetrics.add(constraint.metric_id);
    if (constraint.kind === "RANGE" && constraint.lower_bound > constraint.upper_bound) context.addIssue({ code: z.ZodIssueCode.custom, path: ["constraints", index], message: "range lower_bound must not exceed upper_bound" });
  }
});
