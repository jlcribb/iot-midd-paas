BEGIN;

CREATE TABLE IF NOT EXISTS topology_node_layouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topology_view_id UUID NOT NULL REFERENCES topology_views(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    sector_id UUID REFERENCES sectors(id) ON DELETE CASCADE,
    x DOUBLE PRECISION NOT NULL,
    y DOUBLE PRECISION NOT NULL,
    width DOUBLE PRECISION,
    height DOUBLE PRECISION,
    collapsed BOOLEAN NOT NULL DEFAULT false,
    hidden BOOLEAN NOT NULL DEFAULT false,
    z_index INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT topology_node_layouts_one_entity CHECK (
        ((asset_id IS NOT NULL)::int + (sector_id IS NOT NULL)::int) = 1
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_topology_node_layouts_view_asset
    ON topology_node_layouts(topology_view_id, asset_id)
    WHERE asset_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_topology_node_layouts_view_sector
    ON topology_node_layouts(topology_view_id, sector_id)
    WHERE sector_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_topology_node_layouts_view_id
    ON topology_node_layouts(topology_view_id);

DROP TRIGGER IF EXISTS topology_node_layouts_set_updated_at ON topology_node_layouts;
CREATE TRIGGER topology_node_layouts_set_updated_at
BEFORE UPDATE ON topology_node_layouts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;
