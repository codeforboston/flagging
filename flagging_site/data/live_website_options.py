from ..admin import ModelView
from .database import db
from distutils.util import strtobool
from sqlalchemy.orm import Session


class LiveWebsiteOptions(db.Model):
    __tablename__ = 'live_website_options'
    id = db.Column(db.Integer, primary_key=True)
    boating_season = db.Column(db.Boolean, default=True, nullable=False)

    @classmethod
    def is_boating_season(cls) -> bool:
        return bool(cls.query.first().boating_season)


class LiveWebsiteOptionsModelView(ModelView):
    can_export = False
    # The following flags enforce the existence of only one set of options:
    can_create = False
    can_delete = False
    can_edit = True

    def __init__(self, session: Session):
        super().__init__(LiveWebsiteOptions, session, ignore_columns=['id'])
