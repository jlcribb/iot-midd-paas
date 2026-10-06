import { binary64Hex } from "@/lib/gdss/expression/canonical";
import { catalogUnit } from "@/lib/gdss/expression/units";
import type { UnitIdentity } from "@/lib/gdss/expression";
import { GDSS_OBSERVATION_LIMITS_V1 } from "./limits";
import { observationFail } from "./diagnostics";

export const MIN_OBSERVATION_TIME_US = -62135596800000000n; // 0001-01-01T00:00:00Z
export const MAX_OBSERVATION_TIME_US = 253402300799999999n; // 9999-12-31T23:59:59.999999Z
export function canonicalInt64(value:bigint) { return { $int64:value.toString(10) }; }
export function parseCanonicalInt64(value:unknown):bigint {
  if (!value || typeof value!=="object" || !("$int64" in value) || typeof value.$int64!=="string" || !/^-?(0|[1-9][0-9]*)$/.test(value.$int64))
    observationFail("INVALID_DATASET","Invalid canonical int64");
  const parsed=BigInt(value.$int64);
  if(parsed<-(1n<<63n)||parsed>(1n<<63n)-1n) observationFail("TEMPORAL_COORDINATE_OUT_OF_RANGE","int64 overflow");
  return parsed;
}
export function validateMeasurementTime(value:bigint) {
  if(value<MIN_OBSERVATION_TIME_US||value>MAX_OBSERVATION_TIME_US) observationFail("TEMPORAL_COORDINATE_OUT_OF_RANGE","Measurement time outside approved UTC range");
  return value;
}
export function elapsedMicroseconds(measurement:bigint,origin:bigint) {
  validateMeasurementTime(measurement); validateMeasurementTime(origin);
  const elapsed=measurement-origin;
  if(elapsed>GDSS_OBSERVATION_LIMITS_V1.maxExactElapsedMicroseconds||elapsed<-GDSS_OBSERVATION_LIMITS_V1.maxExactElapsedMicroseconds)
    observationFail("TEMPORAL_COORDINATE_OUT_OF_RANGE","Elapsed microseconds exceed exact binary64 boundary");
  return elapsed;
}
export function simulationCoordinate(measurement:bigint,origin:bigint,simulationT0:number,timeUnit:UnitIdentity) {
  if(!Number.isFinite(simulationT0)) observationFail("TEMPORAL_ALIGNMENT_FAILURE","Non-finite simulation origin");
  const unit=catalogUnit(timeUnit,undefined,"GDSS_UNIT_CONVERSION_V2");
  if(unit.canonical_unit!=="second"||unit.offset!==0) observationFail("DIMENSION_MISMATCH","Simulation time requires a linear time unit");
  const value=simulationT0+Number(elapsedMicroseconds(measurement,origin))/1_000_000/unit.scale;
  if(!Number.isFinite(value)) observationFail("TEMPORAL_COORDINATE_OUT_OF_RANGE","Non-finite simulation coordinate");
  return Object.is(value,-0)?0:value;
}
export const coordinateBits=(value:number)=>binary64Hex(value);
