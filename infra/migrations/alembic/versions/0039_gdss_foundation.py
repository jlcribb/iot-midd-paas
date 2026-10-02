"""GDSS declarative aggregates and immutable governance. Revision 0039."""
from alembic import op

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE public.gdss_identity (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
      canonical_name TEXT NOT NULL UNIQUE CHECK(btrim(canonical_name) <> ''),
      description TEXT NOT NULL,
      created_by TEXT NOT NULL CHECK(btrim(created_by) <> ''),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE public.gdss_unit_definition (
      key TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision > 0),
      definition JSONB NOT NULL CHECK(jsonb_typeof(definition) = 'object'),
      PRIMARY KEY(key, revision)
    );
    CREATE TABLE public.gdss_version (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      identity_id UUID NOT NULL REFERENCES public.gdss_identity(id) ON DELETE RESTRICT,
      version_number INTEGER NOT NULL CHECK(version_number > 0),
      predecessor_version_id UUID,
      lifecycle_status TEXT NOT NULL DEFAULT 'DRAFT'
        CHECK(lifecycle_status IN ('DRAFT','VALIDATED','EXPERIMENTAL','APPROVED','PUBLISHED','DEPRECATED')),
      content JSONB NOT NULL CHECK(jsonb_typeof(content) = 'object'),
      canonical_content TEXT,
      content_hash TEXT CHECK(content_hash ~ '^[0-9a-f]{64}$'),
      created_by TEXT NOT NULL CHECK(btrim(created_by) <> ''),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(identity_id, version_number), UNIQUE(identity_id, id),
      FOREIGN KEY(identity_id, predecessor_version_id) REFERENCES public.gdss_version(identity_id,id)
    );
    CREATE TABLE public.gdss_artifact (
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      symbol TEXT NOT NULL,
      kind TEXT NOT NULL CHECK(kind IN ('Component','Variable','Parameter','Formula','Constraint','Boundary')),
      payload JSONB NOT NULL,
      PRIMARY KEY(model_version_id, symbol)
    );
    CREATE TABLE public.gdss_reference (
      model_version_id UUID NOT NULL,
      source_symbol TEXT NOT NULL, target_symbol TEXT NOT NULL,
      PRIMARY KEY(model_version_id, source_symbol, target_symbol),
      FOREIGN KEY(model_version_id, source_symbol) REFERENCES public.gdss_artifact(model_version_id,symbol),
      FOREIGN KEY(model_version_id, target_symbol) REFERENCES public.gdss_artifact(model_version_id,symbol)
    );
    CREATE TABLE public.gdss_provenance (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      child_symbol TEXT,
      record JSONB NOT NULL CHECK(record->>'kind' IN ('LITERATURE','EMPIRICAL','DERIVED','CALIBRATED','HUMAN_PROPOSED','AI_PROPOSED')),
      FOREIGN KEY(model_version_id,child_symbol) REFERENCES public.gdss_artifact(model_version_id,symbol),
      CHECK(record->>'kind' <> 'LITERATURE' OR length(btrim(record->>'source_reference')) > 0)
    );
    CREATE TABLE public.gdss_unit_reference (
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id),
      key TEXT NOT NULL, revision INTEGER NOT NULL,
      PRIMARY KEY(model_version_id,key),
      FOREIGN KEY(key,revision) REFERENCES public.gdss_unit_definition(key,revision)
    );
    CREATE TABLE public.gdss_lifecycle_event (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
      from_status TEXT NOT NULL, to_status TEXT NOT NULL,
      actor TEXT NOT NULL CHECK(btrim(actor) <> ''),
      timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
      reason TEXT NOT NULL CHECK(btrim(reason) <> ''),
      metadata JSONB NOT NULL DEFAULT '{}',
      UNIQUE(model_version_id,to_status)
    );
    CREATE FUNCTION public.gdss_immutable() RETURNS TRIGGER AS $$
    BEGIN RAISE EXCEPTION 'GDSS immutable record'; END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_units_immutable BEFORE UPDATE OR DELETE ON public.gdss_unit_definition
      FOR EACH ROW EXECUTE FUNCTION public.gdss_immutable();
    CREATE TRIGGER gdss_identity_immutable BEFORE UPDATE OR DELETE ON public.gdss_identity
      FOR EACH ROW EXECUTE FUNCTION public.gdss_immutable();
    CREATE TRIGGER gdss_events_immutable BEFORE UPDATE OR DELETE ON public.gdss_lifecycle_event
      FOR EACH ROW EXECUTE FUNCTION public.gdss_immutable();

    CREATE FUNCTION public.gdss_guard_version() RETURNS TRIGGER AS $$
    DECLARE states TEXT[] := ARRAY['DRAFT','VALIDATED','EXPERIMENTAL','APPROVED','PUBLISHED','DEPRECATED'];
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'GDSS version deletion prohibited'; END IF;
      IF TG_OP = 'INSERT' THEN
        IF NEW.lifecycle_status <> 'DRAFT' OR NEW.content_hash IS NOT NULL OR NEW.canonical_content IS NOT NULL THEN
          RAISE EXCEPTION 'GDSS versions start DRAFT';
        END IF;
        IF NEW.predecessor_version_id IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM public.gdss_version p WHERE p.id=NEW.predecessor_version_id
          AND p.identity_id=NEW.identity_id AND p.version_number < NEW.version_number
        ) THEN RAISE EXCEPTION 'GDSS invalid predecessor'; END IF;
        RETURN NEW;
      END IF;
      IF (NEW.id,NEW.identity_id,NEW.version_number,NEW.predecessor_version_id,NEW.created_by,NEW.created_at)
        IS DISTINCT FROM (OLD.id,OLD.identity_id,OLD.version_number,OLD.predecessor_version_id,OLD.created_by,OLD.created_at)
      THEN RAISE EXCEPTION 'GDSS identity immutable'; END IF;
      IF OLD.lifecycle_status <> 'DRAFT' AND
        (NEW.content,NEW.content_hash,NEW.canonical_content) IS DISTINCT FROM (OLD.content,OLD.content_hash,OLD.canonical_content)
      THEN RAISE EXCEPTION 'GDSS content frozen'; END IF;
      IF NEW.lifecycle_status = OLD.lifecycle_status THEN
        IF NEW.content_hash IS DISTINCT FROM OLD.content_hash OR NEW.canonical_content IS DISTINCT FROM OLD.canonical_content
        THEN RAISE EXCEPTION 'GDSS hash changes only at validation'; END IF;
      ELSE
        IF array_position(states,NEW.lifecycle_status) <> array_position(states,OLD.lifecycle_status)+1
        THEN RAISE EXCEPTION 'GDSS illegal transition'; END IF;
        IF NEW.content IS DISTINCT FROM OLD.content THEN RAISE EXCEPTION 'GDSS transition cannot edit content'; END IF;
        IF NEW.lifecycle_status='VALIDATED' THEN
          IF NEW.canonical_content IS NULL OR NEW.content_hash IS NULL
            OR NEW.canonical_content::jsonb <> NEW.content
            OR encode(sha256(convert_to(NEW.canonical_content,'UTF8')),'hex') <> NEW.content_hash
          THEN RAISE EXCEPTION 'GDSS hash/content mismatch'; END IF;
        END IF;
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_version_guard BEFORE INSERT OR UPDATE OR DELETE ON public.gdss_version
      FOR EACH ROW EXECUTE FUNCTION public.gdss_guard_version();

    CREATE FUNCTION public.gdss_projection_guard() RETURNS TRIGGER AS $$
    BEGIN
      IF pg_trigger_depth() < 2 THEN RAISE EXCEPTION 'GDSS projections must be edited through draft aggregate'; END IF;
      IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
    END; $$ LANGUAGE plpgsql;

    CREATE FUNCTION public.gdss_project_content() RETURNS TRIGGER AS $$
    DECLARE child JSONB; source JSONB; unit JSONB; target TEXT; ref JSONB;
    BEGIN
      IF TG_OP='UPDATE' AND NEW.content=OLD.content THEN RETURN NEW; END IF;
      DELETE FROM public.gdss_reference WHERE model_version_id=NEW.id;
      DELETE FROM public.gdss_provenance WHERE model_version_id=NEW.id;
      DELETE FROM public.gdss_unit_reference WHERE model_version_id=NEW.id;
      DELETE FROM public.gdss_artifact WHERE model_version_id=NEW.id;
      IF jsonb_array_length(NEW.content->'provenance') < 1 THEN RAISE EXCEPTION 'GDSS provenance required'; END IF;
      FOR source IN SELECT value FROM jsonb_array_elements(NEW.content->'provenance') LOOP
        INSERT INTO public.gdss_provenance(model_version_id,record) VALUES(NEW.id,source);
      END LOOP;
      FOR unit IN SELECT value FROM jsonb_array_elements(NEW.content->'units') LOOP
        INSERT INTO public.gdss_unit_definition(key,revision,definition)
          VALUES(unit->>'key',(unit->>'revision')::integer,unit) ON CONFLICT DO NOTHING;
        IF NOT EXISTS(SELECT 1 FROM public.gdss_unit_definition
          WHERE key=unit->>'key' AND revision=(unit->>'revision')::integer AND definition=unit)
        THEN RAISE EXCEPTION 'GDSS catalog revision immutable'; END IF;
        INSERT INTO public.gdss_unit_reference VALUES(NEW.id,unit->>'key',(unit->>'revision')::integer);
      END LOOP;
      FOR child IN SELECT value FROM jsonb_array_elements(NEW.content->'children') LOOP
        INSERT INTO public.gdss_artifact VALUES(NEW.id,child->>'symbol',child->>'kind',child);
        IF jsonb_array_length(child->'provenance') < 1 THEN RAISE EXCEPTION 'GDSS child provenance required'; END IF;
        FOR source IN SELECT value FROM jsonb_array_elements(child->'provenance') LOOP
          INSERT INTO public.gdss_provenance(model_version_id,child_symbol,record) VALUES(NEW.id,child->>'symbol',source);
        END LOOP;
      END LOOP;
      FOR child IN SELECT value FROM jsonb_array_elements(NEW.content->'children') LOOP
        ref := CASE child->>'kind'
          WHEN 'Formula' THEN (child->'input_refs') || jsonb_build_array(child->>'output_ref')
          WHEN 'Constraint' THEN child->'refs'
          WHEN 'Boundary' THEN child->'included_components'
          ELSE '[]'::jsonb END;
        FOR target IN SELECT DISTINCT value FROM jsonb_array_elements_text(ref) LOOP
          INSERT INTO public.gdss_reference VALUES(NEW.id,child->>'symbol',target);
        END LOOP;
      END LOOP;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_project_content AFTER INSERT OR UPDATE OF content ON public.gdss_version
      FOR EACH ROW EXECUTE FUNCTION public.gdss_project_content();

    CREATE FUNCTION public.gdss_require_event() RETURNS TRIGGER AS $$
    BEGIN
      IF OLD.lifecycle_status <> NEW.lifecycle_status AND NOT EXISTS(
        SELECT 1 FROM public.gdss_lifecycle_event WHERE model_version_id=NEW.id
          AND from_status=OLD.lifecycle_status AND to_status=NEW.lifecycle_status
      ) THEN RAISE EXCEPTION 'GDSS transition requires event'; END IF;
      RETURN NULL;
    END; $$ LANGUAGE plpgsql;
    CREATE CONSTRAINT TRIGGER gdss_require_event AFTER UPDATE ON public.gdss_version
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.gdss_require_event();
    CREATE FUNCTION public.gdss_guard_event() RETURNS TRIGGER AS $$
    DECLARE states TEXT[] := ARRAY['DRAFT','VALIDATED','EXPERIMENTAL','APPROVED','PUBLISHED','DEPRECATED'];
    BEGIN
      IF array_position(states,NEW.from_status) IS NULL OR array_position(states,NEW.to_status) IS NULL
        OR array_position(states,NEW.to_status) <> array_position(states,NEW.from_status)+1
        OR NOT EXISTS(SELECT 1 FROM public.gdss_version WHERE id=NEW.model_version_id AND lifecycle_status=NEW.to_status)
      THEN RAISE EXCEPTION 'GDSS event requires successful transition'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_guard_event BEFORE INSERT ON public.gdss_lifecycle_event
      FOR EACH ROW EXECUTE FUNCTION public.gdss_guard_event();
    """)
    for table in ["gdss_artifact", "gdss_reference", "gdss_provenance", "gdss_unit_reference"]:
        op.execute(f"CREATE TRIGGER {table}_guard BEFORE INSERT OR UPDATE OR DELETE ON public.{table} FOR EACH ROW EXECUTE FUNCTION public.gdss_projection_guard()")


def downgrade():
    # Only explicit operator-requested rollback; never used for reconciliation.
    for table in ["gdss_lifecycle_event", "gdss_reference", "gdss_provenance", "gdss_unit_reference", "gdss_artifact", "gdss_version", "gdss_unit_definition", "gdss_identity"]:
        op.execute(f"DROP TABLE public.{table}")
    for fn in ["gdss_guard_event", "gdss_require_event", "gdss_project_content", "gdss_projection_guard", "gdss_guard_version", "gdss_immutable"]:
        op.execute(f"DROP FUNCTION public.{fn}()")
