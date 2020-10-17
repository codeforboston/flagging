"""Configurations for the website.

Be careful with any config variables that reference the system environment, e.g.
USE_MOCK_DATA when it loads from `os.getenv`. These values are filled in when
this module is loaded, meaning if you change the env variables _after_ you load
this module, they won't refresh.
"""
import os
import re
from flask.cli import load_dotenv
from distutils.util import strtobool


# Constants
# ~~~~~~~~~

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
QUERIES_DIR = os.path.join(ROOT_DIR, 'data', 'queries')
DATA_STORE = os.path.join(ROOT_DIR, 'data', '_store')
VAULT_FILE = os.path.join(ROOT_DIR, 'vault.7z')


# Load dotenv
# ~~~~~~~~~~~

if os.getenv('FLASK_ENV') == 'development':
    load_dotenv(os.path.join(ROOT_DIR, '..', '.flaskenv'))
    load_dotenv(os.path.join(ROOT_DIR, '..', '.env'))


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
    SECRET_KEY: str = None  # Note: Loaded from vault

    # ==========================================================================
    # DATABASE CONFIG OPTIONS
    # ==========================================================================
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', os.getenv('USER', 'postgres'))
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: str = '5432'
    POSTGRES_DBNAME: str = 'flagging'

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Returns the URI for the Postgres database.

        Example:
            >>> Config().SQLALCHEMY_DATABASE_URI
            'postgres://postgres:password_here@localhost:5432/flagging'
        """
        user = self.POSTGRES_USER
        password = self.POSTGRES_PASSWORD
        host = self.POSTGRES_HOST
        port = self.POSTGRES_PORT
        db = self.POSTGRES_DBNAME
        return f'postgres://{user}:{password}@{host}:{port}/{db}'

    SQLALCHEMY_RECORD_QUERIES: bool = True
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    QUERIES_DIR: str = QUERIES_DIR
    """Directory that contains various queries that are accessible throughout
    the rest of the code base.
    """

    # ==========================================================================
    # MISC. CUSTOM CONFIG OPTIONS
    #
    # These are options that Flask does not know how to interpret, but our
    # custom code does. These are also used  to handle the behavior of the
    # website. At the moment, all of these options relate to either the "vault"
    # system or offline mode.
    # ==========================================================================
    VAULT_OPTIONAL: bool = False
    """If True, the app instance will not fail to load just because the vault
    wasn't opened. Usually set alongside DEBUG mode.
    """

    VAULT_PASSWORD: str = os.getenv('VAULT_PASSWORD')

    HOBOLINK_AUTH: dict = {
       'password': None,
       'user': None,
       'token': None
    }
    """Note: Do not fill these out manually; the HOBOlink auth gets populated
    from the vault.
    """

    TWITTER_AUTH: dict = {
        'api_key': None,
        'api_key_secret': None,
        'access_token': None,
        'access_token_secret': None,
        'bearer_token': None
    }
    """Note: Do not fill these out manually; the Twitter auth gets populated
    from the vault.
    """

    VAULT_FILE: str = VAULT_FILE
    """Reference to the vault file's location. It's mostly passed here as a
    formality so that it can be adjusted if needed and accessed anywhere without
    importing from config.py.
    """

    USE_MOCK_DATA: bool = False
    """If Offline Mode is turned on, the data used when performing requests will
    be a static pickled version of the data instead of actively pulled from HTTP
    requests.
    
    This is useful for front-end development for two reasons: First, you don't
    need the vault password to develop the front-end of the website. Second, it
    means that the data loads faster and avoids any possible issues.
    """

    DATA_STORE: str = DATA_STORE
    """If Offline Mode is turned on, this is where the data will be pulled from
    when doing requests.
    """

    API_MAX_HOURS: int = 48
    """The maximum number of hours of data that the API will return. We are not
    trying to be stingy about our data, we just want this in order to avoid any
    odd behaviors if the user requests more data than exists.
    """

    SEND_TWEETS: bool = strtobool(os.getenv('SEND_TWEETS') or 'false')
    """If True, the website behaves normally. If False, any time the app would
    send a Tweet, it does not do so. It is useful to turn this off when
    developing to test Twitter messages.
    """

    BASIC_AUTH_USERNAME: str = os.getenv('BASIC_AUTH_USERNAME', 'admin')
    BASIC_AUTH_PASSWORD: str = os.getenv('BASIC_AUTH_PASSWORD', 'password')


class ProductionConfig(Config):
    """The Production Config is used for deployment of the website to the
    internet. Currently the only part of the website that's pretty fleshed out
    is the `flagging` part, so that's the only blueprint we import.
    """
    SEND_TWEETS: str = True

    def __init__(self):
        """Initializing the production config allows us to ensure the existence
        of these variables in the environment."""
        try:
            self.VAULT_PASSWORD: str = os.environ['VAULT_PASSWORD']
            self.BASIC_AUTH_USERNAME: str = os.environ['BASIC_AUTH_USERNAME']
            self.BASIC_AUTH_PASSWORD: str = os.environ['BASIC_AUTH_PASSWORD']
        except KeyError:
            msg = (
                'You did not set all of the environment variables required to '
                'initiate the app in production mode. If you are deploying '
                'the website to Heroku, read the Deployment docs page to '
                'learn how to set env variables in Heroku.'
            )
            raise KeyError(msg)

        # Production does things in reverse: Instead of defining the database
        # using the POSTGRES_* environment variables, the database is set with
        # the `DATABASE_URL` (provided automatically by Postgres), and the
        # POSTGRES_* variables are not used.
        #
        # In the rare event that they are needed in production, they are set
        # to be consistent with the `DATABASE_URL` below:
        postgres_url_schema = re.compile('''
            ^
            postgres://
            ([^\s:@/]+) # Username
            :([^\s:@/]+) # Password
            @([^\s:@/]+) # Host
            :([^\s:@/]+) # Port
            /([^\s:@/]*?) # Database
            $
        ''', re.VERBOSE)
        matches = re.search(postgres_url_schema, self.SQLALCHEMY_DATABASE_URI)
        self.POSTGRES_USER = matches.group(1)
        self.POSTGRES_PASSWORD = matches.group(2)
        self.POSTGRES_HOST = matches.group(3)
        self.POSTGRES_PORT = matches.group(4)
        self.POSTGRES_DBNAME = matches.group(5)

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return os.getenv('DATABASE_URL')


class StagingConfig(ProductionConfig):
    """The ProductionConfig is the as the ProductionConfig, except it does not
    send Tweets unless told to with a `SEND_TWEETS` environment variable.
    """
    SEND_TWEETS = strtobool(os.getenv('SEND_TWEETS') or 'false')


class DevelopmentConfig(Config):
    """The Development Config is used for running the website on your own
    computer. This is the default config loaded up when you use `run_unix_dev`
    or `run_windows_dev` to boot up the website.

    This config turns on both Flask's debug mode (which shows detailed messages
    for unhandled exceptions) and Flask's testing mode (which turns off the
    app instance's builtin exception handling).

    This config also turns on a `VAULT_OPTIONAL` mode, which warns the user if
    the vault hasn't been loaded but doesn't prevent the website from loading
    just because the vault is not open.
    """
    SQLALCHEMY_ECHO: bool = True
    VAULT_OPTIONAL: bool = True
    DEBUG: bool = True
    TESTING: bool = True
    USE_MOCK_DATA = strtobool(os.getenv('USE_MOCK_DATA') or 'false')


class TestingConfig(Config):
    """The Testing Config is used for unit-testing and integration-testing the
    website.
    """
    SEND_TWEETS: bool = False
    TESTING: bool = True


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
        'staging': StagingConfig,
        'development': DevelopmentConfig,
        'testing': TestingConfig,
    }
    try:
        config = config_mapping[env]
    except KeyError:
        raise KeyError('Bad config passed; the config must be production, '
                       'development, or testing.')
    return config()
