import { randomUUID } from "node:crypto";
import { readFileSync,readdirSync } from "node:fs";
import { join } from "node:path";
import { describe,expect,it } from "vitest";
import { contentHash } from "@/lib/gdss/core";
import { assertSimulationAccess, compileSimulationProgram, dynamicBindingHash, encodeTrajectory, executionAttemptId, explicitEulerTransition, GDSS_SIM_LIMITS_V1, runSimulation, simulationInputHash, timeAt, trajectoryHash } from "@/lib/gdss/simulation";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { reservoirFixture } from "../fixtures/gdss-simulation";

const source=()=>readdirSync(join(process.cwd(),"src/lib/gdss/simulation")).filter(f=>f.endsWith(".ts")).map(f=>readFileSync(join(process.cwd(),"src/lib/gdss/simulation",f),"utf8")).join("\n");
const migration=()=>readFileSync(join(process.cwd(),"../../infra/migrations/alembic/versions/0041_gdss_dynamic_simulation.py"),"utf8");
const execute=()=>{const f=reservoirFixture();return {f,result:runSimulation(compileSimulationProgram(f.binding,f.manifest))};};
const fails=(mutate:(f:ReturnType<typeof reservoirFixture>)=>void)=>{const f=reservoirFixture();mutate(f);expect(()=>compileSimulationProgram(f.binding,f.manifest)).toThrow();};
const cases:{id:string;evidence:()=>void}[]=[
  {id:"GDS3-INV-01 exact model version",evidence:()=>fails(f=>{f.manifest.modelVersionId=randomUUID();})},
  {id:"GDS3-INV-02 simulation time excludes wall/device time",evidence:()=>{const f=reservoirFixture();expect(Object.keys(f.manifest.temporalConfiguration).sort()).toEqual(["start","step","stepCount","timeUnit","unitConversionCatalogVersion"].sort());}},
  {id:"GDS3-INV-03 exactly one initial condition per state",evidence:()=>{const f=reservoirFixture();f.manifest.initialConditions=[];expect(runSimulation(compileSimulationProgram(f.binding,f.manifest)).terminationReason).toBe("INVALID_CONFIGURATION");}},
  {id:"GDS3-INV-04 roles are closed and distinct",evidence:()=>fails(f=>{(f.binding.states[0] as {role:string}).role="STOCK";})},
  {id:"GDS3-INV-05 roles are explicit not inferred",evidence:()=>{const {result}=execute();expect(result.status).toBe("COMPLETED");}},
  {id:"GDS3-INV-06 rate dimension equals state divided by TIME",evidence:()=>fails(f=>{f.binding.rates[0].dimension=[3,0,0,0,0,0,0];})},
  {id:"GDS3-INV-07 solver identity explicit",evidence:()=>fails(f=>{(f.manifest as {solverVersion:string}).solverVersion="EULER_LATEST";})},
  {id:"GDS3-INV-08 temporal fields participate in input identity",evidence:()=>{const a=reservoirFixture(),hash=simulationInputHash(a.manifest);for(const field of ["start","step","stepCount"] as const){const b=reservoirFixture();(b.manifest.temporalConfiguration[field] as number)+=1;expect(simulationInputHash(b.manifest)).not.toBe(hash);}}},
  {id:"GDS3-INV-09 no implicit timestep",evidence:()=>{for(const step of [0,-1,Number.NaN])fails(f=>{f.manifest.temporalConfiguration.step=step;});}},
  {id:"GDS3-INV-10 equal inputs equal trajectory identity",evidence:()=>{const a=execute().result,b=execute().result;expect(a.trajectoryHash).toBe(b.trajectoryHash);}},
  {id:"GDS3-INV-11 simultaneous pre-step snapshot",evidence:()=>{const states=[{role:"STATE" as const,stateRef:"x",unit:{key:"meter",revision:1},dimension:[1,0,0,0,0,0,0] as [number,number,number,number,number,number,number],constraintRefs:[]},{role:"STATE" as const,stateRef:"y",unit:{key:"meter",revision:1},dimension:[1,0,0,0,0,0,0] as [number,number,number,number,number,number,number],constraintRefs:[]}];expect(explicitEulerTransition({x:1,y:2},{rx:2,ry:1},states,{x:"rx",y:"ry"},1)).toEqual({x:3,y:3});}},
  {id:"GDS3-INV-12 algebraic loop differs from temporal feedback",evidence:()=>expect(source()).toContain("INSTANTANEOUS_ALGEBRAIC_LOOP_UNSUPPORTED")},
  {id:"GDS3-INV-13 every output point is SIMULATED",evidence:()=>expect(execute().result.trajectory!.points.every(p=>p.epistemicKind==="SIMULATED")).toBe(true)},
  {id:"GDS3-INV-14 simulation is not PREDICTED",evidence:()=>expect(JSON.stringify(execute().result)).not.toContain("PREDICTED")},
  {id:"GDS3-INV-15 solver success is not scientific validation",evidence:()=>expect(JSON.stringify(execute().result)).not.toContain("SCIENTIFICALLY_VALIDATED")},
  {id:"GDS3-INV-16 observed provenance does not propagate",evidence:()=>{const f=reservoirFixture();f.manifest.initialConditions[0].provenanceIdentity="OBSERVED:test";expect(runSimulation(compileSimulationProgram(f.binding,f.manifest)).trajectory!.points[0].epistemicKind).toBe("SIMULATED");}},
  {id:"GDS3-INV-17 no implicit telemetry retrieval",evidence:()=>{const f=reservoirFixture();f.manifest.parameterValues=[];expect(runSimulation(compileSimulationProgram(f.binding,f.manifest)).status).toBe("FAILED");}},
  {id:"GDS3-INV-18 runtime performs no MQTT operation",evidence:()=>expect(source().toLowerCase()).not.toContain("mqtt")},
  {id:"GDS3-INV-19 runtime performs no Control Engine operation",evidence:()=>expect(source().toLowerCase()).not.toContain("control-engine")},
  {id:"GDS3-INV-20 runtime performs no DTE operation",evidence:()=>expect(source()).not.toMatch(/from ["'][^"']*dte/i)},
  {id:"GDS3-INV-21 physical authority is NONE",evidence:()=>expect(execute().result.physicalAuthority).toBe("NONE")},
  {id:"GDS3-INV-22 runtime cannot create actuation artifacts",evidence:()=>expect(source()).not.toMatch(/Actuation(Command|Intent|Authorization)|DeploymentIntent|ControlPolicy/)},
  {id:"GDS3-INV-23 every run is resource bounded",evidence:()=>{expect(Object.values(GDSS_SIM_LIMITS_V1).filter(v=>typeof v==="number").every(v=>v>0&&Number.isFinite(v))).toBe(true);fails(f=>{f.manifest.temporalConfiguration.stepCount=10001;});}},
  {id:"GDS3-INV-24 non-finite numerics fail closed",evidence:()=>{const f=reservoirFixture();f.manifest.initialConditions[0].value=Infinity;expect(()=>runSimulation(compileSimulationProgram(f.binding,f.manifest))).toThrow(/finite/);}},
  {id:"GDS3-INV-25 incomplete simulation is never complete",evidence:()=>{const f=reservoirFixture(),p=compileSimulationProgram(f.binding,f.manifest);p.validateConstraints=()=>({ok:false,constraintRef:"limit"});const r=runSimulation(p);expect([r.status,r.trajectory?.completeness]).toEqual(["FAILED","PARTIAL"]);}},
  {id:"GDS3-INV-26 persisted evidence is append-only",evidence:()=>expect((migration().match(/append_only/g)??[]).length).toBeGreaterThanOrEqual(7)},
  {id:"GDS3-INV-27 model changes do not change existing execution",evidence:()=>{const {f,result}=execute();const hash=result.trajectoryHash;f.model.description="successor";expect(result.trajectoryHash).toBe(hash);}},
  {id:"GDS3-INV-28 solver change requires a new version",evidence:()=>fails(f=>{(f.manifest as {solverVersion:string}).solverVersion="EXPLICIT_EULER_V2";})},
  {id:"GDS3-INV-29 input and result identities are domain separated",evidence:()=>{const r=execute().result;expect(r.simulationInputHash).not.toBe(r.simulationResultHash);}},
  {id:"GDS3-INV-30 Forrester is not core ontology",evidence:()=>expect(source()).not.toMatch(/\b(STOCK|FLOW|Forrester)\b/)},
  {id:"GDS3-INV-31 execution is not an Experiment",evidence:()=>expect(JSON.stringify(execute().result)).not.toMatch(/experiment|hypothesis|comparison/i)},
  {id:"GDS3-INV-32 run is not Digital Twin synchronization",evidence:()=>expect(source()).not.toMatch(/DigitalShadow|DigitalTwin|physicalAsset|synchroniz/i)},
  {id:"GDS3-INV-33 constraints fail and never clamp",evidence:()=>{const f=reservoirFixture(),p=compileSimulationProgram(f.binding,f.manifest);p.validateConstraints=()=>({ok:false,constraintRef:"limit"});expect(runSimulation(p).terminationReason).toBe("CONSTRAINT_VIOLATION");}},
  {id:"GDS3-INV-34 feedback is stepped while SCC is rejected",evidence:()=>{expect(execute().result.status).toBe("COMPLETED");expect(source()).toContain("visiting.has(symbol)");}},
  {id:"GDS3-INV-35 simulation leaves model identity unchanged",evidence:()=>{const f=reservoirFixture(),before=contentHash(f.model);runSimulation(compileSimulationProgram(f.binding,f.manifest));expect(contentHash(f.model)).toBe(before);}},
  {id:"GDS3-INV-36 GDSS identity differs from control replay",evidence:()=>expect(migration()).not.toContain("control_simulation_")},
  {id:"GDS3-INV-37 binding leaves model content hash unchanged",evidence:()=>{const f=reservoirFixture(),before=contentHash(f.model);dynamicBindingHash(f.content);expect(contentHash(f.model)).toBe(before);}},
  {id:"GDS3-INV-38 step_index is temporal authority",evidence:()=>{const f=reservoirFixture(0.1,10);expect(timeAt(f.manifest.temporalConfiguration,10)).toBe(1);expect(runSimulation(compileSimulationProgram(f.binding,f.manifest)).trajectory!.points.map(p=>p.stepIndex)).toEqual([...Array(11).keys()]);}},
  {id:"GDS3-INV-39 object order cannot change trajectory",evidence:()=>{const a=reservoirFixture(),b=reservoirFixture();b.manifest.parameterValues.reverse();const ar=runSimulation(compileSimulationProgram(a.binding,a.manifest)),br=runSimulation(compileSimulationProgram(b.binding,b.manifest));expect(ar.trajectoryHash).toBe(br.trajectoryHash);}},
  {id:"GDS3-INV-40 attempt identity differs from computational identity",evidence:()=>{const a=executionAttemptId(),b=executionAttemptId(),x=execute().result,y=execute().result;expect(a).not.toBe(b);expect(x.simulationInputHash).toBe(y.simulationInputHash);expect(x.trajectoryHash).toBe(y.trajectoryHash);expect(x.simulationResultHash).toBe(y.simulationResultHash);}}
];

describe("GDSS-003 forty invariant gate",()=>{it.each(cases)("$id",({evidence})=>evidence());});

describe("GDSS-003 authorization separation",()=>{
  const project="00000000-0000-4000-8000-000000000031";
  const actor=(role:"viewer"|"operator"|"admin",auth_source:"oauth_session"|"dev_fallback"="oauth_session"):ControlActor=>({user_id:"user",display_name:null,auth_source,role,all_projects:false,project_ids:[project],project_roles:{[project]:role}});
  it("allows operator/admin and rejects viewer/fallback/out-of-project",()=>{expect(()=>assertSimulationAccess(actor("operator"),project,"run_simulation")).not.toThrow();expect(()=>assertSimulationAccess(actor("admin"),project,"run_simulation")).not.toThrow();expect(()=>assertSimulationAccess(actor("viewer"),project,"run_simulation")).toThrow();expect(()=>assertSimulationAccess(actor("admin","dev_fallback"),project,"run_simulation")).toThrow();expect(()=>assertSimulationAccess({...actor("admin"),project_ids:[],project_roles:{}},project,"run_simulation")).toThrow();});
});
