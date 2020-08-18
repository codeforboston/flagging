"""The data store contains offline versions of the data so that you can run a
demo version of the website without the vault keys, or simply develop parts of
the website that don't require actively updated data without having to worry.

This file is a CLI to refresh the data store. You can run it with:

`python flagging_site/data/_store/refresh.py`
"""
import os
import sys
from typing import Optional
import click


@click.command()
@click.option('--vault_password',
              prompt=True,
              default=lambda: os.environ.get('VAULT_PASSWORD', None))
def refresh_data_store(vault_password: Optional[str] = None) -> None:
    """When run, this function runs all the functions that compose the data
    store. The app itself should not be running this function; in fact, this
    function will raise an error if the app is turned on. This should only be
    run from the command line or a Python console.
    """
    os.environ['OFFLINE_MODE'] = 'false'
    if vault_password:
        os.environ['VAULT_PASSWORD'] = vault_password

    from flask import current_app
    if current_app:
        raise Exception('The app should not be running when the data store is '
                        'being refreshed.')

    from flagging_site.data.keys import get_data_store_file_path

    from flagging_site.data.hobolink import get_live_hobolink_data
    from flagging_site.data.hobolink import STATIC_FILE_NAME as hobolink_file
    get_live_hobolink_data('code_for_boston_export_21d')\
        .to_pickle(get_data_store_file_path(hobolink_file))

    from flagging_site.data.usgs import get_live_usgs_data
    from flagging_site.data.usgs import STATIC_FILE_NAME as usgs_file
    get_live_usgs_data().to_pickle(get_data_store_file_path(usgs_file))


if __name__ == '__main__':
    try:
        sys.path.append('.')
        refresh_data_store()
    finally:
        sys.path.remove('.')
