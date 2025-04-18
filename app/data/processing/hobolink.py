import os
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests
from flask import abort
from flask import current_app
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from app.mail import mail_on_fail


BASE_URL = "https://api.hobolink.licor.cloud"
HOBOLINK_ROWS_PER_HOUR = 12
HOBOLINK_STATIC_FILE_NAME = ""


"/v1/data"


@retry(reraise=True, wait=wait_fixed(1), stop=stop_after_attempt(3))
@mail_on_fail
def get_live_hobolink_data(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    days_ago: int = 30,
    loggers: str | None = None,
    exclude_sensors: list[str] | None = None,
) -> pd.DataFrame:
    """This function runs through the whole process for retrieving data from
    HOBOlink: first we perform the request, and then we clean the data.

    Returns:
        Pandas Dataframe containing the cleaned-up Hobolink data.
    """
    if current_app.config["USE_MOCK_DATA"]:
        fpath = os.path.join(current_app.config["DATA_STORE"], "hobolink.pickle")
        df = pd.read_pickle(fpath)
        return df

    if end_date is None:
        end_date = datetime.now(tz=UTC)
    if start_date is None:
        start_date = end_date - timedelta(days=days_ago)
    res = request_to_hobolink(start_date=start_date, end_date=end_date, loggers=loggers)
    df = parse_hobolink_data(res.json(), exclude_sensors=exclude_sensors)
    return df


def request_to_hobolink(
    start_date: datetime, end_date: datetime, loggers: str = None, token: str | None = None
) -> requests.models.Response:
    """ """
    if loggers is None:
        loggers = current_app.config["HOBOLINK_LOGGERS"]
    if token is None:
        token = current_app.config["HOBOLINK_BEARER_TOKEN"]

    res = requests.get(
        urljoin(BASE_URL, "/v1/data"),
        params={
            "start_date_time": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date_time": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "loggers": loggers,
        },
        headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
    )

    if res.status_code >= 400:
        error_msg = (
            f"API request to the HOBOlink endpoint failed with status code {res.status_code}:"
            + res.text
        )
        abort(500, error_msg)

    return res


def parse_hobolink_data(
    data: dict[str, Any], exclude_sensors: list[str] | None = None
) -> pd.DataFrame:
    """
    Clean the response from the HOBOlink API.

    Args:
        res: (str) A string of the text received from the post request to the
             HOBOlink API from a successful request.
    Returns:
        Pandas DataFrame containing the HOBOlink data.
    """
    if not exclude_sensors:
        # This sensor is for internal temp of device.
        exclude_sensors = current_app.config["HOBOLINK_EXCLUDE_SENSORS"]

    df = pd.DataFrame(data["data"])
    df = df.loc[~df["sensor_sn"].isin(exclude_sensors), :]
    df["time"] = pd.to_datetime(df["timestamp"])
    df["sensor_measurement_type"] = df["sensor_measurement_type"].str.lower().str.replace(" ", "_")

    df = df.pivot(index="time", columns="sensor_measurement_type", values="value")
    df = df.reset_index()

    return df
