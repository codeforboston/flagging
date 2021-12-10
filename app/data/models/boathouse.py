from typing import Dict, Any, List

from sqlalchemy import and_, not_
from sqlalchemy.sql.operators import ColumnOperators
from sqlalchemy.ext.hybrid import hybrid_property

from app.data.database import db
from app.data.models.prediction import Prediction


# Todo: should update db.String(255) to db.Text.
class Boathouse(db.Model):
    __tablename__ = 'boathouse'

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name: str = db.Column(db.String(255), unique=True)
    reach_id: int = db.Column(db.Integer, db.ForeignKey('reach.id'))
    latitude: float = db.Column(db.Numeric)
    longitude: float = db.Column(db.Numeric)
    overridden: bool = db.Column(db.Boolean, default=False)
    reason: str = db.Column(db.String(255))
    reach = db.relationship('Reach', back_populates='boathouses')

    latest_prediction: Prediction = db.relationship(
        'Prediction',
        # Join on the latest prediction per reach.
        primaryjoin='and_('
                    'Prediction.reach_id == foreign(Boathouse.reach_id),'
                    ' Prediction.time == select([func.max(Prediction.time)]).as_scalar()'
                    ')',
        lazy='subquery',
        viewonly=True,
        sync_backref=False,
        backref=db.backref('boathouses', lazy='subquery')
    )

    all_predictions: List[Prediction] = db.relationship(
        'Prediction',
        primaryjoin='Prediction.reach_id == foreign(Boathouse.reach_id)',
        lazy='subquery',
        viewonly=True,
        uselist=True
    )

    @hybrid_property
    def safe(self) -> bool:
        return self.latest_prediction.safe and not self.overridden

    @safe.expression
    def safe(cls) -> ColumnOperators:
        return and_(cls.latest_prediction.safe, not_(cls.overridden))

    @classmethod
    def get_all(cls) -> List['Boathouse']:
        return db.session.query(cls).order_by(cls.reach_id, cls.name).all()

    def api_v1_to_dict(self) -> Dict[str, Any]:
        """Represents a Boathouse object as a dict."""
        return {
            'boathouse': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'overridden': self.overridden,
            'reach': self.reach_id,
            'reason': self.reason,
            'safe': self.safe
        }
