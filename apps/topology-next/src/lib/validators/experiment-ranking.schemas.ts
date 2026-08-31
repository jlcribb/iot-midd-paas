import { z } from "zod";
import { RANKING_POLICY_VERSION } from "@/lib/dto/experiment-ranking.dto";

export const createExperimentRankingSchema = z.object({ policyVersion: z.literal(RANKING_POLICY_VERSION).optional() }).strict();
