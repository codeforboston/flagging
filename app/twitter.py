"""This module contains the logic for sending the current flagging status to
Twitter. The message is written by the function `compose_tweet()`, and actually
sending the message is handled by `tweet_current_status()`.
"""
import warnings


with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    import tweepy

from flask import Flask
from flask import current_app

from app.data.database import get_current_time
from app.data.globals import boathouses


tweepy_api = tweepy.API()


def init_tweepy(app: Flask):
    """Uses the app instance's config to add requisite credentials to the
    tweepy API instance.
    """
    # Pass Twitter API tokens into Tweepy's OAuthHandler
    auth = tweepy.OAuth1UserHandler(
        consumer_key=app.config['TWITTER_AUTH']['api_key'],
        consumer_secret=app.config['TWITTER_AUTH']['api_key_secret']
    )
    auth.set_access_token(
        key=app.config['TWITTER_AUTH']['access_token'],
        secret=app.config['TWITTER_AUTH']['access_token_secret']
    )

    # Register the auth defined above
    tweepy_api.auth = auth


def compose_tweet() -> str:
    """Generates the message that gets tweeted out. This function does not
    actually send the Tweet out; this function is separated from the function
    that sends the Tweet in order to assist with testing and development, in
    addition to addressing separation of concerns.

    Returns:
        Message intended to be tweeted that conveys the status of the Charles
        River.
    """

    # Number of boathouses that are not safe. (`not b.safe`)

    current_time = get_current_time().strftime('%I:%M %p, %m/%d/%Y')

    unsafe_count = len(list(filter(lambda b: not b.safe, boathouses)))

    if unsafe_count == 0:
        msg = (
            "Blue flags are being flown at all boathouses on the Lower"
            f" Charles as of {current_time}. Happy boating!"
        )
    else:
        some_or_all = 'some' if len(boathouses) > unsafe_count > 0 else 'all'
        msg = (
            f"🚩 Red flags are being flown at {some_or_all} boathouses on the"
            f" Lower Charles as of {current_time}. See our website for more"
            " details. https://crwa-flagging.herokuapp.com/"
        )

    return msg


def tweet_current_status() -> str:
    """Tweet a message about the status of the Charles River.

    Returns:
        The message that was tweeted out.
    """
    msg = compose_tweet()
    if current_app.config['SEND_TWEETS']:
        tweepy_api.update_status(msg)
    return msg
