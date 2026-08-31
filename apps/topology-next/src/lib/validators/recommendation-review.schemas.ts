import { z } from "zod";
export const createRecommendationReviewSchema = z.object({ decision: z.enum(["APPROVE_FOR_FURTHER_TESTING", "REJECT", "REQUEST_MORE_EXPERIMENTS"]), rationale: z.string() }).strict();
