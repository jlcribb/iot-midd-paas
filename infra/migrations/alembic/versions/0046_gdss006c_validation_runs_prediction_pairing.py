"""GDSS-006C validation runs, prediction commitment and pairing. Revision 0046."""
from alembic import op

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_validation_run(
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      status TEXT NOT NULL DEFAULT 'CREATED' CHECK(status IN('CREATED','READY','RUNNING','COMPLETED','FAILED','INVALIDATED')),
      run_mode TEXT NOT NULL CHECK(run_mode IN('RETROSPECTIVE','PSEUDO_PROSPECTIVE','PROSPECTIVE')),
      protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT, protocol_hash CHAR(64) NOT NULL,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT, model_hash CHAR(64) NOT NULL,
      partition_plan_version_id UUID NOT NULL REFERENCES public.gdss_partition_plan_version(id) ON DELETE RESTRICT, partition_plan_hash CHAR(64) NOT NULL,
      snapshot_id UUID NOT NULL REFERENCES public.gdss_dataset_snapshot(id) ON DELETE RESTRICT, snapshot_hash CHAR(64) NOT NULL,
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT, validity_domain_hash CHAR(64) NOT NULL,
      holdout_id UUID NULL REFERENCES public.gdss_governed_holdout(id) ON DELETE RESTRICT,
      holdout_evaluation_reference_id UUID NULL REFERENCES public.gdss_holdout_evaluation_reference(id) ON DELETE RESTRICT,
      independence_state TEXT NOT NULL CHECK(independence_state IN('INDEPENDENT','INDEPENDENCE_UNKNOWN','INDEPENDENCE_COMPROMISED')),
      run_content JSONB NOT NULL, canonical_content TEXT NOT NULL, content_hash CHAR(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'),
      idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      started_at TIMESTAMPTZ NULL, completed_at TIMESTAMPTZ NULL, failed_at TIMESTAMPTZ NULL, invalidated_at TIMESTAMPTZ NULL,
      UNIQUE(project_id,idempotency_key), UNIQUE(project_id,content_hash), UNIQUE(id,project_id),
      CHECK((holdout_id IS NULL)=(holdout_evaluation_reference_id IS NULL)));
    CREATE TABLE public.gdss_validation_run_event(
      id BIGSERIAL PRIMARY KEY, run_id UUID NOT NULL REFERENCES public.gdss_validation_run(id) ON DELETE RESTRICT, sequence INTEGER NOT NULL,
      from_status TEXT NULL, to_status TEXT NOT NULL CHECK(to_status IN('CREATED','READY','RUNNING','COMPLETED','FAILED','INVALIDATED')),
      actor TEXT NOT NULL, reason TEXT NOT NULL, idempotency_key TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(run_id,sequence), UNIQUE(run_id,idempotency_key));
    CREATE TABLE public.gdss_prediction_record(
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, validation_run_id UUID NOT NULL,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT, model_content_hash CHAR(64) NOT NULL,
      target_key TEXT NOT NULL, forecast_origin TIMESTAMPTZ NOT NULL, horizon_key TEXT NOT NULL, horizon_duration NUMERIC NOT NULL CHECK(horizon_duration>0),
      horizon_unit_key TEXT NOT NULL, horizon_unit_revision INTEGER NOT NULL CHECK(horizon_unit_revision>0), predicted_value DOUBLE PRECISION NOT NULL,
      predicted_unit_key TEXT NOT NULL, predicted_unit_revision INTEGER NOT NULL CHECK(predicted_unit_revision>0), input_snapshot_hash CHAR(64) NOT NULL,
      parameter_snapshot_hash CHAR(64) NOT NULL, boundary_condition_hash CHAR(64) NOT NULL,
      prediction_mode TEXT NOT NULL CHECK(prediction_mode IN('RETROSPECTIVE','PSEUDO_PROSPECTIVE','PROSPECTIVE')),
      trajectory_reference TEXT NULL, trajectory_hash CHAR(64) NULL, prediction_content JSONB NOT NULL, canonical_content TEXT NOT NULL,
      content_hash CHAR(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'), idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), FOREIGN KEY(validation_run_id,project_id) REFERENCES public.gdss_validation_run(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,content_hash), UNIQUE(validation_run_id,idempotency_key), UNIQUE(id,project_id), CHECK((trajectory_reference IS NULL)=(trajectory_hash IS NULL)));
    CREATE TABLE public.gdss_prediction_commitment(
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, prediction_id UUID NOT NULL,
      prediction_hash CHAR(64) NOT NULL, commitment_hash CHAR(64) NOT NULL CHECK(commitment_hash~'^[0-9a-f]{64}$'),
      committed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), trust_class TEXT NOT NULL CHECK(trust_class='PLATFORM_PROSPECTIVE'),
      actor TEXT NOT NULL, audit_reference TEXT NOT NULL, idempotency_key TEXT NOT NULL,
      FOREIGN KEY(prediction_id,project_id) REFERENCES public.gdss_prediction_record(id,project_id) ON DELETE RESTRICT,
      UNIQUE(prediction_id), UNIQUE(project_id,commitment_hash), UNIQUE(project_id,idempotency_key));
    CREATE TABLE public.gdss_observation_reference(
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      observation_identity TEXT NOT NULL, source TEXT NOT NULL, target_key TEXT NOT NULL, observed_value DOUBLE PRECISION NOT NULL,
      unit_key TEXT NOT NULL, unit_revision INTEGER NOT NULL CHECK(unit_revision>0), measurement_time TIMESTAMPTZ NULL,
      availability_time TIMESTAMPTZ NULL, ingestion_time TIMESTAMPTZ NULL, source_content_hash CHAR(64) NOT NULL,
      quality_provenance_reference TEXT NULL, successor_of_id UUID NULL REFERENCES public.gdss_observation_reference(id) ON DELETE RESTRICT,
      reference_content JSONB NOT NULL, canonical_content TEXT NOT NULL, content_hash CHAR(64) NOT NULL,
      idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_prediction_observation_pair(
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, prediction_id UUID NOT NULL, observation_reference_id UUID NOT NULL,
      target_key TEXT NOT NULL, horizon_key TEXT NOT NULL, pairing_rule TEXT NOT NULL CHECK(pairing_rule IN('EXACT_TIMESTAMP','NEAREST_WITHIN_TOLERANCE','WINDOW_AGGREGATE','EXACT_EVENT_ID')),
      tolerance NUMERIC NULL CHECK(tolerance IS NULL OR tolerance>=0), tolerance_unit_key TEXT NULL, tolerance_unit_revision INTEGER NULL,
      directionality TEXT NULL CHECK(directionality IS NULL OR directionality IN('BIDIRECTIONAL','BEFORE_ONLY','AFTER_ONLY')),
      aggregate_identity TEXT NULL, conversion_identity TEXT NULL, conversion_version TEXT NULL, pairing_contract JSONB NOT NULL,
      pair_hash CHAR(64) NOT NULL, pairing_time TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL,
      FOREIGN KEY(prediction_id,project_id) REFERENCES public.gdss_prediction_record(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(observation_reference_id,project_id) REFERENCES public.gdss_observation_reference(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,pair_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_pair_integrity_assessment(
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, pair_id UUID NOT NULL,
      state TEXT NOT NULL CHECK(state IN('PASS','TEMPORAL_INTEGRITY_UNKNOWN','PREDICTION_AFTER_OBSERVATION','TARGET_MISMATCH','HORIZON_MISMATCH','UNIT_MISMATCH','PAIRING_RULE_VIOLATION','OBSERVATION_NOT_ELIGIBLE','INVALIDATED')),
      details JSONB NOT NULL, integrity_hash CHAR(64) NOT NULL, assessed_by TEXT NOT NULL, assessed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(pair_id,project_id) REFERENCES public.gdss_prediction_observation_pair(id,project_id) ON DELETE RESTRICT,
      UNIQUE(pair_id), UNIQUE(project_id,integrity_hash));
    CREATE TABLE public.gdss_prediction_pair_set(
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      target_key TEXT NOT NULL, horizon_key TEXT NOT NULL, scope TEXT NOT NULL, pair_set_content JSONB NOT NULL, canonical_content TEXT NOT NULL,
      pair_set_hash CHAR(64) NOT NULL, idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(project_id,pair_set_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_prediction_pair_set_member(
      pair_set_id UUID NOT NULL REFERENCES public.gdss_prediction_pair_set(id) ON DELETE RESTRICT,
      pair_id UUID NOT NULL REFERENCES public.gdss_prediction_observation_pair(id) ON DELETE RESTRICT, pair_hash CHAR(64) NOT NULL,
      ordinal INTEGER NOT NULL CHECK(ordinal>=0), PRIMARY KEY(pair_set_id,pair_id), UNIQUE(pair_set_id,ordinal));

    CREATE FUNCTION public.gdss006c_reject_mutation() RETURNS TRIGGER AS $$BEGIN RAISE EXCEPTION 'GDSS-006C immutable evidence'; END;$$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006c_guard_run_binding() RETURNS TRIGGER AS $$DECLARE pp UUID; ph TEXT; ps TEXT; sid UUID; sh TEXT; sm BOOLEAN; prj UUID; prh TEXT; prs TEXT; mid UUID; mh TEXT; did UUID; dh TEXT; hp UUID; hs TEXT; hi TEXT; he UUID; BEGIN
      SELECT i.project_id,v.content_hash,v.status,v.snapshot_id INTO pp,ph,ps,sid FROM public.gdss_partition_plan_version v JOIN public.gdss_partition_plan_identity i ON i.id=v.partition_identity_id WHERE v.id=NEW.partition_plan_version_id;
      SELECT project_id,snapshot_hash,materialized INTO hp,sh,sm FROM public.gdss_dataset_snapshot WHERE id=NEW.snapshot_id;
      SELECT i.project_id,p.content_hash,p.status,p.model_version_id,p.model_content_hash,p.validity_domain_version_id,p.validity_domain_hash INTO prj,prh,prs,mid,mh,did,dh FROM public.gdss_validation_protocol_version p JOIN public.gdss_validation_protocol_identity i ON i.id=p.protocol_identity_id WHERE p.id=NEW.protocol_version_id;
      IF NEW.holdout_id IS NOT NULL THEN SELECT project_id,state,independence_state INTO hp,hs,hi FROM public.gdss_governed_holdout WHERE id=NEW.holdout_id; SELECT holdout_id INTO he FROM public.gdss_holdout_evaluation_reference WHERE id=NEW.holdout_evaluation_reference_id; IF hp IS DISTINCT FROM NEW.project_id OR he IS DISTINCT FROM NEW.holdout_id OR hs<>'OPENED_FOR_EVALUATION' OR hi<>'INDEPENDENT' THEN RAISE EXCEPTION 'VALIDATION_RUN_INDEPENDENCE_NOT_ELIGIBLE'; END IF; END IF;
      IF pp IS DISTINCT FROM NEW.project_id OR hp IS DISTINCT FROM NEW.project_id OR prj IS DISTINCT FROM NEW.project_id OR ps<>'PUBLISHED' OR NOT sm OR prs<>'SEALED' OR ph IS DISTINCT FROM NEW.partition_plan_hash OR sh IS DISTINCT FROM NEW.snapshot_hash OR prh IS DISTINCT FROM NEW.protocol_hash OR mid IS DISTINCT FROM NEW.model_version_id OR mh IS DISTINCT FROM NEW.model_hash OR did IS DISTINCT FROM NEW.validity_domain_version_id OR dh IS DISTINCT FROM NEW.validity_domain_hash OR sid IS DISTINCT FROM NEW.snapshot_id THEN RAISE EXCEPTION 'VALIDATION_RUN_BINDING_INVALID'; END IF; RETURN NEW; END;$$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006c_guard_run_event() RETURNS TRIGGER AS $$DECLARE seq INTEGER; prior TEXT; BEGIN SELECT sequence,to_status INTO seq,prior FROM public.gdss_validation_run_event WHERE run_id=NEW.run_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE; IF seq IS NULL THEN IF NEW.sequence<>1 OR NEW.from_status IS NOT NULL OR NEW.to_status<>'CREATED' THEN RAISE EXCEPTION 'Invalid run initial lifecycle'; END IF; ELSIF NEW.sequence<>seq+1 OR NEW.from_status IS DISTINCT FROM prior OR NOT((prior='CREATED'AND NEW.to_status IN('READY','FAILED','INVALIDATED'))OR(prior='READY'AND NEW.to_status IN('RUNNING','FAILED','INVALIDATED'))OR(prior='RUNNING'AND NEW.to_status IN('COMPLETED','FAILED','INVALIDATED'))OR(prior IN('COMPLETED','FAILED')AND NEW.to_status='INVALIDATED')) THEN RAISE EXCEPTION 'VALIDATION_RUN_NOT_READY'; END IF; UPDATE public.gdss_validation_run SET status=NEW.to_status,started_at=CASE WHEN NEW.to_status='RUNNING'THEN clock_timestamp()ELSE started_at END,completed_at=CASE WHEN NEW.to_status='COMPLETED'THEN clock_timestamp()ELSE completed_at END,failed_at=CASE WHEN NEW.to_status='FAILED'THEN clock_timestamp()ELSE failed_at END,invalidated_at=CASE WHEN NEW.to_status='INVALIDATED'THEN clock_timestamp()ELSE invalidated_at END WHERE id=NEW.run_id; RETURN NEW; END;$$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006c_guard_run_row() RETURNS TRIGGER AS $$BEGIN IF pg_trigger_depth()>1 THEN RETURN NEW; END IF; RAISE EXCEPTION 'Validation run immutable; lifecycle event required'; END;$$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006c_guard_prediction() RETURNS TRIGGER AS $$DECLARE rid UUID; rp UUID; rm UUID; rh TEXT; rs TEXT; mode TEXT; BEGIN IF TG_OP='INSERT' THEN SELECT id,project_id,model_version_id,model_hash,status,run_mode INTO rid,rp,rm,rh,rs,mode FROM public.gdss_validation_run WHERE id=NEW.validation_run_id; IF rp IS DISTINCT FROM NEW.project_id OR rm IS DISTINCT FROM NEW.model_version_id OR rh IS DISTINCT FROM NEW.model_content_hash THEN RAISE EXCEPTION 'MODEL_VERSION_MISMATCH'; END IF; IF rs<>'RUNNING' THEN RAISE EXCEPTION 'VALIDATION_RUN_NOT_READY'; END IF; IF mode IS DISTINCT FROM NEW.prediction_mode THEN RAISE EXCEPTION 'VALIDATION_RUN_BINDING_INVALID'; END IF; RETURN NEW; END IF; IF EXISTS(SELECT 1 FROM public.gdss_prediction_commitment WHERE prediction_id=OLD.id) THEN RAISE EXCEPTION 'PREDICTION_IMMUTABLE'; END IF; RETURN COALESCE(NEW,OLD); END;$$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006c_guard_commitment() RETURNS TRIGGER AS $$DECLARE ph TEXT; pp UUID; expected TEXT; BEGIN SELECT content_hash,project_id INTO ph,pp FROM public.gdss_prediction_record WHERE id=NEW.prediction_id FOR UPDATE; expected:=encode(digest(convert_to('gdss006:prediction-commitment:v1','UTF8')||decode('00','hex')||convert_to(format('{"predictionHash":"%s","trustClass":"PLATFORM_PROSPECTIVE"}',ph),'UTF8'),'sha256'),'hex'); IF pp IS DISTINCT FROM NEW.project_id OR ph IS DISTINCT FROM NEW.prediction_hash OR expected IS DISTINCT FROM NEW.commitment_hash THEN RAISE EXCEPTION 'PREDICTION_COMMITMENT_TAMPERED'; END IF; NEW.committed_at:=clock_timestamp(); RETURN NEW; END;$$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006c_guard_pair() RETURNS TRIGGER AS $$DECLARE pp UUID; pt TEXT; ph TEXT; pu TEXT; pur INTEGER; op UUID; ot TEXT; ou TEXT; our INTEGER; BEGIN SELECT project_id,target_key,horizon_key,predicted_unit_key,predicted_unit_revision INTO pp,pt,ph,pu,pur FROM public.gdss_prediction_record WHERE id=NEW.prediction_id; SELECT project_id,target_key,unit_key,unit_revision INTO op,ot,ou,our FROM public.gdss_observation_reference WHERE id=NEW.observation_reference_id; IF pp IS DISTINCT FROM NEW.project_id OR op IS DISTINCT FROM NEW.project_id THEN RAISE EXCEPTION 'CROSS_PROJECT_PAIRING'; END IF; IF pt IS DISTINCT FROM ot OR pt IS DISTINCT FROM NEW.target_key THEN RAISE EXCEPTION 'TARGET_MISMATCH'; END IF; IF ph IS DISTINCT FROM NEW.horizon_key THEN RAISE EXCEPTION 'HORIZON_MISMATCH'; END IF; IF (pu IS DISTINCT FROM ou OR pur IS DISTINCT FROM our) AND NEW.conversion_identity IS NULL THEN RAISE EXCEPTION 'UNIT_MISMATCH'; END IF; RETURN NEW; END;$$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006c_guard_pair_member() RETURNS TRIGGER AS $$DECLARE sp UUID; pp UUID; st TEXT; sh TEXT; pt TEXT; ph TEXT; actual TEXT; BEGIN SELECT project_id,target_key,horizon_key INTO sp,st,sh FROM public.gdss_prediction_pair_set WHERE id=NEW.pair_set_id; SELECT project_id,target_key,horizon_key,pair_hash INTO pp,pt,ph,actual FROM public.gdss_prediction_observation_pair WHERE id=NEW.pair_id; IF sp IS DISTINCT FROM pp THEN RAISE EXCEPTION 'CROSS_PROJECT_PAIRING'; END IF; IF st IS DISTINCT FROM pt THEN RAISE EXCEPTION 'TARGET_MISMATCH'; END IF; IF sh IS DISTINCT FROM ph THEN RAISE EXCEPTION 'HORIZON_MISMATCH'; END IF; IF actual IS DISTINCT FROM NEW.pair_hash THEN RAISE EXCEPTION 'PAIRING_RULE_VIOLATION'; END IF; RETURN NEW; END;$$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss006c_run_binding BEFORE INSERT ON public.gdss_validation_run FOR EACH ROW EXECUTE FUNCTION public.gdss006c_guard_run_binding();
    CREATE TRIGGER trg_gdss006c_run_event BEFORE INSERT ON public.gdss_validation_run_event FOR EACH ROW EXECUTE FUNCTION public.gdss006c_guard_run_event();
    CREATE TRIGGER trg_gdss006c_run_row BEFORE UPDATE OR DELETE ON public.gdss_validation_run FOR EACH ROW EXECUTE FUNCTION public.gdss006c_guard_run_row();
    CREATE TRIGGER trg_gdss006c_prediction BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_prediction_record FOR EACH ROW EXECUTE FUNCTION public.gdss006c_guard_prediction();
    CREATE TRIGGER trg_gdss006c_commitment_insert BEFORE INSERT ON public.gdss_prediction_commitment FOR EACH ROW EXECUTE FUNCTION public.gdss006c_guard_commitment();
    CREATE TRIGGER trg_gdss006c_commitment_history BEFORE UPDATE OR DELETE ON public.gdss_prediction_commitment FOR EACH ROW EXECUTE FUNCTION public.gdss006c_reject_mutation();
    CREATE TRIGGER trg_gdss006c_observation_history BEFORE UPDATE OR DELETE ON public.gdss_observation_reference FOR EACH ROW EXECUTE FUNCTION public.gdss006c_reject_mutation();
    CREATE TRIGGER trg_gdss006c_pair_insert BEFORE INSERT ON public.gdss_prediction_observation_pair FOR EACH ROW EXECUTE FUNCTION public.gdss006c_guard_pair();
    CREATE TRIGGER trg_gdss006c_pair_history BEFORE UPDATE OR DELETE ON public.gdss_prediction_observation_pair FOR EACH ROW EXECUTE FUNCTION public.gdss006c_reject_mutation();
    CREATE TRIGGER trg_gdss006c_integrity_history BEFORE UPDATE OR DELETE ON public.gdss_pair_integrity_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006c_reject_mutation();
    CREATE TRIGGER trg_gdss006c_pair_set_history BEFORE UPDATE OR DELETE ON public.gdss_prediction_pair_set FOR EACH ROW EXECUTE FUNCTION public.gdss006c_reject_mutation();
    CREATE TRIGGER trg_gdss006c_pair_set_member BEFORE INSERT ON public.gdss_prediction_pair_set_member FOR EACH ROW EXECUTE FUNCTION public.gdss006c_guard_pair_member();
    CREATE TRIGGER trg_gdss006c_pair_set_member_history BEFORE UPDATE OR DELETE ON public.gdss_prediction_pair_set_member FOR EACH ROW EXECUTE FUNCTION public.gdss006c_reject_mutation();
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE IF EXISTS public.gdss_prediction_pair_set_member,public.gdss_prediction_pair_set,public.gdss_pair_integrity_assessment,public.gdss_prediction_observation_pair,public.gdss_observation_reference,public.gdss_prediction_commitment,public.gdss_prediction_record,public.gdss_validation_run_event,public.gdss_validation_run CASCADE;
    DROP FUNCTION IF EXISTS public.gdss006c_guard_pair_member(),public.gdss006c_guard_pair(),public.gdss006c_guard_commitment(),public.gdss006c_guard_prediction(),public.gdss006c_guard_run_row(),public.gdss006c_guard_run_event(),public.gdss006c_guard_run_binding(),public.gdss006c_reject_mutation() CASCADE;
    """)
