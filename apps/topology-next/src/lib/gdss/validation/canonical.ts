import { createHash } from "node:crypto";
import { stableValue } from "@/lib/gdss/expression/canonical";
import { validationProtocolContentSchema,validityDomainContentSchema,type ValidationProtocolContent,type ValidityDomainContent } from "./contracts";

function normalize(value:unknown):unknown{
  if(Array.isArray(value))return value.map(normalize);
  if(value&&typeof value==="object")return Object.fromEntries(Object.entries(value).sort(([a],[b])=>a.localeCompare(b)).map(([key,item])=>[key,normalize(item)]));
  return stableValue(value);
}
export const canonicalValidationJson=(value:unknown)=>JSON.stringify(normalize(value));
export function validationHash(domain:string,value:unknown){return createHash("sha256").update(domain,"utf8").update(Buffer.from([0])).update(canonicalValidationJson(value),"utf8").digest("hex");}
export function canonicalProtocolContent(input:unknown):ValidationProtocolContent{
  const value=validationProtocolContentSchema.parse(input);
  return {...value,targets:[...value.targets].sort((a,b)=>a.targetKey.localeCompare(b.targetKey)),horizons:[...value.horizons].sort((a,b)=>a.horizonKey.localeCompare(b.horizonKey)),acceptanceCriteria:[...value.acceptanceCriteria].sort((a,b)=>a.criterionKey.localeCompare(b.criterionKey)),exclusionPolicy:{...value.exclusionPolicy,rules:[...value.exclusionPolicy.rules].sort((a,b)=>a.ruleKey.localeCompare(b.ruleKey))},revalidationTriggers:[...value.revalidationTriggers].sort()};
}
export function canonicalDomainContent(input:unknown):ValidityDomainContent{
  const value=validityDomainContentSchema.parse(input);
  return {...value,predicates:[...value.predicates].map(predicate=>"allowedValues" in predicate?{...predicate,allowedValues:[...predicate.allowedValues].sort()}:predicate).sort((a,b)=>a.predicateKey.localeCompare(b.predicateKey)),boundaries:[...value.boundaries].map(boundary=>({...boundary,predicateKeys:[...boundary.predicateKeys].sort()})).sort((a,b)=>a.boundaryKey.localeCompare(b.boundaryKey))};
}
export const protocolContentHash=(input:unknown)=>validationHash("gdss006:validation-protocol:v1",canonicalProtocolContent(input));
export const validityDomainContentHash=(input:unknown)=>validationHash("gdss006:validity-domain:v1",canonicalDomainContent(input));
