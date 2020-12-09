from ..admin import ModelView
from .database import db
from distutils.util import strtobool


class LiveWebsiteOptions(db.Model):
    __tablename__ = 'live_website_options'
    boating_season = db.Column(db.String, default=True, primary_key=True)
    flagging_message = db.Column(db.Text, default=True)

class LiveWebsiteOptionsModelView(ModelView):
    can_create = False
    can_delete = False
    can_edit = True
    form_choices = {
        'boating_season': [
            ('true', 'true'),
            ('false', 'false'),
        ]
    }

    form_args = {
        'flagging_message': dict(label='Flagging Status Custom Message')
    }
    form_widget_args = {
        'flagging_message': dict(rows=12)
    }


def is_boating_season():
    a = LiveWebsiteOptions.query.first()
    if a.boating_season is None:
        return False
    return strtobool(a.boating_season)

def get_flagging_message():
    a = LiveWebsiteOptions.query.first()
    if a.flagging_message is None:
        print("got none")
        return ""
    print("got the message: " + ''.join(['<p>' + i + '</p>' for i in a.flagging_message.replace('\r','').split('\n\n')]))
    return ''.join(['<p>' + i + '</p>' for i in a.flagging_message.replace('\r','').split('\n\n')])