import type { ControlActor } from "@/lib/dto/control-access.dto";
import { assertCalibrationAccess } from "@/lib/gdss/calibration";
import { validateObservationDataset,type ObservationDataset } from "@/lib/gdss/observation";
import { GdssObservationRepository } from "@/lib/repositories/gdss-observation.repository";
export class GdssObservationService{
  constructor(private readonly repository=new GdssObservationRepository()){}
  async admit(actor:ControlActor,dataset:ObservationDataset,datasetKey:string){assertCalibrationAccess(actor,dataset.projectId,"ADMIT_OBSERVATION");validateObservationDataset(dataset);return this.repository.createDraft(actor,dataset,datasetKey);}
  async validate(actor:ControlActor,projectId:string,datasetVersionId:string,dataset:ObservationDataset,reason:string){assertCalibrationAccess(actor,projectId,"ADMIT_OBSERVATION");validateObservationDataset(dataset);return this.repository.validate(actor,projectId,datasetVersionId,dataset,reason);}
  async publish(actor:ControlActor,projectId:string,datasetVersionId:string,reason:string){assertCalibrationAccess(actor,projectId,"ADMIT_OBSERVATION");return this.repository.lifecycle(actor,projectId,datasetVersionId,3,"VALIDATED","PUBLISHED",reason);}
  async deprecate(actor:ControlActor,projectId:string,datasetVersionId:string,reason:string){assertCalibrationAccess(actor,projectId,"ADMIT_OBSERVATION");return this.repository.lifecycle(actor,projectId,datasetVersionId,4,"PUBLISHED","DEPRECATED",reason);}
}
