import { createHash } from "node:crypto";
import { stableValue } from "@/lib/gdss/expression/canonical";
import type { ObservationDataset } from "./contracts";
function normalize(value:unknown):unknown {
  if(typeof value==="bigint") return {$int64:value.toString(10)};
  if(Array.isArray(value)) return value.map(normalize);
  if(value&&typeof value==="object") return Object.fromEntries(Object.entries(value).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,normalize(v)]));
  return stableValue(value);
}
export const canonicalObservationJson=(value:unknown)=>JSON.stringify(normalize(value));
export function governedHash(domain:string,value:unknown){return createHash("sha256").update(domain,"utf8").update(Buffer.from([0])).update(canonicalObservationJson(value),"utf8").digest("hex");}
export function observationDatasetHash(dataset:ObservationDataset){
  const semantic={...dataset,lifecycleStatus:undefined,sources:[...dataset.sources],series:[...dataset.series].sort((a,b)=>a.ordinal-b.ordinal).map(s=>({...s,points:[...s.points].sort((a,b)=>a.ordinal-b.ordinal)}))};
  return governedHash("midd:gdss:observation-dataset:v1",semantic);
}
export function observationDatasetNdjson(dataset:ObservationDataset){
  const records:unknown[]=[{kind:"header",datasetIdentityId:dataset.datasetIdentityId,datasetVersionId:dataset.datasetVersionId,epistemicOrigin:dataset.epistemicOrigin}];
  dataset.sources.forEach((source,ordinal)=>records.push({kind:"source",ordinal,...source}));
  [...dataset.series].sort((a,b)=>a.ordinal-b.ordinal).forEach(series=>{records.push({kind:"series",...series,points:undefined});[...series.points].sort((a,b)=>a.ordinal-b.ordinal).forEach(point=>records.push({kind:"point",seriesOrdinal:series.ordinal,...point}));});
  return new TextEncoder().encode(records.map(canonicalObservationJson).join("\n")+"\n");
}
