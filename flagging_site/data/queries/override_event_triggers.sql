CREATE OR REPLACE FUNCTION record_override_change()
    RETURNS trigger AS $$
        BEGIN
            INSERT INTO override_history(
                time,
                boathouse,
                overridden,
                reason
            )
            VALUES(
                now() AT TIME ZONE 'EST',
                NEW.boathouse,
                NEW.overridden,
                NEW.reason
            );
            RETURN NULL;
        END; $$
    LANGUAGE 'plpgsql'
;
CREATE TRIGGER record_manual_overrides
    AFTER UPDATE OF overridden, reason ON boathouses
    FOR EACH ROW
    EXECUTE PROCEDURE record_override_change()
;
