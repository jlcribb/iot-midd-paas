import type { StateBinding } from "./contracts";
import { simulationFail } from "./diagnostics";

export function explicitEulerTransition(snapshot:Readonly<Record<string,number>>, rates:Readonly<Record<string,number>>, bindings:readonly StateBinding[], rateForState:Readonly<Record<string,string>>, step:number) {
  const candidates:Record<string,number>={};
  for(const state of [...bindings].sort((a,b)=>a.stateRef.localeCompare(b.stateRef))) {
    const rate=rates[rateForState[state.stateRef]];
    if(!Number.isFinite(rate)) simulationFail("NON_FINITE_RATE","RATE","Rate must be finite",{stateRef:state.stateRef});
    const candidate=snapshot[state.stateRef]+rate*step;
    if(!Number.isFinite(candidate)) simulationFail("NON_FINITE_STATE","TRANSITION","Euler candidate must be finite",{stateRef:state.stateRef});
    candidates[state.stateRef]=Object.is(candidate,-0)?0:candidate;
  }
  return Object.freeze(candidates);
}
