from datetime import datetime
from typing import Any
from typing import Dict
from typing import List

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import select

from app.data.database import db


class Prediction(db.Model):
    __tablename__ = 'prediction'
    reach_id = db.Column(
        db.Integer, db.ForeignKey('reach.id'),
        primary_key=True, nullable=False)
    time = db.Column(db.DateTime, primary_key=True, nullable=False)
    probability = db.Column(db.Numeric)
    safe = db.Column(db.Boolean)

    reach = db.relationship('Reach', back_populates='predictions')

    @classmethod
    def _latest_ts_scalar_subquery(cls):
        return select(func.max(Prediction.time)).as_scalar()

    @classmethod
    def get_latest(cls, reach: int) -> 'Prediction':
        return (
            db.session
            .query(cls)
            .filter(and_(
                cls.time == cls._latest_ts_scalar_subquery(),
                cls.reach == reach))
            .first()
        )

    @classmethod
    def get_all_latest(cls) -> List['Prediction']:
        return (
            db.session
            .query(cls)
            .filter(cls.time == cls._latest_ts_scalar_subquery())
            .all()
        )

    def api_v1_to_dict(self) -> Dict[str, Any]:
        return {
            'probability': self.probability,
            'safe': self.safe,
            'time': self.time
        }


def get_latest_prediction_time() -> datetime:
    return db.session.query(func.max(Prediction.time)).scalar()
