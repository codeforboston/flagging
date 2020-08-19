from typing import Set

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

from .database import Base
from .database import execute_sql_from_file

class CyanoOverrides(Base):
    __tablename__ = 'cyano_overrides'
    reach = Column(Integer, primary_key=True)
    start_time = Column(TIMESTAMP, primary_key=True)
    end_time = Column(TIMESTAMP, primary_key=True)

def get_currently_overridden_reaches() -> Set[int]:
    return set(
        execute_sql_from_file(
            'currently_overridden_reaches.sql'
        )["reach"].unique()
    )
