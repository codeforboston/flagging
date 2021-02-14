from typing import Any
from typing import Dict
from typing import List

from sqlalchemy import func

from sqlalchemy.dialects.postgresql import aggregate_order_by


from .database import db
from .database import execute_sql


class Boathouse(db.Model):
    __tablename__ = 'boathouses'
    boathouse = db.Column(db.String(255), primary_key=True)
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
        return [i.to_dict() for i in res]

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
    def overridden_boathouses(cls):
        """This code is basically performing the following SQL:

            SELECT boathouse
            FROM boathouses
            WHERE overridden
            ORDER BY boathouse
        """
        res = (
            cls.query
            .filter(cls.overridden)
            .order_by(cls.boathouse)
            .all()
        )
        return [i.boathouse for i in res]

    @classmethod
    def get_flags(cls) -> Dict[str, bool]:
        return cls.query.all()


def get_latest_time():
    """
    Returns the latest time in the processed data
    """
    return execute_sql('SELECT MAX(time) FROM processed_data;').iloc[0]['max']


def get_overridden_boathouses():
    """
    Returns a ?list? of overriden boathouses
    """
    ret_val = []

    for bh in Boathouse.query.filter(Boathouse.overridden == True):
        ret_val.append(bh.boathouse)

    return ret_val



