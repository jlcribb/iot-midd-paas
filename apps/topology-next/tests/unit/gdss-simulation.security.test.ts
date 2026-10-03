import { describe,expect,it } from "vitest";
import { contentHash } from "@/lib/gdss/core";
import { compileSimulationProgram,decodeTrajectory,dynamicBindingHash,encodeTrajectory,GDSS_SIM_LIMITS_V1,runSimulation,simulationInputHash,trajectoryHash,type SimulationTrajectory } from "@/lib/gdss/simulation";
import { reservoirFixture } from "../fixtures/gdss-simulation";

const bytes=(text:string)=>new TextEncoder().encode(text);
const text=(value:Uint8Array)=>new TextDecoder().decode(value);
function base(){const f=reservoirFixture(),r=runSimulation(compileSimulationProgram(f.binding,f.manifest)),encoded=encodeTrajectory(r.trajectory!);return{f,r,encoded,lines:text(encoded).slice(0,-1).split("\n")};}
const expected={states:{volume:{unit:{key:"cubic_meter",revision:1},dimension:[3,0,0,0,0,0,0] as [number,number,number,number,number,number,number]}}};

describe("GDSS-003 adversarial decoder",()=>{
  const attacks:[string,(value:ReturnType<typeof base>)=>Uint8Array][]=[
    ["duplicate JSON keys",v=>bytes(text(v.encoded).replace('{"completeness"','{"completeness":"COMPLETE","completeness"'))],
    ["BOM",v=>new Uint8Array([0xef,0xbb,0xbf,...v.encoded])],
    ["CRLF",v=>bytes(text(v.encoded).replaceAll("\n","\r\n"))],
    ["missing final LF",v=>v.encoded.slice(0,-1)],
    ["out-of-order index",v=>{const p=JSON.parse(v.lines[2]);p.stepIndex=9;v.lines[2]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}],
    ["duplicate index",v=>{const p=JSON.parse(v.lines[2]);p.stepIndex=0;v.lines[2]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}],
    ["symbol drift",v=>{const p=JSON.parse(v.lines[1]);p.states.extra=p.states.volume;v.lines[1]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}],
    ["missing state",v=>{const p=JSON.parse(v.lines[1]);delete p.states.volume;v.lines[1]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}],
    ["invalid binary64",v=>{const p=JSON.parse(v.lines[1]);p.states.volume.value.$binary64="xyz";v.lines[1]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}],
    ["negative zero binary64",v=>{const p=JSON.parse(v.lines[1]);p.states.volume.value.$binary64="8000000000000000";v.lines[1]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}],
    ["invalid dimension",v=>{const p=JSON.parse(v.lines[1]);p.states.volume.dimension=[3,0,0];v.lines[1]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}],
    ["invalid unit",v=>{const p=JSON.parse(v.lines[1]);p.states.volume.unit.key="spoof";v.lines[1]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}],
    ["point-count mismatch",v=>{const h=JSON.parse(v.lines[0]);h.pointCount=999;v.lines[0]=JSON.stringify(h);return bytes(v.lines.join("\n")+"\n");}],
    ["unknown point field",v=>{const p=JSON.parse(v.lines[1]);p.timestamp=0;v.lines[1]=JSON.stringify(p);return bytes(v.lines.join("\n")+"\n");}]
  ];
  it.each(attacks)("rejects %s",(_name,attack)=>expect(()=>decodeTrajectory(attack(base()),expected)).toThrow(/rejected/));
  it("rejects byte-count and hash mismatch",()=>{const {encoded}=base();expect(()=>decodeTrajectory(encoded,{...expected,byteLength:encoded.length+1})).toThrow();expect(()=>decodeTrajectory(encoded,{...expected,hash:"0".repeat(64)})).toThrow();});
});

describe("GDSS-003 fail-closed security and resources",()=>{
  it("rejects V1, unknown catalog, non-time unit and invalid steps",()=>{for(const mutate of [(f:ReturnType<typeof reservoirFixture>)=>(f.manifest as {unitConversionCatalogVersion:string}).unitConversionCatalogVersion="GDSS_UNIT_CONVERSION_V1",(f:ReturnType<typeof reservoirFixture>)=>(f.manifest.temporalConfiguration as {unitConversionCatalogVersion:string}).unitConversionCatalogVersion="UNKNOWN",(f:ReturnType<typeof reservoirFixture>)=>f.manifest.temporalConfiguration.timeUnit={key:"meter",revision:1},(f:ReturnType<typeof reservoirFixture>)=>f.manifest.temporalConfiguration.step=0,(f:ReturnType<typeof reservoirFixture>)=>f.manifest.temporalConfiguration.stepCount=10001]){const f=reservoirFixture();mutate(f);expect(()=>compileSimulationProgram(f.binding,f.manifest)).toThrow();}});
  it("rejects state/rate/algebraic/parameter/constraint explosion",()=>{for(const field of ["states","rates","algebraics","parameters","constraintRefs"] as const){const f=reservoirFixture(),limit={states:64,rates:64,algebraics:256,parameters:256,constraintRefs:256}[field];const sample=(f.binding[field] as unknown[])[0]??(field==="constraintRefs"?"constraint":{});(f.binding[field] as unknown[]).splice(0,Infinity,...Array.from({length:limit+1},()=>structuredClone(sample)));expect(()=>compileSimulationProgram(f.binding,f.manifest)).toThrow();}});
  it("rejects evaluator operation exhaustion and numeric divergence",()=>{const f=reservoirFixture(),program=compileSimulationProgram(f.binding,f.manifest);program.evaluateRates=()=>({volume_rate:{value:2,operations:GDSS_SIM_LIMITS_V1.evaluatorOperationsPerStep+1}});expect(runSimulation(program).terminationReason).toBe("RESOURCE_LIMIT_EXCEEDED");const divergent=compileSimulationProgram(f.binding,f.manifest);divergent.evaluateRates=()=>({volume_rate:{value:Infinity,operations:1}});expect(runSimulation(divergent).terminationReason).toBe("NON_FINITE_RATE");});
  it("rejects instantaneous algebraic SCC",()=>{const f=reservoirFixture(),dim:[number,number,number,number,number,number,number]=[3,0,0,0,0,0,0],p=f.model.provenance;f.model.children.push({kind:"Variable",symbol:"a",label:"a",description:"",provenance:p,unit_ref:"cubic_meter",dimension:dim,computational_role:"AUXILIARY",epistemic_kind:"DERIVED"},{kind:"Variable",symbol:"b",label:"b",description:"",provenance:p,unit_ref:"cubic_meter",dimension:dim,computational_role:"AUXILIARY",epistemic_kind:"DERIVED"},{kind:"Formula",symbol:"a_formula",label:"a",description:"",provenance:p,expression_source:"b",input_refs:["b"],output_ref:"a",validity_domain:{}},{kind:"Formula",symbol:"b_formula",label:"b",description:"",provenance:p,expression_source:"a",input_refs:["a"],output_ref:"b",validity_domain:{}});f.binding.algebraics.push({role:"ALGEBRAIC",algebraicRef:"a",formulaRef:"a_formula",outputRef:"a"},{role:"ALGEBRAIC",algebraicRef:"b",formulaRef:"b_formula",outputRef:"b"});f.content.algebraics=structuredClone(f.binding.algebraics);f.content.modelContentHash=contentHash(f.model);f.binding.modelContentHash=f.content.modelContentHash;f.binding.dynamicBindingHash=dynamicBindingHash(f.content);f.manifest.modelContentHash=f.binding.modelContentHash;f.manifest.dynamicBindingHash=f.binding.dynamicBindingHash;expect(()=>compileSimulationProgram(f.binding,f.manifest)).toThrow(/cycle/);});
  it("enforces the 16 MiB trajectory boundary",()=>{const huge="x".repeat(GDSS_SIM_LIMITS_V1.trajectoryBytes);const trajectory:SimulationTrajectory={completeness:"COMPLETE",simulationInputHash:"0".repeat(64),points:[{stepIndex:0,epistemicKind:"SIMULATED",states:{[huge]:{value:0,unit:{key:"meter",revision:1},dimension:[1,0,0,0,0,0,0]}}}]};expect(()=>encodeTrajectory(trajectory)).toThrow(/byte limit/);});
});
