# flake8: noqa: E501
"""
Updated version of model for 2025

The arithmetic mean features model with linear predictors
TO USE THIS, MUST USE USGS COPY.PY
"""

import numpy as np
import pandas as pd


MODEL_YEAR = "2025"

MODEL_THRESHOLD = 410


def process_data(
    df_hobolink: pd.DataFrame, df_usgs_w: pd.DataFrame, df_usgs_b: pd.DataFrame
) -> pd.DataFrame:
    """Combines the data from the Hobolink and the USGS into one table.

    Args:
        df_hobolink: Hobolink data
        df_usgs_w: USGS NWIS Waltham data
        df_usgs_b: USGS NWIS Brookline data

    Returns:
        Cleaned dataframe.
    """
    df_hobolink = df_hobolink.copy()
    df_usgs_w = df_usgs_w.copy()
    df_usgs_b = df_usgs_b.copy()

    # Cast to datetime type.
    # When this comes from Celery, it might be a string.
    df_hobolink["time"] = pd.to_datetime(df_hobolink["time"])
    df_usgs_w["time"] = pd.to_datetime(df_usgs_w["time"])
    df_usgs_b["time"] = pd.to_datetime(df_usgs_b["time"])

    # Convert all timestamps to hourly in preparation for aggregation.
    df_usgs_w["time"] = df_usgs_w["time"].dt.floor("h")
    df_usgs_b["time"] = df_usgs_b["time"].dt.floor("h")
    df_hobolink["time"] = df_hobolink["time"].dt.floor("h")

    # TODO: LOOK AT THE NORMAL MEANS INSTEAD OF GEOMETRIC MEANS OF THE DATA. LOG EVERYTHING NOT RECOMMENDED
    # The new model takes geomeans of some variables.
    # Put a floor on 0 for all of these variables, to be safe.
    df_usgs_w["log_stream_flow"] = np.log(np.maximum(df_usgs_w["stream_flow"], 1))

    # Now collapse the data.
    # Take the mean measurements of everything except rain; rain is the sum
    # within an hour. (HOBOlink devices record all rain seen in 10 minutes).
    df_usgs_w = (
        df_usgs_w.groupby("time")
        .agg(
            {
                "log_stream_flow": "mean",
            }
        )
        .reset_index()
    )
    df_usgs_b = (
        df_usgs_b.groupby("time")
        .agg(
            {
                "gage_height": "mean",
                "precip": "mean",
            }
        )
        .reset_index()
    )

    df_hobolink = (
        df_hobolink.groupby("time")
        .agg(
            {
                "pressure": "mean",
                "par": "mean",
                "rain": "sum",
                "rh": "mean",
                "dew_point": "mean",
                "wind_speed": "mean",
                "gust_speed": "mean",
                "wind_dir": "mean",
                "air_temp": "mean",
            }
        )
        .reset_index()
    )

    # This is an outer join to include all the data (we collect more Hobolink
    # data than USGS data). With that said, for the most recent value, we need
    # to make sure one of the sources didn't update before the other one did.
    # Note that usually Hobolink updates first.

    # to merge, make sure that there are not any overlapping column names
    df = df_hobolink.merge(right=df_usgs_w, how="left", on="time")
    df = df.merge(right=df_usgs_b, how="left", on="time")
    df = df.sort_values("time")
    df = df.reset_index()

    # Drop last row if either Hobolink or either USGS is missing.
    # We drop instead of `ffill()` because we want the model to output
    # consistently each hour.
    # Choosing an arbitrary variable from each of the three datasets - waltham, hobolink, muddy river
    if df.iloc[-1, :][["log_stream_flow", "rain", "gage_height"]].isna().any():
        df = df.drop(df.index[-1])

    # The code from here on consists of feature transformations.
    # for var in x:
    #     df[f"exp_log_mean_{var}"] = np.exp(
    #         df[var].rolling(window=12, min_periods=1).apply(lambda x: np.log(x + 1).mean(), raw=True)
    #     ) - 1

    df["mean_rh_0_to_72h"] = (df["rh"]).rolling(72).mean()
    df["mean_gage_height_0_to_24h"] = df["gage_height"].rolling(24).mean()
    df["mean_gage_height_0_to_72h"] = df["gage_height"].rolling(72).mean()
    df["mean_precip_0_to_24h"] = df["precip"].rolling(24).mean()
    df["mean_precip_0_to_48h"] = df["precip"].rolling(48).mean()
    df["mean_precip_0_to_72h"] = df["precip"].rolling(72).mean()
    df["mean_pressure_0_to_1h"] = df["pressure"].rolling(1).mean()
    df["mean_dew_0_to_72h"] = df["dew_point"].rolling(72).mean()
    df["mean_par_0_to_1h"] = df["par"].rolling(1).mean()
    df["mean_par_0_to_24h"] = df["par"].rolling(24).mean()
    df["mean_par_0_to_48h"] = df["par"].rolling(48).mean()
    df["mean_par_0_to_72h"] = df["par"].rolling(72).mean()
    df["mean_air_temp_0_to_1h"] = df["air_temp"].rolling(1).mean()
    df["mean_air_temp_0_to_48h"] = df["air_temp"].rolling(48).mean()
    df["mean_air_temp_0_to_72h"] = df["air_temp"].rolling(72).mean()

    df["geomean_stream_flow_0h_to_1h"] = df["log_stream_flow"].rolling(1).mean()
    df["geomean_stream_flow_0h_to_12h"] = df["log_stream_flow"].rolling(12).mean()
    df["geomean_stream_flow_0h_to_48h"] = df["log_stream_flow"].rolling(48).mean()
    df["sum_rain_0h_to_12h"] = df["rain"].rolling(12).sum()

    df["_last_rain"] = df["time"].where(df["rain"] > 0).ffill().fillna(df["time"].min())
    df["days_since_last_rain"] = (df["time"] - df["_last_rain"]).dt.total_seconds() / 60 / 60 / 24
    df["days_since_last_rain"] = np.minimum(df["days_since_last_rain"], 60)
    return df


def reach_2_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    For Location 1 (Reach 2):

    log(y1) ≈ 6.26703436 + 1.49282919 * (A) - 0.06759288 * (B) - 0.00057831 * (C)
        + 0.00012892 * (D) + 0.00031725 * (E)

        A is the total rain in inches over the last 0-12 hours.
        B is the number of days since the last rainfall.
        C is the average photosynthetic active radiation over the last 0-72 hours.
        D is the geometric mean of the flow discharge over the last 0-1 hour.
        E is the average photosynthetic active radiation over the last 0-24 hours.

    If log(y1) > log(410), the water should be flagged.

    Args:
        df: Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """

    df["predicted_ecoli_cfu_100ml"] = np.exp(
        6.26703436
        + 1.49282919 * df["sum_rain_0h_to_12h"]
        - 0.06759288 * df["days_since_last_rain"]
        - 0.00057831 * df["mean_par_0_to_72h"]
        + 0.00012892 * df["geomean_stream_flow_0h_to_1h"]
        + 0.00031725 * df["mean_par_0_to_24h"]
    )

    df["safe"] = df["predicted_ecoli_cfu_100ml"] < MODEL_THRESHOLD
    df["reach_id"] = 2

    return df[["reach_id", "time", "predicted_ecoli_cfu_100ml", "safe"]]


def reach_3_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    For Location 2 (Reach 3):

    log(y2) ≈ 1.89615335 + 0.00204568 * (A) - 0.01131549 * (B) + 0.05599591 * (C)
        + 0.76839106 * (D) - 0.00382190 * (E)

        A is the average flow discharge over the last 0-1 hour.
        B is the average air temperature over the last 0-72 hours.
        C is the average relative humidity over the last 0-72 hours.
        D is the total rain in inches over the last 0-12 hours.
        E is the average air temperature over the last 0-1 hour.

    If log(y2) > log(410), the water should be flagged.

    Args:
        df: (pd.DataFrame) Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """

    df["predicted_ecoli_cfu_100ml"] = np.exp(
        1.89615335
        + 0.00204568 * df["geomean_stream_flow_0h_to_1h"]
        - 0.01131549 * df["mean_air_temp_0_to_72h"]
        + 0.05599591 * df["mean_rh_0_to_72h"]
        + 0.76839106 * df["sum_rain_0h_to_12h"]
        - 0.00382190 * df["mean_air_temp_0_to_1h"]
    )

    df["safe"] = df["predicted_ecoli_cfu_100ml"] < MODEL_THRESHOLD
    df["reach_id"] = 3

    return df[["reach_id", "time", "predicted_ecoli_cfu_100ml", "safe"]]


def reach_4_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    For Location 3 (Reach 4):

    log(y3) ≈ 4.63754422 + 295.32071359 * (A) + 0.00058180 * (B) + 0.02037119 * (C)
        + 0.00436879 * (D) + 0.36385351 * (E)

        A is the average precipitation over the last 0-24 hours.
        B is the average flow discharge over the last 0-48 hours.
        C is the average gage height over the last 0-24 hours.
        D is the average dew point over the last 0-72 hours.
        E is the the total rain in inches over the last 0-12 hours.

    If log(y3) > log(410), the water should be flagged.

    Args:
        df: (pd.DataFrame) Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """

    df["predicted_ecoli_cfu_100ml"] = np.exp(
        4.63754422
        + 295.32071359 * df["mean_precip_0_to_48h"]
        + 0.00058180 * df["geomean_stream_flow_0h_to_48h"]
        + 0.02037119 * df["mean_gage_height_0_to_24h"]
        + 0.00436879 * df["mean_dew_0_to_72h"]
        + 0.36385351 * df["sum_rain_0h_to_12h"]
    )

    df["safe"] = df["predicted_ecoli_cfu_100ml"] < MODEL_THRESHOLD
    df["reach_id"] = 4

    return df[["reach_id", "time", "predicted_ecoli_cfu_100ml", "safe"]]


def reach_5_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    For Location 4 (Reach 5):

    log(y4) ≈ 8.21991286 - 129.51401580 * (A) + 680.15322386 * (B) - 0.00036148 * (C)
        - 0.06276234 * (D) - 0.03413243 * (E)

    log(y4) ≈ 7.83998714 + 0.00307767 * (A) -0.06024566 * (B) + 1.47575767 * (C)
        -0.03135596 * (D) - -0.03135596 * (E)

        A is the average precipitation over the last 0-24 hours.
        B is the average precipitation over the last 0-48 hours.
        C is the average Photosynthetic Active Radiation over the last 0-1 hour.
        D is the average air temperature over the last 0-48 hours.
        E is the number of days since the last rainfall.

    If log(y4) > log(410), the water should be flagged.

    Args:
        df: (pd.DataFrame) Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """

    df["predicted_ecoli_cfu_100ml"] = np.exp(
        8.21991286
        - 129.51401580 * df["mean_precip_0_to_24h"]
        + 680.15322386 * df["mean_precip_0_to_48h"]
        - 0.00036148 * df["mean_par_0_to_1h"]
        - 0.06276234 * df["mean_air_temp_0_to_48h"]
        - 0.03413243 * df["days_since_last_rain"]
    )

    df["safe"] = df["predicted_ecoli_cfu_100ml"] < MODEL_THRESHOLD
    df["reach_id"] = 5

    return df[["reach_id", "time", "predicted_ecoli_cfu_100ml", "safe"]]


def all_models(df: pd.DataFrame, *args, **kwargs):
    # Cast to datetime type.
    # When this comes from Celery, it might be a string.
    df["time"] = pd.to_datetime(df["time"])

    out = pd.concat(
        [
            reach_2_model(df, *args, **kwargs),
            reach_3_model(df, *args, **kwargs),
            reach_4_model(df, *args, **kwargs),
            reach_5_model(df, *args, **kwargs),
        ],
        axis=0,
    )
    out = out.sort_values(["reach_id", "time"])

    out = out.loc[out["predicted_ecoli_cfu_100ml"].notna(), :]
    return out
