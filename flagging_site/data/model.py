"""
This file contains all the logic for modeling. The model takes data from the SQL
backend, do some calculations on that data, and then output model results.

The model should be an emulation of the model in their spreadsheet called
`ManualModel_Hourly.xlsx`.

In the future, we also may want to store the model's coefficients in a yaml
file, and then load those coefficients so that CRWA can fit the model on new
data whenever they want and simply update a plain text file without having to
touch the code, but that's a bit of a longer term goal.

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


def process_data(df: pd.DataFrame):
    df = df.copy()

    df['stream_flow'] = 200  # TODO: make into real data
    df['water_temp'] = 38  # TODO: ask CRWA to plug in the temp reader

    # They take the measurement at each hour, and drop the rest.
    # TODO:
    #  Ask CRWA if the intent was to take the average per hour, or the
    #  value at each hour. Their spreadsheet takes the value at each hour, and
    #  discards all data at :10, :20, :30, :40, and :50. We just want to make
    #  sure that is their intent.
    df = df.loc[df['time'].dt.minute == 0, :]

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
    for col in ['wind_speed', 'water_temp', 'air_temp', 'stream_flow']:
        df[f'{col}_1d_mean'] = df[col].rolling(24).mean()

    for col in ['stream_flow', 'par']:
        df[f'{col}_2d_mean'] = df[col].rolling(48).mean()

    for incr in [1, 2, 7]:
        df[f'rain_{str(incr)}d_sum'] = df['rain'].rolling(24 * incr).sum()

    # Lastly, they measure the "time since last significant rain." Significant
    # rain is defined as a cumulative sum of 0.2 in over a 24 hour time period.
    df['sig_rain'] = df['rain_1d_sum'] >= SIGNIFICANT_RAIN
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
    df = df.copy()
    df['r2_out'] = (
        0.2629
        + 0.0444 * (df['water_temp_1d_mean'] * 9/5 + 32)
        - 0.0364 * (df['air_temp_1d_mean'] * 9/5 + 32)
        + 0.0014 * (24 * df['days_since_sig_rain'])
        - 0.226 * np.log(24 * df['days_since_sig_rain'] + 0.0001)
    )
    df['r2_sigmoid'] = sigmoid(df['r2_out'])
    df['r2_safe'] = df['r2_sigmoid'] < SAFETY_THRESHOLD
    return (
        df[['time', 'r2_out', 'r2_sigmoid', 'r2_safe']]
        .tail(n=24)
    )


def reach_3_model(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['r3_out'] = (
        1.4144
        + 0.0255 * (df['water_temp_1d_mean'] * 9/5 + 32)
        - 0.0007 * df['par_2d_mean']
        + 0.0009 * (24 * df['days_since_sig_rain'])
        - 0.3022 * np.log(24 * df['days_since_sig_rain'] + 0.0001)
        + 0.0015 * df['stream_flow_2d_mean']
        - 0.3957 * np.log(df['stream_flow_2d_mean'])
    )
    df['r3_sigmoid'] = sigmoid(df['r3_out'])
    df['r3_safe'] = df['r3_sigmoid'] < SAFETY_THRESHOLD
    return (
        df[['time', 'r3_out', 'r3_sigmoid', 'r3_safe']]
        .tail(n=24)
    )


def reach_4_model(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['r4_out'] = (
        3.6513
        + 0.0254 * (df['water_temp_1d_mean'] * 9/5 + 32)
        - 0.6636 * np.log(df['par_2d_mean'])
        - 0.0014 * (24 * df['days_since_sig_rain'])
        - 0.3428 * np.log(24 * df['days_since_sig_rain'] + 0.0001)
    )
    df['r4_sigmoid'] = sigmoid(df['r4_out'])
    df['r4_safe'] = df['r4_sigmoid'] < SAFETY_THRESHOLD
    return (
        df[['time', 'r4_out', 'r4_sigmoid', 'r4_safe']]
        .tail(n=24)
    )

def reach_5_model(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['r5_lg'] = (
        - 3.184
        + 3.936 * df['rain_2d_sum']
        - 1.62 * df['rain_7d_sum']
        + 1.2798 * np.log(df['stream_flow_1d_mean'])
        - 0.3397 * df['wind_speed_1d_mean']
        - 0.2112 * df['water_temp_1d_mean']
    )
    df['r5_conc_lf'] = np.exp(
        2.7144
        + 0.65 * np.log(df['stream_flow_1d_mean'])
        + 1.68 * df['rain_2d_sum']
        - 0.071 * df['water_temp_1d_mean']
        - 0.29 * df['rain_7d_sum']
        - 0.09 * df['wind_speed_1d_mean']
    )
    df['r5_sigmoid'] = sigmoid(df['r5_lg'])
    df['r5_safe'] = (df['r5_sigmoid'] < 0.6) & (df['r5_conc_lf'] < 630)
    return (
        df[['time', 'r5_lg', 'r5_sigmoid', 'r5_conc_lf', 'r5_safe']]
        .tail(n=24)
    )
