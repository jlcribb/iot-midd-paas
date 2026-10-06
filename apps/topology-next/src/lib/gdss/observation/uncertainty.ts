import type { Uncertainty } from "./contracts";
import { observationFail } from "./diagnostics";
export function validateUncertainty(value:Uncertainty){
  if(value.mode!=="UNKNOWN"&&(!Number.isFinite(value.bound)||value.bound<0)) observationFail("INVALID_UNCERTAINTY","Known uncertainty bound must be finite and non-negative");
  return value;
}
