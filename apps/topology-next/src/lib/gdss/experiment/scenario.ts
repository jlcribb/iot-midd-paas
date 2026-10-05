import { canonicalJson } from "@/lib/gdss/expression/canonical";
import { simulationInputHash } from "@/lib/gdss/simulation";
import type { ExplicitQuantityInput,SimulationInputManifest } from "@/lib/gdss/simulation";
import type { ControlledInput,ExperimentValue,OverrideTargetKind,ScenarioOverride } from "./contracts";
import { controlledInputProofHash } from "./canonical";
import { experimentFail } from "./diagnostics";

function locate(manifest:SimulationInputManifest,kind:OverrideTargetKind,identity:string):ExperimentValue{
  if(kind==="TEMPORAL_CONFIGURATION"){
    if(identity==="start"||identity==="step")return{value:manifest.temporalConfiguration[identity],unit:manifest.temporalConfiguration.timeUnit,quantitySemantics:"INTERVAL",provenanceIdentity:"base-temporal"};
    if(identity==="stepCount")return{value:manifest.temporalConfiguration.stepCount,provenanceIdentity:"base-temporal"};
    experimentFail("INVALID_DESIGN","MATERIALIZATION","Unknown temporal target",{identity});
  }
  const list=kind==="PARAMETER"?manifest.parameterValues:manifest.initialConditions,item=list.find(v=>v.ref===identity);
  if(!item)experimentFail("INVALID_DESIGN","MATERIALIZATION","Override target absent from base manifest",{kind,identity});
  const resolved=item!;
  return{value:resolved.value,unit:resolved.unit,quantitySemantics:resolved.quantitySemantics,provenanceIdentity:resolved.provenanceIdentity};
}
const same=(a:ExperimentValue,b:ExperimentValue)=>canonicalJson({value:Object.is(a.value,-0)?0:a.value,unit:a.unit??null,quantitySemantics:a.quantitySemantics??null})===canonicalJson({value:Object.is(b.value,-0)?0:b.value,unit:b.unit??null,quantitySemantics:b.quantitySemantics??null});
export function materializeManifest(base:SimulationInputManifest,overrides:ScenarioOverride[],controlled:ControlledInput[]){
  if(overrides.length>32)experimentFail("RESOURCE_LIMIT_EXCEEDED","MATERIALIZATION","Override limit exceeded");
  const manifest=structuredClone(base),changed=new Set<string>();
  for(const o of overrides){const actual=locate(base,o.targetKind,o.targetIdentity);if(!same(actual,o.expectedPreviousValue))experimentFail("EXPECTED_VALUE_MISMATCH","MATERIALIZATION","Expected previous value differs from governed base",{target:o.targetIdentity});const key=`${o.targetKind}:${o.targetIdentity}`;if(changed.has(key))experimentFail("UNDECLARED_VARIATION","MATERIALIZATION","Target changed more than once");changed.add(key);const v=Object.is(o.replacementValue.value,-0)?0:o.replacementValue.value;if(!Number.isFinite(v))experimentFail("NON_FINITE_METRIC","MATERIALIZATION","Replacement must be finite");if(o.targetKind==="TEMPORAL_CONFIGURATION"){if(o.targetIdentity==="start"||o.targetIdentity==="step")manifest.temporalConfiguration[o.targetIdentity]=v;else if(o.targetIdentity==="stepCount"&&Number.isSafeInteger(v)&&v>=0)manifest.temporalConfiguration.stepCount=v;else experimentFail("INVALID_DESIGN","MATERIALIZATION","Invalid temporal override");}else{const list=o.targetKind==="PARAMETER"?manifest.parameterValues:manifest.initialConditions,index=list.findIndex(x=>x.ref===o.targetIdentity);const old=list[index];list[index]={...old,value:v,unit:o.replacementValue.unit??old.unit,quantitySemantics:o.replacementValue.quantitySemantics??old.quantitySemantics,provenanceIdentity:o.provenanceIdentity} as ExplicitQuantityInput;}}
  const proof=controlled.map(c=>{const actual=locate(manifest,c.targetKind,c.targetIdentity);if(!same(actual,c.expectedGovernedValue))experimentFail("UNDECLARED_VARIATION","MATERIALIZATION","Controlled input changed",{target:c.targetIdentity});return{targetKind:c.targetKind,targetIdentity:c.targetIdentity,value:actual};}).sort((a,b)=>`${a.targetKind}:${a.targetIdentity}`.localeCompare(`${b.targetKind}:${b.targetIdentity}`));
  return{manifest,simulationInputHash:simulationInputHash(manifest),controlledInputProofHash:controlledInputProofHash(proof)};
}
export { locate as governedBaseValue };
