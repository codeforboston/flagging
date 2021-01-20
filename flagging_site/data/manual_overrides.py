from typing import Set

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import TIMESTAMP
from sqlalchemy import VARCHAR
from sqlalchemy.orm import Session

from ..admin import ModelView
# from .database import Base
from .database import execute_sql_from_file
from .database import Boathouses


# class ManualOverrides(Base):
#     __tablename__ = 'cyano_overrides'
#     reach = Column(Integer, primary_key=True)
#     start_time = Column(TIMESTAMP, primary_key=True)
#     end_time = Column(TIMESTAMP, primary_key=True)
#     reason = Column(VARCHAR(255))


class ManualOverridesModelView(ModelView):
    
    form_choices = {
        'reason': [
            ('cyanobacteria', 'Cyanobacteria'),
            ('sewage', 'Sewage'),
            ('other', 'Other'),
        ]
    }

    def __init__(self, session: Session):
        super().__init__(
            Boathouses,
            session,
            endpoint='manual_overrides',
            name='Boathouses (including Manual Overrides)'
        )

# def get_currently_overridden_reaches() -> Set[int]:
#     return set(
#         execute_sql_from_file(
#             'currently_overridden_reaches.sql'
#         )["reach"].unique()
#     )
