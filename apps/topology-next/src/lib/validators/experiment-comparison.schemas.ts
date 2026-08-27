import { z } from "zod";

export const createExperimentComparisonSchema = z.object({
  baselineEvaluationId: z.string().uuid(), candidateEvaluationId: z.string().uuid()
}).strict().refine((value) => value.baselineEvaluationId !== value.candidateEvaluationId, {
  message: "Baseline and candidate evaluations must be distinct", path: ["candidateEvaluationId"]
});
