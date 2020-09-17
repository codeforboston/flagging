import pandas as pd
import tweepy
from flask import Flask


tweepy_api = tweepy.API()


def init_tweepy(app: Flask):
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


def tweet_out_status():
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
    tweepy_api.update_status(msg)
