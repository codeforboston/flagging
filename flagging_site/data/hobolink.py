"""
This file handles connections to the HOBOlink API, including cleaning and
formatting of the data that we receive from it.
"""
# TODO:
#  Pandas is inefficient. It should go to SQL, not to Pandas. I am currently
#  using pandas because we do not have any cron jobs or any caching or SQL, but
#  I think in future versions we should not be using Pandas at all.
import io
import requests
import pandas as pd
from flask import abort
from .keys import get_keys
from .keys import offline_mode
from .keys import get_data_store_file_path

# Constants

HOBOLINK_URL = 'http://webservice.hobolink.com/restv2/data/custom/file'
EXPORT_NAME = 'code_for_boston_export'
# Each key is the original column name; the value is the renamed column.
HOBOLINK_COLUMNS = {
    'Time, GMT-04:00': 'time',
    'Pressure': 'pressure',
    'PAR': 'par',
    'Rain': 'rain',
    'RH': 'rh',
    'DewPt': 'dew_point',
    'Wind Speed': 'wind_speed',
    'Gust Speed': 'gust_speed',
    'Wind Dir': 'wind_dir',
    'Water Temp': 'water_temp',
    'Temp': 'air_temp',
    # 'Batt, V, Charles River Weather Station': 'battery'
}
STATIC_FILE_NAME = 'hobolink.pickle'
# ~ ~ ~ ~


def get_live_hobolink_data(export_name: str = EXPORT_NAME) -> pd.DataFrame:
    """This function runs through the whole process for retrieving data from
    HOBOlink: first we perform the request, and then we clean the data.

    Args:
        export_name: (str) Name of the "export." On the Hobolink web dashboard,
                     go to Data > Exports and choose a name off the list.

    Returns:
        Pandas Dataframe containing the cleaned-up Hobolink data.
    """
    if offline_mode():
        df = pd.read_pickle(get_data_store_file_path(STATIC_FILE_NAME))
    else:
        res = request_to_hobolink(export_name=export_name)
        df = parse_hobolink_data(res.text)
    return df


def request_to_hobolink(
        export_name: str = EXPORT_NAME,
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
        'authentication': get_keys()['hobolink']
    }

    res = requests.post(HOBOLINK_URL, json=data)
    # handle HOBOLINK errors by checking HTTP status code
    # status codes in 400's are client errors, in 500's are server errors
    if res.status_code // 100 in [4, 5]:
        error_message = "link has failed with error # " + str(res.status_code)
        return abort(res.status_code, error_message)
    return res


def parse_hobolink_data(res: str) -> pd.DataFrame:
    """
    Clean the response from the HOBOlink API.

    Args:
        res: (str) A string of the text received from the post request to the
             HOBOlink API from a successful request.
    Returns:
        Pandas DataFrame containing the HOBOlink data.
    """
    # TODO:
    #  The first half of the output is a yaml-formatted text stream. Is there
    #  anything useful in it? Can we store it and make use of it somehow?
    if isinstance(res, requests.models.Response):
        res = res.text

    # Turn the text from the API response into a Pandas DataFrame.
    split_by = '------------'
    str_table = res[res.find(split_by) + len(split_by):]
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
    df = df.loc[df['water_temp'].notna()]

    # Convert time column to Pandas datetime
    df['time'] = pd.to_datetime(df['time'])

    return df
