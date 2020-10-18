"""
This file handles connections to the USGS API to retrieve data from the Waltham
gauge.

Link  to the web interface (not the api) 
https://waterdata.usgs.gov/nwis/uv?site_no=01104500
"""
import os
import pandas as pd
import requests
from flask import abort
from flask import current_app

# Constants
USGS_URL = 'https://waterdata.usgs.gov/nwis/uv'

USGS_STATIC_FILE_NAME = 'usgs.pickle'
# ~ ~ ~ ~


def get_live_usgs_data(days_ago: int = 5) -> pd.DataFrame:
    """This function runs through the whole process for retrieving data from
    usgs: first we perform the request, and then we parse the data.

    Returns:
        Pandas Dataframe containing the usgs data.
    """
    if current_app.config['USE_MOCK_DATA']:
        fpath = os.path.join(
            current_app.config['DATA_STORE'], USGS_STATIC_FILE_NAME
        )
        df = pd.read_pickle(fpath)
    else:
        res = request_to_usgs(days_ago=days_ago)
        df = parse_usgs_data(res)
    return df


def request_to_usgs(days_ago: int = 5) -> requests.models.Response:
    """Get a request from the USGS.



    Returns:
        Request Response containing the data from the request.
    """

    todays_date = pd.Timestamp('today').date()
    prior_date = todays_date - pd.Timedelta(f'{days_ago} days')

    payload = {
        'cb_00060': 'on',
        'cb_00065': 'on',
        'format': 'rdb',
        'site_no': '01104500',
        'period': {
            'begin_date': str(todays_date),
            'end_date': str(prior_date)
        }
    }

    res = requests.get(USGS_URL, params=payload)
    if res.status_code // 100 in [4, 5]:
        error_msg = 'API request to the USGS endpoint failed with status code '\
                    + str(res.status_code)
        abort(res.status_code, error_msg)
    return res


def parse_usgs_data(res) -> pd.DataFrame:
    """
    Clean the response from the USGS API.

    Args:
        res: response object from USGS

    Returns:
        Pandas DataFrame containing the usgs data.
    """

    raw_data = [
        i.split('\t')
        for i in res.text.split('\n')
        if not i.startswith('#') and i != ''
    ]

    # First row is column headers
    # Second row is ????
    # Third row downward is the data
    df = pd.DataFrame(raw_data[2:], columns=raw_data[0])

    df = df.rename(columns={
        'datetime': 'time',
        '66190_00060': 'stream_flow',
        '66191_00065': 'gage_height'
    })

    # Filter columns
    df = df[['time', 'stream_flow', 'gage_height']]

    # Convert types
    df['time'] = pd.to_datetime(df['time'])
    df['stream_flow'] = df['stream_flow'].astype(float)
    df['gage_height'] = df['gage_height'].astype(float)

    return df
