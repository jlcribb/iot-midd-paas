import type { SimulationRunView } from "@/components/control/simulation-workbench-client";

/** This is a display-only equality check over server-materialized opaque IDs. */
export function reproducibilityEvidence(runs: SimulationRunView[]) {
  const fingerprints = runs.flatMap((run) => typeof run.result_fingerprint === "string" ? [run.result_fingerprint] : []);
  if (fingerprints.length < 2) return { status: "PENDING" as const, count: fingerprints.length };
  return { status: new Set(fingerprints).size === 1 ? "CONSISTENT" as const : "DIFFERENT" as const, count: fingerprints.length };
}

export function isTerminalRun(status: string) {
  return status === "COMPLETED" || status === "FAILED" || status === "CANCELLED";
}
