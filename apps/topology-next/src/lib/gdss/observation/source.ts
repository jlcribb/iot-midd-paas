import type { EpistemicOrigin, ObservationSourceReference } from "./contracts";
import { observationFail } from "./diagnostics";
const sha=/^[0-9a-f]{64}$/;
const physical=new Set(["GOVERNED_FILE_ARTIFACT","GOVERNED_DATABASE_SNAPSHOT"]);
export function validateSources(origin:EpistemicOrigin,sources:readonly ObservationSourceReference[]) {
  if(!sources.length) observationFail("INVALID_DATASET","At least one immutable source is required");
  for(const source of sources){
    if(!sha.test(source.contentSha256)) observationFail("SOURCE_HASH_MISMATCH","Invalid source content hash");
    if(origin==="PHYSICAL_OBSERVATION"){
      if(!physical.has(source.sourceType)||!source.physicalSystemIdentity?.trim()||!source.channelIdentity.trim())
        observationFail("SOURCE_EPISTEMIC_ORIGIN_MISMATCH","Physical evidence requires physical source, system and channel identities");
      if(source.generatorIdentity||source.generatorVersion||source.generatorContentHash) observationFail("SOURCE_EPISTEMIC_ORIGIN_MISMATCH","Physical source cannot carry synthetic generator provenance");
    }else{
      if(source.sourceType!=="SYNTHETIC_FIXTURE"||source.physicalSystemIdentity!==null||!source.generatorIdentity?.trim()||!source.generatorVersion?.trim()||!source.generatorContentHash||!sha.test(source.generatorContentHash)||!source.channelIdentity.trim())
        observationFail("SOURCE_EPISTEMIC_ORIGIN_MISMATCH","Synthetic evidence requires fixture/generator provenance and null physical identity");
    }
  }
  return sources;
}
