import warnings
from functools import wraps
from typing import Any
from typing import Callable
from typing import TypeVar
from unittest.mock import patch

import pytest
import requests

from app.data.models.boathouse import Boathouse
from app.data.models.website_options import WebsiteOptions
from app.data.processing import core
from app.mail import mail
from app.twitter import compose_tweet


C = TypeVar("C", bound=Callable[..., Any])


@pytest.fixture
def mock_update_db():
    with patch.object(core, "update_db") as mocked_func:
        yield mocked_func


@pytest.fixture
def mail_send():
    with patch.object(mail, "send") as mocked_func:
        yield mocked_func


def test_mail_when_error_raised(mail_send, app, cli_runner, monkeypatch, db_session):
    # This should not cause an email to be send:
    monkeypatch.setattr(core, "update_db", lambda: None)
    cli_runner.invoke(app.cli, ["update-db"])
    assert mail_send.call_count == 0

    def raise_an_error():
        raise ValueError

    # This however should trigger an email to be sent:
    monkeypatch.setattr(core, "update_db", raise_an_error)
    cli_runner.invoke(app.cli, ["update-db"])
    assert mail_send.call_count == 1


def test_no_tweet_off_season(app, db_session, cli_runner, mock_update_db, mock_send_tweet):
    # Default database state (i.e. during testing) is boating_season is true.
    # So "update-website" should send a tweet.
    res = cli_runner.invoke(app.cli, ["update-db", "--tweet-status"])
    assert res.exit_code == 0
    assert mock_update_db.call_count == 1
    assert mock_send_tweet.call_count == 1

    # Now set boating_season to false.
    db_session.query(WebsiteOptions).filter(WebsiteOptions.id == 1).update(
        {"boating_season": False}
    )
    db_session.commit()

    # No tweets should go out when it's not boating season.
    # The call count should not have gone up since the previous assert.
    res = cli_runner.invoke(app.cli, ["update-website"])
    assert res.exit_code == 0
    assert mock_update_db.call_count == 2
    assert mock_send_tweet.call_count == 1


def test_shell_runs(app):
    available = {k: v for i in app.shell_context_processors for k, v in i().items()}
    assert "app" in available
    assert "client" in available
    assert "db" in available


def tweets_parametrization(func: C) -> C:
    """This decorator creates two new fixtures: overrides and expected_text.
    It performs the work of overriding a number of flags equivalent to the
    `overriddes` amount before the decorated text receives the db_session.
    """

    @pytest.mark.parametrize(
        ("overrides", "expected_text"),
        [
            (0, "Blue flags are being flown"),
            (2, "Red flags are being flown at some"),
            (999, "Red flags are being flown at all"),
        ],
    )
    @wraps(func)
    def _wrap(overrides, expected_text, db_session, *args, **kwargs):
        db_session.query(Boathouse).filter(Boathouse.id <= overrides).update({"overridden": True})
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


@pytest.mark.check_grammar
@tweets_parametrization
def test_tweet_grammar(overrides, expected_text, db_session):
    """Uses LanguageTool's public API to see if there are any grammatical errors
    in the tweet messages. Grammatical errors may be caused by faulty logic when
    constructing the message.
    """
    res = requests.post(
        "https://api.languagetool.org/v2/check",
        params={"language": "en-US", "text": compose_tweet()},
    )

    if res.status_code >= 400:
        warnings.warn(f"Error via languagetool.org: {res.text}")
    else:
        matches = res.json()["matches"]

        # There will be one message in the 'matches', which is there because
        # LanguageTool doesn't know that "CRWA" is a valid word. Otherwise
        # there should be no issues.
        assert len(matches) <= 1, (
            "There may be a grammatical error in this tweet:\n"
            f"{compose_tweet()!r}.\nIf you think this is a false positive, run "
            'pytest with the option -m "not check_grammar" to skip this test.'
        )
