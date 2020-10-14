import os
from inspect import cleandoc
from flask import Flask
from flask import redirect
from flask import request
from flask import Response
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose
from flask_admin.contrib import sqla
from werkzeug.exceptions import HTTPException

from flask_basicauth import BasicAuth
from werkzeug.exceptions import HTTPException

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

    # Add an endpoint to the app that lets the database be updated manually.
    # app.add_url_rule('/admin/update-db', 'admin.update_db', update_database_manually)

    with app.app_context():
        # Register /admin sub-views
        from .data.cyano_overrides import ManualOverridesModelView
        admin.add_view(ManualOverridesModelView(db.session))
        admin.add_view(DatabaseView(name='Update Database', endpoint='update-db', category='Database'))
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
