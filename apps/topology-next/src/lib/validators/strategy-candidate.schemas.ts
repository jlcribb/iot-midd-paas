import { z } from "zod";

const finite = z.number().finite();
const valuesDomain = z.object({ values: z.array(finite).min(1).max(1000) }).strict();
const rangeDomain = z.object({ min: finite, max: finite, step: finite }).strict();

export const createStrategySearchSpaceSchema = z.object({
  name: z.string().trim().min(1).max(160),
  description: z.string().trim().max(2000).default(""),
  strategy_type: z.enum(["proportional", "threshold"]),
  generation_method: z.literal("GRID"),
  parameters: z.record(z.union([valuesDomain, rangeDomain])).refine((value) => Object.keys(value).length > 0, "parameters must not be empty")
}).strict();
