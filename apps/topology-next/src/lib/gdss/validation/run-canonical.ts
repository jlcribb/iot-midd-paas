import { canonicalValidationJson, validationHash } from "./canonical";
import {
  observationReferenceContentSchema,
  pairSetContentSchema,
  pairingContractSchema,
  predictionContentSchema,
  validationRunContentSchema,
  type ObservationReferenceContent,
  type PairSetContent,
  type PairingContract,
  type PredictionContent,
  type ValidationRunContent,
} from "./run-contracts";

export const canonicalValidationRun = (v: unknown): ValidationRunContent =>
  validationRunContentSchema.parse(v);
export const canonicalPrediction = (v: unknown): PredictionContent =>
  predictionContentSchema.parse(v);
export const canonicalObservationReference = (
  v: unknown,
): ObservationReferenceContent => observationReferenceContentSchema.parse(v);
export const canonicalPairingContract = (v: unknown): PairingContract =>
  pairingContractSchema.parse(v);
export const canonicalPairSet = (v: unknown): PairSetContent => {
  const x = pairSetContentSchema.parse(v);
  return { ...x, pairHashes: [...new Set(x.pairHashes)].sort() };
};
export const validationRunHash = (v: unknown) =>
  validationHash("gdss006:validation-run:v1", canonicalValidationRun(v));
export const predictionHash = (v: unknown) =>
  validationHash("gdss006:prediction:v1", canonicalPrediction(v));
export const observationReferenceHash = (v: unknown) =>
  validationHash(
    "gdss006:observation-reference:v1",
    canonicalObservationReference(v),
  );
export const predictionCommitmentHash = (predictionContentHash: string) =>
  validationHash("gdss006:prediction-commitment:v1", {
    predictionHash: predictionContentHash,
    trustClass: "PLATFORM_PROSPECTIVE",
  });
export const predictionObservationPairHash = (
  predictionContentHash: string,
  observationHash: string,
  contract: unknown,
) =>
  validationHash("gdss006:prediction-observation-pair:v1", {
    predictionHash: predictionContentHash,
    observationHash,
    contract: canonicalPairingContract(contract),
  });
export const pairIntegrityHash = (
  pairHash: string,
  state: string,
  details: unknown,
) => validationHash("gdss006:pair-integrity:v1", { pairHash, state, details });
export const predictionPairSetHash = (v: unknown) =>
  validationHash("gdss006:pair-set:v1", canonicalPairSet(v));
export { canonicalValidationJson };
