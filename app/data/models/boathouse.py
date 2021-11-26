from typing import Dict, Any, List

from sqlalchemy import func
from sqlalchemy import and_, not_
from sqlalchemy.sql.operators import ColumnOperators
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import aggregate_order_by

from app.data.database import db
from app.data.models.prediction import Prediction
from app.data.processing.predictive_models import latest_model_outputs


# Todo: should update db.String(255) to db.Text.
class Boathouse(db.Model):
    __tablename__ = 'boathouses'
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
        viewonly=True,
        lazy='subquery',
        backref=db.backref('boathouses', lazy='subquery')
    )
    #
    # all_predictions: List[Prediction] = db.relationship(
    #     'Prediction',
    #     primaryjoin='Prediction.reach == Boathouse.reach',
    #     viewonly=True,
    #     uselist=True
    # )

    @hybrid_property
    def safe(self) -> bool:
        return self.latest_prediction.safe and not self.overridden

    @safe.expression
    def safe(cls) -> ColumnOperators:
        return and_(cls.latest_prediction.safe, not_(cls.overridden))

    @classmethod
    def get_all(cls) -> List['Boathouse']:
        return db.session.query(cls).order_by(cls.reach_id, cls.name).all()

    def to_dict(self) -> Dict[str, Any]:
        """Represents a Boathouse object as a dict."""
        return {
            k: getattr(self, k)
            for k in self.__table__.columns.keys()
        }

    @classmethod
    def all_boathouses_dict(cls) -> List[Dict[str, Any]]:
        """Descriptive data about the boathouses, presented as a list of dicts.
        This can be queried via the REST API.

        You can think of this function as performing the following query:

            SELECT reach, boathouse, latitude, longitude, overriden, reason
            FROM boathouses
            ORDER BY reach, boathouse
        """
        res = (
            cls.query
                .order_by(
                    cls.reach_id,
                    cls.name
                )
                .all()
        )

        df = latest_model_outputs()

        def _reach_is_safe(r: int) -> bool:
            return df.loc[df['reach_id'] == r, 'safe'].iloc[0]

        return_data = []
        for i in res:
            # remove the "id" field.
            bh = i.to_dict()
            bh['safe'] = \
                bool(_reach_is_safe(bh['reach_id']) and (not bh['overridden']))
            bh.pop('id')

            # `reach_id` --> `reach` for backwards compatibility with api v1
            bh['reach'] = bh['reach_id']
            bh.pop('reach_id')

            # `name` --> `boathouse` for backwards compatibility with api v1
            bh['boathouse'] = bh['name']
            bh.pop('name')

            return_data.append(bh)



        return return_data

    @classmethod
    def boathouse_names_by_reach(cls) -> Dict[int, List[str]]:
        """Returns a dict with the following format:

          - key = reach number
          - value = list of boathouses in that reach

        The code is a bit hard to read, but it is basically performing the
        following SQL query before turning it into a dict:

            SELECT
              reach,
              array_agg(boathouse ORDER BY boathouse ASC) AS boathouse_array
            FROM boathouses
            GROUP BY reach
            ORDER BY reach
        """
        res = (
            db.session.query(
                cls.reach_id,
                func.array_agg(
                    aggregate_order_by(
                        cls.name,
                        cls.name.asc()
                    )
                )
            )
            .group_by(cls.reach_id)
            .order_by(cls.reach_id)
            .all()
        )
        return {i[0]: i[1] for i in res}

    @classmethod
    def all_flags(cls) -> Dict[str, bool]:
        data = cls.all_boathouses_dict()
        return {bh['boathouse']: bh['safe'] for bh in data}
