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
from celery.result import AsyncResult
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
    from app.data.processing.core import update_db
    update_db()


def update_db_async() -> AsyncResult:
    """This function basically controls all of our data refreshes. The
    following tables are updated in order:

    - usgs
    - hobolink
    - processed_data
    - model_outputs

    The functions run to calculate the data are imported from other files
    within the data folder.

    This function uses Celery to run the pipeline. The pipeline is not
    awaited, meaning that this function returns before the job finishes.
    """
    from app.data.celery import celery_app
    from app.data.celery import build_pipeline

    celery_app.health()
    return build_pipeline(write_to_db=True).delay()


def get_current_time() -> pd.Timestamp:
    return (
        pd.Timestamp('now', tz='UTC')
        .tz_convert('US/Eastern')
        .tz_localize(None)
    )
