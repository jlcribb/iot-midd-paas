import type {
  ApiAsset,
  ApiProject,
  ApiSector,
  ApiTopologyLink,
  ApiTopologyLinkLayout,
  ApiTopologyNodeLayout,
  ApiTopologyView,
  ApiTopologyViewLayoutPayload,
  ViewType
} from "@/components/topology/types";

interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
  };
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });
  const json = (await response.json()) as ApiResponse<T>;
  if (!response.ok || !json.success) {
    throw new Error(json.error?.message ?? `Request failed: ${response.status}`);
  }
  return json.data;
}

export async function listProjects(): Promise<ApiProject[]> {
  return request<ApiProject[]>("/api/projects");
}

export async function updateProject(id: string, payload: {
  name?: string;
  description?: string | null;
  status?: ApiProject["status"];
  parametric_control_enabled?: boolean;
  metadata?: Record<string, unknown>;
}): Promise<ApiProject> {
  return request<ApiProject>(`/api/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function listSectors(projectId: string): Promise<ApiSector[]> {
  return request<ApiSector[]>(`/api/projects/${projectId}/sectors`);
}

export async function listAssets(projectId: string): Promise<ApiAsset[]> {
  return request<ApiAsset[]>(`/api/projects/${projectId}/assets`);
}

export async function listTopology(projectId: string): Promise<ApiTopologyLink[]> {
  return request<ApiTopologyLink[]>(`/api/projects/${projectId}/topology`);
}

export async function listTopologyViews(projectId: string, viewType?: ViewType): Promise<ApiTopologyView[]> {
  const query = viewType ? `?view_type=${viewType}` : "";
  return request<ApiTopologyView[]>(`/api/projects/${projectId}/topology/views${query}`);
}

export async function createTopologyView(projectId: string, payload: {
  name: string;
  view_type: ViewType;
  is_default: boolean;
  metadata?: Record<string, unknown>;
}): Promise<ApiTopologyView> {
  return request<ApiTopologyView>(`/api/projects/${projectId}/topology/views`, {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      metadata: payload.metadata ?? {}
    })
  });
}

export async function getTopologyViewLayout(viewId: string): Promise<{
  view: ApiTopologyView;
  layout: ApiTopologyViewLayoutPayload;
}> {
  return request(`/api/topology-views/${viewId}/layout`);
}

export async function saveTopologyViewLayout(viewId: string, payload: {
  node_layouts: ApiTopologyNodeLayout[];
  link_layouts: ApiTopologyLinkLayout[];
}): Promise<{
  view: ApiTopologyView;
  layout: ApiTopologyViewLayoutPayload;
}> {
  return request(`/api/topology-views/${viewId}/layout`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function createSector(payload: {
  project_id: string;
  name: string;
  code?: string | null;
  description?: string | null;
  location_id?: string | null;
  metadata?: Record<string, unknown>;
}): Promise<ApiSector> {
  return request<ApiSector>("/api/sectors", {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.project_id,
      name: payload.name,
      code: payload.code ?? null,
      description: payload.description ?? null,
      location_id: payload.location_id ?? null,
      metadata: payload.metadata ?? {}
    })
  });
}

export async function updateSector(id: string, payload: {
  name?: string;
  code?: string | null;
  description?: string | null;
  location_id?: string | null;
  metadata?: Record<string, unknown>;
}): Promise<ApiSector> {
  return request<ApiSector>(`/api/sectors/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteSector(id: string): Promise<ApiSector> {
  return request<ApiSector>(`/api/sectors/${id}`, {
    method: "DELETE"
  });
}

export async function createAsset(payload: {
  project_id: string;
  sector_id: string;
  parent_asset_id?: string | null;
  asset_type: ApiAsset["asset_type"];
  subtype: string;
  name: string;
  status?: ApiAsset["status"];
  code?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown>;
}): Promise<ApiAsset> {
  return request<ApiAsset>("/api/assets", {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.project_id,
      sector_id: payload.sector_id,
      location_id: null,
      parent_asset_id: payload.parent_asset_id ?? null,
      asset_type: payload.asset_type,
      subtype: payload.subtype,
      name: payload.name,
      code: payload.code ?? null,
      description: payload.description ?? null,
      status: payload.status ?? "active",
      role: null,
      serial_number: null,
      manufacturer: null,
      model: null,
      firmware_version: null,
      hardware_version: null,
      mac_address: null,
      ip_address: null,
      last_seen_at: null,
      metadata: payload.metadata ?? {}
    })
  });
}

export async function updateAsset(id: string, payload: {
  name?: string;
  subtype?: string;
  status?: ApiAsset["status"];
  parent_asset_id?: string | null;
  metadata?: Record<string, unknown>;
  code?: string | null;
  description?: string | null;
}): Promise<ApiAsset> {
  return request<ApiAsset>(`/api/assets/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteAsset(id: string): Promise<ApiAsset> {
  return request<ApiAsset>(`/api/assets/${id}`, {
    method: "DELETE"
  });
}

export async function createTopologyLink(payload: {
  project_id: string;
  source_asset_id?: string | null;
  source_sector_id?: string | null;
  target_asset_id?: string | null;
  target_sector_id?: string | null;
  relation_type: ApiTopologyLink["relation_type"];
}): Promise<ApiTopologyLink> {
  return request<ApiTopologyLink>("/api/topology-links", {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.project_id,
      source_asset_id: payload.source_asset_id ?? null,
      source_sector_id: payload.source_sector_id ?? null,
      target_asset_id: payload.target_asset_id ?? null,
      target_sector_id: payload.target_sector_id ?? null,
      relation_type: payload.relation_type,
      connection_medium: null,
      protocol: null,
      ports: [],
      link_quality: null,
      status: "active",
      metadata: {
        created_from_canvas: true
      }
    })
  });
}

export async function updateTopologyLink(id: string, payload: {
  relation_type?: ApiTopologyLink["relation_type"];
  status?: ApiTopologyLink["status"];
  metadata?: Record<string, unknown>;
}): Promise<ApiTopologyLink> {
  return request<ApiTopologyLink>(`/api/topology-links/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteTopologyLink(id: string): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/api/topology-links/${id}`, {
    method: "DELETE"
  });
}
