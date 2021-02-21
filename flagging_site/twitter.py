import tweepy
from flask import Flask
from flask import current_app

from .data.boathouses import Boathouse
from .data.database import get_current_time

tweepy_api = tweepy.API()


def init_tweepy(app: Flask):
    """Uses the app instance's config to add requisite credentials to the
    tweepy API instance.
    """
    # Pass Twitter API tokens into Tweepy's OAuthHandler
    auth = tweepy.OAuthHandler(
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

    flags = Boathouse.all_flags()
    current_time = get_current_time().strftime('%I:%M:%S %p, %m/%d/%Y')

    unsafe_count = len([k for k, v in flags.items() if v is False])
    total_count = len(flags)

    base_msg = (
        'The CRWA is reporting that {some_or_all} boathouses are {safe_or_unsafe}'
        ' as of {current_time}.{text_if_not_safe}'
    )

    text_if_not_safe = \
        ' Review our site for more details. https://crwa-flagging.herokuapp.com/'

    msg = base_msg.format(
        some_or_all='some' if total_count > unsafe_count > 0 else 'all',
        safe_or_unsafe='unsafe' if unsafe_count > 0 else 'safe',
        current_time=current_time,
        text_if_not_safe=text_if_not_safe if unsafe_count > 0 else ''
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
