import type { ControlAccessSnapshot } from "@/lib/dto/control-access.dto";
import type {
  BindingOperationalView,
  ControlOperationsPage,
  DeliveryOperationalView,
  OperationalAttentionItem,
  PolicyOperationalView,
  ProjectControlOperationsSummary,
  RecommendationOperationalView
} from "@/lib/dto/control-operations.dto";

interface ApiSuccessResponse<T> {
  success: true;
  data: T;
}

interface ApiFailureResponse {
  success: false;
  error?: { message?: string };
}

export class ControlOperationsApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
  }
}

export interface OperationsPageInput {
  limit?: number;
  offset?: number;
}

export interface RecommendationQuery extends OperationsPageInput {
  policyId?: string;
  correlationId?: string;
}

export interface DeliveryQuery extends OperationsPageInput {
  status?: string;
  recommendationId?: string;
  commandId?: string;
  correlationId?: string;
}

function queryString(input: object) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(input)) {
    if ((typeof value === "string" || typeof value === "number") && value !== "") query.set(key, String(value));
  }
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

async function get<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  const payload = await response.json().catch(() => null) as ApiSuccessResponse<T> | ApiFailureResponse | null;
  if (!response.ok || !payload || !payload.success) {
    const message = payload && !payload.success ? payload.error?.message : undefined;
    throw new ControlOperationsApiError(response.status, message || "Unable to load control operations data");
  }
  return payload.data;
}

function projectPath(projectId: string, resource: string, query?: object) {
  return `/api/control/operations/projects/${encodeURIComponent(projectId)}/${resource}${queryString(query ?? {})}`;
}

export const controlOperationsClient = {
  getAccess: () => get<ControlAccessSnapshot>("/api/control/access"),
  getSummary: (projectId: string) => get<ProjectControlOperationsSummary>(projectPath(projectId, "summary")),
  getPolicies: (projectId: string, page: OperationsPageInput) => get<ControlOperationsPage<PolicyOperationalView>>(projectPath(projectId, "policies", page)),
  getBindings: (projectId: string, page: OperationsPageInput) => get<ControlOperationsPage<BindingOperationalView>>(projectPath(projectId, "bindings", page)),
  getRecommendations: (projectId: string, query: RecommendationQuery) => get<ControlOperationsPage<RecommendationOperationalView>>(projectPath(projectId, "recommendations", query)),
  getDeliveries: (projectId: string, query: DeliveryQuery) => get<ControlOperationsPage<DeliveryOperationalView>>(projectPath(projectId, "deliveries", query)),
  getAttention: (projectId: string) => get<OperationalAttentionItem[]>(projectPath(projectId, "attention"))
};
