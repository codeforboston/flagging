"""Configurations for the website.

Be careful with any config variables that reference the system environment, e.g.
USE_MOCK_DATA when it loads from `os.getenv`. These values are filled in when
this module is loaded, meaning if you change the env variables _after_ you load
this module, they won't refresh.
"""

import os
import os.path as op
from base64 import b64encode
from typing import Annotated
from typing import Any

from flask.cli import load_dotenv
from pydantic import Field
from pydantic import HttpUrl
from pydantic import computed_field
from pydantic import field_validator
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings
from pydantic_settings import NoDecode


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


class Config(BaseSettings):
    """This class is a container for all config variables. Instances of this
    class are loaded into the Flask app in the `create_app` function.
    """

    # ==========================================================================
    # FLASK BUILTIN CONFIG OPTIONS
    #
    # These options are Flask builtins, meaning that Flask treats these
    # particular config options in a special way.
    #
    # See here for more: https://flask.palletsprojects.com/en/1.1.x/config/
    # ==========================================================================

    DEBUG: bool = False
    SECRET_KEY: str = Field(default_factory=lambda: b64encode(os.urandom(32)).decode())
    PREFERRED_URL_SCHEME: str = "https"

    # ==========================================================================
    # Database
    # ==========================================================================

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"

    DATABASE_URL: str | None = None
    """Heroku-specific env var. This overrides the POSTGRES_ fields."""

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgres://", "postgresql://")
        else:
            return str(
                MultiHostUrl.build(
                    scheme="postgresql",
                    username=self.POSTGRES_USER,
                    password=self.POSTGRES_PASSWORD,
                    host=self.POSTGRES_HOST,
                    port=self.POSTGRES_PORT,
                    path=self.POSTGRES_DB,
                )
            )

    # Flask-SQLAlchemy
    # https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Flask-DB
    # https://github.com/nickjj/flask-db
    FLASK_DB_SEEDS_PATH: str = "alembic/seeds.py"

    # Flask-Admin
    # https://flask-admin.readthedocs.io/en/latest/
    FLASK_ADMIN_SWATCH: str = "lumen"

    # Flask-BasicAuth
    # https://flask-basicauth.readthedocs.io/en/latest/
    BASIC_AUTH_USERNAME: str
    BASIC_AUTH_PASSWORD: str

    # Flask-Caching
    # https://flask-caching.readthedocs.io/en/latest/
    # Set CACHE_TYPE=null in environment variables to turn off.
    CACHE_DEFAULT_TIMEOUT: int = 60 * 60 * 7
    CACHE_TYPE: str = "flask_caching.backends." + os.getenv("CACHE_TYPE", "redis")
    # REDIS_URL is specific to Heroku
    CACHE_REDIS_URL: str | None = Field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/")
    )
    CACHE_KEY_PREFIX: str = "frontend_cache"

    # Celery
    CELERY_BROKER_URL: str | None = Field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/")
    )
    CELERY_RESULT_BACKEND: str | None = Field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/")
    )

    @field_validator("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", "CACHE_REDIS_URL", mode="after")
    @classmethod
    def add_ssl_cert_reqs_to_heroku_redis_url(cls, v: str | None) -> str | None:
        # This is required when running on Heroku.
        if v is not None and v == os.getenv("REDIS_URL"):
            v += "?ssl_cert_reqs=none"
            return v
        return v

    # Mail
    MAIL_SERVER: str = Field(
        default_factory=lambda: os.getenv("MAILGUN_SMTP_SERVER", "smtp.gmail.com")
    )
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: str | None = Field(default_factory=lambda: os.getenv("MAILGUN_SMTP_LOGIN"))
    MAIL_PASSWORD: str | None = Field(default_factory=lambda: os.getenv("MAILGUN_SMTP_PASSWORD"))
    MAIL_ERROR_ALERTS_TO: Annotated[list[str], NoDecode] = Field(default_factory=lambda: [])
    MAIL_DATABASE_EXPORTS_TO: Annotated[list[str], NoDecode] = Field(default_factory=lambda: [])
    SEND_EMAILS: bool = False

    # ==========================================================================
    # MISC. CUSTOM CONFIG OPTIONS
    #
    # These are options that Flask does not know how to interpret, but our
    # custom code does. These are also used  to handle the behavior of the
    # website.
    # ==========================================================================

    HOBOLINK_LOGGERS: str | None = None
    HOBOLINK_BEARER_TOKEN: str | None = None
    HOBOLINK_EXCLUDE_SENSORS: Annotated[list[str], NoDecode] = Field(default_factory=lambda: [])

    TWITTER_AUTH: dict[str, Any] = {
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

    USE_CELERY: bool = True
    """We need to get around Heroku free tier limitations by not using a worker
    dyno to process backend database stuff. This will end up blocking requests
    during heavy operations, but oh well. That's the price for not funding
    river science.
    """

    SEND_TWEETS: bool = False
    """If True, the website behaves normally. If False, any time the app would
    send a Tweet, it does not do so. It is useful to turn this off when
    developing to test Twitter messages.
    """

    DEFAULT_WIDGET_VERSION: int = 2

    MAPBOX_ACCESS_TOKEN: str | None = None

    SENTRY_DSN: HttpUrl | None = None
    SENTRY_ENVIRONMENT: str | None = None

    @field_validator(
        "MAIL_ERROR_ALERTS_TO",
        "MAIL_DATABASE_EXPORTS_TO",
        "HOBOLINK_EXCLUDE_SENSORS",
        mode="before",
    )
    @classmethod
    def validate_semicolon_separated_lists(cls, v: list[str] | str | None) -> list[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(";")]
        elif v is None:
            return []
        return v


config = Config()
