import { catalogUnit } from "@/lib/gdss/expression";
import { UNIT_CONVERSION_CATALOG_VERSION_V2 } from "@/lib/gdss/expression/versions";
import { dimensionsEqual } from "@/lib/gdss/expression/dimensions";
import type { TemporalConfiguration } from "./contracts";
import { simulationFail } from "./diagnostics";
import { GDSS_SIM_LIMITS_V1 } from "./limits";

export const TIME_DIMENSION = Object.freeze([0,0,1,0,0,0,0] as const);

export function validateTemporalConfiguration(input: TemporalConfiguration) {
  if (input.unitConversionCatalogVersion !== UNIT_CONVERSION_CATALOG_VERSION_V2)
    simulationFail("VERSION_MISMATCH","PREFLIGHT","GDSS-003 requires GDSS_UNIT_CONVERSION_V2",{details:{actual:input.unitConversionCatalogVersion}});
  if (!Number.isFinite(input.start) || !Number.isFinite(input.step) || input.step <= 0 || !Number.isSafeInteger(input.stepCount) || input.stepCount < 0)
    simulationFail("INVALID_CONFIGURATION","PREFLIGHT","Temporal start, positive step and integer stepCount are required");
  if (input.stepCount > GDSS_SIM_LIMITS_V1.stepCount)
    simulationFail("RESOURCE_LIMIT_EXCEEDED","PREFLIGHT","stepCount exceeds GDSS_SIM_LIMITS_V1",{details:{limit:GDSS_SIM_LIMITS_V1.stepCount,actual:input.stepCount}});
  if (input.timeUnit.key !== "second" || input.timeUnit.revision !== 1)
    simulationFail("INVALID_TIME_UNIT","PREFLIGHT","GDSS-003 v1 requires second@1",{details:{actual:input.timeUnit}});
  const unit = catalogUnit(input.timeUnit,undefined,UNIT_CONVERSION_CATALOG_VERSION_V2);
  if (!dimensionsEqual(unit.dimension,[...TIME_DIMENSION]) || unit.affineFamily || !unit.quantitySemantics.includes("INTERVAL"))
    simulationFail("INVALID_TIME_UNIT","PREFLIGHT","Temporal unit must be a non-affine TIME interval");
  return input;
}
export function timeAt(configuration: TemporalConfiguration, stepIndex:number) {
  if (!Number.isSafeInteger(stepIndex) || stepIndex < 0 || stepIndex > configuration.stepCount)
    simulationFail("INVALID_CONFIGURATION","PREFLIGHT","stepIndex is outside temporal configuration");
  const value = configuration.start + stepIndex * configuration.step;
  if (!Number.isFinite(value)) simulationFail("INVALID_CONFIGURATION","PREFLIGHT","Derived simulation coordinate is non-finite");
  return Object.is(value,-0) ? 0 : value;
}
