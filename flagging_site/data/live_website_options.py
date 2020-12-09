from ..admin import ModelView
from .database import db
from distutils.util import strtobool


class LiveWebsiteOptions(db.Model):
    __tablename__ = 'live_website_options'
    boating_season = db.Column(db.String, default=True, primary_key=True)
    flagging_message = db.Column(db.VARCHAR(32767), default=True)

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

    form_widget_args = {
        'description': {
            'rows': 20,
            'style': 'color: black'
        }
    }


def is_boating_season():
    a = LiveWebsiteOptions.query.first()
    if a.boating_season is None:
        return False
    return strtobool(a.boating_season)
