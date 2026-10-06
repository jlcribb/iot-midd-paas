import { GDSS_OBSERVATION_LIMITS_V1 } from "./limits";
import type { ObservationDataset } from "./contracts";
import { observationFail } from "./diagnostics";
import { validatePointQuality } from "./quality";
import { validateSources } from "./source";
import { validateMeasurementTime } from "./time";
import { validateUncertainty } from "./uncertainty";
export function validateObservationDataset(dataset:ObservationDataset){
  if(dataset.sources.length>GDSS_OBSERVATION_LIMITS_V1.sourcesPerDataset||dataset.series.length>GDSS_OBSERVATION_LIMITS_V1.seriesPerDataset) observationFail("RESOURCE_LIMIT_EXCEEDED","Observation structure exceeds limits");
  validateSources(dataset.epistemicOrigin,dataset.sources);
  const sourceIds=new Set(dataset.sources.map(s=>s.sourceIdentity));
  if(sourceIds.size!==dataset.sources.length) observationFail("INVALID_DATASET","Duplicate source identity");
  let count=0; const keys=new Set<string>();
  for(const series of dataset.series){
    if(keys.has(series.seriesKey)||series.points.length>GDSS_OBSERVATION_LIMITS_V1.pointsPerSeries) observationFail("INVALID_DATASET","Duplicate series or too many points");
    keys.add(series.seriesKey); count+=series.points.length;
    const coordinates=new Set<string>();
    for(const point of series.points){
      validateMeasurementTime(point.measurementTimeUs); validatePointQuality(point); validateUncertainty(point.uncertainty);
      if(!sourceIds.has(point.sourceIdentity)) observationFail("INVALID_DATASET","Point source is not governed by the dataset");
      const coordinate=point.measurementTimeUs.toString();
      if(coordinates.has(coordinate)) observationFail("DUPLICATE_MEASUREMENT_COORDINATE","Duplicate series measurement coordinate");
      coordinates.add(coordinate);
    }
  }
  if(count>GDSS_OBSERVATION_LIMITS_V1.pointsPerDataset) observationFail("RESOURCE_LIMIT_EXCEEDED","Dataset point limit exceeded");
  return dataset;
}
