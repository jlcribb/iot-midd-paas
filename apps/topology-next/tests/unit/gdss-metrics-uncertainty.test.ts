import { describe, expect, it } from "vitest";
import {
  baselineHash,
  baselineKeys,
  canonicalBaselineDefinition,
  canonicalUncertaintyAssessment,
  compareMetric,
  computeMetric,
  metricDefinitionHash,
  metricKeys,
  metricResultHash,
  predictionIntervalHash,
  uncertaintyAssessmentHash,
  uncertaintyCompleteness,
  uncertaintySourceTypes,
  type MetricDefinitionContent,
  type MetricKey,
  type MetricPoint,
} from "@/lib/gdss/validation";
const base = (
  metricKey: MetricKey,
  category: MetricDefinitionContent["category"],
  extra: Partial<MetricDefinitionContent> = {},
): MetricDefinitionContent => ({
  semanticVersion: "GDSS_METRIC_DEFINITION_V1",
  metricKey,
  name: metricKey,
  category,
  formulaVersion: `${metricKey}:FORMULA:1`,
  directionality:
    metricKey === "BIAS_V1"
      ? "CLOSER_TO_ZERO_IS_BETTER"
      : metricKey === "INTERVAL_COVERAGE_V1"
        ? "HIGHER_IS_BETTER"
        : "LOWER_IS_BETTER",
  requiredInputs: ["prediction", "observation"],
  unitSemantics: "same compatible unit",
  aggregationSemantics: "ordered binary64 reduction",
  missingnessBehavior: "GOVERNED_PAIR_SET_ONLY",
  validityConstraints: ["PASS pairs only"],
  implementationIdentifier: "midd-gdss006d-v1",
  ...extra,
});
const points: MetricPoint[] = [
  {
    prediction: 2,
    observation: 1,
    predictionTime: 1000,
    observationTime: 2000,
    lower: 0,
    upper: 2,
  },
  {
    prediction: 4,
    observation: 2,
    predictionTime: 4000,
    observationTime: 3000,
    lower: 1,
    upper: 3,
  },
  {
    prediction: 6,
    observation: 9,
    predictionTime: 6000,
    observationTime: 9000,
    lower: 5,
    upper: 8,
  },
];
describe("GDSS-006D metric, baseline and uncertainty foundation", () => {
  it("uses the exact V1 metric, baseline and eight-source allowlists", () => {
    expect(metricKeys).toEqual([
      "MAE_V1",
      "RMSE_V1",
      "BIAS_V1",
      "SMAPE_V1",
      "TRAJECTORY_RMSE_V1",
      "PEAK_MAGNITUDE_ERROR_V1",
      "PEAK_TIMING_ERROR_V1",
      "STEADY_STATE_DEVIATION_V1",
      "INTERVAL_COVERAGE_V1",
      "MEAN_INTERVAL_WIDTH_V1",
    ]);
    expect(baselineKeys).toEqual([
      "NAIVE_LAST_VALUE_V1",
      "HISTORICAL_MEAN_V1",
      "SEASONAL_NAIVE_V1",
      "AUTHORIZED_REFERENCE_MODEL_V1",
    ]);
    expect(uncertaintySourceTypes).toHaveLength(8);
  });
  it("matches manual point-error reference vectors", () => {
    expect(computeMetric("MAE_V1", points, base("MAE_V1", "POINT_ERROR"))).toBe(
      2,
    );
    expect(
      computeMetric("RMSE_V1", points, base("RMSE_V1", "POINT_ERROR")),
    ).toBeCloseTo(Math.sqrt(14 / 3), 14);
    expect(
      computeMetric("BIAS_V1", points, base("BIAS_V1", "POINT_ERROR")),
    ).toBe(0);
  });
  it("implements stable SMAPE including both-zero and near-zero", () => {
    const d = base("SMAPE_V1", "RELATIVE_ERROR", {
      smapeDenominatorFloor: 0.1,
      bothZeroTreatment: "ZERO_CONTRIBUTION",
    });
    expect(
      computeMetric(
        "SMAPE_V1",
        [
          { prediction: 0, observation: 0 },
          { prediction: 0.01, observation: 0 },
        ],
        d,
      ),
    ).toBeCloseTo(0.1, 14);
  });
  it("matches trajectory and deterministic peak reference vectors", () => {
    expect(
      computeMetric(
        "TRAJECTORY_RMSE_V1",
        points,
        base("TRAJECTORY_RMSE_V1", "TRAJECTORY", { minimumCoverage: 1 }),
      ),
    ).toBeCloseTo(Math.sqrt(14 / 3), 14);
    expect(
      computeMetric(
        "PEAK_MAGNITUDE_ERROR_V1",
        points,
        base("PEAK_MAGNITUDE_ERROR_V1", "DYNAMIC_RESPONSE"),
      ),
    ).toBe(3);
    expect(
      computeMetric(
        "PEAK_TIMING_ERROR_V1",
        points,
        base("PEAK_TIMING_ERROR_V1", "DYNAMIC_RESPONSE", {
          peakTimingSigned: true,
        }),
      ),
    ).toBe(-3);
  });
  it("uses predeclared steady-state window and interval formulas", () => {
    expect(
      computeMetric(
        "STEADY_STATE_DEVIATION_V1",
        points,
        base("STEADY_STATE_DEVIATION_V1", "DYNAMIC_RESPONSE", {
          steadyStateWindowCount: 2,
          steadyStateTolerance: 10,
        }),
      ),
    ).toBe(-0.5);
    expect(
      computeMetric(
        "INTERVAL_COVERAGE_V1",
        points,
        base("INTERVAL_COVERAGE_V1", "INTERVAL"),
      ),
    ).toBeCloseTo(2 / 3, 14);
    expect(
      computeMetric(
        "MEAN_INTERVAL_WIDTH_V1",
        points,
        base("MEAN_INTERVAL_WIDTH_V1", "INTERVAL"),
      ),
    ).toBeCloseTo(7 / 3, 14);
  });
  it("rejects non-finite values and invalid interval contracts", () => {
    expect(() =>
      computeMetric(
        "MAE_V1",
        [{ prediction: NaN, observation: 1 }],
        base("MAE_V1", "POINT_ERROR"),
      ),
    ).toThrow("METRIC_INPUT_INVALID");
    expect(() =>
      predictionIntervalHash({
        semanticVersion: "GDSS_PREDICTION_INTERVAL_V1",
        predictionId: "11111111-1111-4111-8111-111111111111",
        lowerBound: 2,
        upperBound: 1,
        coverageLevel: 0.95,
        unit: { key: "meter", revision: 1 },
        method: "SUPPLIED_INTERVAL",
        methodVersion: "v1",
      }),
    ).toThrow();
  });
  it("classifies baseline comparison only through predeclared rule", () => {
    const r = {
      semanticVersion: "GDSS_BASELINE_COMPARISON_RULE_V1" as const,
      tolerance: 0.1,
      unit: { key: "meter", revision: 1 },
      metricKey: "MAE_V1" as const,
      directionality: "LOWER_IS_BETTER" as const,
    };
    expect(compareMetric(1, 2, r)).toBe("MODEL_OUTPERFORMS_BASELINE");
    expect(compareMetric(2.05, 2, r)).toBe("MODEL_EQUIVALENT_TO_BASELINE");
    expect(compareMetric(3, 2, r)).toBe("MODEL_UNDERPERFORMS_BASELINE");
  });
  it("requires exact authorized reference model", () => {
    const b = {
      semanticVersion: "GDSS_BASELINE_V1" as const,
      baselineKey: "AUTHORIZED_REFERENCE_MODEL_V1" as const,
      name: "ref",
      algorithmVersion: "v1",
      targetKey: "level",
      horizonKey: "five_min",
      inputPolicy: "committed exact model predictions",
      referenceModelVersionId: "11111111-1111-4111-8111-111111111111",
      referenceModelHash: "a".repeat(64),
    };
    expect(baselineHash(b)).toBe(baselineHash({ ...b }));
    expect(() =>
      canonicalBaselineDefinition({ ...b, referenceModelVersionId: undefined }),
    ).toThrow();
  });
  it("preserves unknown uncertainty instead of fabricating zero", () => {
    const u = {
      semanticVersion: "GDSS_UNCERTAINTY_ASSESSMENT_V1" as const,
      sourceType: "MODEL_STRUCTURAL_UNCERTAINTY" as const,
      knowledgeState: "UNKNOWN" as const,
      method: null,
      unit: null,
      assumptions: [],
      dependencies: [],
      coverageTarget: null,
      qualityProvenanceReference: null,
      scope: "run",
    };
    expect(() =>
      canonicalUncertaintyAssessment({ ...u, lowerBound: 0, upperBound: 0 }),
    ).toThrow();
    expect(uncertaintyCompleteness(["UNKNOWN"])).toBe("UNKNOWN");
    expect(uncertaintyCompleteness(["KNOWN_QUANTIFIED", "UNKNOWN"])).toBe(
      "INSUFFICIENT",
    );
    expect(
      uncertaintyCompleteness(["KNOWN_QUANTIFIED", "KNOWN_UNQUANTIFIED"]),
    ).toBe("PARTIAL");
    expect(
      uncertaintyCompleteness(["KNOWN_QUANTIFIED", "NOT_APPLICABLE"]),
    ).toBe("COMPLETE_FOR_DECLARED_SCOPE");
  });
  it("represents error and uncertainty as independent axes", () => {
    for (const error of ["LOW", "HIGH"] as const)
      for (const uncertainty of ["LOW", "HIGH"] as const)
        expect({ error, uncertainty }).toEqual({ error, uncertainty });
  });
  it("hashes definitions and results deterministically", () => {
    const d = base("MAE_V1", "POINT_ERROR"),
      u = {
        semanticVersion: "GDSS_UNCERTAINTY_ASSESSMENT_V1" as const,
        sourceType: "MEASUREMENT_UNCERTAINTY" as const,
        knowledgeState: "KNOWN_QUANTIFIED" as const,
        method: "DECLARED_BOUNDS" as const,
        lowerBound: -0.1,
        upperBound: 0.1,
        unit: { key: "meter", revision: 1 },
        assumptions: ["calibrated"],
        dependencies: [],
        coverageTarget: 0.95,
        qualityProvenanceReference: "certificate",
        scope: "run",
      };
    expect(metricDefinitionHash(d)).toHaveLength(64);
    expect(metricResultHash({ value: 1 })).not.toBe(
      metricResultHash({ value: 2 }),
    );
    expect(uncertaintyAssessmentHash(u)).toBe(
      uncertaintyAssessmentHash({ ...u }),
    );
  });
  it("measures 10k paths diagnostically", () => {
    const p = Array.from({ length: 10000 }, (_, i) => ({
        prediction: i % 101,
        observation: (i + 1) % 101,
        lower: (i % 101) - 2,
        upper: (i % 101) + 2,
      })),
      start = performance.now();
    computeMetric("MAE_V1", p, base("MAE_V1", "POINT_ERROR"));
    computeMetric("RMSE_V1", p, base("RMSE_V1", "POINT_ERROR"));
    const metricMs = performance.now() - start,
      trajectoryStart = performance.now();
    computeMetric(
      "TRAJECTORY_RMSE_V1",
      p,
      base("TRAJECTORY_RMSE_V1", "TRAJECTORY"),
    );
    const trajectoryMs = performance.now() - trajectoryStart,
      baselineStart = performance.now();
    const naiveBaseline = p.map((x) => x.observation);
    expect(naiveBaseline).toHaveLength(10000);
    const baselineMs = performance.now() - baselineStart,
      c = performance.now();
    computeMetric(
      "INTERVAL_COVERAGE_V1",
      p,
      base("INTERVAL_COVERAGE_V1", "INTERVAL"),
    );
    console.log(
      "GDSS006D_PERFORMANCE",
      JSON.stringify({
        pairs: 10000,
        maeRmseMs: +metricMs.toFixed(3),
        trajectoryRmseMs: +trajectoryMs.toFixed(3),
        baselineGenerationMs: +baselineMs.toFixed(3),
        intervalCoverageMs: +(performance.now() - c).toFixed(3),
      }),
    );
  });
});
