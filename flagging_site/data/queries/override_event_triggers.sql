/*
Database triggers

Eventually this can cause problems because of the Heroku free tier row
limit of 10,000. The rest of the database takes up just above ~2,500 rows.
The table "override_history" takes a while to fil,l but eventually it can
fill, if this website sticks around in prod for a while.

TODO:
  Solve the aforementioned problem in an elegant way? Right now there is
  no solution for this other than to flush it after a couple years...
*/

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