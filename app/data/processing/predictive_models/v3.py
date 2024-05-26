# flake8: noqa: E501
import numpy as np
import pandas as pd


MODEL_YEAR = "2024"

SIGNIFICANT_RAIN = 0.1
SAFETY_THRESHOLD = 0.65


def sigmoid(ser: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-ser))


def process_data(df_hobolink: pd.DataFrame, df_usgs: pd.DataFrame) -> pd.DataFrame:
    """Combines the data from the Hobolink and the USGS into one table.

    Args:
        df_hobolink: Hobolink data
        df_usgs: USGS NWIS data

    Returns:
        Cleaned dataframe.
    """
    df_hobolink = df_hobolink.copy()
    df_usgs = df_usgs.copy()

    # Cast to datetime type.
    # When this comes from Celery, it might be a string.
    df_hobolink["time"] = pd.to_datetime(df_hobolink["time"])
    df_usgs["time"] = pd.to_datetime(df_usgs["time"])

    # Convert all timestamps to hourly in preparation for aggregation.
    df_usgs["time"] = df_usgs["time"].dt.floor("h")
    df_hobolink["time"] = df_hobolink["time"].dt.floor("h")

    # Now collapse the data.
    # Take the mean measurements of everything except rain; rain is the sum
    # within an hour. (HOBOlink devices record all rain seen in 10 minutes).
    df_usgs = df_usgs.groupby("time").mean().reset_index()
    df_hobolink = (
        df_hobolink.groupby("time")
        .agg(
            {
                "pressure": np.mean,
                "par": np.mean,
                "rain": np.sum,
                "rh": np.mean,
                "dew_point": np.mean,
                "wind_speed": np.mean,
                "gust_speed": np.mean,
                "wind_dir": np.mean,
                # 'water_temp': np.mean,
                "air_temp": np.mean,
            }
        )
        .reset_index()
    )

    # This is an outer join to include all the data (we collect more Hobolink
    # data than USGS data). With that said, for the most recent value, we need
    # to make sure one of the sources didn't update before the other one did.
    # Note that usually Hobolink updates first.
    df = df_hobolink.merge(right=df_usgs, how="left", on="time")
    df = df.sort_values("time")
    df = df.reset_index()

    # Drop last row if either Hobolink or USGS is missing.
    # We drop instead of `ffill()` because we want the model to output
    # consistently each hour.
    if df.iloc[-1, :][["stream_flow", "rain"]].isna().any():
        df = df.drop(df.index[-1])

    # The code from here on consists of feature transformations.

    # Calculate rolling means
    df["stream_flow_1d_mean"] = df["stream_flow"].rolling(24).mean()
    df["pressure_2d_mean"] = df["pressure"].rolling(48).mean()

    # Calculate rolling sums
    df["rain_0_to_12h_sum"] = df["rain"].rolling(12).sum()

    # Lastly, they measure the "time since last significant rain." Significant
    # rain is defined as a cumulative sum of 0.1 in a 12-hour time period.
    df["sig_rain"] = df["rain_0_to_12h_sum"] >= SIGNIFICANT_RAIN
    df["last_sig_rain"] = df["time"].where(df["sig_rain"]).ffill().fillna(df["time"].min())
    df["days_since_sig_rain"] = (df["time"] - df["last_sig_rain"]).dt.total_seconds() / 60 / 60 / 24

    return df


def reach_2_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    1NBS:
    𝑎 = 1.444 ∗ 10^2
    𝑤 = −1.586 ∗ 10^−4
    𝑥 = 4.785
    𝑦 = −6.973
    𝑧 = 1.137

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

    df["probability"] = sigmoid(
        14.44
        - 0.0001586 * df["stream_flow_1d_mean"]
        + 4.785 * df["pressure_2d_mean"]
        - 6.973 * df["rain_0_to_12h_sum"]
        + 1.137 * df["days_since_sig_rain"]
    )

    df["safe"] = df["probability"] <= SAFETY_THRESHOLD
    df["reach_id"] = 2

    return df[["reach_id", "time", "probability", "safe"]]


def reach_3_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    2LARZ:
    𝑎 = −19.119085
    𝑤 = −0.001841
    𝑥 = 0.658676
    𝑦 = −2.766888
    𝑧 = 0.642593

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

    df["probability"] = sigmoid(
        -19.119085
        - 0.001841 * df["stream_flow_1d_mean"]
        + 0.658676 * df["pressure_2d_mean"]
        - 2.766888 * df["rain_0_to_12h_sum"]
        + 0.642593 * df["days_since_sig_rain"]
    )

    df["safe"] = df["probability"] <= SAFETY_THRESHOLD
    df["reach_id"] = 3

    return df[["reach_id", "time", "probability", "safe"]]


def reach_4_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    3BU:
    𝑎 = −23.96789
    𝑤 = 0.00248
    𝑥 = 0.83702
    𝑦 = −5.34479
    𝑧 = −0.02940

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

    df["probability"] = sigmoid(
        -23.96789
        + 0.00248 * df["stream_flow_1d_mean"]
        + 0.83702 * df["pressure_2d_mean"]
        - 5.34479 * df["rain_0_to_12h_sum"]
        - 0.02940 * df["days_since_sig_rain"]
    )

    df["safe"] = df["probability"] <= SAFETY_THRESHOLD
    df["reach_id"] = 4

    return df[["reach_id", "time", "probability", "safe"]]


def reach_5_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    4LONG:
    𝑎 = −395.24225
    𝑤 = −0.03635
    𝑥 = 13.67660
    𝑦 = −19.65122
    𝑧 = 11.64241

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

    df["probability"] = sigmoid(
        -395.24225
        - 0.03635 * df["stream_flow_1d_mean"]
        + 13.67660 * df["pressure_2d_mean"]
        - 19.65122 * df["rain_0_to_12h_sum"]
        + 11.64241 * df["days_since_sig_rain"]
    )

    df["safe"] = df["probability"] <= SAFETY_THRESHOLD
    df["reach_id"] = 5

    return df[["reach_id", "time", "probability", "safe"]]


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

    # TODO:
    #  I'm a little worried that I had to add the below to make a test pass.
    #  I thought this part of the code was pretty settled by now, but guess
    #  not. I need to look into what's going on.

    out = out.loc[out["probability"].notna(), :]
    return out
