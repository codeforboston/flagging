from ..admin import ModelView
from .database import db
from flask import Markup
from sqlalchemy.orm import Session


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
        # Paragraphs (delimited by double newlines) are wrapped in <p> tags
        # We remove `\r` (carriage return) to make identifying double newlines easier.
        return Markup(''.join([
            '<p>' + i + '</p>'
            for i in msg.replace('\r', '').split('\n\n')
        ]))


class LiveWebsiteOptionsModelView(ModelView):
    can_export = False
    # The following flags enforce the existence of only one set of options:
    can_create = False
    can_delete = False
    can_edit = True

    form_args = {'flagging_message': dict(label='Flagging Status Message')}
    form_widget_args = {'flagging_message': dict(rows=12)}

    def __init__(self, session: Session):
        super().__init__(LiveWebsiteOptions, session, ignore_columns=['id'])
