from typing import List
from typing import Optional

from app.data.database import db


class Reach(db.Model):
    __tablename__ = "reach"
    __allow_unmapped__ = True  # SQLA 3.0 compat. Todo: replace with Mapped[]

    id: int = db.Column(db.Integer, primary_key=True, unique=True)
    boathouses: List["Boathouse"] = db.relationship(  # noqa: F821
        "Boathouse", order_by="asc(Boathouse.name)", back_populates="reach"
    )
    predictions: List["Prediction"] = db.relationship(  # noqa: F821
        "Prediction", order_by="asc(Prediction.time)", uselist=True, back_populates="reach"
    )

    @classmethod
    def get_all(cls) -> List["Reach"]:
        return db.session.query(cls).order_by(cls.id).all()

    def predictions_last_x_hours(self, x: Optional[int] = None) -> List["Prediction"]:  # noqa: F821
        if x is None:
            return self.predictions
        from app.data.models.prediction import Prediction

        return (
            db.session.query(Prediction)
            .filter(Prediction.reach_id == self.id)
            .order_by(Prediction.time.desc())
            .limit(x)
            .all()
        )
