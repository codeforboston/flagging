DROP TABLE IF EXISTS usgs;
CREATE TABLE IF NOT EXISTS usgs (
    time            timestamp,
    stream_flow     decimal,
    gage_height     decimal
);

DROP TABLE IF EXISTS hobolink;
CREATE TABLE IF NOT EXISTS hobolink (
    time            timestamp,
    pressure        decimal,
    par             decimal, /* photosynthetically active radiation */
    rain            decimal,
    rh              decimal, /* relative humidity */
    dew_point       decimal,
    wind_speed      decimal,
    gust_speed      decimal,
    wind_dir        decimal,
    water_temp      decimal,
    air_temp        decimal
);

DROP TABLE IF EXISTS boathouses;
CREATE TABLE IF NOT EXISTS boathouses (
    reach           int,
    boathouse       varchar(255),
    latitude        decimal,
    longitude       decimal
);

DROP TABLE IF EXISTS model_outputs;
CREATE TABLE IF NOT EXISTS model_outputs (
    reach           int,
    time            timestamp,
    log_odds        decimal,
    probability     decimal,
    safe            boolean
);

DROP TABLE IF EXISTS cyano_overrides;
CREATE TABLE IF NOT EXISTS cyano_overrides (
    reach           int,
    start_time      timestamp,
    end_time        timestamp
);

COMMIT;