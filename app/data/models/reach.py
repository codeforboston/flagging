

from typing import Dict, Any, List

from sqlalchemy import func
from sqlalchemy import and_, not_
from sqlalchemy.sql.operators import ColumnOperators
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import aggregate_order_by

from app.data.database import db
from app.data.processing.predictive_models import latest_model_outputs


class Reach(db.Model):
    __tablename__ = 'reach'
    id: int = db.Column(db.Integer, primary_key=True, unique=True)
    boathouses: List['Boathouse'] = db.relationship(
        'Boathouse',
        order_by='asc(Boathouse.name)',
        back_populates='reach')
    predictions: List['Prediction'] = db.relationship(
        'Prediction',
        order_by='asc(Prediction.time)',
        uselist=True,
        back_populates='reach')

    @classmethod
    def get_all(cls) -> List['Reach']:
        return db.session.query(cls).order_by(cls.id).all()
