"""
This file handles connections to the USGS API to retrieve data from the Waltham
gauge.

https://waterdata.usgs.gov/nwis/uv?site_no=01104500
"""
import pandas as pd
import requests
import io

# Constants
USGS_URL = 'https://waterdata.usgs.gov/nwis/uv?site_no=01104500'
# Each key is the original column name; the value is the renamed column.

# ~ ~ ~ ~

def get_usgs_data() -> pd.DataFrame:
    """This function  runs through the whole process for retrieving data from
    usgs: first we perform the request, and then we clean the data.

    Returns:
        Pandas Dataframe containing the usgs data.
    """
    res = request_to_usgs()
    df = parse_usgs_data(res)
    return df


def request_to_usgs(
) -> requests.models.Response:
    """
    Get a request from the USGS.

    Returns:
        Request Response containing the data from the request.
    """
    
    res = requests.get('https://waterservices.usgs.gov/nwis/iv/?format=json&sites=01104500&period=P7D&parameterCd=00060,00065&siteStatus=all')

    return res

def parse_usgs_data(res) -> pd.DataFrame:
    """
    Clean the response from the HOBOlink API.

    Args:
        res: response object from USGS

    Returns:
        Pandas DataFrame containing the usgs data.
    """

    json = res.json()
    time_list = []
    volume_list = []
    height_list = []

    for time_data in json['value']['timeSeries'][0]['values'][0]['value']:
        time_list.append(time_data['dateTime'])

    for vol_data in json['value']['timeSeries'][0]['values'][0]['value']:
        volume_list.append(vol_data['value'])

    for height_data in json['value']['timeSeries'][1]['values'][0]['value']:
        height_list.append(height_data['value'])

    df = pd.DataFrame(list(zip(time_list, volume_list, height_list)),
        columns =['Time', 'Discharge Volume', 'Gage height'])

    return df
