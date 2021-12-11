"""This file handles all database stuff, i.e. writing and retrieving data to
the Postgres database. Note that of the functionality in this file is available
directly in the command line.

While the app is running, the database connection is managed by SQLAlchemy. The
`db` object defined near the top of the file is that connector, and is used
throughout both this file and other files in the code base. The `db` object is
connected to the actual database in the `create_app` function: the app instance
is passed in via `db.init_app(app)`, and the `db` object looks for the config
variable `SQLALCHEMY_DATABASE_URI`.
"""
import os
from typing import Optional

import pandas as pd
from flask import current_app

from flask_sqlalchemy import SQLAlchemy
from flask_postgres import init_db_callback
from sqlalchemy.exc import ResourceClosedError


db = SQLAlchemy()


def execute_sql(query: str) -> Optional[pd.DataFrame]:
    """Execute arbitrary SQL in the database. This works for both read and
    write operations. If it is a write operation, it will return None;
    otherwise it returns a Pandas dataframe.

    Args:
        query: (str) A string that contains the contents of a SQL query.

    Returns:
        Either a Pandas Dataframe the selected data for read queries, or None
        for write queries.
    """
    with db.engine.connect() as conn:
        res = conn.execute(query)
        try:
            df = pd.DataFrame(
                res.fetchall(),
                columns=res.keys()
            )
            return df
        except ResourceClosedError:
            return None


def execute_sql_from_file(file_name: str) -> Optional[pd.DataFrame]:
    """Execute SQL from a file in the `QUERIES_DIR` directory, which should be
    located at `app/data/queries`.

    Args:
        file_name: (str) A file name inside the `QUERIES_DIR` directory. It
                   should be only the file name alone and not the full path.

    Returns:
        Either a Pandas Dataframe the selected data for read queries, or None
        for write queries.
    """
    path = os.path.join(current_app.config['QUERIES_DIR'], file_name)
    with current_app.open_resource(path) as f:
        s = f.read().decode('utf8')
        return execute_sql(s)


@init_db_callback
def init_db():
    """This data clears and then populates the database from scratch. You only
    need to run this function once per instance of the database.
    """

    # This file creates tables for all of the tables that don't have
    # SQLAlchemy models associated with this.
    # Somewhat of a formality because we'll overwrite most of these
    # soon.
    execute_sql_from_file('schema.sql')

    # This creates tables for everything with a SQLAlchemy model.
    db.create_all()

    # The boathouses table is populated. This table doesn't change, so it
    # only needs to be populated once.
    execute_sql_from_file('define_reach.sql')
    execute_sql_from_file('define_boathouse.sql')

    # The file for keeping track of if it's currently boating season
    execute_sql_from_file('define_default_options.sql')

    # Create a database trigger for manual overrides.
    execute_sql_from_file('override_event_triggers.sql')

    # Now update the database
    update_db()


def update_db():
    """This function basically controls all of our data refreshes. The
    following tables are updated in order:

    - usgs
    - hobolink
    - processed_data
    - model_outputs

    The functions run to calculate the data are imported from other files
    within the data folder.
    """
    options = {
        'con': db.engine,
        'index': False,
        'if_exists': 'replace'
    }

    hours = current_app.config['STORAGE_HOURS']

    from .globals import cache

    try:
        # Populate the `usgs` table.
        from app.data.processing.usgs import get_live_usgs_data
        df_usgs = get_live_usgs_data()
        df_usgs.tail(hours * 4).to_sql('usgs', **options)

        # Populate the `hobolink` table.
        from app.data.processing.hobolink import get_live_hobolink_data
        df_hobolink = get_live_hobolink_data()
        df_hobolink.tail(hours * 6).to_sql('hobolink', **options)

        # Populate the `processed_data` table.
        from app.data.processing.predictive_models import process_data
        df = process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
        df = df.tail(hours)
        df.to_sql('processed_data', **options)

        # Populate the `model_outputs` table.
        from app.data.models.prediction import Prediction
        from app.data.processing.predictive_models import all_models
        model_outs = all_models(df)
        # TODO:
        #  I'm a little worried that I had to add the below to make a test pass.
        #  I thought this part of the code was pretty settled by now, but guess
        #  not. I need to look into what's going on.
        model_outs = model_outs.loc[model_outs['probability'].notna(), :]
        model_outs.to_sql(Prediction.__tablename__, **options)

    finally:
        # Clear the cache every time this function runs.
        # the try -> finally makes sure this always runs, even if an error
        # occurs somewhere when updating.
        cache.clear()


def get_current_time() -> pd.Timestamp:
    return (
        pd.Timestamp('now', tz='UTC')
        .tz_convert('US/Eastern')
        .tz_localize(None)
    )
