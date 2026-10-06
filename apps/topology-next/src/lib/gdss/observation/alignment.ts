import { binary64Hex } from "@/lib/gdss/expression/canonical";
import type { AlignmentResult, AlignmentSpecification, ObservationDataset } from "./contracts";
import { observationFail } from "./diagnostics";
import { simulationCoordinate } from "./time";
import { validateObservationDataset } from "./dataset";
export function alignObservationDataset(dataset:ObservationDataset,specification:AlignmentSpecification,grid:readonly number[]):AlignmentResult {
  validateObservationDataset(dataset);
  if(specification.version!=="EXACT_COORDINATE_MATCH_V1"||specification.interpolation!=="NONE"||specification.resampling!=="NONE"||specification.extrapolation!=="NONE") observationFail("TEMPORAL_ALIGNMENT_FAILURE","Only exact coordinate alignment is supported");
  const gridBits=new Map(grid.map(value=>[binary64Hex(value),value]));
  const seriesByKey=new Map(dataset.series.map(series=>[series.seriesKey,series]));
  const points:AlignmentResult["points"]=[];
  for(const mapping of [...specification.mappings].sort((a,b)=>a.mappingKey.localeCompare(b.mappingKey))){
    const series=seriesByKey.get(mapping.seriesKey); if(!series) observationFail("UNKNOWN_QUANTITY_MAPPING","Mapped observation series does not exist");
    for(const point of [...series.points].sort((a,b)=>a.ordinal-b.ordinal)){
      if(point.quality!=="ACCEPTED"){points.push({mappingKey:mapping.mappingKey,seriesKey:series.seriesKey,pointOrdinal:point.ordinal,disposition:"EXCLUDED",reason:point.quality,simulationCoordinate:null,observedValue:point.value});continue;}
      const coordinate=simulationCoordinate(point.measurementTimeUs,specification.measurementTimeOriginUs,specification.simulationT0,specification.simulationTimeUnit);
      const exact=gridBits.get(binary64Hex(coordinate));
      if(exact===undefined) observationFail("TEMPORAL_ALIGNMENT_FAILURE","Accepted point has no exact simulation coordinate");
      points.push({mappingKey:mapping.mappingKey,seriesKey:series.seriesKey,pointOrdinal:point.ordinal,disposition:"MATCHED",reason:null,simulationCoordinate:exact,observedValue:point.value});
    }
  }
  const matchedCount=points.filter(point=>point.disposition==="MATCHED").length;
  if(matchedCount<specification.minimumMatchedCount) observationFail("INSUFFICIENT_OBSERVATIONS","Minimum exact match count not reached");
  return {points,matchedCount,excludedCount:points.length-matchedCount};
}
