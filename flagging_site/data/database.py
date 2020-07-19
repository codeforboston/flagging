"""
This file should handle all database connection stuff, namely: writing and
retrieving data.
"""
import os
import pandas as pd
from typing import Optional
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import ResourceClosedError


db = SQLAlchemy()


def execute_sql(query: str) -> Optional[pd.DataFrame]:
    """Execute arbitrary SQL in the database. This works for both read and write
    operations. If it is a write operation, it will return None; otherwise it
    returns a Pandas dataframe."""
    with db.engine.connect() as conn:
        res = conn.execute(query)
        try:
            df = pd.DataFrame(res.fetchall())
            df.columns = res.keys()
            return df
        except ResourceClosedError:
            return None


def execute_sql_from_file(file_name: str):
    path = os.path.join(current_app.config['QUERIES_DIR'], file_name)
    with current_app.open_resource(path) as f:
        return execute_sql(f.read().decode('utf8'))


def init_db():
    """Clear existing data and create new tables."""
    with current_app.app_context():

        # Read the `schema.sql` file, which initializes the database.
        execute_sql_from_file('schema.sql')

        update_database()


def update_database():
    """At the moment this overwrites the entire database. In the future we want
    this to simply update it.
    """

    options = {
        'con': db.engine,
        'index': False,
        'if_exists': 'replace'
    }

    # Populate the `usgs` table.
    from .usgs import get_live_usgs_data
    df_usgs = get_live_usgs_data()
    df_usgs.to_sql('usgs', **options)

    # Populate the `hobolink` table.
    from .hobolink import get_live_hobolink_data
    print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    df_hobolink = get_live_hobolink_data()
    print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    df_hobolink.to_sql('hobolink', **options)

    from .model import process_data
    df = process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
    df.to_sql('processed_data', **options)

    from .model import all_models
    model_outs = all_models(df)
    model_outs.to_sql('model_outputs', **options)
