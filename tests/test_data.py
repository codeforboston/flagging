from flagging_site.data.hobolink import get_hobolink_data
from flagging_site.data.usgs import get_usgs_data
import pandas as pd


def test_hobolink_data_is_recent(app):
    with app.app_context():
        df = get_hobolink_data()
        last_timestamp = df['time'].iloc[-1]
        time_difference = (pd.to_datetime('today') - last_timestamp)
        assert time_difference < pd.Timedelta(hours=1)


def test_usgs_data_is_recent(app):
    with app.app_context():
        df = get_usgs_data()
        last_timestamp = df['time'].iloc[-1]
        time_difference = (pd.to_datetime('today') - last_timestamp)
        assert time_difference < pd.Timedelta(hours=1)
