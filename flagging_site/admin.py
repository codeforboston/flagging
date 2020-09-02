import os

from flask import Flask
from flask import redirect
from flask import request
from flask import Response
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose
from flask_admin.contrib import sqla
from werkzeug.exceptions import HTTPException

from .auth import AuthException
from .auth import basic_auth
from .data import db


admin = Admin(template_mode='bootstrap3')

def init_admin(app: Flask):
    with app.app_context():
        # Register /admin
        admin.init_app(app)

        # Register /admin sub-views
        from .data.cyano_overrides import CyanoOverridesModelView
        admin.add_view(CyanoOverridesModelView(db.session))
        
        admin.add_view(LogoutView(name="Logout"))


# Adapted from https://computableverse.com/blog/flask-admin-using-basicauth
class AdminModelView(sqla.ModelView):
    """
    Extension of SQLAlchemy ModelView that requires BasicAuth authentication,
    and shows all columns in the form (including primary keys).
    """

    def __init__(self, model, *args, **kwargs):
        # Show all columns in form
        self.column_list = [c.key for c in model.__table__.columns]
        self.form_columns = self.column_list

        super().__init__(model, *args, **kwargs)

    def is_accessible(self):
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
            if '/admin/' == request.path:
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
        else:
            return True

    def inaccessible_callback(self, name, **kwargs):
        """Ask for credentials when access fails"""
        return redirect(basic_auth.challenge())


class LogoutView(BaseView):
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
