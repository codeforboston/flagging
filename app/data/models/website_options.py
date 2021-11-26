from typing import Optional
import markdown
from markupsafe import Markup
from app.data.database import db


class WebsiteOptions(db.Model):
    __tablename__ = 'live_website_options'
    id: int = db.Column(db.Integer, primary_key=True)
    flagging_message: Optional[str] = db.Column(db.Text, nullable=True)
    boating_season: bool = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def rendered_flagging_message(self) -> str:
        if self.flagging_message is None:
            return ''
        else:
            return Markup(markdown.markdown(self.flagging_message))

    @classmethod
    def get(cls) -> 'WebsiteOptions':
        return db.session.query(cls).first()
