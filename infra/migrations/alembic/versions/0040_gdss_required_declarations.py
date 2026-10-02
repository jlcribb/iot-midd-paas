"""Harden GDSS required provenance and catalog signatures. Revision 0040."""
from alembic import op

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE public.gdss_provenance ADD CONSTRAINT gdss_provenance_required
      CHECK(record ?& ARRAY['kind','description','asserted_by']
        AND coalesce(length(btrim(record->>'description')),0)>0
        AND coalesce(length(btrim(record->>'asserted_by')),0)>0
        AND (record->>'kind'<>'LITERATURE' OR coalesce(length(btrim(record->>'source_reference')),0)>0));
    CREATE FUNCTION public.gdss_dimension_valid(d JSONB) RETURNS BOOLEAN AS $$
      SELECT CASE WHEN jsonb_typeof(d)='array' THEN jsonb_array_length(d)=7
        AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(d) x
          WHERE jsonb_typeof(x)<>'number' OR x::text !~ '^-?[0-9]+$')
        ELSE FALSE END;
    $$ LANGUAGE SQL IMMUTABLE;
    ALTER TABLE public.gdss_unit_definition ADD CONSTRAINT gdss_unit_signature_valid
      CHECK(definition ?& ARRAY['key','revision','symbol','name','dimension','scale','offset','canonical_unit']
        AND definition->>'key'=key AND (definition->>'revision')::integer=revision
        AND public.gdss_dimension_valid(definition->'dimension')
        AND jsonb_typeof(definition->'scale')='number' AND (definition->>'scale')::numeric>0
        AND jsonb_typeof(definition->'offset')='number');
    CREATE FUNCTION public.gdss_required_structure() RETURNS TRIGGER AS $$
    DECLARE child JSONB; unit JSONB;
    BEGIN
      IF NOT (NEW.content ?& ARRAY['description','validity_domain','provenance','units','children'])
        OR jsonb_typeof(NEW.content->'provenance') IS DISTINCT FROM 'array'
        OR jsonb_typeof(NEW.content->'units') IS DISTINCT FROM 'array'
        OR jsonb_typeof(NEW.content->'children') IS DISTINCT FROM 'array'
      THEN RAISE EXCEPTION 'GDSS required aggregate structure'; END IF;
      IF jsonb_array_length(NEW.content->'provenance')<1 OR jsonb_array_length(NEW.content->'units')<1
      THEN RAISE EXCEPTION 'GDSS required provenance/catalog'; END IF;
      FOR child IN SELECT value FROM jsonb_array_elements(NEW.content->'children') LOOP
        IF NOT (child ?& ARRAY['symbol','kind','provenance'])
          OR jsonb_typeof(child->'provenance') IS DISTINCT FROM 'array'
        THEN RAISE EXCEPTION 'GDSS required child structure'; END IF;
        IF jsonb_array_length(child->'provenance')<1 THEN RAISE EXCEPTION 'GDSS child provenance required'; END IF;
        IF child->>'kind' IN ('Variable','Parameter') THEN
          SELECT value INTO unit FROM jsonb_array_elements(NEW.content->'units') WHERE value->>'key'=child->>'unit_ref';
          IF unit IS NULL OR NOT public.gdss_dimension_valid(child->'dimension')
            OR child->'dimension' IS DISTINCT FROM unit->'dimension'
          THEN RAISE EXCEPTION 'GDSS dimension declaration mismatch'; END IF;
        END IF;
        IF child->>'kind'='Variable' THEN
          IF coalesce(child->>'computational_role','') NOT IN ('INPUT','OUTPUT','STATE','AUXILIARY','EXTERNAL')
            OR coalesce(child->>'epistemic_kind','') NOT IN ('OBSERVED','SIMULATED','PREDICTED','DERIVED','CALIBRATED','COUNTERFACTUAL')
          THEN RAISE EXCEPTION 'GDSS invalid semantic category'; END IF;
        END IF;
      END LOOP;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER gdss_required_structure BEFORE INSERT OR UPDATE OF content ON public.gdss_version
      FOR EACH ROW EXECUTE FUNCTION public.gdss_required_structure();
    """)


def downgrade():
    op.execute("DROP TRIGGER gdss_required_structure ON public.gdss_version")
    op.execute("DROP FUNCTION public.gdss_required_structure()")
    op.execute("ALTER TABLE public.gdss_unit_definition DROP CONSTRAINT gdss_unit_signature_valid")
    op.execute("DROP FUNCTION public.gdss_dimension_valid(JSONB)")
    op.execute("ALTER TABLE public.gdss_provenance DROP CONSTRAINT gdss_provenance_required")
