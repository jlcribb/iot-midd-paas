import type { Asset, AssetTreeNode } from "@/lib/dto/asset.dto";
import type {
  ControlAuditView,
  ControlRecommendationView,
  ControlStatusView
} from "@/lib/dto/control.dto";
import type { ControlPolicy } from "@/lib/dto/control-policy.dto";
import type { Location } from "@/lib/dto/location.dto";
import type { Project } from "@/lib/dto/project.dto";
import type { Sector } from "@/lib/dto/sector.dto";
import type { TopologyLink } from "@/lib/dto/topology.dto";
import type {
  CreateAssetInput,
  UpdateAssetInput
} from "@/lib/validators/asset.schemas";
import type {
  CreateControlPolicyInput,
  UpdateControlPolicyInput
} from "@/lib/validators/control-policy.schemas";
import type {
  CreateLocationInput,
  UpdateLocationInput
} from "@/lib/validators/location.schemas";
import type {
  CreateProjectInput,
  UpdateProjectInput
} from "@/lib/validators/project.schemas";
import type {
  CreateSectorInput,
  UpdateSectorInput
} from "@/lib/validators/sector.schemas";
import type {
  CreateTopologyLinkInput,
  UpdateTopologyLinkInput
} from "@/lib/validators/topology.schemas";

export interface IProjectRepository {
  create(input: CreateProjectInput): Promise<Project>;
  findById(id: string): Promise<Project | null>;
  findAll(filters?: { status?: Project["status"] }): Promise<Project[]>;
  update(id: string, input: UpdateProjectInput): Promise<Project | null>;
}

export interface ILocationRepository {
  create(input: CreateLocationInput): Promise<Location>;
  findById(id: string): Promise<Location | null>;
  findAll(): Promise<Location[]>;
  update(id: string, input: UpdateLocationInput): Promise<Location | null>;
}

export interface ISectorRepository {
  create(input: CreateSectorInput): Promise<Sector>;
  findById(id: string): Promise<Sector | null>;
  findByProjectId(projectId: string): Promise<Sector[]>;
  update(id: string, input: UpdateSectorInput): Promise<Sector | null>;
  existsNameInProject(projectId: string, name: string, excludeId?: string): Promise<boolean>;
  existsCodeInProject(projectId: string, code: string, excludeId?: string): Promise<boolean>;
  softDeactivate(id: string): Promise<Sector | null>;
  softDeactivateByProject(projectId: string): Promise<void>;
}

export interface IAssetRepository {
  create(input: CreateAssetInput): Promise<Asset>;
  findById(id: string): Promise<Asset | null>;
  findByProjectId(projectId: string): Promise<Asset[]>;
  findBySectorId(sectorId: string): Promise<Asset[]>;
  findChildren(parentAssetId: string): Promise<Asset[]>;
  findTree(rootAssetId: string): Promise<AssetTreeNode[]>;
  findNodeDevices(nodeAssetId: string): Promise<Asset[]>;
  findOfflineAssets(projectId: string, offlineMinutes: number): Promise<Asset[]>;
  update(id: string, input: UpdateAssetInput): Promise<Asset | null>;
  deleteSafe(id: string): Promise<Asset | null>;
  existsProjectCode(projectId: string, code: string, excludeId?: string): Promise<boolean>;
  existsSerialNumber(serialNumber: string, excludeId?: string): Promise<boolean>;
  existsNormalizedMac(macAddress: string, excludeId?: string): Promise<boolean>;
  softDeactivateByProject(projectId: string): Promise<void>;
}

export interface ITopologyRepository {
  create(input: CreateTopologyLinkInput): Promise<TopologyLink>;
  findById(id: string): Promise<TopologyLink | null>;
  findByProjectId(projectId: string): Promise<TopologyLink[]>;
  findByAssetId(assetId: string): Promise<TopologyLink[]>;
  update(id: string, input: UpdateTopologyLinkInput): Promise<TopologyLink | null>;
  delete(id: string): Promise<boolean>;
  existsExactRelation(
    projectId: string,
    relationType: string,
    sourceAssetId: string | null,
    sourceSectorId: string | null,
    targetAssetId: string | null,
    targetSectorId: string | null,
    excludeId?: string
  ): Promise<boolean>;
  deactivateByProject(projectId: string): Promise<void>;
  deactivateBySectorAndAssets(sectorId: string, assetIds: string[]): Promise<void>;
  deactivateByAssetIds(assetIds: string[]): Promise<void>;
}

export interface IControlObservabilityRepository {
  findLatestRecommendations(filters?: {
    projectId?: string;
    projectIds?: string[];
    limit?: number;
  }): Promise<ControlRecommendationView[]>;
  findAuditEntries(filters?: {
    projectId?: string;
    projectIds?: string[];
    status?: "processed" | "skipped" | "error";
    limit?: number;
  }): Promise<ControlAuditView[]>;
  getStatus(filters?: { projectIds?: string[] }): Promise<ControlStatusView>;
}

export interface IControlPolicyRepository {
  create(input: CreateControlPolicyInput): Promise<ControlPolicy>;
  findById(id: string): Promise<ControlPolicy | null>;
  findAll(filters?: {
    projectId?: string;
    projectIds?: string[];
    variable?: string;
    enabled?: boolean;
  }): Promise<ControlPolicy[]>;
  update(id: string, input: UpdateControlPolicyInput & { version?: number }): Promise<ControlPolicy | null>;
}

export interface IControlPolicyAuditRepository {
  recordChange(entry: {
    entityId: string;
    action: "CONTROL_POLICY_CREATED" | "CONTROL_POLICY_UPDATED" | "CONTROL_POLICY_DISABLED" | "CONTROL_POLICY_ACTUATION_BINDING_CREATED" | "CONTROL_POLICY_ACTUATION_BINDING_UPDATED" | "CONTROL_POLICY_ACTUATION_BINDING_REMOVED";
    before: unknown;
    after: unknown;
    context?: Record<string, unknown>;
  }): Promise<void>;
}
