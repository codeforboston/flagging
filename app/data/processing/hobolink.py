"""
This file handles connections to the HOBOlink API, including cleaning and
formatting of the data that we receive from it.
"""
import io
from typing import Union

import pandas as pd
import requests
from flask import abort
from flask import current_app
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from app.data.processing.utils import mock_source
from app.mail import mail_on_fail


# Constants

HOBOLINK_URL = 'http://webservice.hobolink.com/restv2/data/custom/file'
HOBOLINK_DEFAULT_EXPORT_NAME = 'code_for_boston_export_21d'
HOBOLINK_ROWS_PER_HOUR = 6
# Each key is the original column name; the value is the renamed column.
HOBOLINK_COLUMNS = {
    'Time, GMT-': 'time',
    'Pressure': 'pressure',
    'PAR': 'par',
    'Rain': 'rain',
    'RH': 'rh',
    'DewPt': 'dew_point',
    'Wind Speed': 'wind_speed',
    'Gust Speed': 'gust_speed',
    'Wind Dir': 'wind_dir',
    # 'Water Temp': 'water_temp',
    'Temp': 'air_temp',
    # 'Batt, V, Charles River Weather Station': 'battery'
}
HOBOLINK_STATIC_FILE_NAME = 'hobolink.pickle'


@retry(reraise=True, wait=wait_fixed(1), stop=stop_after_attempt(3))
@mock_source(filename=HOBOLINK_STATIC_FILE_NAME)
@mail_on_fail
def get_live_hobolink_data(
        export_name: str = HOBOLINK_DEFAULT_EXPORT_NAME
) -> pd.DataFrame:
    """This function runs through the whole process for retrieving data from
    HOBOlink: first we perform the request, and then we clean the data.

    Args:
        export_name: (str) Name of the "export." On the Hobolink web dashboard,
                     go to Data > Exports and choose a name off the list.

    Returns:
        Pandas Dataframe containing the cleaned-up Hobolink data.
    """
    res = request_to_hobolink(export_name=export_name)
    df = parse_hobolink_data(res.text)
    return df


def request_to_hobolink(
        export_name: str = HOBOLINK_DEFAULT_EXPORT_NAME,
) -> requests.models.Response:
    """
    Get a request from the Hobolink server.

    Args:
        export_name: (str) Name of the "export." On the Hobolink web dashboard,
                     go to Data > Exports and choose a name off the list.

    Returns:
        Request Response containing the data from the request.
    """
    data = {
        'query': export_name,
        'authentication': current_app.config['HOBOLINK_AUTH']
    }

    res = requests.post(HOBOLINK_URL, json=data)

    # handle HOBOLINK errors by checking HTTP status code
    # status codes in 400's are client errors, in 500's are server errors
    if res.status_code >= 400:
        error_msg = 'API request to the HOBOlink endpoint failed with status ' \
                    f'code {res.status_code}.'
        abort(res.status_code, error_msg)

    return res


def parse_hobolink_data(
        res: Union[str, requests.models.Response]
) -> pd.DataFrame:
    """
    Clean the response from the HOBOlink API.

    Args:
        res: (str) A string of the text received from the post request to the
             HOBOlink API from a successful request.
    Returns:
        Pandas DataFrame containing the HOBOlink data.
    """
    if isinstance(res, requests.models.Response):
        res = res.text

    # The first half of the text from the response is a yaml. The part below
    # the yaml is the actual data. The following lines split the text and grab
    # the csv:
    split_by = '------------'
    str_table = res[res.find(split_by) + len(split_by):]

    # Turn the text from the API response into a Pandas DataFrame.
    df = pd.read_csv(io.StringIO(str_table), sep=',')

    # There is a weird issue in the HOBOlink data where it sometimes returns
    # multiple columns with the same name and spreads real data out across
    # those two columns. It is VERY weird. I promise this code used to be much
    # simpler before we ran into this issue and it broke the website. Please
    # trust us that it does have to be this complicated.
    for old_col_startswith, new_col in HOBOLINK_COLUMNS.items():

        # Only look at rows that start with `old_col_startswith`
        subset_df = df.loc[
            :,
            filter(lambda x: x.startswith(old_col_startswith), df.columns)
        ]

        # Remove rows with missing data (i.e. the 05, 15, 25, 35, 45, and 55 min
        # timestamps, which only include the battery status.)
        subset_df = subset_df.loc[~subset_df.isna().all(axis=1)]

        # Take the first nonmissing column value within the subset of rows we've
        # selected. This trick is similar to doing a COALESCE in sql.
        df[new_col] = subset_df \
            .apply(lambda x: x[x.first_valid_index()], axis=1)

    # Only keep these columns
    df = df[HOBOLINK_COLUMNS.values()]

    # Remove the rows with all missing values again.
    df = df.loc[df['air_temp'].notna()]

    # Convert time column to Pandas datetime
    df['time'] = pd.to_datetime(df['time'], format='%m/%d/%y %H:%M:%S')

    return df.reset_index(drop=True)
