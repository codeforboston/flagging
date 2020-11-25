from typing import Set

from sqlalchemy import Column
from sqlalchemy import BOOLEAN
from sqlalchemy import Integer
from sqlalchemy import TIMESTAMP
from sqlalchemy import VARCHAR
from sqlalchemy import String

from ..admin import AdminModelView
from .database import Base
from .database import LiveWebsiteOpts
from .database import execute_sql_from_file
from distutils.util import strtobool


class LiveWebsiteOptions(Base):
    __tablename__ = 'live_website_options'
    boating_season = Column(VARCHAR(255), primary_key=True)


class LiveWebsiteOptionsModelView(AdminModelView):
    form_choices = {
        'boating_season': [
            ('true', 'True'),
            ('false', 'False'),
        ]
    }
    def __init__(self, session):
        super().__init__(LiveWebsiteOptions, session)


def is_boating_season():
    df = execute_sql_from_file('boating_season.sql')
    if df is None:
        return False
    print("got df")
    print(df["boating_season"])
    dfSet = set(df)
    print("df set: ")
    print(dfSet)
    print(len(LiveWebsiteOpts.query.all()))
    a = LiveWebsiteOpts.query.first()
    print("hey hey hey")
    print(a.boating_season)
    return strtobool(a.boating_season)
