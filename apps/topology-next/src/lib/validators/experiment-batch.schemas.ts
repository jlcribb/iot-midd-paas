import { z } from "zod";
export const createExperimentBatchSchema=z.object({search_space_id:z.string().uuid(),simulation_session_id:z.string().uuid(),evaluation_profile_id:z.string().uuid().optional(),name:z.string().trim().min(1).max(160),description:z.string().trim().max(2000).default(""),candidate_ids:z.array(z.string().uuid()).min(1).max(100).optional()}).strict();
