import { decodeTrajectory,trajectoryHash,TRAJECTORY_FORMAT_VERSION } from "@/lib/gdss/simulation";
import type { GovernedTrajectory,TrajectoryEvidence } from "./contracts";
import { experimentFail } from "./diagnostics";
const TRAJECTORY_MEDIA_TYPE="application/vnd.midd.gdss-trajectory+ndjson;version=1";
export function readGovernedTrajectory(e:TrajectoryEvidence):GovernedTrajectory{
  if(e.mediaType!==TRAJECTORY_MEDIA_TYPE||e.formatVersion!==TRAJECTORY_FORMAT_VERSION)experimentFail("MALFORMED_TRAJECTORY","TRAJECTORY_READ","GDSS-003 trajectory format mismatch");
  if(e.byteLength!==e.payload.byteLength||trajectoryHash(e.payload)!==e.trajectoryHash)experimentFail("ARTIFACT_INTEGRITY_FAILURE","TRAJECTORY_READ","Trajectory bytes do not match identity");
  const trajectory=decodeTrajectory(e.payload,{byteLength:e.byteLength,hash:e.trajectoryHash,simulationInputHash:e.simulationInputHash,states:e.expectedStates});
  if(trajectory.points.length!==e.pointCount||trajectory.completeness!==e.completeness)experimentFail("MALFORMED_TRAJECTORY","TRAJECTORY_READ","Trajectory metadata mismatch");
  return Object.freeze({evidence:e,trajectory,points:Object.freeze(trajectory.points)}) as GovernedTrajectory;
}
