import type { Residual } from "./contracts";
import { canonicalObservationJson } from "@/lib/gdss/observation";
export function makeResidual(input:Omit<Residual,"residual"|"contribution">):Residual{const residual=input.observed-input.simulated;return{...input,residual:Object.is(residual,-0)?0:residual,contribution:residual*residual};}
export function encodeResidualArtifact(input:readonly Residual[]):Uint8Array{
  const residuals=[...input].sort((a,b)=>a.mappingKey.localeCompare(b.mappingKey)||a.pointOrdinal-b.pointOrdinal),trajectoryHashes=[...new Set(residuals.map(value=>value.trajectoryHash))];if(!residuals.length||trajectoryHashes.length!==1)throw Error("ARTIFACT_RECONCILIATION_FAILURE");
  const groups=new Map<string,Residual[]>();for(const residual of residuals){const group=groups.get(residual.mappingKey)??[];if(group.length!==residual.pointOrdinal)throw Error("ARTIFACT_RECONCILIATION_FAILURE");group.push(residual);groups.set(residual.mappingKey,group);}
  const tupleFields=["pointOrdinal","coordinate","observed","simulated","residual","contribution"] as const,lines=[canonicalObservationJson({format:"GDSS_CALIBRATION_RESIDUALS_NDJSON_V1",pointCount:residuals.length,seriesCount:groups.size,trajectoryHash:trajectoryHashes[0],tupleFields})];
  for(const [mappingKey,group] of [...groups].sort(([a],[b])=>a.localeCompare(b)))lines.push(canonicalObservationJson({kind:"series",mappingKey,points:group.map(value=>[value.pointOrdinal,value.coordinate,value.observed,value.simulated,value.residual,value.contribution])}));
  lines.push(canonicalObservationJson({kind:"summary",pointCount:residuals.length,seriesCount:groups.size}));return new TextEncoder().encode(lines.join("\n")+"\n");
}
