from flask_admin import expose
from sqlalchemy.orm import Session
from werkzeug.utils import redirect

from app.admin.base import ModelView
from app.data import WebsiteOptions


class WebsiteOptionsModelView(ModelView):

    can_export = False
    # The following flags enforce the existence of only one set of options:
    can_create = False
    can_delete = False
    can_edit = True
    edit_modal = False

    edit_template = 'admin/edit_with_markdown.html'

    form_args = {'flagging_message': dict(label='Flagging Status Message')}
    form_widget_args = {'flagging_message': dict(rows=16)}

    def __init__(self, session: Session):
        super().__init__(WebsiteOptions, session, ignore_columns=['id'])

    @expose('/')
    def index(self):
        return redirect(self.url + '/edit/?id=1')
