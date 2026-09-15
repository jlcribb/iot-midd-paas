import {z} from "zod";
import {uuidSchema} from "@/lib/validators/common";

export const createControlledPolicyVersionCandidateSchema=z.object({proposalId:uuidSchema}).strict();
