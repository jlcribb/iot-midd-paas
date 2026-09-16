import{z}from"zod";
export const activationAuthorizationSchema=z.object({decision:z.enum(["AUTHORIZE_POLICY_ACTIVATION","REJECT_ACTIVATION","REQUEST_ACTIVATION_REASSESSMENT"]),rationale:z.string().trim().min(10).max(2000)}).strict();
export const emptyActivationSchema=z.object({}).strict();
