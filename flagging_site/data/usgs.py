"""
This file handles connections to the USGS API to retrieve data from the Waltham
gauge.

Link  to the web interface (not the api) 
https://waterdata.usgs.gov/nwis/uv?site_no=01104500
"""
import pandas as pd
import requests
import numpy as np

# Constants
USGS_URL = 'https://waterservices.usgs.gov/nwis/iv/'
USGS_COLUMNS = ['Timestamp', 'Discharge Volume', 'Gage height']

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
    
    payload = {
        'format': 'json',
        'sites': '01104500',
        'period': 'P7D',
        'parameterCd': '00060,00065',
        'siteStatus': 'all'
    }
    
    res = requests.get(USGS_URL, params=payload)
    return res

def parse_usgs_data(res) -> pd.DataFrame:
    """
    Clean the response from the USGS API.

    Args:
        res: response object from USGS

    Returns:
        Pandas DataFrame containing the usgs data.
    """

    raw_data = res.json()

    df = pd.DataFrame.from_dict(raw_data)

    discharge_volume = raw_data['value']['timeSeries'][0]['values'][0]['value']
    gage_height = raw_data['value']['timeSeries'][1]['values'][0]['value']

    data_list = [
        [vol_entry['dateTime'], vol_entry['value'], height_entry['value']] 
        for [vol_entry, height_entry] in zip (discharge_volume, gage_height)
    ]

    data_2d_array = np.array(data_list)
    
    df = pd.DataFrame(data_2d_array, columns = USGS_COLUMNS)

    return df