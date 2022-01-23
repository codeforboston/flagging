DROP TRIGGER IF EXISTS record_manual_overrides ON boathouse;

CREATE OR REPLACE FUNCTION record_override_change()
    -- Create a trigger that records the history of manual overrides.
    RETURNS trigger AS $$
        BEGIN
            INSERT INTO override_history(
                time,
                boathouse_name,
                overridden,
                reason
            )
            VALUES(
                now() AT TIME ZONE 'EST',
                NEW.name,
                NEW.overridden,
                NEW.reason
            );
            RETURN NULL;
        END; $$
    LANGUAGE 'plpgsql'
;

CREATE TRIGGER record_manual_overrides
    AFTER UPDATE OF overridden, reason ON boathouse
    FOR EACH ROW
    EXECUTE PROCEDURE record_override_change()
;
