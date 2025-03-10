"""
This file handles connections to the USGS API to retrieve data from the Waltham
and Muddy River gauge.

Link to the web interface (not the api)
Waltham: https://waterdata.usgs.gov/nwis/uv?site_no=01104500
Muddy River: https://waterdata.usgs.gov/nwis/uv?site_no=01104683
"""

from typing import Union

import pandas as pd
import requests
from flask import abort
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from app.data.processing.utils import mock_source
from app.mail import mail_on_fail


USGS_URL = "https://waterdata.usgs.gov/nwis/uv"
USGS_STATIC_FILE_NAME = "usgs.pickle"
USGS_DEFAULT_DAYS_AGO = 14
USGS_ROWS_PER_HOUR_WALTHAM = 4
USGS_ROWS_PER_HOUR_MUDDY_RIVER = 6


@retry(reraise=True, wait=wait_fixed(1), stop=stop_after_attempt(3))
@mock_source(filename=USGS_STATIC_FILE_NAME)
@mail_on_fail
def get_live_usgs_data(
    days_ago: int = USGS_DEFAULT_DAYS_AGO, site_no: str = "01104500"
) -> pd.DataFrame:
    """This function runs through the whole process for retrieving data from
    usgs: first we perform the request, and then we parse the data.

    Returns:
        Pandas Dataframe containing the usgs data.
    """
    res = request_to_usgs(days_ago=days_ago, site_no=site_no)
    df = parse_usgs_data(res, site_no=site_no)
    return df


def request_to_usgs(days_ago: int = 14, site_no: str = "01104500") -> requests.models.Response:
    """Get a request from the USGS.

    Args:
        days_ago: (int) Number of days of data to get.
        site_no: (str) String of integer site number, either Waltham or Muddy River sites.

    Returns:
        Request Response containing the data from the request.
    """
    # if site is waltham, takes both gage height and flow discharge,
    # otherwise, only takes gage height
    if site_no == "01104500":
        additional_feature = "on"
    else:
        additional_feature = "off"

    payload = {
        "cb_00060": additional_feature,
        "cb_00065": "on",  # always accepts gage height
        "format": "rdb",
        "site_no": site_no,
        "period": days_ago,
    }

    res = requests.get(USGS_URL, params=payload)
    if res.status_code >= 400:
        error_msg = (
            "API request to the USGS endpoint failed with status " f"code {res.status_code}."
        )
        abort(500, error_msg)
    return res


def parse_usgs_data(res: Union[str, requests.models.Response], site_no: str) -> pd.DataFrame:
    """
    Clean the response from the USGS API.

    Args:
        res: response object from USGS
        site_no: site_no of usgs data currently being parsed

    Returns:
        Pandas DataFrame containing the usgs data.
    """
    if isinstance(res, requests.models.Response):
        res = res.text

    raw_data = [i.split("\t") for i in res.split("\n") if not i.startswith("#") and i != ""]

    # First row is column headers
    # Second row is ????
    # Third row downward is the data
    df = pd.DataFrame(raw_data[2:], columns=raw_data[0])

    column_map = {
        "01104500": {
            "datetime": "time",
            "66190_00060": "stream_flow",
            "66191_00065": "gage_height",
        },
        "01104683": {"datetime": "time", "66196_00065": "gage_height"},
    }
    if site_no not in column_map:
        raise ValueError(f"Unknown site number {site_no}. Cannot map columns.")
    df = df.rename(columns=column_map[site_no])

    df = df[list(column_map[site_no].values())]

    # Convert types
    df["time"] = pd.to_datetime(df["time"])
    # Note to self: ran this once in a test and it gave the following error:
    # >>> ValueError: could not convert string to float: ''
    # Reran and it went away
    # The error was here in this line casting `stream_flow` to a float:

    numeric_columns = set(column_map[site_no].values()) - {"time"}  # All columns except "time"
    for col in numeric_columns:
        df[col] = df[col].replace("", None).astype(float)
    return df
