import { z } from "zod";
export const createGovernedDeploymentAuthorizationSchema = z.object({ decision:z.enum(["AUTHORIZE_CONTROLLED_DEPLOYMENT_INTENT","REJECT_DEPLOYMENT","REQUEST_READINESS_REASSESSMENT"]), rationale:z.string().trim().min(10).max(2000) }).strict();
