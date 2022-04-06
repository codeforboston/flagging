"""
This file handles the construction of the Flask application object.
"""
import datetime
import decimal
import hashlib
import os
from functools import wraps
from typing import Optional

import click
from flask import Flask
from flask import Markup
from flask import current_app
from flask import jsonify
from flask import render_template
from flask import request
from flask import send_file
from flask.cli import with_appcontext
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(config: Optional[str] = None) -> Flask:
    """Create and configure an instance of the Flask application.

    Args:
        config: (ClassVar) Can be either a string such as `config.BaseConfig`,
                or the actual object itself.

    Returns:
        The fully configured Flask app instance.
    """
    app = Flask(__name__)

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

    # Fix an issue with some flask-admin stuff redirecting to "http". Because
    # we use HTTP BasicAuth, the http scheme is bad during authorized sessions.
    # (This issue is specifically caused by Meinheld.)
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return app


def register_extensions(app: Flask):
    """Register all extensions for the app."""
    from app.data.database import db
    db.init_app(app)

    from app.data.globals import cache
    cache.init_app(app)

    from app.data.celery import init_celery
    init_celery(app)

    from app.admin.main import init_admin
    init_admin(app)

    from app.twitter import init_tweepy
    init_tweepy(app)

    from app.blueprints.api_v1 import init_swagger
    init_swagger(app)

    from app.mail import mail
    mail.init_app(app)

    cors = CORS(resources={
        '/api/*': {'origins': '*'},
        '/flags': {'origins': '*'}
    })
    cors.init_app(app)


def register_blueprints(app: Flask):
    """Register the "blueprints." Blueprints are basically like mini web apps
    that can be joined to the main web app.
    """
    app.url_map.strict_slashes = False

    from app.blueprints.api_v1 import bp as api_bp
    app.register_blueprint(api_bp)

    from app.blueprints.frontend import bp as flagging_bp
    app.register_blueprint(flagging_bp)

    @app.route('/favicon.ico')
    def favicon():
        return send_file('static/favicon/favicon.ico')


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
        """Return a 404 if a page isn't found."""
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

    @app.template_filter('strftime')
    def strftime(
            value: datetime.datetime,
            fmt: str = "%Y-%m-%d %I:%M:%S %p"
    ) -> str:
        """Render datetimes with a default format for the frontend."""
        return value.strftime(fmt)

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

    def get_widget_filename(version: int = None):
        """Function that gets stuck inside the Jinja env to get the proper file
        for the widget. Why parametrize the widget filename? Because there may
        be a reason we need to swap to an older version, and this makes it
        easier to do that. (Just swap the config variable.) Unlikely to matter,
        but if it ever does...
        """
        if version is None:
            version = current_app.config['DEFAULT_WIDGET_VERSION']
        v = str(version).zfill(2)
        return f'_flag_widget_v{v}.html'

    import os.path as op

    def read_file(filename: str):
        with open(op.join('app', 'templates', filename), 'r') as f:
            s = f.read()
        return s

    app.jinja_env.globals.update({
        'read': read_file,
        # SVG files
        'GITHUB_SVG': _load_svg('github.svg'),
        'TWITTER_SVG': _load_svg('twitter.svg'),
        'HAMBURGER_SVG': _load_svg('hamburger.svg'),
        'INFO_ICON': _load_svg('iconmonstr-info-9.svg'),

        # MD5 hashes
        'STYLE_CSS_MD5': _md5_hash_file('style.css'),
        'FLAGS_CSS_MD5': _md5_hash_file('flags.css'),
        'DATAFRAME_CSS_MD5': _md5_hash_file('dataframe.css'),

        # Other stuff
        'get_widget_filename': get_widget_filename,
        'MAPBOX_ACCESS_TOKEN': app.config['MAPBOX_ACCESS_TOKEN']
    })


def register_commands(app: Flask):
    """All of these commands are related to the Database, and allow either the
    user or the Heroku Scheduler to make updates to the website via the command
    line.
    """

    from .mail import mail_on_fail

    def dev_only(func: callable) -> callable:
        """Decorator that ensures a function only runs in the development
        environment. Commands tagged with this will raise an error when you run
        them in production. This is a safeguard against accidentally doing
        something you shouldn't be doing.
        """

        @wraps(func)
        def _wrap(*args, **kwargs):
            if current_app.env not in ['development', 'testing']:
                raise RuntimeError(
                    'You can only run this in the development environment.'
                    ' Make sure you set up the environment correctly if you'
                    ' believe you are in dev.'
                )
            return func(*args, **kwargs)

        return _wrap

    @app.cli.command('update-db')
    @click.option('--async', 'async_',
                  is_flag=True,
                  default=False,
                  help='If set, then run this command in Celery.'
                       ' This can help save a bit of money on Heroku compute.')
    @with_appcontext
    @mail_on_fail
    def update_db_command(async_: bool = False):
        """Update the database with the latest live data."""
        from app.data.celery import update_db_task
        if async_:
            res = update_db_task.delay()
            click.echo(f'Started update database task ({res.id!r}).')
        else:
            click.echo('Updating the database...')
            update_db_task.run()
            click.echo('Updated the database successfully.')

    @app.cli.command('update-website')
    @click.option('--async', 'async_',
                  is_flag=True,
                  default=False,
                  help='If set, then run this command in Celery.'
                       ' This can help save a bit of money on Heroku compute.')
    @mail_on_fail
    def update_website_command(async_: bool = False):
        """Updates the database, then Tweets a message."""
        from app.data.celery import update_website_task
        if async_:
            res = update_website_task.delay()
            click.echo(f'Started update website task ({res.id!r}).')
        else:
            click.echo('Updating the website...')
            update_website_task.run()
            click.echo('Updated the website successfully.')

    @app.cli.command('gen-mock-data')
    @dev_only
    def generate_mock_data():
        """Create or update mock data.

        Mock data is stored in app/data/_store. Theese offline
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

        from app.data.processing.hobolink import HOBOLINK_STATIC_FILE_NAME
        from app.data.processing.hobolink import get_live_hobolink_data
        from app.data.processing.usgs import USGS_STATIC_FILE_NAME
        from app.data.processing.usgs import get_live_usgs_data

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
        subprocess.call(['pip-compile', 'requirements.in', *ctx.args])
        subprocess.call(['pip-compile', 'docs/requirements.in', *ctx.args])

    @app.cli.command('email-90-day-data')
    @click.option('--async', 'async_',
                  is_flag=True,
                  default=False,
                  help='If set, then run this command in Celery.'
                       ' This can help save a bit of money on Heroku compute.')
    @mail_on_fail
    def email_90_day_data_command(async_: bool = False):
        from app.data.celery import send_database_exports_task
        if async_:
            res = send_database_exports_task.delay()
            click.echo(f'Started send database exports task ({res.id!r}).')
        else:
            click.echo('Sending database dump email...')
            send_database_exports_task.run()
            click.echo('Sent the database export email successfully.')

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
        from app.data.globals import cache
        cache.clear()

    from celery.bin.celery import celery as celery_cmd
    app.cli.add_command(celery_cmd)


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
        import numpy as np  # noqa: F401
        import pandas as pd  # noqa: F401
        from flask import current_app as app  # noqa: F401
        from flask.testing import FlaskClient  # noqa: F401

        from app.data import db  # noqa: F401
        from app.data.celery import celery_app  # noqa: F401
        from app.data.database import execute_sql  # noqa: F401
        from app.data.globals import boathouses  # noqa: F401
        from app.data.globals import reaches  # noqa: F401
        from app.data.globals import website_options  # noqa: F401
        from app.data.processing.hobolink import \
            get_live_hobolink_data  # noqa: F401
        from app.data.processing.hobolink import \
            request_to_hobolink  # noqa: F401
        from app.data.processing.predictive_models import \
            process_data  # noqa: F401
        from app.data.processing.usgs import get_live_usgs_data  # noqa: F401
        from app.data.processing.usgs import request_to_usgs  # noqa: F401
        from app.twitter import compose_tweet  # noqa: F401

        def get_auth():
            from base64 import b64encode
            user = app.config['BASIC_AUTH_USERNAME']
            pw = app.config['BASIC_AUTH_PASSWORD']
            auth = f'{user}:{pw}'
            auth_encoded = b64encode(auth.encode()).decode('utf-8')
            return {'Authorization': f'Basic {auth_encoded}'}

        class _AuthorizedClient(FlaskClient):

            def __init__(self, *args, **kwargs):
                self._auth = get_auth()
                super().__init__(*args, **kwargs)

            def open(self, *args, **kwargs):
                kwargs.setdefault('headers', self._auth)
                return super().open(*args, **kwargs)

        app.test_client_class = _AuthorizedClient
        client = app.test_client()

        return locals()
