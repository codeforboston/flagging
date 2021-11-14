import markdown
from markupsafe import Markup

from app.data import db


class WebsiteOptions(db.Model):
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
