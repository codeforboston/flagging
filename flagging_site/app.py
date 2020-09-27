"""
This file handles the construction of the Flask application object.
"""
import os
import click
import time
import json
from typing import Optional
from typing import Dict
from typing import Union

from flask import Flask

import py7zr
from lzma import LZMAError
from py7zr.exceptions import PasswordRequired

from .config import Config
from .config import get_config_from_env


def create_app(config: Optional[Union[Config, str]] = None) -> Flask:
    """Create and configure an instance of the Flask application. We use the
    `create_app` scheme over defining the `app` directly at the module level so
    the app isn't loaded immediately by importing the module.

    Args:
        config: (ClassVar) Can be either a string such as `config.BaseConfig`,
                or the actual object itself.
    Returns:
        The fully configured Flask app instance.
    """
    app = Flask(__name__)

    # Get a config for the website. If one was not passed in the function, then
    # a config will be used depending on the `FLASK_ENV`.
    if config is None:
        # Determine the config based on the `FLASK_ENV`.
        config = get_config_from_env(app.env)
    elif isinstance(config, str):
        # If config is string, parse it as if it's an env.
        config = get_config_from_env(config)

    app.config.from_object(config)

    # Use the stuff inside `vault.zip` file to update the app.
    update_config_from_vault(app)

    # Register the "blueprints." Blueprints are basically like mini web apps
    # that can be joined to the main web app. In this particular app, the way
    # blueprints are imported is: If BLUEPRINTS is in the config, then import
    # only from that list. Otherwise, import everything that's inside of
    # `blueprints/__init__.py`.
    from .blueprints.api import bp as api_bp
    app.register_blueprint(api_bp)

    from .blueprints.flagging import bp as flagging_bp
    app.register_blueprint(flagging_bp)

    # Add Swagger to the app. Swagger automates the API documentation and
    # provides an interface for users to query the API on the website.
    init_swagger(app)

    # Register the database commands
    from .data import db
    db.init_app(app)

    # Register admin
    from .admin import init_admin
    init_admin(app)

    # Register Twitter bot
    from .twitter import init_tweepy
    init_tweepy(app)

    @app.before_request
    def before_request():
        from flask import g
        g.request_start_time = time.time()
        g.request_time = lambda: '%.3fs' % (time.time() - g.request_start_time)

    @app.cli.command('create-db')
    def create_db_command():
        """Create database (after verifying that it isn't already there)."""
        from .data.database import create_db
        if create_db():
            click.echo('The database was created.')
        else:
            click.echo('The database was already there.')

    @app.cli.command('init-db')
    def init_db_command():
        """Clear existing data and create new tables."""
        from .data.database import init_db
        init_db()
        click.echo('Initialized the database.')

    @app.cli.command('update-db')
    def update_db_command():
        """Update the database with the latest live data."""
        from .data.database import update_database
        update_database()
        click.echo('Updated the database.')

    @app.cli.command('update-website')
    @click.pass_context
    def update_website_command(ctx):
        """Updates the database, then Tweets a message."""
        ctx.invoke(update_db_command)
        from .twitter import tweet_current_status
        msg = tweet_current_status()
        click.echo(f'Sent out tweet: {msg!r}')

    # Make a few useful functions available in Flask shell without imports
    @app.shell_context_processor
    def make_shell_context():
        import pandas as pd
        import numpy as np
        from flask import current_app
        from .blueprints.flagging import get_data
        from .data import db
        from .data.hobolink import get_live_hobolink_data
        from .data.predictive_models import process_data
        from .data.usgs import get_live_usgs_data
        from .twitter import compose_tweet

        return {
            'pd': pd,
            'np': np,
            'app': current_app,
            'db': db,
            'get_data': get_data,
            'get_live_hobolink_data': get_live_hobolink_data,
            'get_live_usgs_data': get_live_usgs_data,
            'process_data': process_data,
            'compose_tweet': compose_tweet
        }

    # And we're all set! We can hand the app over to flask at this point.
    return app


def init_swagger(app: Flask):
    """This function handles all the logic for adding Swagger automated
    documentation to the application instance.

    Args:
        app: A Flask application instance.
    """
    from flasgger import Swagger
    from flasgger import LazyString
    from flask import url_for

    swagger_config = {
        'headers': [],
        'specs': [
            {
                'endpoint': 'reach_api',
                'route': '/api/reach_api.json',
                'rule_filter': lambda rule: True,  # all in
                'model_filter': lambda tag: True,  # all in
            }
        ],
        'static_url_path': '/flasgger_static',
        # 'static_folder': '/static/flasgger',
        'swagger_ui': True,
        'specs_route': '/api/docs'
    }
    template = {
        'info': {
            'title': 'CRWA Public Flagging API',
            'description':
                "API for the Charles River Watershed Association's predictive "
                'models, and the data used for those models.',
            'contact': {
                'responsibleOrganization': 'Charles River Watershed Association',
                'responsibleDeveloper': 'Code for Boston',
            },
        }
    }
    app.config['SWAGGER'] = {
        'uiversion': 3,
        'favicon': LazyString(
            lambda: url_for('static', filename='favicon/favicon.ico'))
    }

    Swagger(app, config=swagger_config, template=template)


def _load_secrets_from_vault(
        password: str,
        vault_file: str
) -> Dict[str, Union[str, Dict[str, str]]]:
    """This code loads the keys directly from the vault zip file.

    The schema of the vault's `secrets.json` file looks like this:

    >>> {
    >>>     "SECRET_KEY": str,
    >>>     "HOBOLINK_AUTH": {
    >>>         "password": str,
    >>>         "user": str,
    >>>         "token": str
    >>>     },
    >>>     "TWITTER_AUTH": {
    >>>         "api_key": str,
    >>>         "api_key_secret": str,
    >>>         "access_token": str,
    >>>         "access_token_secret": str,
    >>>         "bearer_token": str
    >>>     }
    >>> }

    Args:
        vault_password: (str) Password for opening up the `vault_file`.
        vault_file: (str) File path of the zip file containing `keys.json`.

    Returns:
        Dict of credentials.
    """
    with py7zr.SevenZipFile(vault_file, mode='r', password=password) as f:
        archive = f.readall()
        d = json.load(archive['secrets.json'])
    return d


def update_config_from_vault(app: Flask) -> None:
    """
    This updates the state of the `app` to have the secrets from the vault. The
    vault also stores the "SECRET_KEY", which is a Flask builtin configuration
    variable (i.e. Flask treats the "SECRET_KEY" as special). So we also
    populate the "SECRET_KEY" in this step.

    If we fail to load the vault in development mode, then the user is warned
    that the vault was not loaded successfully. In production mode, failing to
    load the vault raises a RuntimeError.

    Args:
        app: A Flask application instance.
    """
    try:
        secrets = _load_secrets_from_vault(
            password=app.config['VAULT_PASSWORD'],
            vault_file=app.config['VAULT_FILE']
        )
        # Add 'SECRET_KEY', 'HOBOLINK_AUTH', AND 'TWITTER_AUTH' to the config.
        app.config.update(secrets)
    except (LZMAError, PasswordRequired, KeyError):
        msg = 'Unable to load the vault; bad password provided.'
        if app.config.get('VAULT_OPTIONAL'):
            print(f'Warning: {msg}')
            app.config['SECRET_KEY'] = os.urandom(16)
        else:
            raise RuntimeError(msg)
