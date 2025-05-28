# flake8: noqa: E501
"""
Updated version of model for 2025
"""

import numpy as np
import pandas as pd


MODEL_YEAR = "2025"

MODEL_THRESHOLD = 630


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
    df_hobolink["log_air_temp"] = np.log(np.maximum(df_hobolink["temperature"], 1))
    df_usgs_b["log_gage_height"] = np.log(np.maximum(df_usgs_b["gage_height"], 1))

    # Fill missing data for dew point using the Magnus formula.
    # Hobolink device is having issues with this field.
    c = 243.04
    b = 17.625
    temp_celsius = (df_hobolink["temperature"] - 32) * 5 / 9
    gamma = np.log(df_hobolink["rh"] / 100) + (b * temp_celsius) / (c + temp_celsius)
    dew_point_est = (c * gamma / (b - gamma)) * 9 / 5 + 32
    df_hobolink["dew_point"] = df_hobolink["dew_point"].fillna(dew_point_est)

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
                "log_gage_height": "mean",
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
                "wind_direction": "mean",
                # 'water_temp': np.mean,
                # "air_temp": "mean",
                "log_air_temp": "mean",
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
    if df.iloc[-1, :][["log_stream_flow", "rain", "log_gage_height"]].isna().any():
        df = df.drop(df.index[-1])

    # The code from here on consists of feature transformations.

    df["geomean_rh_0_to_72h"] = np.exp(np.log(df["rh"]).rolling(72).mean())
    df["geomean_air_temp_0_to_72h"] = np.exp(df["log_air_temp"].rolling(72).mean())
    df["geomean_gage_height_0_to_12h"] = np.exp(df["log_gage_height"].rolling(12).mean())
    df["geomean_gage_height_0_to_24h"] = np.exp(df["log_gage_height"].rolling(24).mean())
    df["geomean_pressure_0_to_72h"] = np.exp(np.log(df["pressure"]).rolling(72).mean())
    df["geomean_dew_0_to_1h"] = np.exp(np.log(df["dew_point"]).rolling(1).mean())
    df["geomean_par_0_to_72h"] = np.exp(np.log(df["par"]).rolling(72).mean())

    df["geomean_stream_flow_0h_to_12h"] = np.exp(df["log_stream_flow"].rolling(12).mean())
    df["geomean_stream_flow_0h_to_24h"] = np.exp(df["log_stream_flow"].rolling(24).mean())
    df["sum_rain_0h_to_12h"] = df["rain"].rolling(12).sum()
    df["sum_rain_0h_to_24h"] = df["rain"].rolling(24).sum()

    df["_last_rain"] = df["time"].where(df["rain"] > 0).ffill().fillna(df["time"].min())
    df["days_since_last_rain"] = (df["time"] - df["_last_rain"]).dt.total_seconds() / 60 / 60 / 24
    df["days_since_last_rain"] = np.minimum(df["days_since_last_rain"], 60)
    return df


def reach_2_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    For Location 1 (Reach 2):

    log(y1) ≈ 34.46902113 + 0.93885992 * (A) + 0.03317324 * (B) - 0.04724746 * (C)
        + 0.55518803 * (D) - 1.17528218 * (E)

        A is the total rain in inches over the last 0-12 hours.
        B is the average relative humidity over the last 0-72 hours.
        C is the number of days since the last rainfall.
        D is the average gage height over the last 0-24 hours.
        E is the average pressure over the last 0-72 hours.

    If log(y1) > log(410), the water should be flagged.

    # TODO: what does rows do...?
    Args:
        df: Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """
    if rows is None:
        df = df.copy()
    else:
        df = df.tail(n=rows).copy()

    df["predicted_ecoli_cfu_100ml"] = np.exp(
        34.46902113
        + 0.93885992 * df["sum_rain_0h_to_12h"]
        + 0.03317324 * df["geomean_rh_0_to_72h"]
        - 0.04724746 * df["days_since_last_rain"]
        + 0.55518803 * df["geomean_gage_height_0_to_24h"]
        - 1.17528218 * df["geomean_pressure_0_to_72h"]
    )

    df["safe"] = df["predicted_ecoli_cfu_100ml"] < MODEL_THRESHOLD
    df["reach_id"] = 2

    return df[["reach_id", "time", "predicted_ecoli_cfu_100ml", "safe"]]


def reach_3_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    For Location 2 (Reach 3):

    log(y2) ≈ -0.127560493 + 0.002151132 * (A) + 0.729157175 * (B) + 0.050053561 * (C)
        - 0.025954114 * (D) + 0.376567517 * (E)

        A is the average flow discharge over the last 0-12 hours.
        B is the total rain in inches over the last 0-24 hours.
        C is the average relative humidity over the last 0-72 hours.
        D is the average dew point over the last 0-1 hour.
        E is the average gage height over the last 0-12 hours.

    If log(y2) > log(410), the water should be flagged.

    Args:
        df: (pd.DataFrame) Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """
    if rows is None:
        df = df.copy()
    else:
        df = df.tail(n=rows).copy()

    df["predicted_ecoli_cfu_100ml"] = np.exp(
        -0.127560493
        + 0.002151132 * df["geomean_stream_flow_0h_to_12h"]
        + 0.729157175 * df["sum_rain_0h_to_24h"]
        + 0.050053561 * df["geomean_rh_0_to_72h"]
        - 0.025954114 * df["geomean_dew_0_to_1h"]
        + 0.376567517 * df["geomean_gage_height_0_to_24h"]
    )

    df["safe"] = df["predicted_ecoli_cfu_100ml"] < MODEL_THRESHOLD
    df["reach_id"] = 3

    return df[["reach_id", "time", "predicted_ecoli_cfu_100ml", "safe"]]


def reach_4_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    For Location 3 (Reach 4):
    log(y3) ≈ -0.76489744 + 0.97382836 * (A) + 0.03942634 * (B) - 0.02300373 * (C)
        + 0.57635453 * (D) + 0.00063504 * (E)

        A is the total rain in inches over the last 0-12 hours.
        B is the average relative humidity over the last 0-72 hours.
        C is the average dew point over the last 0-1 hour.
        D is the average gage height over the last 0-24 hours.
        E is the average flow discharge over the last 0-24 hours.

    If log(y3) > log(410), the water should be flagged.

    Args:
        df: (pd.DataFrame) Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """
    if rows is None:
        df = df.copy()
    else:
        df = df.tail(n=rows).copy()

    df["predicted_ecoli_cfu_100ml"] = np.exp(
        -0.76489744
        + 0.97382836 * df["sum_rain_0h_to_12h"]
        + 0.03942634 * df["geomean_rh_0_to_72h"]
        - 0.02300373 * df["geomean_dew_0_to_1h"]
        + 0.57635453 * df["geomean_gage_height_0_to_24h"]
        + 0.00063504 * df["geomean_stream_flow_0h_to_24h"]
    )

    df["safe"] = df["predicted_ecoli_cfu_100ml"] < MODEL_THRESHOLD
    df["reach_id"] = 4

    return df[["reach_id", "time", "predicted_ecoli_cfu_100ml", "safe"]]


def reach_5_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    For Location 4 (Reach 5):
    log(y4) ≈ 7.83998714 + 0.00307767 * (A) -0.06024566 * (B) + 1.47575767 * (C)
        -0.03135596 * (D) - -0.03135596 * (E)

        A is the average flow discharge over the last 0-12 hours.
        B is the average air temperature over the last 0-72 hours.
        C is the total rain in inches over the last 0-24 hours.
        D is the number of days since the last rainfall.
        E is the average Photosynthetic Active Radiation over the last 0-72 hourz.

    If log(y4) > log(410), the water should be flagged.

    Args:
        df: (pd.DataFrame) Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """
    if rows is None:
        df = df.copy()
    else:
        df = df.tail(n=rows).copy()

    df["predicted_ecoli_cfu_100ml"] = np.exp(
        7.83998714
        + 0.00307767 * df["geomean_stream_flow_0h_to_12h"]
        - 0.06024566 * df["geomean_air_temp_0_to_72h"]
        + 1.47575767 * df["sum_rain_0h_to_24h"]
        - 0.03135596 * df["days_since_last_rain"]
        - 0.03135596 * df["geomean_par_0_to_72h"]
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
