import { z } from "zod";

// M7.6 deliberately accepts no caller-controlled delivery/actor/activation fields.
export const createGovernedDeploymentExecutionSchema = z.object({}).strict();
