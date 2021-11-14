from typing import Dict, Any, List

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import aggregate_order_by

from app.data import db
from app.data.processing.predictive_models import latest_model_outputs


class Boathouse(db.Model):
    __tablename__ = 'boathouses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    boathouse = db.Column(db.String(255))
    reach = db.Column(db.Integer, unique=False)
    latitude = db.Column(db.Numeric, unique=False)
    longitude = db.Column(db.Numeric, unique=False)
    overridden = db.Column(db.Boolean, unique=False, default=False)
    reason = db.Column(db.String(255), unique=False)

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
                cls.reach,
                cls.boathouse
            )
            .all()
        )

        df = latest_model_outputs()

        def _reach_is_safe(r: int) -> bool:
            return df.loc[df['reach'] == r, 'safe'].iloc[0]

        return_data = []
        for i in res:
            # remove the "id" field.
            bh = i.to_dict()
            bh['safe'] = \
                bool(_reach_is_safe(bh['reach']) and (not bh['overridden']))
            bh.pop('id')
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
                cls.reach,
                func.array_agg(
                    aggregate_order_by(
                        cls.boathouse,
                        cls.boathouse.asc()
                    )
                )
            )
            .group_by(cls.reach)
            .order_by(cls.reach)
            .all()
        )
        return {i[0]: i[1] for i in res}

    @classmethod
    def all_flags(cls) -> Dict[str, bool]:
        data = cls.all_boathouses_dict()
        return {bh['boathouse']: bh['safe'] for bh in data}