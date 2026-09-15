import { describe, expect, it, vi } from "vitest";
import { ConflictError } from "@/lib/errors/domain-errors";
import { ControlledDeploymentPreparationRepository } from "@/lib/repositories/controlled-deployment-preparation.repository";

const projectId = "11111111-1111-4111-8111-111111111111", candidateId = "22222222-2222-4222-8222-222222222222", targetId = "33333333-3333-4333-8333-333333333333";
describe("ControlledDeploymentPreparationRepository", () => {
  it("denies missing, rejected, or cross-project M7.3 provenance before persistence", async () => {
    for (const input of [null, { m7_3_approved: false, target_project_id: projectId }, { m7_3_approved: true, target_project_id: "44444444-4444-4444-8444-444444444444" }]) {
      const query = vi.fn().mockResolvedValue({ rows: input ? [input] : [] });
      const transaction = async <T>(fn: any): Promise<T> => fn({ query });
      const repository = new ControlledDeploymentPreparationRepository({ query } as never, transaction as never);
      await expect(repository.createOrGet(projectId,candidateId,targetId,"actor")).rejects.toBeInstanceOf(ConflictError);
      expect(query).toHaveBeenCalledTimes(1);
    }
  });
});
