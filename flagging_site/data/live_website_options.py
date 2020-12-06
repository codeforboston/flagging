from ..admin import ModelView
from .database import db
from distutils.util import strtobool


class LiveWebsiteOptions(db.Model):
    __tablename__ = 'live_website_options'
    boating_season = db.Column(db.String, default=True, primary_key=True)


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


def is_boating_season():
    a = LiveWebsiteOptions.query.first()
    if a.boating_season is None:
        return False
    return strtobool(a.boating_season)
