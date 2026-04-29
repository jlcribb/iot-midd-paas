BEGIN;

CREATE OR REPLACE FUNCTION trg_assets_validate_sector_project()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_sector_project_id UUID;
BEGIN
    SELECT s.project_id
    INTO v_sector_project_id
    FROM sectors s
    WHERE s.id = NEW.sector_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'sector_id % does not exist', NEW.sector_id;
    END IF;

    IF v_sector_project_id <> NEW.project_id THEN
        RAISE EXCEPTION 'asset sector project mismatch: sector project_id must match asset project_id';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS assets_validate_sector_project_before_write ON assets;
CREATE TRIGGER assets_validate_sector_project_before_write
BEFORE INSERT OR UPDATE OF project_id, sector_id
ON assets
FOR EACH ROW
EXECUTE FUNCTION trg_assets_validate_sector_project();

COMMIT;
