"""
This file handles the construction of the Flask application object.
"""
import os
import click
import time
import json
import zipfile
from typing import Optional

from flask import Flask

from .config import Config
from .config import get_config_from_env


def create_app(config: Optional[Config] = None) -> Flask:
    """Create and configure an instance of the Flask application. We use the
    `create_app` scheme over defining the `app` directly at the module level so
    the app isn't loaded immediately by importing the module.

    Args:
        config: (ClassVar) Can be either a string such as `config.BaseConfig`,
                or the actual object itself.
    Returns:
        The fully configured Flask app instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Get a config for the website. If one was not passed in the function, then
    # a config will be used depending on the `FLASK_ENV`.
    if not config:
        # Determine the config based on the `FLASK_ENV`.
        config = get_config_from_env(app.env)

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
    add_swagger_plugin_to_app(app)

    # Register the database commands
    from .data import db
    db.init_app(app)

    # Register auth
    from .auth import init_auth
    init_auth(app)

    # Register admin
    from .admin import init_admin
    init_admin(app)

    @app.before_request
    def before_request():
        from flask import g
        g.request_start_time = time.time()
        g.request_time = lambda: '%.3fs' % (time.time() - g.request_start_time)

    @app.cli.command('create-db')
    def create_db_command():
        """Create database (after verifying that it isn't already there)"""
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

    # Make a few useful functions available in Flask shell without imports
    @app.shell_context_processor
    def make_shell_context():
        import pandas as pd
        import numpy as np
        from .blueprints.flagging import get_data
        from .data import db
        from .data.hobolink import get_live_hobolink_data
        from .data.predictive_models import process_data
        from .data.usgs import get_live_usgs_data

        return {
            'pd': pd,
            'np': np,
            'db': db,
            'get_data': get_data,
            'get_live_hobolink_data': get_live_hobolink_data,
            'get_live_usgs_data': get_live_usgs_data,
            'process_data': process_data,
        }

    # And we're all set! We can hand the app over to flask at this point.
    return app


def add_swagger_plugin_to_app(app: Flask):
    """This function hnadles all the logic for adding Swagger automated
    documentation to the application instance.
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


def _load_keys_from_vault(
        vault_password: str,
        vault_file: str
) -> dict:
    """This code loads the keys directly from the vault zip file.

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


def update_config_from_vault(app: Flask) -> None:
    """
    This updates the state of the `app` to have the keys from the vault. The
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
        keys = _load_keys_from_vault(
            vault_password=app.config['VAULT_PASSWORD'],
            vault_file=app.config['VAULT_FILE']
        )
    except (RuntimeError, KeyError):
        msg = 'Unable to load the vault; bad password provided.'
        if app.env == 'production':
            raise RuntimeError(msg)
        else:
            print(f'Warning: {msg}')
            app.config['KEYS'] = None
            app.config['SECRET_KEY'] = os.urandom(16)
    else:
        app.config['KEYS'] = keys
        app.config['SECRET_KEY'] = keys['flask']['secret_key']
