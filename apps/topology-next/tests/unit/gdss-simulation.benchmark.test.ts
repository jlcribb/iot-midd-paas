import { performance } from "node:perf_hooks";
import { describe,expect,it } from "vitest";
import { compileSimulationProgram,encodeTrajectory,GDSS_SIM_LIMITS_V1,runSimulation } from "@/lib/gdss/simulation";
import { reservoirFixture } from "../fixtures/gdss-simulation";

const BENCHMARK_THRESHOLDS=Object.freeze({elapsedMs:3_000,heapDeltaBytes:128*1024*1024});

describe("GDSS-003 benchmark gate",()=>{
  it("executes the approved 10,000-step reservoir within predetermined bounds",()=>{
    const fixture=reservoirFixture(0.01,10_000),program=compileSimulationProgram(fixture.binding,fixture.manifest);
    const heapBefore=process.memoryUsage().heapUsed,start=performance.now(),result=runSimulation(program),elapsedMs=performance.now()-start,heapDeltaBytes=Math.max(0,process.memoryUsage().heapUsed-heapBefore),artifactBytes=encodeTrajectory(result.trajectory!).byteLength;
    const evidence={model:"analytical_reservoir",states:1,steps:10_000,trajectoryPoints:result.trajectory?.points.length,evaluatorOperations:result.evaluatorOperations,artifactBytes,elapsedMs:Number(elapsedMs.toFixed(3)),heapDeltaBytes,limitProfile:GDSS_SIM_LIMITS_V1.profileVersion,status:result.status};
    console.info("GDSS_SIM_BENCHMARK",JSON.stringify(evidence));
    expect(result.status).toBe("COMPLETED");expect(evidence.trajectoryPoints).toBe(10_001);expect(artifactBytes).toBeLessThanOrEqual(GDSS_SIM_LIMITS_V1.trajectoryBytes);expect(elapsedMs).toBeLessThan(BENCHMARK_THRESHOLDS.elapsedMs);expect(heapDeltaBytes).toBeLessThan(BENCHMARK_THRESHOLDS.heapDeltaBytes);
  });
});
