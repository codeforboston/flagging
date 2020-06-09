"""
Configurations for the website.
"""
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Constants
# ~~~~~~~~~

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_STORE = os.path.join(ROOT_DIR, 'data', '_store')
VAULT_FILE = os.path.join(ROOT_DIR, 'vault.zip')


# Configs
# ~~~~~~~

@dataclass
class BaseConfig:
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
    #
    # Not currently used, but soon we'll want to start using the config to set
    # up references to the database, data storage, and data retrieval.
    # ==========================================================================
    DATABASE: str = None

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

class ProductionConfig(BaseConfig):
    """The Production Config is used for deployment of the website to the
    internet. Currently the only part of the website that's pretty fleshed out
    is the `flagging` part, so that's the only blueprint we import.
    """
    BLUEPRINTS: Optional[List[str]] = ['flagging']

class DevelopmentConfig(BaseConfig):
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

class OfflineDevelopmentConfig(DevelopmentConfig):
    """The Offline Development Config extends `DevelopmentConfig` to use a
    pickled version of the data instead of loading data through the whole
    pipeline from HTTP requests. It is useful for front-end development for two
    reasons: First, you don't need the vault password to develop the front-end
    of the website. Second, it means that the data loads faster and avoids any
    possible issues.
    """
    OFFLINE_MODE: bool = True


class TestingConfig(BaseConfig):
    """The Testing Config is used for unit-testing and integration-testing the
    website.
    """
    TESTING: bool = True
