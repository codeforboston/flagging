"""
This file handles the construction of the Flask application object.
"""
import os
import click
import json
import decimal

import datetime
from typing import Optional
from typing import Dict
from typing import Union

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from flask import current_app
from flask import Markup
from flask_caching import Cache
import py7zr
from lzma import LZMAError
from py7zr.exceptions import PasswordRequired

from .data.database import set_cache


def create_app(config: Optional[str] = None) -> Flask:
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
    app.config['CACHE_TYPE'] = 'simple'

    set_cache(Cache(app))

    from .config import get_config_from_env
    cfg = get_config_from_env(config or app.env)
    app.config.from_object(cfg)

    # Use the stuff inside `vault.zip` file to update the app.
    # Note: SOON TO BE DEPRECATED:
    update_config_from_vault(app)

    with app.app_context():
        register_extensions(app)
        register_blueprints(app)
        register_errorhandlers(app)
        register_jinja_env(app)
        register_commands(app)
        register_misc(app)

    return app


def register_extensions(app: Flask):
    """Register all extensions for the app."""
    from .data import db
    db.init_app(app)

    from .admin import init_admin
    init_admin(app)

    from .twitter import init_tweepy
    init_tweepy(app)

    from .blueprints.api import init_swagger
    init_swagger(app)


def register_blueprints(app: Flask):
    """Register the "blueprints." Blueprints are basically like mini web apps
    that can be joined to the main web app.
    """
    from .blueprints.api import bp as api_bp
    app.register_blueprint(api_bp)

    from .blueprints.flagging import bp as flagging_bp
    app.register_blueprint(flagging_bp)


def register_errorhandlers(app: Flask):
    """Error handlers are the way the app knows what to do in situations such as
    a Page Not Found error or a bad user/password input.
    """

    @app.errorhandler(401)
    def unauthorized(e):
        """When a 401 error is triggered, we ask the user to log in using HTTP
        Basic-Auth. If they input bad credentials we send the error page.
        """
        body = render_template(
            'error.html',
            title='Invalid Authorization',
            status_code=401,
            msg='Bad username or password provided.'
        )
        status = 401
        headers = {'WWW-Authenticate': 'Basic realm="Login Required"'}
        return body, status, headers

    @app.errorhandler(404)
    def not_found(e):
        """ Return error 404 """
        if request.path.startswith('/api/'):
            # we return a json saying so
            body = jsonify(Message='404 Error - Method Not Allowed')
        else:
            # if not, direct user to generic site-wide 404 page
            body = render_template(
                'error.html',
                title='Page not found',
                status_code=404,
                msg="This page doesn't exist!"
            )
        return body, 404

    @app.errorhandler(500)
    def internal_server_error(e):
        """ Return error 500 """
        app.logger.error(e)
        body = render_template(
            'error.html',
            title='Internal Server Error',
            status_code=500,
            msg='Something went wrong.'
        )
        return body, 500


def register_jinja_env(app: Flask):
    """Update the Jinja environment.

    This function mainly adds SVG files to the Jinja environment.

    It's much more flexible to work with raw SVG markup in an HTML file, rather
    than using an SVG file rendered as an image. (E.g. doing this allows us to
    change the colors using CSS.) This function loads SVG markup into our Jinja
    environment via reading from SVG files.
    """

    def _load_svg(file_name: str):
        """Load an svg file from `static/images/`."""
        with open(os.path.join(app.static_folder, 'images', file_name)) as f:
            s = f.read()
        return Markup(s)

    app.jinja_env.globals.update({
        'GITHUB_SVG': _load_svg('github.svg'),
        'TWITTER_SVG': _load_svg('twitter.svg'),
        'HAMBURGER_SVG': _load_svg('hamburger.svg'),
        'INFO_ICON': _load_svg('iconmonstr-info-6.svg')
    })


def register_commands(app: Flask):
    """All of these commands are related to the Database, and allow either the
    user or the Heroku Scheduler to make updates to the website via the command
    line.
    """

    @app.cli.command('create-db')
    @click.option('--overwrite/--no-overwrite',
                  default=False,
                  is_flag=True,
                  show_default=True,
                  help='If true, overwrite the database if it exists.')
    def create_db_command(overwrite: bool = False):
        """Create database (after verifying that it isn't already there)."""
        from .data.database import create_db
        create_db(overwrite=overwrite)

    @app.cli.command('init-db')
    @click.option('--pop/--no-pop',
                  default=True,
                  is_flag=True,
                  show_default=True,
                  help='If true, then do a db update when initializing the db.')
    @click.pass_context
    def init_db_command(ctx: click.Context, pop: bool):
        """Clear existing data and create new tables."""
        from .data.database import init_db
        init_db()
        click.echo('Initialized the database.')
        if pop:
            ctx.invoke(update_db_command)

    @app.cli.command('update-db')
    def update_db_command():
        """Update the database with the latest live data."""
        from .data.database import update_database
        update_database()
        click.echo('Updated the database successfully.')

    @app.cli.command('update-website')
    @click.pass_context
    def update_website_command(ctx: click.Context):
        """Updates the database, then Tweets a message."""
        from .data.live_website_options import LiveWebsiteOptions

        # Update the database
        ctx.invoke(update_db_command)

        # If the model updated and it's boating season, send a tweet.
        # Otherwise, do nothing.
        if (
                LiveWebsiteOptions.is_boating_season()
                and current_app.config['SEND_TWEETS']
        ):
            from .twitter import tweet_current_status
            msg = tweet_current_status()
            click.echo(f'Sent out tweet: {msg!r}')

    @app.cli.command('gen-mock-data')
    def generate_mock_data():
        """Create or update mock data.

        Mock data is stored in flagging_site/data/_store. Theese offline
        versions of the data are there for three reasons:

        1. Running demo/dev version of the site without credentials.
        2. Running demo/dev version of the site if the HOBOlink API ever breaks.
        3. For unit-testing some functionality of the website.

        This data is used for when the actual website when the `USE_MOCK_DATA`
        config variable is True. It is useful for dev, but it should never be
        used in production.
        """
        current_app.config['USE_MOCK_DATA'] = False

        def _format_path(fn: str) -> str:
            return os.path.join(current_app.config['DATA_STORE'], fn)

        from .data.usgs import get_live_usgs_data
        from .data.usgs import USGS_STATIC_FILE_NAME
        from .data.hobolink import get_live_hobolink_data
        from .data.hobolink import HOBOLINK_STATIC_FILE_NAME

        df_hobolink = get_live_hobolink_data()
        df_usgs = get_live_usgs_data()

        fname_hobolink = _format_path(HOBOLINK_STATIC_FILE_NAME)
        df_hobolink.to_pickle(fname_hobolink)
        click.echo(f'Wrote HOBOlink data to {fname_hobolink!r}')

        fname_usgs = _format_path(USGS_STATIC_FILE_NAME)
        df_usgs.to_pickle(fname_usgs)
        click.echo(f'Wrote USGS data to {fname_hobolink!r}')


def register_misc(app: Flask):
    """For things that don't neatly fit into the other "register" functions.

    This function updates the JSON encoder (i.e. what the REST API uses to
    ranslate Python objects to JSON), and adds defaults to the Flask shell.
    """

    # In most cases this is equivalent to:
    # >>> from flask.json import JSONEncoder
    # However this way of doing it is safe in case an extension overrides it.
    JSONEncoder = app.json_encoder

    class CustomJSONEncoder(JSONEncoder):
        """Add support for Decimal types and datetimes."""
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float(o)
            elif isinstance(o, datetime.date):
                return o.isoformat()
            else:
                return super().default(o)

    app.json_encoder = CustomJSONEncoder

    @app.shell_context_processor
    def make_shell_context():
        """This function makes some objects available in the Flask shell without
        the need to manually declare an import. This is just a convenience for
        using the Flask shell.
        """
        import pandas as pd
        import numpy as np
        from flask import current_app as app
        from .data import db
        from .data.hobolink import get_live_hobolink_data
        from .data.hobolink import request_to_hobolink
        from .data.predictive_models import process_data
        from .data.usgs import get_live_usgs_data
        from .data.usgs import request_to_usgs
        from .twitter import compose_tweet
        return locals()


# ==============================================================================
# vvv-- will soon be deprecating this stuff.


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
