"""The data store contains offline versions of the data so that you can run a
demo version of the website without the vault keys, or simply develop parts of
the website that don't require actively updated data without having to worry.
"""
import os
import click


@click.command()
@click.option('--vault_password',
              prompt=True,
              default=lambda: os.environ.get('VAULT_PASSWORD', None))
def refresh_data_store(vault_password) -> None:
    """When run, this function runs all the functions that compose the data
    store. The app itself should not be running this function; in fact, this
    function will raise an error if the app is turned on. This should only be
    run from the command line or a Python console.
    """
    os.environ['VAULT_PASSWORD'] = vault_password

    from flask import current_app
    if current_app:
        raise Exception('The app should not be running when this is ')

    from flagging_site.data.hobolink import get_hobolink_data
    from flagging_site.data.usgs import get_usgs_data


if __name__ == '__main__':
    refresh_data_store()
