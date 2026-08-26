export type EvaluationMetricDirection = "MINIMIZE" | "MAXIMIZE" | "TARGET" | "RANGE";
export type EvaluationNormalizationMethod = "MIN_MAX" | "TARGET_DISTANCE" | "RANGE_DISTANCE";

export interface EvaluationMetric {
  id: string;
  code: string;
  version: number;
  name: string;
  description: string;
  unit: string | null;
  direction: EvaluationMetricDirection;
  normalization_method: EvaluationNormalizationMethod;
  normalization_config: Record<string, unknown>;
  weightable: boolean;
  active: boolean;
  created_at: string;
}

export interface EvaluationProfileMetric {
  metric: EvaluationMetric;
  weight: number;
  required: boolean;
}

export interface EvaluationProfile {
  id: string;
  project_id: string;
  code: string;
  version: number;
  name: string;
  description: string;
  status: "ACTIVE" | "RETIRED";
  schema_version: 1;
  metadata: Record<string, unknown>;
  created_by: string;
  created_at: string;
  metrics: EvaluationProfileMetric[];
}

export interface CreateEvaluationProfileInput {
  code: string;
  name: string;
  description?: string;
  metadata?: Record<string, unknown>;
  metrics: Array<{ metric_id: string; weight: number; required?: boolean }>;
}
