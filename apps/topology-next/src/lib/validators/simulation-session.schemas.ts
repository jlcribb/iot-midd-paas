import { z } from "zod";

const jsonObjectSchema = z.record(z.unknown());

export const createSimulationSessionSchema = z.object({
  snapshot_refs: jsonObjectSchema.default({}),
  metadata: jsonObjectSchema.default({})
}).strict();

const telemetryRecordSchema = z.object({
  event_id: z.string().uuid(),
  project_id: z.string().uuid(),
  variable: z.string().trim().min(1),
  value: z.number().finite(),
  timestamp: z.string().datetime({ offset: true }),
  context: jsonObjectSchema.default({}),
  metadata: jsonObjectSchema.default({}),
  quality: z.string().trim().min(1).default("raw"),
  source: z.string().trim().min(1).default("simulation.dataset"),
  event_kind: z.literal("telemetry.observed").default("telemetry.observed")
}).strict();

export const prepareSimulationSessionSchema = z.object({
  policy_id: z.string().uuid(),
  dataset: z.object({
    source_kind: z.enum(["historical", "synthetic"]),
    records: z.array(telemetryRecordSchema).min(1).max(10_000)
  }).strict(),
  configuration: z.object({
    initial_virtual_time: z.string().datetime({ offset: true }).optional(),
    random_seed: z.number().int().safe().optional(),
    evaluation_options: z.object({ include_trace: z.boolean().default(true) }).strict().default({ include_trace: true })
  }).strict().default({ evaluation_options: { include_trace: true } })
}).strict();
