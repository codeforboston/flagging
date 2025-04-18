from datetime import datetime
from typing import Any
from typing import Dict
from typing import List

import pytz
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import select

from app.data.database import db


class Prediction(db.Model):
    __tablename__ = "prediction"
    reach_id = db.Column(db.Integer, db.ForeignKey("reach.id"), primary_key=True, nullable=False)
    time = db.Column(db.DateTime, primary_key=True, nullable=False)
    predicted_ecoli_cfu_100ml = db.Column(db.Numeric)
    # probability = db.Column(db.Numeric)
    safe = db.Column(db.Boolean)

    reach = db.relationship("Reach", back_populates="predictions")

    @property
    def local_time(self) -> datetime:
        return self.time.astimezone(pytz.timezone("US/Eastern"))

    @property
    def predicted_ecoli_cfu_100ml_rounded(self) -> float:
        return round(self.predicted_ecoli_cfu_100ml, 1)

    # @property
    # def probability_rounded_and_formatted(self) -> str:
    #     return str(round(self.probability * 100, 1)) + "%"

    @classmethod
    def _latest_ts_scalar_subquery(cls):
        return select(func.max(Prediction.time)).scalar_subquery()

    @classmethod
    def get_latest(cls, reach: int) -> "Prediction":
        return (
            db.session.query(cls)
            .filter(and_(cls.time == cls._latest_ts_scalar_subquery(), cls.reach == reach))
            .first()
        )

    @classmethod
    def get_all_latest(cls) -> List["Prediction"]:
        return db.session.query(cls).filter(cls.time == cls._latest_ts_scalar_subquery()).all()

    # def api_v1_to_dict(self) -> Dict[str, Any]:
    #     return {"prediction": float(self.probability), "safe": self.safe, "time": self.time}
    def api_v1_to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": float(self.predicted_ecoli_cfu_100ml),
            "safe": self.safe,
            "time": self.time,
        }


def get_latest_prediction_time() -> datetime:
    return db.session.query(func.max(Prediction.time)).scalar()
