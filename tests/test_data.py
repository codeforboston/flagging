import os
from datetime import UTC
from datetime import datetime

import pandas as pd
import pytest
from sqlalchemy import text

from app.data.models.boathouse import Boathouse
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.usgs import get_live_usgs_data


STATIC_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


@pytest.mark.auth_required
def test_hobolink_data_is_recent(live_app):
    with live_app.app_context():
        df = get_live_hobolink_data()
        last_timestamp = df["time"].iloc[-1]
        time_difference = datetime.now(UTC) - last_timestamp
        assert time_difference < pd.Timedelta(hours=2)


def test_usgs_w_data_is_recent(live_app):
    with live_app.app_context():
        df = get_live_usgs_data(site_no="01104500")
        last_timestamp = df["time"].iloc[-1]
        time_difference = datetime.now(UTC) - last_timestamp
        assert time_difference < pd.Timedelta(hours=12)


def test_usgs_b_data_is_recent(live_app):
    with live_app.app_context():
        df = get_live_usgs_data(site_no="01104683")
        last_timestamp = df["time"].iloc[-1]
        time_difference = datetime.now(UTC) - last_timestamp
        assert time_difference < pd.Timedelta(hours=12)


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
