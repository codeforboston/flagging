"""
This file handles the construction of the Flask application object.
"""
import os
from typing import Type
from flask import Flask

from .data.keys import get_keys


def create_app(config: Type = None) -> Flask:
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
    if config:
        app.config.from_object(config)
    elif app.env == 'production':
        from .config import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif app.env == 'development':
        from .config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    else:
        raise ValueError('Bad config passed; the config must be `production` '
                         'or `development`.')

    # Use the stuff inside `vault.zip` file to update the app.
    update_config_from_vault(app)

    # Register the "blueprints." Blueprints are basically like mini web apps
    # that can be joined to the main web app. In this particular app, the way
    # blueprints are imported is: If BLUEPRINTS is in the config, then import
    # only from that list. Otherwise, import everything that's inside of
    # `blueprints/__init__.py`.
    from . import blueprints
    if app.config.get('BLUEPRINTS'):
        bp_list = app.config['BLUEPRINTS']
    else:
        bp_list = filter(lambda x: not x.startswith('_'), dir(blueprints))
    for bp_module in bp_list:
        app.register_blueprint(getattr(blueprints, bp_module).bp)

    # Register the database commands
    # from .data import db
    # db.init_app(app)

    # And we're all set! We can hand the app over to flask at this point.
    return app


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
        app.config['KEYS'] = get_keys()
    except (RuntimeError, KeyError):
        msg = 'Unable to load the vault; bad password provided.'
        if app.env == 'production':
            raise RuntimeError(msg)
        else:
            print(f'Warning: {msg}')
            app.config['KEYS'] = None
            app.config['SECRET_KEY'] = None
    else:
        app.config['SECRET_KEY'] = app.config['KEYS']['flask']['secret_key']


if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'
    os.environ['VAULT_PASSWORD'] = input('Enter vault password: ')
    app = create_app()
    app.run()
