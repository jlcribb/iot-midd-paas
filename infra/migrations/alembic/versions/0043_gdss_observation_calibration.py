"""Governed observation, calibration and model adequacy. Revision 0043."""
from alembic import op

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_observation_dataset_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      dataset_key TEXT NOT NULL CHECK(length(btrim(dataset_key)) BETWEEN 1 AND 128), created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(project_id,dataset_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_observation_dataset_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), dataset_identity_id UUID NOT NULL REFERENCES public.gdss_observation_dataset_identity(id) ON DELETE RESTRICT,
      version_number INTEGER NOT NULL CHECK(version_number>0), predecessor_version_id UUID NULL REFERENCES public.gdss_observation_dataset_version(id) ON DELETE RESTRICT,
      epistemic_origin TEXT NOT NULL CHECK(epistemic_origin IN ('PHYSICAL_OBSERVATION','SYNTHETIC_OBSERVATION')),
      state TEXT NOT NULL DEFAULT 'DRAFT' CHECK(state IN ('DRAFT','VALIDATED','PUBLISHED','DEPRECATED')),
      time_contract TEXT NOT NULL CHECK(time_contract='GDSS_OBSERVATION_TIME_V1'), unit_contract TEXT NOT NULL CHECK(unit_contract='GDSS_UNIT_CONVERSION_V2'),
      dataset_hash CHAR(64) NULL CHECK(dataset_hash IS NULL OR dataset_hash ~ '^[0-9a-f]{64}$'), artifact_id UUID NULL,
      created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), validated_by TEXT NULL, validated_at TIMESTAMPTZ NULL,
      published_by TEXT NULL, published_at TIMESTAMPTZ NULL, deprecated_by TEXT NULL, deprecated_at TIMESTAMPTZ NULL,
      UNIQUE(dataset_identity_id,version_number), UNIQUE(dataset_identity_id,id));
    CREATE UNIQUE INDEX gdss_observation_dataset_hash_uq ON public.gdss_observation_dataset_version(dataset_hash) WHERE dataset_hash IS NOT NULL;
    CREATE TABLE public.gdss_observation_source_reference (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), dataset_version_id UUID NOT NULL REFERENCES public.gdss_observation_dataset_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 15), source_type TEXT NOT NULL CHECK(source_type IN ('GOVERNED_FILE_ARTIFACT','GOVERNED_DATABASE_SNAPSHOT','SYNTHETIC_FIXTURE')),
      source_identity TEXT NOT NULL, source_artifact_identity TEXT NOT NULL, source_content_sha256 CHAR(64) NOT NULL CHECK(source_content_sha256 ~ '^[0-9a-f]{64}$'), channel_identity TEXT NOT NULL,
      physical_system_identity TEXT NULL, instrument_identity TEXT NULL, instrument_calibration_metadata JSONB NULL,
      parser_contract TEXT NULL, query_contract TEXT NULL, generator_identity TEXT NULL, generator_version TEXT NULL,
      generator_content_hash CHAR(64) NULL CHECK(generator_content_hash IS NULL OR generator_content_hash ~ '^[0-9a-f]{64}$'), seed TEXT NULL,
      provenance JSONB NOT NULL DEFAULT '{}' CHECK(jsonb_typeof(provenance)='object'),
      UNIQUE(dataset_version_id,ordinal), UNIQUE(dataset_version_id,source_identity), UNIQUE(id,dataset_version_id),
      CHECK((source_type IN ('GOVERNED_FILE_ARTIFACT','GOVERNED_DATABASE_SNAPSHOT') AND length(btrim(physical_system_identity))>0 AND generator_identity IS NULL AND generator_version IS NULL AND generator_content_hash IS NULL)
         OR (source_type='SYNTHETIC_FIXTURE' AND physical_system_identity IS NULL AND length(btrim(generator_identity))>0 AND length(btrim(generator_version))>0 AND generator_content_hash IS NOT NULL)));
    CREATE TABLE public.gdss_observation_series (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), dataset_version_id UUID NOT NULL REFERENCES public.gdss_observation_dataset_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 7), series_key TEXT NOT NULL, quantity_identity TEXT NOT NULL,
      dimension JSONB NOT NULL CHECK(jsonb_typeof(dimension)='array' AND jsonb_array_length(dimension)=7), unit_identity JSONB NOT NULL CHECK(jsonb_typeof(unit_identity)='object'),
      quantity_semantics TEXT NOT NULL CHECK(quantity_semantics IN ('ABSOLUTE','INTERVAL')), uncertainty_default JSONB NOT NULL DEFAULT '{"mode":"UNKNOWN"}',
      resolution_bits CHAR(16) NULL CHECK(resolution_bits IS NULL OR resolution_bits ~ '^[0-9a-f]{16}$'),
      UNIQUE(dataset_version_id,ordinal), UNIQUE(dataset_version_id,series_key), UNIQUE(id,dataset_version_id));
    CREATE TABLE public.gdss_observation_point (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), series_id UUID NOT NULL REFERENCES public.gdss_observation_series(id) ON DELETE RESTRICT,
      source_reference_id UUID NOT NULL REFERENCES public.gdss_observation_source_reference(id) ON DELETE RESTRICT, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 10000),
      measurement_time_us BIGINT NOT NULL, value_bits CHAR(16) NULL CHECK(value_bits IS NULL OR value_bits ~ '^[0-9a-f]{16}$'),
      quality TEXT NOT NULL CHECK(quality IN ('ACCEPTED','SUSPECT','REJECTED','MISSING','DEVICE_ERROR')),
      uncertainty_mode TEXT NOT NULL CHECK(uncertainty_mode IN ('UNKNOWN','ABSOLUTE_BOUND','RELATIVE_BOUND')), uncertainty_bound_bits CHAR(16) NULL,
      resolution_bits CHAR(16) NULL, source_record_identity TEXT NOT NULL, source_record_sha256 CHAR(64) NOT NULL CHECK(source_record_sha256 ~ '^[0-9a-f]{64}$'),
      diagnostic_code TEXT NULL, diagnostic_details JSONB NOT NULL DEFAULT '{}',
      UNIQUE(series_id,ordinal), UNIQUE(series_id,measurement_time_us), UNIQUE(series_id,source_record_identity),
      CHECK((quality='ACCEPTED' AND value_bits IS NOT NULL) OR quality<>'ACCEPTED'), CHECK((quality='MISSING' AND value_bits IS NULL) OR quality<>'MISSING'),
      CHECK((uncertainty_mode='UNKNOWN' AND uncertainty_bound_bits IS NULL) OR (uncertainty_mode<>'UNKNOWN' AND uncertainty_bound_bits IS NOT NULL)));
    CREATE TABLE public.gdss_observation_dataset_lifecycle_event (
      id BIGSERIAL PRIMARY KEY, dataset_version_id UUID NOT NULL REFERENCES public.gdss_observation_dataset_version(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 4), from_state TEXT NULL, to_state TEXT NOT NULL CHECK(to_state IN ('DRAFT','VALIDATED','PUBLISHED','DEPRECATED')),
      actor TEXT NOT NULL, reason TEXT NOT NULL, resulting_dataset_hash CHAR(64) NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(dataset_version_id,sequence));

    CREATE TABLE public.gdss_calibration_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      calibration_key TEXT NOT NULL CHECK(length(btrim(calibration_key)) BETWEEN 1 AND 128), created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(project_id,calibration_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_calibration_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), calibration_identity_id UUID NOT NULL REFERENCES public.gdss_calibration_identity(id) ON DELETE RESTRICT,
      version_number INTEGER NOT NULL CHECK(version_number>0), predecessor_version_id UUID NULL REFERENCES public.gdss_calibration_version(id) ON DELETE RESTRICT,
      state TEXT NOT NULL DEFAULT 'DRAFT' CHECK(state IN ('DRAFT','VALIDATED','PUBLISHED','DEPRECATED')),
      model_identity_id UUID NOT NULL REFERENCES public.gdss_identity(id) ON DELETE RESTRICT, model_version_id UUID NOT NULL, model_version_number INTEGER NOT NULL CHECK(model_version_number>0), model_content_hash CHAR(64) NOT NULL CHECK(model_content_hash ~ '^[0-9a-f]{64}$'),
      binding_id UUID NOT NULL REFERENCES public.gdss_dynamic_binding(id) ON DELETE RESTRICT, binding_version_id UUID NOT NULL, binding_version_number INTEGER NOT NULL CHECK(binding_version_number>0), dynamic_binding_hash CHAR(64) NOT NULL CHECK(dynamic_binding_hash ~ '^[0-9a-f]{64}$'),
      objective_version TEXT NOT NULL CHECK(objective_version IN ('RMSE_V1','WEIGHTED_NORMALIZED_MSE_V1')), search_version TEXT NOT NULL CHECK(search_version='FINITE_GRID_SEARCH_V1'),
      alignment_specification JSONB NOT NULL CHECK(jsonb_typeof(alignment_specification)='object'), minimum_matched_count INTEGER NOT NULL CHECK(minimum_matched_count>0), adequacy_criteria JSONB NULL,
      calibration_design_hash CHAR(64) NULL CHECK(calibration_design_hash IS NULL OR calibration_design_hash ~ '^[0-9a-f]{64}$'),
      resource_profile_version TEXT NOT NULL CHECK(resource_profile_version='GDSS_CALIBRATION_LIMITS_V1'), recovery_profile_version TEXT NOT NULL CHECK(recovery_profile_version='GDSS_CALIBRATION_RECOVERY_V1'),
      created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), validated_by TEXT NULL, validated_at TIMESTAMPTZ NULL, published_by TEXT NULL, published_at TIMESTAMPTZ NULL, deprecated_by TEXT NULL, deprecated_at TIMESTAMPTZ NULL,
      FOREIGN KEY(model_identity_id,model_version_id) REFERENCES public.gdss_version(identity_id,id) ON DELETE RESTRICT,
      FOREIGN KEY(binding_version_id,model_version_id) REFERENCES public.gdss_dynamic_binding_version(id,model_version_id) ON DELETE RESTRICT,
      UNIQUE(calibration_identity_id,version_number), UNIQUE(calibration_identity_id,id));
    CREATE UNIQUE INDEX gdss_calibration_design_hash_uq ON public.gdss_calibration_version(calibration_design_hash) WHERE calibration_design_hash IS NOT NULL;
    CREATE TABLE public.gdss_calibration_dataset_assignment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), calibration_version_id UUID NOT NULL REFERENCES public.gdss_calibration_version(id) ON DELETE RESTRICT,
      dataset_version_id UUID NOT NULL REFERENCES public.gdss_observation_dataset_version(id) ON DELETE RESTRICT, ordinal INTEGER NOT NULL CHECK(ordinal>=0),
      role TEXT NOT NULL CHECK(role IN ('CALIBRATION','VALIDATION','HOLDOUT','EXPLORATORY')), assignment_weight_bits CHAR(16) NULL,
      UNIQUE(calibration_version_id,ordinal), UNIQUE(calibration_version_id,dataset_version_id,role), UNIQUE(id,calibration_version_id));
    CREATE TABLE public.gdss_calibration_series_mapping (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), dataset_assignment_id UUID NOT NULL REFERENCES public.gdss_calibration_dataset_assignment(id) ON DELETE RESTRICT,
      observation_series_id UUID NOT NULL REFERENCES public.gdss_observation_series(id) ON DELETE RESTRICT, mapping_key TEXT NOT NULL, target_quantity_identity TEXT NOT NULL,
      source_unit JSONB NOT NULL, target_unit JSONB NOT NULL, dimension JSONB NOT NULL CHECK(jsonb_typeof(dimension)='array' AND jsonb_array_length(dimension)=7),
      quantity_semantics TEXT NOT NULL CHECK(quantity_semantics IN ('ABSOLUTE','INTERVAL')), conversion_contract TEXT NOT NULL CHECK(conversion_contract='GDSS_UNIT_CONVERSION_V2'),
      included BOOLEAN NOT NULL, normalization_scale_bits CHAR(16) NULL, weight_bits CHAR(16) NULL,
      UNIQUE(dataset_assignment_id,mapping_key), UNIQUE(dataset_assignment_id,observation_series_id));
    CREATE TABLE public.gdss_calibration_parameter (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), calibration_version_id UUID NOT NULL REFERENCES public.gdss_calibration_version(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 35), parameter_identity TEXT NOT NULL, base_value_bits CHAR(16) NOT NULL, unit_identity JSONB NOT NULL,
      lower_bound_bits CHAR(16) NOT NULL, upper_bound_bits CHAR(16) NOT NULL, mode TEXT NOT NULL CHECK(mode IN ('CALIBRATED','FIXED')), fixed_value_bits CHAR(16) NULL,
      candidate_values JSONB NULL, candidate_count INTEGER NOT NULL CHECK(candidate_count BETWEEN 1 AND 16), axis_hash CHAR(64) NOT NULL CHECK(axis_hash ~ '^[0-9a-f]{64}$'),
      UNIQUE(calibration_version_id,ordinal), UNIQUE(calibration_version_id,parameter_identity),
      CHECK((mode='CALIBRATED' AND candidate_values IS NOT NULL AND fixed_value_bits IS NULL) OR (mode='FIXED' AND candidate_values IS NULL AND fixed_value_bits IS NOT NULL AND candidate_count=1)));
    CREATE TABLE public.gdss_calibration_lifecycle_event (
      id BIGSERIAL PRIMARY KEY, calibration_version_id UUID NOT NULL REFERENCES public.gdss_calibration_version(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 4), from_state TEXT NULL, to_state TEXT NOT NULL CHECK(to_state IN ('DRAFT','VALIDATED','PUBLISHED','DEPRECATED')),
      actor TEXT NOT NULL, reason TEXT NOT NULL, resulting_design_hash CHAR(64) NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(calibration_version_id,sequence));

    CREATE TABLE public.gdss_calibration_artifact (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      artifact_kind TEXT NOT NULL CHECK(artifact_kind IN ('GDSS_OBSERVATION_DATASET_ARTIFACT_V1','GDSS_CALIBRATION_MANIFEST_V1','GDSS_CALIBRATION_RESIDUALS_V1','GDSS_CALIBRATION_RESULT_V1')),
      artifact_version INTEGER NOT NULL CHECK(artifact_version=1), media_type TEXT NOT NULL, payload BYTEA NOT NULL,
      byte_length INTEGER NOT NULL CHECK(byte_length BETWEEN 1 AND 67108864), content_sha256 CHAR(64) NOT NULL CHECK(content_sha256 ~ '^[0-9a-f]{64}$'),
      semantic_hash CHAR(64) NULL CHECK(semantic_hash IS NULL OR semantic_hash ~ '^[0-9a-f]{64}$'), created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(project_id,content_sha256,artifact_kind,artifact_version), UNIQUE(id,project_id));
    ALTER TABLE public.gdss_observation_dataset_version ADD CONSTRAINT gdss_observation_dataset_artifact_fk
      FOREIGN KEY(artifact_id) REFERENCES public.gdss_calibration_artifact(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE public.gdss_calibration_execution_attempt (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      calibration_version_id UUID NOT NULL REFERENCES public.gdss_calibration_version(id) ON DELETE RESTRICT, attempt_number INTEGER NOT NULL CHECK(attempt_number>0), idempotency_key TEXT NOT NULL,
      calibration_design_hash CHAR(64) NOT NULL CHECK(calibration_design_hash ~ '^[0-9a-f]{64}$'), model_content_hash CHAR(64) NOT NULL CHECK(model_content_hash ~ '^[0-9a-f]{64}$'),
      ordered_dataset_hashes JSONB NOT NULL CHECK(jsonb_typeof(ordered_dataset_hashes)='array'), alignment_hash CHAR(64) NOT NULL CHECK(alignment_hash ~ '^[0-9a-f]{64}$'),
      manifest_artifact_id UUID NOT NULL REFERENCES public.gdss_calibration_artifact(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
      requested_by TEXT NOT NULL, requested_at TIMESTAMPTZ NOT NULL DEFAULT now(), abort_requested BOOLEAN NOT NULL DEFAULT FALSE,
      abort_requested_by TEXT NULL, abort_requested_at TIMESTAMPTZ NULL, abort_reason TEXT NULL,
      terminal_state TEXT NULL CHECK(terminal_state IS NULL OR terminal_state IN ('COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','ABORTED')), terminal_at TIMESTAMPTZ NULL,
      UNIQUE(calibration_version_id,attempt_number), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_calibration_execution_event (
      id BIGSERIAL PRIMARY KEY, attempt_id UUID NOT NULL REFERENCES public.gdss_calibration_execution_attempt(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence>0), event_class TEXT NOT NULL CHECK(event_class IN ('COMPUTATIONAL_EXECUTION_EVENT','GOVERNANCE_PUBLICATION_EVENT')),
      event_type TEXT NOT NULL CHECK(event_type IN ('ACCEPTED','RUNNING','COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','ABORTED','RESULT_PUBLISHED')),
      actor TEXT NOT NULL, reason TEXT NULL, result_artifact_id UUID NULL REFERENCES public.gdss_calibration_artifact(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
      result_hash CHAR(64) NULL CHECK(result_hash IS NULL OR result_hash ~ '^[0-9a-f]{64}$'), audit_correlation_identity TEXT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(attempt_id,sequence));
    CREATE UNIQUE INDEX gdss_calibration_attempt_terminal_uq ON public.gdss_calibration_execution_event(attempt_id) WHERE event_type IN ('COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','ABORTED');
    CREATE UNIQUE INDEX gdss_calibration_result_publication_uq ON public.gdss_calibration_execution_event(attempt_id) WHERE event_type='RESULT_PUBLISHED';
    CREATE TABLE public.gdss_calibration_candidate_evaluation (
      id BIGSERIAL PRIMARY KEY, attempt_id UUID NOT NULL REFERENCES public.gdss_calibration_execution_attempt(id) ON DELETE RESTRICT,
      candidate_ordinal INTEGER NOT NULL CHECK(candidate_ordinal BETWEEN 0 AND 255), sequence INTEGER NOT NULL CHECK(sequence>0),
      parameter_vector_hash CHAR(64) NOT NULL CHECK(parameter_vector_hash ~ '^[0-9a-f]{64}$'), canonical_vector JSONB NOT NULL CHECK(jsonb_typeof(canonical_vector)='object'),
      state TEXT NOT NULL CHECK(state IN ('PENDING','CLAIMED','DISPATCHED','SUCCEEDED','INFEASIBLE','SIMULATION_FAILED','NOT_DISPATCHED_ABORTED')),
      claim_token UUID NULL, worker_identity TEXT NULL, lease_expires_at TIMESTAMPTZ NULL, dispatch_attempt INTEGER NOT NULL DEFAULT 0 CHECK(dispatch_attempt BETWEEN 0 AND 3),
      gdss_simulation_attempt_id UUID NULL REFERENCES public.gdss_simulation_attempt(id) ON DELETE RESTRICT,
      objective_bits CHAR(16) NULL CHECK(objective_bits IS NULL OR objective_bits ~ '^[0-9a-f]{16}$'), failure_code TEXT NULL,
      trajectory_hash CHAR(64) NULL REFERENCES public.gdss_simulation_artifact(hash) ON DELETE RESTRICT,
      residual_artifact_id UUID NULL REFERENCES public.gdss_calibration_artifact(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(attempt_id,candidate_ordinal,sequence));
    CREATE UNIQUE INDEX gdss_calibration_candidate_terminal_uq ON public.gdss_calibration_candidate_evaluation(attempt_id,candidate_ordinal) WHERE state IN ('SUCCEEDED','INFEASIBLE','SIMULATION_FAILED','NOT_DISPATCHED_ABORTED');
    CREATE INDEX gdss_calibration_simulation_attachment_idx ON public.gdss_calibration_candidate_evaluation(gdss_simulation_attempt_id) WHERE gdss_simulation_attempt_id IS NOT NULL;
    CREATE TABLE public.gdss_calibration_parameter_estimate_set (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), attempt_id UUID NOT NULL UNIQUE REFERENCES public.gdss_calibration_execution_attempt(id) ON DELETE RESTRICT,
      selected_candidate_ordinal INTEGER NOT NULL, selected_parameter_vector_hash CHAR(64) NOT NULL, objective_version TEXT NOT NULL CHECK(objective_version IN ('RMSE_V1','WEIGHTED_NORMALIZED_MSE_V1')),
      objective_bits CHAR(16) NOT NULL, model_binding_evidence JSONB NOT NULL, dataset_alignment_evidence JSONB NOT NULL, simulation_evidence JSONB NOT NULL,
      estimate_set_hash CHAR(64) NOT NULL CHECK(estimate_set_hash ~ '^[0-9a-f]{64}$'), tie_rule TEXT NOT NULL CHECK(tie_rule='LOWEST_CANDIDATE_ORDINAL'), created_at TIMESTAMPTZ NOT NULL DEFAULT now());
    CREATE TABLE public.gdss_calibration_parameter_estimate (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), estimate_set_id UUID NOT NULL REFERENCES public.gdss_calibration_parameter_estimate_set(id) ON DELETE RESTRICT,
      ordinal INTEGER NOT NULL, parameter_identity TEXT NOT NULL, base_value_bits CHAR(16) NOT NULL, estimated_value_bits CHAR(16) NOT NULL,
      unit_identity JSONB NOT NULL, lower_bound_bits CHAR(16) NOT NULL, upper_bound_bits CHAR(16) NOT NULL, axis_hash CHAR(64) NOT NULL,
      UNIQUE(estimate_set_id,ordinal), UNIQUE(estimate_set_id,parameter_identity));
    CREATE TABLE public.gdss_model_adequacy_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), attempt_id UUID NOT NULL UNIQUE REFERENCES public.gdss_calibration_execution_attempt(id) ON DELETE RESTRICT,
      classification TEXT NOT NULL CHECK(classification IN ('FIT_COMPUTED_NO_ADEQUACY_CLAIM','ACCEPTABLE_UNDER_DECLARED_CRITERIA','POOR_FIT_UNDER_DECLARED_CRITERIA','INSUFFICIENT_EVIDENCE','INCOMPARABLE')),
      criteria JSONB NULL, residual_summary_artifact_id UUID NULL REFERENCES public.gdss_calibration_artifact(id) ON DELETE RESTRICT,
      identifiability TEXT NOT NULL CHECK(identifiability='NOT_ASSESSED'), rationale TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
    CREATE TABLE public.gdss_calibration_estimate_review (
      id BIGSERIAL PRIMARY KEY, estimate_set_id UUID NOT NULL REFERENCES public.gdss_calibration_parameter_estimate_set(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence>0), decision TEXT NOT NULL CHECK(decision IN ('ACCEPT_FOR_SUCCESSOR_PROPOSAL','REJECT')),
      reviewer TEXT NOT NULL, reason TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(estimate_set_id,sequence), UNIQUE(estimate_set_id));
    CREATE TABLE public.gdss_calibration_diagnostic (
      id BIGSERIAL PRIMARY KEY, attempt_id UUID NOT NULL REFERENCES public.gdss_calibration_execution_attempt(id) ON DELETE RESTRICT,
      candidate_ordinal INTEGER NULL, observation_point_id UUID NULL REFERENCES public.gdss_observation_point(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 512), diagnostic_class TEXT NOT NULL CHECK(diagnostic_class IN ('SEMANTIC','OPERATIONAL')),
      stage TEXT NOT NULL, severity TEXT NOT NULL CHECK(severity IN ('INFO','WARNING','ERROR','FATAL')), code TEXT NOT NULL,
      semantic_content_hash CHAR(64) NULL CHECK(semantic_content_hash IS NULL OR semantic_content_hash ~ '^[0-9a-f]{64}$'), details JSONB NOT NULL DEFAULT '{}',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(attempt_id,sequence));

    CREATE FUNCTION public.gdss005_reject_mutation() RETURNS TRIGGER AS $$
    BEGIN RAISE EXCEPTION 'GDSS-005 evidence is append-only'; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_dataset_freeze() RETURNS TRIGGER AS $$
    DECLARE version_id UUID; frozen BOOLEAN;
    BEGIN
      IF pg_trigger_depth()>1 THEN RETURN NEW; END IF;
      IF TG_TABLE_NAME='gdss_observation_dataset_version' THEN version_id:=OLD.id;
      ELSIF TG_TABLE_NAME='gdss_observation_point' THEN SELECT dataset_version_id INTO version_id FROM public.gdss_observation_series WHERE id=OLD.series_id;
      ELSE version_id:=OLD.dataset_version_id; END IF;
      SELECT state<>'DRAFT' OR EXISTS(SELECT 1 FROM public.gdss_calibration_dataset_assignment a JOIN public.gdss_calibration_execution_attempt x ON x.calibration_version_id=a.calibration_version_id WHERE a.dataset_version_id=version_id) INTO frozen FROM public.gdss_observation_dataset_version WHERE id=version_id;
      IF TG_OP='DELETE' OR frozen THEN RAISE EXCEPTION 'GDSS-005 dataset is frozen'; END IF; RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_calibration_freeze() RETURNS TRIGGER AS $$
    DECLARE version_id UUID; frozen BOOLEAN;
    BEGIN
      IF pg_trigger_depth()>1 THEN RETURN NEW; END IF;
      IF TG_TABLE_NAME='gdss_calibration_version' THEN version_id:=OLD.id;
      ELSIF TG_TABLE_NAME='gdss_calibration_series_mapping' THEN SELECT calibration_version_id INTO version_id FROM public.gdss_calibration_dataset_assignment WHERE id=OLD.dataset_assignment_id;
      ELSE version_id:=OLD.calibration_version_id; END IF;
      SELECT state<>'DRAFT' OR EXISTS(SELECT 1 FROM public.gdss_calibration_execution_attempt WHERE calibration_version_id=version_id) INTO frozen FROM public.gdss_calibration_version WHERE id=version_id;
      IF TG_OP='DELETE' OR frozen THEN RAISE EXCEPTION 'GDSS-005 calibration design is frozen'; END IF; RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_lifecycle_transition() RETURNS TRIGGER AS $$
    DECLARE prior_sequence INTEGER; prior_state TEXT;
    BEGIN
      IF TG_TABLE_NAME='gdss_observation_dataset_lifecycle_event' THEN SELECT sequence,to_state INTO prior_sequence,prior_state FROM public.gdss_observation_dataset_lifecycle_event WHERE dataset_version_id=NEW.dataset_version_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE;
      ELSE SELECT sequence,to_state INTO prior_sequence,prior_state FROM public.gdss_calibration_lifecycle_event WHERE calibration_version_id=NEW.calibration_version_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE; END IF;
      IF prior_sequence IS NULL THEN IF NEW.sequence<>1 OR NEW.from_state IS NOT NULL OR NEW.to_state<>'DRAFT' THEN RAISE EXCEPTION 'Lifecycle must begin DRAFT'; END IF;
      ELSIF NEW.sequence<>prior_sequence+1 OR NEW.from_state IS DISTINCT FROM prior_state OR NOT((prior_state='DRAFT' AND NEW.to_state='VALIDATED') OR (prior_state='VALIDATED' AND NEW.to_state='PUBLISHED') OR (prior_state='PUBLISHED' AND NEW.to_state='DEPRECATED')) THEN RAISE EXCEPTION 'Illegal GDSS-005 lifecycle transition'; END IF;
      IF TG_TABLE_NAME='gdss_observation_dataset_lifecycle_event' THEN UPDATE public.gdss_observation_dataset_version SET state=NEW.to_state,dataset_hash=COALESCE(NEW.resulting_dataset_hash,dataset_hash),validated_by=CASE WHEN NEW.to_state='VALIDATED' THEN NEW.actor ELSE validated_by END,validated_at=CASE WHEN NEW.to_state='VALIDATED' THEN clock_timestamp() ELSE validated_at END,published_by=CASE WHEN NEW.to_state='PUBLISHED' THEN NEW.actor ELSE published_by END,published_at=CASE WHEN NEW.to_state='PUBLISHED' THEN clock_timestamp() ELSE published_at END,deprecated_by=CASE WHEN NEW.to_state='DEPRECATED' THEN NEW.actor ELSE deprecated_by END,deprecated_at=CASE WHEN NEW.to_state='DEPRECATED' THEN clock_timestamp() ELSE deprecated_at END WHERE id=NEW.dataset_version_id;
      ELSE UPDATE public.gdss_calibration_version SET state=NEW.to_state,calibration_design_hash=COALESCE(NEW.resulting_design_hash,calibration_design_hash),validated_by=CASE WHEN NEW.to_state='VALIDATED' THEN NEW.actor ELSE validated_by END,validated_at=CASE WHEN NEW.to_state='VALIDATED' THEN clock_timestamp() ELSE validated_at END,published_by=CASE WHEN NEW.to_state='PUBLISHED' THEN NEW.actor ELSE published_by END,published_at=CASE WHEN NEW.to_state='PUBLISHED' THEN clock_timestamp() ELSE published_at END,deprecated_by=CASE WHEN NEW.to_state='DEPRECATED' THEN NEW.actor ELSE deprecated_by END,deprecated_at=CASE WHEN NEW.to_state='DEPRECATED' THEN clock_timestamp() ELSE deprecated_at END WHERE id=NEW.calibration_version_id; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_execution_event() RETURNS TRIGGER AS $$
    DECLARE last_sequence INTEGER; last_type TEXT;
    BEGIN
      SELECT sequence,event_type INTO last_sequence,last_type FROM public.gdss_calibration_execution_event WHERE attempt_id=NEW.attempt_id ORDER BY sequence DESC LIMIT 1 FOR UPDATE;
      IF last_sequence IS NULL THEN IF NEW.sequence<>1 OR NEW.event_type<>'ACCEPTED' THEN RAISE EXCEPTION 'First attempt event must be ACCEPTED'; END IF;
      ELSIF NEW.sequence<>last_sequence+1 THEN RAISE EXCEPTION 'Attempt event sequence mismatch';
      ELSIF last_type='ACCEPTED' AND NEW.event_type<>'RUNNING' THEN RAISE EXCEPTION 'ACCEPTED must transition to RUNNING';
      ELSIF last_type='RUNNING' AND NEW.event_type NOT IN ('COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','ABORTED') THEN RAISE EXCEPTION 'RUNNING requires a terminal';
      ELSIF last_type IN ('COMPLETED','COMPLETED_WITH_WARNINGS') AND NEW.event_type<>'RESULT_PUBLISHED' THEN RAISE EXCEPTION 'Only publication may follow success';
      ELSIF last_type IN ('FAILED','ABORTED','RESULT_PUBLISHED') THEN RAISE EXCEPTION 'Attempt already terminal'; END IF; RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_candidate_event() RETURNS TRIGGER AS $$
    DECLARE last_sequence INTEGER; last_state TEXT; governed_abort BOOLEAN;
    BEGIN
      IF NEW.gdss_simulation_attempt_id IS NOT NULL AND EXISTS(SELECT 1 FROM public.gdss_calibration_candidate_evaluation e WHERE e.gdss_simulation_attempt_id=NEW.gdss_simulation_attempt_id AND (e.attempt_id,e.candidate_ordinal) IS DISTINCT FROM (NEW.attempt_id,NEW.candidate_ordinal)) THEN RAISE EXCEPTION 'Simulation attempt already attached to another candidate'; END IF;
      SELECT sequence,state INTO last_sequence,last_state FROM public.gdss_calibration_candidate_evaluation WHERE attempt_id=NEW.attempt_id AND candidate_ordinal=NEW.candidate_ordinal ORDER BY sequence DESC LIMIT 1 FOR UPDATE;
      IF last_sequence IS NULL THEN IF NEW.sequence<>1 OR NEW.state<>'PENDING' THEN RAISE EXCEPTION 'Candidate must begin PENDING'; END IF;
      ELSIF NEW.sequence<>last_sequence+1 OR last_state IN ('SUCCEEDED','INFEASIBLE','SIMULATION_FAILED','NOT_DISPATCHED_ABORTED') THEN RAISE EXCEPTION 'Candidate sequence or terminal mismatch';
      ELSIF NEW.state='NOT_DISPATCHED_ABORTED' THEN
        SELECT a.abort_requested AND a.abort_requested_by IS NOT NULL AND a.abort_requested_at IS NOT NULL AND a.abort_reason IS NOT NULL
          AND EXISTS(SELECT 1 FROM public.gdss_calibration_execution_event x WHERE x.attempt_id=a.id AND x.event_type='ABORTED')
          INTO governed_abort FROM public.gdss_calibration_execution_attempt a WHERE a.id=NEW.attempt_id FOR SHARE;
        IF last_state NOT IN ('PENDING','CLAIMED') OR NOT COALESCE(governed_abort,FALSE) THEN RAISE EXCEPTION 'NOT_DISPATCHED_ABORTED requires governed attempt abort'; END IF;
      ELSIF NOT((last_state='PENDING' AND NEW.state='CLAIMED') OR (last_state='CLAIMED' AND NEW.state IN ('CLAIMED','DISPATCHED')) OR (last_state='DISPATCHED' AND NEW.state IN ('SUCCEEDED','INFEASIBLE','SIMULATION_FAILED'))) THEN RAISE EXCEPTION 'Illegal candidate transition'; END IF; RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_artifact_integrity() RETURNS TRIGGER AS $$
    BEGIN IF octet_length(NEW.payload)<>NEW.byte_length OR encode(digest(NEW.payload,'sha256'),'hex')<>NEW.content_sha256 THEN RAISE EXCEPTION 'ARTIFACT_RECONCILIATION_FAILURE'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_finalization() RETURNS TRIGGER AS $$
    DECLARE expected INTEGER; terminal INTEGER;
    BEGIN IF NEW.event_type IN ('COMPLETED','COMPLETED_WITH_WARNINGS') THEN
      SELECT count(DISTINCT candidate_ordinal),count(DISTINCT candidate_ordinal) FILTER(WHERE state IN ('SUCCEEDED','INFEASIBLE','SIMULATION_FAILED','NOT_DISPATCHED_ABORTED')) INTO expected,terminal FROM public.gdss_calibration_candidate_evaluation WHERE attempt_id=NEW.attempt_id;
      IF expected=0 OR expected<>terminal OR NEW.result_hash IS NULL OR NEW.result_artifact_id IS NULL THEN RAISE EXCEPTION 'Incomplete calibration finalization'; END IF;
    END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_model_binding_coherence() RETURNS TRIGGER AS $$
    DECLARE mi UUID; mn INTEGER; mh TEXT; bi UUID; bn INTEGER; bm UUID; bh TEXT; mp UUID; bp UUID; cp UUID; bs TEXT; cv UUID;
    BEGIN
      IF TG_TABLE_NAME='gdss_calibration_series_mapping' THEN
        SELECT a.calibration_version_id INTO cv FROM public.gdss_calibration_dataset_assignment a WHERE a.id=NEW.dataset_assignment_id;
        IF NOT EXISTS(SELECT 1 FROM public.gdss_calibration_version c JOIN public.gdss_artifact a ON a.model_version_id=c.model_version_id AND a.symbol=NEW.target_quantity_identity JOIN public.gdss_dynamic_binding_version b ON b.id=c.binding_version_id WHERE c.id=cv AND a.kind='Variable' AND (EXISTS(SELECT 1 FROM jsonb_array_elements(COALESCE(b.content->'states','[]')) x WHERE x->>'stateRef'=NEW.target_quantity_identity) OR EXISTS(SELECT 1 FROM jsonb_array_elements(COALESCE(b.content->'algebraics','[]')) x WHERE x->>'outputRef'=NEW.target_quantity_identity))) THEN RAISE EXCEPTION 'MODEL_BINDING_MISMATCH'; END IF;
        RETURN NEW;
      END IF;
      SELECT v.identity_id,v.version_number,v.content_hash,i.project_id INTO mi,mn,mh,mp FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id;
      SELECT v.binding_id,v.version_number,v.model_version_id,v.dynamic_binding_hash,b.project_id INTO bi,bn,bm,bh,bp FROM public.gdss_dynamic_binding_version v JOIN public.gdss_dynamic_binding b ON b.id=v.binding_id WHERE v.id=NEW.binding_version_id;
      SELECT project_id INTO cp FROM public.gdss_calibration_identity WHERE id=NEW.calibration_identity_id;
      SELECT to_status INTO bs FROM public.gdss_dynamic_binding_lifecycle_event WHERE binding_version_id=NEW.binding_version_id ORDER BY sequence DESC LIMIT 1;
      IF (mi,mn,mh,bi,bn,bm,bh,mp,bp,bs) IS DISTINCT FROM (NEW.model_identity_id,NEW.model_version_number,NEW.model_content_hash,NEW.binding_id,NEW.binding_version_number,NEW.model_version_id,NEW.dynamic_binding_hash,cp,cp,'PUBLISHED') THEN RAISE EXCEPTION 'MODEL_BINDING_MISMATCH'; END IF; RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss005_guard_source_origin() RETURNS TRIGGER AS $$
    DECLARE origin TEXT;
    BEGIN SELECT epistemic_origin INTO origin FROM public.gdss_observation_dataset_version WHERE id=NEW.dataset_version_id FOR SHARE;
      IF (origin='PHYSICAL_OBSERVATION' AND (NEW.source_type='SYNTHETIC_FIXTURE' OR NEW.physical_system_identity IS NULL)) OR (origin='SYNTHETIC_OBSERVATION' AND (NEW.source_type<>'SYNTHETIC_FIXTURE' OR NEW.physical_system_identity IS NOT NULL)) THEN RAISE EXCEPTION 'SOURCE_EPISTEMIC_ORIGIN_MISMATCH'; END IF; RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss005_source_origin BEFORE INSERT OR UPDATE ON public.gdss_observation_source_reference FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_source_origin();
    CREATE TRIGGER trg_gdss005_model_binding BEFORE INSERT OR UPDATE ON public.gdss_calibration_version FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_model_binding_coherence();
    CREATE TRIGGER trg_gdss005_mapping_context BEFORE INSERT OR UPDATE ON public.gdss_calibration_series_mapping FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_model_binding_coherence();
    CREATE TRIGGER trg_gdss005_artifact_integrity BEFORE INSERT ON public.gdss_calibration_artifact FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_artifact_integrity();
    CREATE TRIGGER trg_gdss005_dataset_lifecycle BEFORE INSERT ON public.gdss_observation_dataset_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_lifecycle_transition();
    CREATE TRIGGER trg_gdss005_calibration_lifecycle BEFORE INSERT ON public.gdss_calibration_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_lifecycle_transition();
    CREATE TRIGGER trg_gdss005_execution_event BEFORE INSERT ON public.gdss_calibration_execution_event FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_execution_event();
    CREATE TRIGGER trg_gdss005_finalization BEFORE INSERT ON public.gdss_calibration_execution_event FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_finalization();
    CREATE TRIGGER trg_gdss005_candidate_event BEFORE INSERT ON public.gdss_calibration_candidate_evaluation FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_candidate_event();

    CREATE INDEX gdss_observation_dataset_state_idx ON public.gdss_observation_dataset_version(dataset_identity_id,state);
    CREATE INDEX gdss_observation_source_hash_idx ON public.gdss_observation_source_reference(source_content_sha256);
    CREATE INDEX gdss_observation_source_type_idx ON public.gdss_observation_source_reference(dataset_version_id,source_type);
    CREATE INDEX gdss_observation_series_quantity_idx ON public.gdss_observation_series(quantity_identity);
    CREATE INDEX gdss_observation_point_time_idx ON public.gdss_observation_point(series_id,measurement_time_us);
    CREATE INDEX gdss_calibration_model_idx ON public.gdss_calibration_version(model_version_id);
    CREATE INDEX gdss_calibration_binding_idx ON public.gdss_calibration_version(binding_version_id);
    CREATE INDEX gdss_calibration_mapping_target_idx ON public.gdss_calibration_series_mapping(target_quantity_identity);
    CREATE INDEX gdss_calibration_attempt_state_idx ON public.gdss_calibration_execution_attempt(project_id,terminal_state,requested_at);
    CREATE INDEX gdss_calibration_candidate_claim_idx ON public.gdss_calibration_candidate_evaluation(attempt_id,state,candidate_ordinal);
    CREATE INDEX gdss_calibration_estimate_hash_idx ON public.gdss_calibration_parameter_estimate_set(estimate_set_hash);
    CREATE INDEX gdss_calibration_diagnostic_idx ON public.gdss_calibration_diagnostic(attempt_id,diagnostic_class,code);
    CREATE TRIGGER trg_gdss005_dataset_version_freeze BEFORE UPDATE OR DELETE ON public.gdss_observation_dataset_version FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_dataset_freeze();
    CREATE TRIGGER trg_gdss005_source_freeze BEFORE UPDATE OR DELETE ON public.gdss_observation_source_reference FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_dataset_freeze();
    CREATE TRIGGER trg_gdss005_series_freeze BEFORE UPDATE OR DELETE ON public.gdss_observation_series FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_dataset_freeze();
    CREATE TRIGGER trg_gdss005_calibration_version_freeze BEFORE UPDATE OR DELETE ON public.gdss_calibration_version FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_calibration_freeze();
    CREATE TRIGGER trg_gdss005_assignment_freeze BEFORE UPDATE OR DELETE ON public.gdss_calibration_dataset_assignment FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_calibration_freeze();
    CREATE TRIGGER trg_gdss005_mapping_freeze BEFORE UPDATE OR DELETE ON public.gdss_calibration_series_mapping FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_calibration_freeze();
    CREATE TRIGGER trg_gdss005_parameter_freeze BEFORE UPDATE OR DELETE ON public.gdss_calibration_parameter FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_calibration_freeze();
    CREATE TRIGGER trg_gdss005_dataset_identity_immutable BEFORE UPDATE OR DELETE ON public.gdss_observation_dataset_identity FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_point_freeze BEFORE UPDATE OR DELETE ON public.gdss_observation_point FOR EACH ROW EXECUTE FUNCTION public.gdss005_guard_dataset_freeze();
    CREATE TRIGGER trg_gdss005_dataset_event_immutable BEFORE UPDATE OR DELETE ON public.gdss_observation_dataset_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_calibration_identity_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_identity FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_calibration_event_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_artifact_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_artifact FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_execution_event_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_execution_event FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_candidate_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_candidate_evaluation FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_estimate_set_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_parameter_estimate_set FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_estimate_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_parameter_estimate FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_adequacy_immutable BEFORE UPDATE OR DELETE ON public.gdss_model_adequacy_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_review_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_estimate_review FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    CREATE TRIGGER trg_gdss005_diagnostic_immutable BEFORE UPDATE OR DELETE ON public.gdss_calibration_diagnostic FOR EACH ROW EXECUTE FUNCTION public.gdss005_reject_mutation();
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE public.gdss_calibration_diagnostic;
    DROP TABLE public.gdss_calibration_estimate_review;
    DROP TABLE public.gdss_model_adequacy_assessment;
    DROP TABLE public.gdss_calibration_parameter_estimate;
    DROP TABLE public.gdss_calibration_parameter_estimate_set;
    DROP TABLE public.gdss_calibration_candidate_evaluation;
    DROP TABLE public.gdss_calibration_execution_event;
    DROP TABLE public.gdss_calibration_execution_attempt;
    ALTER TABLE public.gdss_observation_dataset_version DROP CONSTRAINT gdss_observation_dataset_artifact_fk;
    DROP TABLE public.gdss_calibration_artifact;
    DROP TABLE public.gdss_calibration_lifecycle_event;
    DROP TABLE public.gdss_calibration_parameter;
    DROP TABLE public.gdss_calibration_series_mapping;
    DROP TABLE public.gdss_calibration_dataset_assignment;
    DROP TABLE public.gdss_calibration_version;
    DROP TABLE public.gdss_calibration_identity;
    DROP TABLE public.gdss_observation_dataset_lifecycle_event;
    DROP TABLE public.gdss_observation_point;
    DROP TABLE public.gdss_observation_series;
    DROP TABLE public.gdss_observation_source_reference;
    DROP TABLE public.gdss_observation_dataset_version;
    DROP TABLE public.gdss_observation_dataset_identity;
    DROP FUNCTION public.gdss005_guard_source_origin();
    DROP FUNCTION public.gdss005_guard_model_binding_coherence();
    DROP FUNCTION public.gdss005_guard_finalization();
    DROP FUNCTION public.gdss005_guard_artifact_integrity();
    DROP FUNCTION public.gdss005_guard_candidate_event();
    DROP FUNCTION public.gdss005_guard_execution_event();
    DROP FUNCTION public.gdss005_guard_lifecycle_transition();
    DROP FUNCTION public.gdss005_guard_calibration_freeze();
    DROP FUNCTION public.gdss005_guard_dataset_freeze();
    DROP FUNCTION public.gdss005_reject_mutation();
    """)
