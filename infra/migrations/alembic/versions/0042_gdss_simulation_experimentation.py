"""Governed simulation experimentation and comparative evidence. Revision 0042."""
from alembic import op

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_experiment_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      canonical_name TEXT NOT NULL CHECK(length(canonical_name) BETWEEN 1 AND 128), description TEXT NOT NULL DEFAULT '' CHECK(length(description)<=4096),
      created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256), created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(project_id,canonical_name), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_experiment_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_identity_id UUID NOT NULL, project_id UUID NOT NULL,
      version_number INTEGER NOT NULL CHECK(version_number>0), predecessor_version_id UUID NULL,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      binding_version_id UUID NOT NULL REFERENCES public.gdss_dynamic_binding_version(id) ON DELETE RESTRICT,
      model_content_hash CHAR(64) NOT NULL CHECK(model_content_hash ~ '^[0-9a-f]{64}$'), dynamic_binding_hash CHAR(64) NOT NULL CHECK(dynamic_binding_hash ~ '^[0-9a-f]{64}$'),
      research_question TEXT NOT NULL CHECK(length(research_question) BETWEEN 1 AND 4096), hypothesis TEXT NULL CHECK(hypothesis IS NULL OR length(hypothesis) BETWEEN 1 AND 4096),
      base_simulation_manifest JSONB NOT NULL CHECK(jsonb_typeof(base_simulation_manifest)='object'), base_simulation_input_hash CHAR(64) NOT NULL CHECK(base_simulation_input_hash ~ '^[0-9a-f]{64}$'),
      completeness_policy TEXT NOT NULL CHECK(completeness_policy IN ('ALL_REQUIRED_SCENARIOS','ALLOW_PARTIAL_EXPLICIT')),
      semantic_versions JSONB NOT NULL CHECK(jsonb_typeof(semantic_versions)='object'), canonical_design TEXT NOT NULL CHECK(octet_length(convert_to(canonical_design,'UTF8')) BETWEEN 2 AND 262144),
      experiment_design_hash CHAR(64) NOT NULL CHECK(experiment_design_hash ~ '^[0-9a-f]{64}$'), created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256), created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      FOREIGN KEY(experiment_identity_id,project_id) REFERENCES public.gdss_experiment_identity(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predecessor_version_id) REFERENCES public.gdss_experiment_version(id) ON DELETE RESTRICT,
      UNIQUE(experiment_identity_id,version_number), UNIQUE(experiment_identity_id,experiment_design_hash), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_experiment_lifecycle_event (
      id BIGSERIAL PRIMARY KEY, experiment_version_id UUID NOT NULL REFERENCES public.gdss_experiment_version(id) ON DELETE RESTRICT,
      sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 4), from_status TEXT NULL CHECK(from_status IS NULL OR from_status IN ('DRAFT','VALIDATED','PUBLISHED','DEPRECATED')),
      to_status TEXT NOT NULL CHECK(to_status IN ('DRAFT','VALIDATED','PUBLISHED','DEPRECATED')), actor TEXT NOT NULL CHECK(length(actor) BETWEEN 1 AND 256), reason TEXT NOT NULL CHECK(length(reason) BETWEEN 1 AND 4096), created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(experiment_version_id,sequence));
    CREATE TABLE public.gdss_experiment_factor (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_version_id UUID NOT NULL, project_id UUID NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 7), factor_key TEXT NOT NULL CHECK(length(factor_key) BETWEEN 1 AND 128),
      target_kind TEXT NOT NULL CHECK(target_kind IN ('PARAMETER','INITIAL_CONDITION','TEMPORAL_CONFIGURATION')), target_identity TEXT NOT NULL CHECK(length(target_identity) BETWEEN 1 AND 256), unit_identity JSONB NULL CHECK(unit_identity IS NULL OR jsonb_typeof(unit_identity)='object'),
      ordered_values JSONB NOT NULL CHECK(jsonb_typeof(ordered_values)='array' AND jsonb_array_length(ordered_values) BETWEEN 1 AND 32), provenance JSONB NOT NULL CHECK(jsonb_typeof(provenance)='object'),
      FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(experiment_version_id,ordinal), UNIQUE(experiment_version_id,factor_key), UNIQUE(experiment_version_id,target_kind,target_identity), UNIQUE(id,experiment_version_id));
    CREATE TABLE public.gdss_experiment_controlled_input (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_version_id UUID NOT NULL, project_id UUID NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
      target_kind TEXT NOT NULL CHECK(target_kind IN ('PARAMETER','INITIAL_CONDITION','TEMPORAL_CONFIGURATION')), target_identity TEXT NOT NULL CHECK(length(target_identity) BETWEEN 1 AND 256), expected_governed_value JSONB NOT NULL,
      unit_identity JSONB NULL CHECK(unit_identity IS NULL OR jsonb_typeof(unit_identity)='object'), FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(experiment_version_id,ordinal), UNIQUE(experiment_version_id,target_kind,target_identity), UNIQUE(id,experiment_version_id));
    CREATE TABLE public.gdss_experiment_metric_definition (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_version_id UUID NOT NULL, project_id UUID NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 31), metric_key TEXT NOT NULL CHECK(length(metric_key) BETWEEN 1 AND 128),
      operation TEXT NOT NULL CHECK(operation IN ('INITIAL_VALUE','FINAL_VALUE','MINIMUM','MAXIMUM','ARITHMETIC_POINT_MEAN','LEFT_RECTANGLE_INTEGRAL','PEAK_STEP','TIME_TO_THRESHOLD')),
      metric_version TEXT NOT NULL CHECK(metric_version='GDSS_EXPERIMENT_METRICS_V1'), state_symbol TEXT NOT NULL CHECK(length(state_symbol) BETWEEN 1 AND 256), definition JSONB NOT NULL CHECK(jsonb_typeof(definition)='object'), definition_hash CHAR(64) NOT NULL CHECK(definition_hash ~ '^[0-9a-f]{64}$'),
      FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(experiment_version_id,ordinal), UNIQUE(experiment_version_id,metric_key), UNIQUE(experiment_version_id,definition_hash), UNIQUE(id,experiment_version_id));
    CREATE TABLE public.gdss_experiment_comparison_definition (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_version_id UUID NOT NULL, metric_definition_id UUID NOT NULL, project_id UUID NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 63), comparison_key TEXT NOT NULL CHECK(length(comparison_key) BETWEEN 1 AND 128),
      operation TEXT NOT NULL CHECK(operation IN ('ABSOLUTE_DIFFERENCE','RELATIVE_DIFFERENCE','PERCENT_DIFFERENCE','ORDERING')), comparison_version TEXT NOT NULL CHECK(comparison_version='GDSS_EXPERIMENT_COMPARISONS_V1'),
      reference_selector JSONB NOT NULL CHECK(jsonb_typeof(reference_selector)='object'), target_selector JSONB NOT NULL CHECK(jsonb_typeof(target_selector)='object'), required_scenario_selectors JSONB NOT NULL CHECK(jsonb_typeof(required_scenario_selectors)='array'),
      temporal_policy TEXT NOT NULL CHECK(temporal_policy='GDSS_TEMPORAL_COMPARABILITY_V1'), definition_hash CHAR(64) NOT NULL CHECK(definition_hash ~ '^[0-9a-f]{64}$'),
      FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(metric_definition_id,experiment_version_id) REFERENCES public.gdss_experiment_metric_definition(id,experiment_version_id) ON DELETE RESTRICT,
      UNIQUE(experiment_version_id,ordinal), UNIQUE(experiment_version_id,comparison_key), UNIQUE(experiment_version_id,definition_hash), UNIQUE(id,experiment_version_id));
    CREATE TABLE public.gdss_experiment_artifact (
      hash CHAR(64) PRIMARY KEY CHECK(hash ~ '^[0-9a-f]{64}$'), media_type TEXT NOT NULL CHECK(media_type IN ('application/vnd.midd.gdss-experiment-manifest+json;version=1','application/vnd.midd.gdss-experiment-result+json;version=1')),
      format_version TEXT NOT NULL CHECK(format_version IN ('GDSS_EXPERIMENT_MANIFEST_JSON_V1','GDSS_EXPERIMENT_RESULT_JSON_V1')), byte_length INTEGER NOT NULL CHECK(byte_length BETWEEN 2 AND 16777216), payload BYTEA NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      CHECK(octet_length(payload)=byte_length), CHECK(encode(digest(payload,'sha256'),'hex')=hash),
      CHECK((format_version='GDSS_EXPERIMENT_MANIFEST_JSON_V1' AND byte_length<=4194304) OR (format_version='GDSS_EXPERIMENT_RESULT_JSON_V1' AND byte_length<=16777216)));
    CREATE TABLE public.gdss_experiment_execution_attempt (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT, experiment_version_id UUID NOT NULL,
      experiment_design_hash CHAR(64) NOT NULL CHECK(experiment_design_hash ~ '^[0-9a-f]{64}$'), manifest_hash CHAR(64) NOT NULL REFERENCES public.gdss_experiment_artifact(hash) ON DELETE RESTRICT,
      scenario_count INTEGER NOT NULL CHECK(scenario_count BETWEEN 1 AND 256), requested_by TEXT NOT NULL CHECK(length(requested_by) BETWEEN 1 AND 256), idempotency_key TEXT NULL CHECK(idempotency_key IS NULL OR length(idempotency_key) BETWEEN 1 AND 256),
      abort_requested BOOLEAN NOT NULL DEFAULT FALSE, abort_requested_by TEXT NULL, abort_requested_at TIMESTAMPTZ NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(id,project_id), UNIQUE(id,experiment_version_id), CHECK((abort_requested=FALSE AND abort_requested_by IS NULL AND abort_requested_at IS NULL) OR (abort_requested=TRUE AND abort_requested_by IS NOT NULL AND abort_requested_at IS NOT NULL)));
    CREATE UNIQUE INDEX gdss_experiment_attempt_idempotency_uq ON public.gdss_experiment_execution_attempt(project_id,idempotency_key) WHERE idempotency_key IS NOT NULL;
    CREATE TABLE public.gdss_experiment_materialized_scenario (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_attempt_id UUID NOT NULL, project_id UUID NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255), scenario_type TEXT NOT NULL CHECK(scenario_type IN ('BASELINE','ALTERNATIVE','COUNTERFACTUAL')),
      reference_scenario_ordinal INTEGER NULL CHECK(reference_scenario_ordinal IS NULL OR reference_scenario_ordinal BETWEEN 0 AND 255), scenario_definition_hash CHAR(64) NOT NULL CHECK(scenario_definition_hash ~ '^[0-9a-f]{64}$'), simulation_input_hash CHAR(64) NOT NULL CHECK(simulation_input_hash ~ '^[0-9a-f]{64}$'),
      factor_assignments JSONB NOT NULL CHECK(jsonb_typeof(factor_assignments)='array'), authorized_overrides JSONB NOT NULL CHECK(jsonb_typeof(authorized_overrides)='array' AND jsonb_array_length(authorized_overrides)<=32), controlled_input_proof_hash CHAR(64) NOT NULL CHECK(controlled_input_proof_hash ~ '^[0-9a-f]{64}$'), materialized_simulation_manifest JSONB NOT NULL CHECK(jsonb_typeof(materialized_simulation_manifest)='object'),
      FOREIGN KEY(experiment_attempt_id,project_id) REFERENCES public.gdss_experiment_execution_attempt(id,project_id) ON DELETE RESTRICT,
      UNIQUE(experiment_attempt_id,ordinal), UNIQUE(experiment_attempt_id,scenario_definition_hash), UNIQUE(id,experiment_attempt_id), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_experiment_scenario_execution (
      id BIGSERIAL PRIMARY KEY, experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT, materialized_scenario_id UUID NOT NULL,
      sequence INTEGER NOT NULL CHECK(sequence>0), state TEXT NOT NULL CHECK(state IN ('PENDING','CLAIMED','DISPATCHED','TERMINAL_SUCCESS','TERMINAL_FAILURE','NOT_DISPATCHED_ABORTED')),
      claim_token UUID NULL, lease_expires_at TIMESTAMPTZ NULL, dispatch_attempt INTEGER NOT NULL CHECK(dispatch_attempt BETWEEN 0 AND 3),
      gdss_simulation_attempt_id UUID NULL REFERENCES public.gdss_simulation_attempt(id) ON DELETE RESTRICT, simulation_input_hash CHAR(64) NOT NULL CHECK(simulation_input_hash ~ '^[0-9a-f]{64}$'), simulation_result_hash CHAR(64) NULL CHECK(simulation_result_hash IS NULL OR simulation_result_hash ~ '^[0-9a-f]{64}$'), trajectory_hash CHAR(64) NULL REFERENCES public.gdss_simulation_artifact(hash) ON DELETE RESTRICT, failure_classification TEXT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      FOREIGN KEY(materialized_scenario_id,experiment_attempt_id) REFERENCES public.gdss_experiment_materialized_scenario(id,experiment_attempt_id) ON DELETE RESTRICT, UNIQUE(materialized_scenario_id,sequence));
    CREATE TABLE public.gdss_experiment_execution_event (
      id BIGSERIAL PRIMARY KEY, experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT, sequence INTEGER NOT NULL CHECK(sequence IN (1,2)),
      status TEXT NOT NULL CHECK(status IN ('RUNNING','COMPLETED','COMPLETED_WITH_FAILURES','FAILED','ABORTED')), result_hash CHAR(64) NULL REFERENCES public.gdss_experiment_artifact(hash) ON DELETE RESTRICT,
      completeness TEXT NULL CHECK(completeness IS NULL OR completeness IN ('COMPLETE','PARTIAL','ABORTED')), failure_classification TEXT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(experiment_attempt_id,sequence));
    CREATE TABLE public.gdss_experiment_metric_result (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT, materialized_scenario_id UUID NOT NULL,
      metric_definition_id UUID NOT NULL REFERENCES public.gdss_experiment_metric_definition(id) ON DELETE RESTRICT, status TEXT NOT NULL CHECK(status IN ('SUCCEEDED','NOT_REACHED','INELIGIBLE','FAILED')), result JSONB NOT NULL CHECK(jsonb_typeof(result)='object'), result_hash CHAR(64) NOT NULL CHECK(result_hash ~ '^[0-9a-f]{64}$'),
      trajectory_hash CHAR(64) NULL REFERENCES public.gdss_simulation_artifact(hash) ON DELETE RESTRICT, simulation_result_hash CHAR(64) NULL CHECK(simulation_result_hash IS NULL OR simulation_result_hash ~ '^[0-9a-f]{64}$'), operation_count BIGINT NOT NULL CHECK(operation_count>=0), created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      FOREIGN KEY(materialized_scenario_id,experiment_attempt_id) REFERENCES public.gdss_experiment_materialized_scenario(id,experiment_attempt_id) ON DELETE RESTRICT,
      UNIQUE(experiment_attempt_id,materialized_scenario_id,metric_definition_id), UNIQUE(experiment_attempt_id,result_hash), UNIQUE(id,experiment_attempt_id));
    CREATE TABLE public.gdss_experiment_comparison_result (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT, comparison_definition_id UUID NOT NULL REFERENCES public.gdss_experiment_comparison_definition(id) ON DELETE RESTRICT,
      reference_metric_result_id UUID NULL, target_metric_result_id UUID NULL, status TEXT NOT NULL CHECK(status IN ('SUCCEEDED','INELIGIBLE','FAILED')), result JSONB NOT NULL CHECK(jsonb_typeof(result)='object'), result_hash CHAR(64) NOT NULL CHECK(result_hash ~ '^[0-9a-f]{64}$'), operation_count INTEGER NOT NULL CHECK(operation_count>=0), created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      FOREIGN KEY(reference_metric_result_id,experiment_attempt_id) REFERENCES public.gdss_experiment_metric_result(id,experiment_attempt_id) ON DELETE RESTRICT,
      FOREIGN KEY(target_metric_result_id,experiment_attempt_id) REFERENCES public.gdss_experiment_metric_result(id,experiment_attempt_id) ON DELETE RESTRICT,
      UNIQUE(experiment_attempt_id,comparison_definition_id), UNIQUE(experiment_attempt_id,result_hash));
    CREATE TABLE public.gdss_experiment_diagnostic (
      id BIGSERIAL PRIMARY KEY, experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT, sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 512), code TEXT NOT NULL CHECK(length(code) BETWEEN 1 AND 128),
      severity TEXT NOT NULL CHECK(severity IN ('ERROR','WARNING','INFO')), stage TEXT NOT NULL CHECK(stage IN ('DESIGN','EXPANSION','MATERIALIZATION','DISPATCH','TRAJECTORY_READ','METRIC','COMPARISON','TERMINALIZATION','ABORT','RECOVERY','PERSISTENCE')),
      materialized_scenario_id UUID NULL REFERENCES public.gdss_experiment_materialized_scenario(id) ON DELETE RESTRICT, details JSONB NOT NULL DEFAULT '{}' CHECK(jsonb_typeof(details)='object'), message TEXT NOT NULL CHECK(length(message) BETWEEN 1 AND 4096), created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(experiment_attempt_id,sequence));

    CREATE FUNCTION public.gdss_experiment_reject_evidence_mutation() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'GDSS-004 evidence is append-only'; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss_experiment_version_guard() RETURNS TRIGGER AS $$
    DECLARE identity_project UUID; model_project UUID; binding_project UUID; binding_model UUID; stored_model_hash TEXT; stored_binding_hash TEXT; predecessor_identity UUID;
    BEGIN
      SELECT project_id INTO identity_project FROM public.gdss_experiment_identity WHERE id=NEW.experiment_identity_id;
      SELECT i.project_id,v.content_hash INTO model_project,stored_model_hash FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id;
      SELECT b.project_id,v.model_version_id,v.dynamic_binding_hash INTO binding_project,binding_model,stored_binding_hash FROM public.gdss_dynamic_binding_version v JOIN public.gdss_dynamic_binding b ON b.id=v.binding_id WHERE v.id=NEW.binding_version_id;
      IF identity_project IS DISTINCT FROM NEW.project_id OR model_project IS DISTINCT FROM NEW.project_id OR binding_project IS DISTINCT FROM NEW.project_id OR binding_model IS DISTINCT FROM NEW.model_version_id OR stored_model_hash IS DISTINCT FROM NEW.model_content_hash OR stored_binding_hash IS DISTINCT FROM NEW.dynamic_binding_hash THEN RAISE EXCEPTION 'GDSS experiment exact base binding mismatch'; END IF;
      IF NEW.predecessor_version_id IS NOT NULL THEN SELECT experiment_identity_id INTO predecessor_identity FROM public.gdss_experiment_version WHERE id=NEW.predecessor_version_id; IF predecessor_identity IS DISTINCT FROM NEW.experiment_identity_id THEN RAISE EXCEPTION 'GDSS experiment predecessor mismatch'; END IF; END IF;
      IF NEW.semantic_versions->>'experiment' IS DISTINCT FROM 'GDSS_EXPERIMENT_V1' OR NEW.semantic_versions->>'metrics' IS DISTINCT FROM 'GDSS_EXPERIMENT_METRICS_V1' OR NEW.semantic_versions->>'comparisons' IS DISTINCT FROM 'GDSS_EXPERIMENT_COMPARISONS_V1' THEN RAISE EXCEPTION 'Unsupported GDSS experiment semantic versions'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss_experiment_design_mutation_guard() RETURNS TRIGGER AS $$
    DECLARE version_id UUID; status TEXT;
    BEGIN
      IF TG_TABLE_NAME='gdss_experiment_version' THEN IF TG_OP='DELETE' THEN version_id:=OLD.id; ELSE version_id:=NEW.id; END IF;
      ELSE IF TG_OP='DELETE' THEN version_id:=OLD.experiment_version_id; ELSE version_id:=NEW.experiment_version_id; END IF; END IF;
      SELECT to_status INTO status FROM public.gdss_experiment_lifecycle_event WHERE experiment_version_id=version_id ORDER BY sequence DESC LIMIT 1;
      IF TG_TABLE_NAME='gdss_experiment_version' THEN
        IF TG_OP='DELETE' THEN RAISE EXCEPTION 'GDSS experiment version is append-only'; END IF;
        IF TG_OP='UPDATE' AND (NEW.id<>OLD.id OR NEW.experiment_identity_id<>OLD.experiment_identity_id OR NEW.version_number<>OLD.version_number OR NEW.project_id<>OLD.project_id) THEN RAISE EXCEPTION 'GDSS experiment lineage is immutable'; END IF;
      END IF;
      IF TG_TABLE_NAME<>'gdss_experiment_version' AND (status IS NULL OR status<>'DRAFT') THEN RAISE EXCEPTION 'GDSS experiment children require DRAFT lifecycle'; END IF;
      IF TG_TABLE_NAME='gdss_experiment_version' AND status IS NOT NULL AND status<>'DRAFT' THEN RAISE EXCEPTION 'GDSS experiment design is frozen after validation'; END IF;
      IF TG_OP='DELETE' THEN RETURN OLD; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss_experiment_lifecycle_guard() RETURNS TRIGGER AS $$
    DECLARE last_sequence INTEGER; last_status TEXT; factor_count INTEGER; metric_count INTEGER; comparison_count INTEGER;
    BEGIN
      PERFORM 1 FROM public.gdss_experiment_version WHERE id=NEW.experiment_version_id FOR UPDATE;
      SELECT sequence,to_status INTO last_sequence,last_status FROM public.gdss_experiment_lifecycle_event WHERE experiment_version_id=NEW.experiment_version_id ORDER BY sequence DESC LIMIT 1;
      IF last_sequence IS NULL THEN IF NEW.sequence<>1 OR NEW.from_status IS NOT NULL OR NEW.to_status<>'DRAFT' THEN RAISE EXCEPTION 'Lifecycle must begin NULL to DRAFT'; END IF;
      ELSIF NEW.sequence<>last_sequence+1 OR NEW.from_status IS DISTINCT FROM last_status OR NOT ((last_status='DRAFT' AND NEW.to_status='VALIDATED') OR (last_status='VALIDATED' AND NEW.to_status='PUBLISHED') OR (last_status='PUBLISHED' AND NEW.to_status='DEPRECATED')) THEN RAISE EXCEPTION 'Illegal GDSS experiment lifecycle transition'; END IF;
      IF NEW.to_status='VALIDATED' THEN SELECT count(*) INTO factor_count FROM public.gdss_experiment_factor WHERE experiment_version_id=NEW.experiment_version_id; SELECT count(*) INTO metric_count FROM public.gdss_experiment_metric_definition WHERE experiment_version_id=NEW.experiment_version_id; SELECT count(*) INTO comparison_count FROM public.gdss_experiment_comparison_definition WHERE experiment_version_id=NEW.experiment_version_id; IF factor_count>8 OR metric_count>32 OR comparison_count>64 THEN RAISE EXCEPTION 'GDSS experiment limits exceeded'; END IF; END IF;
      RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss_experiment_attempt_guard() RETURNS TRIGGER AS $$
    DECLARE version_project UUID; design_hash TEXT; lifecycle TEXT; artifact_format TEXT;
    BEGIN SELECT project_id,experiment_design_hash INTO version_project,design_hash FROM public.gdss_experiment_version WHERE id=NEW.experiment_version_id FOR SHARE; SELECT to_status INTO lifecycle FROM public.gdss_experiment_lifecycle_event WHERE experiment_version_id=NEW.experiment_version_id ORDER BY sequence DESC LIMIT 1; SELECT format_version INTO artifact_format FROM public.gdss_experiment_artifact WHERE hash=NEW.manifest_hash;
      IF version_project IS DISTINCT FROM NEW.project_id OR design_hash IS DISTINCT FROM NEW.experiment_design_hash OR lifecycle IS DISTINCT FROM 'PUBLISHED' OR artifact_format IS DISTINCT FROM 'GDSS_EXPERIMENT_MANIFEST_JSON_V1' THEN RAISE EXCEPTION 'GDSS experiment attempt ownership/publication/artifact mismatch'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss_experiment_abort_guard() RETURNS TRIGGER AS $$
    BEGIN IF TG_OP='DELETE' OR OLD.id<>NEW.id OR OLD.project_id<>NEW.project_id OR OLD.experiment_version_id<>NEW.experiment_version_id OR OLD.experiment_design_hash<>NEW.experiment_design_hash OR OLD.manifest_hash<>NEW.manifest_hash OR OLD.scenario_count<>NEW.scenario_count OR OLD.requested_by<>NEW.requested_by OR OLD.idempotency_key IS DISTINCT FROM NEW.idempotency_key OR OLD.created_at<>NEW.created_at OR OLD.abort_requested OR NOT NEW.abort_requested OR NEW.abort_requested_by IS NULL OR NEW.abort_requested_at IS NULL OR EXISTS(SELECT 1 FROM public.gdss_experiment_execution_event WHERE experiment_attempt_id=OLD.id AND sequence=2) THEN RAISE EXCEPTION 'Only one pre-terminal abort request update is permitted'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss_experiment_scenario_event_guard() RETURNS TRIGGER AS $$
    DECLARE prior RECORD; expected_hash TEXT; aborted BOOLEAN;
    BEGIN SELECT simulation_input_hash INTO expected_hash FROM public.gdss_experiment_materialized_scenario WHERE id=NEW.materialized_scenario_id AND experiment_attempt_id=NEW.experiment_attempt_id FOR UPDATE; SELECT abort_requested INTO aborted FROM public.gdss_experiment_execution_attempt WHERE id=NEW.experiment_attempt_id FOR SHARE; IF EXISTS(SELECT 1 FROM public.gdss_experiment_execution_event WHERE experiment_attempt_id=NEW.experiment_attempt_id AND sequence=2) THEN RAISE EXCEPTION 'Terminal experiment evidence is frozen'; END IF; SELECT sequence,state,dispatch_attempt,claim_token,lease_expires_at,gdss_simulation_attempt_id INTO prior FROM public.gdss_experiment_scenario_execution WHERE materialized_scenario_id=NEW.materialized_scenario_id ORDER BY sequence DESC LIMIT 1;
      IF expected_hash IS DISTINCT FROM NEW.simulation_input_hash THEN RAISE EXCEPTION 'Scenario input hash mismatch'; END IF;
      IF prior.sequence IS NULL THEN IF NEW.sequence<>1 OR NEW.state<>'PENDING' OR NEW.dispatch_attempt<>0 THEN RAISE EXCEPTION 'Scenario execution must begin PENDING'; END IF;
      ELSIF NEW.sequence<>prior.sequence+1 THEN RAISE EXCEPTION 'Scenario execution sequence gap';
      ELSIF NEW.state='CLAIMED' AND NOT aborted AND ((prior.state='PENDING' AND NEW.dispatch_attempt=1) OR (prior.state='CLAIMED' AND prior.lease_expires_at<=clock_timestamp() AND NEW.dispatch_attempt=prior.dispatch_attempt+1)) THEN NULL;
      ELSIF NEW.state='DISPATCHED' AND prior.state='CLAIMED' AND NEW.dispatch_attempt=prior.dispatch_attempt AND NEW.claim_token=prior.claim_token AND NEW.gdss_simulation_attempt_id IS NOT NULL THEN NULL;
      ELSIF NEW.state IN ('TERMINAL_SUCCESS','TERMINAL_FAILURE') AND prior.state='DISPATCHED' AND NEW.gdss_simulation_attempt_id=prior.gdss_simulation_attempt_id AND NEW.simulation_result_hash IS NOT NULL THEN NULL;
      ELSIF NEW.state='TERMINAL_FAILURE' AND prior.state='CLAIMED' AND prior.dispatch_attempt=3 AND NEW.dispatch_attempt=3 AND NEW.gdss_simulation_attempt_id IS NULL AND NEW.simulation_result_hash IS NULL AND NEW.failure_classification='DISPATCH_RETRY_EXHAUSTED' THEN NULL;
      ELSIF NEW.state='NOT_DISPATCHED_ABORTED' AND aborted AND prior.state IN ('PENDING','CLAIMED') AND (prior.state='PENDING' OR prior.lease_expires_at<=clock_timestamp()) THEN NULL;
      ELSE RAISE EXCEPTION 'Illegal GDSS scenario execution transition'; END IF;
      RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss_experiment_execution_event_guard() RETURNS TRIGGER AS $$
    DECLARE prior RECORD; expected INTEGER; actual INTEGER; pending INTEGER; result_format TEXT;
    BEGIN PERFORM 1 FROM public.gdss_experiment_execution_attempt WHERE id=NEW.experiment_attempt_id FOR UPDATE; SELECT sequence,status INTO prior FROM public.gdss_experiment_execution_event WHERE experiment_attempt_id=NEW.experiment_attempt_id ORDER BY sequence DESC LIMIT 1;
      IF prior.sequence IS NULL THEN IF NEW.sequence<>1 OR NEW.status<>'RUNNING' OR NEW.result_hash IS NOT NULL OR NEW.completeness IS NOT NULL THEN RAISE EXCEPTION 'Experiment execution must begin RUNNING'; END IF; SELECT scenario_count INTO expected FROM public.gdss_experiment_execution_attempt WHERE id=NEW.experiment_attempt_id; SELECT count(*),count(*) FILTER (WHERE e.state='PENDING') INTO actual,pending FROM public.gdss_experiment_materialized_scenario s LEFT JOIN public.gdss_experiment_scenario_execution e ON e.materialized_scenario_id=s.id AND e.sequence=1 WHERE s.experiment_attempt_id=NEW.experiment_attempt_id; IF actual<>expected OR pending<>expected OR EXISTS(SELECT 1 FROM public.gdss_experiment_materialized_scenario s WHERE s.experiment_attempt_id=NEW.experiment_attempt_id AND s.ordinal<>(SELECT count(*) FROM public.gdss_experiment_materialized_scenario x WHERE x.experiment_attempt_id=s.experiment_attempt_id AND x.ordinal<s.ordinal)) THEN RAISE EXCEPTION 'Incomplete scenario universe at RUNNING'; END IF;
      ELSE IF prior.sequence<>1 OR NEW.sequence<>2 OR NEW.status NOT IN ('COMPLETED','COMPLETED_WITH_FAILURES','FAILED','ABORTED') OR NEW.result_hash IS NULL OR NEW.completeness IS NULL THEN RAISE EXCEPTION 'Exactly one terminal experiment event is required'; END IF; SELECT format_version INTO result_format FROM public.gdss_experiment_artifact WHERE hash=NEW.result_hash; IF result_format IS DISTINCT FROM 'GDSS_EXPERIMENT_RESULT_JSON_V1' THEN RAISE EXCEPTION 'Terminal event requires result artifact'; END IF; IF EXISTS(SELECT 1 FROM public.gdss_experiment_materialized_scenario s LEFT JOIN LATERAL (SELECT state FROM public.gdss_experiment_scenario_execution e WHERE e.materialized_scenario_id=s.id ORDER BY sequence DESC LIMIT 1) q ON true WHERE s.experiment_attempt_id=NEW.experiment_attempt_id AND q.state NOT IN ('TERMINAL_SUCCESS','TERMINAL_FAILURE','NOT_DISPATCHED_ABORTED')) THEN RAISE EXCEPTION 'All scenarios must be terminally classified'; END IF; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss_experiment_result_ownership_guard() RETURNS TRIGGER AS $$
    DECLARE attempt_version UUID; definition_version UUID;
    BEGIN SELECT experiment_version_id INTO attempt_version FROM public.gdss_experiment_execution_attempt WHERE id=NEW.experiment_attempt_id;
      IF TG_TABLE_NAME='gdss_experiment_metric_result' THEN SELECT experiment_version_id INTO definition_version FROM public.gdss_experiment_metric_definition WHERE id=NEW.metric_definition_id;
      ELSE SELECT experiment_version_id INTO definition_version FROM public.gdss_experiment_comparison_definition WHERE id=NEW.comparison_definition_id; END IF;
      IF attempt_version IS DISTINCT FROM definition_version THEN RAISE EXCEPTION 'GDSS result definition belongs to another ExperimentVersion'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER gdss_experiment_version_validate BEFORE INSERT ON public.gdss_experiment_version FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_version_guard();
    CREATE TRIGGER gdss_experiment_version_mutation BEFORE UPDATE OR DELETE ON public.gdss_experiment_version FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_design_mutation_guard();
    CREATE TRIGGER gdss_experiment_identity_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_identity FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE TRIGGER gdss_experiment_factor_mutation BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_experiment_factor FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_design_mutation_guard();
    CREATE TRIGGER gdss_experiment_controlled_mutation BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_experiment_controlled_input FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_design_mutation_guard();
    CREATE TRIGGER gdss_experiment_metric_definition_mutation BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_experiment_metric_definition FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_design_mutation_guard();
    CREATE TRIGGER gdss_experiment_comparison_definition_mutation BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_experiment_comparison_definition FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_design_mutation_guard();
    CREATE TRIGGER gdss_experiment_lifecycle_validate BEFORE INSERT ON public.gdss_experiment_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_lifecycle_guard();
    CREATE TRIGGER gdss_experiment_attempt_validate BEFORE INSERT ON public.gdss_experiment_execution_attempt FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_attempt_guard();
    CREATE TRIGGER gdss_experiment_attempt_abort BEFORE UPDATE OR DELETE ON public.gdss_experiment_execution_attempt FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_abort_guard();
    CREATE TRIGGER gdss_experiment_scenario_event_validate BEFORE INSERT ON public.gdss_experiment_scenario_execution FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_scenario_event_guard();
    CREATE TRIGGER gdss_experiment_event_validate BEFORE INSERT ON public.gdss_experiment_execution_event FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_execution_event_guard();
    CREATE TRIGGER gdss_experiment_lifecycle_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_lifecycle_event FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE TRIGGER gdss_experiment_artifact_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_artifact FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE TRIGGER gdss_experiment_scenario_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_materialized_scenario FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE TRIGGER gdss_experiment_scenario_event_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_scenario_execution FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE TRIGGER gdss_experiment_event_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_execution_event FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE TRIGGER gdss_experiment_metric_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_metric_result FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE TRIGGER gdss_experiment_comparison_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_comparison_result FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE TRIGGER gdss_experiment_diagnostic_append_only BEFORE UPDATE OR DELETE ON public.gdss_experiment_diagnostic FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_reject_evidence_mutation();
    CREATE CONSTRAINT TRIGGER gdss_experiment_metric_ownership AFTER INSERT ON public.gdss_experiment_metric_result DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_result_ownership_guard();
    CREATE CONSTRAINT TRIGGER gdss_experiment_comparison_ownership AFTER INSERT ON public.gdss_experiment_comparison_result DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.gdss_experiment_result_ownership_guard();
    CREATE INDEX gdss_experiment_identity_project_idx ON public.gdss_experiment_identity(project_id,canonical_name);
    CREATE INDEX gdss_experiment_version_identity_idx ON public.gdss_experiment_version(experiment_identity_id,version_number);
    CREATE INDEX gdss_experiment_version_base_idx ON public.gdss_experiment_version(model_version_id,binding_version_id);
    CREATE INDEX gdss_experiment_lifecycle_version_idx ON public.gdss_experiment_lifecycle_event(experiment_version_id,sequence);
    CREATE INDEX gdss_experiment_attempt_project_idx ON public.gdss_experiment_execution_attempt(project_id,created_at);
    CREATE INDEX gdss_experiment_attempt_version_idx ON public.gdss_experiment_execution_attempt(experiment_version_id,created_at);
    CREATE INDEX gdss_experiment_scenario_attempt_idx ON public.gdss_experiment_materialized_scenario(experiment_attempt_id,ordinal);
    CREATE INDEX gdss_experiment_scenario_input_idx ON public.gdss_experiment_materialized_scenario(simulation_input_hash);
    CREATE INDEX gdss_experiment_scenario_event_latest_idx ON public.gdss_experiment_scenario_execution(materialized_scenario_id,sequence DESC);
    CREATE INDEX gdss_experiment_scenario_claim_idx ON public.gdss_experiment_scenario_execution(state,lease_expires_at);
    CREATE INDEX gdss_experiment_event_attempt_idx ON public.gdss_experiment_execution_event(experiment_attempt_id,sequence);
    CREATE INDEX gdss_experiment_metric_attempt_idx ON public.gdss_experiment_metric_result(experiment_attempt_id,materialized_scenario_id);
    CREATE INDEX gdss_experiment_comparison_attempt_idx ON public.gdss_experiment_comparison_result(experiment_attempt_id);
    CREATE INDEX gdss_experiment_diagnostic_attempt_idx ON public.gdss_experiment_diagnostic(experiment_attempt_id,sequence);
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE public.gdss_experiment_diagnostic, public.gdss_experiment_comparison_result, public.gdss_experiment_metric_result, public.gdss_experiment_execution_event, public.gdss_experiment_scenario_execution, public.gdss_experiment_materialized_scenario, public.gdss_experiment_execution_attempt, public.gdss_experiment_artifact, public.gdss_experiment_comparison_definition, public.gdss_experiment_metric_definition, public.gdss_experiment_controlled_input, public.gdss_experiment_factor, public.gdss_experiment_lifecycle_event, public.gdss_experiment_version, public.gdss_experiment_identity;
    DROP FUNCTION IF EXISTS public.gdss_experiment_result_ownership_guard();
    DROP FUNCTION IF EXISTS public.gdss_experiment_execution_event_guard(), public.gdss_experiment_scenario_event_guard(), public.gdss_experiment_abort_guard(), public.gdss_experiment_attempt_guard(), public.gdss_experiment_lifecycle_guard(), public.gdss_experiment_design_mutation_guard(), public.gdss_experiment_version_guard(), public.gdss_experiment_reject_evidence_mutation();
    """)
