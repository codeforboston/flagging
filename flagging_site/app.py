"""
This file handles the construction of the Flask application object.
"""
import os
import click
import decimal

import datetime
from typing import Optional
from functools import wraps

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from flask import current_app
from flask import Markup


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

    from .config import get_config_from_env
    cfg = get_config_from_env(config or app.env)
    app.config.from_object(cfg)

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
    from .data import db, cache
    db.init_app(app)
    cache.init_app(app)

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
    import hashlib

    def _load_svg(file_name: str):
        """Load an svg file from `static/images/`."""
        with open(os.path.join(app.static_folder, 'images', file_name)) as f:
            s = f.read()
        return Markup(s)

    def _md5_hash_file(file_name: str):
        """Create a MD5 hash for the CSS files to add to the URLs. This helps
        the browser to know whether you can use a cached version of the CSS
        file, or if it's been updated and the cached version should *not* be
        used. This method works in most browsers.
        """
        with open(os.path.join(app.static_folder, file_name)) as f:
            val = hashlib.md5(f.read().encode('utf8')).hexdigest()
        return val

    app.jinja_env.globals.update({
        'GITHUB_SVG': _load_svg('github.svg'),
        'TWITTER_SVG': _load_svg('twitter.svg'),
        'HAMBURGER_SVG': _load_svg('hamburger.svg'),
        'INFO_ICON': _load_svg('iconmonstr-info-9.svg'),
        'STYLE_CSS_MD5': _md5_hash_file('style.css'),
        'FLAGS_CSS_MD5': _md5_hash_file('flags.css'),
        'DATAFRAME_CSS_MD5': _md5_hash_file('dataframe.css')
    })


def register_commands(app: Flask):
    """All of these commands are related to the Database, and allow either the
    user or the Heroku Scheduler to make updates to the website via the command
    line.
    """

    def dev_only(func: callable) -> callable:
        """Decorator that ensures a command only runs in the development
        environment. Commands tagged with this will raise an error when you run
        them in production.
        """
        @wraps(func)
        def _wrap(*args, **kwargs):
            if current_app.env != 'development':
                raise RuntimeError(
                    'You can only run this in the development environment. '
                    'Make sure you set up the environment correctly if you '
                    'believe you are in dev.'
                )
            return func(*args, **kwargs)
        return _wrap

    @app.cli.command('create-db')
    @click.option('--overwrite/--no-overwrite',
                  default=False,
                  is_flag=True,
                  show_default=True,
                  help='If true, overwrite the database if it exists.')
    @dev_only
    def create_db_command(overwrite: bool = False):
        """Create the database."""
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

    @app.cli.command('delete-db')
    @click.option('--test-db', '-t',
                  default=False,
                  is_flag=True,
                  help='Deletes the database "flagging_test".')
    @dev_only
    def delete_db_command(test_db: bool):
        """Delete the database."""
        from .data.database import delete_db
        if test_db:
            dbname = 'flagging_test'
        else:
            dbname = current_app.config['POSTGRES_DBNAME']
        delete_db(dbname=dbname)

    @app.cli.command('update-db')
    def update_db_command():
        """Update the database with the latest live data."""
        from .data.database import update_db
        update_db()
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
    @dev_only
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

    @app.cli.command('pip-compile',
                     context_settings=dict(
                         ignore_unknown_options=True,
                         allow_extra_args=True,
                         help_option_names=[]))
    @click.pass_context
    @dev_only
    def pip_compile(ctx: click.Context):
        """Compile the .in files in /requirements.

        This command is for development purposes only.
        """
        import subprocess
        subprocess.call(['pip-compile', 'requirements/dev_osx.in', *ctx.args])
        subprocess.call(['pip-compile', 'requirements/dev_windows.in', *ctx.args])
        subprocess.call(['pip-compile', 'requirements/prod.in', *ctx.args])

    @app.cli.command('clear-cache')
    def clear_cache():
        """Clear the cache.

        Used in the production environment after every release. (Basically, if
        the code base changes, that might indicate the cache will be outdated).
        We do this instead of clearing the cache during `create_app()` because
        often when the app is spinning up, the previous cache is still valid and
        we'd still like to use that cache.

        See for more:

        https://devcenter.heroku.com/articles/release-phase
        """
        from .data import cache
        cache.clear()


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
