import type { DimensionDefinition } from "@/lib/gdss/core";
import type { QuantitySemantics, UnitIdentity } from "@/lib/gdss/expression";

export type EpistemicOrigin = "PHYSICAL_OBSERVATION" | "SYNTHETIC_OBSERVATION";
export type ObservationSourceType = "GOVERNED_FILE_ARTIFACT" | "GOVERNED_DATABASE_SNAPSHOT" | "SYNTHETIC_FIXTURE";
export type ObservationQuality = "ACCEPTED" | "SUSPECT" | "REJECTED" | "MISSING" | "DEVICE_ERROR";
export type Uncertainty = { mode:"UNKNOWN" } | { mode:"ABSOLUTE_BOUND"|"RELATIVE_BOUND"; bound:number };
export type ObservationLifecycle = "DRAFT" | "VALIDATED" | "PUBLISHED" | "DEPRECATED";

export interface ObservationSourceReference {
  sourceType:ObservationSourceType; sourceIdentity:string; artifactIdentity:string; contentSha256:string;
  channelIdentity:string; physicalSystemIdentity:string|null; instrumentIdentity?:string;
  instrumentCalibrationMetadata?:Record<string,unknown>; parserContract?:string; queryContract?:string;
  generatorIdentity?:string; generatorVersion?:string; generatorContentHash?:string; seed?:string;
}
export interface ObservationPoint {
  ordinal:number; measurementTimeUs:bigint; value:number|null; quality:ObservationQuality;
  uncertainty:Uncertainty; resolution?:number; sourceIdentity:string; sourceRecordIdentity:string; sourceRecordSha256:string;
}
export interface ObservationSeries {
  ordinal:number; seriesKey:string; quantityIdentity:string; dimension:DimensionDefinition; unit:UnitIdentity;
  quantitySemantics:QuantitySemantics; points:ObservationPoint[];
}
export interface ObservationDataset {
  projectId:string; datasetIdentityId:string; datasetVersionId:string; versionNumber:number;
  lifecycleStatus:ObservationLifecycle; epistemicOrigin:EpistemicOrigin;
  sources:ObservationSourceReference[]; series:ObservationSeries[];
}
export interface SeriesMapping {
  mappingKey:string; seriesKey:string; targetQuantityIdentity:string; sourceUnit:UnitIdentity; targetUnit:UnitIdentity;
  dimension:DimensionDefinition; quantitySemantics:QuantitySemantics; included:boolean; normalizationScale?:number; weight?:number;
}
export interface AlignmentSpecification {
  version:"EXACT_COORDINATE_MATCH_V1"; measurementTimeOriginUs:bigint; simulationT0:number;
  simulationTimeUnit:UnitIdentity; mappings:SeriesMapping[]; minimumMatchedCount:number;
  interpolation:"NONE"; resampling:"NONE"; extrapolation:"NONE";
}
export interface AlignmentPoint {
  mappingKey:string; seriesKey:string; pointOrdinal:number; disposition:"MATCHED"|"EXCLUDED";
  reason:string|null; simulationCoordinate:number|null; observedValue:number|null;
}
export interface AlignmentResult { points:AlignmentPoint[]; matchedCount:number; excludedCount:number; }
