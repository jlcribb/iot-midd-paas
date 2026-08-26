import { z } from "zod";

const code = z.string().trim().regex(/^[a-z][a-z0-9_]{2,63}$/, "code must be snake_case and 3..64 characters");

export const createEvaluationProfileSchema = z.object({
  code,
  name: z.string().trim().min(1).max(160),
  description: z.string().trim().max(2000).default(""),
  metadata: z.record(z.unknown()).default({}),
  metrics: z.array(z.object({
    metric_id: z.string().uuid(),
    weight: z.number().finite().positive().max(1),
    required: z.boolean().default(true)
  }).strict()).min(1).max(32)
}).strict().superRefine((value, context) => {
  const ids = new Set<string>();
  for (const metric of value.metrics) {
    if (ids.has(metric.metric_id)) context.addIssue({ code: z.ZodIssueCode.custom, path: ["metrics"], message: "metric_id must be unique within a profile" });
    ids.add(metric.metric_id);
  }
  const sum = value.metrics.reduce((total, metric) => total + metric.weight, 0);
  if (Math.abs(sum - 1) > 1e-9) context.addIssue({ code: z.ZodIssueCode.custom, path: ["metrics"], message: "metric weights must sum to 1" });
});
