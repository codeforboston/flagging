import pandas as pd
import tweepy
from flask import Flask
from flask import current_app


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
    from .data.predictive_models import latest_model_outputs
    from .data.cyano_overrides import get_currently_overridden_reaches

    df = latest_model_outputs()
    df = df.set_index('reach')

    overridden_reaches = get_currently_overridden_reaches()

    flags = {
        reach: val['safe'] and reach not in overridden_reaches
        for reach, val
        in df.to_dict(orient='index').items()
    }

    current_time = pd.to_datetime('today').strftime('%I:%M:%S %p, %m/%d/%Y')

    if all(i for i in flags.values()):
        msg = (
            'Our predictive model is reporting all reaches are safe for '
            f'recreational activities as of {current_time}.'
        )
    else:
        unsafe = ', '.join([str(k) for k, v in flags.items() if v is False])
        msg = (
            'Our predictive model is reporting that the following reaches are '
            f'unsafe as of {current_time}: {unsafe}.'
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
