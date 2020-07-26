"""
This file handles the construction of the Flask application object.
"""
import os
from typing import Optional
from flask import Flask

from .data.keys import get_keys
from .config import Config
from .config import get_config_from_env
from flasgger import Swagger


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
    from . import blueprints
    register_blueprints_from_module(app, blueprints)

    #Swagger configs for flasgger
    swagger_config = {
        "headers": [
        ],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        # "static_folder": "static",  # must be set by user
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }

    swagger = Swagger(app, config=swagger_config)

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


def register_blueprints_from_module(app: Flask, module: object) -> None:
    """
    This function looks within the submodules of a module for objects
    specifically named `bp`. It then assumes those objects are blueprints, and
    registers them to the app.

    Args:
        app: (Flask) Flask instance to which we will register blueprints.
        module: (object) A module that contains submodules which themselves
                contain `bp` objects.
    """
    if app.config.get('BLUEPRINTS'):
        blueprint_list = app.config['BLUEPRINTS']
    else:
        blueprint_list = filter(lambda x: not x.startswith('_'), dir(module))
    for submodule in blueprint_list:
        app.register_blueprint(getattr(module, submodule).bp)


if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'
    os.environ['VAULT_PASSWORD'] = input('Enter vault password: ')
    app = create_app()
    app.run()
