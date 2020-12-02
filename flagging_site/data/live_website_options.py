from typing import Set
from sqlalchemy import Column
from sqlalchemy import BOOLEAN
from sqlalchemy import INTEGER
from sqlalchemy import TIMESTAMP
from sqlalchemy import VARCHAR
from sqlalchemy import String
from wtforms import SelectField
from wtforms.validators import InputRequired
from ..admin import AdminModelView
from .database import Base
from .database import db
from .database import execute_sql_from_file
from distutils.util import strtobool

class LiveWebsiteOptions(db.Model):
    __tablename__ = 'live_website_options'
    id = db.Column(INTEGER, primary_key=True)
    boating_season = db.Column(db.String, default=True)

class LiveWebsiteOptionsModelView(AdminModelView):
    can_create = False
    can_delete = False
    can_edit = True
    form_choices = {
        'boating_season': [
            ('true', 'true'),
            ('false', 'false'),
        ]
    }

    def __init__(self, session):
        super().__init__(LiveWebsiteOptions, session)

def is_boating_season():
    a = LiveWebsiteOptions.query.first()
    if a.boating_season is None:
        return False
    return strtobool(a.boating_season)