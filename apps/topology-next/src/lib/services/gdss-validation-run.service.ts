import type { ControlActor } from "@/lib/dto/control-access.dto";
import {
  assertValidationRunAccess,
  canTransitionValidationRun,
  canonicalObservationReference,
  canonicalPairSet,
  canonicalPairingContract,
  canonicalPrediction,
  canonicalValidationRun,
  type ValidationRunState,
} from "@/lib/gdss/validation";
import { ValidationRunError } from "@/lib/gdss/validation/run-diagnostics";
import { GdssValidationRunRepository } from "@/lib/repositories/gdss-validation-run.repository";

export class GdssValidationRunService {
  constructor(
    private readonly repository = new GdssValidationRunRepository(),
  ) {}
  private run(actor: ControlActor, projectId: string) {
    assertValidationRunAccess(actor, projectId, "RUN_VALIDATION");
  }
  createValidationRun(
    actor: ControlActor,
    projectId: string,
    input: unknown,
    idempotencyKey: string,
  ) {
    this.run(actor, projectId);
    return this.repository.createRun(
      actor,
      projectId,
      canonicalValidationRun(input),
      idempotencyKey,
    );
  }
  private async transition(
    actor: ControlActor,
    projectId: string,
    runId: string,
    target: ValidationRunState,
    reason: string,
    idempotencyKey: string,
  ) {
    this.run(actor, projectId);
    const row = await this.repository.getRun(projectId, runId);
    if (!row) throw new ValidationRunError("VALIDATION_RUN_BINDING_INVALID");
    if (row.status === target) return row;
    if (!canTransitionValidationRun(row.status, target))
      throw new ValidationRunError(
        row.status === "RUNNING"
          ? "VALIDATION_RUN_ALREADY_STARTED"
          : "VALIDATION_RUN_NOT_READY",
      );
    return this.repository.transitionRun(
      actor,
      projectId,
      runId,
      target,
      reason,
      idempotencyKey,
    );
  }
  markValidationRunReady(
    a: ControlActor,
    p: string,
    id: string,
    reason: string,
    key: string,
  ) {
    return this.transition(a, p, id, "READY", reason, key);
  }
  startValidationRun(
    a: ControlActor,
    p: string,
    id: string,
    reason: string,
    key: string,
  ) {
    return this.transition(a, p, id, "RUNNING", reason, key);
  }
  completeValidationRun(
    a: ControlActor,
    p: string,
    id: string,
    reason: string,
    key: string,
  ) {
    return this.transition(a, p, id, "COMPLETED", reason, key);
  }
  failValidationRun(
    a: ControlActor,
    p: string,
    id: string,
    reason: string,
    key: string,
  ) {
    return this.transition(a, p, id, "FAILED", reason, key);
  }
  invalidateValidationRun(
    a: ControlActor,
    p: string,
    id: string,
    reason: string,
    key: string,
  ) {
    return this.transition(a, p, id, "INVALIDATED", reason, key);
  }
  createPrediction(
    a: ControlActor,
    p: string,
    runId: string,
    input: unknown,
    key: string,
  ) {
    this.run(a, p);
    return this.repository.createPrediction(
      a,
      p,
      runId,
      canonicalPrediction(input),
      key,
    );
  }
  commitPrediction(
    a: ControlActor,
    p: string,
    predictionId: string,
    key: string,
  ) {
    this.run(a, p);
    return this.repository.commitPrediction(a, p, predictionId, key);
  }
  createObservationReference(
    a: ControlActor,
    p: string,
    input: unknown,
    key: string,
  ) {
    this.run(a, p);
    return this.repository.createObservationReference(
      a,
      p,
      canonicalObservationReference(input),
      key,
    );
  }
  pairPredictionWithObservation(
    a: ControlActor,
    p: string,
    predictionId: string,
    observationId: string,
    input: unknown,
    key: string,
  ) {
    this.run(a, p);
    return this.repository.pairPrediction(
      a,
      p,
      predictionId,
      observationId,
      canonicalPairingContract(input),
      key,
    );
  }
  assessPairIntegrity(
    a: ControlActor,
    p: string,
    predictionId: string,
    observationId: string,
    input: unknown,
    key: string,
  ) {
    return this.pairPredictionWithObservation(
      a,
      p,
      predictionId,
      observationId,
      input,
      key,
    );
  }
  materializePredictionPairSet(
    a: ControlActor,
    p: string,
    input: unknown,
    key: string,
  ) {
    this.run(a, p);
    return this.repository.materializePairSet(
      a,
      p,
      canonicalPairSet(input),
      key,
    );
  }
}
