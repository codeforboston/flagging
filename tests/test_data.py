import os

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from sqlalchemy import text

from app.data.models.boathouse import Boathouse
from app.data.processing import hobolink
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.usgs import get_live_usgs_data


STATIC_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


@pytest.fixture
def now():
    """Returns current time in EST."""
    return pd.to_datetime("now", utc=True).tz_convert("US/Eastern").tz_localize(None)


@pytest.mark.auth_required
def test_hobolink_data_is_recent(live_app, now):
    with live_app.app_context():
        df = get_live_hobolink_data()
        last_timestamp = df["time"].iloc[-1]
        time_difference = now - last_timestamp
        assert time_difference < pd.Timedelta(hours=2)


def test_usgs_data_is_recent(live_app, now):
    with live_app.app_context():
        df = get_live_usgs_data()
        last_timestamp = df["time"].iloc[-1]
        time_difference = now - last_timestamp
        assert time_difference < pd.Timedelta(hours=2)


@pytest.mark.parametrize(
    ("input_data", "expected_output_data"),
    [
        ("test_case_01_input.txt", "test_case_01_output.feather"),
        ("test_case_02_input.txt", "test_case_02_output.feather"),
    ],
)
def test_hobolink_handles_erroneous_csv(input_data, expected_output_data, live_app, monkeypatch):
    """
    Tests that the code supports when Hobolink erroneously returns
    a CSV where some column headers are repeated and only one contains
    the actual data.
    """

    with open(os.path.join(STATIC_RESOURCES, input_data), "r") as f:
        csv_text = f.read()

    fn = os.path.join(STATIC_RESOURCES, expected_output_data)
    expected_dataframe = pd.read_feather(fn)

    class MockHobolinkResponse:
        text = csv_text

    monkeypatch.setattr(hobolink, "request_to_hobolink", lambda export_name: MockHobolinkResponse())

    with live_app.app_context():
        assert_frame_equal(get_live_hobolink_data(), expected_dataframe)


def test_boathouse_trigger(db_session):
    """Make sure we're recording the overrides."""

    def number_of_rows(r):
        return len([i for i in r])

    before = db_session.execute(text("""SELECT * FROM override_history;"""))

    db_session.query(Boathouse).filter(Boathouse.name == "Union Boat Club").update(
        {"overridden": True}
    )
    db_session.commit()

    after = db_session.execute(text("""SELECT * FROM override_history;"""))

    assert number_of_rows(after) == number_of_rows(before) + 1
