"""Configurations for the website.

Be careful with any config variables that reference the system environment, e.g.
OFFLINE_MODE when it loads from `os.getenv`. These values are filled in when
this module is loaded, meaning if you change the env variables _after_ you load
this module, they won't refresh.
"""
import os
from typing import Dict, Any, Optional, List
from distutils.util import strtobool


# Constants
# ~~~~~~~~~

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
QUERIES_DIR = os.path.join(ROOT_DIR, 'data', 'queries')
DATA_STORE = os.path.join(ROOT_DIR, 'data', '_store')
VAULT_FILE = os.path.join(ROOT_DIR, 'vault.zip')


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
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432
    POSTGRES_DBNAME: str = 'flagging'

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        user = self.POSTGRES_USER
        password = self.POSTGRES_PASSWORD
        host = self.POSTGRES_HOST
        port = self.POSTGRES_PORT
        db = self.POSTGRES_DBNAME
        return f'postgres://{user}:{password}@{host}:{port}/{db}'

    SQLALCHEMY_ECHO: bool = True
    SQLALCHEMY_RECORD_QUERIES: bool = True
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    QUERIES_DIR: str = QUERIES_DIR

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

    KEYS: Dict[str, Dict[str, Any]] = None
    """These are where the keys from the vault are stored. It should be a dict 
    of dicts. Each key in the first level dict corresponds to a different
    service that needs keys / secured credentials stored.
    
    Currently, HOBOlink and Flask's `SECRET_KEY` are the two services that pass
    through the vault.
    """

    VAULT_FILE: str = VAULT_FILE
    """Reference to the vault file's location. It's mostly passed here as a
    formality so that it can be adjusted if needed and accessed anywhere without
    importing from config.py.
    """

    OFFLINE_MODE: bool = False
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

    BLUEPRINTS: Optional[List[str]] = None
    """Names of the blueprints available to the app. We can use this to turn
    parts of the website off or on depending on if they're fully developed
    or not. If BLUEPRINTS is `None`, then it imports all the blueprints it can
    find in the `blueprints` module.
    """


class ProductionConfig(Config):
    """The Production Config is used for deployment of the website to the
    internet. Currently the only part of the website that's pretty fleshed out
    is the `flagging` part, so that's the only blueprint we import.
    """
    BLUEPRINTS: Optional[List[str]] = ['flagging']

    def __init__(self):
        self.BASIC_AUTH_USERNAME: str = os.environ['BASIC_AUTH_USERNAME']
        self.BASIC_AUTH_PASSWORD: str = os.environ['BASIC_AUTH_PASSWORD']


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
    VAULT_OPTIONAL: bool = True
    DEBUG: bool = True
    TESTING: bool = True
    OFFLINE_MODE = strtobool(os.getenv('OFFLINE_MODE') or 'false')
    BASIC_AUTH_USERNAME: str = os.getenv('BASIC_AUTH_USERNAME', 'admin')
    BASIC_AUTH_PASSWORD: str = os.getenv('BASIC_AUTH_PASSWORD', 'password')


class TestingConfig(Config):
    """The Testing Config is used for unit-testing and integration-testing the
    website.
    """
    TESTING: bool = True
    BASIC_AUTH_USERNAME: str = os.getenv('BASIC_AUTH_USERNAME', 'admin')
    BASIC_AUTH_PASSWORD: str = os.getenv('BASIC_AUTH_PASSWORD', 'password')


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
        'testing': TestingConfig
    }
    try:
        config = config_mapping[env]
    except KeyError:
        raise KeyError('Bad config passed; the config must be production, '
                       'development, or testing.')
    return config()
