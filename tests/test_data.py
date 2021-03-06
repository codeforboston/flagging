import os
import pickle

import pytest
import pandas as pd

from flagging_site.data import hobolink
from flagging_site.data.hobolink import get_live_hobolink_data
from flagging_site.data.usgs import get_live_usgs_data


STATIC_RESOURCES = os.path.join(os.path.dirname(__file__), 'static')


def test_hobolink_data_is_recent(app):
    with app.app_context():
        df = get_live_hobolink_data()
        last_timestamp = df['time'].iloc[-1]
        time_difference = (pd.to_datetime('today') - last_timestamp)
        assert time_difference < pd.Timedelta(hours=2)


def test_usgs_data_is_recent(app):
    with app.app_context():
        df = get_live_usgs_data()
        last_timestamp = df['time'].iloc[-1]
        time_difference = (pd.to_datetime('today') - last_timestamp)
        assert time_difference < pd.Timedelta(hours=2)


@pytest.mark.parametrize(
    ('input_data', 'expected_output_data'),
    [
        ('test_case_01_input.txt', 'test_case_01_output.feather'),
        ('test_case_02_input.txt', 'test_case_02_output.feather')
    ]
)
def test_hobolink_handles_erroneous_csv(
        input_data,
        expected_output_data,
        app,
        monkeypatch
):
    """
    Tests that the code supports when Hobolink erroneously returns
    a CSV where some column headers are repeated and only one contains
    the actual data.
    """

    with open(os.path.join(STATIC_RESOURCES, input_data), 'r') as f:
        csv_text = f.read()

    fn = os.path.join(STATIC_RESOURCES, expected_output_data)
    expected_dataframe = pd.read_feather(fn)

    class MockHobolinkResponse:
        text = csv_text

    monkeypatch.setattr(
        hobolink,
        'request_to_hobolink',
        lambda export_name: MockHobolinkResponse()
    )

    with app.app_context():
        assert get_live_hobolink_data().equals(expected_dataframe)
