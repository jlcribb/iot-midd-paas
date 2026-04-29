"""Core Public Schema for Digital Twin Assets

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-27 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create core public schema objects for projects/assets topology."""

    op.execute("SET LOCAL search_path TO public")
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status_enum') THEN
                CREATE TYPE project_status_enum AS ENUM ('draft', 'active', 'inactive', 'archived');
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'asset_type_enum') THEN
                CREATE TYPE asset_type_enum AS ENUM (
                    'programmable_node',
                    'sensor',
                    'actuator',
                    'gateway',
                    'relay_module',
                    'camera',
                    'power_unit'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'asset_status_enum') THEN
                CREATE TYPE asset_status_enum AS ENUM (
                    'provisioning',
                    'online',
                    'offline',
                    'active',
                    'inactive',
                    'fault',
                    'maintenance',
                    'retired'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'topology_relation_enum') THEN
                CREATE TYPE topology_relation_enum AS ENUM (
                    'contains',
                    'hosts',
                    'reads',
                    'controls',
                    'connects_to',
                    'routes_to',
                    'depends_on',
                    'powered_by',
                    'mounted_on'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'link_status_enum') THEN
                CREATE TYPE link_status_enum AS ENUM ('planned', 'active', 'inactive', 'fault', 'retired');
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at := now();
            RETURN NEW;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION normalize_mac_address(mac text)
        RETURNS text
        LANGUAGE plpgsql
        IMMUTABLE
        AS $$
        BEGIN
            IF mac IS NULL THEN
                RETURN NULL;
            END IF;

            RETURN lower(trim(mac));
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            description TEXT,
            status project_status_enum NOT NULL DEFAULT 'draft',
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT projects_name_not_blank CHECK (btrim(name) <> '')
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            description TEXT,
            latitude NUMERIC(9,6),
            longitude NUMERIC(9,6),
            altitude NUMERIC(9,2),
            accuracy_meters NUMERIC(9,2),
            country TEXT,
            province TEXT,
            city TEXT,
            address_text TEXT,
            building TEXT,
            floor TEXT,
            zone TEXT,
            rack TEXT,
            position TEXT,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            CONSTRAINT locations_name_not_blank CHECK (btrim(name) <> ''),
            CONSTRAINT locations_lat_range CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
            CONSTRAINT locations_lon_range CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
            CONSTRAINT locations_lat_lon_pair CHECK (
                (latitude IS NULL AND longitude IS NULL)
                OR
                (latitude IS NOT NULL AND longitude IS NOT NULL)
            ),
            CONSTRAINT locations_accuracy_nonnegative CHECK (accuracy_meters IS NULL OR accuracy_meters >= 0)
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sectors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
            name TEXT NOT NULL,
            code TEXT,
            description TEXT,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT sectors_name_not_blank CHECK (btrim(name) <> '')
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            sector_id UUID NOT NULL REFERENCES sectors(id) ON DELETE CASCADE,
            location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
            parent_asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,

            asset_type asset_type_enum NOT NULL,
            subtype TEXT NOT NULL,
            name TEXT NOT NULL,
            code TEXT,
            description TEXT,
            status asset_status_enum NOT NULL DEFAULT 'inactive',

            role TEXT,
            serial_number TEXT,
            manufacturer TEXT,
            model TEXT,
            firmware_version TEXT,
            hardware_version TEXT,
            mac_address TEXT,
            ip_address INET,
            last_seen_at TIMESTAMPTZ,

            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            CONSTRAINT assets_name_not_blank CHECK (btrim(name) <> ''),
            CONSTRAINT assets_subtype_not_blank CHECK (btrim(subtype) <> ''),
            CONSTRAINT assets_not_self_parent CHECK (parent_asset_id IS NULL OR parent_asset_id <> id)
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS topology_links (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

            source_asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
            target_asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
            source_sector_id UUID REFERENCES sectors(id) ON DELETE CASCADE,
            target_sector_id UUID REFERENCES sectors(id) ON DELETE CASCADE,

            relation_type topology_relation_enum NOT NULL,
            connection_medium TEXT,
            protocol TEXT,
            ports JSONB NOT NULL DEFAULT '[]'::jsonb,
            link_quality NUMERIC(5,2),
            status link_status_enum NOT NULL DEFAULT 'active',
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            CONSTRAINT topology_links_one_source CHECK (
                ((source_asset_id IS NOT NULL)::int + (source_sector_id IS NOT NULL)::int) = 1
            ),
            CONSTRAINT topology_links_one_target CHECK (
                ((target_asset_id IS NOT NULL)::int + (target_sector_id IS NOT NULL)::int) = 1
            ),
            CONSTRAINT topology_links_no_same_asset CHECK (
                source_asset_id IS NULL OR target_asset_id IS NULL OR source_asset_id <> target_asset_id
            ),
            CONSTRAINT topology_links_no_same_sector CHECK (
                source_sector_id IS NULL OR target_sector_id IS NULL OR source_sector_id <> target_sector_id
            ),
            CONSTRAINT topology_links_quality_range CHECK (
                link_quality IS NULL OR (link_quality >= 0 AND link_quality <= 100)
            ),
            CONSTRAINT topology_links_ports_is_array CHECK (jsonb_typeof(ports) = 'array')
        );
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_sectors_project_name
            ON sectors(project_id, name);
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_sectors_project_code_not_null
            ON sectors(project_id, code)
            WHERE code IS NOT NULL;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_assets_project_code_not_null
            ON assets(project_id, code)
            WHERE code IS NOT NULL;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_assets_serial_number_not_null
            ON assets(serial_number)
            WHERE serial_number IS NOT NULL;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_assets_mac_address_not_null
            ON assets(normalize_mac_address(mac_address))
            WHERE mac_address IS NOT NULL;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_topology_links_exact_relation
            ON topology_links (
                project_id,
                relation_type,
                COALESCE(source_asset_id, '00000000-0000-0000-0000-000000000000'::uuid),
                COALESCE(source_sector_id, '00000000-0000-0000-0000-000000000000'::uuid),
                COALESCE(target_asset_id, '00000000-0000-0000-0000-000000000000'::uuid),
                COALESCE(target_sector_id, '00000000-0000-0000-0000-000000000000'::uuid)
            );
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_status ON projects(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_locations_city ON locations(city)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_locations_province_city ON locations(province, city)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_locations_lat_lon
            ON locations(latitude, longitude)
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_locations_metadata_gin ON locations USING GIN (metadata)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sectors_project_id ON sectors(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sectors_location_id ON sectors(location_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sectors_metadata_gin ON sectors USING GIN (metadata)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_project_id ON assets(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_sector_id ON assets(sector_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_location_id ON assets(location_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_parent_asset_id ON assets(parent_asset_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_asset_type ON assets(asset_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_status ON assets(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_last_seen_at ON assets(last_seen_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_project_asset_type ON assets(project_id, asset_type)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_assets_project_sector_asset_type
            ON assets(project_id, sector_id, asset_type);
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_metadata_gin ON assets USING GIN (metadata)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_project_id ON topology_links(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_source_asset_id ON topology_links(source_asset_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_target_asset_id ON topology_links(target_asset_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_source_sector_id ON topology_links(source_sector_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_target_sector_id ON topology_links(target_sector_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_relation_type ON topology_links(relation_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_status ON topology_links(status)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_topology_links_project_relation_type
            ON topology_links(project_id, relation_type);
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_metadata_gin ON topology_links USING GIN (metadata)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_topology_links_ports_gin ON topology_links USING GIN (ports)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_assets_validate()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            parent_project_id UUID;
            parent_sector_id UUID;
            parent_asset_type asset_type_enum;
        BEGIN
            IF NEW.mac_address IS NOT NULL THEN
                NEW.mac_address := normalize_mac_address(NEW.mac_address);
            END IF;

            IF NEW.parent_asset_id IS NOT NULL THEN
                SELECT a.project_id, a.sector_id, a.asset_type
                INTO parent_project_id, parent_sector_id, parent_asset_type
                FROM assets a
                WHERE a.id = NEW.parent_asset_id;

                IF NOT FOUND THEN
                    RAISE EXCEPTION 'parent_asset_id % does not exist', NEW.parent_asset_id;
                END IF;

                IF parent_project_id <> NEW.project_id THEN
                    RAISE EXCEPTION 'child asset project_id must match parent project_id';
                END IF;

                IF parent_sector_id <> NEW.sector_id THEN
                    RAISE EXCEPTION 'child asset sector_id must match parent sector_id';
                END IF;

                IF parent_asset_type NOT IN ('programmable_node', 'gateway', 'relay_module', 'power_unit') THEN
                    RAISE EXCEPTION 'parent asset type % cannot contain child assets', parent_asset_type;
                END IF;

                IF NEW.asset_type IN ('programmable_node', 'gateway', 'power_unit') THEN
                    RAISE EXCEPTION 'asset_type % cannot be assigned as child via parent_asset_id in this model', NEW.asset_type;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_topology_links_validate()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_project_id UUID;
        BEGIN
            IF NEW.source_asset_id IS NOT NULL THEN
                SELECT project_id INTO v_project_id
                FROM assets
                WHERE id = NEW.source_asset_id;

                IF NOT FOUND THEN
                    RAISE EXCEPTION 'source_asset_id % does not exist', NEW.source_asset_id;
                END IF;

                IF v_project_id <> NEW.project_id THEN
                    RAISE EXCEPTION 'source_asset_id belongs to a different project';
                END IF;
            END IF;

            IF NEW.target_asset_id IS NOT NULL THEN
                SELECT project_id INTO v_project_id
                FROM assets
                WHERE id = NEW.target_asset_id;

                IF NOT FOUND THEN
                    RAISE EXCEPTION 'target_asset_id % does not exist', NEW.target_asset_id;
                END IF;

                IF v_project_id <> NEW.project_id THEN
                    RAISE EXCEPTION 'target_asset_id belongs to a different project';
                END IF;
            END IF;

            IF NEW.source_sector_id IS NOT NULL THEN
                SELECT project_id INTO v_project_id
                FROM sectors
                WHERE id = NEW.source_sector_id;

                IF NOT FOUND THEN
                    RAISE EXCEPTION 'source_sector_id % does not exist', NEW.source_sector_id;
                END IF;

                IF v_project_id <> NEW.project_id THEN
                    RAISE EXCEPTION 'source_sector_id belongs to a different project';
                END IF;
            END IF;

            IF NEW.target_sector_id IS NOT NULL THEN
                SELECT project_id INTO v_project_id
                FROM sectors
                WHERE id = NEW.target_sector_id;

                IF NOT FOUND THEN
                    RAISE EXCEPTION 'target_sector_id % does not exist', NEW.target_sector_id;
                END IF;

                IF v_project_id <> NEW.project_id THEN
                    RAISE EXCEPTION 'target_sector_id belongs to a different project';
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$;
        """
    )

    op.execute("DROP TRIGGER IF EXISTS projects_set_updated_at ON projects")
    op.execute(
        """
        CREATE TRIGGER projects_set_updated_at
        BEFORE UPDATE ON projects
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute("DROP TRIGGER IF EXISTS locations_set_updated_at ON locations")
    op.execute(
        """
        CREATE TRIGGER locations_set_updated_at
        BEFORE UPDATE ON locations
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute("DROP TRIGGER IF EXISTS sectors_set_updated_at ON sectors")
    op.execute(
        """
        CREATE TRIGGER sectors_set_updated_at
        BEFORE UPDATE ON sectors
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute("DROP TRIGGER IF EXISTS assets_set_updated_at ON assets")
    op.execute(
        """
        CREATE TRIGGER assets_set_updated_at
        BEFORE UPDATE ON assets
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute("DROP TRIGGER IF EXISTS topology_links_set_updated_at ON topology_links")
    op.execute(
        """
        CREATE TRIGGER topology_links_set_updated_at
        BEFORE UPDATE ON topology_links
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute("DROP TRIGGER IF EXISTS assets_validate_before_write ON assets")
    op.execute(
        """
        CREATE TRIGGER assets_validate_before_write
        BEFORE INSERT OR UPDATE ON assets
        FOR EACH ROW
        EXECUTE FUNCTION trg_assets_validate();
        """
    )
    op.execute("DROP TRIGGER IF EXISTS topology_links_validate_before_write ON topology_links")
    op.execute(
        """
        CREATE TRIGGER topology_links_validate_before_write
        BEFORE INSERT OR UPDATE ON topology_links
        FOR EACH ROW
        EXECUTE FUNCTION trg_topology_links_validate();
        """
    )


def downgrade() -> None:
    """Drop core public schema objects created in this migration."""

    op.execute("SET LOCAL search_path TO public")

    op.execute("DROP TABLE IF EXISTS topology_links")
    op.execute("DROP TABLE IF EXISTS assets")
    op.execute("DROP TABLE IF EXISTS sectors")
    op.execute("DROP TABLE IF EXISTS locations")
    op.execute("DROP TABLE IF EXISTS projects")

    op.execute("DROP FUNCTION IF EXISTS trg_topology_links_validate()")
    op.execute("DROP FUNCTION IF EXISTS trg_assets_validate()")
    op.execute("DROP FUNCTION IF EXISTS normalize_mac_address(text)")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    op.execute("DROP TYPE IF EXISTS link_status_enum")
    op.execute("DROP TYPE IF EXISTS topology_relation_enum")
    op.execute("DROP TYPE IF EXISTS asset_status_enum")
    op.execute("DROP TYPE IF EXISTS asset_type_enum")
    op.execute("DROP TYPE IF EXISTS project_status_enum")
