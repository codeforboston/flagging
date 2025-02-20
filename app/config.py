"""Configurations for the website.

Be careful with any config variables that reference the system environment, e.g.
USE_MOCK_DATA when it loads from `os.getenv`. These values are filled in when
this module is loaded, meaning if you change the env variables _after_ you load
this module, they won't refresh.
"""

import os
import os.path as op

from distutils.util import strtobool
from flask.cli import load_dotenv


# Constants
# ~~~~~~~~~

ROOT_DIR = op.abspath(op.dirname(__file__))
QUERIES_DIR = op.join(ROOT_DIR, "data", "queries")
DATA_STORE = op.join(ROOT_DIR, "data", "_store")

# Load dotenv
# ~~~~~~~~~~~

if os.getenv("ENV") != "production":
    load_dotenv(op.join(ROOT_DIR, "..", ".env"))
    load_dotenv(op.join(ROOT_DIR, "..", ".flaskenv"))


# Configs
# ~~~~~~~


class Config:
    """This class is a container for all config variables. Instances of this
    class are loaded into the Flask app in the `create_app` function.
    """

    def __repr__(self):
        return f"{self.__class__.__name__}()"

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
    SECRET_KEY: str = os.getenv("SECRET_KEY", os.urandom(32))

    # ==========================================================================
    # DATABASE CONFIG OPTIONS
    # ==========================================================================

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", os.getenv("USER", "postgres"))
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "flagging")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Returns the URI for the Postgres database.
        Example:
            >>> Config().SQLALCHEMY_DATABASE_URI
            'postgres://postgres:password_here@localhost:5432/flagging'
        """
        if "DATABASE_URL" in os.environ:
            return os.environ["DATABASE_URL"].replace("postgres://", "postgresql://")
        else:
            user = self.POSTGRES_USER
            password = self.POSTGRES_PASSWORD
            host = self.POSTGRES_HOST
            port = self.POSTGRES_PORT
            db = self.POSTGRES_DB
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"

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

    # Flask-DB
    FLASK_DB_SEEDS_PATH = "alembic/seeds.py"

    # Flask-Admin
    # https://flask-admin.readthedocs.io/en/latest/
    FLASK_ADMIN_SWATCH = "lumen"

    # Flask-BasicAuth
    # https://flask-basicauth.readthedocs.io/en/latest/
    BASIC_AUTH_USERNAME: str = os.getenv("BASIC_AUTH_USERNAME", "admin")
    BASIC_AUTH_PASSWORD: str = os.getenv("BASIC_AUTH_PASSWORD", "password")

    # Flask-Caching
    # https://flask-caching.readthedocs.io/en/latest/
    # Set CACHE_TYPE=null in environment variables to turn off.
    CACHE_DEFAULT_TIMEOUT: int = 60 * 60 * 7
    CACHE_TYPE: str = "flask_caching.backends." + os.getenv("CACHE_TYPE", "redis")
    CACHE_REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/")
    CACHE_KEY_PREFIX: str = "frontend_cache"

    # Celery
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/")
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "redis://localhost:6379/")

    # Mail
    MAIL_SERVER = os.getenv("MAILGUN_SMTP_SERVER") or "smtp.gmail.com"
    MAIL_PORT = int(os.getenv("MAILGUN_SMTP_PORT") or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAILGUN_SMTP_LOGIN") or os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAILGUN_SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD")
    MAIL_ERROR_ALERTS_TO = os.getenv("MAIL_ERROR_ALERTS_TO", "")
    MAIL_DATABASE_EXPORTS_TO = os.getenv("MAIL_DATABASE_EXPORTS_TO", "")
    # ==========================================================================
    # MISC. CUSTOM CONFIG OPTIONS
    #
    # These are options that Flask does not know how to interpret, but our
    # custom code does. These are also used  to handle the behavior of the
    # website.
    # ==========================================================================

    ENV: str = None

    HOBOLINK_AUTH: dict = {
        "user": os.getenv("HOBOLINK_USERNAME"),
        "password": os.getenv("HOBOLINK_PASSWORD"),
        "token": os.getenv("HOBOLINK_TOKEN"),
    }

    TWITTER_AUTH: dict = {
        "api_key": os.getenv("TWITTER_API_KEY") or "",
        "api_key_secret": os.getenv("TWITTER_API_KEY_SECRET") or "",
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN") or "",
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET") or "",
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

    USE_CELERY: bool = strtobool(os.getenv("USE_CELERY", "true"))
    """We need to get around Heroku free tier limitations by not using a worker
    dyno to process backend database stuff. This will end up blocking requests
    during heavy operations, but oh well. That's the price for not funding
    river science.
    """

    SEND_TWEETS: bool = strtobool(os.getenv("SEND_TWEETS", "false"))
    """If True, the website behaves normally. If False, any time the app would
    send a Tweet, it does not do so. It is useful to turn this off when
    developing to test Twitter messages.
    """

    DEFAULT_WIDGET_VERSION: int = 2

    MAPBOX_ACCESS_TOKEN: str = os.getenv("MAPBOX_ACCESS_TOKEN")

    SENTRY_DSN: str | None = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT: str | None = os.getenv("SENTRY_ENVIRONMENT")


class ProductionConfig(Config):
    """The Production Config is used for deployment of the website to the
    internet. Currently the only part of the website that's pretty fleshed out
    is the `flagging` part, so that's the only blueprint we import.
    """

    ENV: str = "production"
    CACHE_TYPE: str = "flask_caching.backends.redis"
    PREFERRED_URL_SCHEME: str = "https"
    SEND_TWEETS: bool = strtobool(os.getenv("SEND_TWEETS", "true"))

    def __init__(self):
        """Initializing the production config allows us to ensure the existence
        of these variables in the environment."""
        try:
            self.BASIC_AUTH_USERNAME: str = os.environ["BASIC_AUTH_USERNAME"]
            self.BASIC_AUTH_PASSWORD: str = os.environ["BASIC_AUTH_PASSWORD"]
        except KeyError:
            msg = (
                "You did not set all of the environment variables required to "
                "initiate the app in production mode. If you are deploying "
                "the website to Heroku, read the Deployment docs page to "
                "learn how to set env variables in Heroku. If you are not on "
                "Heroku, make sure your FLASK_ENV environment variable is set!"
            )
            print(msg)
            raise
        self.CACHE_REDIS_URL = self.CACHE_REDIS_URL + "?ssl_cert_reqs=none"
        self.CELERY_BROKER_URL = self.CELERY_BROKER_URL + "?ssl_cert_reqs=none"
        self.CELERY_RESULT_BACKEND = self.CELERY_RESULT_BACKEND + "?ssl_cert_reqs=none"
        self.CACHE_OPTIONS = {"ssl_cert_reqs": "CERT_NONE"}


class StagingConfig(ProductionConfig):
    ENV: str = "staging"
    pass


class DevelopmentConfig(Config):
    """The Development Config is used for running the website on your own
    computer. This is the default config loaded up when you use `run_unix_dev`
    or `run_windows_dev` to boot up the website.

    This config turns on both Flask's debug mode (which shows detailed messages
    for unhandled exceptions) and Flask's testing mode (which turns off the
    app instance's builtin exception handling).
    """

    ENV: str = "development"
    DEBUG: bool = True
    TESTING: bool = True
    CACHE_DEFAULT_TIMEOUT: int = 60
    USE_MOCK_DATA: bool = strtobool(os.getenv("USE_MOCK_DATA", "false"))
    SQLALCHEMY_ECHO: bool = strtobool(os.getenv("SQLALCHEMY_ECHO", "false"))


class TestingConfig(Config):
    """The Testing Config is used for unit-testing and integration-testing the
    website.
    """

    ENV: str = "testing"
    PREFERRED_URL_SCHEME: str = "https"
    SEND_TWEETS: bool = True  # Won't actually send tweets.
    TESTING: bool = True
    CACHE_TYPE: str = "flask_caching.backends.simple"
    USE_MOCK_DATA: bool = True
    TWITTER_AUTH: dict = {k: "?" for k in Config.TWITTER_AUTH}
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "flagging") + "_test"
    MAIL_USERNAME = "admin@admin.com"
    MAIL_ERROR_ALERTS_TO = "some@email.com"
    BASIC_AUTH_USERNAME: str = "admin"
    BASIC_AUTH_PASSWORD: str = "password"


class DemoConfig(ProductionConfig):
    """Config for the Heroku one-click deploy demo mode."""

    ENV: str = "demo"
    USE_MOCK_DATA: bool = True


def get_config_from_env(env: str) -> Config:
    """This function takes a string variable, looks at what that string variable
    is, and returns an instance of a Config class corresponding to that string
    variable.

    Args:
        env: (str) A string. Usually this is from `app.env` inside of the
             `create_app` function, which in turn is set by the environment
             variable `ENV`.
    Returns:
        A Config instance corresponding with the string passed.

    Example:
        >>> get_config_from_env('development')
        DevelopmentConfig()
    """
    config_mapping = {
        "production": ProductionConfig,
        "staging": StagingConfig,
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "demo": DemoConfig,
    }
    try:
        config = config_mapping[env]
    except KeyError:
        valid_confs = config_mapping.values()
        print(f"Bad config passed; the config must be in {valid_confs}")
        raise
    else:
        return config()
