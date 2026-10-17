import{datasetSnapshotContentSchema,evidenceUnitContentSchema,governedHoldoutContentSchema,partitionPlanContentSchema,type DatasetSnapshotContent,type EvidenceUnitContent,type GovernedHoldoutContent,type PartitionPlanContent}from"./partition-contracts";import{validationHash,canonicalValidationJson}from"./canonical";
export function canonicalEvidenceUnit(input:unknown):EvidenceUnitContent{return evidenceUnitContentSchema.parse(input);}
export function canonicalDatasetSnapshot(input:unknown):DatasetSnapshotContent{const v=datasetSnapshotContentSchema.parse(input);return{...v,includedEvidenceUnitIds:[...new Set(v.includedEvidenceUnitIds)].sort(),exclusions:[...v.exclusions].sort()};}
export function canonicalPartitionPlan(input:unknown):PartitionPlanContent{const v=partitionPlanContentSchema.parse(input);return{...v,duplicateStrategies:[...new Set(v.duplicateStrategies)].sort()as PartitionPlanContent["duplicateStrategies"],exclusions:[...v.exclusions].sort(),lineageReferences:[...v.lineageReferences].sort((a,b)=>a.childEvidenceUnitId.localeCompare(b.childEvidenceUnitId)||a.parentEvidenceUnitId.localeCompare(b.parentEvidenceUnitId)||a.relationType.localeCompare(b.relationType)),assignments:[...v.assignments].sort((a,b)=>a.evidenceUnitId.localeCompare(b.evidenceUnitId)||a.role.localeCompare(b.role))};}
export function canonicalGovernedHoldout(input:unknown):GovernedHoldoutContent{return governedHoldoutContentSchema.parse(input);}
export const evidenceUnitHash=(v:unknown)=>validationHash("gdss006:evidence-unit:v1",canonicalEvidenceUnit(v));
export const partitionPlanHash=(v:unknown)=>validationHash("gdss006:partition-plan:v1",canonicalPartitionPlan(v));
export const datasetSnapshotHash=(v:unknown)=>validationHash("gdss006:dataset-snapshot:v1",canonicalDatasetSnapshot(v));
export const governedHoldoutHash=(v:unknown)=>validationHash("gdss006:holdout:v1",canonicalGovernedHoldout(v));
export const holdoutAccessHash=(v:unknown)=>validationHash("gdss006:holdout-access:v1",v);
export{canonicalValidationJson};
