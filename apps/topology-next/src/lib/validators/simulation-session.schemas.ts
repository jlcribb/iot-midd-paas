import { z } from "zod";

const jsonObjectSchema = z.record(z.unknown());

export const createSimulationSessionSchema = z.object({
  snapshot_refs: jsonObjectSchema.default({}),
  metadata: jsonObjectSchema.default({})
}).strict();
