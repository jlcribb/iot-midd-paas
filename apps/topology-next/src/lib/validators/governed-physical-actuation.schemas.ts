import{z}from"zod";
export const emptyPhysicalActuationSchema=z.object({}).strict();
export const physicalActuationAuthorizationSchema=z.object({decision:z.enum(["AUTHORIZE_PHYSICAL_ACTUATION_INTENT","REJECT_PHYSICAL_ACTUATION","REQUEST_ACTUATION_REASSESSMENT"]),rationale:z.string().trim().min(10).max(2000)}).strict();
export const emptyGovernedActuationIntentSchema=z.object({}).strict();
