"""Add PostGIS geography column to locations

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-27 12:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add locations.geom (geography Point) and spatial index when PostGIS is available."""

    op.execute("SET LOCAL search_path TO public")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'postgis') THEN
                CREATE EXTENSION IF NOT EXISTS postgis;
            ELSE
                RAISE NOTICE 'PostGIS no está disponible en esta instancia; se omite columna locations.geom.';
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'locations'
                      AND column_name = 'geom'
                ) THEN
                    ALTER TABLE public.locations
                    ADD COLUMN geom geography(Point, 4326);
                END IF;

                UPDATE public.locations
                SET geom = ST_SetSRID(
                    ST_MakePoint(longitude::double precision, latitude::double precision),
                    4326
                )::geography
                WHERE latitude IS NOT NULL
                  AND longitude IS NOT NULL
                  AND geom IS NULL;

                CREATE INDEX IF NOT EXISTS idx_locations_geom
                ON public.locations
                USING GIST (geom);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Drop spatial index and geography column if they exist."""

    op.execute("SET LOCAL search_path TO public")
    op.execute("DROP INDEX IF EXISTS public.idx_locations_geom")
    op.execute("ALTER TABLE IF EXISTS public.locations DROP COLUMN IF EXISTS geom")
