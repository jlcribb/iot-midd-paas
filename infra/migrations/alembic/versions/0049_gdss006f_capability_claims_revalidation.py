"""GDSS-006F predictive capability, governed claims and revalidation. Revision 0049."""

from alembic import op

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE TABLE public.gdss_capability_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_CAPABILITY_ASSESSMENT_V1'),
      evidence_set_id UUID NOT NULL, evidence_set_hash CHAR(64) NOT NULL,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT, model_content_hash CHAR(64) NOT NULL,
      target_key TEXT NOT NULL, horizon_key TEXT NOT NULL, validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      protocol_family TEXT NOT NULL, metric_profile TEXT[] NOT NULL CHECK(cardinality(metric_profile) BETWEEN 1 AND 64),
      baseline_profile TEXT[] NOT NULL CHECK(cardinality(baseline_profile) BETWEEN 1 AND 32),
      uncertainty_profile TEXT[] NOT NULL CHECK(cardinality(uncertainty_profile) BETWEEN 1 AND 32),
      evidence_period_start BIGINT NOT NULL, evidence_period_end BIGINT NOT NULL CHECK(evidence_period_start<=evidence_period_end),
      domain_scope JSONB NOT NULL CHECK(jsonb_typeof(domain_scope)='array'), assessment_policy_version TEXT NOT NULL CHECK(assessment_policy_version='GDSS_CAPABILITY_POLICY_V1'),
      state TEXT NOT NULL CHECK(state IN('NOT_EVALUATED','INSUFFICIENT_EVIDENCE','EVIDENCE_OF_LIMITED_CAPABILITY','EVIDENCE_OF_CAPABILITY','CONFLICTING_EVIDENCE','EVIDENCE_OF_FAILURE','INVALIDATED')),
      rationale_code TEXT NOT NULL, axis_explanation JSONB NOT NULL, limitation_manifest JSONB NOT NULL,
      conflict_manifest JSONB NOT NULL, negative_evidence_manifest JSONB NOT NULL, causal_reference TEXT NULL,
      content_hash CHAR(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'), predecessor_assessment_id UUID NULL,
      idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(evidence_set_id,project_id) REFERENCES public.gdss_predictive_evidence_set(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predecessor_assessment_id,project_id) REFERENCES public.gdss_capability_assessment(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_predictive_claim_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      canonical_key TEXT NOT NULL, idempotency_key TEXT NOT NULL, created_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(project_id,canonical_key), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_predictive_claim_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, claim_identity_id UUID NOT NULL,
      claim_version INTEGER NOT NULL CHECK(claim_version>0), semantic_version TEXT NOT NULL CHECK(semantic_version='GDSS_PREDICTIVE_CLAIM_V1'),
      capability_assessment_id UUID NOT NULL, capability_assessment_hash CHAR(64) NOT NULL,
      evidence_set_id UUID NOT NULL, evidence_set_hash CHAR(64) NOT NULL,
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT, model_content_hash CHAR(64) NOT NULL,
      target_key TEXT NOT NULL, horizon_key TEXT NOT NULL, validity_domain_version_id UUID NOT NULL REFERENCES public.gdss_validity_domain_version(id) ON DELETE RESTRICT,
      claim_scope JSONB NOT NULL CHECK(jsonb_typeof(claim_scope)='object'), limitation_manifest JSONB NOT NULL,
      negative_evidence_manifest JSONB NOT NULL, conflict_manifest JSONB NOT NULL, uncertainty_summary JSONB NOT NULL,
      template_version TEXT NOT NULL CHECK(template_version='GDSS_PREDICTIVE_CLAIM_TEMPLATE_V1'), rendered_human_text TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN('DRAFT','EVIDENCE_ASSEMBLED','REVIEW_REQUIRED','AUTHORIZED','REJECTED','SUPERSEDED','REVOKED')),
      content_hash CHAR(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'), predecessor_claim_id UUID NULL,
      valid_through_epoch_micros BIGINT NULL, idempotency_key TEXT NOT NULL, authored_by TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(), updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(claim_identity_id,project_id) REFERENCES public.gdss_predictive_claim_identity(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(capability_assessment_id,project_id) REFERENCES public.gdss_capability_assessment(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(evidence_set_id,project_id) REFERENCES public.gdss_predictive_evidence_set(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predecessor_claim_id,project_id) REFERENCES public.gdss_predictive_claim_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(claim_identity_id,claim_version), UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_predictive_claim_event (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, claim_id UUID NOT NULL,
      sequence INTEGER NOT NULL CHECK(sequence>0), from_status TEXT NULL, to_status TEXT NOT NULL,
      actor TEXT NOT NULL, reason TEXT NOT NULL, idempotency_key TEXT NOT NULL, event_hash CHAR(64) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(claim_id,project_id) REFERENCES public.gdss_predictive_claim_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(claim_id,sequence), UNIQUE(project_id,idempotency_key), UNIQUE(project_id,event_hash));

    CREATE TABLE public.gdss_predictive_claim_review (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, claim_id UUID NOT NULL,
      claim_hash CHAR(64) NOT NULL, reviewer TEXT NOT NULL,
      decision TEXT NOT NULL CHECK(decision IN('APPROVE_FOR_AUTHORIZATION','REQUEST_REVISION','REJECT')),
      rationale TEXT NOT NULL, scope_findings JSONB NOT NULL, evidence_findings JSONB NOT NULL,
      content_hash CHAR(64) NOT NULL, idempotency_key TEXT NOT NULL, reviewed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(claim_id,project_id) REFERENCES public.gdss_predictive_claim_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_predictive_claim_authorization (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, claim_id UUID NOT NULL,
      authorizer TEXT NOT NULL, decision TEXT NOT NULL CHECK(decision='AUTHORIZE'), authorized_scope JSONB NOT NULL,
      authorized_scope_hash CHAR(64) NOT NULL, claim_hash CHAR(64) NOT NULL, assessment_hash CHAR(64) NOT NULL,
      evidence_set_hash CHAR(64) NOT NULL, sod_exception_reason TEXT NULL, content_hash CHAR(64) NOT NULL,
      idempotency_key TEXT NOT NULL, authorized_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(claim_id,project_id) REFERENCES public.gdss_predictive_claim_version(id,project_id) ON DELETE RESTRICT,
      UNIQUE(claim_id), UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_predictive_claim_revocation (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL, claim_id UUID NOT NULL, authorization_id UUID NOT NULL,
      actor TEXT NOT NULL, reason TEXT NOT NULL, trigger_type TEXT NOT NULL, content_hash CHAR(64) NOT NULL,
      idempotency_key TEXT NOT NULL, revoked_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(claim_id,project_id) REFERENCES public.gdss_predictive_claim_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(authorization_id,project_id) REFERENCES public.gdss_predictive_claim_authorization(id,project_id) ON DELETE RESTRICT,
      UNIQUE(claim_id), UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE TABLE public.gdss_revalidation_trigger_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      capability_assessment_id UUID NOT NULL, claim_id UUID NULL, evidence_set_id UUID NOT NULL,
      trigger_type TEXT NOT NULL CHECK(trigger_type IN('MODEL_STRUCTURE_CHANGED','FORMULA_CHANGED','PARAMETER_REGIME_CHANGED','NUMERICAL_METHOD_CHANGED','INPUT_DOMAIN_CHANGED','SENSOR_CHANGED','VALIDITY_DOMAIN_CHANGED','HORIZON_CHANGED','DRIFT_DETECTED','CONTRADICTORY_EVIDENCE','BASELINE_CHANGED','METRIC_CHANGED')),
      state TEXT NOT NULL CHECK(state IN('DETECTED','REVIEW_REQUIRED','ACKNOWLEDGED','REVALIDATION_REQUIRED','RESOLVED','INVALIDATED')),
      causal_artifact_id UUID NOT NULL, causal_artifact_hash CHAR(64) NOT NULL, rationale TEXT NOT NULL,
      predecessor_trigger_id UUID NULL, content_hash CHAR(64) NOT NULL, idempotency_key TEXT NOT NULL,
      assessed_by TEXT NOT NULL, assessed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(capability_assessment_id,project_id) REFERENCES public.gdss_capability_assessment(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(claim_id,project_id) REFERENCES public.gdss_predictive_claim_version(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(evidence_set_id,project_id) REFERENCES public.gdss_predictive_evidence_set(id,project_id) ON DELETE RESTRICT,
      FOREIGN KEY(predecessor_trigger_id,project_id) REFERENCES public.gdss_revalidation_trigger_assessment(id,project_id) ON DELETE RESTRICT,
      UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));
    CREATE INDEX gdss_revalidation_trigger_unresolved_idx ON public.gdss_revalidation_trigger_assessment(project_id,claim_id,state) WHERE state IN('DETECTED','REVIEW_REQUIRED','REVALIDATION_REQUIRED');

    CREATE TABLE public.gdss_evidence_transfer_assessment (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      source_model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      target_model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      source_evidence_set_id UUID NOT NULL, source_evidence_set_hash CHAR(64) NOT NULL,
      requested_transfer_scope JSONB NOT NULL, requested_mode TEXT NOT NULL,
      result TEXT NOT NULL CHECK(result IN('FULL_REVALIDATION_REQUIRED','TRANSFER_REJECTED')),
      reason TEXT NOT NULL, content_hash CHAR(64) NOT NULL, idempotency_key TEXT NOT NULL,
      assessed_by TEXT NOT NULL, assessed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(source_evidence_set_id,project_id) REFERENCES public.gdss_predictive_evidence_set(id,project_id) ON DELETE RESTRICT,
      CHECK(source_model_version_id<>target_model_version_id),
      UNIQUE(project_id,content_hash), UNIQUE(project_id,idempotency_key), UNIQUE(id,project_id));

    CREATE FUNCTION public.gdss006f_reject_mutation() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'CAPABILITY_ASSESSMENT_IMMUTABLE'; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006f_guard_capability() RETURNS TRIGGER AS $$
    DECLARE s RECORD; axes INTEGER; pstate TEXT;
    BEGIN
      SELECT * INTO s FROM public.gdss_predictive_evidence_set WHERE id=NEW.evidence_set_id;
      SELECT count(*),min(c.state) INTO axes,pstate FROM public.gdss_evidence_strength_profile p JOIN public.gdss_evidence_strength_axis_assessment a ON a.profile_id=p.id JOIN public.gdss_evidence_completeness_assessment c ON c.evidence_set_id=p.evidence_set_id WHERE p.evidence_set_id=NEW.evidence_set_id;
      IF s.project_id IS DISTINCT FROM NEW.project_id OR s.content_hash IS DISTINCT FROM NEW.evidence_set_hash OR s.model_version_id IS DISTINCT FROM NEW.model_version_id OR s.model_hash IS DISTINCT FROM NEW.model_content_hash OR s.target_key IS DISTINCT FROM NEW.target_key OR s.horizon_key IS DISTINCT FROM NEW.horizon_key OR s.validity_domain_version_id IS DISTINCT FROM NEW.validity_domain_version_id OR axes<>7 OR pstate IS DISTINCT FROM 'COMPLETE' THEN RAISE EXCEPTION 'CAPABILITY_SCOPE_INVALID'; END IF;
      IF NEW.predecessor_assessment_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.gdss_capability_assessment p WHERE p.id=NEW.predecessor_assessment_id AND p.project_id=NEW.project_id AND p.model_version_id=NEW.model_version_id AND p.target_key=NEW.target_key AND p.horizon_key=NEW.horizon_key) THEN RAISE EXCEPTION 'CAPABILITY_SCOPE_INVALID'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006f_guard_claim_insert() RETURNS TRIGGER AS $$
    DECLARE a RECORD; i UUID; expected INTEGER; p RECORD;
    BEGIN
      SELECT * INTO a FROM public.gdss_capability_assessment WHERE id=NEW.capability_assessment_id;
      SELECT project_id INTO i FROM public.gdss_predictive_claim_identity WHERE id=NEW.claim_identity_id;
      SELECT coalesce(max(claim_version),0)+1 INTO expected FROM public.gdss_predictive_claim_version WHERE claim_identity_id=NEW.claim_identity_id;
      IF i IS DISTINCT FROM NEW.project_id OR a.project_id IS DISTINCT FROM NEW.project_id OR a.content_hash IS DISTINCT FROM NEW.capability_assessment_hash OR a.evidence_set_id IS DISTINCT FROM NEW.evidence_set_id OR a.evidence_set_hash IS DISTINCT FROM NEW.evidence_set_hash OR a.model_version_id IS DISTINCT FROM NEW.model_version_id OR a.model_content_hash IS DISTINCT FROM NEW.model_content_hash OR a.target_key IS DISTINCT FROM NEW.target_key OR a.horizon_key IS DISTINCT FROM NEW.horizon_key OR a.validity_domain_version_id IS DISTINCT FROM NEW.validity_domain_version_id THEN RAISE EXCEPTION 'CLAIM_SCOPE_EXCEEDS_EVIDENCE'; END IF;
      IF NEW.claim_version<>expected THEN RAISE EXCEPTION 'STALE_AUTHORIZATION_REPLAY'; END IF;
      IF NEW.predecessor_claim_id IS NOT NULL THEN SELECT * INTO p FROM public.gdss_predictive_claim_version WHERE id=NEW.predecessor_claim_id; IF p.project_id IS DISTINCT FROM NEW.project_id OR p.claim_identity_id IS DISTINCT FROM NEW.claim_identity_id OR p.claim_version<>NEW.claim_version-1 THEN RAISE EXCEPTION 'CLAIM_SCOPE_EXCEEDS_EVIDENCE'; END IF; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006f_guard_claim_update() RETURNS TRIGGER AS $$
    BEGIN
      IF OLD.project_id<>NEW.project_id OR OLD.claim_identity_id<>NEW.claim_identity_id OR OLD.claim_version<>NEW.claim_version OR OLD.capability_assessment_id<>NEW.capability_assessment_id OR OLD.evidence_set_id<>NEW.evidence_set_id OR OLD.authored_by<>NEW.authored_by THEN RAISE EXCEPTION 'CLAIM_IMMUTABLE'; END IF;
      IF OLD.status='DRAFT' AND NEW.status='DRAFT' THEN RETURN NEW; END IF;
      IF OLD.claim_scope IS DISTINCT FROM NEW.claim_scope OR OLD.content_hash IS DISTINCT FROM NEW.content_hash OR OLD.rendered_human_text IS DISTINCT FROM NEW.rendered_human_text OR OLD.limitation_manifest IS DISTINCT FROM NEW.limitation_manifest OR OLD.negative_evidence_manifest IS DISTINCT FROM NEW.negative_evidence_manifest OR OLD.conflict_manifest IS DISTINCT FROM NEW.conflict_manifest OR OLD.uncertainty_summary IS DISTINCT FROM NEW.uncertainty_summary OR OLD.valid_through_epoch_micros IS DISTINCT FROM NEW.valid_through_epoch_micros THEN RAISE EXCEPTION 'CLAIM_IMMUTABLE'; END IF;
      IF NOT((OLD.status='DRAFT' AND NEW.status='EVIDENCE_ASSEMBLED') OR (OLD.status='EVIDENCE_ASSEMBLED' AND NEW.status='REVIEW_REQUIRED') OR (OLD.status='REVIEW_REQUIRED' AND NEW.status IN('AUTHORIZED','REJECTED')) OR (OLD.status='AUTHORIZED' AND NEW.status IN('SUPERSEDED','REVOKED'))) THEN RAISE EXCEPTION 'CLAIM_ALREADY_TERMINAL'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006f_guard_review() RETURNS TRIGGER AS $$ DECLARE c RECORD; BEGIN SELECT * INTO c FROM public.gdss_predictive_claim_version WHERE id=NEW.claim_id; IF c.project_id IS DISTINCT FROM NEW.project_id OR c.status<>'REVIEW_REQUIRED' OR c.content_hash IS DISTINCT FROM NEW.claim_hash THEN RAISE EXCEPTION 'CLAIM_NOT_REVIEWABLE'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006f_guard_authorization() RETURNS TRIGGER AS $$ DECLARE c RECORD; a RECORD; approved INTEGER; BEGIN SELECT * INTO c FROM public.gdss_predictive_claim_version WHERE id=NEW.claim_id FOR UPDATE; SELECT * INTO a FROM public.gdss_capability_assessment WHERE id=c.capability_assessment_id; SELECT count(*) INTO approved FROM public.gdss_predictive_claim_review WHERE claim_id=c.id AND decision='APPROVE_FOR_AUTHORIZATION'; IF c.project_id IS DISTINCT FROM NEW.project_id OR c.status<>'REVIEW_REQUIRED' OR approved=0 OR c.content_hash IS DISTINCT FROM NEW.claim_hash OR a.content_hash IS DISTINCT FROM NEW.assessment_hash OR c.evidence_set_hash IS DISTINCT FROM NEW.evidence_set_hash THEN RAISE EXCEPTION 'STALE_AUTHORIZATION_REPLAY'; END IF; IF c.authored_by=NEW.authorizer AND NEW.sod_exception_reason IS NULL THEN RAISE EXCEPTION 'CLAIM_SOD_VIOLATION'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006f_guard_revocation() RETURNS TRIGGER AS $$ DECLARE c RECORD; a RECORD; BEGIN SELECT * INTO c FROM public.gdss_predictive_claim_version WHERE id=NEW.claim_id FOR UPDATE; SELECT * INTO a FROM public.gdss_predictive_claim_authorization WHERE id=NEW.authorization_id; IF c.project_id IS DISTINCT FROM NEW.project_id OR c.status<>'AUTHORIZED' OR a.claim_id IS DISTINCT FROM c.id OR a.project_id IS DISTINCT FROM NEW.project_id THEN RAISE EXCEPTION 'CLAIM_REVOCATION_FORBIDDEN'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006f_guard_event() RETURNS TRIGGER AS $$
    DECLARE n INTEGER; last_state TEXT;
    BEGIN
      SELECT count(*) INTO n FROM public.gdss_predictive_claim_event WHERE claim_id=NEW.claim_id;
      SELECT to_status INTO last_state FROM public.gdss_predictive_claim_event WHERE claim_id=NEW.claim_id ORDER BY sequence DESC LIMIT 1;
      IF NEW.sequence<>n+1 OR (n=0 AND (NEW.from_status IS NOT NULL OR NEW.to_status<>'DRAFT')) OR (n>0 AND NEW.from_status IS DISTINCT FROM last_state) THEN RAISE EXCEPTION 'CLAIM_IMMUTABLE'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE FUNCTION public.gdss006f_guard_transfer() RETURNS TRIGGER AS $$ DECLARE s RECORD; sp UUID; tp UUID; BEGIN SELECT * INTO s FROM public.gdss_predictive_evidence_set WHERE id=NEW.source_evidence_set_id; SELECT i.project_id INTO sp FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.source_model_version_id; SELECT i.project_id INTO tp FROM public.gdss_version v JOIN public.gdss_identity i ON i.id=v.identity_id WHERE v.id=NEW.target_model_version_id; IF s.project_id IS DISTINCT FROM NEW.project_id OR s.model_version_id IS DISTINCT FROM NEW.source_model_version_id OR s.content_hash IS DISTINCT FROM NEW.source_evidence_set_hash OR sp IS DISTINCT FROM NEW.project_id OR tp IS DISTINCT FROM NEW.project_id OR NEW.result NOT IN('FULL_REVALIDATION_REQUIRED','TRANSFER_REJECTED') THEN RAISE EXCEPTION 'EVIDENCE_TRANSFER_FORBIDDEN'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss006f_capability_guard BEFORE INSERT ON public.gdss_capability_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006f_guard_capability();
    CREATE TRIGGER trg_gdss006f_capability_history BEFORE UPDATE OR DELETE ON public.gdss_capability_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    CREATE TRIGGER trg_gdss006f_identity_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_claim_identity FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    CREATE TRIGGER trg_gdss006f_claim_insert BEFORE INSERT ON public.gdss_predictive_claim_version FOR EACH ROW EXECUTE FUNCTION public.gdss006f_guard_claim_insert();
    CREATE TRIGGER trg_gdss006f_claim_update BEFORE UPDATE ON public.gdss_predictive_claim_version FOR EACH ROW EXECUTE FUNCTION public.gdss006f_guard_claim_update();
    CREATE TRIGGER trg_gdss006f_claim_delete BEFORE DELETE ON public.gdss_predictive_claim_version FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    CREATE TRIGGER trg_gdss006f_event_guard BEFORE INSERT ON public.gdss_predictive_claim_event FOR EACH ROW EXECUTE FUNCTION public.gdss006f_guard_event();
    CREATE TRIGGER trg_gdss006f_event_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_claim_event FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    CREATE TRIGGER trg_gdss006f_review_guard BEFORE INSERT ON public.gdss_predictive_claim_review FOR EACH ROW EXECUTE FUNCTION public.gdss006f_guard_review();
    CREATE TRIGGER trg_gdss006f_review_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_claim_review FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    CREATE TRIGGER trg_gdss006f_authorization_guard BEFORE INSERT ON public.gdss_predictive_claim_authorization FOR EACH ROW EXECUTE FUNCTION public.gdss006f_guard_authorization();
    CREATE TRIGGER trg_gdss006f_authorization_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_claim_authorization FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    CREATE TRIGGER trg_gdss006f_revocation_guard BEFORE INSERT ON public.gdss_predictive_claim_revocation FOR EACH ROW EXECUTE FUNCTION public.gdss006f_guard_revocation();
    CREATE TRIGGER trg_gdss006f_revocation_history BEFORE UPDATE OR DELETE ON public.gdss_predictive_claim_revocation FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    CREATE TRIGGER trg_gdss006f_revalidation_history BEFORE UPDATE OR DELETE ON public.gdss_revalidation_trigger_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    CREATE TRIGGER trg_gdss006f_transfer_guard BEFORE INSERT ON public.gdss_evidence_transfer_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006f_guard_transfer();
    CREATE TRIGGER trg_gdss006f_transfer_history BEFORE UPDATE OR DELETE ON public.gdss_evidence_transfer_assessment FOR EACH ROW EXECUTE FUNCTION public.gdss006f_reject_mutation();
    """)


def downgrade():
    op.execute(r"""
    DROP TABLE IF EXISTS public.gdss_evidence_transfer_assessment,public.gdss_revalidation_trigger_assessment,
      public.gdss_predictive_claim_revocation,public.gdss_predictive_claim_authorization,
      public.gdss_predictive_claim_review,public.gdss_predictive_claim_event,
      public.gdss_predictive_claim_version,public.gdss_predictive_claim_identity,
      public.gdss_capability_assessment CASCADE;
    DROP FUNCTION IF EXISTS public.gdss006f_guard_transfer(),public.gdss006f_guard_event(),
      public.gdss006f_guard_revocation(),public.gdss006f_guard_authorization(),
      public.gdss006f_guard_review(),public.gdss006f_guard_claim_update(),
      public.gdss006f_guard_claim_insert(),public.gdss006f_guard_capability(),
      public.gdss006f_reject_mutation() CASCADE;
    """)
