import type { ComparisonDefinition,ComparisonResult,ExperimentManifest,ExperimentResult,GovernedTrajectory,MetricResult,ScenarioOutcome } from "./contracts";
import { evaluateMetric } from "./metrics";
import { evaluateComparison } from "./comparisons";
import { GDSS_EXPERIMENT_LIMITS_V1 } from "./limits";
import { experimentFail } from "./diagnostics";

export interface ScenarioEvidence { outcome:ScenarioOutcome; trajectory?:GovernedTrajectory }

export function constructExperimentResult(manifestHash:string,manifest:ExperimentManifest,evidence:readonly ScenarioEvidence[],aborted=false):ExperimentResult{
  const ordered=[...evidence].sort((a,b)=>a.outcome.ordinal-b.outcome.ordinal);
  if(ordered.length!==manifest.scenarios.length||ordered.some((v,i)=>v.outcome.ordinal!==i))experimentFail("IDENTITY_MISMATCH","TERMINALIZATION","Scenario evidence must exactly cover the manifest universe");
  let pointCount=0,byteCount=0,metricOps=0,comparisonOps=0;
  const metrics:MetricResult[]=[];
  for(const item of ordered){
    if(!item.trajectory)for(const def of manifest.metrics)metrics.push({metricKey:def.key,scenarioOrdinal:item.outcome.ordinal,status:"INELIGIBLE",diagnosticCode:"INELIGIBLE_MISSING_REQUIRED_SCENARIO",operationCount:0});
    else {pointCount+=item.trajectory.evidence.pointCount;byteCount+=item.trajectory.evidence.byteLength;for(const def of manifest.metrics){const value=evaluateMetric(item.trajectory,def,item.outcome.ordinal,GDSS_EXPERIMENT_LIMITS_V1.metricOperations-metricOps);metricOps+=value.operationCount;metrics.push(value);}}
    if(pointCount>GDSS_EXPERIMENT_LIMITS_V1.totalReferencedTrajectoryPoints||byteCount>GDSS_EXPERIMENT_LIMITS_V1.aggregateReferencedTrajectoryBytes||metricOps>GDSS_EXPERIMENT_LIMITS_V1.metricOperations)experimentFail("RESOURCE_LIMIT_EXCEEDED","TERMINALIZATION","Aggregate trajectory or metric budget exceeded");
  }
  const comparisons:ComparisonResult[]=[];
  for(const def of manifest.comparisons){const metric=manifest.metrics.find(v=>v.key===def.metricKey);if(!metric)experimentFail("IDENTITY_MISMATCH","COMPARISON","Comparison metric definition is absent");const resolvedMetric=metric!;const reference=metrics.find(v=>v.metricKey===def.metricKey&&v.scenarioOrdinal===def.referenceScenarioOrdinal),target=metrics.find(v=>v.metricKey===def.metricKey&&v.scenarioOrdinal===def.targetScenarioOrdinal);const referenceManifest=manifest.scenarios[def.referenceScenarioOrdinal]?.manifest,targetManifest=manifest.scenarios[def.targetScenarioOrdinal]?.manifest;let value:ComparisonResult;if(!reference||!target||!referenceManifest||!targetManifest)value={comparisonKey:def.key,status:"INELIGIBLE",diagnosticCode:"INELIGIBLE_MISSING_REQUIRED_SCENARIO",operationCount:0};else value=evaluateComparison(def,resolvedMetric,reference,target,referenceManifest,targetManifest);comparisonOps+=value.operationCount;if(comparisonOps>GDSS_EXPERIMENT_LIMITS_V1.comparisonOperations)experimentFail("RESOURCE_LIMIT_EXCEEDED","COMPARISON","Comparison operation budget exceeded");comparisons.push(value);}
  const failures=ordered.filter(v=>v.outcome.terminalClassification!=="SUCCESS");const comparisonFailure=comparisons.some(v=>v.status!=="SUCCEEDED"),metricFailure=metrics.some(v=>v.status==="FAILED");
  const status=aborted?"ABORTED":failures.length===0&&!metricFailure&&!comparisonFailure?"COMPLETED":manifest.completenessPolicy==="ALLOW_PARTIAL_EXPLICIT"&&ordered.some(v=>v.outcome.terminalClassification==="SUCCESS")&&!metricFailure?"COMPLETED_WITH_FAILURES":"FAILED";
  const completeness=status==="COMPLETED"?"COMPLETE":status==="ABORTED"?"ABORTED":"PARTIAL";
  const diagnostics:Array<{code:string;stage:string;details:Record<string,unknown>}>=[];
  if(failures.length)diagnostics.push({code:aborted?"ABORT_REQUESTED":"INELIGIBLE_MISSING_REQUIRED_SCENARIO",stage:aborted?"ABORT":"TERMINALIZATION",details:{ordinals:failures.map(v=>v.outcome.ordinal)}});
  return{manifestHash,status,completeness,scenarios:ordered.map(v=>v.outcome),metrics,comparisons,findings:comparisons.filter(v=>v.status==="SUCCEEDED").map(v=>({kind:"SIMULATION_COMPARISON",...v})),diagnostics,provenance:"SIMULATION_DERIVED",physicalAuthority:"NONE"};
}

export const requiredScenarioOrdinals=(definitions:readonly ComparisonDefinition[])=>[...new Set(definitions.flatMap(v=>[v.referenceScenarioOrdinal,v.targetScenarioOrdinal,...v.requiredScenarioOrdinals]))].sort((a,b)=>a-b);
