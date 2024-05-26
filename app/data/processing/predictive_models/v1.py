# flake8: noqa: E501
"""
This file contains all the logic for modeling. The model takes data from the SQL
backend, do some calculations on that data, and then output model results.

Useful links:

- Hobolink documentation:
https://www.metrics24.de/WebRoot/Store5/Shops/62187045/5D79/1FE4/31E4/0996/0440/0A0C/6D0B/7D8C/HOBOlink-Users-Guide.pdf

- Regulatory standards in MA:
https://www.mass.gov/files/documents/2016/08/tz/36wqara.pdf
"""
import numpy as np
import pandas as pd


MODEL_VERSION = '2020'

SIGNIFICANT_RAIN = 0.2
SAFETY_THRESHOLD = 0.65


def sigmoid(ser: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-ser))


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

    # Now collapse the data.
    # Take the mean measurements of everything except rain; rain is the sum
    # within an hour. (HOBOlink devices record all rain seen in 10 minutes).
    df_usgs = (
        df_usgs
        .groupby('time')
        .mean()
        .reset_index()
    )
    df_hobolink = (
        df_hobolink
        .groupby('time')
        .agg({
            'pressure': np.mean,
            'par': np.mean,
            'rain': np.sum,
            'rh': np.mean,
            'dew_point': np.mean,
            'wind_speed': np.mean,
            'gust_speed': np.mean,
            'wind_dir': np.mean,
            # 'water_temp': np.mean,
            'air_temp': np.mean,
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
    if df.iloc[-1, :][['stream_flow', 'rain']].isna().any():
        df = df.drop(df.index[-1])

    # The code from here on consists of feature transformations.

    # Calculate rolling means
    df['par_1d_mean'] = df['par'].rolling(24).mean()
    df['stream_flow_1d_mean'] = df['stream_flow'].rolling(24).mean()

    # Calculate rolling sums
    df['rain_0_to_24h_sum'] = df['rain'].rolling(24).sum()
    df['rain_0_to_48h_sum'] = df['rain'].rolling(48).sum()
    df['rain_24_to_48h_sum'] = df['rain_0_to_48h_sum'] - df['rain_0_to_24h_sum']

    # Lastly, they measure the "time since last significant rain." Significant
    # rain is defined as a cumulative sum of 0.2 in over a 24 hour time period.
    df['sig_rain'] = df['rain_0_to_24h_sum'] >= SIGNIFICANT_RAIN
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
    """Model params:
    a- rainfall sum 0-24 hrs
    d- Days since last rain
    f- PAR avg 24 hr

    Logistic model: 0.3531*a - 0.0362*d - 0.000312*f + 0.6233

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

    df['probability'] = sigmoid(
        0.6233
        + 0.3531 * df['rain_0_to_24h_sum']
        - 0.0362 * df['days_since_sig_rain']
        - 0.000312 * df['par_1d_mean']
    )

    df['safe'] = df['probability'] <= SAFETY_THRESHOLD
    df['reach_id'] = 2

    return df[['reach_id', 'time', 'probability', 'safe']]


def reach_3_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    a- rainfall sum 0-24 hrs
    b- rainfall sum 24-48 hr
    d- Days since last rain

    Logistic model: 0.267*a + 0.1681*b - 0.02855*d + 0.5157

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

    df['probability'] = sigmoid(
        0.5157
        + 0.267 * df['rain_0_to_24h_sum']
        + 0.1681 * df['rain_24_to_48h_sum']
        - 0.02855 * df['days_since_sig_rain']
    )

    df['safe'] = df['probability'] <= SAFETY_THRESHOLD
    df['reach_id'] = 3

    return df[['reach_id', 'time', 'probability', 'safe']]


def reach_4_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    a- rainfall sum 0-24 hrs
    b- rainfall sum 24-48 hr
    d- Days since last rain
    f- PAR avg 24 hr
    Logistic model: 0.30276*a + 0.1611*b - 0.02267*d - 0.000427*f + 0.5791

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

    df['probability'] = sigmoid(
        0.5791
        + 0.30276 * df['rain_0_to_24h_sum']
        + 0.1611 * df['rain_24_to_48h_sum']
        - 0.02267 * df['days_since_sig_rain']
        - 0.000427 * df['par_1d_mean']
    )

    df['safe'] = df['probability'] <= SAFETY_THRESHOLD
    df['reach_id'] = 4

    return df[['reach_id', 'time', 'probability', 'safe']]


def reach_5_model(df: pd.DataFrame, rows: int = None) -> pd.DataFrame:
    """
    c- rainfall sum 0-48 hr
    d- Days since last rain
    e- Flow avg 0-24 hr
    Logistic model: 0.1091*c - 0.01355*d + 0.000342*e + 0.3333

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

    df['probability'] = sigmoid(
        0.3333
        + 0.1091 * df['rain_0_to_48h_sum']
        - 0.01355 * df['days_since_sig_rain']
        + 0.000342 * df['stream_flow_1d_mean']
    )

    df['safe'] = df['probability'] <= SAFETY_THRESHOLD
    df['reach_id'] = 5

    return df[['reach_id', 'time', 'probability', 'safe']]


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

    # TODO:
    #  I'm a little worried that I had to add the below to make a test pass.
    #  I thought this part of the code was pretty settled by now, but guess
    #  not. I need to look into what's going on.

    out = out.loc[out['probability'].notna(), :]
    return out
