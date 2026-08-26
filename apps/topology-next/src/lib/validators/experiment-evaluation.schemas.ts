import { z } from "zod";

export const createExperimentEvaluationSchema = z.object({
  simulationResultId: z.string().uuid(),
  evaluationProfileId: z.string().uuid()
}).strict();
