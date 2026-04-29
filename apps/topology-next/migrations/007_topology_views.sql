BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'topology_view_type_enum') THEN
        CREATE TYPE topology_view_type_enum AS ENUM ('logical', 'physical', 'geographic');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS topology_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    view_type topology_view_type_enum NOT NULL DEFAULT 'logical',
    is_default BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT topology_views_name_not_blank CHECK (btrim(name) <> '')
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_topology_views_project_name
    ON topology_views(project_id, name);

CREATE UNIQUE INDEX IF NOT EXISTS ux_topology_views_default_per_type
    ON topology_views(project_id, view_type)
    WHERE is_default = true;

CREATE INDEX IF NOT EXISTS ix_topology_views_project_id
    ON topology_views(project_id);

DROP TRIGGER IF EXISTS topology_views_set_updated_at ON topology_views;
CREATE TRIGGER topology_views_set_updated_at
BEFORE UPDATE ON topology_views
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;
