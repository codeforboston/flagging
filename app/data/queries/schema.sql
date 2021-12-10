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

CREATE TABLE IF NOT EXISTS override_history (
    time            timestamp,
    boathouse_name  text,
    overridden      boolean,
    reason          text
);

COMMIT;
