"""
This file contains all the logic for modeling. The model takes data from the SQL
backend, do some calculations on that data, and then output model results.


Variables:

a) rainfall sum 0-24 hrs
b)rainfall sum 24-48 hr
c)rainfall sum 0-48 hr
d)Days since last rain
e)Flow avg 0-24 hr
f)PAR avg 24 hr


Equations:

Reach 2:    0.3531*a  -  0.0362*d  -  0.000312*f  + 0.6233
Reach 3:    0.267*a + 0.1681*b - 0.02855*d  + 0.5157
Reach 4:    0.30276*a + 0.1611*b - 0.02267*d - 0.000427*f  +0.5791
Reach 5:    0.1091*c  -  0.01355*d + 0.000342*e  +0.3333

These output model numbers such that EXP(model) / (1+EXP(model)) yields percent
probability of flag and =<65% is a flag. EXP means raise e to the power of model
number.


Useful links:

- Hobolink documentation:
https://www.metrics24.de/WebRoot/Store5/Shops/62187045/5D79/1FE4/31E4/0996/0440/0A0C/6D0B/7D8C/HOBOlink-Users-Guide.pdf

- Regulatory standards in MA:
https://www.mass.gov/files/documents/2016/08/tz/36wqara.pdf

TODO: Fill the model parameters from the `ManualModel_Hourly.xlsx` spreadsheet.

TODO:
 make sure that hobolink is taking the hourly rate of rainfall at every 10 min
 increment, otherwise their aggregation of rainfall doesn't make sense. If it
 is the case that hobolink is taking 10 minute rainfall, then that leads to
 another challenge, however, which is confirming that CRWA trained their model
 on the 'incorrect' increments. If they did, then we cannot touch their
 aggregation because them model parameters will reflect their particular
 aggregation.
"""
import numpy as np
import pandas as pd

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

    # They take the measurement at each hour, and drop the rest.
    # TODO:
    #  Ask CRWA if the intent was to take the average per hour, or the
    #  value at each hour. Their spreadsheet takes the value at each hour, and
    #  discards all data at :10, :20, :30, :40, and :50. We just want to make
    #  sure that is their intent.
    df_hobolink = df_hobolink.loc[df_hobolink['time'].dt.minute == 0, :]
    df_usgs = df_usgs.loc[df_usgs['time'].dt.minute == 0, :]
    df = df_hobolink.merge(right=df_usgs, how='outer', on='time')

    # Next, they do the following:
    #
    # 1 day avg of:
    #   - wind_speed
    #   - water_temp
    #   - air_temp
    #   - stream_flow (via USGS)
    # 2 day avg of:
    #   - par
    #   - stream_flow (via USGS)
    # sum of rain at following increments:
    #   - 1 day
    #   - 2 day
    #   - 7 day
    for col in ['par', 'stream_flow']:
        df[f'{col}_1d_mean'] = df[col].rolling(24).mean()

    for incr in [24, 48]:
        df[f'rain_0_to_{str(incr)}h_sum'] = df['rain'].rolling(incr).sum()
    df[f'rain_24_to_48h_sum'] = (
        df[f'rain_0_to_48h_sum'] - df[f'rain_0_to_24h_sum']
    )

    # Lastly, they measure the "time since last significant rain." Significant
    # rain is defined as a cumulative sum of 0.2 in over a 24 hour time period.
    df['sig_rain'] = df['rain_0_to_24h_sum'] >= SIGNIFICANT_RAIN
    df['last_sig_rain'] = (
        df['time']
        .where(df['sig_rain'])
        .shift()
        .ffill()
        .fillna(df['time'].min())
    )
    df['days_since_sig_rain'] = (
        (df['time'] - df['last_sig_rain']).dt.seconds / 60 / 60 / 24
    )

    return df


def reach_2_model(df: pd.DataFrame) -> pd.DataFrame:
    """Model params:
    a- rainfall sum 0-24 hrs
    d- Days since last rain
    f- PAR avg 24 hr
    0.3531*a  -  0.0362*d  -  0.000312*f  + 0.6233

    Args:
        df: Input data from `process_data()`

    Returns:
        Outputs for model as a dataframe.
    """
    df = df.copy()
    df['r2_out'] = (
        0.6233
        + 0.3531 * df['rain_0_to_24h_sum']
        - 0.0362 * df['days_since_sig_rain']
        - 0.000312 * df['par_1d_mean']
    )
    df['r2_sigmoid'] = sigmoid(df['r2_out'])
    df['r2_safe'] = df['r2_sigmoid'] <= SAFETY_THRESHOLD
    return (
        # df[['time', 'r2_out', 'r2_sigmoid', 'r2_safe']]
        df[['r2_safe']]
        # .tail(n=24)
        .tail(n=1)
    )


def reach_3_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    a- rainfall sum 0-24 hrs
    b- rainfall sum 24-48 hr
    d- Days since last rain
    0.267*a + 0.1681*b - 0.02855*d  + 0.5157

    Args:
        df: Input data from `process_data()`

    Returns:
        Outputs for model as a dataframe.
    """
    df = df.copy()
    df['r3_out'] = (
        0.5157
        + 0.267 * df['rain_0_to_24h_sum']
        + 0.1681 * df['rain_24_to_48h_sum']
        - 0.02855 * df['days_since_sig_rain']
    )
    df['r3_sigmoid'] = sigmoid(df['r3_out'])
    df['r3_safe'] = df['r3_sigmoid'] <= SAFETY_THRESHOLD
    return (
        # df[['time', 'r3_out', 'r3_sigmoid', 'r3_safe']]
        df[['r3_safe']]
        .tail(n=1)
        # .tail(n=24)
    )


def reach_4_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    a- rainfall sum 0-24 hrs
    b- rainfall sum 24-48 hr
    d- Days since last rain
    f- PAR avg 24 hr
    0.30276*a + 0.1611*b - 0.02267*d - 0.000427*f  +0.5791

    Args:
        df: Input data from `process_data()`

    Returns:
        Outputs for model as a dataframe.
    """
    df = df.copy()
    df['r4_out'] = (
        0.5791
        + 0.30276 * df['rain_0_to_24h_sum']
        + 0.1611 * df['rain_24_to_48h_sum']
        - 0.02267 * df['days_since_sig_rain']
        - 0.000427 * df['par_1d_mean']
    )
    df['r4_sigmoid'] = sigmoid(df['r4_out'])
    df['r4_safe'] = df['r4_sigmoid'] <= SAFETY_THRESHOLD
    return (
        # df[['time', 'r4_out', 'r4_sigmoid', 'r4_safe']]
        df[['r4_safe']]
        .tail(n=1)
        # .tail(n=24)
    )


def reach_5_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    c- rainfall sum 0-48 hr
    d- Days since last rain
    e- Flow avg 0-24 hr
    0.1091*c  -  0.01355*d + 0.000342*e  +0.3333

    Args:
        df: Input data from `process_data()`

    Returns:
        Outputs for model as a dataframe.
    """
    df = df.copy()
    df['r5_out'] = (
        0.3333
        + 0.1091 * df['rain_0_to_48h_sum']
        - 0.01355 * df['days_since_sig_rain']
        + 0.000342 * df['stream_flow_1d_mean']
    )
    df['r5_sigmoid'] = sigmoid(df['r5_out'])
    df['r5_safe'] = df['r5_sigmoid'] <= SAFETY_THRESHOLD
    return (
        # df[['time', 'r5_out', 'r5_sigmoid', 'r5_safe']]
        df[['r5_safe']]
        .tail(n=1)
        # .tail(n=24)
    )
