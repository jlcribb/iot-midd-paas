import { z } from "zod";
export const createControlledDeploymentPreparationSchema = z.object({ targetAssetId: z.string().uuid() }).strict();
