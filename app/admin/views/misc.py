from flask_admin import expose, AdminIndexView as _AdminIndexView
from werkzeug.utils import redirect

from app.admin.base import BaseView
from app.data.globals import cache


class LogoutView(BaseView):
    """Returns a logout page that uses a jQuery trick to emulate a logout."""

    @expose('/')
    def index(self):
        body = self.render('admin/logout.html')
        status = 401
        cache.clear()
        return body, status


class AdminIndexView(BaseView, _AdminIndexView):
    @expose('/reset-cache')
    def reset_cache(self):
        cache.clear()
        return redirect('/admin')