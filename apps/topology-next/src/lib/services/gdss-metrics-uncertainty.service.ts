import type { ControlActor } from "@/lib/dto/control-access.dto";
import {
  assertMetricDefinition,
  assertValidationRunAccess,
  baselineKeys,
  canonicalBaselineDefinition,
  canonicalComparisonRule,
  canonicalMetricDefinition,
  canonicalPredictionInterval,
  canonicalUncertaintyAssessment,
  metricKeys,
} from "@/lib/gdss/validation";
import { MetricFoundationError } from "@/lib/gdss/validation/metric-diagnostics";
import { GdssMetricsUncertaintyRepository } from "@/lib/repositories/gdss-metrics-uncertainty.repository";
export class GdssMetricsUncertaintyService {
  constructor(
    private readonly repository = new GdssMetricsUncertaintyRepository(),
  ) {}
  private auth(a: ControlActor, p: string) {
    assertValidationRunAccess(a, p, "RUN_VALIDATION");
  }
  createMetricDefinitionIdentity(a: ControlActor, p: string, key: string) {
    this.auth(a, p);
    if (!metricKeys.includes(key as any))
      throw new MetricFoundationError("METRIC_NOT_ALLOWED");
    return this.repository.createMetricIdentity(a, p, key);
  }
  createMetricDefinitionVersion(
    a: ControlActor,
    p: string,
    id: string,
    input: unknown,
  ) {
    this.auth(a, p);
    const c = canonicalMetricDefinition(input);
    assertMetricDefinition(c);
    return this.repository.createMetricVersion(a, p, id, c);
  }
  computeMetricResult(
    a: ControlActor,
    p: string,
    version: string,
    set: string,
    key: string,
  ) {
    this.auth(a, p);
    return this.repository.computeMetricResult(a, p, version, set, key);
  }
  createBaselineIdentity(
    a: ControlActor,
    p: string,
    name: string,
    key: string,
  ) {
    this.auth(a, p);
    if (!baselineKeys.includes(key as any))
      throw new MetricFoundationError("BASELINE_NOT_ALLOWED");
    return this.repository.createBaselineIdentity(a, p, name, key);
  }
  createBaselineVersion(
    a: ControlActor,
    p: string,
    id: string,
    input: unknown,
  ) {
    this.auth(a, p);
    return this.repository.createBaselineVersion(
      a,
      p,
      id,
      canonicalBaselineDefinition(input),
    );
  }
  generateBaselinePredictions(
    a: ControlActor,
    p: string,
    v: string,
    set: string,
  ) {
    this.auth(a, p);
    return this.repository.generateBaselinePredictions(a, p, v, set);
  }
  computeBaselineMetricResult(
    a: ControlActor,
    p: string,
    b: string,
    m: string,
    set: string,
    key: string,
  ) {
    this.auth(a, p);
    return this.repository.computeBaselineMetricResult(a, p, b, m, set, key);
  }
  compareModelToBaseline(
    a: ControlActor,
    p: string,
    m: string,
    b: string,
    input: unknown,
    key: string,
  ) {
    this.auth(a, p);
    return this.repository.compare(
      a,
      p,
      m,
      b,
      canonicalComparisonRule(input),
      key,
    );
  }
  createUncertaintyAssessment(
    a: ControlActor,
    p: string,
    input: unknown,
    run: string | null,
    set: string | null,
    key: string,
  ) {
    this.auth(a, p);
    return this.repository.createUncertaintyAssessment(
      a,
      p,
      canonicalUncertaintyAssessment(input),
      run,
      set,
      key,
    );
  }
  createPredictionInterval(
    a: ControlActor,
    p: string,
    input: unknown,
    key: string,
  ) {
    this.auth(a, p);
    return this.repository.createPredictionInterval(
      a,
      p,
      canonicalPredictionInterval(input),
      key,
    );
  }
  assessIntervalCoverage(a: ControlActor, p: string, set: string, key: string) {
    this.auth(a, p);
    return this.repository.assessIntervalCoverage(a, p, set, key);
  }
  assessUncertaintyCompleteness(
    a: ControlActor,
    p: string,
    scope: string,
    ids: string[],
    key: string,
  ) {
    this.auth(a, p);
    return this.repository.assessCompleteness(a, p, scope, ids, key);
  }
}
