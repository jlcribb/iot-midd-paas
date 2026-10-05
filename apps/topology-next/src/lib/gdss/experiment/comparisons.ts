import type { ComparisonDefinition,ComparisonResult,MetricDefinition,MetricResult } from "./contracts";
import type { SimulationInputManifest } from "@/lib/gdss/simulation";
import { assertConvertible,catalogUnit,fromCanonical,toCanonical,UNIT_CONVERSION_CATALOG_VERSION_V2 } from "@/lib/gdss/expression";
import { finite } from "./diagnostics";
import { temporalCompatibility } from "./temporal-comparability";
export function evaluateComparison(def:ComparisonDefinition,metric:MetricDefinition,reference:MetricResult,target:MetricResult,referenceManifest:SimulationInputManifest,targetManifest:SimulationInputManifest):ComparisonResult{
  const temporal=temporalCompatibility(metric,referenceManifest,targetManifest);if(!temporal.ok)return{comparisonKey:def.key,status:"INELIGIBLE",diagnosticCode:temporal.diagnosticCode,operationCount:0};
  if(reference.status!=="SUCCEEDED"||target.status!=="SUCCEEDED"||reference.value===undefined||target.value===undefined)return{comparisonKey:def.key,status:"INELIGIBLE",diagnosticCode:"INELIGIBLE_MISSING_REQUIRED_SCENARIO",operationCount:0};
  let r=Object.is(reference.value,-0)?0:reference.value,t=Object.is(target.value,-0)?0:target.value;
  if(JSON.stringify(reference.dimension)!==JSON.stringify(target.dimension)||Boolean(reference.unit)!==Boolean(target.unit))return{comparisonKey:def.key,status:"INELIGIBLE",diagnosticCode:"INELIGIBLE_UNIT_SEMANTICS",operationCount:0};
  if(reference.unit&&target.unit&&(reference.unit.key!==target.unit.key||reference.unit.revision!==target.unit.revision)){try{const source=catalogUnit(target.unit,undefined,UNIT_CONVERSION_CATALOG_VERSION_V2),destination=catalogUnit(reference.unit,undefined,UNIT_CONVERSION_CATALOG_VERSION_V2);assertConvertible(source,destination);t=fromCanonical(toCanonical(t,source,target.quantitySemantics??"INTERVAL"),destination,reference.quantitySemantics??"INTERVAL");}catch{return{comparisonKey:def.key,status:"INELIGIBLE",diagnosticCode:"INELIGIBLE_UNIT_SEMANTICS",operationCount:0};}}
  if(def.operation==="ORDERING")return{comparisonKey:def.key,status:"SUCCEEDED",ordering:t<r?"TARGET_LESS_THAN_REFERENCE":t>r?"TARGET_GREATER_THAN_REFERENCE":"TARGET_EQUAL_TO_REFERENCE",operationCount:1};
  if(def.operation==="ABSOLUTE_DIFFERENCE")return{comparisonKey:def.key,status:"SUCCEEDED",value:finite(t-r,"COMPARISON","NON_FINITE_COMPARISON"),unit:target.unit,dimension:target.dimension,operationCount:1};
  if(r===0)return{comparisonKey:def.key,status:"INELIGIBLE",diagnosticCode:"INELIGIBLE_REFERENCE_ZERO",operationCount:0};const relative=finite((t-r)/r,"COMPARISON","NON_FINITE_COMPARISON");return{comparisonKey:def.key,status:"SUCCEEDED",value:def.operation==="PERCENT_DIFFERENCE"?finite(relative*100,"COMPARISON","NON_FINITE_COMPARISON"):relative,operationCount:def.operation==="PERCENT_DIFFERENCE"?3:2};
}
