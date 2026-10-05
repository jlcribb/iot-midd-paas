import { canonicalJson } from "@/lib/gdss/expression/canonical";
import { GDSS_EXPERIMENT_LIMITS_V1 } from "./limits";
import type { ExperimentDesign } from "./contracts";
import { experimentFail } from "./diagnostics";
import { EXPERIMENT_SEMANTIC_VERSION,EXPANSION_VERSION,METRICS_VERSION,COMPARISONS_VERSION,NUMERIC_VERSION,TEMPORAL_COMPARABILITY_VERSION } from "./versions";

const id=/^[A-Za-z][A-Za-z0-9_.:-]{0,255}$/;
export function validateExperimentDesign(d:ExperimentDesign){
  if(d.lifecycleStatus!=="PUBLISHED")experimentFail("INVALID_DESIGN","DESIGN","Only PUBLISHED ExperimentVersion is executable");
  if(!d.researchQuestion.trim())experimentFail("INVALID_DESIGN","DESIGN","Research question is required");
  if(d.resourceProfile.profileVersion!==GDSS_EXPERIMENT_LIMITS_V1.profileVersion)experimentFail("VERSION_MISMATCH","DESIGN","Unsupported experiment limit profile");
  const checks:[[number,number,string],[number,number,string],[number,number,string],[number,number,string]]=[
    [d.factors.length,GDSS_EXPERIMENT_LIMITS_V1.factors,"factors"],[d.controlledInputs.length,GDSS_EXPERIMENT_LIMITS_V1.controlledInputs,"controlled inputs"],[d.metrics.length,GDSS_EXPERIMENT_LIMITS_V1.metricDefinitions,"metrics"],[d.comparisons.length,GDSS_EXPERIMENT_LIMITS_V1.comparisonDefinitions,"comparisons"]];
  for(const [actual,limit,name] of checks)if(actual>limit)experimentFail("RESOURCE_LIMIT_EXCEEDED","DESIGN",`${name} exceed limits`,{actual,limit});
  if(canonicalJson(d).length>GDSS_EXPERIMENT_LIMITS_V1.canonicalDesignBytes)experimentFail("RESOURCE_LIMIT_EXCEEDED","DESIGN","Canonical design exceeds byte limit");
  const targets=new Set<string>(),factorKeys=new Set<string>();
  for(const f of d.factors){if(!id.test(f.factorKey)||!id.test(f.targetIdentity))experimentFail("INVALID_DESIGN","DESIGN","Invalid factor identity");const target=`${f.targetKind}:${f.targetIdentity}`;if(targets.has(target))experimentFail("DUPLICATE_FACTOR_TARGET","DESIGN","Factor target must be unique");targets.add(target);if(factorKeys.has(f.factorKey))experimentFail("INVALID_DESIGN","DESIGN","Factor key must be unique");factorKeys.add(f.factorKey);if(!f.values.length||f.values.length>GDSS_EXPERIMENT_LIMITS_V1.valuesPerFactor)experimentFail("RESOURCE_LIMIT_EXCEEDED","DESIGN","Factor domain size invalid");const values=new Set(f.values.map(v=>canonicalJson({value:Object.is(v.value,-0)?0:v.value,unit:v.unit,quantitySemantics:v.quantitySemantics})));if(values.size!==f.values.length)experimentFail("DUPLICATE_FACTOR_VALUE","DESIGN","Duplicate normalized factor value");if(f.values.some(v=>!Number.isFinite(v.value)))experimentFail("NON_FINITE_METRIC","DESIGN","Factor values must be finite");}
  for(const c of d.controlledInputs){const target=`${c.targetKind}:${c.targetIdentity}`;if(targets.has(target))experimentFail("INVALID_DESIGN","DESIGN","Controlled input cannot also be a factor");if(!id.test(c.targetIdentity)||!Number.isFinite(c.expectedGovernedValue.value))experimentFail("INVALID_DESIGN","DESIGN","Invalid controlled input");targets.add(target);}
  if(new Set(d.metrics.map(v=>v.key)).size!==d.metrics.length||new Set(d.comparisons.map(v=>v.key)).size!==d.comparisons.length)experimentFail("INVALID_DESIGN","DESIGN","Metric/comparison keys must be unique");
  for(const m of d.metrics)if(m.operation==="TIME_TO_THRESHOLD"&&!m.threshold)experimentFail("INVALID_DESIGN","DESIGN","Threshold metric requires threshold");
  for(const c of d.comparisons)if(!d.metrics.some(m=>m.key===c.metricKey))experimentFail("INVALID_DESIGN","DESIGN","Comparison metric is absent");
  return Object.freeze({design:d,versions:{experiment:EXPERIMENT_SEMANTIC_VERSION,expansion:EXPANSION_VERSION,metrics:METRICS_VERSION,comparisons:COMPARISONS_VERSION,numeric:NUMERIC_VERSION,temporal:TEMPORAL_COMPARABILITY_VERSION}});
}
