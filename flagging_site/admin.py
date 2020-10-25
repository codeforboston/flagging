import io
import pandas as pd
import datetime

from flask import Flask
from flask import redirect
from flask import request
from flask import Response
from flask import send_file
from flask import abort
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose
from flask_admin.contrib import sqla

from flask_basicauth import BasicAuth
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import ProgrammingError

from .data import db

admin = Admin(template_mode='bootstrap3')

basic_auth = BasicAuth()


# Taken from https://computableverse.com/blog/flask-admin-using-basicauth
class AuthException(HTTPException):
    def __init__(self, message):
        """HTTP Forbidden error that prompts for login"""
        super().__init__(message, Response(
            'You could not be authenticated. Please refresh the page.',
            status=401,
            headers={'WWW-Authenticate': 'Basic realm="Login Required"'}
        ))


def init_admin(app: Flask):
    """Registers the Flask-Admin extensions to the app, and attaches the
    model views to the admin panel.

    Args:
        app: A Flask application instance.
    """
    basic_auth.init_app(app)
    admin.init_app(app)

    @app.before_request
    def auth():
        """Authorize all paths that start with /admin/."""
        if request.path.startswith('/admin/'):
            validate_credentials()

    with app.app_context():
        # Register /admin sub-views
        from .data.cyano_overrides import ManualOverridesModelView
        admin.add_view(ManualOverridesModelView(db.session))

        # Database functions
        admin.add_view(DatabaseView(
            name='Update Database', url='db/update', category='Database'
        ))

        admin.add_view(DownloadView(
            name='Download', url='db/download', category='Database'
        ))

        admin.add_view(LogoutView(name='Logout'))


def validate_credentials() -> bool:
    """
    Protect admin pages with basic_auth.
    If logged out and current page is /admin/, then ask for credentials.
    Otherwise, raises HTTP 401 error and redirects user to /admin/ on the
    frontend (redirecting with HTTP redirect causes user to always be
    redirected to /admin/ even after logging in).

    We redirect to /admin/ because our logout method only works if the path to
    /logout is the same as the path to where we put in our credentials. So if
    we put in credentials at /admin/cyanooverride, then we would need to logout
    at /admin/cyanooverride/logout, which would be difficult to arrange. Instead,
    we always redirect to /admin/ to put in credentials, and then logout at
    /admin/logout.
    """
    if not basic_auth.authenticate():
        if request.path.startswith('/admin/'):
            raise AuthException('Not authenticated. Refresh the page.')
        else:
            raise HTTPException(
                'Attempted to visit admin page but not authenticated.',
                Response(
                    '''
                    Not authenticated. Navigate to /admin/ to login.
                    <script>window.location = "/admin/";</script>
                    ''',
                    status=401  # 'Forbidden' status
                )
            )
    return True


class AdminBaseView(BaseView):
    def is_accessible(self):
        return validate_credentials()

    def inaccessible_callback(self, name, **kwargs):
        """Ask for credentials when access fails"""
        return redirect(basic_auth.challenge())


# Adapted from https://computableverse.com/blog/flask-admin-using-basicauth
class AdminModelView(sqla.ModelView, AdminBaseView):
    """
    Extension of SQLAlchemy ModelView that requires BasicAuth authentication,
    and shows all columns in the form (including primary keys).
    """

    def __init__(self, model, *args, **kwargs):
        # Show all columns in form
        self.column_list = [c.key for c in model.__table__.columns]
        self.form_columns = self.column_list
        super().__init__(model, *args, **kwargs)


class LogoutView(AdminBaseView):
    @expose('/')
    def index(self):
        """
        To log out of basic auth for admin pages,
        we raise an HTTP 401 error (there isn't really a cleaner way)
        and then redirect on the frontend to home.
        """
        raise HTTPException(
            'Logged out.',
            Response(
                '''
                Successfully logged out.
                <script>window.location = "/";</script>
                ''',
                status=401
            )
        )


class DatabaseView(AdminBaseView):
    @expose('/')
    def index(self):
        return self.render('admin/update.html')

    @expose('/run-update')
    def update_db(self):
        """When this function is called, the database updates. This function is
        designed to be available in the app during runtime, and is protected by
        BasicAuth so that only administrators can run it.
        """
        # If auth passed, then update database.
        from .data.database import update_database
        update_database()

        # Notify the user that the update was successful, then redirect:
        return '''<!DOCTYPE html>
            <html>
                <body>
                    <script>
                        setTimeout(function(){
                            window.location.href = '/admin/';
                        }, 3000);
                    </script>
                    <p>Databases updated. Redirecting in 3 seconds...</p>
                </body>
            </html>
        '''


def _send_csv_attachment_of_dataframe(
        df: pd.DataFrame,
        file_name: str,
        date_prefix: bool = False
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


class DownloadView(AdminBaseView):
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
        # We are doing it like this to avoid needing to utilize sessions.
        query = f'''SELECT * FROM {sql_table_name}'''
        try:
            df = execute_sql(query)
        except ProgrammingError:
            raise HTTPException(
                'Invalid SQL.',
                Response(
                    f'<b>Invalid SQL query:</b> <tt>{query}</tt>',
                    status=500
                )
            )

        return _send_csv_attachment_of_dataframe(
            df=df,
            file_name=f'{sql_table_name}.csv',
            date_prefix=True
        )

    @expose('/csv/hobolink_source')
    def source_hobolink(self):
        from .data.hobolink import get_live_hobolink_data
        df_hobolink = get_live_hobolink_data('code_for_boston_export_90d')

        return _send_csv_attachment_of_dataframe(
            df=df_hobolink,
            file_name=f'hobolink_source.csv',
            date_prefix=True
        )

    @expose('/csv/usgs_source')
    def source_usgs(self):
        from .data.usgs import get_live_usgs_data
        df_usgs = get_live_usgs_data(days_ago=90)

        return _send_csv_attachment_of_dataframe(
            df=df_usgs,
            file_name=f'usgs_source.csv',
            date_prefix=True
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
            file_name=f'model_outputs_source.csv',
            date_prefix=True
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
            file_name=f'model_outputs_source.csv',
            date_prefix=True
        )


