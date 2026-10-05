import type { ExperimentDesign,MetricDefinition } from "@/lib/gdss/experiment";
import { GDSS_EXPERIMENT_LIMITS_V1 } from "@/lib/gdss/experiment";
import { reservoirFixture } from "./gdss-simulation";

const volume:[number,number,number,number,number,number,number]=[3,0,0,0,0,0,0];
const flow:[number,number,number,number,number,number,number]=[3,0,-1,0,0,0,0];
const metric=(key:string,operation:MetricDefinition["operation"],stateSymbol="volume"):MetricDefinition=>({key,operation,stateSymbol,expectedUnit:{key:"cubic_meter",revision:1},expectedDimension:volume,requiredCompleteness:"COMPLETE"});
export function reservoirExperimentFixture(stepCount=10):{design:ExperimentDesign;binding:ReturnType<typeof reservoirFixture>["binding"]}{
  const fixture=reservoirFixture(1,stepCount);fixture.manifest.parameterValues.find(v=>v.ref==="qin")!.value=10;
  const values=[8,10,12,14].map(value=>({value,unit:{key:"cubic_meter_per_second",revision:1},quantitySemantics:"INTERVAL" as const,provenanceIdentity:`declared:qin:${value}`}));
  const metrics=[metric("final","FINAL_VALUE"),metric("integral","LEFT_RECTANGLE_INTEGRAL")];
  const comparisons=[8,12,14].flatMap((_,i)=>["ABSOLUTE_DIFFERENCE","PERCENT_DIFFERENCE","ORDERING"].map((operation,j)=>({key:`baseline-${i}-${j}`,operation:operation as "ABSOLUTE_DIFFERENCE"|"PERCENT_DIFFERENCE"|"ORDERING",metricKey:"final",referenceScenarioOrdinal:1,targetScenarioOrdinal:i+(i===0?0:1),requiredScenarioOrdinals:[1,i+(i===0?0:1)]})));
  const design:ExperimentDesign={projectId:fixture.manifest.projectId,experimentVersionId:"00000000-0000-4000-8000-000000000042",lifecycleStatus:"PUBLISHED",researchQuestion:"How does declared inflow change simulated reservoir volume?",hypothesis:"Larger inflow produces larger final simulated volume",baseManifest:fixture.manifest,factors:[{factorKey:"qin",targetKind:"PARAMETER",targetIdentity:"qin",values}],controlledInputs:[{targetKind:"PARAMETER",targetIdentity:"qout",expectedGovernedValue:{value:1,unit:{key:"cubic_meter_per_second",revision:1},provenanceIdentity:"parameter:qout"}},{targetKind:"INITIAL_CONDITION",targetIdentity:"volume",expectedGovernedValue:{value:10,unit:{key:"cubic_meter",revision:1},provenanceIdentity:"initial:test"}}],metrics,comparisons,completenessPolicy:"ALL_REQUIRED_SCENARIOS",baselineAssignments:{qin:10},resourceProfile:GDSS_EXPERIMENT_LIMITS_V1};
  void flow;return{design,binding:fixture.binding};
}
