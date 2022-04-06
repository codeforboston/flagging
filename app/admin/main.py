import re

from flask import Flask
from flask import request
from flask import redirect
from flask_admin import Admin

from app.data.database import db
from app.admin.auth import basic_auth
from app.admin.views.data import DownloadView
from app.admin.views.data import DatabaseView
from app.admin.views.misc import LogoutView
from app.admin.views.misc import AdminIndexView
from app.admin.views.website_options import WebsiteOptionsModelView
from app.admin.views.boathouse import ManualOverridesModelView
from app.admin.views.boathouse import BoathouseModelView


admin = Admin(template_mode='bootstrap3', index_view=AdminIndexView())


def init_admin(app: Flask):
    """Registers the Flask-Admin extensions to the app, and attaches the
    model views to the admin panel.

    Args:
        app: A Flask application instance.
    """
    @app.before_request
    def auth_protect_admin_pages():
        """Authorize all paths that start with /admin/."""
        if re.match('^/admin(?:$|/+)', request.path):

            # Force HTTPS
            if not request.is_secure:
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)

            # Now check if logged in. (Error is raised if not authorized.)
            basic_auth.get_login()

    with app.app_context():
        basic_auth.init_app(app)
        admin.init_app(app)

        # Register /admin sub-views

        admin.add_view(WebsiteOptionsModelView(db.session))
        admin.add_view(ManualOverridesModelView(db.session))
        admin.add_view(BoathouseModelView(db.session))
        admin.add_view(DatabaseView(name='Update Database', url='db/update',
                                    category='Manage DB'))
        admin.add_view(DownloadView(name='Download', url='db/download',
                                    category='Manage DB'))
        admin.add_view(LogoutView(name='Logout', url='logout'))
