BEGIN;

CREATE OR REPLACE FUNCTION trg_assets_prevent_parent_cycles()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_cycle_exists BOOLEAN;
BEGIN
    IF NEW.parent_asset_id IS NULL THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' AND NEW.parent_asset_id = OLD.parent_asset_id THEN
        RETURN NEW;
    END IF;

    WITH RECURSIVE parent_chain AS (
        SELECT a.id, a.parent_asset_id
        FROM assets a
        WHERE a.id = NEW.parent_asset_id
        UNION ALL
        SELECT p.id, p.parent_asset_id
        FROM assets p
        JOIN parent_chain c ON p.id = c.parent_asset_id
    )
    SELECT EXISTS (
        SELECT 1
        FROM parent_chain
        WHERE id = NEW.id
    )
    INTO v_cycle_exists;

    IF v_cycle_exists THEN
        RAISE EXCEPTION 'parent cycle detected for asset %', NEW.id;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS assets_prevent_parent_cycles_before_write ON assets;
CREATE TRIGGER assets_prevent_parent_cycles_before_write
BEFORE INSERT OR UPDATE OF parent_asset_id
ON assets
FOR EACH ROW
EXECUTE FUNCTION trg_assets_prevent_parent_cycles();

COMMIT;
