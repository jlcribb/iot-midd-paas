"""GDSS-006E domain assessment and predictive evidence assembly. Revision 0048."""

from alembic import op

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_domain_validity_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT, model_hash CHAR(64) NOT NULL,
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      validity_domain_hash CHAR(64) NOT NULL, validation_run_id UUID NOT NULL, target_key TEXT NOT NULL, horizon_key TEXT NOT NULL,
      context_snapshot JSONB NOT NULL, assessment_result TEXT NOT NULL CHECK(assessment_result IN('WITHIN_VALIDITY_DOMAIN','NEAR_DOMAIN_BOUNDARY','OUTSIDE_VALIDITY_DOMAIN','DOMAIN_UNKNOWN')),
      assessment_content JSONB NOT NULL, assessment_hash CHAR(64) NOT NULL CHECK(assessment_hash~'^[0-9a-f]{64}$'),
      idempotency_key TEXT NOT NULL, assessed_by TEXT NOT NULL, assessed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(validation_run_id,project_id) REFERENCES public.gdss_validation_run(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,assessment_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_domain_predicate_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, domain_assessment_id UUID NOT NULL,
      predicate_key TEXT NOT NULL, result TEXT NOT NULL CHECK(result IN('PASS','BOUNDARY','FAIL','UNKNOWN')), reason TEXT NOT NULL,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 63),
      FOREIGN KEY(domain_assessment_id,project_id) REFERENCES public.gdss_domain_validity_assessment(id,project_id) ON DELETE RESTRICT,
      UNIQUE(domain_assessment_id,predicate_key), UNIQUE(domain_assessment_id,ordinal));
    CREATE TABLE public.gdss_predictive_position_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      domain_assessment_id UUID NOT NULL, model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      validation_run_id UUID NOT NULL, target_key TEXT NOT NULL, horizon_key TEXT NOT NULL,
      position TEXT NOT NULL CHECK(position IN('INTERPOLATION','BOUNDARY_PREDICTION','EXTRAPOLATION','UNKNOWN_POSITION')),
      context_snapshot JSONB NOT NULL, support_envelope JSONB NOT NULL, assessment_content JSONB NOT NULL,
      assessment_hash CHAR(64) NOT NULL CHECK(assessment_hash~'^[0-9a-f]{64}$'), idempotency_key TEXT NOT NULL,
      assessed_by TEXT NOT NULL, assessed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(domain_assessment_id,project_id) REFERENCES public.gdss_domain_validity_assessment(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(validation_run_id,project_id) REFERENCES public.gdss_validation_run(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,assessment_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_predictive_evidence_negative_finding (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      target_key TEXT NOT NULL, horizon_key TEXT NOT NULL,
      finding_type TEXT NOT NULL CHECK(finding_type IN('MODEL_UNDERPERFORMS_BASELINE','HIGH_BIAS','LOW_COVERAGE','UNCERTAINTY_INSUFFICIENT','OUTSIDE_VALIDITY_DOMAIN','TEMPORAL_INTEGRITY_UNKNOWN','INDEPENDENCE_COMPROMISED')),
      source_artifact_type TEXT NOT NULL CHECK(source_artifact_type IN('VALIDATION_RUN','PREDICTION_PAIR_SET','METRIC_RESULT','BASELINE_COMPARISON_RESULT','UNCERTAINTY_ASSESSMENT','DOMAIN_VALIDITY_ASSESSMENT','PREDICTIVE_POSITION_ASSESSMENT')), source_artifact_id UUID NOT NULL, source_artifact_hash CHAR(64) NOT NULL,
      description TEXT NOT NULL, content_hash CHAR(64) NOT NULL, idempotency_key TEXT NOT NULL, registered_by TEXT NOT NULL,
      registered_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_predictive_evidence_conflict (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      target_key TEXT NOT NULL, horizon_key TEXT NOT NULL,
      conflict_type TEXT NOT NULL CHECK(conflict_type IN('METRIC_DIRECTION_CONFLICT','BASELINE_COMPARISON_CONFLICT','DOMAIN_SUPPORT_CONFLICT','UNCERTAINTY_CONFLICT')),
      source_artifact_type TEXT NOT NULL CHECK(source_artifact_type IN('VALIDATION_RUN','PREDICTION_PAIR_SET','METRIC_RESULT','BASELINE_COMPARISON_RESULT','UNCERTAINTY_ASSESSMENT','DOMAIN_VALIDITY_ASSESSMENT','PREDICTIVE_POSITION_ASSESSMENT')), source_artifact_id UUID NOT NULL, source_artifact_hash CHAR(64) NOT NULL,
      conflicting_artifact_ids UUID[] NOT NULL CHECK(cardinality(conflicting_artifact_ids) BETWEEN 2 AND 64),
      description TEXT NOT NULL, content_hash CHAR(64) NOT NULL, idempotency_key TEXT NOT NULL, registered_by TEXT NOT NULL,
      registered_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_predictive_evidence_limitation (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT,
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      target_key TEXT NOT NULL, horizon_key TEXT NOT NULL,
      limitation_type TEXT NOT NULL CHECK(limitation_type IN('UNCERTAINTY_PARTIAL','EXTERNAL_VALIDATION_ABSENT','DOMAIN_COVERAGE_NARROW','HOLDOUT_SINGLE_USE_CONSUMED','PLATFORM_ONLY_PROSPECTIVITY','DEPENDENT_GROUP_LIMITATION','NEAR_DUPLICATE_DETECTION_UNAVAILABLE','SPARSE_HORIZON_COVERAGE','DATA_QUALITY_UNKNOWN')),
      source_artifact_type TEXT NOT NULL CHECK(source_artifact_type IN('VALIDATION_RUN','PREDICTION_PAIR_SET','METRIC_RESULT','BASELINE_COMPARISON_RESULT','UNCERTAINTY_ASSESSMENT','DOMAIN_VALIDITY_ASSESSMENT','PREDICTIVE_POSITION_ASSESSMENT')), source_artifact_id UUID NOT NULL, source_artifact_hash CHAR(64) NOT NULL,
      description TEXT NOT NULL, content_hash CHAR(64) NOT NULL, idempotency_key TEXT NOT NULL, registered_by TEXT NOT NULL,
      registered_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_predictive_evidence_set (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_PREDICTIVE_EVIDENCE_SET_V1'),
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT, model_hash CHAR(64) NOT NULL,
      protocol_version_id UUID NOT NULL REFERENCES public.gdss_validation_protocol_version(id) ON DELETE RESTRICT, protocol_hash CHAR(64) NOT NULL,
      validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT, validity_domain_hash CHAR(64) NOT NULL,
      partition_plan_version_id UUID NOT NULL REFERENCES public.gdss_partition_plan_version(id) ON DELETE RESTRICT, partition_plan_hash CHAR(64) NOT NULL,
      snapshot_id UUID NOT NULL, snapshot_hash CHAR(64) NOT NULL, target_key TEXT NOT NULL, horizon_key TEXT NOT NULL,
      validation_run_ids UUID[] NOT NULL CHECK(cardinality(validation_run_ids) BETWEEN 1 AND 100),
      pair_set_ids UUID[] NOT NULL CHECK(cardinality(pair_set_ids) BETWEEN 1 AND 100),
      domain_assessment_ids UUID[] NOT NULL CHECK(cardinality(domain_assessment_ids) BETWEEN 1 AND 1000),
      position_assessment_ids UUID[] NOT NULL CHECK(cardinality(position_assessment_ids) BETWEEN 1 AND 1000),
      reference_count INTEGER NOT NULL CHECK(reference_count BETWEEN 1 AND 10000), manifest JSONB NOT NULL,
      canonical_manifest TEXT NOT NULL, content_hash CHAR(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'),
      idempotency_key TEXT NOT NULL, materialized_by TEXT NOT NULL, materialized_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(snapshot_id,project_id) REFERENCES public.gdss_dataset_snapshot(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_predictive_evidence_reference (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, evidence_set_id UUID NOT NULL,
      ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 9999), artifact_type TEXT NOT NULL CHECK(artifact_type IN('VALIDATION_PROTOCOL_VERSION','PARTITION_PLAN_VERSION','DATASET_SNAPSHOT','VALIDATION_RUN','PREDICTION_PAIR_SET','METRIC_RESULT','BASELINE_COMPARISON_RESULT','UNCERTAINTY_ASSESSMENT','PREDICTION_INTERVAL','INTERVAL_ASSESSMENT','DOMAIN_VALIDITY_ASSESSMENT','PREDICTIVE_POSITION_ASSESSMENT','NEGATIVE_FINDING','EVIDENCE_CONFLICT','EVIDENCE_LIMITATION')),
      artifact_id UUID NOT NULL, artifact_hash CHAR(64) NOT NULL, source_phase TEXT NOT NULL CHECK(source_phase IN('GDSS-006A','GDSS-006B','GDSS-006C','GDSS-006D','GDSS-006E')),
      role TEXT NOT NULL CHECK(role IN('SUPPORTING','CONTRADICTING','LIMITING','CONTEXTUAL','INVALIDATING')),
      reference_hash CHAR(64) NOT NULL, FOREIGN KEY(evidence_set_id,project_id) REFERENCES public.gdss_predictive_evidence_set(id,project_id) ON DELETE RESTRICT,
      UNIQUE(evidence_set_id,ordinal), UNIQUE(evidence_set_id,artifact_type,artifact_id), UNIQUE(evidence_set_id,reference_hash));
    CREATE TABLE public.gdss_evidence_completeness_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, evidence_set_id UUID NOT NULL,
      state TEXT NOT NULL CHECK(state IN('COMPLETE','PARTIAL','INSUFFICIENT','UNKNOWN')), required_artifact_types TEXT[] NOT NULL,
      present_artifact_types TEXT[] NOT NULL, missing_artifact_types TEXT[] NOT NULL, content_hash CHAR(64) NOT NULL,
      assessed_by TEXT NOT NULL, assessed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(evidence_set_id,project_id) REFERENCES public.gdss_predictive_evidence_set(id,project_id) ON DELETE RESTRICT,
      UNIQUE(evidence_set_id), UNIQUE(project_id,content_hash), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_evidence_strength_profile (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, evidence_set_id UUID NOT NULL,
      method_version TEXT NOT NULL CHECK(method_version='GDSS_EVIDENCE_STRENGTH_V1'), content_hash CHAR(64) NOT NULL,
      derived_by TEXT NOT NULL, derived_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(evidence_set_id,project_id) REFERENCES public.gdss_predictive_evidence_set(id,project_id) ON DELETE RESTRICT,
      UNIQUE(evidence_set_id,method_version), UNIQUE(project_id,content_hash), UNIQUE(id,project_id));
    CREATE TABLE public.gdss_evidence_strength_axis_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, profile_id UUID NOT NULL,
      axis TEXT NOT NULL CHECK(axis IN('INDEPENDENCE','TEMPORALITY','DOMAIN_COVERAGE','UNCERTAINTY_COMPLETENESS','BASELINE_STRENGTH','REPLICATION','DATA_QUALITY')),
      state TEXT NOT NULL CHECK(state IN('UNKNOWN','INSUFFICIENT','LIMITED','ADEQUATE','STRONG')), evidence JSONB NOT NULL,
      content_hash CHAR(64) NOT NULL, FOREIGN KEY(profile_id,project_id) REFERENCES public.gdss_evidence_strength_profile(id,project_id) ON DELETE RESTRICT,
      UNIQUE(profile_id,axis), UNIQUE(project_id,content_hash));

    CREATE FUNCTION public.gdss006e_reject_mutation() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'EVIDENCE_SET_IMMUTABLE'; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006e_guard_domain_assessment() RETURNS TRIGGER AS $$
    DECLARE rp UUID; rm UUID; rh TEXT; rd UUID; rdh TEXT; pr UUID; dp UUID; dh TEXT;
    BEGIN
      SELECT project_id,model_version_id,model_hash,validity_domain_version_id,validity_domain_hash,protocol_version_id INTO rp,rm,rh,rd,rdh,pr FROM public.gdss_validation_run WHERE id=NEW.validation_run_id;
      SELECT i.project_id,v.content_hash INTO dp,dh FROM public.gdss_validity_domain_version v JOIN public.gdss_validity_domain_identity i ON i.id=v.domain_identity_id WHERE v.id=NEW.validity_domain_version_id;
      IF rp IS DISTINCT FROM NEW.project_id OR dp IS DISTINCT FROM NEW.project_id OR rm IS DISTINCT FROM NEW.model_version_id OR rh IS DISTINCT FROM NEW.model_hash OR rd IS DISTINCT FROM NEW.validity_domain_version_id OR rdh IS DISTINCT FROM NEW.validity_domain_hash OR dh IS DISTINCT FROM NEW.validity_domain_hash THEN RAISE EXCEPTION 'DOMAIN_EVIDENCE_MISMATCH'; END IF;
      IF NOT EXISTS(SELECT 1 FROM public.gdss_validation_target WHERE protocol_version_id=pr AND target_key=NEW.target_key) THEN RAISE EXCEPTION 'TARGET_EVIDENCE_MISMATCH'; END IF;
      IF NOT EXISTS(SELECT 1 FROM public.gdss_validation_horizon WHERE protocol_version_id=pr AND horizon_key=NEW.horizon_key) THEN RAISE EXCEPTION 'HORIZON_EVIDENCE_MISMATCH'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006e_guard_position() RETURNS TRIGGER AS $$
    DECLARE d RECORD;
    BEGIN SELECT * INTO d FROM public.gdss_domain_validity_assessment WHERE id=NEW.domain_assessment_id;
      IF d.project_id IS DISTINCT FROM NEW.project_id OR d.model_version_id IS DISTINCT FROM NEW.model_version_id OR d.validity_domain_version_id IS DISTINCT FROM NEW.validity_domain_version_id OR d.validation_run_id IS DISTINCT FROM NEW.validation_run_id OR d.target_key IS DISTINCT FROM NEW.target_key OR d.horizon_key IS DISTINCT FROM NEW.horizon_key THEN RAISE EXCEPTION 'DOMAIN_EVIDENCE_MISMATCH'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006e_guard_evidence_set() RETURNS TRIGGER AS $$
    DECLARE mp UUID; mh TEXT; pp UUID; ph TEXT; ps TEXT; dp UUID; dh TEXT; ds TEXT; xp UUID; xh TEXT; xs BOOLEAN; bp UUID; bh TEXT; bs TEXT; bad INTEGER;
    BEGIN
      SELECT i.project_id,v.content_hash INTO mp,mh FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.model_version_id;
      SELECT i.project_id,v.content_hash,v.status INTO pp,ph,ps FROM public.gdss_validation_protocol_version v JOIN public.gdss_validation_protocol_identity i ON i.id=v.protocol_identity_id WHERE v.id=NEW.protocol_version_id;
      SELECT i.project_id,v.content_hash,v.status INTO dp,dh,ds FROM public.gdss_validity_domain_version v JOIN public.gdss_validity_domain_identity i ON i.id=v.domain_identity_id WHERE v.id=NEW.validity_domain_version_id;
      SELECT i.project_id,v.content_hash,v.status INTO bp,bh,bs FROM public.gdss_partition_plan_version v JOIN public.gdss_partition_plan_identity i ON i.id=v.partition_identity_id WHERE v.id=NEW.partition_plan_version_id;
      SELECT project_id,snapshot_hash,materialized INTO xp,xh,xs FROM public.gdss_dataset_snapshot WHERE id=NEW.snapshot_id;
      IF mp IS DISTINCT FROM NEW.project_id OR pp IS DISTINCT FROM NEW.project_id OR dp IS DISTINCT FROM NEW.project_id OR bp IS DISTINCT FROM NEW.project_id OR xp IS DISTINCT FROM NEW.project_id OR mh IS DISTINCT FROM NEW.model_hash OR ph IS DISTINCT FROM NEW.protocol_hash OR dh IS DISTINCT FROM NEW.validity_domain_hash OR bh IS DISTINCT FROM NEW.partition_plan_hash OR xh IS DISTINCT FROM NEW.snapshot_hash OR NOT xs OR ps='INVALIDATED' OR ds='INVALIDATED' OR bs='INVALIDATED' THEN RAISE EXCEPTION 'EVIDENCE_REFERENCE_INVALID'; END IF;
      IF NOT EXISTS(SELECT 1 FROM public.gdss_validation_target WHERE protocol_version_id=NEW.protocol_version_id AND target_key=NEW.target_key) THEN RAISE EXCEPTION 'TARGET_EVIDENCE_MISMATCH'; END IF;
      IF NOT EXISTS(SELECT 1 FROM public.gdss_validation_horizon WHERE protocol_version_id=NEW.protocol_version_id AND horizon_key=NEW.horizon_key) THEN RAISE EXCEPTION 'HORIZON_EVIDENCE_MISMATCH'; END IF;
      SELECT count(*) INTO bad FROM unnest(NEW.validation_run_ids) r(id) LEFT JOIN public.gdss_validation_run v ON v.id=r.id WHERE v.id IS NULL OR v.project_id IS DISTINCT FROM NEW.project_id OR v.model_version_id IS DISTINCT FROM NEW.model_version_id OR v.protocol_version_id IS DISTINCT FROM NEW.protocol_version_id OR v.validity_domain_version_id IS DISTINCT FROM NEW.validity_domain_version_id OR v.partition_plan_version_id IS DISTINCT FROM NEW.partition_plan_version_id OR v.snapshot_id IS DISTINCT FROM NEW.snapshot_id;
      IF bad>0 THEN RAISE EXCEPTION 'MODEL_VERSION_EVIDENCE_MISMATCH'; END IF;
      SELECT count(*) INTO bad FROM unnest(NEW.pair_set_ids) s(id) LEFT JOIN public.gdss_prediction_pair_set p ON p.id=s.id WHERE p.id IS NULL OR p.project_id IS DISTINCT FROM NEW.project_id OR p.target_key IS DISTINCT FROM NEW.target_key OR p.horizon_key IS DISTINCT FROM NEW.horizon_key;
      IF bad>0 THEN RAISE EXCEPTION 'HORIZON_EVIDENCE_MISMATCH'; END IF;
      SELECT count(*) INTO bad FROM unnest(NEW.domain_assessment_ids) a(id) LEFT JOIN public.gdss_domain_validity_assessment d ON d.id=a.id WHERE d.id IS NULL OR d.project_id IS DISTINCT FROM NEW.project_id OR d.model_version_id IS DISTINCT FROM NEW.model_version_id OR d.validity_domain_version_id IS DISTINCT FROM NEW.validity_domain_version_id OR d.target_key IS DISTINCT FROM NEW.target_key OR d.horizon_key IS DISTINCT FROM NEW.horizon_key;
      IF bad>0 THEN RAISE EXCEPTION 'DOMAIN_EVIDENCE_MISMATCH'; END IF;
      SELECT count(*) INTO bad FROM unnest(NEW.position_assessment_ids) a(id) LEFT JOIN public.gdss_predictive_position_assessment d ON d.id=a.id WHERE d.id IS NULL OR d.project_id IS DISTINCT FROM NEW.project_id OR d.model_version_id IS DISTINCT FROM NEW.model_version_id OR d.validity_domain_version_id IS DISTINCT FROM NEW.validity_domain_version_id OR d.target_key IS DISTINCT FROM NEW.target_key OR d.horizon_key IS DISTINCT FROM NEW.horizon_key;
      IF bad>0 THEN RAISE EXCEPTION 'DOMAIN_EVIDENCE_MISMATCH'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006e_guard_reference() RETURNS TRIGGER AS $$
    DECLARE hp UUID; actual TEXT; invalid BOOLEAN:=FALSE; current_count INTEGER; expected_count INTEGER;
    BEGIN
      SELECT count(r.id),s.reference_count INTO current_count,expected_count FROM public.gdss_predictive_evidence_set s LEFT JOIN public.gdss_predictive_evidence_reference r ON r.evidence_set_id=s.id WHERE s.id=NEW.evidence_set_id GROUP BY s.reference_count;
      IF expected_count IS NULL OR current_count>=expected_count OR NEW.ordinal<>current_count THEN RAISE EXCEPTION 'EVIDENCE_SET_IMMUTABLE'; END IF;
      CASE NEW.artifact_type
        WHEN 'VALIDATION_PROTOCOL_VERSION' THEN SELECT i.project_id,v.content_hash,(v.status='INVALIDATED') INTO hp,actual,invalid FROM public.gdss_validation_protocol_version v JOIN public.gdss_validation_protocol_identity i ON i.id=v.protocol_identity_id WHERE v.id=NEW.artifact_id;
        WHEN 'PARTITION_PLAN_VERSION' THEN SELECT i.project_id,v.content_hash,(v.status='INVALIDATED') INTO hp,actual,invalid FROM public.gdss_partition_plan_version v JOIN public.gdss_partition_plan_identity i ON i.id=v.partition_identity_id WHERE v.id=NEW.artifact_id;
        WHEN 'DATASET_SNAPSHOT' THEN SELECT project_id,snapshot_hash,FALSE INTO hp,actual,invalid FROM public.gdss_dataset_snapshot WHERE id=NEW.artifact_id;
        WHEN 'VALIDATION_RUN' THEN SELECT project_id,content_hash,(status IN('FAILED','INVALIDATED')) INTO hp,actual,invalid FROM public.gdss_validation_run WHERE id=NEW.artifact_id;
        WHEN 'PREDICTION_PAIR_SET' THEN SELECT project_id,pair_set_hash,FALSE INTO hp,actual,invalid FROM public.gdss_prediction_pair_set WHERE id=NEW.artifact_id;
        WHEN 'METRIC_RESULT' THEN SELECT project_id,content_hash,(status='INVALIDATED') INTO hp,actual,invalid FROM public.gdss_metric_result WHERE id=NEW.artifact_id;
        WHEN 'BASELINE_COMPARISON_RESULT' THEN SELECT project_id,content_hash,FALSE INTO hp,actual,invalid FROM public.gdss_baseline_comparison_result WHERE id=NEW.artifact_id;
        WHEN 'UNCERTAINTY_ASSESSMENT' THEN SELECT project_id,content_hash,FALSE INTO hp,actual,invalid FROM public.gdss_uncertainty_assessment WHERE id=NEW.artifact_id;
        WHEN 'PREDICTION_INTERVAL' THEN SELECT project_id,content_hash,FALSE INTO hp,actual,invalid FROM public.gdss_prediction_interval WHERE id=NEW.artifact_id;
        WHEN 'INTERVAL_ASSESSMENT' THEN SELECT project_id,content_hash,FALSE INTO hp,actual,invalid FROM public.gdss_interval_assessment WHERE id=NEW.artifact_id;
        WHEN 'DOMAIN_VALIDITY_ASSESSMENT' THEN SELECT project_id,assessment_hash,FALSE INTO hp,actual,invalid FROM public.gdss_domain_validity_assessment WHERE id=NEW.artifact_id;
        WHEN 'PREDICTIVE_POSITION_ASSESSMENT' THEN SELECT project_id,assessment_hash,FALSE INTO hp,actual,invalid FROM public.gdss_predictive_position_assessment WHERE id=NEW.artifact_id;
        WHEN 'NEGATIVE_FINDING' THEN SELECT project_id,content_hash,FALSE INTO hp,actual,invalid FROM public.gdss_predictive_evidence_negative_finding WHERE id=NEW.artifact_id;
        WHEN 'EVIDENCE_CONFLICT' THEN SELECT project_id,content_hash,FALSE INTO hp,actual,invalid FROM public.gdss_predictive_evidence_conflict WHERE id=NEW.artifact_id;
        WHEN 'EVIDENCE_LIMITATION' THEN SELECT project_id,content_hash,FALSE INTO hp,actual,invalid FROM public.gdss_predictive_evidence_limitation WHERE id=NEW.artifact_id;
      END CASE;
      IF hp IS NULL OR hp IS DISTINCT FROM NEW.project_id OR actual IS DISTINCT FROM NEW.artifact_hash THEN RAISE EXCEPTION 'EVIDENCE_REFERENCE_INVALID'; END IF;
      IF invalid AND NEW.role='SUPPORTING' THEN RAISE EXCEPTION 'EVIDENCE_REFERENCE_INVALIDATED'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006e_guard_scoped_evidence() RETURNS TRIGGER AS $$
    DECLARE hp UUID; actual TEXT; mv UUID; pv UUID; dv UUID; tk TEXT; hk TEXT;
    BEGIN
      CASE NEW.source_artifact_type
        WHEN 'VALIDATION_RUN' THEN SELECT project_id,content_hash,model_version_id,protocol_version_id,validity_domain_version_id,NEW.target_key,NEW.horizon_key INTO hp,actual,mv,pv,dv,tk,hk FROM public.gdss_validation_run WHERE id=NEW.source_artifact_id AND EXISTS(SELECT 1 FROM public.gdss_validation_target WHERE protocol_version_id=gdss_validation_run.protocol_version_id AND target_key=NEW.target_key) AND EXISTS(SELECT 1 FROM public.gdss_validation_horizon WHERE protocol_version_id=gdss_validation_run.protocol_version_id AND horizon_key=NEW.horizon_key);
        WHEN 'PREDICTION_PAIR_SET' THEN SELECT s.project_id,s.pair_set_hash,p.model_version_id,r.protocol_version_id,r.validity_domain_version_id,s.target_key,s.horizon_key INTO hp,actual,mv,pv,dv,tk,hk FROM public.gdss_prediction_pair_set s JOIN public.gdss_prediction_pair_set_member sm ON sm.pair_set_id=s.id JOIN public.gdss_prediction_observation_pair po ON po.id=sm.pair_id JOIN public.gdss_prediction_record p ON p.id=po.prediction_id JOIN public.gdss_validation_run r ON r.id=p.validation_run_id WHERE s.id=NEW.source_artifact_id LIMIT 1;
        WHEN 'METRIC_RESULT' THEN SELECT m.project_id,m.content_hash,m.model_version_id,m.protocol_version_id,p.validity_domain_version_id,m.target_key,m.horizon_key INTO hp,actual,mv,pv,dv,tk,hk FROM public.gdss_metric_result m JOIN public.gdss_validation_protocol_version p ON p.id=m.protocol_version_id WHERE m.id=NEW.source_artifact_id;
        WHEN 'BASELINE_COMPARISON_RESULT' THEN SELECT c.project_id,c.content_hash,m.model_version_id,m.protocol_version_id,p.validity_domain_version_id,m.target_key,m.horizon_key INTO hp,actual,mv,pv,dv,tk,hk FROM public.gdss_baseline_comparison_result c JOIN public.gdss_metric_result m ON m.id=c.model_metric_result_id JOIN public.gdss_validation_protocol_version p ON p.id=m.protocol_version_id WHERE c.id=NEW.source_artifact_id;
        WHEN 'UNCERTAINTY_ASSESSMENT' THEN SELECT u.project_id,u.content_hash,r.model_version_id,r.protocol_version_id,r.validity_domain_version_id,s.target_key,s.horizon_key INTO hp,actual,mv,pv,dv,tk,hk FROM public.gdss_uncertainty_assessment u JOIN public.gdss_validation_run r ON r.id=u.run_id JOIN public.gdss_prediction_pair_set s ON s.id=u.pair_set_id WHERE u.id=NEW.source_artifact_id;
        WHEN 'DOMAIN_VALIDITY_ASSESSMENT' THEN SELECT d.project_id,d.assessment_hash,d.model_version_id,r.protocol_version_id,d.validity_domain_version_id,d.target_key,d.horizon_key INTO hp,actual,mv,pv,dv,tk,hk FROM public.gdss_domain_validity_assessment d JOIN public.gdss_validation_run r ON r.id=d.validation_run_id WHERE d.id=NEW.source_artifact_id;
        WHEN 'PREDICTIVE_POSITION_ASSESSMENT' THEN SELECT d.project_id,d.assessment_hash,d.model_version_id,r.protocol_version_id,d.validity_domain_version_id,d.target_key,d.horizon_key INTO hp,actual,mv,pv,dv,tk,hk FROM public.gdss_predictive_position_assessment d JOIN public.gdss_validation_run r ON r.id=d.validation_run_id WHERE d.id=NEW.source_artifact_id;
      END CASE;
      IF hp IS NULL OR hp IS DISTINCT FROM NEW.project_id OR actual IS DISTINCT FROM NEW.source_artifact_hash OR mv IS DISTINCT FROM NEW.model_version_id OR pv IS DISTINCT FROM NEW.protocol_version_id OR dv IS DISTINCT FROM NEW.validity_domain_version_id OR tk IS DISTINCT FROM NEW.target_key OR hk IS DISTINCT FROM NEW.horizon_key THEN RAISE EXCEPTION 'EVIDENCE_REFERENCE_INVALID'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss006e_domain_guard BEFORE INSERT ON public.gdss_domain_validity_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006e_guard_domain_assessment();
    CREATE TRIGGER trg_gdss006e_position_guard BEFORE INSERT ON public.gdss_predictive_position_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006e_guard_position();
    CREATE TRIGGER trg_gdss006e_set_guard BEFORE INSERT ON public.gdss_predictive_evidence_set FOR EACH ROW EXECUTE FUNCTION public.gdss006e_guard_evidence_set();
    CREATE TRIGGER trg_gdss006e_reference_guard BEFORE INSERT ON public.gdss_predictive_evidence_reference FOR EACH ROW EXECUTE FUNCTION public.gdss006e_guard_reference();
    CREATE TRIGGER trg_gdss006e_negative_guard BEFORE INSERT ON public.gdss_predictive_evidence_negative_finding FOR EACH ROW EXECUTE FUNCTION public.gdss006e_guard_scoped_evidence();
    CREATE TRIGGER trg_gdss006e_conflict_guard BEFORE INSERT ON public.gdss_predictive_evidence_conflict FOR EACH ROW EXECUTE FUNCTION public.gdss006e_guard_scoped_evidence();
    CREATE TRIGGER trg_gdss006e_limitation_guard BEFORE INSERT ON public.gdss_predictive_evidence_limitation FOR EACH ROW EXECUTE FUNCTION public.gdss006e_guard_scoped_evidence();
    CREATE TRIGGER trg_gdss006e_domain_history BEFORE UPDATE OR DELETE ON public.gdss_domain_validity_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_predicate_history BEFORE UPDATE OR DELETE ON public.gdss_domain_predicate_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_position_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_position_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_negative_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_evidence_negative_finding FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_conflict_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_evidence_conflict FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_limitation_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_evidence_limitation FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_set_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_evidence_set FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_reference_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_evidence_reference FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_completeness_history BEFORE UPDATE OR DELETE ON public.gdss_evidence_completeness_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_profile_history BEFORE UPDATE OR DELETE ON public.gdss_evidence_strength_profile FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    CREATE TRIGGER trg_gdss006e_axis_history BEFORE UPDATE OR DELETE ON public.gdss_evidence_strength_axis_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006e_reject_mutation();
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE IF EXISTS public.gdss_evidence_strength_axis_assessment,public.gdss_evidence_strength_profile,
      public.gdss_evidence_completeness_assessment,public.gdss_predictive_evidence_reference,
      public.gdss_predictive_evidence_set,public.gdss_predictive_evidence_limitation,
      public.gdss_predictive_evidence_conflict,public.gdss_predictive_evidence_negative_finding,
      public.gdss_predictive_position_assessment,public.gdss_domain_predicate_assessment,
      public.gdss_domain_validity_assessment CASCADE;
    DROP FUNCTION IF EXISTS public.gdss006e_guard_reference(),public.gdss006e_guard_evidence_set(),
      public.gdss006e_guard_scoped_evidence(),public.gdss006e_guard_position(),public.gdss006e_guard_domain_assessment(),public.gdss006e_reject_mutation() CASCADE;
    """)
