import markdown
from flask import Markup
from flask import redirect
from flask_admin import expose
from sqlalchemy.orm import Session

from ..admin import ModelView
from .database import db


class LiveWebsiteOptions(db.Model):
    __tablename__ = 'live_website_options'
    id = db.Column(db.Integer, primary_key=True)
    flagging_message = db.Column(db.Text, nullable=True)
    boating_season = db.Column(db.Boolean, default=True, nullable=False)

    @classmethod
    def is_boating_season(cls) -> bool:
        return bool(cls.query.first().boating_season)

    @classmethod
    def get_flagging_message(cls) -> Markup:
        msg = cls.query.first().flagging_message or ''
        return Markup(markdown.markdown(msg))


class LiveWebsiteOptionsModelView(ModelView):

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
        super().__init__(LiveWebsiteOptions, session, ignore_columns=['id'])

    @expose('/')
    def index(self):
        return redirect(self.url + '/edit/?id=1')
