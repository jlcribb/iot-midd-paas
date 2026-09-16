import{z}from"zod";
export const controlLoopAuthorizationSchema=z.object({decision:z.enum(["AUTHORIZE_SHADOW_CONTROL_LOOP","REJECT_CONTROL_LOOP_ENABLEMENT","REQUEST_CONTROL_LOOP_REASSESSMENT"]),rationale:z.string().trim().min(10).max(2000)}).strict();
export const controlLoopSessionSchema=z.object({execution_mode:z.enum(["SHADOW","DRY_RUN"]),max_cycles:z.number().int().min(1).max(100),input_snapshots:z.array(z.record(z.unknown())).max(100).default([])}).strict().superRefine((x,ctx)=>{if(x.input_snapshots.length>x.max_cycles)ctx.addIssue({code:z.ZodIssueCode.custom,path:["input_snapshots"],message:"input_snapshots cannot exceed max_cycles"});});
export const emptyControlLoopSchema=z.object({}).strict();
