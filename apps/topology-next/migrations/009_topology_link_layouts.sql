BEGIN;

CREATE TABLE IF NOT EXISTS topology_link_layouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topology_view_id UUID NOT NULL REFERENCES topology_views(id) ON DELETE CASCADE,
    topology_link_id UUID NOT NULL REFERENCES topology_links(id) ON DELETE CASCADE,
    hidden BOOLEAN NOT NULL DEFAULT false,
    label_offset_x DOUBLE PRECISION NOT NULL DEFAULT 0,
    label_offset_y DOUBLE PRECISION NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_topology_link_layouts_view_link
    ON topology_link_layouts(topology_view_id, topology_link_id);

CREATE INDEX IF NOT EXISTS ix_topology_link_layouts_view_id
    ON topology_link_layouts(topology_view_id);

DROP TRIGGER IF EXISTS topology_link_layouts_set_updated_at ON topology_link_layouts;
CREATE TRIGGER topology_link_layouts_set_updated_at
BEFORE UPDATE ON topology_link_layouts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;
