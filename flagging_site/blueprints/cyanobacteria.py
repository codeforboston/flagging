import pandas as pd
from flask import Blueprint
from ..data.usgs import get_usgs_data
from ..data import db
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import create_engine

bp = Blueprint('cyanobacteria', __name__, url_prefix='/cyanobacteria')


@bp.route('/')
def index() -> str:
    df = get_usgs_data()
    try:
        df.to_sql('raw_usgs', con=db.engine, if_exists='replace')
    except ValueError:
        pass
    df = pd.read_sql('''select * from raw_usgs''', con=db.engine)
    print(df)
    return 'hello world'