import{EvidenceCustodyError}from"./partition-diagnostics";import type{EvidenceLineage,EvidenceUnitContent,PartitionAssignment,PartitionPlanContent}from"./partition-contracts";
/** Edge depth: root/current unit is 0; the sixteenth lineage edge is 16. */
export const LINEAGE_DEPTH_LIMIT=16;
export type EvidenceUnitRecord={id:string;content:EvidenceUnitContent};
const guardedRoles=new Set(["VALIDATION","HOLDOUT","EXTERNAL_VALIDATION","CHALLENGE"]);
export function assertAcyclicLineage(edges:EvidenceLineage[]){
 const derivationParents=new Map<string,string[]>(),allParents=new Map<string,string[]>();
 for(const e of edges){
  allParents.set(e.childEvidenceUnitId,[...(allParents.get(e.childEvidenceUnitId)??[]),e.parentEvidenceUnitId]);
  if(e.relationType!=="GROUPED_WITH"&&e.relationType!=="TEMPORALLY_DEPENDENT_ON")derivationParents.set(e.childEvidenceUnitId,[...(derivationParents.get(e.childEvidenceUnitId)??[]),e.parentEvidenceUnitId]);
 }
 const visiting=new Set<string>(),done=new Set<string>();
 const visit=(id:string)=>{if(visiting.has(id))throw new EvidenceCustodyError("EVIDENCE_LINEAGE_CYCLE");if(done.has(id))return;visiting.add(id);for(const parent of derivationParents.get(id)??[])visit(parent);visiting.delete(id);done.add(id);};
 for(const id of derivationParents.keys())visit(id);
 for(const id of allParents.keys()){
  const stack=(allParents.get(id)??[]).map(parent=>({id:parent,depth:1,path:new Set([id])}));
  while(stack.length){const current=stack.pop()!;if(current.depth>LINEAGE_DEPTH_LIMIT)throw new EvidenceCustodyError("LINEAGE_DEPTH_LIMIT_EXCEEDED");if(current.path.has(current.id))continue;const path=new Set(current.path).add(current.id);for(const parent of allParents.get(current.id)??[])stack.push({id:parent,depth:current.depth+1,path});}
 }
}
export function assertPartitionIndependent(plan:PartitionPlanContent,units:EvidenceUnitRecord[],edges:EvidenceLineage[]){assertAcyclicLineage(edges);const byId=new Map(units.map(u=>[u.id,u.content])),assignment=new Map<string,PartitionAssignment>();for(const a of plan.assignments){if(assignment.has(a.evidenceUnitId))throw new EvidenceCustodyError("EVIDENCE_PARTITION_OVERLAP");if(!byId.has(a.evidenceUnitId))throw new EvidenceCustodyError("INDEPENDENCE_UNKNOWN");assignment.set(a.evidenceUnitId,a);}const calibration=new Set([...assignment].filter(([,a])=>a.role==="CALIBRATION").map(([id])=>id)),guarded=new Set([...assignment].filter(([,a])=>guardedRoles.has(a.role)).map(([id])=>id));
 const groupRoles=new Map<string,Set<string>>();if(plan.dependentGroups)for(const a of plan.assignments)if(a.groupKey){const roles=groupRoles.get(a.groupKey)??new Set<string>();roles.add(a.role);groupRoles.set(a.groupKey,roles);}for(const roles of groupRoles.values())if(roles.has("CALIBRATION")&&[...roles].some(r=>guardedRoles.has(r)))throw new EvidenceCustodyError("DEPENDENT_GROUP_SPLIT");
 for(const strategy of plan.duplicateStrategies){const seen=new Map<string,string>();for(const a of plan.assignments){const u=byId.get(a.evidenceUnitId)!;const identity=strategy==="EXACT_CONTENT_HASH"?u.contentHash:strategy==="SOURCE_IDENTITY_DUPLICATE"?`${u.sourceIdentity}:${u.sourceVersion}`:u.semanticGroup;if(!identity)continue;const prior=seen.get(identity);if(prior&&((prior==="CALIBRATION"&&guardedRoles.has(a.role))||(a.role==="CALIBRATION"&&guardedRoles.has(prior))))throw new EvidenceCustodyError("DUPLICATE_EVIDENCE_DETECTED");seen.set(identity,a.role);}}
 if(plan.temporalCutoff)for(const id of assignment.keys()){const u=byId.get(id)!;if(!u.availabilityTime)throw new EvidenceCustodyError("INDEPENDENCE_UNKNOWN");if(u.availabilityTime>plan.temporalCutoff)throw new EvidenceCustodyError("TEMPORAL_LEAKAGE_DETECTED");}
 const parents=new Map<string,string[]>();for(const e of edges)parents.set(e.childEvidenceUnitId,[...(parents.get(e.childEvidenceUnitId)??[]),e.parentEvidenceUnitId]);for(const id of guarded){const stack=(parents.get(id)??[]).map(x=>({id:x,d:1})),seen=new Set<string>();while(stack.length){const n=stack.pop()!;if(n.d>LINEAGE_DEPTH_LIMIT)throw new EvidenceCustodyError("LINEAGE_DEPTH_LIMIT_EXCEEDED");if(seen.has(n.id))continue;seen.add(n.id);if(calibration.has(n.id))throw new EvidenceCustodyError("TRANSITIVE_LINEAGE_OVERLAP");for(const p of parents.get(n.id)??[])stack.push({id:p,d:n.d+1});}}
}
