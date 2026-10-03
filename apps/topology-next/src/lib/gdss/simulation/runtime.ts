import type { SimulationDiagnostic } from "./diagnostics";
import { SimulationFault, simulationFail } from "./diagnostics";
import type { SimulationPoint, SimulationProgram, SimulationResult, SimulationTrajectory, TerminationReason } from "./contracts";
import { simulationInputHash, simulationResultHash, trajectoryHash } from "./canonical";
import { GDSS_SIM_LIMITS_V1 } from "./limits";
import { explicitEulerTransition } from "./solver";
import { encodeTrajectory } from "./trajectory";
import { PHYSICAL_AUTHORITY, SIMULATION_EPISTEMIC_KIND } from "./versions";
import { validateTemporalConfiguration } from "./temporal";

const reasonFor=(code:string):TerminationReason=>({NON_FINITE_STATE:"NON_FINITE_STATE",NON_FINITE_RATE:"NON_FINITE_RATE",EXPRESSION_FAILURE:"EXPRESSION_FAILURE",DIMENSION_FAILURE:"DIMENSION_FAILURE",CONSTRAINT_VIOLATION:"CONSTRAINT_VIOLATION",RESOURCE_LIMIT_EXCEEDED:"RESOURCE_LIMIT_EXCEEDED",INSTANTANEOUS_ALGEBRAIC_LOOP_UNSUPPORTED:"INSTANTANEOUS_ALGEBRAIC_LOOP_UNSUPPORTED",SOLVER_FAILURE:"SOLVER_FAILURE"}[code] as TerminationReason ?? "INVALID_CONFIGURATION");

function point(program:SimulationProgram,index:number,snapshot:Readonly<Record<string,number>>):SimulationPoint {
  const states:SimulationPoint["states"]={};
  for(const binding of [...program.binding.states].sort((a,b)=>a.stateRef.localeCompare(b.stateRef))) states[binding.stateRef]={value:snapshot[binding.stateRef],unit:binding.unit,dimension:binding.dimension};
  return {stepIndex:index,epistemicKind:SIMULATION_EPISTEMIC_KIND,states};
}
function finish(inputHash:string,status:SimulationResult["status"],reason:TerminationReason,trajectory:SimulationTrajectory|null,diagnostics:SimulationDiagnostic[],operations:number):SimulationResult {
  let hash:string|null=null;
  if(trajectory) { try { hash=trajectoryHash(encodeTrajectory(trajectory)); } catch(error) { if(status==="FAILED") trajectory=null; else throw error; } }
  return {status,terminationReason:reason,simulationInputHash:inputHash,trajectory,trajectoryHash:hash,simulationResultHash:simulationResultHash({simulationInputHash:inputHash,status,terminationReason:reason,completeness:trajectory?.completeness??null,trajectoryHash:hash,diagnostics}),diagnostics,physicalAuthority:PHYSICAL_AUTHORITY,evaluatorOperations:operations};
}

export function runSimulation(program:SimulationProgram):SimulationResult {
  const inputHash=simulationInputHash(program.manifest); let operations=0; const diagnostics:SimulationDiagnostic[]=[]; const points:SimulationPoint[]=[];
  try {
    validateTemporalConfiguration(program.manifest.temporalConfiguration);
    const initial=new Map<string,number>();
    for(const item of program.manifest.initialConditions){ if(initial.has(item.ref)) simulationFail("DUPLICATE_INITIAL_CONDITION","INITIALIZATION","Initial condition is duplicated",{stateRef:item.ref}); if(!Number.isFinite(item.value)) simulationFail("NON_FINITE_STATE","INITIALIZATION","Initial value must be finite",{stateRef:item.ref}); const state=program.binding.states.find(value=>value.stateRef===item.ref); if(!state||state.unit.key!==item.unit.key||state.unit.revision!==item.unit.revision) simulationFail("INVALID_BINDING","INITIALIZATION","Initial-condition unit does not match exact state binding",{stateRef:item.ref}); initial.set(item.ref,Object.is(item.value,-0)?0:item.value); }
    if(initial.size!==program.binding.states.length) simulationFail("MISSING_INITIAL_CONDITION","INITIALIZATION","Every state requires exactly one initial condition");
    for(const state of program.binding.states) if(!initial.has(state.stateRef)) simulationFail("MISSING_INITIAL_CONDITION","INITIALIZATION","State initial condition is missing",{stateRef:state.stateRef});
    const parameters=new Map<string,number>(); for(const item of program.manifest.parameterValues){ if(parameters.has(item.ref)||!Number.isFinite(item.value)) simulationFail("MISSING_PARAMETER","INITIALIZATION","Parameters must be unique and finite",{details:{ref:item.ref}}); const parameter=program.binding.model.children.find(value=>value.symbol===item.ref); if(!parameter||parameter.kind!=="Parameter"||parameter.unit_ref!==item.unit.key||!program.binding.model.units.some(unit=>unit.key===item.unit.key&&unit.revision===item.unit.revision)) simulationFail("INVALID_BINDING","INITIALIZATION","Parameter unit does not match exact model declaration",{details:{ref:item.ref}}); parameters.set(item.ref,item.value); }
    for(const binding of program.binding.parameters) if(!parameters.has(binding.parameterRef)) simulationFail("MISSING_PARAMETER","INITIALIZATION","Explicit parameter is missing",{details:{ref:binding.parameterRef}});
    let snapshot=Object.freeze(Object.fromEntries(initial)); points.push(point(program,0,snapshot));
    const rateForState=Object.fromEntries(program.binding.rates.map(rate=>[rate.stateRef,rate.rateRef]));
    for(let stepIndex=0;stepIndex<program.manifest.temporalConfiguration.stepCount;stepIndex++){
      const algebraicEvaluations=program.evaluateAlgebraics(snapshot,Object.fromEntries(parameters)); operations+=Object.values(algebraicEvaluations).reduce((n,v)=>n+v.operations,0);
      const algebraics=Object.fromEntries(Object.entries(algebraicEvaluations).map(([k,v])=>[k,v.value])); if(Object.values(algebraics).some(v=>!Number.isFinite(v))) simulationFail("EXPRESSION_FAILURE","ALGEBRAIC","Algebraic result is non-finite",{stepIndex});
      const rateEvaluations=program.evaluateRates(snapshot,algebraics,Object.fromEntries(parameters)); const stepOperations=Object.values(algebraicEvaluations).concat(Object.values(rateEvaluations)).reduce((n,v)=>n+v.operations,0); operations+=Object.values(rateEvaluations).reduce((n,v)=>n+v.operations,0);
      if(stepOperations>GDSS_SIM_LIMITS_V1.evaluatorOperationsPerStep||operations>GDSS_SIM_LIMITS_V1.totalEvaluatorOperations) simulationFail("RESOURCE_LIMIT_EXCEEDED","RATE","Evaluator operation budget exceeded",{stepIndex,details:{stepOperations,operations}});
      const rates=Object.fromEntries(Object.entries(rateEvaluations).map(([k,v])=>[k,v.value]));
      const candidates=explicitEulerTransition(snapshot,rates,program.binding.states,rateForState,program.manifest.temporalConfiguration.step);
      const constraint=program.validateConstraints(candidates); if(!constraint.ok) simulationFail("CONSTRAINT_VIOLATION","CONSTRAINT","Candidate violates governed constraint",{stepIndex:stepIndex+1,details:{constraintRef:constraint.constraintRef}});
      snapshot=candidates; points.push(point(program,stepIndex+1,snapshot));
    }
    const trajectory:{completeness:"COMPLETE";simulationInputHash:string;points:SimulationPoint[]}={completeness:"COMPLETE",simulationInputHash:inputHash,points}; encodeTrajectory(trajectory);
    return finish(inputHash,"COMPLETED","END_TIME_REACHED",trajectory,diagnostics,operations);
  } catch(error) {
    const diagnostic=error instanceof SimulationFault?error.diagnostic:{code:"SOLVER_FAILURE" as const,severity:"ERROR" as const,stage:"TRANSITION" as const,details:{},message:error instanceof Error?error.message:"Unknown solver failure"}; diagnostics.push(diagnostic);
    const trajectory=points.length?{completeness:"PARTIAL" as const,simulationInputHash:inputHash,points}:null;
    return finish(inputHash,"FAILED",reasonFor(diagnostic.code),trajectory,diagnostics,operations);
  }
}
