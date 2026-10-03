import type { PoolClient } from "pg";
import { withTransaction, type TransactionRunner } from "@/lib/db/tx";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { NotFoundError } from "@/lib/errors/domain-errors";
import { assertGdssAccess } from "@/lib/gdss/service";
import { evaluateExpression, type EvaluationContext, type ModelVersionSnapshot } from "@/lib/gdss/expression";

export class GdssEvaluationService {
  constructor(private readonly transaction: TransactionRunner = withTransaction) {}

  async evaluate(actor: ControlActor, projectId: string, modelVersionId: string, context: Omit<EvaluationContext,"projectId"|"modelVersionId">) {
    assertGdssAccess(actor,projectId,"evaluate");
    return this.transaction(async (tx: PoolClient) => {
      const result = await tx.query<ModelVersionSnapshot & { project_id:string }>(
        "SELECT v.id,v.content,v.content_hash,v.lifecycle_status,i.project_id FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=$1::uuid AND i.project_id=$2::uuid",
        [modelVersionId,projectId]
      );
      if (!result.rows[0]) throw new NotFoundError("GDSS version not found");
      return evaluateExpression(result.rows[0],{...context,projectId,modelVersionId});
    });
  }
}
