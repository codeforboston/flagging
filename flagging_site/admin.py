import re
import io
import pandas as pd

from flask import Flask
from flask import request
from flask import Response
from flask import send_file
from flask import abort
from flask import url_for
from flask_admin import Admin
from flask_admin import BaseView as _BaseView
from flask_admin import expose
from flask_admin.contrib import sqla

from flask_basicauth import BasicAuth as _BasicAuth
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import ProgrammingError

from .data import db


# ==============================================================================
# Extensions
# ==============================================================================

class BasicAuth(_BasicAuth):
    """Uses HTTP BasicAuth to authenticate the admin user."""

    def get_login(self):
        """Check if properly authenticated. If not, then return a 401 error.
        The 401 error page will in turn prompt the user for a username and
        password.
        """
        if not self.authenticate():
            abort(401)


admin = Admin(template_mode='bootstrap3')
basic_auth = BasicAuth()


def init_admin(app: Flask):
    """Registers the Flask-Admin extensions to the app, and attaches the
    model views to the admin panel.

    Args:
        app: A Flask application instance.
    """
    basic_auth.init_app(app)
    admin.init_app(app)

    @app.before_request
    def auth_protect_admin_pages():
        """Authorize all paths that start with /admin/."""
        if re.match('^/admin(?:$|/+)', request.path):
            basic_auth.get_login()

    with app.app_context():
        # Register /admin sub-views
        from .data.manual_overrides import ManualOverridesModelView
        from .data.manual_overrides import ManualOverrides
        from .data.database import Boathouses

        admin.add_view(ModelView(Boathouses, db.session))
        admin.add_view(ManualOverridesModelView(ManualOverrides, db.session))
        admin.add_view(DatabaseView(name='Update Database', url='db/update',
                                    category='Manage DB'))
        admin.add_view(DownloadView(name='Download', url='db/download',
                                    category='Manage DB'))
        admin.add_view(LogoutView(name='Logout', url='logout'))


# ==============================================================================
# Base classes
# ==============================================================================


class BaseView(_BaseView):
    """All admin views should inherit from here. This base view adds required
    authorization to everything on the admin panel.
    """

    def is_accessible(self):
        return basic_auth.authenticate()

    def inaccessible_callback(self, name, **kwargs):
        """Ask for credentials when access fails."""
        return basic_auth.get_login()


class ModelView(sqla.ModelView, BaseView):
    """Base Admin view for SQLAlchemy models."""
    can_export = True
    export_types = ['csv']

    def __init__(self, model, *args, **kwargs):
        # Show all columns in form
        self.column_list = [c.key for c in model.__table__.columns]
        self.form_columns = self.column_list
        super().__init__(model, *args, **kwargs)


# ==============================================================================
# Views
# ==============================================================================


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        body = self.render('admin/logout.html')
        status = 401
        return body, status


class DatabaseView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/update.html')

    @expose('/run-update')
    def update_db(self):
        """When this function is called, the database updates. This function is
        designed to be available in the app during runtime, and is protected by
        BasicAuth so that only administrators can run it.
        """
        from .data.database import update_database
        update_database()

        # Notify the user that the update was successful, then redirect:
        return self.render('admin/redirect.html',
                           message='Database updated.',
                           redirect_to=url_for('admin.index'))


def _send_csv_attachment_of_dataframe(
        df: pd.DataFrame,
        file_name: str,
        date_prefix: bool = True
):
    strio = io.StringIO()
    df.to_csv(strio, index=False)

    # Convert to bytes
    bytesio = io.BytesIO()
    bytesio.write(strio.getvalue().encode('utf-8'))
    # seeking was necessary. Python 3.5.2, Flask 0.12.2
    bytesio.seek(0)
    strio.close()

    if date_prefix:
        todays_date = (
            pd.Timestamp('now', tz='UTC')
            .tz_convert('US/Eastern')
            .strftime('%Y_%m_%d')
        )
        file_name = f'{todays_date}-{file_name}'

    return send_file(
        bytesio,
        as_attachment=True,
        attachment_filename=file_name,
        mimetype='text/csv'
    )


class DownloadView(BaseView):
    TABLES = [
        'hobolink',
        'usgs',
        'processed_data',
        'model_outputs',
        'boathouses'
    ]

    @expose('/')
    def index(self):
        return self.render('admin/download.html')

    @expose('/csv/<sql_table_name>')
    def download_from_db(self, sql_table_name: str):
        # Do not ever delete the following two lines!
        # This is necessary for security.
        if sql_table_name not in self.TABLES:
            raise abort(404)

        from .data.database import execute_sql
        # WARNING:
        # Be careful when parameterizing queries like how we do it below.
        # The reason it's OK in this case is because users don't touch it.
        # However it is dangerous to do this in some other contexts.
        query = f'''SELECT * FROM {sql_table_name}'''
        try:
            df = execute_sql(query)
        except ProgrammingError:
            raise HTTPException(
                'Invalid SQL.',
                Response(
                    f'<b>Invalid SQL query:</b> <samp>{query}</samp>',
                    status=500
                )
            )

        return _send_csv_attachment_of_dataframe(
            df=df,
            file_name=f'{sql_table_name}.csv'
        )

    @expose('/csv/hobolink_source')
    def source_hobolink(self):
        from .data.hobolink import get_live_hobolink_data
        df_hobolink = get_live_hobolink_data('code_for_boston_export_90d')

        return _send_csv_attachment_of_dataframe(
            df=df_hobolink,
            file_name='hobolink_source.csv'
        )

    @expose('/csv/usgs_source')
    def source_usgs(self):
        from .data.usgs import get_live_usgs_data
        df_usgs = get_live_usgs_data(days_ago=90)

        return _send_csv_attachment_of_dataframe(
            df=df_usgs,
            file_name='usgs_source.csv'
        )

    @expose('/csv/model_outputs')
    def source_model_outputs(self):
        from .data.usgs import get_live_usgs_data
        df_usgs = get_live_usgs_data(days_ago=90)

        from .data.hobolink import get_live_hobolink_data
        df_hobolink = get_live_hobolink_data('code_for_boston_export_90d')

        from .data.predictive_models import process_data
        df = process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)

        return _send_csv_attachment_of_dataframe(
            df=df,
            file_name='model_outputs_source.csv'
        )

    @expose('/csv/model_outputs')
    def source_model_outputs(self):
        from .data.usgs import get_live_usgs_data
        df_usgs = get_live_usgs_data(days_ago=90)

        from .data.hobolink import get_live_hobolink_data
        df_hobolink = get_live_hobolink_data('code_for_boston_export_90d')

        from .data.predictive_models import process_data
        df = process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)

        from .data.predictive_models import all_models
        model_outs = all_models(df, rows=len(df))

        return _send_csv_attachment_of_dataframe(
            df=model_outs,
            file_name='model_outputs_source.csv'
        )
