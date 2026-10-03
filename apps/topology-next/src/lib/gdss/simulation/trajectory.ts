import { TextDecoder, TextEncoder } from "node:util";
import { binary64Hex } from "@/lib/gdss/expression/canonical";
import { dimensionsEqual } from "@/lib/gdss/expression/dimensions";
import type { SimulationPoint, SimulationTrajectory } from "./contracts";
import { trajectoryHash } from "./canonical";
import { simulationFail } from "./diagnostics";
import { GDSS_SIM_LIMITS_V1 } from "./limits";
import { TRAJECTORY_FORMAT_VERSION } from "./versions";

const encoder=new TextEncoder();
const exactKeys=(value:Record<string,unknown>,expected:string[])=>Object.keys(value).sort().join("\0")===expected.slice().sort().join("\0");

function noDuplicateKeys(text:string) {
  const stack:{type:"object"|"array";keys?:Set<string>;expectKey?:boolean}[]=[]; let i=0;
  const stringToken=()=>{ i++; const start=i; while(i<text.length){ if(text[i]==="\\"){i+=2;continue;} if(text[i]==='"') return text.slice(start,i++); i++; } throw Error("unterminated string"); };
  while(i<text.length){ const char=text[i];
    if(char==='"'){ const raw=stringToken(), top=stack[stack.length-1]; let j=i; while(/\s/.test(text[j]??""))j++; if(top?.type==="object"&&text[j]===":"){ const key=JSON.parse('"'+raw+'"') as string; if(top.keys!.has(key)) throw Error("duplicate key"); top.keys!.add(key); } continue; }
    if(char==="{") stack.push({type:"object",keys:new Set()}); else if(char==="[") stack.push({type:"array"}); else if(char==="}"||char==="]") stack.pop(); i++;
  }
  if(stack.length) throw Error("unbalanced JSON");
}

function canonicalLine(value:unknown){ return JSON.stringify(value); }
export function encodeTrajectory(trajectory:SimulationTrajectory):Uint8Array {
  if(trajectory.points.length<1 || trajectory.points.length>GDSS_SIM_LIMITS_V1.trajectoryPoints) simulationFail("RESOURCE_LIMIT_EXCEEDED","SERIALIZATION","Trajectory point count is outside limits");
  const symbols=Object.keys(trajectory.points[0].states).sort();
  const header={completeness:trajectory.completeness,format:TRAJECTORY_FORMAT_VERSION,pointCount:trajectory.points.length,simulationInputHash:trajectory.simulationInputHash,stateSymbols:symbols};
  const lines=[canonicalLine(header)];
  trajectory.points.forEach((point,index)=>{
    if(point.stepIndex!==index || point.epistemicKind!=="SIMULATED" || Object.keys(point.states).sort().join("\0")!==symbols.join("\0")) simulationFail("INVALID_TRAJECTORY","SERIALIZATION","Trajectory ordering or symbol set is noncanonical");
    const states:Record<string,unknown>={};
    for(const symbol of symbols){ const state=point.states[symbol]; states[symbol]={dimension:[...state.dimension],unit:{key:state.unit.key,revision:state.unit.revision},value:{$binary64:binary64Hex(state.value)}}; }
    lines.push(canonicalLine({epistemicKind:"SIMULATED",states,stepIndex:index}));
  });
  const bytes=encoder.encode(lines.join("\n")+"\n");
  if(bytes.byteLength>GDSS_SIM_LIMITS_V1.trajectoryBytes) simulationFail("RESOURCE_LIMIT_EXCEEDED","SERIALIZATION","Canonical trajectory exceeds byte limit",{details:{actual:bytes.byteLength,limit:GDSS_SIM_LIMITS_V1.trajectoryBytes}});
  return bytes;
}

function fromHex(hex:string){ if(!/^[0-9a-f]{16}$/.test(hex)) throw Error("invalid binary64"); const bytes=Uint8Array.from(hex.match(/../g)!.map(v=>parseInt(v,16))); const value=new DataView(bytes.buffer).getFloat64(0,false); if(!Number.isFinite(value)||Object.is(value,-0)||binary64Hex(value)!==hex) throw Error("noncanonical binary64"); return value; }

export function decodeTrajectory(bytes:Uint8Array,expected?:{byteLength?:number;hash?:string;simulationInputHash?:string;states?:Record<string,{unit:{key:string;revision:number};dimension:[number,number,number,number,number,number,number]}>}):SimulationTrajectory {
  try {
    if(expected?.byteLength!==undefined&&expected.byteLength!==bytes.byteLength) throw Error("byte-count mismatch");
    if(expected?.hash&&trajectoryHash(bytes)!==expected.hash) throw Error("hash mismatch");
    if(bytes[0]===0xef&&bytes[1]===0xbb&&bytes[2]===0xbf) throw Error("BOM");
    const text=new TextDecoder("utf-8",{fatal:true}).decode(bytes);
    if(text.includes("\r")||!text.endsWith("\n")) throw Error("noncanonical line ending");
    const lines=text.slice(0,-1).split("\n"); if(lines.length<2) throw Error("missing points");
    lines.forEach(noDuplicateKeys);
    const header=JSON.parse(lines[0]) as Record<string,unknown>;
    if(!exactKeys(header,["completeness","format","pointCount","simulationInputHash","stateSymbols"])||header.format!==TRAJECTORY_FORMAT_VERSION||(header.completeness!=="COMPLETE"&&header.completeness!=="PARTIAL")||!Number.isSafeInteger(header.pointCount)||header.pointCount!==lines.length-1||!Array.isArray(header.stateSymbols)||header.stateSymbols.some(v=>typeof v!=="string")||[...(header.stateSymbols as string[])].sort().join("\0")!==(header.stateSymbols as string[]).join("\0")||new Set(header.stateSymbols as string[]).size!==(header.stateSymbols as string[]).length) throw Error("invalid header");
    if(expected?.simulationInputHash&&header.simulationInputHash!==expected.simulationInputHash) throw Error("input hash mismatch");
    const symbols=header.stateSymbols as string[], points:SimulationPoint[]=[];
    lines.slice(1).forEach((line,index)=>{ const raw=JSON.parse(line) as Record<string,unknown>; if(!exactKeys(raw,["epistemicKind","states","stepIndex"])||raw.epistemicKind!=="SIMULATED"||raw.stepIndex!==index||!raw.states||typeof raw.states!=="object"||Array.isArray(raw.states)||Object.keys(raw.states as object).sort().join("\0")!==symbols.join("\0")) throw Error("invalid point"); const states:SimulationPoint["states"]={}; for(const symbol of symbols){ const state=(raw.states as Record<string,Record<string,unknown>>)[symbol]; if(!exactKeys(state,["dimension","unit","value"])||!Array.isArray(state.dimension)||state.dimension.length!==7||state.dimension.some(v=>!Number.isSafeInteger(v))||!state.unit||typeof state.unit!=="object"||!exactKeys(state.unit as Record<string,unknown>,["key","revision"])||typeof (state.unit as Record<string,unknown>).key!=="string"||!Number.isSafeInteger((state.unit as Record<string,unknown>).revision)||!state.value||typeof state.value!=="object"||!exactKeys(state.value as Record<string,unknown>,["$binary64"])) throw Error("invalid state"); const unit=state.unit as {key:string;revision:number}; const dimension=state.dimension as [number,number,number,number,number,number,number]; const governed=expected?.states?.[symbol]; if(governed&&(governed.unit.key!==unit.key||governed.unit.revision!==unit.revision||!dimensionsEqual(governed.dimension,dimension))) throw Error("invalid unit dimension"); states[symbol]={value:fromHex((state.value as Record<string,string>)["$binary64"]),unit,dimension}; } points.push({stepIndex:index,epistemicKind:"SIMULATED",states}); });
    return {completeness:header.completeness as "COMPLETE"|"PARTIAL",simulationInputHash:String(header.simulationInputHash),points};
  } catch(error){ const reason=error instanceof Error?error.message:"unknown"; simulationFail("INVALID_TRAJECTORY","SERIALIZATION",`Canonical trajectory rejected: ${reason}`,{details:{reason}}); }
}
