"""
This file handles their access credentials and tokens for various APIs required
to retrieve data for the website.

The file that contains the credentials is called "vault.zip", and is referenced
by a constant, `VAULT_FILE`. This file is accessed using a password stored in
the config called `VAULT_PASSWORD`.

Inside the "vault.zip" file, there is a file named "keys.yml." And this is the
file with all the credentials (plus a Flask secret key). It looks like this:

    flask:
      secret_key: "<key is here>"
    hobolink:
      password: "<password is here>"
      user: "crwa"
      token: "<token is here>"
"""
import os
import zipfile
import json
from distutils.util import strtobool
from flask import current_app

from flagging_site.config import VAULT_FILE


def get_keys() -> dict:
    """Retrieves the keys from the `current_app` if it exists. If not, then this
    function tries to load directly from the vault. The reason this function
    exists is so that you can use the API wrappers regardless of whether or not
    the Flask app is running.

    Note that this function requires that you assign the vault password to the
    environmental variable named `VAULT_PASSWORD`.

    Returns:
        The full keys dict.
    """
    if current_app:
        d = current_app.config['KEYS']
    else:
        vault_file = os.getenv('VAULT_FILE') or VAULT_FILE
        d = load_keys_from_vault(vault_password=os.environ['VAULT_PASSWORD'],
                                 vault_file=vault_file)
    return d.copy()


def load_keys_from_vault(
        vault_password: str,
        vault_file: str = VAULT_FILE
) -> dict:
    """This code loads the keys directly from the vault zip file. Users should
    preference using the `get_keys()` function over this function.

    Args:
        vault_password: (str) Password for opening up the `vault_file`.
        vault_file: (str) File path of the zip file containing `keys.json`.

    Returns:
        Dict of credentials.
    """
    pwd = bytes(vault_password, 'utf-8')
    with zipfile.ZipFile(vault_file) as f:
        with f.open('keys.json', pwd=pwd, mode='r') as keys_file:
            d = json.load(keys_file)
    return d


def offline_mode() -> bool:
    if current_app:
        return current_app.config['OFFLINE_MODE']
    else:
        return bool(strtobool(os.getenv('OFFLINE_MODE', 'false')))


def get_data_store_file_path(file_name: str) -> str:
    if current_app:
        return os.path.join(current_app.config['DATA_STORE'], file_name)
    else:
        from ..config import DATA_STORE
        return os.path.join(DATA_STORE, file_name)
