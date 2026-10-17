"""GDSS-006B transitive lineage depth contract remediation. Revision 0050."""

from alembic import op

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
    CREATE OR REPLACE FUNCTION public.gdss006b_guard_lineage() RETURNS TRIGGER AS $$
    DECLARE
      cycle_found BOOLEAN;
      depth_exceeded BOOLEAN;
      excluded_id UUID;
    BEGIN
      -- Serialize graph extensions per project so concurrent edges cannot each
      -- validate against a stale lineage closure.
      PERFORM pg_advisory_xact_lock(hashtextextended(NEW.project_id::text, 0));
      IF TG_OP = 'UPDATE' THEN excluded_id := OLD.id; END IF;

      IF NEW.relation_type <> 'GROUPED_WITH' THEN
        WITH RECURSIVE descendants(id, depth, path) AS (
          SELECT NEW.child_evidence_unit_id, 0,
                 ARRAY[NEW.child_evidence_unit_id]::UUID[]
          UNION ALL
          SELECT l.child_evidence_unit_id, d.depth + 1,
                 d.path || l.child_evidence_unit_id
          FROM descendants d
          JOIN public.gdss_evidence_lineage l
            ON l.parent_evidence_unit_id = d.id
           AND l.project_id = NEW.project_id
          WHERE d.depth < 16
            AND (excluded_id IS NULL OR l.id <> excluded_id)
            AND NOT l.child_evidence_unit_id = ANY(d.path)
        )
        SELECT EXISTS(
          SELECT 1 FROM descendants
          WHERE id = NEW.parent_evidence_unit_id AND depth > 0
        ) INTO cycle_found;
        IF cycle_found THEN
          RAISE EXCEPTION 'EVIDENCE_LINEAGE_CYCLE';
        END IF;
      END IF;

      -- Depth counts edges: the current/root unit is 0, the inserted edge is 1.
      -- Explore both sides of the prospective edge. Reaching a combined depth
      -- of 17 means independence closure is not provable under the V1 contract.
      WITH RECURSIVE
      ancestors(id, depth, path) AS (
        SELECT NEW.parent_evidence_unit_id, 0,
               ARRAY[NEW.parent_evidence_unit_id]::UUID[]
        UNION ALL
        SELECT l.parent_evidence_unit_id, a.depth + 1,
               a.path || l.parent_evidence_unit_id
        FROM ancestors a
        JOIN public.gdss_evidence_lineage l
          ON l.child_evidence_unit_id = a.id
         AND l.project_id = NEW.project_id
        WHERE a.depth < 16
          AND (excluded_id IS NULL OR l.id <> excluded_id)
          AND NOT l.parent_evidence_unit_id = ANY(a.path)
      ),
      descendants(id, depth, path) AS (
        SELECT NEW.child_evidence_unit_id, 0,
               ARRAY[NEW.child_evidence_unit_id]::UUID[]
        UNION ALL
        SELECT l.child_evidence_unit_id, d.depth + 1,
               d.path || l.child_evidence_unit_id
        FROM descendants d
        JOIN public.gdss_evidence_lineage l
          ON l.parent_evidence_unit_id = d.id
         AND l.project_id = NEW.project_id
        WHERE d.depth < 16
          AND (excluded_id IS NULL OR l.id <> excluded_id)
          AND NOT l.child_evidence_unit_id = ANY(d.path)
      )
      SELECT EXISTS(
        SELECT 1 FROM ancestors a CROSS JOIN descendants d
        WHERE a.depth + 1 + d.depth > 16
      ) INTO depth_exceeded;

      IF depth_exceeded THEN
        RAISE EXCEPTION 'LINEAGE_DEPTH_LIMIT_EXCEEDED';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade():
    op.execute(r"""
    CREATE OR REPLACE FUNCTION public.gdss006b_guard_lineage() RETURNS TRIGGER AS $$
    DECLARE cycle_found BOOLEAN;
    BEGIN
      IF NEW.relation_type <> 'GROUPED_WITH' THEN
        WITH RECURSIVE descendants(id,depth) AS (
          SELECT NEW.child_evidence_unit_id,0
          UNION ALL
          SELECT l.child_evidence_unit_id,d.depth+1
          FROM descendants d
          JOIN public.gdss_evidence_lineage l ON l.parent_evidence_unit_id=d.id
          WHERE d.depth<64
        )
        SELECT EXISTS(
          SELECT 1 FROM descendants
          WHERE id=NEW.parent_evidence_unit_id AND depth>0
        ) INTO cycle_found;
        IF cycle_found THEN RAISE EXCEPTION 'EVIDENCE_LINEAGE_CYCLE'; END IF;
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
