import io
import pandas as pd
import pickle

from flagging_site.data import hobolink
from flagging_site.data.hobolink import get_live_hobolink_data
from flagging_site.data.usgs import get_live_usgs_data


def test_hobolink_data_is_recent(app):
    with app.app_context():
        df = get_live_hobolink_data()
        last_timestamp = df['time'].iloc[-1]
        time_difference = (pd.to_datetime('today') - last_timestamp)
        assert time_difference < pd.Timedelta(hours=1)


def test_usgs_data_is_recent(app):
    with app.app_context():
        df = get_live_usgs_data()
        last_timestamp = df['time'].iloc[-1]
        time_difference = (pd.to_datetime('today') - last_timestamp)
        assert time_difference < pd.Timedelta(hours=1)


def test_hobolink_handles_erroneous_csv(app, monkeypatch):
    """
    Tests that the code supports when Hobolink erroneously returns
    a CSV where some column headers are repeated and only one contains
    the actual data.
    """
    with io.open('tests/static/split_columns_hobolink_export.pickle', 'rb') as f:
        expected_dataframe = pickle.load(f)

    with io.open('tests/static/split_columns_hobolink_export.csv', 'r') as f:
        csv_text = f.read()

    class MockHobolinkResponse:
        text = csv_text
    monkeypatch.setattr(
        hobolink,
        'request_to_hobolink',
        lambda export_name: MockHobolinkResponse()
    )

    with app.app_context():
        assert get_live_hobolink_data().equals(expected_dataframe)
