DROP TABLE IF EXISTS raw_usgs;
CREATE TABLE IF NOT EXISTS raw_usgs (
    time            timestamp,
    stream_flow     decimal,
    gage_height     decimal
);

DROP TABLE IF EXISTS raw_hobolink;
CREATE TABLE IF NOT EXISTS raw_hobolink (
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

DROP TABLE IF EXISTS ecoli_predictions;
CREATE TABLE IF NOT EXISTS ecoli_predictions (
    timestamp       timestamp,
    r2_probability  decimal,
    r3_probability  decimal,
    r4_probability  decimal,
    r5_probability  decimal,
    r2_safe         boolean,
    r3_safe         boolean,
    r4_safe         boolean,
    r5_safe         boolean
);

COMMIT;