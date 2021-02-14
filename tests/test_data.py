import os
from functools import wraps

import pytest
import pandas as pd

from flagging_site.data import hobolink
from flagging_site.data import Boathouse
from flagging_site.data.hobolink import get_live_hobolink_data
from flagging_site.data.usgs import get_live_usgs_data
from flagging_site.twitter import compose_tweet

STATIC_RESOURCES = os.path.join(os.path.dirname(__file__), 'static')


@pytest.fixture
def now():
    """Returns current time in EST."""
    return (
        pd.to_datetime('now', utc=True)
        .tz_convert('US/Eastern')
        .tz_localize(None)
    )


@pytest.mark.auth_required
def test_hobolink_data_is_recent(live_app, now):
    with live_app.app_context():
        df = get_live_hobolink_data()
        last_timestamp = df['time'].iloc[-1]
        time_difference = now - last_timestamp
        assert time_difference < pd.Timedelta(hours=2)


def test_usgs_data_is_recent(live_app, now):
    with live_app.app_context():
        df = get_live_usgs_data()
        last_timestamp = df['time'].iloc[-1]
        time_difference = now - last_timestamp
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
        live_app,
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

    with live_app.app_context():
        assert get_live_hobolink_data().equals(expected_dataframe)


def tweets_parametrization(func: callable):
    """This decorator creates two new fixtures: overrides and expected_text.
    It performs the work of overriding a number of flags equivalent to the
    `overriddes` amount before the decorated text receives the db_session.
    """
    @pytest.mark.parametrize(
        ('overrides', 'expected_text'),
        [
            (0, 'all boathouses are safe as of'),
            (2, 'some boathouses are unsafe as of'),
            (999, 'all boathouses are unsafe as of'),
        ]
    )
    @wraps(func)
    def _wrap(overrides, expected_text, db_session, *args, **kwargs):
        db_session \
            .query(Boathouse) \
            .filter(Boathouse.id <= overrides) \
            .update({"overridden": True})
        db_session.commit()
        func(overrides, expected_text, db_session, *args, **kwargs)

    return _wrap


@tweets_parametrization
def test_tweet(overrides, expected_text, db_session):
    """Make sure it contains the text"""
    tweet = compose_tweet()
    assert expected_text in tweet


@tweets_parametrization
def test_tweet_chars(overrides, expected_text, db_session):
    """Tweets can have up to 280 characters (URLs are special and always count
    as 23 chars), but we want to be safe anyway, so we'll limit to 240 chars.
    """
    tweet = compose_tweet()
    assert len(tweet) < 240
