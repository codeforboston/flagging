"""
These are intended to be run from the Flask Shell.  They are not incorporated in the web app.

To run:
1. start docker
2. anaconda
3. fdb.bat
4. flask.bat
5. In Flask:
    from app.data.processing.fetch_calculate_and_output import fetch_and_output, consolidate
    begin_date = "2025-07-02"
    end_date = "2025-08-01"
    fetch_and_output(begin_date, end_date)
"""

import os
import re
from datetime import datetime

import pandas as pd
import requests

from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.predictive_models import v4
from app.data.processing.usgs import parse_usgs_data


dir_pattern_re = re.compile("^2025-[0-9][0-9]-[0-9][0-9]")


def fetch_and_output(begin_date: str, end_date: str) -> None:
    d_begin_date = datetime.strptime(begin_date, "%Y-%m-%d")
    d_end_date = datetime.strptime(end_date, "%Y-%m-%d")
    df_hobolink = get_live_hobolink_data(start_date=d_begin_date, end_date=d_end_date)
    res_w = requests.get(
        "https://waterservices.usgs.gov/nwis/iv/",
        params={
            "sites": "01104500",
            "parameterCd": "00060,00065",
            "startDT": begin_date,
            "endDT": end_date,
            "format": "rdb",
        },
    )

    res_b = requests.get(
        "https://waterservices.usgs.gov/nwis/iv/",
        params={
            "sites": "01104683",
            "parameterCd": "00065",
            "startDT": begin_date,
            "endDT": end_date,
            "format": "rdb",
        },
    )

    df_usgs_w = parse_usgs_data(res_w, site_no="01104500")
    df_usgs_b = parse_usgs_data(res_b, site_no="01104683")

    df_combined = v4.process_data(df_hobolink=df_hobolink, df_usgs_w=df_usgs_w, df_usgs_b=df_usgs_b)
    df_predictions = v4.all_models(df_combined)

    df_combined.to_csv(f"{begin_date} - {end_date}-combined.csv", index=False)
    df_predictions.to_csv(f"{begin_date} - {end_date}-predictions.csv", index=False)

    df_usgs_w.to_csv(f"{begin_date} - {end_date}-usgs_w.csv", index=False)
    df_usgs_b.to_csv(f"{begin_date} - {end_date}-usgs_b.csv", index=False)
    df_hobolink.to_csv(f"{begin_date} - {end_date}-hobolink.csv", index=False)
    return


def consolidate(category: str) -> None:
    dir_list = os.listdir(".")
    match_list = []
    for file in dir_list:
        if dir_pattern_re.search(file) and file.find(category.lower()) > -1:
            match_list.append(file)
    match_list.sort()
    first = True
    for file in match_list:
        df = pd.read_csv(file)
        if first:
            first = False
            consol_df = df
        else:
            consol_df = pd.concat([consol_df, df])
    subset_cols = ["reach_id", "time"] if category.lower().startswith("pred") else ["time"]
    consol_df = consol_df.drop_duplicates(subset=subset_cols)
    consol_df.to_csv(match_list[0][:10] + " - " + match_list[-1][13:] + ".csv", index=False)
    print(consol_df.shape)
    return
