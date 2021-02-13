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
    # from .data.manual_overrides import get_currently_overridden_reaches
    from .blueprints.flagging import get_flags

    df = latest_model_outputs()
    df = df.set_index('reach')

    # overridden_reaches = get_currently_overridden_reaches()
    flags = get_flags()

    # flags = {
    #     reach: val['safe'] and reach not in overridden_reaches
    #     for reach, val
    #     in df.to_dict(orient='index').items()
    # }

    current_time = (
        pd.Timestamp('now', tz='UTC')
        .tz_convert('US/Eastern')
        .strftime('%I:%M:%S %p, %m/%d/%Y')
    )
    unsafe_count = list(flags.values()).count(False)
    tot_count = len(flags)
    if unsafe_count < 1:
        msg = (
            'Our predictive model is reporting all boathouses are safe for '
            f'recreational activities as of {current_time}.'
        )
    elif unsafe_count == tot_count:
        # unsafe = ''.join([str(k) for k, v in flags.items() if v is False])
        msg = (
            f'The CRWA is reporting that all boathouses are unsafe for recreational activities '
            f'as of {current_time}. https://crwa-flagging.herokuapp.com/'
        )
    else:
        # unsafe = ''
        # unsafe_found = 0
        # for key in flags.keys():
        #     if flags.get(key) is False:
        #         unsafe += str(key)
        #         unsafe_found += 1
        #         if unsafe_found < unsafe_count - 1:
        #             unsafe += ', '
        #         else:
        #             if unsafe_found == unsafe_count - 1:
        #                 if unsafe_count > 2:
        #                     unsafe += ', and '
        #                 else:
        #                     unsafe += ' and '
        # msg = (
        #     f'The CRWA is reporting that reaches {unsafe} are unsafe for recreational activities as of {current_time}. '
        #     f' https://crwa-flagging.herokuapp.com/'
        # )

        msg = (
            f'The CRWA is reporting that some boathouses are unsafe and other boathouses are safe for '
            f'recreational activities as of {current_time}. Review our site for more details.'
            f' https://crwa-flagging.herokuapp.com/'
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
