# flake8: noqa: E501
"""
Updated version of model for 2023
"""
import numpy as np
import pandas as pd


MODEL_YEAR = '2023'

SIGNIFICANT_RAIN = 0.1

MODEL_THRESHOLD = 235


def process_data(
        df_hobolink: pd.DataFrame,
        df_usgs: pd.DataFrame
) -> pd.DataFrame:
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
    df_hobolink['time'] = pd.to_datetime(df_hobolink['time'])
    df_usgs['time'] = pd.to_datetime(df_usgs['time'])

    # Convert all timestamps to hourly in preparation for aggregation.
    df_usgs['time'] = df_usgs['time'].dt.floor('h')
    df_hobolink['time'] = df_hobolink['time'].dt.floor('h')

    # The new model takes geomeans of some variables.
    # Put a floor on 0 for all of these variables, to be safe.
    df_usgs['log_stream_flow'] = \
        np.log(np.maximum(df_usgs['stream_flow'], 1))
    df_hobolink['log_air_temp'] = \
        np.log(np.maximum(df_hobolink['air_temp'], 1))

    # TODO: look into how to calculate this
    # the new model also takes max of whether there was > 0.1 rain per
    # 10 minute increment.
    df_hobolink['_sig_rain'] = \
        (df_hobolink['rain'].rolling(24 * 6).max()) >= SIGNIFICANT_RAIN
    df_hobolink['_last_sig_rain'] = (
        df_hobolink['time']
        .where(df_hobolink['_sig_rain'])
        .ffill()
        .fillna(df_hobolink['time'].min())
    )
    df_hobolink['days_since_sig_rain'] = (
        (df_hobolink['time'] - df_hobolink['_last_sig_rain']).dt.total_seconds() / 60 / 60 / 24
    )

    # Now collapse the data.
    # Take the mean measurements of everything except rain; rain is the sum
    # within an hour. (HOBOlink devices record all rain seen in 10 minutes).
    df_usgs = (
        df_usgs
        .groupby('time')
        .agg({
            'log_stream_flow': np.mean,
        })
        .reset_index()
    )
    df_hobolink = (
        df_hobolink
        .groupby('time')
        .agg({
            'rain': np.sum,
            'log_air_temp': np.mean,
            'days_since_sig_rain': np.min
        })
        .reset_index()
    )

    # This is an outer join to include all the data (we collect more Hobolink
    # data than USGS data). With that said, for the most recent value, we need
    # to make sure one of the sources didn't update before the other one did.
    # Note that usually Hobolink updates first.
    df = df_hobolink.merge(right=df_usgs, how='left', on='time')
    df = df.sort_values('time')
    df = df.reset_index()

    # Drop last row if either Hobolink or USGS is missing.
    # We drop instead of `ffill()` because we want the model to output
    # consistently each hour.
    if df.iloc[-1, :][['log_air_temp', 'rain']].isna().any():
        df = df.drop(df.index[-1])

    # The code from here on consists of feature transformations.

    df['geomean_air_temp_0_to_72h'] = np.exp(df['log_air_temp'].rolling(72).mean())

    df['geomean_stream_flow_0h_to_1h'] = np.exp(df['log_stream_flow'])
    df['geomean_stream_flow_0h_to_12h'] = np.exp(df['log_stream_flow'].rolling(12).mean())
    df['geomean_stream_flow_0h_to_24h'] = np.exp(df['log_stream_flow'].rolling(24).mean())

    df[f'sum_rain_0h_to_12h'] = df['rain'].rolling(12).sum()
    df[f'sum_rain_48h_to_96h'] = df['rain'].rolling(96).sum() - df['rain'].rolling(48).sum()
    df[f'sum_rain_0h_to_168h'] = df['rain'].rolling(168).sum()

    # todo: validate sig rain:
    # - C is the number of days since the last “Major Rainfall” (more than 0.1 inches)

    # Lastly, they measure the "time since last significant rain." Significant
    # rain is defined as a cumulative sum of 0.1 in over a 24 hour time period.
    df['sig_rain'] = df['sum_rain_0h_to_12h'] >= SIGNIFICANT_RAIN
    df['last_sig_rain'] = (
        df['time']
        .where(df['sig_rain'])
        .ffill()
        .fillna(df['time'].min())
    )
    df['days_since_sig_rain'] = (
        (df['time'] - df['last_sig_rain']).dt.total_seconds() / 60 / 60 / 24
    )

    return df


def reach_2_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    For Location 1 (Reach 2):
    log(y1) ≈ 5.1681832 + 4.6625787 ∗ (A) + 0.0006113 ∗ (B)

        A is the total rain in inches over the last 0-12 hours.
        B is the average flow discharge over the last 0-1 hour.

    If log(y1) > log(235), the water should be flagged.

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


    df['predicted_ecoli_cfu_100ml'] = np.exp(
        5.1681832
        + 4.6625787 * df['sum_rain_0h_to_12h']
        + 0.0006113 * df['geomean_stream_flow_0h_to_1h']
    )

    df['safe'] = df['predicted_ecoli_cfu_100ml'] < MODEL_THRESHOLD
    df['reach_id'] = 2

    return df[['reach_id', 'time', 'predicted_ecoli_cfu_100ml', 'safe']]


def reach_3_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    For Location 2 (Reach 3):
    log(y2) ≈ 5.501886 + 2.997021 ∗ (A) − 0.014088 y2 ∗ (B) + 0.003538 ∗ (C)

        A is the total rain in inches over the last 0-12 hours.
        B is the average air temperature over the last 0-3 days.
        C is the number of days since the last “Major Rainfall” (more than 0.1 inches)

    If log(y2) > log(235), the water should be flagged.

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

    df['predicted_ecoli_cfu_100ml'] = np.exp(
        5.501886
        + 2.997021 * df['sum_rain_0h_to_12h']
        - 0.014088 * df['geomean_air_temp_0_to_72h']
        + 0.003538 * df['days_since_sig_rain']
    )

    df['safe'] = df['predicted_ecoli_cfu_100ml'] < MODEL_THRESHOLD
    df['reach_id'] = 3

    return df[['reach_id', 'time', 'predicted_ecoli_cfu_100ml', 'safe']]


def reach_4_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    For Location 3 (Reach 4):
    log(y3) ≈ 4.380013 + 0.011368 ∗ (A) − 0.010225 y3 ∗ (B) + 3.765905 ∗ (C)

        A is the average flow discharge over the last 0-12 hours.
        B is the average flow discharge over the last 0-24 hours.
        C is the total rain in inches over the last 0-12 hours.

    If log(y3) > log(235), the water should be flagged.

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

    df['predicted_ecoli_cfu_100ml'] = np.exp(
        4.380013
        + 0.011368 * df['geomean_stream_flow_0h_to_12h']
        - 0.010225 * df['geomean_stream_flow_0h_to_24h']
        + 3.765905 * df['sum_rain_0h_to_12h']
    )

    df['safe'] = df['predicted_ecoli_cfu_100ml'] < MODEL_THRESHOLD
    df['reach_id'] = 4

    return df[['reach_id', 'time', 'predicted_ecoli_cfu_100ml', 'safe']]


def reach_5_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    For Location 4 (Reach 5):
    log(y4) ≈ 3.0615415 − 0.5564694 ∗ (A) + 0.0022405 ∗ (B) + 0.2938575 ∗ (C) − 0.0305788 ∗ (D)

        A is the total rain in inches over the last 48-96 hours.
        B is the average flow discharge over the last 0-1 hour.
        C is the total rain in inches over the last 0-7 days.
        D is the total rain in inches over the last 0-12 hours.

    If log(y4) > log(235), the water should be flagged.

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

    df['predicted_ecoli_cfu_100ml'] = np.exp(
        3.0615415
        - 0.5564694 * df['sum_rain_48h_to_96h']
        + 0.0022405 * df['geomean_stream_flow_0h_to_1h']
        + 0.2938575 * df['sum_rain_0h_to_168h']
        - 0.0305788 * df['sum_rain_0h_to_12h']
    )

    df['safe'] = df['predicted_ecoli_cfu_100ml'] < MODEL_THRESHOLD
    df['reach_id'] = 5

    return df[['reach_id', 'time', 'predicted_ecoli_cfu_100ml', 'safe']]


def all_models(df: pd.DataFrame, *args, **kwargs):
    # Cast to datetime type.
    # When this comes from Celery, it might be a string.
    df['time'] = pd.to_datetime(df['time'])

    out = pd.concat([
        reach_2_model(df, *args, **kwargs),
        reach_3_model(df, *args, **kwargs),
        reach_4_model(df, *args, **kwargs),
        reach_5_model(df, *args, **kwargs),
    ], axis=0)
    out = out.sort_values(['reach_id', 'time'])

    out = out.loc[out['predicted_ecoli_cfu_100ml'].notna(), :]
    return out
