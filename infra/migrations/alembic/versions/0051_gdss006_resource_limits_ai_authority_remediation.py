"""GDSS-006 resource-limit and AI-authority remediation. Revision 0051."""

from alembic import op

revision = "0051"
down_revision = "0050"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM public.gdss_validation_acceptance_criterion
        GROUP BY protocol_version_id
        HAVING count(DISTINCT (metric_key,metric_version)) > 16
      ) THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXISTING_DATA metric definitions per protocol exceed 16'; END IF;
      IF EXISTS (
        SELECT 1 FROM public.gdss_capability_assessment
        WHERE cardinality(metric_profile)>16 OR cardinality(baseline_profile)>8
      ) THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXISTING_DATA capability profile exceeds canonical limits'; END IF;
      IF EXISTS (
        SELECT 1
        FROM public.gdss_baseline_metric_result b
        JOIN public.gdss_prediction_pair_set_member sm ON sm.pair_set_id=b.pair_set_id
        JOIN public.gdss_prediction_observation_pair po ON po.id=sm.pair_id
        JOIN public.gdss_prediction_record pr ON pr.id=po.prediction_id
        JOIN public.gdss_validation_run r ON r.id=pr.validation_run_id
        GROUP BY r.protocol_version_id
        HAVING count(DISTINCT b.baseline_version_id)>8
      ) THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXISTING_DATA baselines per protocol exceed 8'; END IF;
    END $$;

    CREATE FUNCTION public.gdss0051_guard_protocol_metric_limit() RETURNS TRIGGER AS $$
    DECLARE actual_count INTEGER;
    BEGIN
      PERFORM pg_advisory_xact_lock(hashtextextended(NEW.protocol_version_id::text, 0));
      SELECT count(DISTINCT (metric_key,metric_version)) INTO actual_count
      FROM (
        SELECT metric_key,metric_version
        FROM public.gdss_validation_acceptance_criterion
        WHERE protocol_version_id=NEW.protocol_version_id AND id<>NEW.id
        UNION ALL SELECT NEW.metric_key,NEW.metric_version
      ) selected_metrics;
      IF actual_count>16 THEN
        RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED resource=METRIC_DEFINITIONS_PER_PROTOCOL limit=16 actual=%',actual_count;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss0051_guard_protocol_seal_limits() RETURNS TRIGGER AS $$
    DECLARE metric_count INTEGER;
    BEGIN
      IF NEW.to_status='SEALED' THEN
        PERFORM pg_advisory_xact_lock(hashtextextended(NEW.protocol_version_id::text, 0));
        SELECT count(DISTINCT (metric_key,metric_version)) INTO metric_count
        FROM public.gdss_validation_acceptance_criterion
        WHERE protocol_version_id=NEW.protocol_version_id;
        IF metric_count>16 THEN
          RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED resource=METRIC_DEFINITIONS_PER_PROTOCOL limit=16 actual=%',metric_count;
        END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss0051_guard_metric_result_limit() RETURNS TRIGGER AS $$
    DECLARE actual_count INTEGER;
    BEGIN
      PERFORM pg_advisory_xact_lock(hashtextextended(NEW.protocol_version_id::text, 0));
      SELECT count(DISTINCT metric_definition_version_id) INTO actual_count
      FROM (
        SELECT metric_definition_version_id FROM public.gdss_metric_result
        WHERE protocol_version_id=NEW.protocol_version_id AND id<>NEW.id
        UNION ALL SELECT NEW.metric_definition_version_id
      ) selected_metrics;
      IF actual_count>16 THEN
        RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED resource=METRIC_DEFINITIONS_PER_PROTOCOL limit=16 actual=%',actual_count;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss0051_guard_baseline_result_limit() RETURNS TRIGGER AS $$
    DECLARE bound_protocol UUID; protocol_count INTEGER; actual_count INTEGER;
    BEGIN
      SELECT min(r.protocol_version_id::text)::uuid,count(DISTINCT r.protocol_version_id)
      INTO bound_protocol,protocol_count
      FROM public.gdss_prediction_pair_set_member sm
      JOIN public.gdss_prediction_observation_pair po ON po.id=sm.pair_id
      JOIN public.gdss_prediction_record pr ON pr.id=po.prediction_id
      JOIN public.gdss_validation_run r ON r.id=pr.validation_run_id
      WHERE sm.pair_set_id=NEW.pair_set_id;
      IF bound_protocol IS NULL OR protocol_count<>1 THEN
        RAISE EXCEPTION 'BASELINE_PAIRSET_MISMATCH';
      END IF;
      PERFORM pg_advisory_xact_lock(hashtextextended(bound_protocol::text, 0));
      SELECT count(DISTINCT baseline_version_id) INTO actual_count
      FROM (
        SELECT b.baseline_version_id
        FROM public.gdss_baseline_metric_result b
        JOIN public.gdss_prediction_pair_set_member sm ON sm.pair_set_id=b.pair_set_id
        JOIN public.gdss_prediction_observation_pair po ON po.id=sm.pair_id
        JOIN public.gdss_prediction_record pr ON pr.id=po.prediction_id
        JOIN public.gdss_validation_run r ON r.id=pr.validation_run_id
        WHERE r.protocol_version_id=bound_protocol AND b.id<>NEW.id
        UNION ALL SELECT NEW.baseline_version_id
      ) selected_baselines;
      IF actual_count>8 THEN
        RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED resource=BASELINES_PER_PROTOCOL limit=8 actual=%',actual_count;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_gdss0051_protocol_metric_limit
      BEFORE INSERT OR UPDATE ON public.gdss_validation_acceptance_criterion
      FOR EACH ROW EXECUTE FUNCTION public.gdss0051_guard_protocol_metric_limit();
    CREATE TRIGGER trg_gdss0051_protocol_seal_limits
      BEFORE INSERT ON public.gdss_validation_protocol_lifecycle_event
      FOR EACH ROW EXECUTE FUNCTION public.gdss0051_guard_protocol_seal_limits();
    CREATE TRIGGER trg_gdss0051_metric_result_limit
      BEFORE INSERT OR UPDATE ON public.gdss_metric_result
      FOR EACH ROW EXECUTE FUNCTION public.gdss0051_guard_metric_result_limit();
    CREATE TRIGGER trg_gdss0051_baseline_result_limit
      BEFORE INSERT OR UPDATE ON public.gdss_baseline_metric_result
      FOR EACH ROW EXECUTE FUNCTION public.gdss0051_guard_baseline_result_limit();

    DO $$ DECLARE item RECORD; BEGIN
      FOR item IN SELECT conname FROM pg_constraint
        WHERE conrelid='public.gdss_capability_assessment'::regclass AND contype='c'
          AND pg_get_constraintdef(oid) LIKE '%cardinality(metric_profile)%'
      LOOP EXECUTE format('ALTER TABLE public.gdss_capability_assessment DROP CONSTRAINT %I',item.conname); END LOOP;
      FOR item IN SELECT conname FROM pg_constraint
        WHERE conrelid='public.gdss_capability_assessment'::regclass AND contype='c'
          AND pg_get_constraintdef(oid) LIKE '%cardinality(baseline_profile)%'
      LOOP EXECUTE format('ALTER TABLE public.gdss_capability_assessment DROP CONSTRAINT %I',item.conname); END LOOP;
    END $$;
    ALTER TABLE public.gdss_capability_assessment
      ADD CONSTRAINT gdss0051_capability_metric_profile_limit CHECK(cardinality(metric_profile) BETWEEN 1 AND 16),
      ADD CONSTRAINT gdss0051_capability_baseline_profile_limit CHECK(cardinality(baseline_profile) BETWEEN 1 AND 8);
    """)


def downgrade():
    op.execute(r"""
    DROP TRIGGER IF EXISTS trg_gdss0051_protocol_metric_limit ON public.gdss_validation_acceptance_criterion;
    DROP TRIGGER IF EXISTS trg_gdss0051_protocol_seal_limits ON public.gdss_validation_protocol_lifecycle_event;
    DROP TRIGGER IF EXISTS trg_gdss0051_metric_result_limit ON public.gdss_metric_result;
    DROP TRIGGER IF EXISTS trg_gdss0051_baseline_result_limit ON public.gdss_baseline_metric_result;
    DROP FUNCTION IF EXISTS public.gdss0051_guard_protocol_metric_limit();
    DROP FUNCTION IF EXISTS public.gdss0051_guard_protocol_seal_limits();
    DROP FUNCTION IF EXISTS public.gdss0051_guard_metric_result_limit();
    DROP FUNCTION IF EXISTS public.gdss0051_guard_baseline_result_limit();
    ALTER TABLE public.gdss_capability_assessment
      DROP CONSTRAINT IF EXISTS gdss0051_capability_metric_profile_limit,
      DROP CONSTRAINT IF EXISTS gdss0051_capability_baseline_profile_limit,
      ADD CONSTRAINT gdss006f_capability_metric_profile_limit CHECK(cardinality(metric_profile) BETWEEN 1 AND 64),
      ADD CONSTRAINT gdss006f_capability_baseline_profile_limit CHECK(cardinality(baseline_profile) BETWEEN 1 AND 32);
    """)
