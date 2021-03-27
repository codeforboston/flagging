"""Configurations for the website.

Be careful with any config variables that reference the system environment, e.g.
USE_MOCK_DATA when it loads from `os.getenv`. These values are filled in when
this module is loaded, meaning if you change the env variables _after_ you load
this module, they won't refresh.
"""
import os
from flask.cli import load_dotenv
from distutils.util import strtobool


# Constants
# ~~~~~~~~~

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
QUERIES_DIR = os.path.join(ROOT_DIR, 'data', 'queries')
DATA_STORE = os.path.join(ROOT_DIR, 'data', '_store')

# Load dotenv
# ~~~~~~~~~~~

if os.getenv('FLASK_ENV') != 'production':
    load_dotenv(os.path.join(ROOT_DIR, '..', '.env'))
    load_dotenv(os.path.join(ROOT_DIR, '..', '.flaskenv'))


# Configs
# ~~~~~~~

class Config:
    """This class is a container for all config variables. Instances of this
    class are loaded into the Flask app in the `create_app` function.
    """
    def __repr__(self):
        return f'{self.__class__.__name__}()'

    # ==========================================================================
    # FLASK BUILTIN CONFIG OPTIONS
    #
    # These options are Flask builtins, meaning that Flask treats these
    # particular config options in a special way.
    #
    # See here for more: https://flask.palletsprojects.com/en/1.1.x/config/
    # ==========================================================================

    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str = os.getenv('SECRET_KEY', os.urandom(32))

    # ==========================================================================
    # DATABASE CONFIG OPTIONS
    # ==========================================================================

    POSTGRES_USER: str = os.getenv('POSTGRES_USER',
                                   os.getenv('USER', 'postgres'))
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: str = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'flagging')

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Returns the URI for the Postgres database.
        Example:
            >>> Config().SQLALCHEMY_DATABASE_URI
            'postgres://postgres:password_here@localhost:5432/flagging'
        """
        if 'DATABASE_URL' in os.environ:
            return os.getenv('DATABASE_URL')
        else:
            user = self.POSTGRES_USER
            password = self.POSTGRES_PASSWORD
            host = self.POSTGRES_HOST
            port = self.POSTGRES_PORT
            db = self.POSTGRES_DB
            return f'postgresql://{user}:{password}@{host}:{port}/{db}'

    QUERIES_DIR: str = QUERIES_DIR
    """Directory that contains various queries that are accessible throughout
    the rest of the code base.
    """

    # Flask-SQLAlchemy
    # https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # ==========================================================================
    # CONFIG OPTIONS FROM OTHER EXTENSIONS
    # ==========================================================================

    # Flask-Admin
    # https://flask-admin.readthedocs.io/en/latest/
    FLASK_ADMIN_SWATCH = 'lumen'

    # Flask-BasicAuth
    # https://flask-basicauth.readthedocs.io/en/latest/
    BASIC_AUTH_USERNAME: str = os.getenv('BASIC_AUTH_USERNAME', 'admin')
    BASIC_AUTH_PASSWORD: str = os.getenv('BASIC_AUTH_PASSWORD', 'password')

    # Flask-Caching
    # https://flask-caching.readthedocs.io/en/latest/
    # Set CACHE_TYPE=null in environment variables to turn off.
    CACHE_DEFAULT_TIMEOUT: int = 60 * 60 * 7
    CACHE_TYPE: str = os.getenv('CACHE_TYPE', 'simple')

    # ==========================================================================
    # MISC. CUSTOM CONFIG OPTIONS
    #
    # These are options that Flask does not know how to interpret, but our
    # custom code does. These are also used  to handle the behavior of the
    # website.
    # ==========================================================================

    HOBOLINK_AUTH: dict = {
       'user': os.getenv('HOBOLINK_USERNAME'),
       'password': os.getenv('HOBOLINK_PASSWORD'),
       'token': os.getenv('HOBOLINK_TOKEN')
    }

    TWITTER_AUTH: dict = {
        'api_key': os.getenv('TWITTER_API_KEY'),
        'api_key_secret': os.getenv('TWITTER_API_KEY_SECRET'),
        'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
        'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    }

    USE_MOCK_DATA: bool = False
    """This is useful for front-end development for 2 reasons: First, you don't
    need credentials to develop the front-end of the website. Second, it means
    that the data loads faster and avoids any possible issues.
    """

    DATA_STORE: str = DATA_STORE
    """If Offline Mode is turned on, this is where the data will be pulled from
    when doing requests.
    """

    API_MAX_HOURS: int = 24 * 7
    """The maximum number of hours of data that the API will return. We need
    this to avoid any odd behaviors if the user requests more data than exists.
    """

    STORAGE_HOURS: int = 24 * 7
    """Each hour of data takes 15 rows of data:

    - 6 for HOBOlink
    - 4 for USGS
    - 1 for processed data
    - 4 for models

    Heroku free tier has a 10,000 total row limit across all tables, so we want
    to be well within that limit to the extent we can assure it.
    """

    SEND_TWEETS: bool = strtobool(os.getenv('SEND_TWEETS', 'false'))
    """If True, the website behaves normally. If False, any time the app would
    send a Tweet, it does not do so. It is useful to turn this off when
    developing to test Twitter messages.
    """

    DEFAULT_WIDGET_VERSION: int = 2

    MAPBOX_ACCESS_TOKEN: str = os.getenv(
        'MAPBOX_ACCESS_TOKEN',
        # This is a token that's floating around the web in a lot of quickstart
        # examples for LeafletJS, and seems to work. ¯\_(ツ)_/¯
        #
        # You should not use it ideally, but as a default for very quick runs
        # and demos, it should be OK.
        'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw')  # noqa


class ProductionConfig(Config):
    """The Production Config is used for deployment of the website to the
    internet. Currently the only part of the website that's pretty fleshed out
    is the `flagging` part, so that's the only blueprint we import.
    """
    PREFERRED_URL_SCHEME: str = 'https'
    SEND_TWEETS: bool = strtobool(os.getenv('SEND_TWEETS', 'true'))
    CACHE_TYPE: str = 'redis'
    CACHE_REDIS_URL: str = os.getenv('REDIS_URL')

    def __init__(self):
        """Initializing the production config allows us to ensure the existence
        of these variables in the environment."""
        try:
            self.BASIC_AUTH_USERNAME: str = os.environ['BASIC_AUTH_USERNAME']
            self.BASIC_AUTH_PASSWORD: str = os.environ['BASIC_AUTH_PASSWORD']
        except KeyError:
            msg = (
                'You did not set all of the environment variables required to '
                'initiate the app in production mode. If you are deploying '
                'the website to Heroku, read the Deployment docs page to '
                'learn how to set env variables in Heroku. If you are not on '
                'Heroku, make sure your FLASK_ENV environment variable is set!'
            )
            print(msg)
            raise


class DevelopmentConfig(Config):
    """The Development Config is used for running the website on your own
    computer. This is the default config loaded up when you use `run_unix_dev`
    or `run_windows_dev` to boot up the website.

    This config turns on both Flask's debug mode (which shows detailed messages
    for unhandled exceptions) and Flask's testing mode (which turns off the
    app instance's builtin exception handling).
    """
    DEBUG: bool = True
    TESTING: bool = True
    CACHE_DEFAULT_TIMEOUT: int = 60
    USE_MOCK_DATA: bool = strtobool(os.getenv('USE_MOCK_DATA', 'false'))
    SQLALCHEMY_ECHO: bool = strtobool(os.getenv('SQLALCHEMY_ECHO', 'false'))


class TestingConfig(Config):
    """The Testing Config is used for unit-testing and integration-testing the
    website.
    """
    SEND_TWEETS: bool = True  # Won't actually send tweets.
    TESTING: bool = True
    CACHE_TYPE: str = 'simple'
    USE_MOCK_DATA: bool = True
    TWITTER_AUTH: dict = {k: None for k in Config.TWITTER_AUTH}
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'flagging') + '_test'


class DemoConfig(ProductionConfig):
    """Config for the Heroku one-click deploy demo mode."""
    USE_MOCK_DATA: bool = True


def get_config_from_env(env: str) -> Config:
    """This function takes a string variable, looks at what that string variable
    is, and returns an instance of a Config class corresponding to that string
    variable.

    Args:
        env: (str) A string. Usually this is from `app.env` inside of the
             `create_app` function, which in turn is set by the environment
             variable `FLASK_ENV`.
    Returns:
        A Config instance corresponding with the string passed.

    Example:
        >>> get_config_from_env('development')
        DevelopmentConfig()
    """
    config_mapping = {
        'production': ProductionConfig,
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'demo': DemoConfig
    }
    try:
        config = config_mapping[env]
    except KeyError:
        valid_confs = config_mapping.values()
        print(f'Bad config passed; the config must be in {valid_confs}')
        raise
    else:
        return config()
