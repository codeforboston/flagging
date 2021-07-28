"""
This file handles connections to the USGS API to retrieve data from the Waltham
gauge.

Link to the web interface (not the api)
https://waterdata.usgs.gov/nwis/uv?site_no=01104500
"""
import os
from typing import Union

import pandas as pd
import requests
from flask import abort
from flask import current_app
from tenacity import retry
from tenacity import wait_fixed
from tenacity import stop_after_attempt

from .database import celery_app

# Constants
USGS_URL = 'https://waterdata.usgs.gov/nwis/uv'

USGS_STATIC_FILE_NAME = 'usgs.pickle'
# ~ ~ ~ ~


@celery_app.task
def live_usgs_data_task(days_ago: int = 14) -> dict:
    return get_live_usgs_data(days_ago=days_ago).to_dict(orient='records')


@retry(reraise=True, wait=wait_fixed(1), stop=stop_after_attempt(3))
def get_live_usgs_data(days_ago: int = 14) -> pd.DataFrame:
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


def request_to_usgs(days_ago: int = 14) -> requests.models.Response:
    """Get a request from the USGS.

    Args:
        days_ago: (int) Number of days of data to get.

    Returns:
        Request Response containing the data from the request.
    """

    payload = {
        'cb_00060': 'on',
        'cb_00065': 'on',
        'format': 'rdb',
        'site_no': '01104500',
        'period': days_ago
    }

    res = requests.get(USGS_URL, params=payload)
    if res.status_code >= 400:
        error_msg = 'API request to the USGS endpoint failed with status ' \
                    f'code {res.status_code}.'
        abort(res.status_code, error_msg)
    return res


def parse_usgs_data(
        res: Union[str, requests.models.Response]
) -> pd.DataFrame:
    """
    Clean the response from the USGS API.

    Args:
        res: response object from USGS

    Returns:
        Pandas DataFrame containing the usgs data.
    """
    if isinstance(res, requests.models.Response):
        res = res.text

    raw_data = [
        i.split('\t')
        for i in res.split('\n')
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
    # Note to self: ran this once in a test and it gave the following error:
    # >>> ValueError: could not convert string to float: ''
    # Reran and it went away
    # The error was here in this line casting `stream_flow` to a float:
    df['stream_flow'] = df['stream_flow'].astype(float)
    df['gage_height'] = df['gage_height'].astype(float)

    return df
