DROP TABLE IF EXISTS usgs;
CREATE TABLE usgs (
    time            timestamp,
    stream_flow     decimal,
    gage_height     decimal
);

DROP TABLE IF EXISTS hobolink;
CREATE TABLE hobolink (
    time            timestamp,
    pressure        decimal,
    par             decimal, -- photosynthetically active radiation
    rain            decimal,
    rh              decimal, -- relative humidity
    dew_point       decimal,
    wind_speed      decimal,
    gust_speed      decimal,
    wind_dir        decimal,
    water_temp      decimal,
    air_temp        decimal
);

DROP TABLE IF EXISTS model_outputs;
CREATE TABLE model_outputs (
    reach           int,
    time            timestamp,
    log_odds        decimal,
    probability     decimal,
    safe            boolean
);

/* We don't want to ever drop this table because it may contain important
   information that can't be recalculated. */
CREATE TABLE IF NOT EXISTS override_history (
    time            timestamp,
    boathouse       text,
    overridden      boolean,
    reason          text
);


/* These tables are defined with SQLAlchemy. */

DROP TABLE IF EXISTS boathouses;
DROP TABLE IF EXISTS live_website_options;

COMMIT;
